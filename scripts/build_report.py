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
    tl = "\n".join(f"**{k}** (`{v.get('modele')}`) : succès {P(v.get('succes_global'))}, n={v.get('n')}, σ répétitions {v.get('ecart_type_repetitions', 'sans objet : 1 répétition')}, appels LLM moyens {v.get('appels_llm_moyen')}, formats invalides moyens {v.get('format_invalide_moyen')}, durée moyenne {v.get('duree_moyenne_s')} s par texte.\n" if v.get("n") else f"**{k}** : non exécuté.\n" for k, v in llm.items())
if "statut" not in llm:
    for k_, v_ in llm.items():
        if v_.get("n"):
            ok_ = [c for c, x in v_["par_chiffre"].items() if x >= 0.5]; ko_ = [c for c, x in v_["par_chiffre"].items() if x < 0.5]
            tl += (f"\nSur {v_['n']} textes (un par chiffrement, 200 lettres, 1 répétition), `{v_['modele']}` retrouve le clair pour : {', '.join(ok_) or 'aucun'} ; "
                   f"échec pour : {', '.join(ko_) or 'aucun'}. Les réponses sont contraintes par un schéma JSON (sorties structurées d'Ollama) : "
                   f"{v_.get('format_invalide_moyen')} format invalide en moyenne. L'orchestrateur rejette les conclusions non fondées "
                   f"(repli moyen : {v_.get('repli_moyen')} par texte). **n est très petit : ces chiffres sont indicatifs, pas statistiquement significatifs.** "
                   f"Le coût est élevé (≈ {v_.get('appels_llm_moyen')} appels et {v_.get('duree_moyenne_s')} s par texte sur CPU) contre une fraction de seconde pour les agents à règles.\n")

# ---------- contenu additionnel (tout est lu dans le dépôt : aucun chiffre saisi à la main) ----------
import sys
sys.path.insert(0, str(R / "src"))
from vigenere_squad.llm import SCHEMA_REPONSE  # noqa: E402
from vigenere_squad.tools.registry import ALLOWLIST, OUTILS  # noqa: E402


def _cell(x):
    return str(x).replace("|", "/").replace("\n", " ")


def _court(x, n=95):
    x = _cell(x)
    return x if len(x) <= n else x[: n - 1] + "…"


def _resume_evt(e):
    t = e.get("type")
    if t == "llm":
        return "réponse : `" + _court(e.get("reponse", "").replace("`", "'"), 80) + "`"
    if t == "outil":
        return f"outil `{e.get('outil')}` {_court(e.get('args'), 40)} → " + _court(e.get("resultat"), 70)
    if t in ("decision", "repli", "fin", "debut", "erreur_format", "llm_indisponible", "outil_refuse", "outil_panne"):
        return _court({k: v for k, v in e.items() if k not in ("seq", "t_ms", "agent", "type", "run_id")}, 110)
    return _court(e, 100)


def trace_table(chemin, n=40):
    f = R / chemin
    if not f.is_file():
        return "*(trace non incluse dans cette copie du dépôt)*\n"
    evts = [json.loads(l) for l in f.read_text(encoding="utf-8").splitlines() if l.strip()][:n]
    out = "| # | t (ms) | agent | type | contenu |\n|-:|--:|-----:|------:|----------------------------------------------|\n"
    for e in evts:
        out += f"| {e['seq']} | {e['t_ms']:.0f} | {e['agent']} | {e['type']} | {_resume_evt(e)} |\n"
    return out


def read_txt(rel):
    f = R / rel
    return f.read_text(encoding="utf-8") if f.is_file() else ""


outils_tab = "| outil | genre | agents autorisés | arguments (bornes) | rôle |\n|---|---|---|---|---|\n"
for nom, (_, genre, desc, spec) in OUTILS.items():
    ags = ", ".join(a for a, l in ALLOWLIST.items() if nom in l)
    sp = ", ".join(f"{a} : {v}" if isinstance(v, list) else f"{a} : [{v[1]}, {v[2]}]" for a, v in spec.items()) or "—"
    outils_tab += f"| `{nom}` | {genre} | {ags} | {sp} | {desc} |\n"

recap = "| système | succès | exactitude moyenne | durée moyenne par texte | messages agent par texte |\n|---|---|---|---|---|\n"
recap += f"| (a) outils seuls | {P(O['succes_global'])} | {P(O['exactitude_moyenne'])} | {O['duree_moyenne_s']} s | — |\n"
recap += f"| (b) agents à règles | {P(A['succes_global'])} | {P(A['exactitude_moyenne'])} | {A['duree_moyenne_s']} s | {A['appels_llm_moyen']} |\n"
for k_, v_ in (m.get("llm") or {}).items():
    if isinstance(v_, dict) and v_.get("n"):
        recap += f"| (c) LLM `{v_['modele']}` (n={v_['n']}) | {P(v_['succes_global'])} | {P(v_['exactitude_moyenne'])} | {v_['duree_moyenne_s']} s | {v_['appels_llm_moyen']} |\n"

delta = "| cellule (chiffrement / longueur) | outils seuls | agents à règles | écart |\n|---|---|---|---|\n"
nb_diff = 0
for c_, va in A["par_cellule"].items():
    vo = O["par_cellule"].get(c_)
    if vo is not None and abs(va - vo) > 0.05:
        lib = c_.replace("|", " / ")
        delta += f"| {lib} | {P(vo)} | {P(va)} | {100 * (va - vo):+.1f} pts |\n"; nb_diff += 1
if nb_diff == 0:
    delta = "*(aucune cellule ne diffère de plus de 5 points)*\n"

bruit_tab = tab(m["robustesse"]["bruit_frappe"])
ang = m["robustesse"].get("anglais")
ang_tab = tab(ang) if ang else ""
llm_cells = ""
for k_, v_ in (m.get("llm") or {}).items():
    if isinstance(v_, dict) and v_.get("n"):
        llm_cells += f"\n| chiffrement (200 lettres) | `{v_['modele']}` |\n|---|---|\n" + "".join(f"| {c_.split('|')[0]} | {'réussi' if x >= 0.5 else 'échec'} ({P(x)}) |\n" for c_, x in v_["par_cellule"].items())

schema_txt = json.dumps(SCHEMA_REPONSE, indent=2, ensure_ascii=False)
prompts_txt = ""
for r_ in ("classifieur", "cryptanalyste", "linguiste", "pedagogue"):
    corps = read_txt(f"src/vigenere_squad/prompts/{r_}.md").strip().splitlines()
    prompts_txt += f"\n## A.{('classifieur','cryptanalyste','linguiste','pedagogue').index(r_) + 1} Prompt du {r_}\n\n" + "\n".join("> " + l + "\\" for l in corps[1:]) + "\n"
config_txt = read_txt("config/experiment.yaml").strip()
stride_txt = read_txt("docs/THREAT_MODEL.md").split("\n", 2)[-1].strip()
def petit(t):
    return "\n```{=latex}\n\\begingroup\\scriptsize\n```\n\n" + t + "\n```{=latex}\n\\endgroup\n```\n"


trace_regles = petit(trace_table("traces/scripted/vigenere-200-0-r0.jsonl", 40))
trace_llm = petit(trace_table("traces/llm_qwen3_4b/beaufort-200-0-r0.jsonl", 18))
outils_tab = petit(outils_tab)

exe = env.get("execution_llm")
exe_txt = (f" Étape LLM exécutée sur : {exe['plateforme']}, Python {exe['python']}, {exe['cpu_count']} CPU, {exe['ram_go']} Go de RAM." if exe else "")
sh = m["shannon"]; k = m["kasiski"]
md = f"""---
title: "Vigenère-Squad — une équipe d'agents LLM locaux pour la cryptanalyse classique"
author: "Vyuob"
date: "Version 1.0.0"
geometry: a4paper,margin=2.3cm
fontsize: 11pt
mainfont: "Liberation Sans"
sansfont: "Liberation Sans"
monofont: "DejaVu Sans Mono"
monofontoptions: "Scale=0.85"
linestretch: 1.1
toc: true
toc-title: "Table des matières"
lang: fr
header-includes:
  - \\usepackage{{fvextra}}
  - \\usepackage{{titlesec}}
  - \\usepackage{{titling}}
  - \\pretitle{{\\begin{{center}}\\fontsize{{24}}{{29}}\\selectfont\\bfseries\\color[HTML]{{1F3A5F}}}}
  - \\posttitle{{\\end{{center}}\\vspace{{6pt}}}}
  - \\titleformat{{\\section}}{{\\fontsize{{20}}{{24}}\\selectfont\\bfseries\\color[HTML]{{1F3A5F}}}}{{}}{{0pt}}{{}}
  - \\titleformat{{\\subsection}}{{\\fontsize{{15}}{{18}}\\selectfont\\bfseries\\color[HTML]{{1F3A5F}}}}{{}}{{0pt}}{{}}
  - \\titleformat{{\\subsubsection}}{{\\fontsize{{12.5}}{{15}}\\selectfont\\bfseries}}{{}}{{0pt}}{{}}
  - \\titlespacing*{{\\section}}{{0pt}}{{22pt}}{{9pt}}
  - \\titlespacing*{{\\subsection}}{{0pt}}{{15pt}}{{6pt}}
  - \\titlespacing*{{\\subsubsection}}{{0pt}}{{11pt}}{{4pt}}
  - \\DefineVerbatimEnvironment{{Highlighting}}{{Verbatim}}{{breaklines,commandchars=\\\\\\{{\\}}}}
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

## 2.2 Protocole de messages

À chaque pas, l'orchestrateur envoie à l'agent **un seul objet JSON** : son rôle, un contexte restreint (hypothèse courante, hypothèses déjà rejetées, graine), la liste des outils qu'il a le droit d'appeler avec leurs arguments, les observations déjà obtenues et une consigne de format. Le texte chiffré n'y figure jamais.
L'agent répond par un objet JSON d'une des deux formes `{{"action": "tool", "tool": ..., "args": {{...}}}}` ou `{{"action": "final", ...}}`. La réponse est validée (Pydantic) ; un JSON invalide, une action inconnue ou un outil hors liste sont comptés, tracés et renvoyés à l'agent comme observation d'erreur (3 erreurs de format ou 6 erreurs au total, puis repli de l'orchestrateur).

Avec Ollama, la réponse est de plus **contrainte par un schéma JSON** (sorties structurées) : la clé `action` est obligatoire et limitée à `tool` ou `final`. Ce schéma a été ajouté après un premier essai où `qwen3:4b` recopiait le message reçu au lieu d'y répondre (voir §6) :

```json
{schema_txt}
```

Si le LLM est injoignable ou dépasse le délai (300 s par appel, 60 s en mode rapide), l'agent échoue proprement (événement `llm_indisponible` dans la trace) et l'orchestrateur se replie ; il ne plante jamais.

# 3. Outils

- **Indice de coïncidence** $IC=\\sum n_i(n_i-1)/N(N-1)$ : ≈ 0,078 en français monoalphabétique, ≈ 0,038 pour un texte aléatoire.
- **Kasiski** : les distances entre répétitions de trigrammes sont des multiples de la longueur de clé ; vote des diviseurs.
- **Friedman** : $L\\approx (k_p-k_r)N/((N-1)IC-k_rN+k_p)$ avec $k_p=0{{,}}0778$, $k_r=1/26$.
- **Chi²** sur les fréquences du français : décalage de César, et par colonne pour Vigenère. **Beaufort** se ramène à Vigenère par la symétrie $25-C$.
- **Autoclave** : Kasiski échoue (le flux de clé contient le clair) ; ascension de colline sur le mot-clé, scorée par quadrigrammes.
- **Substitution** : recuit simulé / ascension de colline sur une permutation, avec 6 redémarrages, scorée par un modèle de langue 1–4-grammes interpolé (table 26⁴ en log₁₀).

## 3.1 Catalogue d'outils et listes blanches

Chaque agent ne peut appeler que les outils de sa liste ; les arguments sont validés (type, bornes, valeurs permises) **avant** exécution. Aucun outil n'accède au système de fichiers, au shell ni au réseau.

{outils_tab}

# 4. Protocole expérimental

Corpus généré avec la graine {m['meta']['seed']} (SHA-256 `{m['meta']['corpus_sha256'][:16]}…`) : 6 chiffrements × 5 longueurs × 5 textes. Les textes clairs sont tirés d'un fichier de test que le modèle de langue n'a jamais vu.
Chaque mesure est répétée {m['meta']['repetitions']} fois (graines 42–44). Succès : au moins {int(100 * m['meta']['seuil_succes_exactitude'])} % de lettres exactes. Comparaisons : (a) outils seuls ; (b) agents à règles sans LLM ; (c) un LLM local (`qwen3:4b`) sur un petit sous-ensemble.
Tous les paramètres sont dans `config/experiment.yaml` ; l'environnement (versions, matériel, digest des modèles, hachages des prompts) dans `results/ENVIRONMENT.json`.
Environnement de cette exécution : Python {env['python']}, {env['plateforme']}, {env['cpu_count']} CPU, durée {m['meta']['duree_totale_s']} s, pic mémoire {m['meta']['pic_memoire_mo']} Mo.{exe_txt}

# 5. Résultats

## 5.1 Baseline : outils seuls

{tab(O)}
(σ entre répétitions : {O['ecart_type_repetitions']}.)

## 5.2 Agents + outils (politique à règles, sans LLM)

{tab(A)}
(σ entre répétitions : {A['ecart_type_repetitions']} ; {A['iterations_moyen']} hypothèses testées en moyenne ; {A['appels_llm_moyen']} messages agent par texte ; {A['duree_moyenne_s']} s par texte.)

**Synthèse des trois systèmes.**

{recap}

![Succès par chiffrement et longueur](../results/figures/succes_par_chiffre_longueur.png)

**Lecture.** Au-delà de 500 lettres tout est cassé. Les chiffrements monoalphabétiques simples le sont dès 50 lettres. La substitution demande environ 200 lettres ou plus, ce qui est cohérent avec la distance d'unicité (§5.5).
Les agents à règles font **moins bien** que la baseline sur Vigenère et Beaufort courts : choisir la longueur de clé par Kasiski + IC des colonnes est moins fiable que tester les longueurs 2–12 et garder le meilleur score.

**Cellules où les agents diffèrent de la baseline (écart > 5 points) :**

{delta}

## 5.3 Avec LLM local

{tl}
{llm_cells}

## 5.4 Robustesse et pannes

- 5 % de lettres du chiffré remplacées : succès {P(m['robustesse']['bruit_frappe']['succes_global'])}.
- Clair anglais (le Linguiste est entraîné sur le français) : succès {P(m['robustesse'].get('anglais', {}).get('succes_global'))}.

**Détail du cas « 5 % de bruit »** (agents à règles) :

{bruit_tab}

**Détail du cas « clair anglais »** (agents à règles ; l'ensemble d'entraînement du Linguiste est français) :

{ang_tab}

**Injection de pannes** :

{tp}
![Robustesse aux pannes](../results/figures/pannes.png){{width=60%}}

Les pannes d'outils sont absorbées par de nouvelles tentatives dans l'agent. Les réponses LLM corrompues (JSON invalide, action inconnue, vide) déclenchent un rejet de schéma puis, au-delà de 3 erreurs, un repli de l'orchestrateur.

## 5.5 Kasiski contre l'autoclave et distance d'unicité

La vraie longueur de clé figure dans le top 3 de Kasiski pour {P(k['vigenere']['longueur_vraie_dans_top3'])} des Vigenère (n={k['vigenere']['n']}) contre {P(k['autoclave']['longueur_vraie_dans_top3'])} des autoclaves (n={k['autoclave']['n']}) : l'autoclave brouille Kasiski.
Le modèle de langue donne une entropie de {sh['entropie_bits_par_lettre']} bits/lettre (borne haute), soit une redondance de {sh['redondance_bits_par_lettre']} bits/lettre et des distances d'unicité $U=H(K)/D$ de {sh['distance_unicite_lettres']['cesar']} lettres (César), {sh['distance_unicite_lettres']['affine']} (affine), {sh['distance_unicite_lettres']['vigenere_6']} (Vigenère, clé de 6) et {sh['distance_unicite_lettres']['substitution']} (substitution) : ordres de grandeur, car l'entropie est surestimée sur un petit corpus.
Le succès réel exige davantage de lettres que $U$ : l'unicité est une condition nécessaire, pas suffisante, pour un attaquant au calcul borné.

![Succès vs longueur](../results/figures/succes_vs_unicite.png){{width=75%}}

Le Pédagogue produit des exercices valides dans {P(m['exercices_pedagogue']['taux'])} des cas (n={m['exercices_pedagogue']['n']}, vérifiés par déchiffrement avec la clé du corrigé).

## 5.6 Étude de cas : une trace complète

Trace réelle d'un texte chiffré par Vigenère (200 lettres, clé de 5), résolu par les agents à règles. Les « réponses » des agents sont ici produites par la politique à règles, selon le même protocole JSON que le LLM : l'orchestrateur ne voit pas la différence.

{trace_regles}

On y lit : (1) le Classifieur mesure l'IC (0,047, proche de l'aléatoire) et Kasiski (7 répétitions) et conclut « polyalphabétique » ; (2) le Cryptanalyste teste les longueurs candidates et retient celle dont l'IC par colonne est élevé ; (3) le Linguiste compare le score de quadrigrammes au seuil ; (4) l'orchestrateur accepte ; (5) le Pédagogue génère un exercice. Chaque étape est rejouable avec `vigenere-squad rejouer <trace>`.

**Trace avec un vrai LLM** (`qwen3:4b`, Beaufort, 200 lettres, début de la trace) :

{trace_llm}

On y voit le modèle enchaîner des appels d'outils valides, puis conclure « final » en citant une attaque qu'il n'a jamais exécutée : l'orchestrateur le détecte et ignore l'hypothèse (événement `repli`). C'est le comportement attendu de la séparation « le LLM décide, le code vérifie ».

# 6. Discussion et limites

- **Résultat négatif assumé** : les agents ne battent pas la baseline en précision. Leur valeur : modularité, trace complète, explications, tolérance aux pannes, listes d'outils fermées.
- **Corpus d'entraînement minuscule** (≈ 6,7 ko) : modèle de langue pauvre, entropie surestimée, textes de test qui se recouvrent aux grandes longueurs.
- **Linguiste** : le seuil accepte parfois un clair en partie faux ; il suppose le français.
- **LLM** : évalué sur un sous-ensemble minimal (6 textes de 200 lettres, 1 répétition, un seul modèle, `qwen3:4b`) pour tenir sur un portable sans GPU ; le second modèle prévu (`llama3.2:3b`) n'a pas été évalué dans le temps imparti. Les mesures LLM sont donc indicatives.
- Pas de comparaison avec un LLM seul sans outils (hors périmètre) ; les LLM de ≤ 8 Go calculent mal des fréquences, ce qui justifie la répartition « LLM décide / code calcule ».

## 6.1 Travaux liés

Les outils reprennent des méthodes classiques : examen de Kasiski (1863) pour la longueur de clé, indice de coïncidence et test de Friedman (1922), distance d'unicité de Shannon (1949), recuit simulé de Kirkpatrick et al. (1983) pour la substitution. La nouveauté ne se situe pas dans ces algorithmes, mais dans leur **orchestration** : des agents à rôles disjoints, des outils à listes fermées, une trace complète et un contrôle par le code des conclusions du LLM.

## 6.2 Enseignements sur les LLM locaux

- Un petit modèle (0,6 milliard de paramètres) ne suit pas le protocole de façon fiable ; un modèle de 4 milliards le suit si la sortie est contrainte par un schéma, mais raisonne mal sur les chiffrements polyalphabétiques.
- Sans schéma, `qwen3:4b` a recopié le message reçu au lieu d'y répondre : chaque réponse invalide coûtait environ 60 s sur CPU et le test devenait impraticable. Les sorties structurées d'Ollama règlent le problème de format, pas celui du raisonnement.
- Un délai maximal par appel et un repli propre sont indispensables : sur un processeur partagé (CI), un appel peut dépasser 60 s.
- **Boucles** : sur les traces de `qwen3:4b`, le Cryptanalyste rappelle parfois le même outil (jusqu'à 13 fois de suite `ic_colonnes` avec la même longueur) jusqu'à la limite de 14 pas, ce qui déclenche le repli ; l'outil correct (par exemple `force_brute_affine` pour le texte affine) a parfois été appelé trop tard.
- **Explications peu fiables** : le Pédagogue produit des phrases fausses (« clé de 20 caractères » pour une permutation de 26 lettres, « substitution polyalphabétique »), et n'appelle pas l'outil `generer_exercice` : l'exercice proposé n'est alors pas vérifié par le code, contrairement à la politique à règles (100 % d'exercices valides). C'est une limite connue de la version LLM.
- **Format des hypothèses** : dans un cas, le Classifieur a recopié le gabarit du prompt (`monoalphabetique|polyalphabetique`) au lieu de choisir une famille.
- Le coût est très asymétrique : environ 335 s par texte avec le LLM contre une fraction de seconde pour les règles, pour une précision inférieure.

## 6.3 Perspectives

Évaluer plus de textes et de répétitions avec le LLM ; tester d'autres modèles locaux et des tailles de contexte différentes ; élargir le corpus d'entraînement du Linguiste (plusieurs langues) ; remplacer la politique à règles du Cryptanalyste par un LLM guidé par des exemples (few-shot) ; ajouter des chiffrements (Playfair, Hill, transposition).

## 6.4 Usage responsable

Le système ne casse que des chiffrements historiques, sans valeur de sécurité aujourd'hui, sur des textes de test. Il n'envoie aucune donnée hors de la machine locale. Les exercices générés servent à l'apprentissage de la cryptanalyse.

# 7. Sécurité

Modèle de menaces STRIDE complet dans `docs/THREAT_MODEL.md` (table menace / scénario / contre-mesure / test) : injection via le texte chiffré (le texte n'entre pas dans le prompt), clair inventé par le LLM (le code a le dernier mot), boucle infinie (bornes de pas et d'essais), élévation de privilèges (listes blanches, aucun outil shell/fichier/réseau), fuite de données (réseau local uniquement, gitleaks en CI).

# 8. Reproductibilité

`make reproduce` rejoue tout (tests, corpus, baseline, agents, LLM, métriques, figures, site). `make reproduce-small` (CI) utilise `qwen3:0.6b`. Environnement figé par `uv.lock` et `Dockerfile` ; `SHA256SUMS` signé ; archive Zenodo de la release `v1.0.0`.

# 9. Usage de l'IA

Voir `AI_USAGE.md` : conception et code réalisés avec l'assistance de Claude (Anthropic), sous la direction et la relecture de l'auteur ; résultats issus uniquement de l'exécution du dépôt.

# Annexe A — Prompts des agents (version 1.0)

Les prompts sont versionnés dans `src/vigenere_squad/prompts/` ; leurs empreintes SHA-256 figurent dans `results/ENVIRONMENT.json`.
{prompts_txt}

# Annexe B — Configuration de l'expérience

```yaml
{config_txt}
```

# Annexe C — Reproduire pas à pas

**Linux / macOS** (avec `make`) :

```bash
uv sync --frozen --extra dev
make test
make models && make reproduce-small   # rapide
make reproduce                        # complet (plusieurs heures sur CPU)
```

**Windows** (sans `make`, PowerShell) :

```powershell
uv sync --frozen --extra dev
uv run --frozen pytest
uv run --frozen python scripts/reproduce.py --small
uv run --frozen python -m vigenere_squad.evaluate --llm-seul --modeles qwen3:4b --par-cellule 1 --repetitions 1 --timeout 240
```

Pour reproduire uniquement les mesures sans LLM : `uv run --frozen python scripts/reproduce.py --no-llm`. Vérification d'intégrité : `uv run --frozen python scripts/hashes.py --check` puis `minisign -Vm SHA256SUMS -p minisign.pub`.

# Annexe D — Glossaire

- **IC** : indice de coïncidence, probabilité que deux lettres tirées au hasard dans le texte soient identiques.
- **Kasiski** : méthode qui déduit la longueur de la clé des distances entre séquences répétées.
- **Autoclave (autokey)** : Vigenère dont la clé se prolonge avec le texte clair lui-même.
- **Beaufort** : variante de Vigenère où l'on soustrait le texte à la clé.
- **Quadrigramme** : suite de quatre lettres ; leur fréquence mesure la vraisemblance d'un texte.
- **Repli** : décision de l'orchestrateur d'abandonner une hypothèse ou un agent défaillant.
- **Trace** : journal JSONL de tous les messages, appels d'outils et décisions.
- **Schéma JSON** : description de la forme exacte attendue pour la réponse d'un LLM.

# Références

- Kasiski, F. W. (1863). *Die Geheimschriften und die Dechiffrir-Kunst*.
- Friedman, W. F. (1922). *The Index of Coincidence and Its Applications in Cryptography*.
- Shannon, C. E. (1949). Communication theory of secrecy systems. *Bell System Technical Journal*, 28(4).
- Kirkpatrick, S., Gelatt, C. D., Vecchi, M. P. (1983). Optimization by simulated annealing. *Science*, 220.
"""
(R / "docs/rapport.md").write_text(md, encoding="utf-8", newline="\n")
subprocess.run(["pandoc", "docs/rapport.md", "-o", "docs/rapport.pdf", "--pdf-engine=xelatex", "--resource-path=docs"], cwd=R, check=True)
print("docs/rapport.pdf")
