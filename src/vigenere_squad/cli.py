"""CLI : résoudre un chiffré, rejouer une trace, lancer la démo locale."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .llm import OllamaClient, ScriptedClient
from .orchestrator import Orchestrateur


def _client(modele: str | None):
    return OllamaClient(modele) if modele else ScriptedClient()


def cmd_resoudre(a):
    texte = Path(a.fichier).read_text(encoding="utf-8") if a.fichier else a.texte
    st, tr = Orchestrateur(_client(a.llm), trace_dir=a.trace_dir).resoudre(texte, a.run_id)
    print(f"statut      : {st.statut}")
    print(f"chiffrement : {st.type_chiffre}   clé : {st.cle}")
    print(f"hypothèses  : {' -> '.join(t.hypothese + ('✓' if t.accepte else '✗') for t in st.tentatives)}")
    print(f"clair       : {(st.clair or '')[:200]}")
    print(f"explication : {st.explication}")
    print(f"exercice    : {st.exercice}")
    print(f"[{st.appels_llm} appels LLM, {st.appels_outils} appels d'outils, {st.duree_s} s]")


def cmd_rejouer(a):
    for line in Path(a.trace).read_text(encoding="utf-8").splitlines():
        e = json.loads(line)
        reste = {k: v for k, v in e.items() if k not in ("seq", "run_id", "t_ms", "agent", "type")}
        print(f"{e['seq']:>3} {e['t_ms']:>8.1f}ms  {e['agent']:<13} {e['type']:<14} {json.dumps(reste, ensure_ascii=False)[:160]}")


def cmd_demo(a):
    from .demo import servir
    servir(a.port, a.llm)


def main(argv=None):
    p = argparse.ArgumentParser(prog="vigenere-squad", description="Équipe d'agents qui casse les chiffrements classiques")
    sp = p.add_subparsers(dest="cmd", required=True)
    r = sp.add_parser("resoudre"); r.add_argument("texte", nargs="?", default=""); r.add_argument("--fichier")
    r.add_argument("--llm", help="modèle Ollama (ex. qwen3:4b) ; sans cette option : politique à règles")
    r.add_argument("--trace-dir"); r.add_argument("--run-id", default="cli"); r.set_defaults(f=cmd_resoudre)
    j = sp.add_parser("rejouer"); j.add_argument("trace"); j.set_defaults(f=cmd_rejouer)
    d = sp.add_parser("demo"); d.add_argument("--port", type=int, default=8765); d.add_argument("--llm"); d.set_defaults(f=cmd_demo)
    a = p.parse_args(argv)
    if a.cmd == "resoudre" and not (a.texte or a.fichier):
        p.error("fournir un texte ou --fichier")
    a.f(a)


if __name__ == "__main__":
    main(sys.argv[1:])
