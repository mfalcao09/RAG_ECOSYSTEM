"""notion_adapter — página Notion → markdown → content_list.

Motor: API oficial do Notion (REST v2022-06-28) via httpx (import lazy, já instalado).
Sem SDK extra. Aceita URLs públicas/privadas do Notion (`notion.so`, `*.notion.site`)
e refs no formato `notion:<id>`. O token vem de `NOTION_TOKEN` (env) — NUNCA hardcode
(Seção 11 de segurança); a página/database precisa estar compartilhada com a integração.

Estratégia premium (Notion SDK, blocos sincronizados, cache) pode ser plugada depois
SEM mudar o contrato — basta um novo branch de extração.
"""
from __future__ import annotations
import re
from typing import List, Optional

from .base import ContentBlock

# Detecção de referência Notion:
#   - URL: notion.so / www.notion.so / <workspace>.notion.site
#   - ref curta: notion:<id>
_NOTION_URL_RE = re.compile(r"^https?://([\w-]+\.)?notion\.(so|site)/", re.IGNORECASE)
_NOTION_REF_RE = re.compile(r"^notion:", re.IGNORECASE)

# 32 hex TERMINAIS (id Notion sem hífens) — ancorado no fim do path (barra final
# opcional). Conta a partir do fim, então um slug que termine em letras hex coladas
# ao id ainda resolve para os 32 caracteres corretos do id.
_HEX32_TAIL_RE = re.compile(r"([0-9a-fA-F]{32})/?$")

_API_BASE = "https://api.notion.com/v1"
_NOTION_VERSION = "2022-06-28"
_MAX_DEPTH = 3       # limite de recursão em blocos com has_children
_PAGE_SIZE = 100     # máximo permitido pela API por página de resultados


class NotionAdapter:
    name = "notion"

    def can_handle(self, ref: str) -> bool:
        s = (ref or "").strip()
        if not s:
            return False
        return bool(_NOTION_URL_RE.match(s) or _NOTION_REF_RE.match(s))

    def fetch(self, ref: str) -> List[ContentBlock]:
        page_id = self._extract_page_id(ref)
        token = self._get_token()
        client, headers = self._client(token)
        try:
            titulo = self._fetch_title(client, headers, page_id)
            blocks = self._fetch_blocks(client, headers, page_id, depth=0)
        finally:
            client.close()

        md = self._blocks_to_markdown(blocks).strip()
        if not md:
            raise ValueError(
                f"notion_adapter: página {page_id} sem conteúdo textual extraível "
                f"(ref={ref!r}). Confirme que a página está compartilhada com a integração."
            )
        # cabeçalho de proveniência: ancora a citação e dá contexto de origem ao RAG
        text = f"# Fonte (Notion): {titulo} — {ref.strip()}\n\n{md}"
        return [{"type": "text", "text": text, "page_idx": 0}]

    # --- helpers de identidade / auth ---------------------------------------- #
    def _extract_page_id(self, ref: str) -> str:
        """Extrai o page_id (32 hex terminais) e normaliza para UUID 8-4-4-4-12.

        O id Notion fica SEMPRE no fim do path (`.../Slug-<32hex>` ou `notion:<id>`),
        podendo vir hifenizado. Ancoramos a captura no FINAL (e não no 1º run de 32 hex)
        porque o slug humano pode conter letras hex (a/b/c/d/e/f) que, coladas ao id,
        deslocariam um match não-ancorado. Query string / fragmento são descartados."""
        s = (ref or "").strip()
        # descarta query (?) e fragmento (#) — o id está no path
        s = s.split("?", 1)[0].split("#", 1)[0]
        # remove hífens só para a varredura (o id pode vir hifenizado na URL)
        candidato = s.replace("-", "")
        m = _HEX32_TAIL_RE.search(candidato)
        if not m:
            raise ValueError(
                f"notion_adapter: não encontrei um id de página (32 hex) em {ref!r}"
            )
        raw = m.group(1).lower()
        return f"{raw[0:8]}-{raw[8:12]}-{raw[12:16]}-{raw[16:20]}-{raw[20:32]}"

    def _get_token(self) -> str:
        import os

        token = os.environ.get("NOTION_TOKEN")
        if not token or not token.strip():
            raise ValueError(
                "notion_adapter: NOTION_TOKEN ausente. "
                "Crie uma integração interna em notion.so/my-integrations, "
                "compartilhe a página com ela e rode: export NOTION_TOKEN=secret_..."
            )
        return token.strip()

    def _client(self, token: str):
        """Devolve (client httpx, headers). Import lazy como no web_adapter."""
        import httpx

        headers = {
            "Authorization": f"Bearer {token}",
            "Notion-Version": _NOTION_VERSION,
            "Content-Type": "application/json",
        }
        client = httpx.Client(timeout=30.0)
        return client, headers

    # --- chamadas à API ------------------------------------------------------ #
    def _fetch_title(self, client, headers, page_id: str) -> str:
        """GET /pages/{id} → título (primeira propriedade do tipo `title`)."""
        r = client.get(f"{_API_BASE}/pages/{page_id}", headers=headers)
        r.raise_for_status()
        props = (r.json() or {}).get("properties", {}) or {}
        for prop in props.values():
            if isinstance(prop, dict) and prop.get("type") == "title":
                return self._rich_text_to_plain(prop.get("title", [])) or "(sem título)"
        return "(sem título)"

    def _fetch_blocks(self, client, headers, block_id: str, depth: int) -> list:
        """GET /blocks/{id}/children paginado; recursa em has_children até _MAX_DEPTH.

        Anexa os filhos no próprio bloco em `_children` para o conversor montar o
        markdown achatado preservando ordem/hierarquia.
        """
        blocks: list = []
        cursor: Optional[str] = None
        while True:
            params = {"page_size": _PAGE_SIZE}
            if cursor:
                params["start_cursor"] = cursor
            r = client.get(
                f"{_API_BASE}/blocks/{block_id}/children",
                headers=headers,
                params=params,
            )
            r.raise_for_status()
            data = r.json() or {}
            page_results = data.get("results", []) or []

            for blk in page_results:
                if depth < _MAX_DEPTH and blk.get("has_children"):
                    blk["_children"] = self._fetch_blocks(
                        client, headers, blk.get("id", ""), depth + 1
                    )
                blocks.append(blk)

            if data.get("has_more") and data.get("next_cursor"):
                cursor = data["next_cursor"]
            else:
                break
        return blocks

    # --- conversão blocos → markdown ----------------------------------------- #
    def _rich_text_to_plain(self, rich_text: list) -> str:
        """Concatena rich_text[].plain_text (defensivo a itens malformados)."""
        if not rich_text:
            return ""
        partes = []
        for rt in rich_text:
            if isinstance(rt, dict):
                partes.append(rt.get("plain_text", "") or "")
        return "".join(partes).strip()

    def _blocks_to_markdown(self, blocks: list, _depth: int = 0) -> str:
        """Converte a lista de blocos Notion em markdown. Tipos desconhecidos são
        ignorados (não quebram). Filhos (`_children`) são indentados sob o pai."""
        linhas: List[str] = []
        for blk in blocks:
            if not isinstance(blk, dict):
                continue
            btype = blk.get("type", "")
            payload = blk.get(btype, {}) if isinstance(blk.get(btype), dict) else {}
            texto = self._rich_text_to_plain(payload.get("rich_text", []))
            linha = self._render_line(btype, texto, payload)
            if linha is not None:
                linhas.append(linha)

            filhos = blk.get("_children")
            if filhos:
                sub = self._blocks_to_markdown(filhos, _depth + 1)
                if sub:
                    # indenta blocos-filho (2 espaços por nível) preservando hierarquia
                    linhas.append("\n".join("  " + ln for ln in sub.splitlines()))
        return "\n".join(linhas)

    def _render_line(self, btype: str, texto: str, payload: dict) -> Optional[str]:
        """Mapeia 1 bloco → 1 linha markdown. Retorna None para tipos ignorados."""
        if btype == "paragraph":
            return texto  # parágrafo vazio vira linha em branco (separador natural)
        if btype == "heading_1":
            return f"# {texto}"
        if btype == "heading_2":
            return f"## {texto}"
        if btype == "heading_3":
            return f"### {texto}"
        if btype == "bulleted_list_item":
            return f"- {texto}"
        if btype == "numbered_list_item":
            return f"1. {texto}"
        if btype == "to_do":
            marca = "x" if payload.get("checked") else " "
            return f"- [{marca}] {texto}"
        if btype == "quote":
            return f"> {texto}"
        if btype == "callout":
            return f"> {texto}"
        if btype == "code":
            lang = payload.get("language", "") or ""
            return f"```{lang}\n{texto}\n```"
        # tipos desconhecidos (divider, image, table, embed, ...): ignora sem quebrar
        return None
