# Sistematiza

> **RAG poderoso sobre qualquer tema** (sobre [RAG-Anything](https://github.com/HKUDS/RAG-Anything)) **+ organização jurídica de normas** com hierarquia, vigência/revogação e estruturação automática de pastas — empacotado como **plugin + agente Claude Code**.

Transforma documentos soltos em conhecimento **organizado** e **consultável**. Para o domínio jurídico, é uma feature de 1ª classe: o motor entende a hierarquia das fontes do direito (CF > LC > Lei > Decreto > Portaria), calcula **vigência e revogação** automaticamente (marcando a norma revogada **e por qual norma**) e organiza tudo em pastas por assunto/tipo/órgão/ano — da **mais atual para a mais antiga**.

---

## Arquitetura

```
sistematiza/                         (repositório = marketplace de 1 plugin)
├── .claude-plugin/marketplace.json  ← lista o plugin
├── sistematiza/                     ← o PLUGIN
│   ├── .claude-plugin/plugin.json
│   ├── agents/sistematizador.md     ← agente orquestrador
│   ├── commands/                    ← /sistematiza:new|ingest|query|normas|organize|status
│   ├── skills/
│   │   ├── rag-sistematizacao/      ← modo genérico (RAG)
│   │   └── normas-juridicas/        ← modo jurídico (1ª classe)
│   └── engine/                      ← MOTOR Python
│       ├── sistematiza.py           ← CLI (init/normas/ingest/query/status/doctor)
│       ├── st_config.py             ← config por base (backend/storage)
│       ├── st_backends.py           ← llm/vision/embedding (lazy; configurável)
│       ├── st_storage.py            ← local | supabase (por base)
│       ├── normas/                  ← inteligência jurídica (stdlib puro)
│       │   ├── taxonomy.py · model.py · vigencia.py · organizer.py
│       └── tests/                   ← 6 testes (vigência + organização)
├── setup.sh · .gitignore · templates/ · tasks/ · README.md/.html
```

**Princípio-chave — _lazy import_:** o subsistema `normas/` é **stdlib puro** (roda em qualquer Python 3.9+, sem RAG-Anything). Só `ingest`/`query` importam o motor pesado. Logo, você organiza milhares de normas **hoje**, sem baixar 1GB de modelos nem gastar token de API.

---

## Instalação como plugin Claude Code

```bash
# 1) registrar o marketplace local
/plugin marketplace add ~/Projects/GitHub/sistematiza
# 2) instalar o plugin
/plugin install sistematiza@sistematiza-marketplace
```

Comandos disponíveis: `/sistematiza:new`, `/sistematiza:ingest`, `/sistematiza:query`, `/sistematiza:normas`, `/sistematiza:organize`, `/sistematiza:status`. O agente **`sistematizador`** é acionado automaticamente para tarefas de sistematização/organização de normas.

## Motor (para ingest/query — RAG real)

```bash
cd ~/Projects/GitHub/sistematiza
PYTHON=python3.12 ./setup.sh          # cria venv 3.11/3.12 + instala raganything[all]
source .venv/bin/activate
ollama pull qwen2.5:7b nomic-embed-text llama3.2-vision   # backend local (opcional)
```

> O slice jurídico **não precisa** de setup — roda com `python3` do sistema.

---

## Uso — modo jurídico (normas)

```bash
PY="python3 sistematiza/engine/sistematiza.py"

# 1) cria a base
$PY init ./licitacoes --name "Licitações" --modo normas --backend ollama --storage local

# 2) importa as normas (uma entrada por norma; ver schema abaixo)
$PY normas import ./licitacoes sistematiza/engine/tests/sample_normas.json

# 3) organiza tudo
$PY normas organize ./licitacoes
```

Gera, em `./licitacoes/normas/`:

```
_INDICE.md          índice mestre (mais recente primeiro; ⛔ revogadas com a revogadora)
_INDICE.json        versão legível por máquina
acervo/<chave>.md   ficha individual de cada norma
vigentes/_index.md  ✅
revogadas/_index.md ⛔
por-assunto/<slug>/_index.md
por-tipo/<slug>/_index.md
por-orgao/<slug>/_index.md
por-ano/<ano>/_index.md
```

Exemplo de linha do índice mestre:

```
- ⛔ [**Lei Ordinária nº 8.666/1993**](acervo/lei_ordinaria-8.666-1993.md) — Regulamenta o art. 37, XXI... — _REVOGADA por Lei Ordinária nº 14.133/2021 (2021)_
```

### Schema de uma Norma (`registry.json`)

| Campo | Exemplo | Notas |
|---|---|---|
| `tipo` | `"lei_ordinaria"` | chave canônica **ou** texto livre ("Lei Complementar") |
| `numero` | `"14.133"` | |
| `ano` | `2021` | |
| `data` | `"2021-04-01"` | ISO 8601 |
| `orgao` | `"Congresso Nacional"` | |
| `esfera` | `"federal"` | federal/estadual/municipal/distrital |
| `ementa` | `"Lei de Licitações..."` | |
| `assuntos` | `["licitações", ...]` | vira faceta `por-assunto/` |
| `revoga` | `["lei_ordinaria-8.666-1993"]` | referencia **chaves** `<tipo>-<numero>-<ano>` |
| `revoga_parcialmente` / `altera` | `[]` | idem |
| `fonte_url` | `"https://planalto..."` | |

**Hierarquia (rank menor = mais alto):** CF(1) · EC(2) · Tratado(3) · LC(4) · Lei/MP/Decreto-Lei(5) · Decreto(6) · IN/Resolução(7) · Portaria(8) · ...

**Vigência (automática, bidirecional):** declarar `revoga` na revogadora propaga `revogada_por` para a revogada. Uma só declaração mantém os dois lados consistentes.

---

## Uso — modo genérico (RAG sobre qualquer tema)

```bash
$PY init ./pesquisa --modo generico --backend ollama --storage local
$PY ingest ./pesquisa ./meus-pdfs --recursive
$PY query  ./pesquisa "Qual a conclusão do estudo X?" --mode hybrid
```

Modos de query: `naive · local · global · hybrid (recomendado) · mix · bypass`.

---

## Backends (configurável por base)

| Backend | LLM | Embeddings | Quando |
|---|---|---|---|
| `ollama` | qwen2.5 | nomic-embed-text | **Local/privado** — docs sensíveis, custo zero |
| `lmstudio` | gpt-oss-20b | nomic-embed | Local via LM Studio |
| `openai` | gpt-4o-mini | text-embedding-3-large | Nuvem, rápido |
| `claude_openai_emb` | Claude | OpenAI emb | Claude + embeddings de nuvem |

**Segurança (Seção 11):** chaves **nunca** ficam no `.sistematiza.json` — só o **nome** da env var (`api_key_env`). Antes de ingest/query na nuvem: `export OPENAI_API_KEY=...`.

## Storage (configurável por base)
- **local** — `working_dir` em disco (default).
- **supabase** — Postgres + pgvector (experimental).

---

## Verificação (estado atual)

| Item | Status |
|---|---|
| `py_compile` (10 arquivos) | ✅ OK |
| Testes unitários (`normas/`) | ✅ 6/6 |
| Smoke E2E (init→import→organize→status) | ✅ 6 normas, 4 vigentes, 2 revogadas |
| Índice: ordem + revogadas marcadas | ✅ |
| `ingest`/`query` end-to-end | ✅ provado (Ollama local + MinerU `pipeline`) — ver `tasks/todo.md` Review v3 |
| Storage supabase | ⏳ experimental |

---

## Roadmap
- **Entregável 2** — agente de sistematização **permanente** na VPS, fazendo RAG de todos os sistemas/pesquisas/trabalhos (plano apartado: `docs/plano-entregavel2-agente-vps.md`).
- Conectores de fonte (Planalto/LexML) para auto-popular o `registry.json`.
- Versões consolidadas de normas (texto vigente vs. original).

## Créditos
Motor RAG: [HKUDS/RAG-Anything](https://github.com/HKUDS/RAG-Anything) (multimodal RAG sobre LightRAG). Plugin/agente/inteligência jurídica: Marcelo Silva.
