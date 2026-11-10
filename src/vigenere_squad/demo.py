"""Démo locale (serveur HTTP standard, aucune dépendance) : colle un chiffré, voit la trace des agents."""
from __future__ import annotations

import html
import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs

from .cli import _client
from .orchestrator import Orchestrateur

PAGE = """<!doctype html><meta charset=utf-8><title>Vigenère-Squad</title>
<style>body{{font:16px system-ui;max-width:56rem;margin:2rem auto;padding:0 1rem}}textarea{{width:100%;height:7rem}}
pre{{background:#f4f4f4;padding:.6rem;overflow:auto;font-size:13px}}@media(prefers-color-scheme:dark){{body{{background:#161616;color:#eee}}pre{{background:#262626}}}}</style>
<h1>Vigenère-Squad</h1><p>Colle un texte chiffré (César, affine, Vigenère, Beaufort, autoclave, substitution), en français.</p>
<form method=post><textarea name=t placeholder="Texte chiffré">{t}</textarea><br><button>Déchiffrer</button></form>{res}"""


def _rendu(texte: str, llm: str | None) -> str:
    st, tr = Orchestrateur(_client(llm)).resoudre(texte, "demo")
    ev = "\n".join(f"{e['seq']:>3} {e['agent']:<13} {e['type']:<12} " + json.dumps({k: v for k, v in e.items() if k not in ('seq', 'run_id', 't_ms', 'agent', 'type')}, ensure_ascii=False)[:150] for e in tr.events)
    return (f"<h2>{html.escape(st.statut)} — {html.escape(str(st.type_chiffre))}, clé {html.escape(str(st.cle))}</h2>"
            f"<pre>{html.escape((st.clair or '')[:600])}</pre><p>{html.escape(st.explication or '')}</p>"
            f"<p><b>Exercice :</b> <code>{html.escape(st.exercice or '')}</code></p><h3>Trace des agents</h3><pre>{html.escape(ev)}</pre>")


def servir(port: int = 8765, llm: str | None = None):
    class H(BaseHTTPRequestHandler):
        def _send(self, body):
            b = body.encode(); self.send_response(200); self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(b))); self.end_headers(); self.wfile.write(b)

        def do_GET(self): self._send(PAGE.format(t="", res=""))

        def do_POST(self):
            n = min(int(self.headers.get("Content-Length", 0)), 20000)
            t = parse_qs(self.rfile.read(n).decode()).get("t", [""])[0]
            self._send(PAGE.format(t=html.escape(t), res=_rendu(t, llm) if t.strip() else ""))

        def log_message(self, *a): pass
    print(f"Démo sur http://127.0.0.1:{port}  (Ctrl-C pour arrêter ; écoute en local uniquement)")
    HTTPServer(("127.0.0.1", port), H).serve_forever()
