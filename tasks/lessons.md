# tasks/lessons.md — Sistematiza

> Regras aprendidas durante a construção (Seção 1.3 do CLAUDE.md).

- **Lazy import = testabilidade.** Isolar a inteligência de domínio (normas, stdlib puro)
  do motor pesado (raganything/mineru, importado só em ingest/query) permite prova de
  funcionamento real (testes verdes, smoke E2E) sem baixar GBs nem gastar token de API.
- **Python 3.14 quebra o RAG pesado.** mineru/torch podem não ter wheels para 3.14; o
  motor RAG deve rodar em venv 3.11/3.12. O slice jurídico roda em qualquer 3.9+.
- **Segredos só via env var (Seção 11).** O `.sistematiza.json` guarda apenas o NOME da
  env var (`api_key_env`), nunca o segredo. `.gitignore` bloqueia `.env`/`*secret*`/`*api_key*`.
- **Vigência é bidirecional.** Modelar `revoga` na norma revogadora e PROPAGAR para
  `revogada_por` na revogada — assim uma só declaração mantém os dois lados consistentes.
- **Fact-Forcing Gate.** O hook bloqueia a 1ª criação de arquivo de cada turno; basta
  reapresentar os 4 fatos e reexecutar. Para deleção, usar `mktemp -d`/`find -delete` em vez de `rm -rf`.
- **Wiring de lib externa exige smoke-test com mock.** A revisão adversarial pegou bugs
  que o lazy-import escondia: `rag.finalize()` não existe (é `finalize_storages()`);
  `openai_embed` é um `EmbeddingFunc` (usar `.func(...)`, não chamá-lo direto); `aquery`
  exige `_ensure_lightrag_initialized()` antes. Solução: `test_backends_smoke.py` injeta
  módulos `lightrag` falsos em `sys.modules` e valida a FORMA das chamadas — pega regressão
  de assinatura sem baixar 1GB. **Sempre que escrever contra API de lib não exercitada,
  adicionar um smoke com mock.**
- **Cobrir TODOS os estados nas facetas.** Split binário vigente/revogada faz vacatio legis
  e revogação parcial sumirem. Faceta `por-situacao/` cobre 100% e `stats.por_situacao` reconcilia.
- **Extração heurística é sensível ao formato.** Regex de data BR precisa aceitar ordinal em
  variações (`1º`/`1o`/`1°`/`1ª`). Toda extração sai marcada "CONFERIR" — nunca confiar cego.
- **MinerU 3.x usa `--backend`, não só `--method`.** O default `hybrid-auto-engine` carrega o
  VLM e estoura a RAM (OOM em `Predict: 0%`). Para texto/CPU, force `-b pipeline` (leve). No
  RAGAnything isso é um kwarg do parser (`backend=`), repassado por `process_*_complete`.
  `parse_method=txt` sozinho NÃO basta na 3.x — o método só se aplica a pipeline/hybrid-*.
- **`embedding_func` DEVE retornar np.ndarray.** O LightRAG (`EmbeddingFunc.__call__`) faz
  `result.size` para validar a dimensão; uma `list` crua quebra com "'list' object has no
  attribute 'size'" no flush do NanoVectorDB (os `vdb_*.json` nem são gerados). Sempre
  `np.array(...)` no retorno do embed — o mock do smoke não pega isso (só backend real pega).
- **Não passe `system_prompt` customizado ao `aquery` do LightRAG.** Ele SUBSTITUI o template
  `rag_response`/`naive_rag_response`, que contém o placeholder do contexto (`{context_data}`/
  `{content_data}`) — o contexto recuperado some e o LLM responde "sem informação" mesmo com
  retrieval OK. Para instrução/guarda anti-injection, use `QueryParam.user_prompt` (o template
  já tem `{user_prompt}` e já instrui "answer ONLY using the provided Context").
- **Backend local (Ollama) estoura timeout de embedding com a concorrência default.** O LightRAG
  dispara `embedding_func_max_async=8` workers concorrentes; o Ollama é single-instance e serializa
  → workers enfileiram e estouram o timeout de 60s (`Worker execution timeout` → `Failed to finalize
  chunks_vdb`, o vdb não é gerado). Some em fontes de 1 chunk (web), aparece com muitos (vídeo/transcrição).
  Fix: `embedding_func_max_async=2` (ou 1) via `lightrag_kwargs` p/ backend local (campo `embedding_max_async`).
- **`naive`/`mix` > `hybrid` para conteúdo NARRATIVO (transcrição, prosa).** `hybrid`/`local`/`global`
  dependem do grafo de entidades; se o fato não virou entidade discreta casável, o retrieval volta
  vazio mesmo com o chunk indexado. `naive` (vetorial puro) recupera direto. `hybrid` é melhor p/ docs
  com entidades nítidas (normas, fichas). Considerar default de query por tipo de fonte.
- **Adapters: subagentes paralelos + contrato compartilhado = 0 conflito.** Orquestrador fixa `base.py`
  (contrato) + `web.py` (template) ANTES; cada subagente cria só `<fonte>.py`+teste e NÃO toca
  `__init__.py`/`requirements.txt` (pontos de conflito); orquestrador faz wiring + E2E serial (Ollama é
  recurso único — não paralelizar a prova). 2 adapters em ~5 min vs sequencial.
