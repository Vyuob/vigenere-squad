"""Clients LLM : Ollama (local), scripté (baseline sans LLM), injecteur de fautes."""
from __future__ import annotations

import json
import urllib.request

import numpy as np


# Schéma JSON imposé à Ollama (sorties structurées) : un petit modèle ne peut plus recopier le message reçu au lieu d'y répondre.
SCHEMA_REPONSE = {
    "type": "object",
    "properties": {
        "action": {"type": "string", "enum": ["tool", "final"]},
        "tool": {"type": "string"}, "args": {"type": "object"},
        "famille": {"type": "string"}, "hypotheses": {"type": "array", "items": {"type": "string"}},
        "justification": {"type": "string"}, "commentaire": {"type": "string"},
        "plausible": {"type": "boolean"}, "raison": {"type": "string"},
        "explication": {"type": "string"}, "exercice": {"type": "string"},
    },
    "required": ["action"],
}


class OllamaClient:
    def __init__(self, model: str, host: str = "http://localhost:11434", temperature: float = 0.0,
                 seed: int = 42, num_ctx: int = 4096, timeout: int = 300, num_predict: int = 512):
        self.model, self.host, self.temperature, self.seed, self.num_ctx, self.timeout = model, host, temperature, seed, num_ctx, timeout
        self.num_predict = num_predict  # borne la sortie : un petit modèle en mode JSON peut sinon boucler jusqu'au timeout
        self.name = f"ollama:{model}"

    def _post(self, path: str, body: dict | None):
        req = urllib.request.Request(self.host + path, data=json.dumps(body).encode() if body is not None else None,
                                     headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=self.timeout) as r:
            return json.loads(r.read())

    def digest(self) -> str | None:
        try:
            for m in self._post("/api/tags", None)["models"]:
                if m["name"] == self.model or m["name"].split(":")[0] == self.model:
                    return m.get("digest")
        except Exception:  # noqa: BLE001
            return None

    def chat(self, role: str, system: str, user: str) -> str:
        body = {"model": self.model, "stream": False, "format": SCHEMA_REPONSE, "think": False,
                "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
                "options": {"temperature": self.temperature, "seed": self.seed, "num_ctx": self.num_ctx, "num_predict": self.num_predict}}
        return self._post("/api/chat", body)["message"]["content"]


class ScriptedClient:
    """Politique à règles qui joue le rôle du LLM (ablation « sans LLM », CI, tests).
    Même protocole JSON que le LLM : l'orchestrateur ne voit pas la différence."""
    name = "scripted"

    def digest(self):
        return None

    def chat(self, role: str, system: str, user: str) -> str:
        msg = json.loads(user)
        return json.dumps(getattr(self, "_" + role)(msg), ensure_ascii=False)

    @staticmethod
    def _ok(msg):  # observations réussies : {outil: [(args, résultat), ...]}
        d: dict = {}
        for o in msg["observations"]:
            if "resultat" in o:
                d.setdefault(o["outil"], []).append((o["args"], o["resultat"]))
        return d

    def _classifieur(self, msg):
        ok = self._ok(msg)
        if "indice_coincidence" not in ok:
            return {"action": "tool", "tool": "indice_coincidence", "args": {}}
        ic = ok["indice_coincidence"][0][1]["ic"]
        if ic > 0.062:
            return {"action": "final", "famille": "monoalphabetique", "hypotheses": ["cesar", "affine", "substitution"],
                    "justification": f"IC={ic:.4f}, proche du français (0,078) : une seule substitution"}
        if "kasiski" not in ok:
            return {"action": "tool", "tool": "kasiski", "args": {}}
        rep = ok["kasiski"][0][1]["n_repetitions"]
        ordre = ["vigenere", "beaufort", "autoclave"] if rep >= 3 else ["autoclave", "vigenere", "beaufort"]
        return {"action": "final", "famille": "polyalphabetique", "hypotheses": ordre,
                "justification": f"IC={ic:.4f} proche de l'aléatoire ; {rep} répétitions de trigrammes"}

    def _cryptanalyste(self, msg):
        h = msg["contexte"]["hypothese"]; ok = self._ok(msg)
        simple = {"cesar": "chi2_cesar", "affine": "force_brute_affine", "substitution": "attaque_substitution",
                  "autoclave": "attaque_autoclave"}
        if h in simple:
            t = simple[h]
            if t in ok:
                return {"action": "final", "tool": t, "commentaire": f"attaque {h} exécutée"}
            return {"action": "tool", "tool": t, "args": {"seed": msg["contexte"].get("graine", 0)} if t == "attaque_substitution" else {}}
        # vigenere / beaufort : Kasiski -> candidats -> IC colonnes -> attaque
        if "kasiski" not in ok:
            return {"action": "tool", "tool": "kasiski", "args": {"max_len": 12}}
        cands = sorted(c["longueur"] for c in ok["kasiski"][0][1]["longueurs_candidates"][:4])
        if not cands or ok["kasiski"][0][1]["n_repetitions"] < 3:
            cands = list(range(2, 9))
        vus = {a["longueur"]: r["ic_moyen"] for a, r in ok.get("ic_colonnes", [])}
        for L in cands:
            if L not in vus:
                return {"action": "tool", "tool": "ic_colonnes", "args": {"longueur": L}}
        mx = max(vus.values())
        L = min(l for l, v in vus.items() if v >= 0.85 * mx)
        for a, _ in ok.get("attaque_vigenere", []):
            if a.get("longueur") == L and a.get("variante") == h:
                return {"action": "final", "tool": "attaque_vigenere", "commentaire": f"longueur {L}, variante {h}"}
        return {"action": "tool", "tool": "attaque_vigenere", "args": {"longueur": L, "variante": h}}

    def _linguiste(self, msg):
        ok = self._ok(msg)
        if "score_quadrigrammes" not in ok:
            return {"action": "tool", "tool": "score_quadrigrammes", "args": {}}
        r = ok["score_quadrigrammes"][0][1]
        return {"action": "final", "plausible": bool(r["au_dessus_seuil"]),
                "raison": f"score {r['score']} {'>' if r['au_dessus_seuil'] else '<='} seuil {r['seuil']}"}

    def _pedagogue(self, msg):
        ok = self._ok(msg); c = msg["contexte"]
        if "generer_exercice" not in ok:
            return {"action": "tool", "tool": "generer_exercice", "args": {"type_chiffre": c["type"], "graine": 1}}
        return {"action": "final", "explication": (
            f"Le texte a été identifié comme un chiffrement {c['type']} (clé : {c['cle']}). "
            f"Raisonnement : {c['resume']}. Vérification : le texte déchiffré est du français plausible."),
            "exercice": ok["generer_exercice"][0][1]["enonce"]}


class FaultyClient:
    """Enveloppe : avec probabilité p, la réponse du LLM est corrompue (JSON invalide / action inconnue)."""

    def __init__(self, inner, p: float, seed: int = 0):
        self.inner, self.p, self.rng = inner, p, np.random.default_rng(seed)
        self.name = f"{inner.name}+fautes{p}"
        self.injectees = 0

    def digest(self):
        return self.inner.digest()

    def chat(self, role, system, user):
        out = self.inner.chat(role, system, user)
        if self.rng.random() < self.p:
            self.injectees += 1
            return self.rng.choice(["Voici ma réponse : {oups", '{"action": "rm -rf /"}', ""])
        return out
