"""Testes da camada de ingest adapters (FONTES). Determinísticos — sem rede.

Cobrem o roteamento (URL → web_adapter; arquivo → None) e o contrato do WebAdapter
(can_handle, fetch produz content_list com proveniência, vazio levanta erro). A prova
E2E real (URL → query) é feita à parte; aqui travamos a mecânica de roteamento.
"""
import sys
import unittest
from pathlib import Path

ENGINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ENGINE))


class TestAdapterRouting(unittest.TestCase):
    def setUp(self):
        import adapters
        self.adapters = adapters

    def test_url_resolves_to_web(self):
        a = self.adapters.resolve("https://example.com")
        self.assertIsNotNone(a)
        self.assertEqual(a.name, "web")

    def test_http_also_resolves(self):
        self.assertEqual(self.adapters.resolve("http://x.org").name, "web")

    def test_local_file_not_handled(self):
        # arquivos/pastas locais NÃO são adapter → seguem para o parser MinerU
        self.assertIsNone(self.adapters.resolve("/tmp/x.pdf"))
        self.assertIsNone(self.adapters.resolve("./docs/a.md"))

    def test_web_registered(self):
        self.assertIn("web", self.adapters.list_adapters())


class TestWebAdapter(unittest.TestCase):
    def setUp(self):
        from adapters.web import WebAdapter
        self.a = WebAdapter()

    def test_can_handle(self):
        self.assertTrue(self.a.can_handle("https://x.com"))
        self.assertTrue(self.a.can_handle("  HTTP://X.com/p  "))  # trim + case-insensitive
        self.assertFalse(self.a.can_handle("/path/file.pdf"))
        self.assertFalse(self.a.can_handle(""))
        self.assertFalse(self.a.can_handle("ftp://x"))

    def test_fetch_produces_block_with_provenance(self):
        # mocka o motor de extração — sem rede
        self.a._extract_trafilatura = lambda url: "# Título\n\nconteúdo de teste do site."
        blocks = self.a.fetch("https://x.com/artigo")
        self.assertEqual(len(blocks), 1)
        self.assertEqual(blocks[0]["type"], "text")
        self.assertEqual(blocks[0]["page_idx"], 0)
        self.assertIn("conteúdo de teste", blocks[0]["text"])
        self.assertIn("https://x.com/artigo", blocks[0]["text"])  # proveniência ancorada

    def test_empty_extraction_raises(self):
        self.a._extract_trafilatura = lambda url: None
        self.a._extract_bs4 = lambda url: ""
        with self.assertRaises(ValueError):
            self.a.fetch("https://x.com")


if __name__ == "__main__":
    unittest.main(verbosity=2)
