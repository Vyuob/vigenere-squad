"""Supprime les sorties régénérables (multiplateforme, remplace rm -rf)."""
import shutil
from pathlib import Path

R = Path(__file__).resolve().parents[1]
for c in ["results/raw", "results/figures", "traces", ".pytest_cache", "site/figures"]:
    shutil.rmtree(R / c, ignore_errors=True)
(R / ".coverage").unlink(missing_ok=True)
print("nettoyé")
