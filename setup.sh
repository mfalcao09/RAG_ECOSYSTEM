#!/usr/bin/env bash
# =====================================================================
# Sistematiza — setup do MOTOR RAG (venv + dependências). Idempotente.
# As operações stdlib (init / normas / status / doctor) NÃO precisam disto.
# Uso:  ./setup.sh        (ou:  PYTHON=python3.12 ./setup.sh)
# =====================================================================
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENGINE="$ROOT/sistematiza/engine"
VENV="$ROOT/.venv"
PYBIN="${PYTHON:-python3}"

echo "▶ Sistematiza setup em $ROOT"
echo "  Python: $("$PYBIN" --version 2>&1)"
echo "  (recomendado 3.11/3.12 para mineru/torch — use PYTHON=python3.12 ./setup.sh se necessário)"

if [ ! -d "$VENV" ]; then
  "$PYBIN" -m venv "$VENV"
  echo "  venv criado: $VENV"
fi
# shellcheck disable=SC1091
source "$VENV/bin/activate"
python -m pip install --upgrade pip >/dev/null
echo "▶ instalando dependências do motor (raganything[all], ollama)..."
pip install -r "$ENGINE/requirements.txt"

echo "▶ diagnóstico:"
python "$ENGINE/sistematiza.py" doctor || true

cat <<'EOF'

✅ Setup concluído.
  Ative o venv antes de ingest/query:   source .venv/bin/activate
  Backend local (privado):              ollama pull qwen2.5:7b nomic-embed-text llama3.2-vision
  Backend nuvem:                        export OPENAI_API_KEY=...   (e/ou ANTHROPIC_API_KEY=...)
  Teste rápido (sem RAG):               python sistematiza/engine/sistematiza.py --help
EOF
