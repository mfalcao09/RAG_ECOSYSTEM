#!/usr/bin/env python3
"""Adapta um registry.json de formato EXTERNO para o schema do Sistematiza.

Formatos externos comuns trazem vigência como booleano `vigente` e referências de
revogação em TEXTO LIVRE (ex.: "Lei nº 8.031/1990") em vez de chaves. Este adaptador:
  - preserva os campos compatíveis;
  - mantém `vigente` (bool) — que o motor honra como autoritativo;
  - move `revogada_por`/`revoga` (texto livre) para `nota_revogacao`/`observacoes`,
    evitando 'referências órfãs' e preservando a informação na ficha.

Uso: adapt-registry.py <entrada.json> <saida.json>
"""
from __future__ import annotations
import json
import sys

KEEP = ["tipo", "numero", "ano", "data", "orgao", "esfera", "uf",
        "ementa", "assuntos", "fonte_url"]


def _join(v) -> str:
    if isinstance(v, (list, tuple)):
        return "; ".join(str(x) for x in v)
    return str(v)


def adapt(src: list) -> list:
    out = []
    for x in src:
        d = {k: x[k] for k in KEEP if k in x}
        if "vigente" in x and x["vigente"] is not None:
            d["vigente"] = bool(x["vigente"])
        if x.get("revogada_por"):
            d["nota_revogacao"] = "Revogada por: " + _join(x["revogada_por"])
        notas = []
        if x.get("revoga"):
            notas.append("Revoga (fonte): " + _join(x["revoga"]))
        if x.get("confianca") is not None:
            notas.append(f"confiança={x['confianca']}")
        if notas:
            d["observacoes"] = " | ".join(notas)
        out.append(d)
    return out


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("uso: adapt-registry.py <entrada.json> <saida.json>")
        sys.exit(2)
    src = json.load(open(sys.argv[1], encoding="utf-8"))
    res = adapt(src)
    json.dump(res, open(sys.argv[2], "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"adaptadas {len(res)} normas -> {sys.argv[2]}")
