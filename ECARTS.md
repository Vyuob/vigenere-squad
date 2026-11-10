# Écarts au sujet et justifications

Ce document liste, sans les masquer, ce qui diffère du sujet (Projet 1) ou n'a pas été réalisé.

## Écarts assumés
- **Corpus.** Le sujet évoque des textes de Gutenberg, des longueurs de 80 à 2 000 caractères et un script `generer_corpus.py`.
  Réalisé : textes originaux (CC BY 4.0, ≈ 6,7 ko d'entraînement), longueurs 50 à 1 000, 150 chiffrés, graine 42, script
  `scripts/generer_corpus.py --seed 42` (SHA-256 identique à `meta.corpus_sha256`). Raison : reproductibilité hors ligne et absence de
  risque de droits. Conséquence : modèle de langue modeste et textes de test qui se recouvrent aux grandes longueurs (voir rapport, limites).
  Un corpus Gutenberg plus grand peut être préparé (`scripts/fetch_corpus.py`, `data/sources.txt`).
- **Démonstrateur.** Interface locale en bibliothèque standard Python (`vigenere-squad demo`) au lieu de Gradio ou Streamlit : aucune
  dépendance supplémentaire dans `uv.lock`. Elle affiche le raisonnement et les appels d'outils **après** résolution (trace complète),
  pas en flux continu.
- **Évaluation LLM minimale.** 6 textes de 200 lettres, 1 répétition par modèle, trois modèles (`qwen3:4b`, `qwen3:0.6b`, `llama3.2:3b`) (le sujet demande ≥ 3 répétitions pour les mesures dépendant
  du modèle) : résultats indicatifs, sans écart type, non significatifs.
- **Longueur de clé.** La figure « succès en fonction de la longueur du texte et distance d'unicité » est fournie ; la figure
  « longueur minimale de succès en fonction de la longueur de clé » n'a pas été produite : les clés ont 3 à 8 lettres (3 à 7 pour
  l'autoclave) au lieu de 3 à 12, et les résultats ne sont pas ventilés par longueur de clé. La longueur minimale de succès à 90 %
  par procédé est fournie dans le rapport (§5.2).

## Non réalisé
- **Vidéo de démonstration** (lien n°7 de la fiche).
- **Grille de qualité des explications** notée sur 10 explications tirées au hasard.
- **Historique de commits** : bref (dépôt recréé avant publication) ; il n'atteste pas un travail étalé dans le temps.
