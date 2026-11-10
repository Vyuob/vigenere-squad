"""Génération du corpus d'évaluation (déterministe, graine fixée) et variantes de robustesse."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np

from .tools import ciphers
from .tools.lang import DATA, normaliser


def texte_test(langue: str = "fr") -> str:
    if langue == "en":
        return normaliser((DATA / "sample_en_test.txt").read_text(encoding="utf-8"))
    for p in (DATA / "test_fr.txt", DATA / "sample_fr_test.txt"):
        if p.exists():
            return normaliser(p.read_text(encoding="utf-8"))
    raise FileNotFoundError("corpus de test absent")


def generer(seed: int, longueurs: list[int], par_cellule: int, chiffres=ciphers.CHIFFRES, langue: str = "fr") -> list[dict]:
    rng = np.random.default_rng(seed)
    src = texte_test(langue)
    out = []
    for nom in chiffres:
        for L in longueurs:
            for i in range(par_cellule):
                L2 = min(L, len(src))
                off = int(rng.integers(0, len(src) - L2 + 1))
                clair = src[off:off + L2]
                cle = ciphers.cle_aleatoire(nom, rng)
                cle_j = list(cle) if isinstance(cle, tuple) else cle
                out.append({"id": f"{nom}-{L}-{i}", "chiffre": nom, "longueur": L2, "cle": cle_j, "clair": clair,
                            "chiffre_texte": ciphers.chiffrer(nom, clair, cle), "offset": off, "langue": langue})
    return out


def bruiter(chiffre: str, taux: float, seed: int) -> str:
    """Remplace aléatoirement une fraction `taux` de lettres du chiffré (fautes de transmission/frappe)."""
    rng = np.random.default_rng(seed)
    x = list(chiffre)
    for i in range(len(x)):
        if rng.random() < taux:
            x[i] = chr(65 + int(rng.integers(0, 26)))
    return "".join(x)


def sauver(corpus: list[dict], chemin: Path) -> str:
    chemin.parent.mkdir(parents=True, exist_ok=True)
    data = "\n".join(json.dumps(c, ensure_ascii=False, sort_keys=True) for c in corpus) + "\n"
    chemin.write_text(data, encoding="utf-8", newline="\n")
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


def charger(chemin: Path) -> list[dict]:
    return [json.loads(l) for l in chemin.read_text(encoding="utf-8").splitlines() if l.strip()]
