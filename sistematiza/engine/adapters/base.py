"""Contrato dos ingest adapters — qualquer FONTE → content_list normalizado.

Cada adapter converte uma referência (URL, id de vídeo, query de DB, ...) numa lista
de ContentBlock que o RAG-Anything aceita via `insert_content_list()` — bypassando o
parser de arquivo (MinerU). Adicionar uma fonte = adicionar um adapter; o core não muda.

Esta é a camada que transforma "sistematiza" (indexa arquivos) em "RAG_ECOSYSTEM"
(indexa qualquer fonte). Ver docs/ARSENAL-RAG.md §5.
"""
from __future__ import annotations
from typing import Protocol, List, Dict, Any, runtime_checkable

# Bloco no formato esperado por RAGAnything.insert_content_list:
#   texto:    {"type": "text", "text": "...", "page_idx": 0}
#   imagem:   {"type": "image", "img_path": "/abs/...", "image_caption": [...], "page_idx": N}
#   tabela:   {"type": "table", "table_body": "md", "table_caption": [...], "page_idx": N}
#   equação:  {"type": "equation", "latex": "...", "text": "...", "page_idx": N}
ContentBlock = Dict[str, Any]


@runtime_checkable
class SourceAdapter(Protocol):
    """Interface mínima de um adapter de fonte."""

    name: str

    def can_handle(self, ref: str) -> bool:
        """True se este adapter sabe lidar com a referência (ex.: URL http)."""
        ...

    def fetch(self, ref: str) -> List[ContentBlock]:
        """Captura a fonte e devolve content_list normalizado (markdown em blocos)."""
        ...
