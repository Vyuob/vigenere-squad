# Journal des prompts

Les prompts des agents sont versionnés dans `src/vigenere_squad/prompts/` (un fichier par agent) ; leurs SHA-256 sont dans
`results/ENVIRONMENT.json`. Ce journal consigne chaque modification et ce qui a été **réellement mesuré**.

| Version | Modification | Effet mesuré |
|---|---|---|
| 1.0 | Prompts initiaux des quatre agents (rôle, outils autorisés, format JSON de sortie). Le texte du fichier n'a pas changé depuis. | Réf. : politique à règles, sans LLM, 85,6 % (n=450). |
| 1.0 + sortie structurée (code, `llm.py`) | Le schéma JSON de la réponse est transmis à Ollama (`format`) pour imposer `action` ∈ {tool, final}. | `qwen3:0.6b` sans schéma : 0/6 textes, 27 formats invalides par texte. `qwen3:4b` avec schéma : 0 format invalide sur 6 textes. |
| 1.0 + consigne finale (code, `agents.py`) | Le message utilisateur se termine par une consigne (« Réponds maintenant par UN seul objet JSON… ») pour éviter que le modèle recopie le message. | `qwen3:4b` : réponses sans `action` observées avant, plus aucune après. |

**Limite.** Ces comparaisons ne sont pas contrôlées : le modèle change entre la mesure « avant » (`qwen3:0.6b`) et « après »
(`qwen3:4b`), et les échantillons sont petits (6 textes). Elles montrent un effet sur le **format** des réponses, pas une mesure de gain
de précision attribuable aux prompts. Toute future modification de prompt doit être ajoutée ici avec ses métriques avant/après.
