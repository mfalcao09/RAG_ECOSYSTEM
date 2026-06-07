"""Extrator heurístico de metadados de norma a partir de TEXTO (stdlib puro).

PROPÕE candidatos para CONFERÊNCIA HUMANA — nunca confia cegamente (Seção 5).
Entrada: texto (ex.: cabeçalho/ementa de uma lei, ou markdown de um PDF já convertido).
Saída: list[dict] no schema de Norma, com `observacoes` marcando extração automática.

Limitação assumida: heurística por regex de citações brasileiras; serve para reduzir
o trabalho manual, não para substituir a conferência. Toda saída deve ser revisada
antes de `normas import`.
"""
from __future__ import annotations
import re
from typing import List, Dict, Optional, Tuple
from .taxonomy import detect_tipo
from .util import normalize_numero, strip_accents

_MESES = {
    "janeiro": 1, "fevereiro": 2, "marco": 3, "abril": 4, "maio": 5, "junho": 6,
    "julho": 7, "agosto": 8, "setembro": 9, "outubro": 10, "novembro": 11, "dezembro": 12,
}

_TIPO_ALT = (
    r"(Lei Complementar|Lei Delegada|Decreto-Lei|Decreto Legislativo|"
    r"Medida Provis[oó]ria|Emenda Constitucional|Instru[cç][aã]o Normativa|"
    r"Resolu[cç][aã]o|Portaria|Decreto|Lei)"
)
_CIT = re.compile(_TIPO_ALT + r"\s+n[ºo°\.]*\s*([0-9][0-9\.]*)", re.IGNORECASE)
_DATA = re.compile(
    # aceita dia ordinal em variações: "1º", "1o", "1°", "1ª", "1." ou nada
    r"de\s+(\d{1,2})\s*[ºo°ªa\.]?\s+de\s+([A-Za-zçÇãÃéÉ]+)\s+de\s+(\d{4})", re.IGNORECASE
)
_REVOGA = re.compile(r"revoga", re.IGNORECASE)


def _data_apos(texto: str, pos: int, janela: int = 90) -> Tuple[Optional[str], Optional[int]]:
    m = _DATA.search(texto, pos, min(len(texto), pos + janela))
    if not m:
        return None, None
    dia, mes_raw, ano = m.group(1), strip_accents(m.group(2)).lower(), m.group(3)
    mes = _MESES.get(mes_raw, 0)
    if not mes:
        return None, int(ano)
    return f"{ano}-{mes:02d}-{int(dia):02d}", int(ano)


def _citacoes(texto: str) -> List[Dict]:
    cits = []
    for m in _CIT.finditer(texto):
        numero = normalize_numero(m.group(2)).rstrip(".")
        data, ano = _data_apos(texto, m.end())
        cits.append({
            "tipo": detect_tipo(m.group(1)),
            "numero": numero,
            "ano": ano,
            "data": data,
            "_pos": m.start(),
        })
    return cits


def _chave(c: Dict) -> str:
    return f'{c["tipo"]}-{c["numero"] or "s-n"}-{c["ano"] or "s-a"}'


def extrair_de_texto(texto: str) -> List[Dict]:
    """Retorna candidatos (norma principal + normas revogadas detectadas)."""
    cits = _citacoes(texto)
    if not cits:
        return []

    spans = [(m.end(), m.end() + 300) for m in _REVOGA.finditer(texto)]

    def in_revoga(pos: int) -> bool:
        return any(s <= pos <= e for s, e in spans)

    primary = cits[0]
    revogadas = [c for c in cits[1:] if in_revoga(c["_pos"])]
    revoga_chaves = [_chave(c) for c in revogadas]

    candidatos: List[Dict] = []
    seen = set()

    def add(c: Dict, revoga: Optional[List[str]] = None) -> None:
        ch = _chave(c)
        if ch in seen:
            return
        seen.add(ch)
        d = {
            "tipo": c["tipo"], "numero": c["numero"], "ano": c["ano"],
            "data": c["data"], "ementa": "", "assuntos": [],
            "observacoes": "EXTRAÍDO AUTOMATICAMENTE — CONFERIR número/ano/revogação antes de importar.",
        }
        if revoga:
            d["revoga"] = revoga
        candidatos.append(d)

    add(primary, revoga=revoga_chaves or None)
    for c in revogadas:
        add(c)
    return candidatos
