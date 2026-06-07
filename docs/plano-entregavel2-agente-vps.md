# Entregável 2 — Agente de Sistematização Permanente (VPS)

> **Status:** PLANO PARA DISCUSSÃO (não construído). Marcelo pediu: *"comece a construir 2 logo na sequência, mas melhorado. Gere acesso via CC a um agente de sistematização permanente que more na nossa VPS e faça RAG de todos os nossos sistemas, pesquisas e trabalhos. Mas vamos falar isso apartado, criando um plano."*
>
> Este documento é o ponto de partida da conversa. Ao final há **decisões abertas** que preciso de você para fechar antes de construir.

---

## 1. Visão

Um **agente permanente** rodando na VPS que mantém, continuamente, um **RAG vivo de todo o ecossistema** (sistemas, repositórios, pesquisas, documentos, sessões, dados ANEEL, jurídico) — acessível de qualquer sessão Claude Code via um **MCP/HTTP** seguro. Diferente do Entregável 1 (local, sob demanda, por base), o Entregável 2 é **sempre ligado, multi-fonte, auto-atualizável**.

Frase-guia: *"qualquer coisa que já produzimos ou estamos produzindo deve ser consultável em 1 pergunta, com a fonte e a data."*

## 2. O que muda em relação ao Entregável 1

| Dimensão | Entregável 1 (pronto) | Entregável 2 (este plano) |
|---|---|---|
| Execução | local, sob demanda | **permanente na VPS** (serviço) |
| Fontes | arquivos/pastas que você aponta | **conectores automáticos** (GitHub, Notion, Drive, Gmail, Supabase, ANEEL, etc.) |
| Atualização | manual | **cron/reindex incremental** |
| Acesso | CLI / plugin local | **MCP server** (tools via CC) + HTTP API |
| Storage | local/supabase por base | **central** (Supabase pgvector multi-tenant) |
| Reuso | — | **o motor `sistematiza/engine` vira o core** |

## 3. Arquitetura proposta

```
                ┌──────────────────────── Claude Code (qualquer sessão) ───────────────────────┐
                │   MCP tools: sistematiza_query · sistematiza_ingest · sistematiza_sources    │
                └───────────────▲──────────────────────────────────────────────────────────────┘
                                │  (auth: API key server-to-server / JWT — Seção 11)
        ┌───────────────────────┴───────────────────────────┐
        │                VPS (Hostinger)                     │
        │  ┌────────────┐   ┌─────────────────────────────┐  │
        │  │ MCP server │──▶│ Sistematiza-Service (FastAPI)│  │
        │  │ (HTTP/SSE) │   │  - core = sistematiza/engine │  │
        │  └────────────┘   │  - RAG-Anything + LightRAG   │  │
        │                   │  - backend LLM (local/nuvem) │  │
        │                   └──────────┬──────────────────┘  │
        │   ┌──────────────────────────┼───────────────────┐ │
        │   │ Connectors (scheduled / webhook)             │ │
        │   │  GitHub · Notion · Drive · Gmail · Supabase  │ │
        │   │  · ANEEL data lake · jurídico (normas)       │ │
        │   └──────────────────────────┬───────────────────┘ │
        │                   ┌──────────▼──────────┐           │
        │                   │ Supabase (pgvector) │           │
        │                   │  grafos + vetores   │           │
        │                   └─────────────────────┘           │
        └────────────────────────────────────────────────────┘
```

### Componentes
1. **Sistematiza-Service (FastAPI)** — reusa `sistematiza/engine` (motor já testado) como biblioteca. Expõe ingest/query/status. Roda em contêiner na VPS.
2. **Connectors** — um por fonte, com ingestão **incremental** (só o que mudou): GitHub (repos), Notion (DB Sessões + páginas), Google Drive, Gmail (threads relevantes), Supabase (dados de produto), ANEEL data lake (datasets CKAN), jurídico (normas → modo de 1ª classe do Entregável 1).
3. **Scheduler** — cron/systemd timer para reindex periódico + webhooks para tempo real onde der.
4. **MCP server** — expõe ao Claude Code as tools `sistematiza_query`, `sistematiza_ingest`, `sistematiza_sources`. Auth server-to-server.
5. **Storage central** — Supabase pgvector (multi-tenant por workspace), reaproveitando seu MCP/infra Supabase.

## 4. Segurança (Seção 11 — obrigatória)
- API key do serviço **server-side**, hash bcrypt no banco, nunca no frontend/CC bundle.
- CC ↔ VPS via **proxy/Edge** com JWT curto ou API key em header server-to-server.
- **Prompt-injection shield** na ingestão (conteúdo de docs/e-mails vai ao LLM): limite de chars, blocklist, log com hash.
- Anti-bot + rate limit (Traefik) no endpoint.
- Honeytoken `/api/trap`.
- Docs sensíveis (jurídico) → **backend LLM local na própria VPS** (Ollama) para não sair da infra.

## 5. Fases sugeridas
1. **F0 — Fundação:** empacotar `sistematiza/engine` como lib instalável; subir Sistematiza-Service (FastAPI) com 1 fonte (ex.: 1 repo GitHub) end-to-end na VPS.
2. **F1 — MCP + Auth:** MCP server + auth server-to-server; tool `sistematiza_query` funcionando no seu CC.
3. **F2 — Connectors:** Notion, Drive, Supabase, ANEEL; ingestão incremental + scheduler.
4. **F3 — Jurídico vivo:** pipeline de normas (Planalto/LexML) auto-populando o modo de 1ª classe; vigência/revogação atualizada.
5. **F4 — Hardening:** Seção 11 completa (shield, honeytoken, rate limit, observabilidade).

## 6. Decisões abertas (preciso de você antes de construir)

1. **VPS/região:** qual VPS Hostinger e região? (latência importa se for chamado em loop)
2. **Backend LLM na VPS:** Ollama local (privado, sem custo de token, mais lento) **ou** nuvem (OpenAI/Claude via proxy)? Misto por sensibilidade da fonte?
3. **Storage central:** Supabase pgvector (já temos) **ou** Postgres dedicado na VPS? Multi-tenant por workspace (nexvy vs pessoal) como no `notion-routing.json`?
4. **Acesso do CC:** MCP server (preferido, nativo no CC) **ou** HTTP API + skill? (recomendo MCP)
5. **Fontes prioritárias (ordem):** quais entram primeiro? (sugiro: repos GitHub do Intentus → Notion Sessões → ANEEL data lake → jurídico)
6. **Cadência de reindex:** tempo real (webhook) onde der + cron diário para o resto?
7. **Orçamento/custo-alvo:** teto de custo mensal (define local vs nuvem e tamanho da VPS).
8. **Multi-usuário:** só você ou a equipe Nexvy também consulta? (muda auth e tenancy)

---

> **Próximo passo:** quando você responder as 8 decisões acima, eu transformo este plano em um `tasks/todo.md` executável e começamos pela F0 (reuso do motor já pronto).
