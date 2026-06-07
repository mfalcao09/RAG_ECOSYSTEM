"""Testa que a flag `vigente` (vigência curada) é autoritativa, com nota em texto livre."""
import sys
import unittest
from pathlib import Path

ENGINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ENGINE))

from normas import carregar, descricao_situacao   # noqa: E402
from normas.model import REVOGADA, VIGENTE         # noqa: E402


class TestVigenteExplicito(unittest.TestCase):
    def test_flag_autoritativa_sem_relacao(self):
        normas = carregar([
            {"tipo": "lei_ordinaria", "numero": "1", "ano": 2000, "data": "2000-01-01",
             "ementa": "x", "vigente": False, "nota_revogacao": "Revogada por Decreto X"},
            {"tipo": "lei_ordinaria", "numero": "2", "ano": 2001, "data": "2001-01-01",
             "ementa": "y", "vigente": True},
        ])
        by = {n.chave: n for n in normas}
        self.assertEqual(by["lei_ordinaria-1-2000"].situacao, REVOGADA)
        self.assertEqual(by["lei_ordinaria-2-2001"].situacao, VIGENTE)

    def test_descricao_usa_nota_livre(self):
        normas = carregar([{
            "tipo": "decreto", "numero": "9", "ano": 2010, "data": "2010-01-01",
            "ementa": "z", "vigente": False, "nota_revogacao": "Revogado por Decreto 10/2019",
        }])
        d = descricao_situacao(normas[0], normas)
        self.assertIn("REVOGADA", d)
        self.assertIn("Decreto 10/2019", d)


if __name__ == "__main__":
    unittest.main(verbosity=2)
