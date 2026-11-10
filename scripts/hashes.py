"""SHA-256 des livrables (multiplateforme, remplace sha256sum).

    python scripts/hashes.py           # écrit SHA256SUMS
    python scripts/hashes.py --check   # vérifie SHA256SUMS
"""
import hashlib
import sys
from pathlib import Path

R = Path(__file__).resolve().parents[1]
DOSSIERS = ["results", "data", "config", "docs", "src", "tests", "traces"]
FICHIERS = ["pyproject.toml", "uv.lock", "Makefile", "Dockerfile"]


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def lister() -> list[str]:
    out = []
    for d in DOSSIERS:
        for p in (R / d).rglob("*"):
            if p.is_file() and "__pycache__" not in p.parts and p.suffix != ".pyc":
                out.append(p.relative_to(R).as_posix())
    out += [f for f in FICHIERS if (R / f).is_file()]
    return sorted(set(out))  # tri par octets, identique sur tous les OS


def ecrire() -> int:
    lignes = [f"{sha(R / f)}  {f}" for f in lister()]
    (R / "SHA256SUMS").write_text("\n".join(lignes) + "\n", encoding="utf-8", newline="\n")
    print(f"SHA256SUMS : {len(lignes)} fichiers")
    return 0


def verifier() -> int:
    ko = 0
    for ligne in (R / "SHA256SUMS").read_text(encoding="utf-8").splitlines():
        h, f = ligne.split("  ", 1)
        p = R / f
        if not p.is_file() or sha(p) != h:
            print("ECHEC", f); ko += 1
    print("OK" if ko == 0 else f"{ko} fichier(s) différent(s)")
    return 1 if ko else 0


if __name__ == "__main__":
    sys.exit(verifier() if "--check" in sys.argv else ecrire())
