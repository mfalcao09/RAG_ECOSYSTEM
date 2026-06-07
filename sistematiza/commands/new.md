---
description: Cria uma nova base de conhecimento Sistematiza (RAG genérico ou modo normas jurídicas)
argument-hint: "<nome> [generico|normas]"
allowed-tools: Bash, Read, Write
---
Crie uma base de conhecimento Sistematiza. Argumentos: $ARGUMENTS

Passos:
1. Defina o diretório da base (default `./<nome>` no diretório atual) e o modo (`generico` ou `normas`; default `generico`).
2. Backend e storage: use `ollama` + `local` por padrão (privado/offline). Se o usuário indicar nuvem, use `openai` ou `claude_openai_emb` e confirme que a env var da chave existe (`OPENAI_API_KEY`/`ANTHROPIC_API_KEY`) — nunca grave a chave no config.
3. Execute:
   `python3 ${CLAUDE_PLUGIN_ROOT}/engine/sistematiza.py init <dir> --name "<nome>" --modo <modo> --backend <backend> --storage <storage>`
4. Mostre a saída e os próximos passos. Se `modo=normas`, ofereça ajudar a montar o `registry.json` (carregue a skill `normas-juridicas`).
