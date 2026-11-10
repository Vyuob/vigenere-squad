#!/usr/bin/env bash
# Installation sous Linux / macOS : environnement fige + tests.
set -euo pipefail
cd "$(dirname "$0")"
export PATH="$HOME/.local/bin:$PATH"
if ! command -v uv >/dev/null 2>&1; then
  echo "uv introuvable : installation..."
  curl -LsSf https://astral.sh/uv/install.sh | sh
  export PATH="$HOME/.local/bin:$PATH"
fi
echo "[1/2] Environnement figé (uv.lock)..."
uv sync --frozen --extra dev
echo "[2/2] Tests (sans LLM)..."
uv run --frozen pytest -q
echo "OK : installation terminée. Lancez ./demo.sh ou ./verifier.sh"
