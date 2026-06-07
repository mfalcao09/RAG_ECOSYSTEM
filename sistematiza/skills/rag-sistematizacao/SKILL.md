---
name: rag-sistematizacao
description: Use ao construir ou operar uma base de conhecimento RAG sobre qualquer tema com o plugin Sistematiza (RAG-Anything) — criar base, ingerir PDFs/Office/imagens/texto, consultar por hybrid/local/global, escolher backend (local Ollama/LM Studio vs nuvem) e storage (disco vs Supabase). Triggers: "criar um RAG", "base de conhecimento", "ingerir documentos", "sistematizar pesquisa", "RAG sobre <tema>".
---

# RAG Sistematização (motor RAG-Anything)

CLI: `python3 ${CLAUDE_PLUGIN_ROOT}/engine/sistematiza.py ...`

## Fluxo (modo genérico)
1. **init** — `sistematiza init <dir> --modo generico --backend <b> --storage <s>`
2. **ingest** — `sistematiza ingest <dir> <arquivo|pasta> [--recursive]`
3. **query** — `sistematiza query <dir> "<pergunta>" --mode hybrid`

## Backends (configurável por base)
- **ollama / lmstudio** — 100% local, privado, sem custo. Ideal para docs sensíveis. `doctor` deve mostrar `ollama ✅`; baixe modelos com `ollama pull qwen2.5:7b nomic-embed-text llama3.2-vision`.
- **openai** — `gpt-4o-mini` + `text-embedding-3-large`. Rápido, custo por token. `export OPENAI_API_KEY=...`.
- **claude_openai_emb** — Claude para geração + embeddings OpenAI. `export ANTHROPIC_API_KEY=...` e `OPENAI_API_KEY=...`.
- Chaves SEMPRE via env var (Seção 11), nunca no `.sistematiza.json`.

## Storage (configurável por base)
- **local** — `working_dir` em disco; LightRAG cria `kv/vector/graph/doc_status`. Default.
- **supabase** — Postgres + pgvector (experimental; requer extensão `vector` e schema LightRAG; ajustar nomes de storage em `st_storage.py` conforme a versão).

## Modos de query
`naive` (sem retrieval) · `local` (chunks) · `global` (grafo de entidades) · `hybrid` (recomendado) · `mix` (multimodal amplo) · `bypass` (contexto cru).

## Gotchas (do mapeamento da API)
- 1º parse baixa modelos MinerU (~1GB) — precisa de rede uma vez.
- Imagens exigem `vision_model` no backend; sem ele, são puladas com aviso (não é erro).
- Office (`.docx/.pptx/.xlsx`) exige LibreOffice instalado.
- Python 3.11/3.12 recomendado para o venv do motor (mineru/torch podem não ter wheel p/ 3.14).
- `img_path` em content multimodal deve ser caminho ABSOLUTO.
- O CLI chama `finalize()` ao final para fechar os storages do LightRAG; deixe o asyncio concluir.
