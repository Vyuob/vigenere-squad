# Auto-audit — v1.0.0

Ce document dit ce qui a été vérifié, ce qui ne l'a pas été, et ce qui est faible. Les chiffres viennent de `results/metrics.json`.

## Vérifié (reproductible par `make test` / `make reproduce`)
- **57 tests** passent ; couverture ≥ 98 % sur `tools/analysis.py`, `tools/ciphers.py`, `tools/lang.py`, 86 % globale (seuil CI : 70 %).
- Vecteurs de test connus (César, affine, Vigenère « LEMON »), aller-retour chiffrement/déchiffrement des 6 chiffres, déterminisme du corpus (graine 42).
- Sécurité : outil hors liste blanche refusé et tracé, arguments hors bornes refusés, JSON invalide rejeté puis repli, le code a le dernier mot sur le Linguiste.
- Évaluation (profil `full`, politique à règles, 150 textes × 3 répétitions) : outils seuls **86,7 %** de succès (σ répétitions 0,009), agents à règles **85,6 %** (σ 0,003).
  Textes ≥ 500 lettres : 100 % pour les deux. Substitution < 200 lettres et Beaufort < 200 lettres : faibles (figures).
- Pannes : jusqu'à 30 % de réponses LLM corrompues → succès 85 % (contre 98 % sans panne, sous-ensemble 200/500 lettres) ; les pannes d'outils sont absorbées par les nouvelles tentatives.

## Constats négatifs (à ne pas masquer)
1. **Les agents ne battent pas la baseline** : 85,6 % contre 86,7 %. Sur Vigenère/Beaufort courts, le choix de longueur par Kasiski + IC des colonnes est moins bon que l'essai de toutes les longueurs 2–12 + score quadrigrammes. L'intérêt du système multi-agents est la modularité, la traçabilité, l'explication et la robustesse aux pannes, pas la précision.
2. Le seuil de plausibilité du Linguiste accepte parfois un clair partiellement faux (ex. Vigenère de 80 lettres, 80 % de lettres exactes).
3. Corpus d'entraînement minuscule (~6,7 ko) : modèle de langue modeste ; textes de test (~1,6 k lettres) qui se recouvrent aux grandes longueurs.
4. Entropie estimée à 3,1 bits/lettre (borne haute, trop grande car modèle pauvre) → distances d'unicité surestimées (valeurs de `shannon` à lire comme ordres de grandeur).
5. Robustesse : 5 % de lettres erronées → 49 % de succès ; clair anglais → 56 % (le Linguiste est entraîné sur le français, Beaufort/Vigenère courts échouent).

## Non vérifié / à faire avant remise
- **Mesures LLM** (`llm` dans `metrics.json`) : produites uniquement par `make reproduce` sur une machine avec Ollama ; dans le dépôt elles portent sur `qwen3:4b` (6 textes, 1 répétition) ; le second modèle n'a pas été évalué.
- Durée et mémoire de `make reproduce` avec LLM : à relever (`meta.duree_totale_s`, `meta.pic_memoire_mo`) ; non mesurées par l'auteur de l'audit.
- DOI Zenodo, signature de `SHA256SUMS`, page GitHub Pages, exécution CI sur le tag : à effectuer depuis le compte GitHub.
- Pas de vidéo de démonstration.
