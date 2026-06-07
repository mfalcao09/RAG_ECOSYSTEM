"""Configuração por base de conhecimento (.sistematiza.json).

Backend e storage são escolhidos POR BASE (decisão de Marcelo: "configurável por
projeto" / "decidir por base"). Segredos NUNCA ficam aqui — apenas o NOME da
variável de ambiente que os contém (Seção 11 do CLAUDE.md).
"""
from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Dict, Any
from pathlib import Path
import json

CONFIG_FILENAME = ".sistematiza.json"

# Presets de backend. `api_key_env` = NOME da env var com o segredo (nunca o segredo).
# `api_key_literal` = valor não-secreto exigido por servidores locais (ollama/lm-studio).
BACKEND_PRESETS: Dict[str, Dict[str, Any]] = {
    "ollama": {
        "provider": "ollama",
        "llm_model": "qwen2.5:3b",
        "vision_model": "llama3.2-vision",
        "embedding_model": "bge-m3",
        "embedding_dim": 1024,
        "base_url": "http://localhost:11434/v1",
        "api_key_env": "",
        "api_key_literal": "ollama",
    },
    "lmstudio": {
        "provider": "lmstudio",
        "llm_model": "openai/gpt-oss-20b",
        "vision_model": "",
        "embedding_model": "text-embedding-nomic-embed-text-v1.5",
        "embedding_dim": 768,
        "base_url": "http://localhost:1234/v1",
        "api_key_env": "",
        "api_key_literal": "lm-studio",
    },
    "openai": {
        "provider": "openai",
        "llm_model": "gpt-4o-mini",
        "vision_model": "gpt-4o",
        "embedding_model": "text-embedding-3-large",
        "embedding_dim": 3072,
        "base_url": "https://api.openai.com/v1",
        "api_key_env": "OPENAI_API_KEY",
        "api_key_literal": "",
    },
    "claude_openai_emb": {
        "provider": "claude_openai_emb",
        "llm_model": "claude-opus-4-8",
        "vision_model": "claude-opus-4-8",
        "embedding_model": "text-embedding-3-large",
        "embedding_dim": 3072,
        "base_url": "https://api.openai.com/v1",
        "llm_base_url": "https://api.anthropic.com/v1",
        "api_key_env": "OPENAI_API_KEY",
        "llm_api_key_env": "ANTHROPIC_API_KEY",
        "api_key_literal": "",
    },
}


@dataclass
class BaseConfig:
    base_name: str = "base"
    modo: str = "generico"                 # generico | normas
    backend: Dict[str, Any] = field(default_factory=lambda: dict(BACKEND_PRESETS["ollama"]))
    storage: Dict[str, Any] = field(default_factory=lambda: {"kind": "local", "working_dir": "./rag_storage"})
    parser: str = "mineru"                 # mineru | docling
    parse_method: str = "auto"             # auto | txt | ocr  (aplica a pipeline/hybrid-*)
    # Backend do MinerU 3.x. "pipeline" = leve, roda em CPU (default seguro p/ máquinas
    # sem GPU forte). "hybrid-auto-engine"/"vlm-auto-engine" = alta acurácia via VLM, mas
    # exigem VRAM — em RAM apertada estouram (OOM em "Predict: 0%"). Configurável por base.
    mineru_backend: str = "pipeline"

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False, indent=2)

    @classmethod
    def load(cls, base_dir: str) -> "BaseConfig":
        p = Path(base_dir) / CONFIG_FILENAME
        if not p.exists():
            raise FileNotFoundError(
                f"Config não encontrada: {p}. Rode 'sistematiza init <base>' primeiro."
            )
        d = json.loads(p.read_text(encoding="utf-8"))
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})

    def save(self, base_dir: str) -> Path:
        Path(base_dir).mkdir(parents=True, exist_ok=True)
        p = Path(base_dir) / CONFIG_FILENAME
        p.write_text(self.to_json(), encoding="utf-8")
        return p


def make_config(base_name: str, modo: str, backend: str,
                storage_kind: str, working_dir: str) -> BaseConfig:
    cfg = BaseConfig(
        base_name=base_name,
        modo=modo,
        backend=dict(BACKEND_PRESETS.get(backend, BACKEND_PRESETS["ollama"])),
    )
    cfg.storage = {"kind": storage_kind, "working_dir": working_dir}
    if storage_kind == "supabase":
        cfg.storage.update({
            "postgres_host_env": "SUPABASE_DB_HOST",
            "postgres_db_env": "SUPABASE_DB_NAME",
            "postgres_user_env": "SUPABASE_DB_USER",
            "postgres_password_env": "SUPABASE_DB_PASSWORD",
            "note": "Backend pgvector — requer extensão `vector` e tabelas LightRAG (ver README).",
        })
    return cfg
