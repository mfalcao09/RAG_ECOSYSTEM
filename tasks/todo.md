# tasks/todo.md — Sistematiza (Entregável 1)

> Plano da sessão 2026-06-06. Plugin + agente Claude Code sobre RAG-Anything,
> com organização jurídica de normas como feature de 1ª classe.

## Decisões (de Marcelo, via AskUserQuestion)
- Deliverable: **Entregável 1 agora** (plugin CC orquestra RAG local); Entregável 2 (agente VPS permanente) = plano apartado.
- Backend: **configurável por base** (ollama/lmstudio/openai/claude_openai_emb).
- Storage: **decidir por base** (local/supabase).
- Camada jurídica: **feature de 1ª classe** (vigência/revogação/hierarquia).

## Plano (verificável — Seção 8.3)
- [x] Mapear API real do RAG-Anything (subagente Explore) → verifica: relatório com assinaturas exatas ✔
- [x] Subsistema jurídico `normas/` (taxonomy/model/vigencia/organizer) → verifica: 6/6 testes unitários ✔
- [x] CLI `sistematiza.py` (init/normas/ingest/query/status/doctor, lazy import) → verifica: `--help` + smoke ✔
- [x] Backends configuráveis (`st_backends.py`) → verifica: py_compile + assinaturas conforme mapa ✔
- [x] Storage por base (`st_storage.py`, local/supabase) → verifica: py_compile + local testado no smoke ✔
- [x] Wrapper do plugin: `plugin.json`, `marketplace.json`, agente, 6 commands, 2 skills → verifica: plugin-validator
- [x] `setup.sh`, `.gitignore`, template de config → verifica: leitura + sem segredos versionáveis
- [x] README `.md` + `.html` pareados (Seção 4)
- [x] Verificação multi-agente (estrutura + python vs API real + segurança + completude)
- [x] Correção dos 10 achados reais da revisão (2 críticos + 3 altos + segurança + completude)
- [x] Plano do Entregável 2 (agente VPS) em `.md` + `.html`

## Review v2 (pós-revisão adversarial)
Revisão multi-agente (4 perspectivas, 355k tokens) deu correção=FAIL → corrigido tudo:
- 🔴 `finalize()`→`finalize_storages()`; `openai_embed`→`.func()`
- 🟠 `query` agora chama `_ensure_lightrag_initialized()`; storage supabase usa classes PG (lazy); ollama `resp.embeddings`
- 🔒 path-traversal em `working_dir`/`--out` validados; system-guard + cap anti prompt-injection na query
- 🧩 faceta `por-situacao/` (cobre vacatio/parcial); comando `normas extract` (heurístico→conferência); título via `cfg.base_name`; aviso de referências órfãs
- ✅ +3 testes (extractor, backends-mock, cobertura) → **11/11 verdes**; `__pycache__` limpo

## Review
**Prova de funcionamento (smoke real em /tmp):**
- `py_compile`: OK (10 arquivos)
- `unittest`: 6/6 PASS
- `init` → `normas import` (6) → `normas organize`: total=6, vigentes=4, revogadas=2
- `_INDICE.md`: ordenado mais-recente-primeiro; Lei 8.666/1993 e 10.520/2002 marcadas
  **⛔ REVOGADA por Lei Ordinária nº 14.133/2021 (2021)**
- Pastas: `acervo/ por-assunto/ por-tipo/ por-orgao/ por-ano/ vigentes/ revogadas/`
- `doctor`: degrada graciosamente sem o RAG pesado (lazy import confirmado)

**Pendências conhecidas:** ingest/query dependem de backend ativo (não exercitado end-to-end
nesta sessão — exige venv 3.11/3.12 + modelos MinerU ~1GB). Caminho supabase é experimental.

## Review v3 — E2E RAG documental FECHADO (2026-06-06)

A pendência "ingest/query end-to-end" foi resolvida. Prova real com stack 100% local
(Ollama `qwen2.5:3b` + `bge-m3`, MinerU 3.2.3), doc de teste com fato único verificável.

**3 bugs encadeados corrigidos (só visíveis com backend real — o smoke com mock não pegava):**
1. 🔴 **MinerU backend** — o default do MinerU 3.x é `hybrid-auto-engine` (VLM), que estoura
   a RAM (OOM em `Predict: 0%`). Novo campo `mineru_backend="pipeline"` em `st_config`
   (leve, CPU; configurável por base) + `cmd_ingest` passa `backend=` ao parser.
2. 🔴 **Embedding** — o branch ollama devolvia `list`; o LightRAG faz `result.size` → exige
   `np.ndarray`. `st_backends._embed` agora retorna `np.array(...)`. Quebrava o flush do
   `NanoVectorDBStorage[entities]` (os `vdb_*.json` nem eram gerados).
3. 🔴 **Query** — `system_prompt=SYSTEM_GUARD` SUBSTITUÍA o template `naive_rag_response`,
   levando embora o placeholder `{content_data}` (o contexto). O LLM respondia "sem
   informação". Corrigido para `user_prompt=QUERY_GUARD` (QueryParam) — preserva o contexto.

**Prova:** ingest → working_dir populado (grafo 11 nós/2 arestas + `vdb_chunks/entities/relationships.json`);
query (hybrid e naive) recupera os fatos do doc (orçamento R$ 4.880.000, coordenadora, data,
cidade) com `References: doc-teste-sistematiza.pdf`. Sem OOM (RAM estável ~120 MB livre;
199s ingest / ~50s query). **+3 testes de regressão (`test_e2e_regression.py`) → 19/19 verdes.**

**Pendências restantes:** (a) repo **SEM git** inicializado (risco de perda); (b) `README.html`
precisa re-render do `.md`; (c) storage supabase ainda experimental; (d) `qwen2.5:3b` (3B) comete
pequenos erros de transcrição ("quatro milhão") — modelo maior melhora a fidelidade.

## Review v4 — Camada de ingest adapters + web_adapter (2026-06-07)

Início da virada "sistematiza" (arquivos) → **RAG_ECOSYSTEM** (qualquer fonte). Ver `docs/ARSENAL-RAG.md`.

**Entregue:**
- Versionado em `github.com/mfalcao09/RAG_ECOSYSTEM` (commits `022bc57`, `03c4ee2`, …) — sem segredos; `.venv`/`output` ignorados. (Fecha a pendência "a".)
- `docs/ARSENAL-RAG.md`+`.html`: mapa do arsenal (7 fontes × ferramentas × maturidade) + arquitetura de adapters + ordem de ataque.
- **Camada de adapters** (`engine/adapters/`): contrato `SourceAdapter` (`can_handle`/`fetch`) + registro `resolve()`. Adicionar fonte = +1 arquivo, core intacto.
- **`web_adapter`**: URL → markdown (trafilatura + fallback httpx/bs4) → `insert_content_list` (bypassa MinerU). `cmd_ingest` resolve adapter antes do parser de arquivo.
- **E2E web PROVADO**: `https://example.com` → grafo (6 nós/3 arestas) + `vdb_*.json`; `query` com `Referências: https://example.com` (57s ingest / 31s query). +7 testes → **26/26 verdes**.

**Próximo:** `video_adapter` (YouTube via `yt-dlp`+Gemini) → `docs_adapter` (Notion) → áudio/db/comms (§6 do ARSENAL).

## Review v5 — video_adapter + docs_adapter (Notion) em PARALELO (2026-06-07)

2 fontes construídas EM PARALELO (2 subagentes com contrato compartilhado `base.py`/`web.py`), provadas E2E pelo orquestrador.

**Entregue:**
- **`video_adapter`** (`adapters/video.py`): YouTube → `yt-dlp` (legendas, sem baixar vídeo) → markdown → `insert_content_list`. E2E: vídeo 3Blue1Brown → query recupera **"28×28 / 784"** com citação. 16 testes unitários.
- **`docs_adapter`** (`adapters/notion.py`): Notion API (token `NOTION_TOKEN` do env) → blocos→markdown → RAG. E2E: página da sessão → query recupera **cliSessionId/sessionId** com citação. 17 testes.
- **Wiring**: `_ADAPTERS = [Video, Notion, Web]` (específicos antes do web genérico). Roteamento testado (smoke PASS).
- **Fix de concorrência** (`st_config.embedding_max_async` + `_build_rag`): Ollama local estourava timeout de 60s com 8 workers de embedding; reduzido p/ 2 (auto). Sem isso, vídeo (muitos chunks) falhava no flush do `vdb`.
- **59 testes verdes** (26 base + 16 vídeo + 17 Notion).

**Padrão validado:** subagentes paralelos + contrato compartilhado = 0 conflito (cada um só criou `<fonte>.py`+teste; orquestrador fez wiring/E2E). 2 adapters em ~5 min wall-clock.

**Gaps anotados:** (1) `can_handle` Notion cobre `notion.so/.site`, não `notion.com` (URLs reais são `app.notion.com` → usei `notion:<id>`); (2) query default poderia variar por tipo de fonte (narrativa→naive).

**Próximo (§6):** `audio_adapter` (faster-whisper) → `db_adapter` (Supabase) → `comms_adapter`.
