# Modèle de menaces (STRIDE simplifié)

Actifs : intégrité des résultats, machine de l'utilisateur, confidentialité des textes analysés. Frontière de confiance : le LLM (sortie non fiable) ↔ le code.

| Menace | Scénario | Contre-mesure | Test |
|---|---|---|---|
| **S**poofing | Un texte chiffré contient des instructions (« ignore tes règles… ») | Le texte n'est jamais inséré dans le prompt : les outils le reçoivent par liaison côté code ; le LLM ne voit que des statistiques et un aperçu de 60–80 lettres | `test_agents.py` |
| **T**ampering | Le LLM invente une clé ou un clair | « Le code calcule » : le clair vient du résultat d'outil ; le Linguiste est borné par le seuil calculé (le code a le dernier mot) | `test_code_a_le_dernier_mot_sur_linguiste` |
| **R**epudiation | Résultat non explicable | Trace JSONL de chaque message/appel d'outil ; `vigenere-squad rejouer` | `test_trace_jsonl` |
| **I**nformation disclosure | Fuite de textes vers un service distant | Aucun appel réseau hors `localhost:11434` ; la démo écoute `127.0.0.1` ; gitleaks en CI | revue + CI |
| **D**enial of service | Boucle d'agent infinie, entrée géante, outil lent | `MAX_STEPS` par agent, `MAX_TENTATIVES`, bornes strictes des arguments (itérations ≤ 8000…), taille POST ≤ 20 ko | `test_arguments_invalides_refuses`, `test_agent_rejette_json_invalide…` |
| **E**levation of privilege | Le LLM appelle un outil d'un autre rôle ou une commande système | Liste blanche par agent ; aucun outil shell/fichier/réseau ; outil hors liste → refusé et tracé | `test_outil_hors_liste_refuse` |

Hors périmètre : modèle compromis (poids malveillants), attaque physique, déni de service sur Ollama.
