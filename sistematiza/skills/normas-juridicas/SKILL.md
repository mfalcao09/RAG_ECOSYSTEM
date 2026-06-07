---
name: normas-juridicas
description: Use ao organizar legislação/normas jurídicas com o Sistematiza — modelar uma norma, montar o registry.json, calcular vigência e revogação (marcando a revogada e por qual norma a revogou), aplicar a hierarquia normativa (CF>LC>Lei>Decreto>Portaria) e gerar a árvore de pastas por assunto/tipo/órgão/ano. Triggers: "organizar normas", "legislação", "norma revogada", "vigência", "acervo normativo", "está revogada".
---

# Normas Jurídicas (modo de 1ª classe)

## Modelo de uma Norma (entrada em `registry.json`)
```json
{
  "tipo": "lei_ordinaria",
  "numero": "14.133",
  "ano": 2021,
  "data": "2021-04-01",
  "orgao": "Congresso Nacional",
  "esfera": "federal",
  "uf": null,
  "ementa": "Lei de Licitações e Contratos Administrativos.",
  "assuntos": ["licitações", "contratos administrativos"],
  "revoga": ["lei_ordinaria-8.666-1993", "lei_ordinaria-10.520-2002"],
  "revoga_parcialmente": [],
  "altera": [],
  "fonte_url": "https://www.planalto.gov.br/...",
  "observacoes": null
}
```
**Chave** = `<tipo>-<numero>-<ano>` (ex.: `lei_ordinaria-8.666-1993`). Todas as relações referenciam chaves.

## Tipos & hierarquia (rank menor = mais alto)
`constituicao_federal`(1) · `emenda_constitucional`(2) · `tratado_internacional`(3) · `lei_complementar`(4) · `lei_ordinaria`/`medida_provisoria`/`decreto_lei`/`lei_delegada`/`decreto_legislativo`(5) · `decreto`(6) · `instrucao_normativa`/`resolucao`/`regimento`(7) · `portaria`/`circular`(8) · `ordem_de_servico`/`ato_normativo`(9) · `sumula`(10) · `jurisprudencia`(11).

O campo `tipo` aceita a chave canônica OU texto livre ("Lei Complementar", "Decreto-Lei", "Portaria") — há detecção automática por alias.

## Vigência (calculada pelo motor, bidirecional)
- `revoga` → a norma alvo vira **revogada** e ganha `revogada_por` automaticamente.
- `revoga_parcialmente` → alvo vira **revogada parcialmente**.
- `data` futura (vs. hoje) → **vacatio legis**.
- caso contrário → **vigente**.

## Comandos
- importar:  `sistematiza normas import <dir> <normas.json>`
- organizar: `sistematiza normas organize <dir>`
  → gera `_INDICE.md` (mais recente primeiro; ⛔ revogadas marcadas com a revogadora), `_INDICE.json`, `acervo/<chave>.md`, `vigentes/`, `revogadas/`, `por-assunto/`, `por-tipo/`, `por-orgao/`, `por-ano/`.
- situação:  `sistematiza normas status <dir> --chave <chave>`

## Regras de ouro
- **NUNCA inventar** número/ano/revogação. Se a fonte não confirma, registre em `observacoes` e marque para conferência humana (Seção 5 — defesa contra alucinação).
- Sempre **relacione a revogação à norma revogadora** (não basta "revogada").
- Combine com o RAG (`ingest`/`query`) para responder sobre o TEXTO das normas — preferindo as **vigentes**.
