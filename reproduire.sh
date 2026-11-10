#!/usr/bin/env bash
# ./reproduire.sh rapide    (≈ 10-15 min, qwen3:0.6b, comme la CI)
# ./reproduire.sh complet   (plusieurs heures : qwen3:4b + llama3.2:3b)
set -euo pipefail
cd "$(dirname "$0")"
export PATH="$HOME/.local/bin:$PATH"
mode="${1:-}"
case "$mode" in rapide) opt="--small";; complet) opt="";; *) echo "usage : $0 rapide|complet"; exit 2;; esac
command -v uv >/dev/null 2>&1 || { echo "Lancez d'abord ./installer.sh"; exit 1; }
command -v ollama >/dev/null 2>&1 || { echo "Ollama introuvable : https://ollama.com/download"; exit 1; }
echo "ATTENTION : ce script ÉCRASE results/, data/corpus_eval.jsonl et site/. Retour aux résultats livrés : git restore ."
read -r -p "Continuer (o/N) ? " r; [[ "$r" =~ ^[oOyY]$ ]] || exit 0
uv sync --frozen --extra dev
run() { uv run --frozen python scripts/reproduce.py $opt; }
if [ "$mode" = complet ] && command -v caffeinate >/dev/null 2>&1; then caffeinate -i bash -c "$(declare -f run); opt='$opt'; run"
elif [ "$mode" = complet ] && command -v systemd-inhibit >/dev/null 2>&1; then systemd-inhibit --what=sleep --why="Vigenere-Squad" bash -c "$(declare -f run); opt='$opt'; run"
else run; fi
echo "OK : résultats dans results/metrics.json et site/index.html"
