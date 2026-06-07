---
description: Organiza normas jurídicas — importa, calcula vigência/revogação e gera a árvore de pastas/índices
argument-hint: "<dir-base> [normas.json]"
allowed-tools: Bash, Read, Write, Edit
---
Organize o acervo normativo. Argumentos: $ARGUMENTS

Carregue a skill `normas-juridicas` para o schema completo e a inteligência de vigência.

1. **Montar o registry** (se o usuário forneceu fontes — PDFs/links/lista de leis — e ainda não há `registry.json`): ajude a construir `<dir>/normas/registry.json`, uma entrada por norma com `tipo, numero, ano, data (ISO), orgao, ementa, assuntos[]` e relações `revoga`/`revoga_parcialmente` referenciando a CHAVE `<tipo>-<numero>-<ano>`. **NUNCA invente** número/ano/revogação; registre incertezas em `observacoes`.
2. **Importar** (se veio um JSON pronto):
   `python3 ${CLAUDE_PLUGIN_ROOT}/engine/sistematiza.py normas import <dir> <normas.json>`
3. **Organizar**:
   `python3 ${CLAUDE_PLUGIN_ROOT}/engine/sistematiza.py normas organize <dir>`
4. Mostre o `_INDICE.md` (mais recente primeiro; revogadas ⛔ com a norma revogadora) e as facetas geradas (`por-assunto/`, `por-tipo/`, `por-orgao/`, `por-ano/`, `vigentes/`, `revogadas/`).
