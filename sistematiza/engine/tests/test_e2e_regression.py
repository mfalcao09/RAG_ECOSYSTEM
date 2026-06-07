"""Regressões REAIS do E2E (Ollama + MinerU) que o smoke com mock NÃO cobria.

Três bugs encadeados, todos só visíveis com backend real — ver tasks/lessons.md:
  1. embedding (ollama) devolvia list; o LightRAG faz `result.size` → exige np.ndarray.
  2. ingest não forçava o backend MinerU 'pipeline' (o default 'hybrid-auto-engine'
     carrega o VLM e estoura a RAM em máquinas sem GPU forte → OOM em 'Predict: 0%').
  3. query usava system_prompt, que SUBSTITUI o template e leva embora o {content_data}
     (o contexto recuperado) → o LLM responde "sem informação". O certo é user_prompt.
"""
import asyncio
import sys
import tempfile
import types
import unittest
from pathlib import Path

import numpy as np

ENGINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ENGINE))


def _fake_lightrag_modules():
    """Mocka o mínimo de lightrag para build_funcs importar sem deps pesadas."""
    class _FakeEmbeddingFunc:
        def __init__(self, embedding_dim=None, max_token_size=None, func=None):
            self.embedding_dim = embedding_dim
            self.max_token_size = max_token_size
            self.func = func

    async def fake_complete(model, prompt, **kw):
        return "ok"

    class _FakeEmbed:
        async def func(self, texts, **kw):
            return [[0.0] * 4 for _ in texts]

    pkg = types.ModuleType("lightrag")
    llm = types.ModuleType("lightrag.llm")
    openai_mod = types.ModuleType("lightrag.llm.openai")
    openai_mod.openai_complete_if_cache = fake_complete
    openai_mod.openai_embed = _FakeEmbed()
    utils = types.ModuleType("lightrag.utils")
    utils.EmbeddingFunc = _FakeEmbeddingFunc
    return {
        "lightrag": pkg,
        "lightrag.llm": llm,
        "lightrag.llm.openai": openai_mod,
        "lightrag.utils": utils,
    }


class TestEmbeddingReturnsNdarray(unittest.TestCase):
    """Bug #1: o branch ollama precisa devolver np.ndarray (NanoVectorDB faz `.size`)."""

    def setUp(self):
        # SDK ollama falsa: client.embed(...) devolve objeto com .embeddings (como a real)
        fake = types.ModuleType("ollama")

        class _Resp:
            embeddings = [[0.1] * 8, [0.2] * 8]

        class _AsyncClient:
            def __init__(self, host=None):
                pass

            async def embed(self, model=None, input=None):
                return _Resp()

        fake.AsyncClient = _AsyncClient
        sys.modules["ollama"] = fake
        self._lr = _fake_lightrag_modules()
        sys.modules.update(self._lr)

    def tearDown(self):
        sys.modules.pop("ollama", None)
        for m in self._lr:
            sys.modules.pop(m, None)

    def test_ollama_embed_returns_ndarray(self):
        import st_backends
        import st_config
        cfg = st_config.make_config("t", "generico", "ollama", "local", "./rs")
        _llm, _vision, emb = st_backends.build_funcs(cfg)
        out = asyncio.run(emb.func(["a", "b"]))
        self.assertIsInstance(out, np.ndarray)   # não list!
        self.assertTrue(hasattr(out, "size"))    # exatamente o que o LightRAG acessa
        self.assertEqual(out.shape[0], 2)


class TestConfigMineruBackend(unittest.TestCase):
    """Bug #2: default 'pipeline' (leve/CPU) e persistência por base."""

    def test_default_is_pipeline(self):
        import st_config
        self.assertEqual(st_config.BaseConfig().mineru_backend, "pipeline")

    def test_load_preserva_backend(self):
        import st_config
        with tempfile.TemporaryDirectory() as d:
            cfg = st_config.make_config("t", "generico", "ollama", "local", "./rs")
            cfg.mineru_backend = "vlm-auto-engine"
            cfg.save(d)
            self.assertEqual(st_config.BaseConfig.load(d).mineru_backend, "vlm-auto-engine")


class TestQueryGuardWiring(unittest.TestCase):
    """Bugs #2/#3 no nível do CLI (source-check, sem rodar o motor pesado)."""

    SRC = (ENGINE / "sistematiza.py").read_text(encoding="utf-8")

    def test_query_usa_user_prompt(self):
        self.assertIn("user_prompt=QUERY_GUARD", self.SRC)

    def test_query_nao_usa_system_prompt(self):
        # system_prompt customizado substitui o template e leva o contexto embora
        self.assertNotIn("system_prompt=SYSTEM_GUARD", self.SRC)
        self.assertNotIn("system_prompt=QUERY_GUARD", self.SRC)

    def test_ingest_forca_backend_mineru(self):
        self.assertIn('parser_kw["backend"] = _cfg.mineru_backend', self.SRC)


if __name__ == "__main__":
    unittest.main(verbosity=2)
