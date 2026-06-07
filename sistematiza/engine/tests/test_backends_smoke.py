"""Smoke de wiring do motor RAG com lightrag MOCKADO (zero deps pesadas).

Valida a FORMA das chamadas ao backend sem baixar modelos nem chamar API —
pega regressões de assinatura (ex.: usar openai_embed.func, retornar List[List[float]]).
"""
import asyncio
import os
import sys
import types
import unittest
from pathlib import Path

ENGINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ENGINE))

_CALLS = {}


class _FakeEmbeddingFunc:
    def __init__(self, embedding_dim=None, max_token_size=None, func=None):
        self.embedding_dim = embedding_dim
        self.max_token_size = max_token_size
        self.func = func


def _make_fake_lightrag():
    async def fake_complete(model, prompt, **kw):
        _CALLS["complete"] = {"model": model, "prompt": prompt, "kw": kw}
        return "resposta"

    class _FakeEmbed:
        async def func(self, texts, **kw):
            _CALLS["embed"] = {"texts": list(texts), "kw": kw}
            return [[0.0, 0.1, 0.2] for _ in texts]

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


class TestBackendsWiring(unittest.TestCase):
    def setUp(self):
        self._fakes = _make_fake_lightrag()
        sys.modules.update(self._fakes)
        os.environ["OPENAI_API_KEY"] = "test-key"

    def tearDown(self):
        for m in self._fakes:
            sys.modules.pop(m, None)

    def test_openai_embed_usa_func_e_retorna_lista(self):
        import st_config
        import st_backends
        cfg = st_config.make_config("t", "generico", "openai", "local", "./rs")
        llm, vision, emb = st_backends.build_funcs(cfg)
        self.assertTrue(callable(llm))
        self.assertEqual(emb.embedding_dim, 3072)
        out = asyncio.run(emb.func(["a", "b"]))
        self.assertEqual(len(out), 2)
        self.assertEqual(len(out[0]), 3)
        self.assertIn("embed", _CALLS)
        self.assertEqual(_CALLS["embed"]["kw"].get("model"), "text-embedding-3-large")

    def test_llm_func_retorna_coroutine(self):
        import st_config
        import st_backends
        cfg = st_config.make_config("t", "generico", "openai", "local", "./rs")
        llm, _v, _e = st_backends.build_funcs(cfg)
        coro = llm("oi")            # função síncrona retorna coroutine
        self.assertTrue(asyncio.iscoroutine(coro))
        self.assertEqual(asyncio.run(coro), "resposta")


if __name__ == "__main__":
    unittest.main(verbosity=2)
