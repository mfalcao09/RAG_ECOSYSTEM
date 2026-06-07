---
description: Mostra o status de uma base Sistematiza e diagnostica o motor RAG
argument-hint: "<dir-base>"
allowed-tools: Bash, Read
---
Status da base. Argumentos: $ARGUMENTS

1. `python3 ${CLAUDE_PLUGIN_ROOT}/engine/sistematiza.py status <dir>`
2. `python3 ${CLAUDE_PLUGIN_ROOT}/engine/sistematiza.py doctor`
3. Resuma e aponte pendências (ex.: backend não instalado → ver `setup.sh` no README).
