#!/usr/bin/env bash
# =====================================================================
# Sistematiza — instalador LOCAL como plugin Claude Code (marketplace @local).
# Idempotente. Faz backup .bak.sistematiza de cada config antes de editar.
# Re-rode após editar o repo para re-sincronizar o cache.
#
# Replica o que o `/plugin install` faz para um plugin local:
#   1. copia o plugin -> ~/.claude/plugins/cache/local/sistematiza/v1
#   2. registra no marketplace "local"
#   3. registra em installed_plugins.json (schema v2)
#   4. habilita em settings.json -> enabledPlugins
# Após rodar: REINICIE o Claude Code para carregar o plugin.
# =====================================================================
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PLUGIN_DIR="$REPO/sistematiza"
CC="$HOME/.claude/plugins"
CACHE="$CC/cache/local/sistematiza/v1"
NAME="sistematiza"
MKT="local"
VER="0.1.0"
TS="$(date -u +%Y-%m-%dT%H:%M:%S.000Z)"

[ -f "$PLUGIN_DIR/.claude-plugin/plugin.json" ] || { echo "ERRO: plugin.json nao encontrado em $PLUGIN_DIR"; exit 1; }

echo ">> copiando plugin para o cache local ($CACHE)"
mkdir -p "$CACHE"
rsync -a --delete --exclude='__pycache__' --exclude='*.pyc' "$PLUGIN_DIR/" "$CACHE/"
touch "$CACHE/.in_use"

echo ">> registrando marketplace / installed / enabled (com backup)"
python3 - "$CC" "$CACHE" "$NAME" "$MKT" "$VER" "$TS" <<'PY'
import json, os, sys, shutil
cc, cache, name, mkt, ver, ts = sys.argv[1:7]
home = os.path.expanduser('~')

def backup(p):
    if os.path.exists(p):
        shutil.copy2(p, p + '.bak.sistematiza')

def load(p):
    with open(p, encoding='utf-8') as f:
        return json.load(f)

def save(p, d):
    with open(p, 'w', encoding='utf-8') as f:
        json.dump(d, f, ensure_ascii=False, indent=2)

key = f"{name}@{mkt}"

# (a) marketplace local
mfile = os.path.join(cc, 'marketplaces', 'local', '.claude-plugin', 'marketplace.json')
backup(mfile); d = load(mfile)
plugins = d.setdefault('plugins', [])
if not any(p.get('name') == name for p in plugins):
    plugins.append({
        "name": name, "source": cache,
        "description": "RAG-Anything + organizacao juridica de normas (vigencia/revogacao, hierarquia, pastas)",
        "version": ver, "author": {"name": "Marcelo Silva"},
        "keywords": ["rag", "rag-anything", "normas", "juridico"],
    })
    save(mfile, d); print("  marketplace local: + sistematiza")
else:
    print("  marketplace local: ja contem sistematiza")

# (b) installed_plugins.json (schema v2)
ifile = os.path.join(cc, 'installed_plugins.json')
backup(ifile); d = load(ifile)
if key not in d.setdefault('plugins', {}):
    d['plugins'][key] = [{
        "scope": "user", "installPath": cache, "version": ver,
        "installedAt": ts, "lastUpdated": ts,
    }]
    save(ifile, d); print(f"  installed_plugins: + {key}")
else:
    print(f"  installed_plugins: ja contem {key}")

# (c) settings.json -> enabledPlugins
sfile = os.path.join(home, '.claude', 'settings.json')
backup(sfile); d = load(sfile)
ep = d.setdefault('enabledPlugins', {})
if not ep.get(key):
    ep[key] = True
    save(sfile, d); print(f"  settings enabledPlugins: + {key}")
else:
    print(f"  settings: ja habilitado {key}")
PY

echo ""
echo "OK: Sistematiza instalado como plugin @local."
echo ">> REINICIE o Claude Code para carregar."
echo "   Depois: agente 'sistematizador' + /sistematiza:new|ingest|query|normas|organize|status"
