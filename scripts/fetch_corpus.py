"""(Optionnel) Corpus français plus grand : télécharge les URLs listées dans data/sources.txt (une par ligne,
fichiers texte UTF-8 du domaine public, p. ex. Project Gutenberg) et écrit data/train_fr.txt et data/test_fr.txt.
Les lignes commençant par '#' sont ignorées ; la DERNIÈRE URL sert de corpus de TEST (ouvrage jamais vu à l'entraînement).
Sans sources.txt, rien n'est téléchargé : l'échantillon original livré (data/sample_fr_*.txt) est utilisé."""
import re
import sys
import urllib.request
from pathlib import Path

D = Path(__file__).resolve().parents[1] / "data"


def nettoyer(t: str) -> str:
    m = re.search(r"\*\*\* ?START OF.*?\*\*\*", t, re.S); e = re.search(r"\*\*\* ?END OF", t)
    if m and e:
        t = t[m.end():e.start()]
    return t


def main():
    src = D / "sources.txt"
    if not src.exists():
        print("data/sources.txt absent -> corpus d'échantillon livré conservé."); return 0
    urls = [l.strip() for l in src.read_text(encoding="utf-8").splitlines() if l.strip() and not l.startswith("#")]
    if len(urls) < 2:
        print("Il faut >= 2 URLs (entraînement ... test)."); return 1
    textes = []
    for u in urls:
        with urllib.request.urlopen(u, timeout=60) as r:
            textes.append(nettoyer(r.read().decode("utf-8", "replace")))
        print("OK", u, len(textes[-1]), "caractères")
    (D / "train_fr.txt").write_text("\n".join(textes[:-1]), encoding="utf-8", newline="\n")
    (D / "test_fr.txt").write_text(textes[-1][:200_000], encoding="utf-8", newline="\n")
    print("écrit data/train_fr.txt et data/test_fr.txt")
    return 0


if __name__ == "__main__":
    sys.exit(main())
