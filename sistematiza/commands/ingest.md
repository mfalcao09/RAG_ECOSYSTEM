---
description: Ingere documentos (PDF/Office/imagens/texto) no RAG de uma base
argument-hint: "<dir-base> <arquivo|pasta> [--recursive]"
allowed-tools: Bash, Read
---
Ingira documentos no RAG. Argumentos: $ARGUMENTS

1. Rode `python3 ${CLAUDE_PLUGIN_ROOT}/engine/sistematiza.py doctor` para confirmar o backend. Se `raganything`/`mineru` faltarem, oriente: ative o venv e rode `setup.sh` (ver README). Para backend de nuvem, `export <ENV_VAR>=...` antes.
2. Execute:
   `python3 ${CLAUDE_PLUGIN_ROOT}/engine/sistematiza.py ingest <dir> <paths...> [--recursive]`
3. Avise o usuário: o 1º parse baixa modelos MinerU (~1GB, precisa de rede uma vez); documentos Office exigem LibreOffice instalado.
4. Reporte o resultado e sugira uma consulta de teste (`/sistematiza:query`).
