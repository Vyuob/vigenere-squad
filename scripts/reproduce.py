"""Reproduction complète SANS make (Windows, macOS, Linux).

    uv run --frozen python scripts/reproduce.py          # tout (profil full, 2 modèles Ollama)
    uv run --frozen python scripts/reproduce.py --small  # rapide (qwen3:0.6b, comme la CI)
    uv run --frozen python scripts/reproduce.py --no-llm # sans Ollama : baseline + agents scriptés
"""
import shutil
import subprocess
import sys
from pathlib import Path

R = Path(__file__).resolve().parents[1]
PY = sys.executable
small, no_llm = "--small" in sys.argv, "--no-llm" in sys.argv


def run(*cmd):
    print("$", " ".join(cmd), flush=True)
    subprocess.run(cmd, cwd=R, check=True)


if not small:
    run(PY, "-m", "pytest")
if not no_llm:
    if not shutil.which("ollama"):
        sys.exit("Ollama introuvable : installez-le (https://ollama.com/download) ou utilisez --no-llm")
    for m in (["qwen3:0.6b"] if small else ["qwen3:4b", "llama3.2:3b"]):
        run("ollama", "pull", m)
run(PY, "-m", "vigenere_squad.evaluate", "--profil", "small" if small else "full", *([] if no_llm else ["--llm"]))
run(PY, "scripts/build_site.py")
if not small:
    run(PY, "scripts/hashes.py")
