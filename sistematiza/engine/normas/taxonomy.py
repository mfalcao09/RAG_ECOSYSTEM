"""Taxonomia normativa brasileira: hierarquia das fontes do direito + detecção de tipo.

Stdlib-only. `rank` menor = posição mais alta na hierarquia (CF=1 ... Portaria=8 ...).
Ordem de `_TIPOS` é significativa: a detecção por alias resolve do mais específico
para o mais genérico (ex.: "decreto-lei" casa antes de "decreto").
"""
from __future__ import annotations
from .util import strip_accents

# (key, sigla, label, rank, [aliases em minúsculo/sem acento])
_TIPOS = [
    ("constituicao_federal", "CF",   "Constituição Federal",            1,  ["constituicao federal", "constituicao da republica", "cf/88", "crfb", "constituicao de 1988"]),
    ("emenda_constitucional", "EC",  "Emenda Constitucional",           2,  ["emenda constitucional", "emenda a constituicao"]),
    ("tratado_internacional", "TRAT","Tratado/Convenção Internacional", 3,  ["tratado", "convencao internacional", "pacto de", "protocolo internacional"]),
    ("lei_complementar",     "LC",   "Lei Complementar",                4,  ["lei complementar"]),
    ("decreto_lei",          "DL",   "Decreto-Lei",                     5,  ["decreto-lei", "decreto lei"]),
    ("medida_provisoria",    "MP",   "Medida Provisória",               5,  ["medida provisoria", "mp no", "mp n"]),
    ("lei_delegada",         "LDEL", "Lei Delegada",                    5,  ["lei delegada"]),
    ("decreto_legislativo",  "DLEG", "Decreto Legislativo",             5,  ["decreto legislativo"]),
    ("resolucao_legislativa","RESL", "Resolução (Senado/Câmara)",       5,  ["resolucao do senado", "resolucao da camara", "resolucao do congresso"]),
    ("lei_ordinaria",        "LEI",  "Lei Ordinária",                   5,  ["lei ordinaria", "lei no", "lei n", "lei nº", "^lei$", "lei federal", "lei estadual", "lei municipal"]),
    ("decreto",              "DEC",  "Decreto",                         6,  ["decreto regulamentar", "decreto autonomo", "^decreto$", "decreto no", "decreto n", "decreto federal", "decreto estadual", "decreto municipal"]),
    ("regimento",            "REG",  "Regimento",                       7,  ["regimento interno", "regimento"]),
    ("instrucao_normativa",  "IN",   "Instrução Normativa",             7,  ["instrucao normativa", "in no", "in n"]),
    ("resolucao",            "RES",  "Resolução (administrativa)",      7,  ["resolucao normativa", "resolucao", "ren no", "ren n"]),
    ("deliberacao",          "DELIB","Deliberação",                     7,  ["deliberacao"]),
    ("procedimento_de_rede", "PROREDE","Procedimento de Rede (ONS)",    7,  ["procedimento de rede", "prorede"]),
    ("anexo_resolucao",      "ANEXO","Anexo de Resolução",              7,  ["anexo de resolucao", "anexo"]),
    ("portaria_normativa",   "PORTN","Portaria Normativa",              8,  ["portaria normativa"]),
    ("portaria_interministerial","PORTI","Portaria Interministerial",   8,  ["portaria interministerial"]),
    ("portaria",             "PORT", "Portaria",                        8,  ["portaria"]),
    ("despacho",             "DESP", "Despacho",                        9,  ["despacho"]),
    ("manual_tecnico",       "MANUAL","Manual Técnico",                 10, ["manual tecnico", "manual"]),
    ("consulta_publica",     "CP",   "Consulta Pública",                11, ["consulta publica"]),
    ("circular",             "CIRC", "Circular",                        8,  ["circular"]),
    ("ordem_de_servico",     "OS",   "Ordem de Serviço",                9,  ["ordem de servico"]),
    ("ato_normativo",        "ATO",  "Ato Normativo/Declaratório",      9,  ["ato declaratorio", "ato normativo"]),
    ("sumula",               "SUM",  "Súmula",                          10, ["sumula vinculante", "sumula"]),
    ("jurisprudencia",       "JUR",  "Jurisprudência/Acórdão",          11, ["acordao", "jurisprudencia", "decisao judicial"]),
    ("outros",               "OUT",  "Outros",                          99, []),
]

TIPOS = {k: {"sigla": s, "label": l, "rank": r, "aliases": a} for (k, s, l, r, a) in _TIPOS}
ORDER = [k for (k, *_rest) in _TIPOS]


def rank_of(tipo_key: str) -> int:
    return TIPOS.get(tipo_key, TIPOS["outros"])["rank"]


def label_of(tipo_key: str) -> str:
    return TIPOS.get(tipo_key, TIPOS["outros"])["label"]


def sigla_of(tipo_key: str) -> str:
    return TIPOS.get(tipo_key, TIPOS["outros"])["sigla"]


def detect_tipo(raw: str) -> str:
    """Mapeia uma string livre de tipo para a chave canônica.

    Aceita a chave canônica, a sigla, ou uma descrição livre.
    """
    if not raw:
        return "outros"
    if raw in TIPOS:
        return raw
    norm = strip_accents(str(raw)).lower().strip()
    for key, meta in TIPOS.items():
        if norm == meta["sigla"].lower():
            return key
    for key, meta in TIPOS.items():
        for alias in meta["aliases"]:
            pat = alias.strip()
            if not pat:
                continue
            if pat.startswith("^") and pat.endswith("$"):
                if norm == pat[1:-1]:
                    return key
            elif pat in norm:
                return key
    return "outros"
