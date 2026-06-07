"""Testes do video_adapter (YouTube). Determinísticos — SEM rede e SEM yt-dlp real.

Cobrem o roteamento estrito (só URLs de YouTube casam; URL genérica e arquivo NÃO)
e o contrato do VideoAdapter (fetch produz content_list com proveniência; ausência de
legenda levanta erro). O parser de VTT é exercitado com strings inline (legenda manual
limpa e legenda auto-gerada ruidosa). A prova E2E real (URL → query) é feita à parte.
"""
import sys
import unittest
from pathlib import Path

ENGINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ENGINE))


class TestVideoCanHandle(unittest.TestCase):
    def setUp(self):
        from adapters.video import VideoAdapter
        self.a = VideoAdapter()

    def test_name(self):
        self.assertEqual(self.a.name, "youtube")

    def test_youtube_watch(self):
        self.assertTrue(self.a.can_handle("https://www.youtube.com/watch?v=abc"))

    def test_youtu_be(self):
        self.assertTrue(self.a.can_handle("https://youtu.be/abc"))

    def test_youtube_shorts(self):
        self.assertTrue(self.a.can_handle("https://youtube.com/shorts/x"))

    def test_m_youtube(self):
        # m.youtube.com (mobile) também é YouTube
        self.assertTrue(self.a.can_handle("https://m.youtube.com/watch?v=abc"))

    def test_generic_url_not_handled(self):
        # URL genérica é do web_adapter, não deste
        self.assertFalse(self.a.can_handle("https://example.com"))

    def test_local_file_not_handled(self):
        self.assertFalse(self.a.can_handle("/tmp/a.pdf"))

    def test_empty_not_handled(self):
        self.assertFalse(self.a.can_handle(""))

    def test_trim_and_case_insensitive(self):
        self.assertTrue(self.a.can_handle("  HTTPS://WWW.YOUTUBE.COM/watch?v=AbC  "))


class TestVideoFetch(unittest.TestCase):
    def setUp(self):
        from adapters.video import VideoAdapter
        self.a = VideoAdapter()

    def test_fetch_produces_block_with_provenance(self):
        # mocka a captura interna (yt-dlp + parse) — sem rede nem binário
        self.a._capture = lambda url: ("Título Fake do Vídeo", "transcrição fake limpa.")
        blocks = self.a.fetch("https://www.youtube.com/watch?v=XYZ")
        self.assertEqual(len(blocks), 1)
        self.assertEqual(blocks[0]["type"], "text")
        self.assertEqual(blocks[0]["page_idx"], 0)
        texto = blocks[0]["text"]
        self.assertIn("transcrição fake limpa.", texto)               # corpo
        self.assertIn("https://www.youtube.com/watch?v=XYZ", texto)   # proveniência (URL)
        self.assertIn("Título Fake do Vídeo", texto)                  # proveniência (título)

    def test_fetch_no_subtitles_raises(self):
        # sem legenda → transcrição vazia → ValueError claro
        self.a._capture = lambda url: ("Título", None)
        with self.assertRaises(ValueError):
            self.a.fetch("https://youtu.be/semlegenda")

    def test_fetch_empty_transcript_raises(self):
        self.a._capture = lambda url: ("Título", "   ")
        with self.assertRaises(ValueError):
            self.a.fetch("https://youtu.be/vazio")

    def test_fetch_missing_title_falls_back(self):
        # título ausente não quebra fetch — usa placeholder
        self.a._capture = lambda url: (None, "conteúdo presente.")
        blocks = self.a.fetch("https://www.youtube.com/watch?v=AAA")
        self.assertIn("(sem título)", blocks[0]["text"])
        self.assertIn("conteúdo presente.", blocks[0]["text"])


class TestVttParser(unittest.TestCase):
    def setUp(self):
        from adapters.video import VideoAdapter
        self.a = VideoAdapter()

    def test_parse_manual_vtt(self):
        # legenda manual limpa (formato confirmado em vídeo real)
        vtt = (
            "WEBVTT\n"
            "Kind: captions\n"
            "Language: en\n"
            "\n"
            "00:00:04.220 --> 00:00:05.400\n"
            "This is a 3.\n"
            "\n"
            "00:00:06.060 --> 00:00:10.713\n"
            "It's sloppily written.\n"
        )
        out = self.a._parse_vtt(vtt)
        self.assertEqual(out, "This is a 3.\nIt's sloppily written.")
        # garante que NADA de timestamp/metadado vazou
        self.assertNotIn("WEBVTT", out)
        self.assertNotIn("-->", out)
        self.assertNotIn("Kind:", out)

    def test_parse_auto_vtt_strips_tags_and_dedupes(self):
        # legenda auto-gerada: cue settings, timestamps inline, tags <c> e duplicação em rolagem
        vtt = (
            "WEBVTT\n"
            "Kind: captions\n"
            "Language: pt\n"
            "\n"
            "00:00:00.000 --> 00:00:02.000 align:start position:0%\n"
            "olá <00:00:00.480><c>mundo</c>\n"
            "\n"
            "00:00:02.000 --> 00:00:04.000 align:start position:0%\n"
            "olá mundo\n"
            "olá mundo como vai\n"
        )
        out = self.a._parse_vtt(vtt)
        # tags e timestamps inline removidos; "olá mundo" duplicado consecutivo colapsado
        self.assertEqual(out, "olá mundo\nolá mundo como vai")
        self.assertNotIn("<c>", out)
        self.assertNotIn("position:0%", out)
        self.assertNotIn("00:00:00.480", out)

    def test_parse_empty_vtt_returns_empty(self):
        out = self.a._parse_vtt("WEBVTT\n\n")
        self.assertEqual(out, "")


if __name__ == "__main__":
    unittest.main(verbosity=2)
