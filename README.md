# Vigenère-Squad

Une équipe de 4 agents (LLM **local**) qui identifie et casse des textes français chiffrés par **César, affine, Vigenère, Beaufort, autoclave et substitution**,
puis explique sa démarche. *Le LLM décide et explique ; le code calcule.*

```
chiffré → Classifieur (IC, Kasiski) → Cryptanalyste (attaque) → Linguiste (plausible ?) ─non→ hypothèse suivante
                                                                         └oui→ Pédagogue (explication + exercice)
```

Orchestrateur explicite (`src/vigenere_squad/orchestrator.py`), état partagé typé, **liste d'outils fermée par agent**, trace JSONL de chaque message et appel d'outil,
replis en cas de panne. Détails : [SYSTEM_CARD.md](SYSTEM_CARD.md), [docs/THREAT_MODEL.md](docs/THREAT_MODEL.md), [AUDIT.md](AUDIT.md), [AI_USAGE.md](AI_USAGE.md).

## Démarrage rapide (un double-clic)
Télécharger la branche `main` (bouton **Code → Download ZIP** de la page du dépôt, ou `git clone`), décompresser, puis :

| Action | Windows | Linux / macOS |
|---|---|---|
| Installer + tests | `installer.bat` | `./installer.sh` |
| Démonstration locale (navigateur) | `demo.bat` | `./demo.sh` |
| Vérifier tests + empreintes + signature | `verifier.bat` | `./verifier.sh` |

Prérequis : une connexion Internet à la première exécution (le script installe `uv`, qui installe Python et les dépendances). Sous Windows, un `.bat` téléchargé peut déclencher un avertissement : « Informations complémentaires » puis « Exécuter quand même ». Les installeurs sont sur `main` (ils ne figurent pas dans l'archive Zenodo de `v1.0.0`). Détails : [INSTALL.md](INSTALL.md). La reproduction avec LLM demande en plus Ollama.

## En ligne de commande (sans LLM, 1 minute)
```bash
uv sync --frozen --extra dev        # Python ≥ 3.11
make test                           # 61 tests
uv run vigenere-squad resoudre "PHVVDJH..."          # politique à règles
uv run vigenere-squad demo                           # interface locale http://127.0.0.1:8765
uv run vigenere-squad rejouer traces/scripted/vigenere-200-0-r0.jsonl   # rejouer une trace
```

## Plateformes (Linux, macOS, Windows)
Le code Python, les tests et la reproduction sont multiplateformes ; la CI exécute les tests sur **Ubuntu, macOS et Windows**.
`make` n'est pas installé par défaut sous Windows : utiliser les commandes équivalentes (aucune dépendance à bash, `sha256sum` ou `rm`) :

| `make …` | Équivalent sans make (PowerShell, cmd, bash) |
|---|---|
| `install` | `uv sync --frozen --extra dev` |
| `test` | `uv run --frozen pytest` |
| `reproduce` | `uv run --frozen python scripts/reproduce.py` |
| `reproduce-small` | `uv run --frozen python scripts/reproduce.py --small` |
| (sans Ollama) | `uv run --frozen python scripts/reproduce.py --no-llm` |
| `hashes` / `verify` | `uv run --frozen python scripts/hashes.py [--check]` |
| `clean` | `uv run --frozen python scripts/clean.py` |

Fins de ligne : `.gitattributes` force LF, donc les SHA-256 (corpus, `SHA256SUMS`) sont identiques sur tous les systèmes.
Seule la mesure du pic mémoire est indisponible sous Windows (`null` dans `ENVIRONMENT.json`). Alternative isolée : `docker build -t vigenere-squad .`.

## Reproduire les résultats (avec LLM, portable 8 Go sans GPU)
```bash
# 1. installer Ollama (https://ollama.com) puis :
make models            # qwen3:4b + llama3.2:3b  (8 Go : contexte 4096 ; 16 Go : qwen3:8b possible, voir config)
# 2. tout reproduire
make reproduce         # tests → corpus → baseline → agents → LLM ×2 → métriques → figures → site → SHA256SUMS
make reproduce-small   # version rapide (qwen3:0.6b, 1 répétition) = ce que fait la CI
```
Sorties : `results/metrics.json` (toutes les métriques), `results/raw/` (une ligne par essai), `results/figures/`, `results/ENVIRONMENT.json`
(versions, matériel, *digest* des modèles, SHA-256 des prompts, corpus et config), `traces/` (JSONL), `site/index.html`.
Un seul fichier de configuration : [config/experiment.yaml](config/experiment.yaml) (graines, modèles, température, contexte).

## Protocole d'évaluation
- Corpus : 6 chiffrements × 5 longueurs (50–1000 lettres) × 5 = 150 textes, graine 42, textes clairs **jamais vus** par le modèle de langue.
- Chaque mesure répétée **3 fois** (graines 42, 43, 44) ; succès = ≥ 95 % de lettres exactes.
- Comparaisons : (a) **outils seuls** (sans agent), (b) agents à règles **sans LLM**, (c) LLM principal ≤ 8 Go, (d) second LLM.
- Robustesse : 5 % de lettres erronées, clair anglais ; injection de pannes (LLM 0–30 %, outils 0–30 %) ; Kasiski vs autoclave ; distance d'unicité de Shannon.

## Résultats
Voir la [page des résultats](https://vyuob.github.io/vigenere-squad/) (générée depuis `results/metrics.json`) et `docs/rapport.pdf`.

## Limites
Corpus modeste, LLM évalué sur un sous-ensemble, français uniquement : voir la section « Limites connues » de [SYSTEM_CARD.md](SYSTEM_CARD.md).

## Licence et citation
MIT (code) ; CC BY 4.0 (documentation, données, résultats), voir [LICENSES.md](LICENSES.md) ; écarts au sujet : [ECARTS.md](ECARTS.md) ; journal des prompts : [PROMPTS_CHANGELOG.md](PROMPTS_CHANGELOG.md). Citer via [CITATION.cff](CITATION.cff) ; archive Zenodo de la release `v1.0.0` (DOI de toutes les versions : [10.5281/zenodo.24110322](https://doi.org/10.5281/zenodo.24110322)).
