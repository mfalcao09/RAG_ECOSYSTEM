"""video_adapter — URL de YouTube → transcrição limpa → content_list.

Motor único: o binário `yt-dlp` (local, sem API key) extrai a TRANSCRIÇÃO via
LEGENDAS (`--write-subs --write-auto-subs`), SEM baixar o vídeo (`--skip-download`).
O `.vtt` resultante é parseado para texto corrido (remove timestamps, cue settings,
tags `<...>` e a duplicação que legendas auto-geradas produzem em rolagem).

Escopo deliberado: SÓ legendas. Se o vídeo não tem legenda (nem manual, nem auto),
levanta `ValueError`. Fallback de áudio + transcrição (Whisper) é escopo FUTURO e
pode ser plugado depois SEM mudar o contrato — basta um novo branch de captura.

Roteamento: `can_handle` casa SÓ URLs de YouTube; URLs genéricas seguem para o
web_adapter. Por isso o registro deste adapter deve vir ANTES do WebAdapter em
`_ADAPTERS` (ambos casam `https://`, mas este é o mais específico).
"""
from __future__ import annotations
import re
from typing import List, Optional

from .base import ContentBlock

# Hosts/paths que identificam um vídeo do YouTube (e SÓ YouTube).
_YOUTUBE_RE = re.compile(
    r"^https?://"
    r"(?:www\.|m\.)?"                       # opcional: www. ou m.
    r"(?:"
    r"youtube\.com/watch\?(?:[^ ]*&)?v=[\w-]+"   # youtube.com/watch?v=ID
    r"|youtube\.com/shorts/[\w-]+"               # youtube.com/shorts/ID
    r"|youtube\.com/live/[\w-]+"                 # youtube.com/live/ID
    r"|youtu\.be/[\w-]+"                         # youtu.be/ID (encurtado)
    r")",
    re.IGNORECASE,
)

# Linha de timestamp do VTT: "00:00:00.000 --> 00:00:05.400 align:start position:0%".
_TS_RE = re.compile(r"^\d{2}:\d{2}:\d{2}[.,]\d{3}\s*-->\s*")
# Timestamps inline das legendas auto-geradas: "<00:00:00.480>".
_INLINE_TS_RE = re.compile(r"<\d{2}:\d{2}:\d{2}[.,]\d{3}>")
# Tags de marcação do VTT: "<c>", "</c>", "<c.colorXXXX>", "<v Autor>", "<b>" ...
_TAG_RE = re.compile(r"</?[a-zA-Z][^>]*>")


class VideoAdapter:
    name = "youtube"

    def can_handle(self, ref: str) -> bool:
        # SÓ YouTube — URLs genéricas e caminhos de arquivo ficam de fora de propósito.
        return bool(_YOUTUBE_RE.match((ref or "").strip()))

    def fetch(self, ref: str) -> List[ContentBlock]:
        url = ref.strip()
        title, transcript = self._capture(url)
        if not transcript or not transcript.strip():
            raise ValueError(
                f"video_adapter: nenhuma legenda/transcrição disponível para {url}"
            )
        title = (title or "").strip() or "(sem título)"
        # cabeçalho de proveniência: ancora a citação e dá contexto de origem ao RAG
        text = f"# Fonte (YouTube): {title} — {url}\n\n{transcript.strip()}"
        return [{"type": "text", "text": text, "page_idx": 0}]

    # --- captura (yt-dlp) ----------------------------------------------------- #
    def _capture(self, url: str) -> tuple[Optional[str], Optional[str]]:
        """Roda yt-dlp num tmpdir, devolve (título, transcrição limpa).

        Isolado num método para o teste poder fazer monkeypatch sem rede nem binário.
        """
        import shutil
        import subprocess
        import tempfile
        from pathlib import Path

        ytdlp = shutil.which("yt-dlp")
        if not ytdlp:
            raise RuntimeError(
                "video_adapter: binário 'yt-dlp' não encontrado no PATH"
            )

        tmp = tempfile.mkdtemp(prefix="rag_yt_")
        try:
            # título (campo único; não baixa o vídeo)
            title = self._run_print_title(ytdlp, url, subprocess)

            # legendas .vtt (pt.* e en.*; manual + auto), sem baixar o vídeo
            subprocess.run(
                [
                    ytdlp,
                    "--skip-download",
                    "--write-subs",
                    "--write-auto-subs",
                    "--sub-langs",
                    "pt.*,en.*",
                    "--sub-format",
                    "vtt",
                    "-o",
                    f"{tmp}/%(id)s.%(ext)s",
                    url,
                ],
                check=False,            # ausência de legenda não é exceção de processo
                capture_output=True,
                text=True,
                timeout=180,
            )

            vtt = self._pick_vtt(Path(tmp))
            if vtt is None:
                return title, None
            return title, self._parse_vtt(vtt.read_text(encoding="utf-8", errors="replace"))
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def _run_print_title(self, ytdlp: str, url: str, subprocess) -> Optional[str]:
        try:
            r = subprocess.run(
                [ytdlp, "--skip-download", "--print", "%(title)s", url],
                check=False,
                capture_output=True,
                text=True,
                timeout=60,
            )
            out = (r.stdout or "").strip().splitlines()
            return out[-1].strip() if out else None
        except Exception:
            return None

    def _pick_vtt(self, tmpdir) -> Optional["object"]:
        """Escolhe o melhor .vtt baixado: prioriza português, depois inglês.

        yt-dlp nomeia como `<id>.<lang>.vtt` (ex.: `abc.pt.vtt`, `abc.en-ar.vtt`).
        """
        vtts = sorted(tmpdir.glob("*.vtt"))
        if not vtts:
            return None

        def rank(path) -> int:
            # sufixo de idioma fica entre o id e a extensão: "abc.pt.vtt" → "pt"
            lang = path.name.rsplit(".", 2)[-2].lower() if path.name.count(".") >= 2 else ""
            if lang.startswith("pt"):
                return 0
            if lang.startswith("en"):
                return 1
            return 2

        return sorted(vtts, key=rank)[0]

    # --- parse do VTT --------------------------------------------------------- #
    def _parse_vtt(self, raw: str) -> str:
        """Converte o conteúdo de um arquivo .vtt em texto corrido limpo.

        Remove: header WEBVTT, metadados (Kind/Language), NOTE, linhas de timestamp
        (com cue settings), timestamps inline `<00:00:00.480>` e tags `<c>`/`<v>`.
        Colapsa linhas duplicadas consecutivas (legendas auto rolam repetindo a
        última linha) e linhas em branco repetidas.
        """
        linhas_limpas: List[str] = []
        anterior: Optional[str] = None

        for bruta in raw.splitlines():
            linha = bruta.strip()

            # pula cabeçalho, metadados e blocos NOTE
            if not linha:
                continue
            if linha.upper().startswith("WEBVTT"):
                continue
            if linha.startswith(("Kind:", "Language:", "NOTE")):
                continue
            # pula linhas de timestamp ("00:00:00.000 --> ...") e o número da cue
            if _TS_RE.match(linha):
                continue
            if linha.isdigit():
                continue

            # remove timestamps inline e tags de marcação
            linha = _INLINE_TS_RE.sub("", linha)
            linha = _TAG_RE.sub("", linha)
            linha = linha.strip()
            if not linha:
                continue

            # colapsa duplicação consecutiva (rolagem de legenda auto)
            if linha == anterior:
                continue

            linhas_limpas.append(linha)
            anterior = linha

        return "\n".join(linhas_limpas)
