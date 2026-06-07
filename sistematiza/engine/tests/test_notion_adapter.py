"""Testes do notion_adapter (FONTE Notion). Determinísticos — SEM rede.

Cobrem: roteamento (can_handle), extração/normalização do page_id (com e sem hífens),
conversão de blocos Notion → markdown, e o erro de token ausente. Nenhuma chamada real
à API do Notion é feita — o conversor é exercitado com blocos fake e o caminho de rede
é cortado pelo guard de NOTION_TOKEN (delenv) antes de tocar httpx.
"""
import os
import sys
import unittest
from pathlib import Path

ENGINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ENGINE))

# UUID alvo (mesmo id em forma hifenizada e não-hifenizada nos testes de extração)
_UUID = "abcdef12-3456-7890-abcd-ef1234567890"
_HEX = "abcdef1234567890abcdef1234567890"


def _rt(texto: str) -> list:
    """rich_text fake no formato da API: lista de objetos com plain_text."""
    return [{"plain_text": texto}]


class TestNotionCanHandle(unittest.TestCase):
    def setUp(self):
        from adapters.notion import NotionAdapter
        self.a = NotionAdapter()

    def test_url_notion_so(self):
        self.assertTrue(
            self.a.can_handle("https://www.notion.so/Page-abc123def4567890abc123def4567890")
        )

    def test_url_notion_site(self):
        self.assertTrue(self.a.can_handle("https://x.notion.site/y-abcdef1234567890abcdef1234567890"))

    def test_ref_curta(self):
        self.assertTrue(self.a.can_handle("notion:abc"))

    def test_url_generica_false(self):
        self.assertFalse(self.a.can_handle("https://example.com"))

    def test_caminho_arquivo_false(self):
        self.assertFalse(self.a.can_handle("/tmp/a.pdf"))

    def test_vazio_false(self):
        self.assertFalse(self.a.can_handle(""))


class TestExtractPageId(unittest.TestCase):
    def setUp(self):
        from adapters.notion import NotionAdapter
        self.a = NotionAdapter()

    def test_url_com_id_sem_hifens(self):
        # slug + 32 hex direto → UUID normalizado
        ref = f"https://www.notion.so/workspace/Minha-Pagina-{_HEX}"
        self.assertEqual(self.a._extract_page_id(ref), _UUID)

    def test_url_com_id_hifenizado(self):
        # mesmo id, porém já em forma UUID na URL → mesmo resultado
        ref = f"https://www.notion.so/{_UUID}"
        self.assertEqual(self.a._extract_page_id(ref), _UUID)

    def test_hifenizado_e_nao_hifenizado_convergem(self):
        com = self.a._extract_page_id(f"https://www.notion.so/p-{_UUID}")
        sem = self.a._extract_page_id(f"https://www.notion.so/p-{_HEX}")
        self.assertEqual(com, sem)
        self.assertEqual(com, _UUID)

    def test_ref_curta_notion(self):
        self.assertEqual(self.a._extract_page_id(f"notion:{_HEX}"), _UUID)

    def test_sem_id_levanta(self):
        with self.assertRaises(ValueError):
            self.a._extract_page_id("https://www.notion.so/sem-id-aqui")


class TestBlocksToMarkdown(unittest.TestCase):
    def setUp(self):
        from adapters.notion import NotionAdapter
        self.a = NotionAdapter()

    def test_conversao_tipos_principais(self):
        # lista fake exigida no briefing: paragraph, heading_2, bulleted_list_item, to_do
        blocks = [
            {"type": "heading_2", "heading_2": {"rich_text": _rt("Título 2")}},
            {"type": "paragraph", "paragraph": {"rich_text": _rt("um parágrafo")}},
            {"type": "bulleted_list_item",
             "bulleted_list_item": {"rich_text": _rt("item bala")}},
            {"type": "to_do",
             "to_do": {"rich_text": _rt("tarefa feita"), "checked": True}},
            {"type": "to_do",
             "to_do": {"rich_text": _rt("tarefa pendente"), "checked": False}},
        ]
        md = self.a._blocks_to_markdown(blocks)
        self.assertIn("## Título 2", md)
        self.assertIn("um parágrafo", md)
        self.assertIn("- item bala", md)
        self.assertIn("- [x] tarefa feita", md)
        self.assertIn("- [ ] tarefa pendente", md)

    def test_numbered_quote_code(self):
        blocks = [
            {"type": "numbered_list_item",
             "numbered_list_item": {"rich_text": _rt("primeiro")}},
            {"type": "quote", "quote": {"rich_text": _rt("uma citação")}},
            {"type": "code",
             "code": {"rich_text": _rt("print(1)"), "language": "python"}},
        ]
        md = self.a._blocks_to_markdown(blocks)
        self.assertIn("1. primeiro", md)
        self.assertIn("> uma citação", md)
        self.assertIn("```python", md)
        self.assertIn("print(1)", md)

    def test_heading_1_3_e_callout(self):
        blocks = [
            {"type": "heading_1", "heading_1": {"rich_text": _rt("H1")}},
            {"type": "heading_3", "heading_3": {"rich_text": _rt("H3")}},
            {"type": "callout", "callout": {"rich_text": _rt("aviso")}},
        ]
        md = self.a._blocks_to_markdown(blocks)
        self.assertIn("# H1", md)
        self.assertIn("### H3", md)
        self.assertIn("> aviso", md)

    def test_tipo_desconhecido_ignorado(self):
        # divider não tem rich_text e não está mapeado → não quebra, não aparece
        blocks = [
            {"type": "divider", "divider": {}},
            {"type": "paragraph", "paragraph": {"rich_text": _rt("sobrevivo")}},
        ]
        md = self.a._blocks_to_markdown(blocks)
        self.assertIn("sobrevivo", md)
        self.assertNotIn("divider", md)


class TestTokenAusente(unittest.TestCase):
    def setUp(self):
        from adapters.notion import NotionAdapter
        self.a = NotionAdapter()

    def test_fetch_sem_token_levanta(self):
        # garante NOTION_TOKEN fora do env → fetch deve levantar ValueError ANTES da rede
        original = os.environ.pop("NOTION_TOKEN", None)
        try:
            with self.assertRaises(ValueError) as ctx:
                self.a.fetch(f"https://www.notion.so/p-{_HEX}")
            self.assertIn("NOTION_TOKEN", str(ctx.exception))
        finally:
            if original is not None:
                os.environ["NOTION_TOKEN"] = original

    def test_get_token_vazio_levanta(self):
        original = os.environ.get("NOTION_TOKEN")
        os.environ["NOTION_TOKEN"] = "   "
        try:
            with self.assertRaises(ValueError):
                self.a._get_token()
        finally:
            if original is not None:
                os.environ["NOTION_TOKEN"] = original
            else:
                os.environ.pop("NOTION_TOKEN", None)


if __name__ == "__main__":
    unittest.main(verbosity=2)
