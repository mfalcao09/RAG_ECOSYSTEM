"""Testes do subsistema jurídico de normas — stdlib puro (zero deps externas).

Prova de funcionamento (Seção 8.3): vigência/revogação calculadas corretamente e
acervo organizado em pastas com revogadas marcadas, SEM tocar no RAG-Anything.
"""
import json
import sys
import tempfile
import unittest
from pathlib import Path

ENGINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ENGINE))

from normas import carregar, organizar, descricao_situacao  # noqa: E402
from normas.model import REVOGADA, VIGENTE                    # noqa: E402
from normas.taxonomy import detect_tipo, rank_of              # noqa: E402

SAMPLE = Path(__file__).parent / "sample_normas.json"


def _carrega():
    return carregar(json.loads(SAMPLE.read_text(encoding="utf-8")))


class TestTaxonomy(unittest.TestCase):
    def test_detect(self):
        self.assertEqual(detect_tipo("Lei Complementar"), "lei_complementar")
        self.assertEqual(detect_tipo("Decreto-Lei"), "decreto_lei")
        self.assertEqual(detect_tipo("decreto"), "decreto")
        self.assertEqual(detect_tipo("Medida Provisória"), "medida_provisoria")
        self.assertEqual(detect_tipo("Portaria"), "portaria")

    def test_hierarquia(self):
        self.assertLess(rank_of("constituicao_federal"), rank_of("lei_complementar"))
        self.assertLess(rank_of("lei_complementar"), rank_of("lei_ordinaria"))
        self.assertLess(rank_of("lei_ordinaria"), rank_of("decreto"))
        self.assertLess(rank_of("decreto"), rank_of("portaria"))


class TestVigencia(unittest.TestCase):
    def setUp(self):
        self.normas = _carrega()
        self.by = {n.chave: n for n in self.normas}

    def test_revogacao_bidirecional(self):
        l8666 = self.by["lei_ordinaria-8.666-1993"]
        self.assertEqual(l8666.situacao, REVOGADA)
        self.assertIn("lei_ordinaria-14.133-2021", l8666.revogada_por)
        l10520 = self.by["lei_ordinaria-10.520-2002"]
        self.assertEqual(l10520.situacao, REVOGADA)

    def test_vigentes(self):
        self.assertEqual(self.by["lei_ordinaria-14.133-2021"].situacao, VIGENTE)
        self.assertEqual(self.by["decreto-10.024-2019"].situacao, VIGENTE)
        self.assertEqual(self.by["lei_complementar-123-2006"].situacao, VIGENTE)

    def test_descricao(self):
        d = descricao_situacao(self.by["lei_ordinaria-8.666-1993"], self.normas)
        self.assertIn("REVOGADA por", d)
        self.assertIn("14.133", d)


class TestOrganizer(unittest.TestCase):
    def test_arvore(self):
        normas = _carrega()
        with tempfile.TemporaryDirectory() as tmp:
            stats = organizar(normas, tmp, base_name="Licitações")
            out = Path(tmp)
            self.assertTrue((out / "_INDICE.md").exists())
            self.assertTrue((out / "_INDICE.json").exists())
            self.assertTrue((out / "acervo" / "lei_ordinaria-14.133-2021.md").exists())
            self.assertTrue((out / "revogadas" / "_index.md").exists())
            self.assertTrue((out / "vigentes" / "_index.md").exists())
            self.assertTrue((out / "por-assunto" / "licitacoes" / "_index.md").exists())
            self.assertEqual(stats["revogadas"], 2)
            self.assertEqual(stats["total"], 6)

            idx = (out / "_INDICE.md").read_text(encoding="utf-8")
            # mais recente primeiro: 14.133 (2021) antes de 8.666 (1993)
            self.assertLess(idx.index("14.133"), idx.index("8.666"))
            self.assertIn("REVOGADA por", idx)

            data = {d["chave"]: d for d in json.loads((out / "_INDICE.json").read_text(encoding="utf-8"))}
            self.assertEqual(data["lei_ordinaria-8.666-1993"]["situacao"], REVOGADA)


if __name__ == "__main__":
    unittest.main(verbosity=2)
