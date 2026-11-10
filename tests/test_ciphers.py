import numpy as np
import pytest

from vigenere_squad.tools import ciphers as c

T = "LETEXTEQUIVASERVIRDETESTPOURLESCHIFFREMENTS"


def test_vecteurs_connus():
    assert c.cesar("ATTAQUE", 3) == "DWWDTXH"
    assert c.vigenere("ATTACKATDAWN", "LEMON") == "LXFOPVEFRNHR"  # vecteur classique
    assert c.affine("AFFINE", 5, 8) == "IHHWVC"


@pytest.mark.parametrize("nom", c.CHIFFRES)
def test_aller_retour(nom):
    rng = np.random.default_rng(1)
    for _ in range(5):
        k = c.cle_aleatoire(nom, rng)
        assert c.dechiffrer(nom, c.chiffrer(nom, T, k), k) == T


def test_beaufort_involutif():
    assert c.beaufort(c.beaufort(T, "CLE"), "CLE") == T


def test_autoclave_depend_du_clair():
    assert c.autoclave("ATTAQUEALAUBE", "QUEEN") != c.vigenere("ATTAQUEALAUBE", "QUEEN")


def test_substitution_exige_permutation():
    with pytest.raises(AssertionError):
        c.substitution("ABC", "A" * 26)


def test_affine_a_inversible():
    assert len(c.AFFINE_A) == 12  # 12 x 26 = 312 clés
