import json

import pytest
from pathlib import Path

from vigenere_squad.agents import Agent
from vigenere_squad.llm import FaultyClient, ScriptedClient
from vigenere_squad.orchestrator import Orchestrateur
from vigenere_squad.tools import ciphers as c
from vigenere_squad.tools.lang import normaliser
from vigenere_squad.tools.registry import ALLOWLIST, OUTILS, Registre, ToolError, ToolRefused
from vigenere_squad.trace import Trace

TEST = normaliser((Path(__file__).resolve().parents[1] / "data/sample_fr_test.txt").read_text(encoding="utf-8"))


class Fixe:
    name = "fixe"
    def __init__(self, *reps): self.reps = list(reps)
    def chat(self, role, system, user): return self.reps.pop(0) if len(self.reps) > 1 else self.reps[0]


def test_allowlists_coherentes():
    for role, outils in ALLOWLIST.items():
        assert outils and all(o in OUTILS for o in outils)
    assert "attaque_substitution" not in ALLOWLIST["linguiste"]  # séparation des pouvoirs


def test_outil_hors_liste_refuse():
    reg = Registre()
    with pytest.raises(ToolRefused):
        reg.appeler("linguiste", "attaque_substitution", {}, "ABC")
    assert reg.refus == 1


@pytest.mark.parametrize("args", [{"longueur": 999}, {"longueur": "x"}, {"inconnu": 1}, {"variante": "rot13", "longueur": 3}])
def test_arguments_invalides_refuses(args):
    with pytest.raises(ToolRefused):
        Registre().appeler("cryptanalyste", "attaque_vigenere", args, TEST[:100])


def test_panne_injectee():
    with pytest.raises(ToolError):
        Registre(p_panne=1.0).appeler("classifieur", "indice_coincidence", {}, "ABCD")


def test_agent_rejette_json_invalide_puis_abandonne():
    tr = Trace(); a = Agent("linguiste", Fixe("pas du json"), Registre(), tr)
    assert a.run("ABC", {}) is None and a.stats["format_invalide"] == 4


def test_agent_refus_outil_interdit_est_trace():
    tr = Trace(); llm = Fixe('{"action":"tool","tool":"attaque_substitution","args":{}}', '{"action":"final","plausible":true}')
    a = Agent("linguiste", llm, Registre(), tr)
    assert a.run("ABC", {})["final"]["plausible"] is True
    assert tr.count("outil_refuse") == 1


def test_final_incomplet_rejete():
    a = Agent("classifieur", Fixe('{"action":"final","hypotheses":["rot13"]}'), Registre(), Trace())
    assert a.run("ABC", {}) is None


@pytest.mark.parametrize("nom", c.CHIFFRES)
def test_orchestrateur_resout_chaque_chiffre(nom):
    import numpy as np
    rng = np.random.default_rng(11); clair = TEST[100:700]
    ct = c.chiffrer(nom, clair, c.cle_aleatoire(nom, rng))
    st, tr = Orchestrateur(ScriptedClient()).resoudre(ct, "t")
    assert st.statut == "resolu" and st.clair == clair
    assert st.explication and st.exercice
    assert tr.count("outil") >= 1 and tr.count("llm") == st.appels_llm


def test_boucle_de_verification_rejette_puis_corrige():
    ct = c.vigenere(TEST[:600], "CLEFS")
    class Menteur(ScriptedClient):
        def _classifieur(self, msg):  # annonce à tort « César » d'abord
            return {"action": "final", "famille": "?", "hypotheses": ["cesar", "vigenere"], "justification": "test"}
    st, _ = Orchestrateur(Menteur()).resoudre(ct)
    assert [t.hypothese for t in st.tentatives][:2] == ["cesar", "vigenere"]
    assert not st.tentatives[0].accepte and st.tentatives[1].accepte


def test_code_a_le_dernier_mot_sur_linguiste():
    class Complaisant(ScriptedClient):
        def _classifieur(self, msg):
            return {"action": "final", "famille": "?", "hypotheses": ["cesar", "vigenere"], "justification": "test"}
        def _linguiste(self, msg):
            return {"action": "final", "plausible": True, "raison": "ok"}
    ct = c.vigenere(TEST[:600], "CLEFS")
    st, _ = Orchestrateur(Complaisant()).resoudre(ct)
    assert st.desaccords_linguiste >= 1 and st.statut == "resolu"


def test_pannes_repli_sans_crash():
    ct = c.vigenere(TEST[:600], "CLEFS")
    st, _ = Orchestrateur(FaultyClient(ScriptedClient(), 0.5, 3), p_panne_outil=0.5, seed=1).resoudre(ct)
    assert st.statut in ("resolu", "non_verifie", "echec")


def test_trace_jsonl(tmp_path):
    ct = c.cesar(TEST[:300], 5)
    Orchestrateur(ScriptedClient(), trace_dir=str(tmp_path)).resoudre(ct, "r1")
    lignes = [json.loads(l) for l in (tmp_path / "r1.jsonl").read_text(encoding="utf-8").splitlines()]
    assert lignes[0]["type"] == "debut" and lignes[-1]["type"] == "fin"
    assert {"seq", "agent", "type"} <= set(lignes[3])


class Injoignable:
    """LLM qui ne répond jamais (timeout réseau) : l'orchestrateur doit échouer proprement (repli, trace), pas planter."""
    name = "injoignable"
    def digest(self): return None
    def chat(self, role, system, user): raise TimeoutError("timed out")


def test_llm_timeout_repli_sans_crash():
    import numpy as np
    clair = TEST[100:400]
    ct = c.chiffrer("vigenere", clair, c.cle_aleatoire("vigenere", np.random.default_rng(3)))
    st, tr = Orchestrateur(Injoignable()).resoudre(ct, "t")
    assert st.statut == "echec" and st.repli > 0  # échec propre et tracé, pas de plantage
    assert any(e["type"] == "llm_indisponible" for e in tr.events)
