import json
from vigenere_squad import corpus as C
from vigenere_squad.tools import ciphers as c


def test_corpus_deterministe(tmp_path):
    a = C.generer(42, [100], 2); b = C.generer(42, [100], 2)
    assert a == b and len(a) == 12
    assert C.sauver(a, tmp_path / "x.jsonl") == C.sauver(b, tmp_path / "y.jsonl")
    assert C.charger(tmp_path / "x.jsonl")[0]["id"] == "cesar-100-0"


def test_corpus_chiffres_correspondent():
    for s in C.generer(1, [80], 1):
        cle = tuple(s["cle"]) if s["chiffre"] == "affine" else s["cle"]
        assert c.dechiffrer(s["chiffre"], s["chiffre_texte"], cle) == s["clair"]


def test_bruit():
    x = "A" * 1000; y = C.bruiter(x, 0.05, 0)
    assert 20 < sum(a != b for a, b in zip(x, y)) < 90 and C.bruiter(x, 0.05, 0) == y


def test_cli_resoudre(capsys):
    from vigenere_squad import cli
    ct = c.cesar(C.texte_test()[:200], 9)
    cli.main(["resoudre", ct])
    out = capsys.readouterr().out
    assert "cesar" in out and "resolu" in out
