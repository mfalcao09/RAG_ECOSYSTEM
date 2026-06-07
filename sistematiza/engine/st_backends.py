"""Constrói as 3 funções (llm, vision, embedding) exigidas pelo RAG-Anything.

Import PREGUIÇOSO: nada de lightrag no topo, para o CLI rodar sem deps pesadas
nas operações que não precisam (init, normas, status, doctor).

SEGURANÇA (Seção 11): segredos vêm SEMPRE de variável de ambiente; nunca do
arquivo de config nem hardcoded. Para servidores locais (ollama/lm-studio) usa-se
um token não-secreto literal.

Assinaturas conforme a fonte real do RAG-Anything/LightRAG (validadas em revisão):
  - llm/vision: funções SÍNCRONAS que retornam a coroutine de openai_complete_if_cache
    (o LightRAG faz `await` no retorno) — é o padrão de todos os exemplos oficiais.
  - embedding: `openai_embed` é um EmbeddingFunc; usa-se `openai_embed.func(...)`.
"""
from __future__ import annotations
import os
from typing import Tuple, Callable, Any, Optional


def _resolve_key(backend: dict, env_field: str = "api_key_env") -> str:
    env_name = backend.get(env_field) or ""
    if env_name:
        val = os.environ.get(env_name)
        if not val:
            raise EnvironmentError(
                f"Variável de ambiente {env_name} não definida. Exporte-a antes de "
                f"ingerir/consultar (NUNCA coloque a chave no .sistematiza.json)."
            )
        return val
    return backend.get("api_key_literal") or "EMPTY"


def build_funcs(config) -> Tuple[Callable, Optional[Callable], Any]:
    backend = config.backend
    provider = backend.get("provider", "ollama")

    # imports pesados só agora (lazy)
    from lightrag.llm.openai import openai_complete_if_cache, openai_embed
    from lightrag.utils import EmbeddingFunc

    api_key = _resolve_key(backend)                     # chave de embeddings/openai-compat
    base_url = backend.get("base_url")
    llm_model = backend.get("llm_model")
    emb_model = backend.get("embedding_model")
    emb_dim = int(backend.get("embedding_dim", 768))

    # provider claude_openai_emb: LLM aponta p/ endpoint próprio; embeddings p/ openai
    llm_base_url = backend.get("llm_base_url", base_url)
    llm_api_key = api_key
    if backend.get("llm_api_key_env"):
        llm_api_key = _resolve_key(backend, "llm_api_key_env")

    # SÍNCRONAS retornando a coroutine (padrão dos exemplos oficiais; LightRAG faz await).
    def llm_model_func(prompt, system_prompt=None, history_messages=None, **kwargs):
        return openai_complete_if_cache(
            llm_model, prompt,
            system_prompt=system_prompt,
            history_messages=history_messages or [],
            api_key=llm_api_key, base_url=llm_base_url, **kwargs,
        )

    vision_model = backend.get("vision_model") or ""
    vision_func = None
    if vision_model:
        def vision_model_func(prompt, system_prompt=None, history_messages=None,
                              image_data=None, messages=None, **kwargs):
            if messages:                                # formato VLM completo
                return openai_complete_if_cache(
                    vision_model, "", system_prompt=None, history_messages=[],
                    messages=messages, api_key=llm_api_key, base_url=llm_base_url, **kwargs,
                )
            if image_data:                              # imagem única base64
                mm = []
                if system_prompt:
                    mm.append({"role": "system", "content": system_prompt})
                mm.append({"role": "user", "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url",
                     "image_url": {"url": f"data:image/jpeg;base64,{image_data}"}},
                ]})
                return openai_complete_if_cache(
                    vision_model, "", system_prompt=None, history_messages=[],
                    messages=mm, api_key=llm_api_key, base_url=llm_base_url, **kwargs,
                )
            return llm_model_func(prompt, system_prompt, history_messages, **kwargs)
        vision_func = vision_model_func

    # LightRAG (EmbeddingFunc) exige numpy.ndarray no retorno — valida a dimensão via
    # `result.size`. Listas cruas quebram com "'list' object has no attribute 'size'"
    # (regressão que o smoke com mock não pega; só aparece com backend real).
    import numpy as np
    if provider == "ollama":
        async def _embed(texts):
            import ollama
            host = (base_url or "http://localhost:11434/v1").replace("/v1", "")
            client = ollama.AsyncClient(host=host)
            resp = await client.embed(model=emb_model, input=texts)
            embs = resp.embeddings if hasattr(resp, "embeddings") else resp["embeddings"]
            return np.array(embs, dtype=np.float32)
    else:
        async def _embed(texts):
            # openai_embed é um EmbeddingFunc; a função real é openai_embed.func
            out = await openai_embed.func(
                texts, model=emb_model, api_key=api_key, base_url=base_url,
            )
            return np.asarray(out, dtype=np.float32)

    embedding_func = EmbeddingFunc(embedding_dim=emb_dim, max_token_size=8192, func=_embed)
    return llm_model_func, vision_func, embedding_func
