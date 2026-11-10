import numpy as np
import pytest
from pathlib import Path

from vigenere_squad.tools import analysis as an, ciphers as c
from vigenere_squad.tools.lang import ModeleFR, modele, normaliser, seuil_plausible

TEST = normaliser((Path(__file__).resolve().parents[1] / "data/sample_fr_test.txt").read_text(encoding="utf-8"))


def test_normaliser():
    assert normaliser("Été, déjà 1 ç!") == "ETEDEJAC"


def test_ic_francais_vs_aleatoire():
    assert 0.06 < an.indice_coincidence(TEST)["ic"] < 0.09
    rng = np.random.default_rng(0)
    alea = "".join(chr(65 + int(i)) for i in rng.integers(0, 26, 3000))
    assert an.indice_coincidence(alea)["ic"] < 0.045
    assert an.indice_coincidence("A")["n"] == 1


def test_ic_invariant_par_cesar():
    assert abs(an.indice_coincidence(c.cesar(TEST, 7))["ic"] - an.indice_coincidence(TEST)["ic"]) < 1e-12


def test_frequences_e_en_tete():
    assert list(an.frequences(TEST)["top"])[0] == "E"


def test_cesar():
    r = an.chi2_cesar(c.cesar(TEST[:300], 11))
    assert r["cle"] == 11 and r["clair"] == TEST[:300]


def test_affine():
    r = an.force_brute_affine(c.affine(TEST[:300], 7, 3))
    assert r["cle"] == [7, 3] and r["n_cles"] == 312


@pytest.mark.parametrize("variante,f", [("vigenere", c.vigenere), ("beaufort", c.beaufort)])
def test_vigenere_beaufort(variante, f):
    ct = f(TEST[:900], "SECRET")
    k = an.kasiski(ct, max_len=12)
    assert 6 in [x["longueur"] for x in k["longueurs_candidates"]]
    r = an.attaque_vigenere(ct, 6, variante)
    assert r["cle"] == "SECRET" and r["clair"] == TEST[:900]


def test_friedman_ordre_de_grandeur():
    est = an.friedman(c.vigenere(TEST, "CLEFS"))["longueur_estimee"]
    assert est is not None and 2 < est < 10


def test_ic_colonnes_maximal_a_la_bonne_longueur():
    ct = c.vigenere(TEST, "CLEFS")
    assert an.ic_colonnes(ct, 5)["ic_moyen"] > an.ic_colonnes(ct, 4)["ic_moyen"] + 0.015


def test_autoclave():
    ct = c.autoclave(TEST[:500], "MOTS")
    r = an.attaque_autoclave(ct)
    assert r["clair"][10:] == TEST[10:500]  # le début peut garder une lettre de clé fausse, pas la suite


def test_substitution():
    k = c.cle_aleatoire("substitution", np.random.default_rng(5))
    r = an.attaque_substitution(c.substitution(TEST[:700], k), seed=1)
    assert np.mean([a == b for a, b in zip(r["clair"], TEST[:700])]) > 0.9


def test_linguiste_discrimine():
    assert an.score_quadrigrammes(TEST[:200])["au_dessus_seuil"]
    assert not an.score_quadrigrammes(c.vigenere(TEST[:200], "KLMNOP"))["au_dessus_seuil"]


def test_exercice_generateur():
    e = an.generer_exercice(TEST, "vigenere", 3)
    assert c.dechiffrer("vigenere", e["enonce"], e["cle"]) == e["corrige_clair"]


def test_solveur_outils_seuls():
    assert an.solveur_outils_seuls(c.cesar(TEST[:200], 4))["clair"] == TEST[:200]


def test_modele_petit_texte():
    m = ModeleFR("bonjour le monde " * 20)
    assert m.score("AB") < 0 and m.score("") == -9.0
    assert seuil_plausible(modele()) < 0


def test_vigenere_longueur_invalide():
    with pytest.raises(ValueError):
        an.attaque_vigenere("ABC", 0)
