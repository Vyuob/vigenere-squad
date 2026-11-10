"""Outils d'analyse et d'attaque déterministes. Aucun appel LLM ici : « le code calcule »."""
from __future__ import annotations

import math
from collections import Counter
from functools import reduce

import numpy as np

from . import ciphers
from .lang import FREQ_FR, IC_FR, IC_RANDOM, A, modele, normaliser, seuil_plausible, vers_ints, vers_str


def _x(texte: str) -> np.ndarray:
    return vers_ints(normaliser(texte))


# ---------- statistiques ----------
def indice_coincidence(texte: str) -> dict:
    x = _x(texte); n = len(x)
    if n < 2:
        return {"ic": 0.0, "n": n}
    c = np.bincount(x, minlength=26)
    return {"ic": float((c * (c - 1)).sum() / (n * (n - 1))), "n": n,
            "ref_fr": IC_FR, "ref_aleatoire": round(IC_RANDOM, 4)}


def frequences(texte: str, top: int = 6) -> dict:
    x = _x(texte); c = np.bincount(x, minlength=26) / max(len(x), 1)
    ordre = np.argsort(-c)[:top]
    return {"top": {A[i]: round(float(c[i]), 4) for i in ordre}}


def ic_colonnes(texte: str, longueur: int) -> dict:
    x = _x(texte); longueur = int(longueur)
    ics = []
    for j in range(longueur):
        col = x[j::longueur]; n = len(col)
        if n < 2:
            continue
        c = np.bincount(col, minlength=26)
        ics.append((c * (c - 1)).sum() / (n * (n - 1)))
    return {"longueur": longueur, "ic_moyen": float(np.mean(ics)) if ics else 0.0}


def kasiski(texte: str, max_len: int = 20, taille: int = 3) -> dict:
    s = normaliser(texte)
    pos: dict[str, list[int]] = {}
    for i in range(len(s) - taille + 1):
        pos.setdefault(s[i:i + taille], []).append(i)
    dist = [b - a for p in pos.values() if len(p) > 1 for a, b in zip(p, p[1:])]
    votes = Counter()
    for d in dist:
        for f in range(2, max_len + 1):
            if d % f == 0:
                votes[f] += 1
    top = votes.most_common(5)
    return {"n_repetitions": len(dist), "longueurs_candidates": [{"longueur": f, "votes": v} for f, v in top]}


def friedman(texte: str) -> dict:
    ic = indice_coincidence(texte); n = ic["n"]
    if n < 3:
        return {"longueur_estimee": None}
    kp, kr = IC_FR, IC_RANDOM
    den = (n - 1) * ic["ic"] - kr * n + kp
    est = (kp - kr) * n / den if den > 1e-9 else None
    return {"longueur_estimee": round(est, 2) if est and 0 < est < 100 else None}


def _chi2_decalage(col: np.ndarray) -> tuple[int, float]:
    """Meilleur décalage k tel que col-k ressemble au français (chi² minimal)."""
    n = len(col); c = np.bincount(col, minlength=26).astype(float)
    best = (0, 1e18)
    for k in range(26):
        obs = np.roll(c, -k)  # compte des lettres claires après décalage
        chi = float((((obs - n * FREQ_FR) ** 2) / (n * FREQ_FR)).sum())
        if chi < best[1]:
            best = (k, chi)
    return best


def chi2_cesar(texte: str) -> dict:
    x = _x(texte)
    k, chi = _chi2_decalage(x)
    clair = ciphers.cesar(normaliser(texte), k, decrypt=True)
    return {"cle": k, "chi2": round(chi, 1), "clair": clair, "type": "cesar",
            "score": modele().score(clair)}


def force_brute_affine(texte: str) -> dict:
    s = normaliser(texte); m = modele(); best = None
    for a in ciphers.AFFINE_A:
        for b in range(26):
            p = ciphers.affine(s, a, b, decrypt=True)
            sc = m.score(p)
            if best is None or sc > best[0]:
                best = (sc, a, b, p)
    return {"cle": [best[1], best[2]], "clair": best[3], "score": best[0], "type": "affine", "n_cles": 312}


# ---------- Vigenère / Beaufort ----------
def attaque_vigenere(texte: str, longueur: int, variante: str = "vigenere") -> dict:
    s = normaliser(texte); L = int(longueur)
    if not 1 <= L <= 40:
        raise ValueError("longueur hors [1,40]")
    x = vers_ints(s)
    if variante == "beaufort":
        x = 25 - x
    ks = [_chi2_decalage(x[j::L])[0] for j in range(L)]
    if variante == "beaufort":
        ks = [(25 - k) % 26 for k in ks]
        cle = "".join(A[k] for k in ks)
        clair = ciphers.beaufort(s, cle)
    else:
        cle = "".join(A[k] for k in ks)
        clair = ciphers.vigenere(s, cle, decrypt=True)
    return {"cle": cle, "clair": clair, "type": variante, "longueur": L, "score": modele().score(clair)}


# ---------- Autokey ----------
def attaque_autoclave(texte: str, max_cle: int = 10, prefixe: int = 300) -> dict:
    s = normaliser(texte); m = modele(); pre = s[:prefixe]
    best = None
    for L in range(1, max_cle + 1):
        cle = [0] * L
        cur = m.score(ciphers.autoclave(pre, "".join(A[k] for k in cle), True))
        for _ in range(3):
            changed = False
            for j in range(L):
                for k in range(26):
                    if k == cle[j]:
                        continue
                    t = cle[:]; t[j] = k
                    sc = m.score(ciphers.autoclave(pre, "".join(A[i] for i in t), True))
                    if sc > cur + 1e-9:
                        cur, cle, changed = sc, t, True
            if not changed:
                break
        if best is None or cur > best[0] + 0.02:  # préférence aux clés courtes à score voisin
            best = (cur, "".join(A[k] for k in cle))
    clair = ciphers.autoclave(s, best[1], True)
    return {"cle": best[1], "clair": clair, "type": "autoclave", "score": m.score(clair)}


# ---------- Substitution (hill-climbing + recuit) ----------
def attaque_substitution(texte: str, iterations: int = 4000, redemarrages: int = 6, seed: int = 0) -> dict:
    s = normaliser(texte); x = vers_ints(s); m = modele()
    rng = np.random.default_rng(seed)
    c = np.bincount(x, minlength=26)
    freq_ordre = np.argsort(-FREQ_FR)  # lettres claires par fréquence décroissante
    best = (-1e9, None)
    for r in range(redemarrages):
        # init : appariement par rang de fréquence (+ bruit aux redémarrages)
        ordre_c = np.argsort(-(c + (rng.random(26) * (r * 0.8) * (c.mean() + 1))))
        inv = np.empty(26, dtype=np.int64)  # inv[chiffré] = clair
        inv[ordre_c] = freq_ordre
        cur = m.score_ints(inv[x]); T = 0.05
        for it in range(iterations):
            i, j = rng.integers(0, 26, 2)
            if i == j:
                continue
            inv[i], inv[j] = inv[j], inv[i]
            sc = m.score_ints(inv[x])
            if sc >= cur or rng.random() < math.exp((sc - cur) / max(T, 1e-6)):
                cur = sc
            else:
                inv[i], inv[j] = inv[j], inv[i]
            T *= 0.9985
            if cur > best[0]:
                best = (cur, inv.copy())
    inv = best[1]
    clair = vers_str(inv[x])
    cle = "".join(A[int(np.where(inv == p)[0][0])] for p in range(26))  # cle[clair] = chiffré
    return {"cle": cle, "clair": clair, "score": best[0], "type": "substitution"}


# ---------- Linguiste ----------
def score_quadrigrammes(texte: str) -> dict:
    m = modele(); sc = m.score(texte); seuil = seuil_plausible(m)
    return {"score": round(sc, 4), "seuil": round(seuil, 4), "au_dessus_seuil": bool(sc > seuil),
            "apercu": normaliser(texte)[:80]}


# ---------- Pédagogue ----------
def generer_exercice(texte: str, type_chiffre: str = "cesar", graine: int = 0) -> dict:
    """Nouvel exercice du même type, clé tirée par graine ; renvoie énoncé + corrigé."""
    rng = np.random.default_rng(graine)
    clair = normaliser(texte)[:60]
    cle = ciphers.cle_aleatoire(type_chiffre, rng)
    cle_j = list(cle) if isinstance(cle, tuple) else cle
    return {"type": type_chiffre, "enonce": ciphers.chiffrer(type_chiffre, clair, cle), "cle": cle_j,
            "corrige_cle": str(cle), "corrige_clair": clair}


def solveur_outils_seuls(texte: str, seed: int = 0) -> dict:
    """Baseline sans agents ni LLM : attaques par complexité de clé croissante (rasoir d'Ockham),
    on s'arrête à la première dont le clair dépasse le seuil de plausibilité ; sinon meilleur score."""
    s = normaliser(texte); seuil = seuil_plausible(modele()); cands = []
    etapes = [lambda: chi2_cesar(s), lambda: force_brute_affine(s)]
    for var in ("vigenere", "beaufort"):
        etapes.append(lambda var=var: max((attaque_vigenere(s, L, var) for L in range(2, 13)), key=lambda r: r["score"]))
    etapes += [lambda: attaque_autoclave(s), lambda: attaque_substitution(s, iterations=2500, redemarrages=3, seed=seed)]
    for e in etapes:
        r = e(); cands.append(r)
        if r["score"] > seuil:
            return r
    return max(cands, key=lambda r: r["score"])
