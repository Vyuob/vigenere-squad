"""Figures des résultats (matplotlib, palette daltonien-compatible, valeurs annotées)."""
from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

CHIFFRES = ["cesar", "affine", "vigenere", "beaufort", "autoclave", "substitution"]
COUL = ["#0072B2", "#D55E00", "#009E73", "#CC79A7", "#E69F00", "#56B4E9"]


def _matrice(agg):
    ls = sorted({int(k.split("|")[1]) for k in agg["par_cellule"]})
    M = np.array([[agg["par_cellule"].get(f"{c}|{l}", np.nan) for l in ls] for c in CHIFFRES], dtype=float)
    return ls, M


def tracer(m: dict, out: Path):
    out.mkdir(parents=True, exist_ok=True)
    # 1. heatmaps baseline vs agents
    fig, axes = plt.subplots(1, 2, figsize=(10, 3.6), sharey=True)
    for ax, key, titre in zip(axes, ("outils_seuls", "agents_scriptes"), ("Outils seuls (sans agents)", "Agents + outils (règles)")):
        ls, M = _matrice(m[key])
        im = ax.imshow(M, vmin=0, vmax=1, cmap="viridis", aspect="auto")
        ax.set_xticks(range(len(ls)), [str(l) for l in ls]); ax.set_yticks(range(len(CHIFFRES)), CHIFFRES)
        ax.set_xlabel("longueur du texte (lettres)"); ax.set_title(titre, fontsize=10)
        for i in range(M.shape[0]):
            for j in range(M.shape[1]):
                ax.text(j, i, f"{M[i, j]:.2f}", ha="center", va="center", color="white" if M[i, j] < 0.6 else "black", fontsize=8)
    fig.colorbar(im, ax=axes, label="taux de succès (exactitude ≥ 95 %)")
    fig.savefig(out / "succes_par_chiffre_longueur.png", dpi=150, bbox_inches="tight"); plt.close(fig)
    # 2. pannes
    fig, ax = plt.subplots(figsize=(5.5, 3.5))
    for nom, c in (("llm", COUL[0]), ("outil", COUL[1])):
        ps = sorted(m["pannes"][nom], key=float)
        ax.plot([float(p) for p in ps], [m["pannes"][nom][p]["succes_global"] for p in ps], "o-", color=c,
                label="réponses LLM corrompues" if nom == "llm" else "appels d'outils en panne")
    ax.set_ylim(0, 1.05); ax.set_xlabel("taux de pannes injectées"); ax.set_ylabel("taux de succès"); ax.legend(frameon=False)
    ax.set_title("Robustesse aux pannes (orchestrateur + replis)", fontsize=10)
    fig.savefig(out / "pannes.png", dpi=150, bbox_inches="tight"); plt.close(fig)
    # 3. succès vs longueur + distance d'unicité
    fig, ax = plt.subplots(figsize=(6.5, 3.8))
    ag = m["agents_scriptes"]; ls = sorted({int(k.split("|")[1]) for k in ag["par_cellule"]})
    for c, col in zip(CHIFFRES, COUL):
        ax.plot(ls, [ag["par_cellule"].get(f"{c}|{l}", np.nan) for l in ls], "o-", color=col, label=c, ms=4)
    for k, ls_ in (("substitution", ":"), ("vigenere_6", "--")):
        u = m["shannon"]["distance_unicite_lettres"][k]
        ax.axvline(u, color="gray", ls=ls_, lw=1); ax.text(u, 0.02, f" U({k})≈{u:.0f}", fontsize=7, color="gray")
    ax.set_xscale("log"); ax.set_xlabel("longueur du texte (lettres, échelle log)"); ax.set_ylabel("taux de succès"); ax.set_ylim(0, 1.05)
    ax.legend(fontsize=7, ncol=2, frameon=False); ax.set_title("Succès vs longueur et distance d'unicité de Shannon", fontsize=10)
    fig.savefig(out / "succes_vs_unicite.png", dpi=150, bbox_inches="tight"); plt.close(fig)
