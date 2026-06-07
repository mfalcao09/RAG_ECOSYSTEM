"""Utilidades stdlib para o subsistema de normas (sem dependências externas)."""
from __future__ import annotations
import re
import unicodedata


def strip_accents(text: str) -> str:
    """Remove acentuação preservando o resto (NFKD)."""
    nfkd = unicodedata.normalize("NFKD", str(text or ""))
    return "".join(c for c in nfkd if not unicodedata.combining(c))


def slugify(text: str, sep: str = "-") -> str:
    """Converte texto livre em slug seguro para nome de pasta/arquivo."""
    base = strip_accents(text).lower()
    base = re.sub(r"[^a-z0-9]+", sep, base)
    return base.strip(sep) or "sem-valor"


def normalize_numero(numero) -> str:
    """Normaliza número de norma para chave estável (remove apenas espaços)."""
    return re.sub(r"\s+", "", str(numero or "").strip())


def safe_filename(s: str) -> str:
    """Nome de arquivo seguro: remove acentos e troca chars de path por '_'."""
    base = strip_accents(str(s or ""))
    base = re.sub(r'[\/\\:*?"<>|()\[\]\s]+', "_", base)
    return base.strip("_") or "sem-nome"


def format_numero_br(numero) -> str:
    """Formata número com separador de milhar BR (8666 -> 8.666; 123 -> 123)."""
    s = str(numero or "").strip()
    digits = re.sub(r"\D", "", s)
    if not digits:
        return s
    try:
        return f"{int(digits):,}".replace(",", ".")
    except ValueError:
        return s
