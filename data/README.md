# Données

| Fichier | Rôle | Origine / licence |
|---|---|---|
| `sample_fr_train.txt` | entraînement du modèle de langue (n-grammes) | texte **original** écrit pour ce projet, CC0 |
| `sample_fr_test.txt` | textes clairs de l'évaluation (jamais vus à l'entraînement) | idem, CC0 |
| `sample_en_test.txt` | test de robustesse (clair anglais) | idem, CC0 |
| `corpus_eval.jsonl` | corpus chiffré généré (graine 42), SHA-256 dans `results/ENVIRONMENT.json` | généré par `src/vigenere_squad/corpus.py` |

**Limite assumée.** L'échantillon livré est petit (~8,7 ko) : le modèle de langue est donc modeste et les textes de test
(~1,6 k lettres) se recouvrent pour les grandes longueurs. Pour un corpus plus grand : créer `data/sources.txt`
(URLs de textes français du domaine public, la dernière servant de test), puis `make data`.
Aucun texte sous droits n'est redistribué.
