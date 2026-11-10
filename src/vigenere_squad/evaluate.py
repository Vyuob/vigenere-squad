"""Protocole expérimental : exécute toutes les mesures et écrit results/ (raw, metrics.json, figures, ENVIRONMENT.json)."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import platform
try:  # module Unix uniquement (absent sous Windows)
    import resource
except ImportError:  # pragma: no cover
    resource = None
import sys
import time
from collections import defaultdict
from pathlib import Path

import numpy as np
import yaml

from . import __version__, corpus as C
from .llm import FaultyClient, OllamaClient, ScriptedClient
from .orchestrator import Orchestrateur
from .tools import analysis as an, ciphers
from .tools.lang import modele, normaliser

RACINE = Path(__file__).resolve().parents[2]


def _sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def exactitude(a: str | None, b: str) -> float:
    if not a or len(a) != len(b):
        return 0.0
    return float(np.mean([x == y for x, y in zip(a, b)]))


def agreger(recs: list[dict]) -> dict:
    if not recs:
        return {"n": 0}
    def m(rs, k): return round(float(np.mean([r[k] for r in rs])), 4) if rs else None
    out = {"n": len(recs), "succes_global": m(recs, "succes"), "exactitude_moyenne": m(recs, "exactitude"),
           "duree_moyenne_s": m(recs, "duree_s")}
    for cle in ("appels_llm", "iterations", "repli", "desaccords", "format_invalide"):
        if cle in recs[0]:
            out[cle + "_moyen"] = m(recs, cle)
    reps = sorted({r["rep"] for r in recs})
    if len(reps) > 1:
        par_rep = [float(np.mean([r["succes"] for r in recs if r["rep"] == k])) for k in reps]
        out["succes_par_repetition"] = [round(x, 4) for x in par_rep]
        out["ecart_type_repetitions"] = round(float(np.std(par_rep)), 4)
    for dim in ("chiffre", "longueur"):
        out["par_" + dim] = {str(v): m([r for r in recs if r[dim] == v], "succes") for v in sorted({r[dim] for r in recs})}
    out["par_cellule"] = {f"{c}|{l}": m([r for r in recs if r["chiffre"] == c and r["longueur"] == l], "succes")
                          for c in ciphers.CHIFFRES for l in sorted({r["longueur"] for r in recs})
                          if any(r["chiffre"] == c and r["longueur"] == l for r in recs)}
    return out


def _rec(s: dict, rep: int, clair: str | None, extra: dict, seuil: float) -> dict:
    ex = exactitude(clair, s["clair"])
    return {"id": s["id"], "chiffre": s["chiffre"], "longueur": s["longueur"], "rep": rep,
            "exactitude": round(ex, 4), "succes": int(ex >= seuil), **extra}


def run_outils_seuls(corpus, reps, seed, seuil, bruit=None) -> list[dict]:
    out = []
    for r in range(reps):
        for s in corpus:
            ct = C.bruiter(s["chiffre_texte"], bruit, seed + r) if bruit else s["chiffre_texte"]
            t0 = time.perf_counter(); res = an.solveur_outils_seuls(ct, seed + r)
            out.append(_rec(s, r, res["clair"], {"duree_s": round(time.perf_counter() - t0, 3), "type_trouve": res["type"]}, seuil))
    return out


def run_agents(corpus, reps, seed, seuil, llm_factory, p_outil=0.0, bruit=None, trace_dir=None) -> list[dict]:
    out = []
    for r in range(reps):
        llm = llm_factory(seed + r)
        for s in corpus:
            ct = C.bruiter(s["chiffre_texte"], bruit, seed + r) if bruit else s["chiffre_texte"]
            orch = Orchestrateur(llm, p_panne_outil=p_outil, seed=seed + r, trace_dir=trace_dir)
            st, _ = orch.resoudre(ct, f"{s['id']}-r{r}")
            out.append(_rec(s, r, st.clair, {
                "duree_s": st.duree_s, "type_trouve": st.type_chiffre, "statut": st.statut, "iterations": len(st.tentatives),
                "appels_llm": st.appels_llm, "repli": st.repli, "desaccords": st.desaccords_linguiste,
                "format_invalide": st.format_invalide}, seuil))
    return out


def sauver_raw(recs, chemin: Path):
    chemin.parent.mkdir(parents=True, exist_ok=True)
    chemin.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in recs) + "\n", encoding="utf-8", newline="\n")


def kasiski_etude(corpus) -> dict:
    out = {}
    for nom in ("vigenere", "autoclave"):
        ss = [s for s in corpus if s["chiffre"] == nom and s["longueur"] >= 200]
        ok = 0
        for s in ss:
            k = an.kasiski(s["chiffre_texte"], max_len=12)
            top = [c["longueur"] for c in k["longueurs_candidates"][:3]]
            ok += int(len(s["cle"]) in top)
        out[nom] = {"n": len(ss), "longueur_vraie_dans_top3": round(ok / max(len(ss), 1), 4)}
    return out


def exercices_valides(n_par_type: int = 10) -> dict:
    tot = ok = 0
    for t in ciphers.CHIFFRES:
        for g in range(n_par_type):
            e = an.generer_exercice("LETEXTEQUIVASERVIRDEBASEPOURLEXERCICEDECRYPTOGRAPHIE", t, g)
            cle = tuple(e["cle"]) if t == "affine" else e["cle"]
            tot += 1
            ok += int(ciphers.dechiffrer(t, e["enonce"], cle) == e["corrige_clair"])
    return {"n": tot, "valides": ok, "taux": round(ok / tot, 4)}


def shannon(corpus_test: str) -> dict:
    m = modele()
    h = -m.score(corpus_test) * math.log2(10)           # bits/lettre (estimation par entropie croisée, borne haute)
    d = math.log2(26) - h
    cles = {"cesar": math.log2(25), "affine": math.log2(312), "vigenere_6": 6 * math.log2(26),
            "substitution": math.log2(math.factorial(26))}
    return {"entropie_bits_par_lettre": round(h, 3), "redondance_bits_par_lettre": round(d, 3),
            "distance_unicite_lettres": {k: round(v / d, 1) for k, v in cles.items()},
            "note": "H estimée sur un petit corpus (borne haute de l entropie -> redondance sous-estimée -> U surestimée)"}



def _pic_memoire_mo():
    """Pic mémoire du processus (Mo) ; None si indisponible (Windows)."""
    if resource is None:
        return None
    v = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return round(v / 1024 / 1024 if sys.platform == "darwin" else v / 1024, 1)  # macOS : octets, Linux : Ko


def _ram_go():
    """RAM totale (Go) sur Linux, macOS et Windows ; None si indisponible."""
    try:
        if sys.platform.startswith("linux"):
            return round(int(Path("/proc/meminfo").read_text(encoding="utf-8").split()[1]) / 1024 / 1024, 1)
        if sys.platform == "darwin":
            import subprocess
            return round(int(subprocess.check_output(["sysctl", "-n", "hw.memsize"]).strip()) / 1024 ** 3, 1)
        if sys.platform == "win32":
            import ctypes

            class MS(ctypes.Structure):
                _fields_ = [("l", ctypes.c_ulong), ("m", ctypes.c_ulong), ("total", ctypes.c_ulonglong), ("a", ctypes.c_ulonglong),
                            ("b", ctypes.c_ulonglong), ("c", ctypes.c_ulonglong), ("d", ctypes.c_ulonglong), ("e", ctypes.c_ulonglong),
                            ("f", ctypes.c_ulonglong)]
            ms = MS(); ms.l = ctypes.sizeof(MS)
            ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(ms))
            return round(ms.total / 1024 ** 3, 1)
    except Exception:  # noqa: BLE001
        pass
    return None


def environnement(cfg, corpus_hash, modeles) -> dict:
    pk = {}
    for n in ("numpy", "pydantic", "PyYAML", "matplotlib"):
        try:
            from importlib.metadata import version
            pk[n] = version(n)
        except Exception:  # noqa: BLE001
            pk[n] = None
    ram = _ram_go()
    prompts = {p.name: _sha(p) for p in sorted((Path(__file__).parent / "prompts").glob("*.md"))}
    return {"version": __version__, "python": sys.version.split()[0], "plateforme": platform.platform(), "cpu_count": os.cpu_count(),
            "ram_go": ram, "paquets": pk, "pic_memoire_mo": _pic_memoire_mo(),
            "config_sha256": hashlib.sha256(json.dumps(cfg, sort_keys=True).encode()).hexdigest(),
            "corpus_eval_sha256": corpus_hash, "prompts_sha256": prompts, "modeles_llm": modeles}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default=str(RACINE / "config/experiment.yaml"))
    ap.add_argument("--profil", choices=["full", "small"], default="full")
    ap.add_argument("--llm", action="store_true", help="évaluer avec Ollama (sinon : baseline + agents scriptés seulement)")
    ap.add_argument("--out", default=str(RACINE / "results"))
    a = ap.parse_args(argv)
    cfg = yaml.safe_load(Path(a.config).read_text(encoding="utf-8")); out = Path(a.out); t_start = time.time()
    seed, seuil = cfg["seed"], cfg["succes_seuil_exactitude"]
    small = a.profil == "small"
    reps = 1 if small else cfg["corpus"]["repetitions"]
    cc = cfg["profil_small"]["taille_corpus"] if small else cfg["corpus"]
    corpus = C.generer(seed, cc["longueurs"], cc["par_cellule"], langue=cfg["corpus"]["langue"])
    h = C.sauver(corpus, RACINE / "data/corpus_eval.jsonl")
    print(f"[corpus] {len(corpus)} échantillons sha256={h[:12]}")
    metrics: dict = {"meta": {"profil": a.profil, "n_echantillons": len(corpus), "repetitions": reps, "seed": seed,
                              "seuil_succes_exactitude": seuil, "corpus_sha256": h}}

    print("[1/6] baseline outils seuls"); r0 = run_outils_seuls(corpus, reps, seed, seuil)
    sauver_raw(r0, out / "raw/outils_seuls.jsonl"); metrics["outils_seuls"] = agreger(r0)
    print("[2/6] agents + outils (politique à règles, sans LLM)")
    sc = lambda s: ScriptedClient()  # noqa: E731
    r1 = run_agents(corpus, reps, seed, seuil, sc, trace_dir=str(RACINE / "traces/scripted") if not small else None)
    sauver_raw(r1, out / "raw/agents_scriptes.jsonl"); metrics["agents_scriptes"] = agreger(r1)

    print("[3/6] robustesse")
    rob = {}
    rb = run_agents(corpus, 1, seed, seuil, sc, bruit=cfg["robustesse"]["bruit_frappe"]); rob["bruit_frappe"] = agreger(rb)
    rob["bruit_frappe"]["taux_bruit"] = cfg["robustesse"]["bruit_frappe"]
    sauver_raw(rb, out / "raw/robustesse_bruit.jsonl")
    if cfg["robustesse"]["anglais"]:
        en = C.generer(seed, [200, 500], 3, langue="en")
        re_ = run_agents(en, 1, seed, seuil, sc); rob["anglais"] = agreger(re_)
        sauver_raw(re_, out / "raw/robustesse_anglais.jsonl")
    metrics["robustesse"] = rob

    print("[4/6] injection de pannes")
    sub = [s for s in corpus if s["longueur"] in (200, 500)] if not small else corpus
    pan = {"llm": {}, "outil": {}}
    for p in cfg["pannes"]["p_llm"]:
        rr = run_agents(sub, 1, seed, seuil, lambda s, p=p: FaultyClient(ScriptedClient(), p, s)); a_ = agreger(rr)
        pan["llm"][str(p)] = {"succes_global": a_["succes_global"], "repli_moyen": a_["repli_moyen"], "format_invalide_moyen": a_["format_invalide_moyen"]}
    for p in cfg["pannes"]["p_outil"]:
        rr = run_agents(sub, 1, seed, seuil, sc, p_outil=p); a_ = agreger(rr)
        pan["outil"][str(p)] = {"succes_global": a_["succes_global"], "repli_moyen": a_["repli_moyen"]}
    metrics["pannes"] = pan

    print("[5/6] analyses complémentaires")
    metrics["kasiski"] = kasiski_etude(C.generer(seed + 1, [500], 20, ("vigenere", "autoclave")))
    metrics["exercices_pedagogue"] = exercices_valides()
    metrics["shannon"] = shannon(C.texte_test("fr"))

    print("[6/6] LLM local")
    modeles_env = {}
    if a.llm:
        llm_cfg = cfg["llm"]
        ss = cfg["profil_small"] if small else llm_cfg
        sel = [s for s in C.generer(seed, ss["sous_ensemble"]["longueurs"], ss["sous_ensemble"]["par_cellule"], langue=cfg["corpus"]["langue"])]
        liste = {"petit": {"ollama": cfg["profil_small"]["modele"]}} if small else llm_cfg["modeles"]
        metrics["llm"] = {}
        for etiq, mc in liste.items():
            cli0 = OllamaClient(mc["ollama"], temperature=llm_cfg["temperature"], seed=seed, num_ctx=llm_cfg["num_ctx"])
            modeles_env[etiq] = {"modele": mc["ollama"], "digest": cli0.digest(), "temperature": llm_cfg["temperature"], "num_ctx": llm_cfg["num_ctx"]}
            if modeles_env[etiq]["digest"] is None:
                metrics["llm"][etiq] = {"statut": "non_execute", "raison": "Ollama injoignable ou modèle absent (ollama pull)"}
                print(f"  ! {mc['ollama']} indisponible"); continue
            fab = lambda s, mc=mc: OllamaClient(mc["ollama"], temperature=llm_cfg["temperature"], seed=s, num_ctx=llm_cfg["num_ctx"])
            rr = run_agents(sel, ss["repetitions"], seed, seuil, fab, trace_dir=str(RACINE / f"traces/llm_{etiq}"))
            sauver_raw(rr, out / f"raw/agents_llm_{etiq}.jsonl"); metrics["llm"][etiq] = {"modele": mc["ollama"], **agreger(rr)}
    else:
        metrics["llm"] = {"statut": "non_execute", "raison": "option --llm absente"}

    metrics["meta"]["duree_totale_s"] = round(time.time() - t_start, 1)
    metrics["meta"]["pic_memoire_mo"] = _pic_memoire_mo()
    out.mkdir(parents=True, exist_ok=True)
    (out / "metrics.json").write_text(json.dumps(metrics, indent=2, ensure_ascii=False), encoding="utf-8", newline="\n")
    (out / "ENVIRONMENT.json").write_text(json.dumps(environnement(cfg, h, modeles_env), indent=2, ensure_ascii=False), encoding="utf-8", newline="\n")
    from .figures import tracer
    tracer(metrics, out / "figures")
    print(f"OK -> {out}/metrics.json ({metrics['meta']['duree_totale_s']} s)")


if __name__ == "__main__":
    main()
