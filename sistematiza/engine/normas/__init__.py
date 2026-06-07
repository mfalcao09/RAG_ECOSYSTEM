"""Subsistema jurídico de normas do Sistematiza (feature de 1ª classe).

Stdlib-only: pode ser importado e testado sem RAG-Anything/LightRAG instalados.
"""
from __future__ import annotations
from typing import List
from .model import Norma
from .vigencia import resolver, cadeia_revogacao, descricao_situacao, referencias_orfas
from .organizer import organizar
from .extractor import extrair_de_texto
from . import taxonomy

__all__ = [
    "Norma", "resolver", "cadeia_revogacao", "descricao_situacao", "referencias_orfas",
    "organizar", "extrair_de_texto", "taxonomy", "carregar",
]


def carregar(normas_data) -> List[Norma]:
    """Constrói lista de Norma a partir de list[dict] e resolve a vigência."""
    normas = [Norma.from_dict(d) for d in normas_data]
    resolver(normas)
    return normas
