import json

from vigenere_squad import corpus as C, evaluate as E, figures, demo
from vigenere_squad.llm import ScriptedClient, OllamaClient


def test_exactitude():
    assert E.exactitude("ABC", "ABC") == 1.0 and E.exactitude("ABD", "ABC") < 1 and E.exactitude(None, "A") == 0.0


def test_agreger_et_figures(tmp_path):
    corpus = C.generer(1, [100, 200], 2)
    recs = E.run_agents(corpus, 2, 1, 0.95, lambda s: ScriptedClient())
    a = E.agreger(recs)
    assert a["n"] == 48 and 0 <= a["succes_global"] <= 1 and len(a["succes_par_repetition"]) == 2
    m = {"outils_seuls": a, "agents_scriptes": a,
         "pannes": {"llm": {"0.0": {"succes_global": .9}, "0.1": {"succes_global": .8}}, "outil": {"0.0": {"succes_global": .9}}},
         "shannon": E.shannon(C.texte_test())}
    figures.tracer(m, tmp_path)
    assert (tmp_path / "pannes.png").stat().st_size > 1000
    E.sauver_raw(recs, tmp_path / "r.jsonl"); assert len((tmp_path / "r.jsonl").read_text(encoding="utf-8").splitlines()) == 48


def test_baseline_et_etudes():
    r = E.run_outils_seuls(C.generer(2, [200], 1, ("cesar", "vigenere")), 1, 2, 0.95)
    assert all(x["succes"] == 1 for x in r)
    assert E.exercices_valides(2)["taux"] == 1.0
    assert E.kasiski_etude(C.generer(3, [300], 6, ("vigenere", "autoclave")))["vigenere"]["n"] == 6
    assert E.shannon(C.texte_test())["distance_unicite_lettres"]["substitution"] > 20


def test_demo_rendu():
    html = demo._rendu("PHVVDJHVHFUHW" * 6, None)
    assert "Trace des agents" in html


def test_ollama_injoignable():
    assert OllamaClient("x", host="http://127.0.0.1:9", timeout=1).digest() is None


def test_environnement_portable():
    ram = E._ram_go()
    assert ram is None or ram > 0
    pic = E._pic_memoire_mo()
    assert pic is None or pic > 0


def test_hashes_roundtrip(tmp_path, monkeypatch):
    import importlib.util
    from pathlib import Path
    spec = importlib.util.spec_from_file_location("hashes", Path(__file__).resolve().parents[1] / "scripts/hashes.py")
    H = importlib.util.module_from_spec(spec); spec.loader.exec_module(H)
    (tmp_path / "config").mkdir(); (tmp_path / "config/a.yaml").write_text("x: 1\n", encoding="utf-8", newline="\n")
    monkeypatch.setattr(H, "R", tmp_path)
    assert H.ecrire() == 0 and H.verifier() == 0
    (tmp_path / "config/a.yaml").write_text("x: 2\n", encoding="utf-8", newline="\n")
    assert H.verifier() == 1


def test_llm_seul_exige_des_resultats(tmp_path):
    import pytest
    with pytest.raises(SystemExit):
        E.main(["--llm-seul", "--out", str(tmp_path)])


def test_cle_vs_longueur_et_figure(tmp_path):
    res, brut = E.cle_vs_longueur(5, [3, 6], [100, 300], 2, 0.95, avec_agents=False)
    assert res["unicite_theorique"]["6"] > res["unicite_theorique"]["3"] and len(brut) == 4
    assert res["longueur_min_empirique"]["outils_seuls"]["3"] in (100, 300, None)
    figures._fig_cle({**res, "longueur_min_empirique": {"outils_seuls": {"3": 100, "6": None}, "agents_scriptes": {"3": 300, "6": 300}}}, tmp_path)
    assert (tmp_path / "longueur_min_vs_cle.png").stat().st_size > 1000


def test_grille_explications_deterministe():
    corpus = C.generer(9, [100, 300], 2, ("cesar", "vigenere", "affine"))
    g1, g2 = E.grille_explications(corpus, 9, 4), E.grille_explications(corpus, 9, 4)
    assert g1 == g2 and g1["n"] == 4 and 0 <= g1["note_moyenne_sur_10"] <= 10
    assert all(set(c["criteres"]) == {"type_correct", "cle_correcte", "nombres_fideles", "verification_mentionnee", "exercice_valide"} for c in g1["cas"])
