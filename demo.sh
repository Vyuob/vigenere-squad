#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
export PATH="$HOME/.local/bin:$PATH"
command -v uv >/dev/null 2>&1 || { echo "Lancez d'abord ./installer.sh"; exit 1; }
uv sync --frozen
echo "Démonstration locale sur http://127.0.0.1:8765  (Ctrl+C pour arrêter)"
( sleep 3; (xdg-open http://127.0.0.1:8765 || open http://127.0.0.1:8765) >/dev/null 2>&1 || true ) &
uv run --frozen vigenere-squad demo
