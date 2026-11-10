"""Modèle de langue français (n-grammes 1..4 interpolés) et utilitaires de texte."""
from __future__ import annotations

import math
import unicodedata
from functools import lru_cache
from pathlib import Path

import numpy as np

A = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
# Fréquences du français (%, source usuelle : corpus littéraire) — sert au chi² (César/Vigenère)
FREQ_FR = np.array([
    7.64, 0.90, 3.26, 3.67, 14.72, 1.07, 0.87, 0.74, 7.53, 0.61, 0.05, 5.46, 2.97,
    7.10, 5.38, 3.02, 1.36, 6.55, 7.95, 7.24, 6.31, 1.63, 0.04, 0.43, 0.31, 0.14]) / 100.0
IC_FR = 0.0778
IC_RANDOM = 1 / 26
DATA = Path(__file__).resolve().parents[3] / "data"


def normaliser(texte: str) -> str:
    """Majuscules A-Z uniquement (accents supprimés)."""
    t = unicodedata.normalize("NFKD", texte)
    return "".join(c for c in t.upper() if "A" <= c <= "Z")


def vers_ints(texte: str) -> np.ndarray:
    return np.frombuffer(texte.encode("ascii"), dtype=np.uint8).astype(np.int64) - 65


def vers_str(a) -> str:
    return (np.asarray(a, dtype=np.int64) % 26 + 65).astype(np.uint8).tobytes().decode("ascii")


class ModeleFR:
    """P(c | 3 lettres précédentes) interpolé sur les n-grammes 1..4, table log10 26^4."""

    def __init__(self, corpus: str, lambdas=(0.65, 0.25, 0.08, 0.02)):
        t = normaliser(corpus)
        x = vers_ints(t)
        c1 = np.bincount(x, minlength=26).astype(float) + 0.5
        c2 = np.zeros((26, 26)); c3 = np.zeros((26, 26, 26)); c4 = np.zeros((26, 26, 26, 26))
        np.add.at(c2, (x[:-1], x[1:]), 1)
        np.add.at(c3, (x[:-2], x[1:-1], x[2:]), 1)
        np.add.at(c4, (x[:-3], x[1:-2], x[2:-1], x[3:]), 1)
        p1 = c1 / c1.sum()
        p2 = (c2 + 0.1 * p1[None, :]) / (c2.sum(1, keepdims=True) + 0.1)
        p3 = (c3 + 0.1 * p2[None, :, :]) / (c3.sum(2, keepdims=True) + 0.1)
        p4 = (c4 + 0.1 * p3[None, :, :, :]) / (c4.sum(3, keepdims=True) + 0.1)
        l4, l3, l2, l1 = lambdas
        # table[a,b,c,d] = log10 P(d | a,b,c)
        p = l4 * p4 + l3 * p3[None, :, :, :] + l2 * p2[None, None, :, :] + l1 * p1[None, None, None, :]
        self.table = np.log10(p)
        self.flat = self.table.reshape(-1)
        # bigrammes+unigramme pour textes très courts (<4)
        self.logp1 = np.log10(p1)

    def score_ints(self, x: np.ndarray) -> float:
        """Log10-vraisemblance moyenne par lettre (plus haut = plus français)."""
        if len(x) < 4:
            return float(self.logp1[x].mean()) if len(x) else -9.0
        idx = ((x[:-3] * 26 + x[1:-2]) * 26 + x[2:-1]) * 26 + x[3:]
        return float(self.flat[idx].mean())

    def score(self, texte: str) -> float:
        return self.score_ints(vers_ints(normaliser(texte)))


@lru_cache(maxsize=4)
def charger_corpus(chemin: str | None = None) -> str:
    """Corpus d'entraînement : `data/train_fr.txt` s'il existe (téléchargé), sinon l'échantillon livré."""
    for p in ([Path(chemin)] if chemin else []) + [DATA / "train_fr.txt", DATA / "sample_fr_train.txt"]:
        if p.exists():
            return p.read_text(encoding="utf-8")
    raise FileNotFoundError("aucun corpus d'entraînement (lancer `make data`)")


@lru_cache(maxsize=2)
def modele(chemin: str | None = None) -> ModeleFR:
    return ModeleFR(charger_corpus(chemin))


def seuil_plausible(m: ModeleFR, n_ech: int = 40) -> float:
    """Seuil de plausibilité = milieu entre le score moyen d'un texte français et celui d'un texte aléatoire."""
    rng = np.random.default_rng(0)
    alea = float(np.mean([m.score_ints(rng.integers(0, 26, 300)) for _ in range(n_ech)]))
    fr = m.score_ints(vers_ints(normaliser(charger_corpus())[:3000]))
    return (fr + alea) / 2
