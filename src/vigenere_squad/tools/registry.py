"""Registre d'outils : liste fermée par agent, validation stricte des arguments, injection de pannes."""
from __future__ import annotations

import numpy as np

from . import analysis as an
from .ciphers import CHIFFRES


class ToolRefused(Exception):
    """Outil hors liste blanche ou arguments invalides (jamais exécuté)."""


class ToolError(Exception):
    """Panne d'un outil (réelle ou injectée)."""


# nom -> (fonction, genre, description, {arg: (type, min, max) ou liste de valeurs})
OUTILS = {
    "indice_coincidence": (an.indice_coincidence, "analyse", "IC du texte chiffré.", {}),
    "frequences": (an.frequences, "analyse", "Lettres les plus fréquentes.", {"top": (int, 1, 26)}),
    "kasiski": (an.kasiski, "analyse", "Répétitions de trigrammes -> longueurs de clé candidates.", {"max_len": (int, 2, 40)}),
    "friedman": (an.friedman, "analyse", "Estimation de la longueur de clé (Friedman).", {}),
    "ic_colonnes": (an.ic_colonnes, "analyse", "IC moyen des colonnes pour une longueur donnée.", {"longueur": (int, 1, 40)}),
    "chi2_cesar": (an.chi2_cesar, "attaque", "Attaque César par chi² sur fréquences françaises.", {}),
    "force_brute_affine": (an.force_brute_affine, "attaque", "Essai des 312 clés affines.", {}),
    "attaque_vigenere": (an.attaque_vigenere, "attaque", "Vigenère/Beaufort : chi² par colonne, longueur donnée.",
                         {"longueur": (int, 1, 40), "variante": ["vigenere", "beaufort"]}),
    "attaque_autoclave": (an.attaque_autoclave, "attaque", "Autokey : ascension de colline sur mot-clé.", {"max_cle": (int, 1, 12)}),
    "attaque_substitution": (an.attaque_substitution, "attaque", "Substitution : recuit simulé sur quadrigrammes.",
                             {"iterations": (int, 100, 8000), "redemarrages": (int, 1, 10), "seed": (int, 0, 10**6)}),
    "score_quadrigrammes": (an.score_quadrigrammes, "verif", "Score de vraisemblance française + seuil.", {}),
    "generer_exercice": (an.generer_exercice, "exercice", "Nouvel exercice du même type (énoncé + corrigé).",
                         {"type_chiffre": list(CHIFFRES), "graine": (int, 0, 10**6)}),
}

# Listes fermées : un agent ne peut appeler QUE ces outils.
ALLOWLIST = {
    "classifieur": ["indice_coincidence", "frequences", "kasiski"],
    "cryptanalyste": ["kasiski", "friedman", "ic_colonnes", "chi2_cesar", "force_brute_affine",
                      "attaque_vigenere", "attaque_autoclave", "attaque_substitution"],
    "linguiste": ["score_quadrigrammes"],
    "pedagogue": ["generer_exercice"],
}


def _valider(nom: str, args: dict) -> dict:
    spec = OUTILS[nom][3]
    if not isinstance(args, dict):
        raise ToolRefused("args doit être un objet")
    inconnus = set(args) - set(spec)
    if inconnus:
        raise ToolRefused(f"arguments inconnus pour {nom}: {sorted(inconnus)}")
    propres = {}
    for k, v in args.items():
        s = spec[k]
        if isinstance(s, list):
            if v not in s:
                raise ToolRefused(f"{k}={v!r} hors {s}")
        else:
            t, lo, hi = s
            try:
                v = t(v)
            except (TypeError, ValueError):
                raise ToolRefused(f"{k} doit être {t.__name__}")
            if not lo <= v <= hi:
                raise ToolRefused(f"{k}={v} hors [{lo},{hi}]")
        propres[k] = v
    return propres


class Registre:
    def __init__(self, p_panne: float = 0.0, seed: int = 0):
        self.p_panne = p_panne
        self.rng = np.random.default_rng(seed)
        self.appels = 0
        self.refus = 0
        self.pannes = 0

    def decrire(self, role: str) -> list[dict]:
        return [{"nom": n, "description": OUTILS[n][2], "arguments": {k: (v if isinstance(v, list) else f"{v[0].__name__} [{v[1]},{v[2]}]") for k, v in OUTILS[n][3].items()}}
                for n in ALLOWLIST[role]]

    def genre(self, nom: str) -> str:
        return OUTILS[nom][1]

    def appeler(self, role: str, nom: str, args: dict, texte: str) -> dict:
        if nom not in ALLOWLIST.get(role, []):
            self.refus += 1
            raise ToolRefused(f"outil {nom!r} interdit pour {role}")
        args = _valider(nom, args)
        self.appels += 1
        if self.p_panne and self.rng.random() < self.p_panne:
            self.pannes += 1
            raise ToolError(f"panne injectée dans {nom}")
        try:
            return OUTILS[nom][0](texte, **args)
        except ToolRefused:
            raise
        except Exception as e:  # noqa: BLE001 - toute panne d'outil est remontée à l'agent
            raise ToolError(f"{nom}: {e}") from e
