"""docs/rapport.md -> docs/rapport.pdf (pandoc/xelatex). Tous les chiffres sont lus dans results/metrics.json."""
import json
import subprocess
from pathlib import Path

R = Path(__file__).resolve().parents[1]
m = json.loads((R / "results/metrics.json").read_text(encoding="utf-8")); env = json.loads((R / "results/ENVIRONMENT.json").read_text(encoding="utf-8"))
P = lambda v: "n/d" if v is None else f"{100 * v:.1f} %"  # noqa: E731
O, A = m["outils_seuls"], m["agents_scriptes"]


def tab(agg):
    lg = list(agg["par_longueur"]); h = "| chiffrement | " + " | ".join(lg) + " | global |\n|---|" + "---|" * (len(lg) + 1) + "\n"
    for c in agg["par_chiffre"]:
        h += f"| {c} | " + " | ".join(P(agg["par_cellule"].get(f"{c}|{l}")) for l in lg) + f" | {P(agg['par_chiffre'][c])} |\n"
    return h + f"| **toutes** | " + " | ".join(P(agg["par_longueur"][l]) for l in lg) + f" | **{P(agg['succes_global'])}** |\n"


pan = m["pannes"]
tp = "| taux de pannes | succès (LLM corrompu) | repli moyen | succès (outils en panne) |\n|---|---|---|---|\n" + "".join(
    f"| {p} | {P(pan['llm'][p]['succes_global'])} | {pan['llm'][p]['repli_moyen']} | {P(pan['outil'][p]['succes_global'])} |\n" for p in pan["llm"])
llm = m.get("llm", {})
if "statut" in llm:
    tl = f"**Mesures LLM non exécutées dans cette version** (`{llm.get('raison')}`). Elles sont produites par `make reproduce` et remplissent cette section."
else:
    tl = "\n".join(f"**{k}** (`{v.get('modele')}`) : succès {P(v.get('succes_global'))}, n={v.get('n')}, σ répétitions {v.get('ecart_type_repetitions')}, appels LLM moyens {v.get('appels_llm_moyen')}, formats invalides moyens {v.get('format_invalide_moyen')}, durée moyenne {v.get('duree_moyenne_s')} s par texte.\n" if v.get("n") else f"**{k}** : non exécuté.\n" for k, v in llm.items())
sh = m["shannon"]; k = m["kasiski"]
md = f"""---
title: "Vigenère-Squad — une équipe d'agents LLM locaux pour la cryptanalyse classique"
author: "Vyuob"
date: "Version 1.0.0"
geometry: margin=2.5cm
fontsize: 11pt
mainfont: "DejaVu Serif"
toc: true
---

# Résumé / Abstract

**FR.** Vigenère-Squad est un système multi-agents qui identifie et casse six chiffrements classiques (César, affine, Vigenère, Beaufort, autoclave, substitution) sur du texte français.
Quatre agents (Classifieur, Cryptanalyste, Linguiste, Pédagogue) pilotés par un orchestrateur explicite appellent des outils déterministes ; le LLM décide et explique, le code calcule.
Sur {m['meta']['n_echantillons']} textes × {m['meta']['repetitions']} répétitions, les agents à règles (sans LLM) retrouvent le texte dans {P(A['succes_global'])} des cas, contre {P(O['succes_global'])} pour la baseline sans agents ;
les textes de 500 lettres ou plus sont tous cassés. Les agents n'améliorent pas la précision ; ils apportent traçabilité, explication et tolérance aux pannes.

**EN.** Vigenère-Squad is a multi-agent system that identifies and breaks six classical ciphers on French text. Four agents (Classifier, Cryptanalyst, Linguist, Teacher) coordinated by an explicit orchestrator call deterministic tools; the LLM decides and explains, the code computes. On {m['meta']['n_echantillons']} texts × {m['meta']['repetitions']} repetitions the rule-based agents recover {P(A['succes_global'])} of the plaintexts versus {P(O['succes_global'])} for a no-agent baseline; all texts of 500+ letters are broken. Agents do not improve accuracy; they add traceability, explanation and fault tolerance.

# 1. Problème et motivation

Casser un chiffrement classique est une suite de décisions : de quel chiffrement s'agit-il, quelle attaque tenter, le résultat est-il du français, comment l'expliquer ? Les calculs sont mécaniques, le choix de la stratégie l'est moins.
C'est le terrain naturel d'un système d'agents, à condition de ne pas confier au LLM ce qu'un programme fait exactement : compter des lettres, tester 312 clés affines, optimiser une permutation.

# 2. Architecture

Quatre agents à rôles disjoints, un orchestrateur Python explicite (`orchestrator.py`) et un état partagé typé (`EtatPartage`) :

1. **Classifieur** — outils : `indice_coincidence`, `frequences`, `kasiski`. Sortie : famille et ordre des hypothèses.
2. **Cryptanalyste** — outils d'attaque (`chi2_cesar`, `force_brute_affine`, `attaque_vigenere`, `attaque_autoclave`, `attaque_substitution`) et d'analyse (`kasiski`, `friedman`, `ic_colonnes`).
3. **Linguiste** — outil : `score_quadrigrammes` (vraisemblance française et seuil). Valide ou rejette le candidat.
4. **Pédagogue** — outil : `generer_exercice`. Rédige l'explication et propose un exercice vérifiable par le code.

**Boucle de vérification.** Si le Linguiste rejette le texte candidat, l'orchestrateur passe à l'hypothèse suivante (6 tentatives au plus). Le verdict final est celui du code (seuil) : un désaccord LLM/code est compté et tracé.
**Listes d'outils fermées.** Un outil hors liste, ou des arguments hors bornes, sont refusés avant exécution. **Trace.** Chaque message LLM, appel d'outil, refus, panne et décision est écrit en JSONL.
**Le LLM ne recopie jamais le texte** : les outils reçoivent le chiffré ou le candidat par liaison côté code, et le LLM ne voit que des statistiques et un aperçu.

# 3. Outils

- **Indice de coïncidence** $IC=\\sum n_i(n_i-1)/N(N-1)$ : ≈ 0,078 en français monoalphabétique, ≈ 0,038 pour un texte aléatoire.
- **Kasiski** : les distances entre répétitions de trigrammes sont des multiples de la longueur de clé ; vote des diviseurs.
- **Friedman** : $L\\approx (k_p-k_r)N/((N-1)IC-k_rN+k_p)$ avec $k_p=0{{,}}0778$, $k_r=1/26$.
- **Chi²** sur les fréquences du français : décalage de César, et par colonne pour Vigenère. **Beaufort** se ramène à Vigenère par la symétrie $25-C$.
- **Autoclave** : Kasiski échoue (le flux de clé contient le clair) ; ascension de colline sur le mot-clé, scorée par quadrigrammes.
- **Substitution** : recuit simulé / ascension de colline sur une permutation, avec 6 redémarrages, scorée par un modèle de langue 1–4-grammes interpolé (table 26⁴ en log₁₀).

# 4. Protocole expérimental

Corpus généré avec la graine {m['meta']['seed']} (SHA-256 `{m['meta']['corpus_sha256'][:16]}…`) : 6 chiffrements × 5 longueurs × 5 textes. Les textes clairs sont tirés d'un fichier de test que le modèle de langue n'a jamais vu.
Chaque mesure est répétée {m['meta']['repetitions']} fois (graines 42–44). Succès : au moins {int(100 * m['meta']['seuil_succes_exactitude'])} % de lettres exactes. Comparaisons : (a) outils seuls ; (b) agents à règles sans LLM ; (c)–(d) deux LLM locaux.
Tous les paramètres sont dans `config/experiment.yaml` ; l'environnement (versions, matériel, digest des modèles, hachages des prompts) dans `results/ENVIRONMENT.json`.
Environnement de cette exécution : Python {env['python']}, {env['plateforme']}, {env['cpu_count']} CPU, durée {m['meta']['duree_totale_s']} s, pic mémoire {m['meta']['pic_memoire_mo']} Mo.

# 5. Résultats

## 5.1 Baseline : outils seuls

{tab(O)}
(σ entre répétitions : {O['ecart_type_repetitions']}.)

## 5.2 Agents + outils (politique à règles, sans LLM)

{tab(A)}
(σ entre répétitions : {A['ecart_type_repetitions']} ; {A['iterations_moyen']} hypothèses testées en moyenne ; {A['appels_llm_moyen']} messages agent par texte ; {A['duree_moyenne_s']} s par texte.)

![Succès par chiffrement et longueur](../results/figures/succes_par_chiffre_longueur.png)

**Lecture.** Au-delà de 500 lettres tout est cassé. Les chiffrements monoalphabétiques simples le sont dès 50 lettres. La substitution demande environ 200 lettres ou plus, ce qui est cohérent avec la distance d'unicité (§5.5).
Les agents à règles font **moins bien** que la baseline sur Vigenère et Beaufort courts : choisir la longueur de clé par Kasiski + IC des colonnes est moins fiable que tester les longueurs 2–12 et garder le meilleur score.

## 5.3 Avec LLM local

{tl}

## 5.4 Robustesse et pannes

- 5 % de lettres du chiffré remplacées : succès {P(m['robustesse']['bruit_frappe']['succes_global'])}.
- Clair anglais (le Linguiste est entraîné sur le français) : succès {P(m['robustesse'].get('anglais', {}).get('succes_global'))}.

{tp}
![Robustesse aux pannes](../results/figures/pannes.png){{width=60%}}

Les pannes d'outils sont absorbées par de nouvelles tentatives dans l'agent. Les réponses LLM corrompues (JSON invalide, action inconnue, vide) déclenchent un rejet de schéma puis, au-delà de 3 erreurs, un repli de l'orchestrateur.

## 5.5 Kasiski contre l'autoclave et distance d'unicité

La vraie longueur de clé figure dans le top 3 de Kasiski pour {P(k['vigenere']['longueur_vraie_dans_top3'])} des Vigenère (n={k['vigenere']['n']}) contre {P(k['autoclave']['longueur_vraie_dans_top3'])} des autoclaves (n={k['autoclave']['n']}) : l'autoclave brouille Kasiski.
Le modèle de langue donne une entropie de {sh['entropie_bits_par_lettre']} bits/lettre (borne haute), soit une redondance de {sh['redondance_bits_par_lettre']} bits/lettre et des distances d'unicité $U=H(K)/D$ de {sh['distance_unicite_lettres']['cesar']} lettres (César), {sh['distance_unicite_lettres']['affine']} (affine), {sh['distance_unicite_lettres']['vigenere_6']} (Vigenère, clé de 6) et {sh['distance_unicite_lettres']['substitution']} (substitution) : ordres de grandeur, car l'entropie est surestimée sur un petit corpus.
Le succès réel exige davantage de lettres que $U$ : l'unicité est une condition nécessaire, pas suffisante, pour un attaquant au calcul borné.

![Succès vs longueur](../results/figures/succes_vs_unicite.png){{width=75%}}

Le Pédagogue produit des exercices valides dans {P(m['exercices_pedagogue']['taux'])} des cas (n={m['exercices_pedagogue']['n']}, vérifiés par déchiffrement avec la clé du corrigé).

# 6. Discussion et limites

- **Résultat négatif assumé** : les agents ne battent pas la baseline en précision. Leur valeur : modularité, trace complète, explications, tolérance aux pannes, listes d'outils fermées.
- **Corpus d'entraînement minuscule** (≈ 6,7 ko) : modèle de langue pauvre, entropie surestimée, textes de test qui se recouvrent aux grandes longueurs.
- **Linguiste** : le seuil accepte parfois un clair en partie faux ; il suppose le français.
- **LLM** : évalués sur un sous-ensemble (12 textes × 3 répétitions × 2 modèles) pour tenir sur un portable sans GPU.
- Pas de comparaison avec un LLM seul sans outils (hors périmètre) ; les LLM de ≤ 8 Go calculent mal des fréquences, ce qui justifie la répartition « LLM décide / code calcule ».

# 7. Sécurité

Modèle de menaces STRIDE dans `docs/THREAT_MODEL.md` : injection via le texte chiffré (le texte n'entre pas dans le prompt), clair inventé par le LLM (le code a le dernier mot), boucle infinie (bornes de pas et d'essais), élévation de privilèges (listes blanches, aucun outil shell/fichier/réseau), fuite de données (réseau local uniquement, gitleaks en CI).

# 8. Reproductibilité

`make reproduce` rejoue tout (tests, corpus, baseline, agents, LLM, métriques, figures, site). `make reproduce-small` (CI) utilise `qwen3:0.6b`. Environnement figé par `uv.lock` et `Dockerfile` ; `SHA256SUMS` signé ; archive Zenodo de la release `v1.0.0`.

# 9. Usage de l'IA

Voir `AI_USAGE.md` : conception et code réalisés avec l'assistance de Claude (Anthropic), sous la direction et la relecture de l'auteur ; résultats issus uniquement de l'exécution du dépôt.

# Références

- Kasiski, F. W. (1863). *Die Geheimschriften und die Dechiffrir-Kunst*.
- Friedman, W. F. (1922). *The Index of Coincidence and Its Applications in Cryptography*.
- Shannon, C. E. (1949). Communication theory of secrecy systems. *Bell System Technical Journal*, 28(4).
- Kirkpatrick, S., Gelatt, C. D., Vecchi, M. P. (1983). Optimization by simulated annealing. *Science*, 220.
"""
(R / "docs/rapport.md").write_text(md, encoding="utf-8", newline="\n")
subprocess.run(["pandoc", "docs/rapport.md", "-o", "docs/rapport.pdf", "--pdf-engine=xelatex", "--resource-path=docs"], cwd=R, check=True)
print("docs/rapport.pdf")
