"""Organizador de acervo normativo em pastas/índices (modo jurídico).

A partir de uma lista de Norma já resolvida (vigência calculada), gera:

    <out>/
      _INDICE.md            índice mestre (mais recente primeiro; revogadas marcadas)
      _INDICE.json          índice legível por máquina
      acervo/<chave>.md     ficha individual de cada norma
      vigentes/_index.md    (inclui as revogadas PARCIALMENTE — ainda em vigor)
      revogadas/_index.md
      por-situacao/<situacao>/_index.md   ← cobre TODOS os estados (nada some)
      por-tipo/<slug>/_index.md
      por-assunto/<slug>/_index.md
      por-orgao/<slug>/_index.md
      por-ano/<ano>/_index.md
"""
from __future__ import annotations
from typing import List, Dict
from pathlib import Path
import json
import re
from .model import Norma, SITUACAO_BANNER, REVOGADA, REVOGADA_PARCIAL, VIGENTE
from .vigencia import descricao_situacao, cadeia_revogacao
from .taxonomy import label_of
from .util import slugify


def _num_int(s: str) -> int:
    d = re.sub(r"\D", "", str(s or ""))
    return int(d) if d else 0


def _ordena(normas: List[Norma]) -> List[Norma]:
    """Mais recente primeiro; empate -> hierarquia (rank asc) -> número desc."""
    xs = list(normas)
    xs.sort(key=lambda n: _num_int(n.numero), reverse=True)   # menos significativo
    xs.sort(key=lambda n: n.rank)                              # hierarquia
    xs.sort(key=lambda n: n.ordenacao, reverse=True)          # data (mais significativo)
    return xs


def _linha(n: Norma, todas: List[Norma], rel_prefix: str = "acervo") -> str:
    emoji = SITUACAO_BANNER.get(n.situacao, "❔").split()[0]
    desc = descricao_situacao(n, todas)
    ementa = (n.ementa or "").strip()
    if len(ementa) > 140:
        ementa = ementa[:137] + "..."
    return f"- {emoji} [**{n.display}**]({rel_prefix}/{n.chave_fs}.md) — {ementa} — _{desc}_"


def _ficha(n: Norma, todas: List[Norma]) -> str:
    banner = SITUACAO_BANNER.get(n.situacao, "❔ INDEFINIDA")
    emoji = banner.split()[0]
    cad = cadeia_revogacao(n, todas)
    linhas = [
        f"# {n.display}",
        "",
        f"> {emoji} {descricao_situacao(n, todas)}",
        "",
        f"- **Tipo:** {label_of(n.tipo)} (`{n.tipo}`, hierarquia rank {n.rank})",
        f"- **Número:** {n.numero or 's/nº'}",
        f"- **Ano:** {n.ano or '—'}",
        f"- **Data:** {n.data or '—'}",
        f"- **Órgão:** {n.orgao or '—'}",
        f"- **Esfera:** {n.esfera}" + (f"/{n.uf}" if n.uf else ""),
        f"- **Assuntos:** {', '.join(n.assuntos) if n.assuntos else '—'}",
        f"- **Fonte:** {n.fonte_url or '—'}",
    ]
    if cad["revoga"]:
        linhas.append(f"- **Revoga:** {'; '.join(cad['revoga'])}")
    if cad["revogada_por"]:
        linhas.append(f"- **Revogada por:** {'; '.join(cad['revogada_por'])}")
    if n.observacoes:
        linhas += ["", "## Observações", "", n.observacoes]
    linhas += ["", "## Ementa", "", n.ementa or "_(sem ementa)_", ""]
    return "\n".join(linhas)


def _escreve_index(path: Path, titulo: str, normas: List[Norma],
                   todas: List[Norma], rel_prefix: str = "acervo") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    linhas = [
        f"# {titulo}",
        "",
        f"_Total: {len(normas)} norma(s) — ordenadas da mais recente para a mais antiga._",
        "",
    ]
    linhas += [_linha(n, todas, rel_prefix) for n in _ordena(normas)]
    linhas.append("")
    path.write_text("\n".join(linhas), encoding="utf-8")


def organizar(normas: List[Norma], out_dir: str,
              base_name: str = "Acervo Normativo") -> Dict[str, Any]:
    out = Path(out_dir)
    (out / "acervo").mkdir(parents=True, exist_ok=True)

    for n in normas:
        (out / "acervo" / f"{n.chave_fs}.md").write_text(_ficha(n, normas), encoding="utf-8")

    # índice mestre + json
    _escreve_index(out / "_INDICE.md", f"📚 {base_name} — Índice Mestre", normas, normas)
    (out / "_INDICE.json").write_text(
        json.dumps([n.to_dict() for n in _ordena(normas)], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    # vigentes inclui as revogadas PARCIALMENTE (ainda em vigor na parte não revogada)
    vigentes = [n for n in normas if n.situacao in (VIGENTE, REVOGADA_PARCIAL)]
    revogadas = [n for n in normas if n.situacao in (REVOGADA, REVOGADA_PARCIAL)]
    _escreve_index(out / "vigentes" / "_index.md", "✅ Normas Vigentes (inclui parcialmente revogadas)",
                   vigentes, normas, rel_prefix="../acervo")
    _escreve_index(out / "revogadas" / "_index.md", "⛔ Normas Revogadas",
                   revogadas, normas, rel_prefix="../acervo")

    def facet(base: str, valores_de) -> None:
        grupos: Dict[str, List[Norma]] = {}
        for n in normas:
            for val in valores_de(n):
                grupos.setdefault(str(val), []).append(n)
        for val, itens in grupos.items():
            _escreve_index(out / base / slugify(val) / "_index.md",
                           f"{base} · {val}", itens, normas, rel_prefix="../../acervo")

    # por-situacao cobre TODOS os estados → nenhuma norma fica de fora de uma faceta
    facet("por-situacao", lambda n: [n.situacao])
    facet("por-tipo", lambda n: [label_of(n.tipo)])
    facet("por-assunto", lambda n: n.assuntos or ["sem-assunto"])
    facet("por-orgao", lambda n: [n.orgao or "sem-orgao"])
    facet("por-ano", lambda n: [n.ano or "sem-ano"])

    por_situacao: Dict[str, int] = {}
    for n in normas:
        por_situacao[n.situacao] = por_situacao.get(n.situacao, 0) + 1

    return {
        "total": len(normas),
        "vigentes": sum(1 for n in normas if n.situacao == VIGENTE),
        "revogadas": sum(1 for n in normas if n.situacao in (REVOGADA, REVOGADA_PARCIAL)),
        "por_situacao": por_situacao,   # soma == total (reconcilia)
    }
