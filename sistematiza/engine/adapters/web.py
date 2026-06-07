"""web_adapter — URL → markdown limpo → content_list.

Motor primário: trafilatura (local, sem API key, remove boilerplate, gera markdown).
Fallback: httpx + BeautifulSoup (sempre disponível). Estratégia premium para sites
JS-heavy (Apify rag-web-browser / Firecrawl) pode ser plugada depois SEM mudar o
contrato — basta um novo branch de extração.
"""
from __future__ import annotations
import re
from typing import List, Optional

from .base import ContentBlock

_URL_RE = re.compile(r"^https?://", re.IGNORECASE)
_UA = "Mozilla/5.0 (compatible; RAG_ECOSYSTEM/web_adapter)"


class WebAdapter:
    name = "web"

    def can_handle(self, ref: str) -> bool:
        return bool(_URL_RE.match((ref or "").strip()))

    def fetch(self, ref: str) -> List[ContentBlock]:
        url = ref.strip()
        md = self._extract_trafilatura(url) or self._extract_bs4(url)
        if not md or not md.strip():
            raise ValueError(f"web_adapter: não consegui extrair conteúdo de {url}")
        # cabeçalho de proveniência: ancora a citação e dá contexto de origem ao RAG
        text = f"# Fonte: {url}\n\n{md.strip()}"
        return [{"type": "text", "text": text, "page_idx": 0}]

    # --- motores de extração (camadas) --------------------------------------- #
    def _extract_trafilatura(self, url: str) -> Optional[str]:
        try:
            import trafilatura
        except ImportError:
            return None
        downloaded = trafilatura.fetch_url(url)
        if not downloaded:
            return None
        return trafilatura.extract(
            downloaded,
            output_format="markdown",
            include_tables=True,
            include_links=False,
            include_comments=False,
        )

    def _extract_bs4(self, url: str) -> str:
        import httpx
        from bs4 import BeautifulSoup

        r = httpx.get(url, follow_redirects=True, timeout=20.0, headers={"User-Agent": _UA})
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "lxml")
        for tag in soup(["script", "style", "nav", "footer", "header", "aside", "form", "noscript"]):
            tag.decompose()
        main = soup.find("main") or soup.find("article") or soup.body or soup
        return main.get_text("\n", strip=True)
