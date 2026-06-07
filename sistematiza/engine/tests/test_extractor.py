"""Teste do extrator heurístico de normas (stdlib puro)."""
import sys
import unittest
from pathlib import Path

ENGINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ENGINE))

from normas import Norma                       # noqa: E402
from normas.extractor import extrair_de_texto  # noqa: E402

TEXTO = (
    "LEI Nº 14.133, DE 1º DE ABRIL DE 2021. Lei de Licitações e Contratos "
    "Administrativos. Art. 193. Revogam-se: a Lei nº 8.666, de 21 de junho de 1993; "
    "a Lei nº 10.520, de 17 de julho de 2002."
)


class TestExtractor(unittest.TestCase):
    def test_extrai_principal_e_revogadas(self):
        cands = extrair_de_texto(TEXTO)
        by = {Norma.from_dict(c).chave: c for c in cands}
        self.assertIn("lei_ordinaria-14.133-2021", by)
        self.assertIn("lei_ordinaria-8.666-1993", by)
        self.assertIn("lei_ordinaria-10.520-2002", by)
        primary = by["lei_ordinaria-14.133-2021"]
        self.assertIn("lei_ordinaria-8.666-1993", primary["revoga"])
        self.assertIn("lei_ordinaria-10.520-2002", primary["revoga"])
        self.assertIn("CONFERIR", primary["observacoes"])

    def test_texto_vazio(self):
        self.assertEqual(extrair_de_texto(""), [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
