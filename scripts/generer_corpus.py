"""Régénère le corpus d'évaluation (chiffrés + clés + clairs) à graine fixe.

    uv run --frozen python scripts/generer_corpus.py --seed 42
    uv run --frozen python scripts/generer_corpus.py --seed 42 --out /tmp/corpus.jsonl

Par défaut : 6 procédés x longueurs de config/experiment.yaml x par_cellule = 150 chiffrés. Le SHA-256 affiché doit être
celui de `meta.corpus_sha256` dans results/metrics.json (profil full). Les textes clairs viennent de data/sample_fr_test.txt
(texte original du projet) ; un corpus Gutenberg plus grand peut être préparé avec scripts/fetch_corpus.py (voir data/README.md).
"""
import argparse
from pathlib import Path

import yaml

from vigenere_squad import corpus as C

R = Path(__file__).resolve().parents[1]


def main():
    cfg = yaml.safe_load((R / "config/experiment.yaml").read_text(encoding="utf-8"))
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--seed", type=int, default=cfg["seed"])
    ap.add_argument("--longueurs", type=int, nargs="+", default=cfg["corpus"]["longueurs"])
    ap.add_argument("--par-cellule", type=int, default=cfg["corpus"]["par_cellule"])
    ap.add_argument("--langue", default=cfg["corpus"]["langue"])
    ap.add_argument("--out", default=str(R / "data/corpus_eval.jsonl"))
    a = ap.parse_args()
    corpus = C.generer(a.seed, a.longueurs, a.par_cellule, langue=a.langue)
    h = C.sauver(corpus, Path(a.out))
    print(f"{len(corpus)} chiffrés -> {a.out}\nSHA-256 {h}")


if __name__ == "__main__":
    main()
