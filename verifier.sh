#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
export PATH="$HOME/.local/bin:$PATH"
command -v uv >/dev/null 2>&1 || { echo "Lancez d'abord ./installer.sh"; exit 1; }
uv sync --frozen --extra dev
echo "[1/3] Tests..."; uv run --frozen pytest -q
echo "[2/3] Empreintes SHA-256..."; uv run --frozen python scripts/hashes.py --check
echo "[3/3] Signature minisign..."
if command -v minisign >/dev/null 2>&1; then minisign -Vm SHA256SUMS -p minisign.pub
else echo "minisign non installé : étape ignorée (brew install minisign / apt install minisign)"; fi
echo "OK : tout est conforme."
