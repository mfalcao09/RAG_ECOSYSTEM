"""Registro de ingest adapters (camada de FONTES do RAG_ECOSYSTEM).

`resolve(ref)` devolve o adapter que sabe lidar com a referência, ou None
(= tratar como arquivo/pasta local pelo parser MinerU). Adicionar uma fonte nova
é só registrar o adapter em _ADAPTERS — o `cmd_ingest` não muda.
"""
from __future__ import annotations
from typing import Optional, List

from .base import SourceAdapter, ContentBlock  # noqa: F401 (reexport)
from .web import WebAdapter

# ordem = prioridade de resolução
_ADAPTERS: List[SourceAdapter] = [
    WebAdapter(),
]


def resolve(ref: str) -> Optional[SourceAdapter]:
    for adapter in _ADAPTERS:
        try:
            if adapter.can_handle(ref):
                return adapter
        except Exception:
            continue
    return None


def list_adapters() -> List[str]:
    return [a.name for a in _ADAPTERS]
