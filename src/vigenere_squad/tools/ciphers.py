"""Chiffrements classiques (chiffrement/déchiffrement) — A-Z uniquement."""
from __future__ import annotations

import math
import numpy as np

from .lang import vers_ints, vers_str, normaliser

AFFINE_A = [a for a in range(1, 26) if math.gcd(a, 26) == 1]  # 12 valeurs -> 12*26 = 312 clés


def _cle_ints(cle: str) -> np.ndarray:
    return vers_ints(normaliser(cle))


def cesar(texte: str, k: int, decrypt=False) -> str:
    x = vers_ints(texte)
    return vers_str(x - k if decrypt else x + k)


def affine(texte: str, a: int, b: int, decrypt=False) -> str:
    x = vers_ints(texte)
    if not decrypt:
        return vers_str(a * x + b)
    inv = pow(a, -1, 26)
    return vers_str(inv * (x - b))


def vigenere(texte: str, cle: str, decrypt=False) -> str:
    x = vers_ints(texte); k = _cle_ints(cle)
    ks = np.resize(k, len(x))
    return vers_str(x - ks if decrypt else x + ks)


def beaufort(texte: str, cle: str, decrypt=False) -> str:
    """C = K - P ; involutif (déchiffrer = chiffrer)."""
    x = vers_ints(texte); k = _cle_ints(cle)
    return vers_str(np.resize(k, len(x)) - x)


def autoclave(texte: str, cle: str, decrypt=False) -> str:
    """Autokey : flux = mot-clé puis texte clair."""
    x = vers_ints(texte); k = list(_cle_ints(cle)); m = len(k)
    out = np.empty_like(x)
    if not decrypt:
        flux = k + list(x)
        for i in range(len(x)):
            out[i] = (x[i] + flux[i]) % 26
    else:
        p = []
        for i in range(len(x)):
            ki = k[i] if i < m else p[i - m]
            p.append(int((x[i] - ki) % 26))
        out = np.array(p, dtype=np.int64)
    return vers_str(out)


def substitution(texte: str, cle: str, decrypt=False) -> str:
    """`cle` = permutation de 26 lettres : lettre claire A+i -> cle[i]."""
    assert len(set(cle)) == 26
    if decrypt:
        table = {c: chr(65 + i) for i, c in enumerate(cle)}
    else:
        table = {chr(65 + i): c for i, c in enumerate(cle)}
    return "".join(table[c] for c in texte)


CHIFFRES = ("cesar", "affine", "vigenere", "beaufort", "autoclave", "substitution")


def chiffrer(nom: str, texte: str, cle):
    f = {"cesar": lambda: cesar(texte, cle), "affine": lambda: affine(texte, *cle),
         "vigenere": lambda: vigenere(texte, cle), "beaufort": lambda: beaufort(texte, cle),
         "autoclave": lambda: autoclave(texte, cle), "substitution": lambda: substitution(texte, cle)}
    return f[nom]()


def cle_aleatoire(nom: str, rng: np.random.Generator):
    alpha = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    if nom == "cesar":
        return int(rng.integers(1, 26))
    if nom == "affine":
        return (int(rng.choice(AFFINE_A[1:])), int(rng.integers(1, 26)))
    if nom in ("vigenere", "beaufort"):
        n = int(rng.integers(3, 9))
        return "".join(rng.choice(list(alpha), n))
    if nom == "autoclave":
        n = int(rng.integers(3, 8))
        return "".join(rng.choice(list(alpha), n))
    if nom == "substitution":
        return "".join(rng.permutation(list(alpha)))
    raise ValueError(nom)


def dechiffrer(nom: str, texte: str, cle):
    f = {"cesar": lambda: cesar(texte, cle, True), "affine": lambda: affine(texte, cle[0], cle[1], True),
         "vigenere": lambda: vigenere(texte, cle, True), "beaufort": lambda: beaufort(texte, cle),
         "autoclave": lambda: autoclave(texte, cle, True), "substitution": lambda: substitution(texte, cle, True)}
    return f[nom]()
