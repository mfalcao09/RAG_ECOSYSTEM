"""Resolução de vigência/revogação a partir do grafo de relações entre normas.

A inteligência central do modo jurídico: dada uma lista de Normas onde cada uma
declara o que `revoga`/`altera`, propaga essas relações de forma bidirecional e
calcula a `situacao` de cada norma (vigente/revogada/revogada parcialmente/vacatio).
"""
from __future__ import annotations
from typing import List, Dict, Optional
import datetime
from .model import (
    Norma, VIGENTE, REVOGADA, REVOGADA_PARCIAL, VACATIO,
)


def _index(normas: List[Norma]) -> Dict[str, Norma]:
    return {n.chave: n for n in normas}


def resolver(normas: List[Norma], ref_date: Optional[str] = None) -> List[Norma]:
    """Propaga relações e calcula `situacao`. Muta e retorna a mesma lista.

    Bidirecional: se B.revoga inclui a chave de A, então A.revogada_por += [B].
    """
    idx = _index(normas)
    for n in normas:
        n.revogada_por = []
        n.revogada_parcialmente_por = []
        n.alterada_por = []
    for n in normas:
        for alvo in n.revoga:
            if alvo in idx:
                idx[alvo].revogada_por.append(n.chave)
        for alvo in n.revoga_parcialmente:
            if alvo in idx:
                idx[alvo].revogada_parcialmente_por.append(n.chave)
        for alvo in n.altera:
            if alvo in idx:
                idx[alvo].alterada_por.append(n.chave)
    today = ref_date or datetime.date.today().isoformat()
    for n in normas:
        # `vigente` curado é autoritativo (acervos reais carregam flag, não grafo completo)
        if n.vigente is False:
            n.situacao = REVOGADA_PARCIAL if n.revogada_parcialmente_por else REVOGADA
        elif n.vigente is True:
            n.situacao = VIGENTE
        elif n.revogada_por:
            n.situacao = REVOGADA
        elif n.revogada_parcialmente_por:
            n.situacao = REVOGADA_PARCIAL
        elif n.data and n.data > today:
            n.situacao = VACATIO
        else:
            n.situacao = VIGENTE
    return normas


def cadeia_revogacao(norma: Norma, normas: List[Norma]) -> Dict[str, list]:
    """Retorna {'revogada_por': [display...], 'revoga': [display...]}."""
    idx = _index(normas)
    return {
        "revogada_por": [idx[c].display for c in norma.revogada_por if c in idx],
        "revoga": [idx[c].display for c in norma.revoga if c in idx],
    }


def descricao_situacao(norma: Norma, normas: List[Norma]) -> str:
    """Texto curto e legível: 'REVOGADA por Lei nº 14.133/2021 (2021)'.

    Quando a revogadora não está no acervo por chave, usa `nota_revogacao` (texto livre).
    """
    idx = _index(normas)
    if norma.situacao == REVOGADA:
        if norma.revogada_por:
            revs = [
                idx[c].display + (f" ({idx[c].ano})" if idx[c].ano else "")
                for c in norma.revogada_por if c in idx
            ]
            return "REVOGADA por " + "; ".join(revs)
        if norma.nota_revogacao:
            return "REVOGADA — " + norma.nota_revogacao
        return "REVOGADA"
    if norma.situacao == REVOGADA_PARCIAL:
        if norma.revogada_parcialmente_por:
            revs = [idx[c].display for c in norma.revogada_parcialmente_por if c in idx]
            return "REVOGADA PARCIALMENTE por " + "; ".join(revs)
        if norma.nota_revogacao:
            return "REVOGADA PARCIALMENTE — " + norma.nota_revogacao
        return "REVOGADA PARCIALMENTE"
    if norma.situacao == VACATIO:
        return f"VACATIO LEGIS — vigência a partir de {norma.data}"
    if norma.situacao == VIGENTE:
        return "VIGENTE"
    return "SITUAÇÃO INDEFINIDA"


def referencias_orfas(normas: List[Norma]):
    """Lista (chave, campo, ref) onde revoga/revoga_parcialmente/altera apontam
    para uma norma AUSENTE do acervo — evita revogação 'perdida' silenciosamente."""
    idx = {n.chave for n in normas}
    orfas = []
    for n in normas:
        for campo in ("revoga", "revoga_parcialmente", "altera"):
            for ref in getattr(n, campo):
                if ref not in idx:
                    orfas.append((n.chave, campo, ref))
    return orfas
