"""Cobertura de situações: vacatio legis e revogação parcial não podem sumir das facetas."""
import sys
import tempfile
import unittest
from pathlib import Path

ENGINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ENGINE))

from normas import carregar, organizar  # noqa: E402

DADOS = [
    {"tipo": "lei_ordinaria", "numero": "100", "ano": 2030, "data": "2030-01-01",
     "ementa": "Lei futura (vacatio legis)."},
    {"tipo": "lei_ordinaria", "numero": "200", "ano": 2020, "data": "2020-01-01",
     "ementa": "Lei parcialmente revogada."},
    {"tipo": "lei_ordinaria", "numero": "201", "ano": 2021, "data": "2021-01-01",
     "ementa": "Revoga parcialmente a 200.",
     "revoga_parcialmente": ["lei_ordinaria-200-2020"]},
]


class TestCobertura(unittest.TestCase):
    def test_todos_os_estados_tem_faceta(self):
        normas = carregar(DADOS)
        with tempfile.TemporaryDirectory() as tmp:
            stats = organizar(normas, tmp)
            out = Path(tmp)
            self.assertTrue((out / "por-situacao" / "vacatio-legis" / "_index.md").exists())
            self.assertTrue((out / "por-situacao" / "revogada-parcialmente" / "_index.md").exists())
            self.assertTrue((out / "por-situacao" / "vigente" / "_index.md").exists())
            self.assertEqual(sum(stats["por_situacao"].values()), 3)
            vig = (out / "vigentes" / "_index.md").read_text(encoding="utf-8")
            self.assertIn("200", vig)


if __name__ == "__main__":
    unittest.main(verbosity=2)
