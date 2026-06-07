---
description: Consulta o RAG de uma base (modos naive/local/global/hybrid/mix)
argument-hint: "<dir-base> \"<pergunta>\" [--mode hybrid]"
allowed-tools: Bash, Read
---
Consulte o RAG de uma base. Argumentos: $ARGUMENTS

1. Execute:
   `python3 ${CLAUDE_PLUGIN_ROOT}/engine/sistematiza.py query <dir> "<pergunta>" --mode <modo>`
   Default `hybrid`. Use `mix` para multimodal amplo, `local` para focar nos chunks, `global` para o grafo de entidades.
2. Apresente a resposta. Se vier vazia, sugira reingestão (`/sistematiza:ingest`) ou outro modo.
