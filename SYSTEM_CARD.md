# Fiche système — Vigenère-Squad v1.0.0

**But.** Identifier et casser, sans clé, des textes français chiffrés par César, affine, Vigenère, Beaufort, autoclave (autokey) ou substitution
simple, et expliquer la démarche (usage pédagogique).

**Architecture.** 4 agents à rôles disjoints, orchestrés par `orchestrator.py` (état partagé typé `EtatPartage`) :
Classifieur (IC, Kasiski → ordre des hypothèses) → Cryptanalyste (attaque) → Linguiste (plausibilité) → Pédagogue (explication + exercice).
Boucle de vérification : si le Linguiste rejette, l'orchestrateur teste l'hypothèse suivante (jusqu'à 6). Repli explicite si un agent échoue.

**Répartition LLM / code.** *Le LLM décide* (quel outil, quelle longueur de clé, verdict, explication). *Le code calcule* (statistiques, attaques,
scores, déchiffrement). Le texte déchiffré n'est jamais recopié par le LLM : il est lu dans le résultat de l'outil. Le verdict final de plausibilité
est celui du code (seuil), les désaccords LLM/code sont comptés.

**Outils (liste fermée par agent).** Voir `src/vigenere_squad/tools/registry.py` (`ALLOWLIST`). Aucun outil shell, fichier ou réseau.

**Modèles évalués.** Définis dans `config/experiment.yaml` ; étiquette et *digest* relevés dans `results/ENVIRONMENT.json`. Température 0, graine fixée,
contexte 4096 (8 Go).

**Données.** Textes originaux CC0 (voir `data/README.md`), petit corpus.

**Limites connues.**
- Corpus d'entraînement du modèle de langue très petit (~6,7 ko) ; la substitution sur textes courts (≤ 100 lettres) est peu fiable.
- Sans LLM, la politique à règles des agents obtient des taux **comparables, légèrement inférieurs** à la baseline « outils seuls » (voir `results/metrics.json` : `agents_scriptes` vs `outils_seuls`), surtout sur Vigenère/Beaufort courts. L'apport des agents n'est donc pas un gain de précision mais de modularité, traçabilité et explication ; ne pas le présenter autrement.
- Le LLM n'est pas évalué à grande échelle (sous-ensemble minimal : 6 textes × 1 répétition × 1 modèle, `qwen3:4b`) pour tenir sur un portable.
- Un clair non français (anglais) fait échouer le Linguiste : le système suppose le français.
- Substitutions affines/César reconnues comme « substitution » possibles : le critère de succès est le clair retrouvé, pas le nom du chiffrement.

**Usages à éviter.** Ne protège rien et ne casse aucun chiffrement moderne (AES, RSA…) ; outil pédagogique uniquement.
