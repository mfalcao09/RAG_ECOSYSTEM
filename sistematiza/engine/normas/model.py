"""Modelo de dados de uma Norma jurídica."""
from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import List, Optional, Dict, Any
from . import taxonomy
from .util import normalize_numero, format_numero_br, safe_filename

# Situações de vigência
VIGENTE = "vigente"
REVOGADA = "revogada"
REVOGADA_PARCIAL = "revogada_parcialmente"
VACATIO = "vacatio_legis"
SEM_EFICACIA = "sem_eficacia"
INDEFINIDA = "indefinida"

SITUACAO_BANNER = {
    VIGENTE:          "✅ VIGENTE",
    REVOGADA:         "⛔ REVOGADA",
    REVOGADA_PARCIAL: "⚠️ REVOGADA PARCIALMENTE",
    VACATIO:          "🕒 VACATIO LEGIS (ainda não vigente)",
    SEM_EFICACIA:     "🚫 SEM EFICÁCIA",
    INDEFINIDA:       "❔ SITUAÇÃO INDEFINIDA",
}


@dataclass
class Norma:
    tipo: str = "outros"
    numero: str = ""
    ano: Optional[int] = None
    data: Optional[str] = None            # ISO yyyy-mm-dd
    orgao: str = ""
    esfera: str = "federal"               # federal|estadual|municipal|distrital
    uf: Optional[str] = None
    ementa: str = ""
    assuntos: List[str] = field(default_factory=list)
    revoga: List[str] = field(default_factory=list)
    revoga_parcialmente: List[str] = field(default_factory=list)
    altera: List[str] = field(default_factory=list)
    fonte_url: Optional[str] = None
    arquivo: Optional[str] = None
    texto_path: Optional[str] = None
    observacoes: Optional[str] = None
    vigente: Optional[bool] = None          # vigência curada; autoritativa quando presente
    nota_revogacao: Optional[str] = None    # fonte revogadora em texto livre (sem chave)
    # ---- campos computados (preenchidos pelo resolver de vigência) ----
    situacao: str = INDEFINIDA
    revogada_por: List[str] = field(default_factory=list)
    revogada_parcialmente_por: List[str] = field(default_factory=list)
    alterada_por: List[str] = field(default_factory=list)

    def __post_init__(self):
        self.tipo = taxonomy.detect_tipo(self.tipo)
        self.numero = normalize_numero(self.numero)
        if isinstance(self.assuntos, str):
            self.assuntos = [self.assuntos]

    @property
    def chave(self) -> str:
        return f"{self.tipo}-{self.numero or 's-n'}-{self.ano or 's-a'}"

    @property
    def chave_fs(self) -> str:
        """Chave segura para nome de arquivo (numero real pode conter '/', '(', etc.)."""
        return safe_filename(self.chave)

    @property
    def rank(self) -> int:
        return taxonomy.rank_of(self.tipo)

    @property
    def display(self) -> str:
        if self.tipo == "constituicao_federal":
            return f"Constituição Federal de {self.ano}".strip()
        num = format_numero_br(self.numero) if self.numero else "s/nº"
        ano = f"/{self.ano}" if self.ano else ""
        return f"{taxonomy.label_of(self.tipo)} nº {num}{ano}"

    @property
    def ordenacao(self) -> str:
        """Chave de ordenação cronológica (mais recente = maior string ISO)."""
        return self.data or (f"{self.ano}-12-31" if self.ano else "0000-00-00")

    def is_revogada(self) -> bool:
        return self.situacao == REVOGADA

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["chave"] = self.chave
        d["display"] = self.display
        d["rank"] = self.rank
        d["sigla"] = taxonomy.sigla_of(self.tipo)
        return d

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "Norma":
        allowed = set(cls.__dataclass_fields__)  # type: ignore[attr-defined]
        return cls(**{k: v for k, v in d.items() if k in allowed})
