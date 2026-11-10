# Usage de l'IA dans ce projet

**Dans le produit.** Les agents du système s'appuient sur un modèle de langage *local* (Ollama : `qwen3:4b`, `llama3.2:3b`, `qwen3:0.6b` en CI),
sans service distant ni abonnement. Le LLM choisit les outils et rédige les explications ; il ne calcule rien (voir `SYSTEM_CARD.md`).

**Dans la conception et l'écriture.** L'architecture, le code (`src/`), les tests, les documents et la configuration CI ont été produits
**avec l'assistance de Claude (Anthropic)**, via une session de travail pilotée par l'auteur, qui a défini le sujet, choisi le projet,
relu et exécuté le code. Aucun code externe n'a été copié ; les algorithmes (indice de coïncidence, Kasiski, Friedman, chi², recuit simulé)
sont classiques et décrits dans la littérature. Les textes français du dossier `data/` ont été rédigés pour ce projet (CC0).

**Vérification humaine.** Les résultats chiffrés du dépôt proviennent exclusivement de l'exécution de `make reproduce`
(`results/metrics.json`) ; aucune valeur n'est saisie à la main dans le rapport ou le site.

**Limites.** L'assistant ne pouvait pas exécuter de LLM local ni télécharger de corpus dans son environnement : les mesures LLM
ont été produites sur la machine de l'auteur (voir `results/ENVIRONMENT.json`).
