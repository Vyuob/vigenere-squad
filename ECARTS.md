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
- **Longueur de clé.** Le corpus principal a des clés de 3 à 8 lettres (3 à 7 pour l'autoclave). La figure « longueur minimale de succès
  en fonction de la longueur de clé » est produite par une expérience dédiée sur Vigenère (clés de 3 à 12, 10 textes par cellule,
  `evaluate --complements`), comparée à la distance d'unicité de Shannon ; elle ne couvre pas les autres chiffrements.
- **Grille d'explications automatique.** La grille sur 10 explications tirées au hasard est notée par un programme (5 critères × 2 points),
  pas par un humain, et porte sur les agents à règles ; les explications des LLM ne sont pas notées.

## Non réalisé
- **Vidéo de démonstration** (lien n°7 de la fiche).
- **Historique de commits** : bref (dépôt recréé avant publication) ; il n'atteste pas un travail étalé dans le temps.
