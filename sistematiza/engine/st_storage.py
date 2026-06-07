"""Resolve working_dir e lightrag_kwargs conforme o storage escolhido na base.

- local: apenas um working_dir em disco (LightRAG cria kv/vector/graph/doc_status).
- supabase: exporta as envs que o LightRAG espera e seleciona os PG storages.

SEGURANÇA: o working_dir é validado para ficar DENTRO do diretório da base
(anti path-traversal — um .sistematiza.json malicioso não pode redirecionar a
escrita para fora da base).

O caminho supabase é EXPERIMENTAL: requer a extensão `vector` e o backend
postgres do LightRAG. Tentamos importar as CLASSES de storage reais; se não
estiverem instaladas, caímos para os nomes em string (interface alternativa).
"""
from __future__ import annotations
import os
from pathlib import Path
from typing import Tuple, Dict, Any

_PG_STRINGS = {
    "kv_storage": "PGKVStorage",
    "vector_storage": "PGVectorStorage",
    "graph_storage": "PGGraphStorage",
    "doc_status_storage": "PGDocStatusStorage",
}


def _dentro_da_base(caminho: str, base_dir: str) -> bool:
    c = os.path.abspath(caminho)
    b = os.path.abspath(base_dir)
    return c == b or c.startswith(b + os.sep)


def _pg_storages() -> Dict[str, Any]:
    """Classes de storage do Postgres; cai para strings se a lib não estiver instalada."""
    try:
        from lightrag.kg.postgres_impl import (  # type: ignore
            PGKVStorage, PGVectorStorage, PGGraphStorage, PGDocStatusStorage,
        )
        return {
            "kv_storage": PGKVStorage,
            "vector_storage": PGVectorStorage,
            "graph_storage": PGGraphStorage,
            "doc_status_storage": PGDocStatusStorage,
        }
    except Exception:
        # backend postgres não instalado nesta versão do LightRAG → tenta por nome
        return dict(_PG_STRINGS)


def resolve(config, base_dir: str) -> Tuple[str, Dict[str, Any]]:
    st = config.storage or {}
    kind = st.get("kind", "local")

    wd = st.get("working_dir") or "./rag_storage"
    if not os.path.isabs(wd):
        wd = str(Path(base_dir) / wd)
    if not _dentro_da_base(wd, base_dir):
        raise ValueError(
            f"working_dir resolve para fora da base ({os.path.abspath(wd)}). "
            f"Use um caminho relativo dentro de {os.path.abspath(base_dir)}."
        )
    Path(wd).mkdir(parents=True, exist_ok=True)

    if kind == "local":
        return wd, {}

    if kind == "supabase":
        for cfg_field, env_name in [
            ("postgres_host_env", "POSTGRES_HOST"),
            ("postgres_db_env", "POSTGRES_DATABASE"),
            ("postgres_user_env", "POSTGRES_USER"),
            ("postgres_password_env", "POSTGRES_PASSWORD"),
        ]:
            src = st.get(cfg_field)
            if src and os.environ.get(src):
                os.environ[env_name] = os.environ[src]
        return wd, _pg_storages()

    raise ValueError(f"storage.kind desconhecido: {kind!r} (use 'local' ou 'supabase')")
