# Vigenère-Squad — toutes les commandes passent par `uv` (environnement figé par uv.lock)
# Sans make (Windows) : uv run --frozen python scripts/reproduce.py [--small|--no-llm]
UV ?= uv
RUN = $(UV) run --frozen
.PHONY: install test cov data models reproduce reproduce-small site report hashes sign verify demo clean

install:            ## environnement figé
	$(UV) sync --frozen --extra dev

test:               ## tests unitaires/intégration (sans LLM)
	$(RUN) pytest

cov:                ## couverture (outils déterministes >= 70 %)
	$(RUN) pytest --cov=vigenere_squad --cov-report=term-missing --cov-fail-under=70

data:               ## (optionnel) corpus plus grand : voir data/README.md ; sinon l'échantillon livré est utilisé
	$(RUN) python scripts/fetch_corpus.py

models:             ## modèles Ollama de config/experiment.yaml (ollama doit être installé et lancé)
	ollama pull qwen3:4b && ollama pull llama3.2:3b

reproduce: test     ## TOUT reproduire : corpus -> baseline -> agents -> LLM x2 -> métriques -> figures -> site
	$(RUN) python -m vigenere_squad.evaluate --profil full --llm
	$(RUN) python scripts/build_site.py
	$(MAKE) hashes

reproduce-small:    ## version CI : petit modèle (qwen3:0.6b), 1 répétition, quelques minutes
	$(RUN) python -m vigenere_squad.evaluate --profil small --llm
	$(RUN) python scripts/build_site.py

site:
	$(RUN) python scripts/build_site.py

report:             ## docs/rapport.pdf depuis results/metrics.json (nécessite pandoc + xelatex)
	$(RUN) python scripts/build_report.py

hashes:             ## SHA256SUMS des livrables (à signer ensuite : make sign)
	$(RUN) python scripts/hashes.py

sign:               ## signature minisign de SHA256SUMS (clé publique : minisign.pub)
	minisign -Sm SHA256SUMS

verify:
	$(RUN) python scripts/hashes.py --check && minisign -Vm SHA256SUMS -p minisign.pub

demo:
	$(RUN) vigenere-squad demo

clean:
	$(RUN) python scripts/clean.py
