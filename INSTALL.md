# Installation et exécution rapide

Prérequis : rien d'autre que ce dépôt ; les scripts installent `uv` (gestionnaire Python) au besoin. Ollama n'est requis que pour reproduire avec un LLM.

| Action | Windows (double-clic ou terminal) | Linux / macOS |
|---|---|---|
| Installer + tests | `installer.bat` | `./installer.sh` |
| Démonstration locale (navigateur) | `demo.bat` | `./demo.sh` |
| Vérifier tests + empreintes + signature | `verifier.bat` | `./verifier.sh` |
| Reproduire (rapide, ≈ 10-15 min) | `reproduire_rapide.bat` | `./reproduire.sh rapide` |
| Reproduire (complet, plusieurs heures) | `reproduire_complet.bat` | `./reproduire.sh complet` |

Les deux reproductions **écrasent** `results/`, `data/corpus_eval.jsonl` et `site/` ; `git restore .` rétablit les résultats livrés.
`reproduire_complet.bat` désactive la mise en veille pendant l'exécution puis la remet à 30 minutes.
Sous Linux/macOS, si les scripts ne sont pas exécutables : `chmod +x *.sh`.
