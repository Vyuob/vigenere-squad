"""Trace JSONL : un événement par message LLM, appel d'outil, décision ou erreur."""
from __future__ import annotations

import json
import time
from pathlib import Path


class Trace:
    def __init__(self, chemin: str | Path | None = None, run_id: str = "run"):
        self.run_id = run_id
        self.events: list[dict] = []
        self.chemin = Path(chemin) if chemin else None
        self.t0 = time.perf_counter()
        if self.chemin:
            self.chemin.parent.mkdir(parents=True, exist_ok=True)
            self.chemin.write_text("", encoding="utf-8")

    def log(self, agent: str, type_: str, **payload):
        ev = {"seq": len(self.events), "run_id": self.run_id, "t_ms": round((time.perf_counter() - self.t0) * 1000, 1),
              "agent": agent, "type": type_, **payload}
        self.events.append(ev)
        if self.chemin:
            with self.chemin.open("a", encoding="utf-8", newline="\n") as f:
                f.write(json.dumps(ev, ensure_ascii=False, default=str) + "\n")
        return ev

    def count(self, type_: str) -> int:
        return sum(1 for e in self.events if e["type"] == type_)
