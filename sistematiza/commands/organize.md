---
description: Re-gera a organização (índices e pastas) de uma base de normas
argument-hint: "<dir-base>"
allowed-tools: Bash, Read
---
Reorganize o acervo após mudanças no `registry.json`. Argumentos: $ARGUMENTS

1. Execute:
   `python3 ${CLAUDE_PLUGIN_ROOT}/engine/sistematiza.py normas organize <dir>`
2. Mostre o resumo (`total`/`vigentes`/`revogadas`) e o caminho do índice mestre (`_INDICE.md`).
