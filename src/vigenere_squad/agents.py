"""Agents spécialisés : boucle LLM <-> outils, validation de schéma, repli en cas d'échec."""
from __future__ import annotations

import json
from pathlib import Path

from pydantic import BaseModel, ConfigDict, ValidationError, field_validator

from .tools.ciphers import CHIFFRES
from .tools.registry import ALLOWLIST, Registre, ToolError, ToolRefused
from .trace import Trace

PROMPTS = Path(__file__).parent / "prompts"
ROLES = ("classifieur", "cryptanalyste", "linguiste", "pedagogue")
MAX_STEPS = {"classifieur": 5, "cryptanalyste": 14, "linguiste": 4, "pedagogue": 5}


class Reponse(BaseModel):
    model_config = ConfigDict(extra="allow")
    action: str
    tool: str | None = None
    args: dict = {}

    @field_validator("action")
    @classmethod
    def _a(cls, v):
        if v not in ("tool", "final"):
            raise ValueError("action ∈ {tool, final}")
        return v


def _valider_final(role: str, r: Reponse):
    d = r.model_extra or {}
    if role == "classifieur":
        h = d.get("hypotheses")
        if not isinstance(h, list) or not h or any(x not in CHIFFRES for x in h):
            raise ValueError("hypotheses doit être une liste non vide parmi " + ",".join(CHIFFRES))
    if role == "linguiste" and not isinstance(d.get("plausible"), bool):
        raise ValueError("plausible doit être booléen")
    if role == "pedagogue" and not isinstance(d.get("explication"), str):
        raise ValueError("explication (str) requise")
    if role == "cryptanalyste" and not isinstance(r.tool, str):
        raise ValueError("tool requis")


class Agent:
    def __init__(self, role: str, llm, registre: Registre, trace: Trace):
        self.role, self.llm, self.reg, self.trace = role, llm, registre, trace
        self.system = (PROMPTS / f"{role}.md").read_text(encoding="utf-8")
        self.stats = {"llm": 0, "outils": 0, "format_invalide": 0, "refus": 0, "pannes": 0}

    def run(self, texte: str, contexte: dict) -> dict | None:
        """Retourne {'final': dict, 'observations': [...], 'dernier_attaque': résultat complet|None} ou None (échec -> repli)."""
        obs: list[dict] = []; dernier = None; erreurs = 0
        outils = self.reg.decrire(self.role)
        for step in range(MAX_STEPS[self.role]):
            user = json.dumps({"role": self.role, "contexte": contexte, "outils_autorises": outils,
                               "observations": obs,
                               "consigne": 'Réponds maintenant par UN seul objet JSON de la forme {"action": "tool" ou "final", ...}. Ne recopie pas ce message.'},
                              ensure_ascii=False)
            try:
                raw = self.llm.chat(self.role, self.system, user); self.stats["llm"] += 1
            except OSError as e:  # TimeoutError, ConnectionError, URLError… : le LLM est injoignable ou trop lent -> repli
                self.stats["pannes_llm"] = self.stats.get("pannes_llm", 0) + 1
                self.trace.log(self.role, "llm_indisponible", detail=f"{type(e).__name__}: {str(e)[:150]}")
                return None
            self.trace.log(self.role, "llm", step=step, reponse=raw[:600])
            try:
                rep = Reponse.model_validate(json.loads(raw))
                if rep.action == "final":
                    _valider_final(self.role, rep)
            except (json.JSONDecodeError, ValidationError, ValueError) as e:
                self.stats["format_invalide"] += 1; erreurs += 1
                self.trace.log(self.role, "erreur_format", detail=str(e)[:200])
                obs.append({"erreur_format": str(e)[:150]})
                if erreurs > 3:
                    return None
                continue
            if rep.action == "final":
                return {"final": {**(rep.model_extra or {}), "tool": rep.tool}, "observations": obs, "dernier_attaque": dernier}
            try:
                res = self.reg.appeler(self.role, rep.tool or "", rep.args, texte)
                self.stats["outils"] += 1
                self.trace.log(self.role, "outil", outil=rep.tool, args=rep.args, resultat=_court(res))
                if self.reg.genre(rep.tool) == "attaque":
                    dernier = {"outil": rep.tool, **res}
                obs.append({"outil": rep.tool, "args": rep.args, "resultat": _court(res)})
            except ToolRefused as e:
                self.stats["refus"] += 1; erreurs += 1
                self.trace.log(self.role, "outil_refuse", outil=rep.tool, detail=str(e))
                obs.append({"erreur": f"refusé: {e}"})
            except ToolError as e:
                self.stats["pannes"] += 1; erreurs += 1
                self.trace.log(self.role, "outil_panne", outil=rep.tool, detail=str(e))
                obs.append({"erreur": f"panne: {e}"})
            if erreurs > 6:
                return None
        return None


def _court(res: dict) -> dict:
    """Résultat réduit pour le contexte du LLM : pas de texte complet (le code le garde)."""
    out = {}
    for k, v in res.items():
        if k == "clair":
            out["clair_apercu"] = v[:60]
        elif isinstance(v, float):
            out[k] = round(v, 4)
        else:
            out[k] = v
    return out
