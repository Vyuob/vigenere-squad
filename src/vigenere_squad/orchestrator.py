"""Orchestrateur explicite : état partagé typé, boucle de vérification, replis, trace."""
from __future__ import annotations

import time
from dataclasses import asdict, dataclass, field

from .agents import Agent
from .tools import analysis as an
from .tools.ciphers import CHIFFRES
from .tools.lang import normaliser
from .tools.registry import Registre
from .trace import Trace

MAX_TENTATIVES = 6


@dataclass
class Tentative:
    hypothese: str
    type_trouve: str | None
    cle: str | None
    score: float | None
    linguiste_llm: bool | None
    verdict_code: bool | None
    accepte: bool


@dataclass
class EtatPartage:
    chiffre: str
    famille: str | None = None
    hypotheses: list[str] = field(default_factory=list)
    tentatives: list[Tentative] = field(default_factory=list)
    clair: str | None = None
    cle: str | None = None
    type_chiffre: str | None = None
    statut: str = "en_cours"  # resolu | non_verifie | echec
    explication: str | None = None
    exercice: str | None = None
    repli: int = 0
    desaccords_linguiste: int = 0
    appels_llm: int = 0
    appels_outils: int = 0
    format_invalide: int = 0
    duree_s: float = 0.0


class Orchestrateur:
    def __init__(self, llm, p_panne_outil: float = 0.0, seed: int = 0, trace_dir: str | None = None):
        self.llm, self.p_panne, self.seed, self.trace_dir = llm, p_panne_outil, seed, trace_dir

    def resoudre(self, chiffre: str, run_id: str = "run") -> tuple[EtatPartage, Trace]:
        t0 = time.perf_counter()
        trace = Trace(f"{self.trace_dir}/{run_id}.jsonl" if self.trace_dir else None, run_id)
        reg = Registre(self.p_panne, self.seed)
        ag = {r: Agent(r, self.llm, reg, trace) for r in ("classifieur", "cryptanalyste", "linguiste", "pedagogue")}
        ct = normaliser(chiffre)
        st = EtatPartage(chiffre=ct)
        trace.log("orchestrateur", "debut", longueur=len(ct))

        # 1. Classifieur
        r = ag["classifieur"].run(ct, {"longueur": len(ct)})
        if r is None:
            st.repli += 1
            trace.log("orchestrateur", "repli", cible="classifieur", action="ordre par défaut")
            st.hypotheses = ["vigenere", "beaufort", "autoclave", "cesar", "affine", "substitution"]
        else:
            st.famille = r["final"].get("famille")
            st.hypotheses = list(dict.fromkeys(r["final"]["hypotheses"]))
            trace.log("orchestrateur", "decision", etape="classification", famille=st.famille, hypotheses=st.hypotheses,
                      justification=r["final"].get("justification"))
        # on complète par les hypothèses non listées : la boucle finit par tout couvrir
        st.hypotheses += [h for h in CHIFFRES if h not in st.hypotheses]

        # 2. Boucle cryptanalyste -> linguiste
        meilleur = None
        for h in st.hypotheses[:MAX_TENTATIVES]:
            c = ag["cryptanalyste"].run(ct, {"hypothese": h, "rejets": [t.hypothese for t in st.tentatives], "graine": self.seed})
            cand = c["dernier_attaque"] if c else None
            if cand is None:
                st.repli += 1
                trace.log("orchestrateur", "repli", cible="cryptanalyste", hypothese=h, action="hypothèse ignorée")
                continue
            code = an.score_quadrigrammes(cand["clair"])
            lg = ag["linguiste"].run(cand["clair"], {"hypothese": h})
            llm_v = lg["final"].get("plausible") if lg else None
            if llm_v is None:
                st.repli += 1
                trace.log("orchestrateur", "repli", cible="linguiste", action="verdict du code")
            elif llm_v != code["au_dessus_seuil"]:
                st.desaccords_linguiste += 1
                trace.log("orchestrateur", "desaccord", cible="linguiste", llm=llm_v, code=code["au_dessus_seuil"])
            verdict = code["au_dessus_seuil"]  # le code a le dernier mot (garde-fou)
            t = Tentative(h, cand.get("type"), str(cand.get("cle")), cand["score"], llm_v, verdict, verdict)
            st.tentatives.append(t)
            trace.log("orchestrateur", "decision", etape="verification", hypothese=h, score=round(cand["score"], 3), accepte=verdict)
            if meilleur is None or cand["score"] > meilleur["score"]:
                meilleur = cand
            if verdict:
                meilleur = cand
                break
        if meilleur is None:
            st.statut = "echec"
        else:
            accepte = any(t.accepte for t in st.tentatives)
            if not accepte:
                trace.log("orchestrateur", "decision", etape="aucune hypothèse validée", action="meilleur score retenu")
            st.statut = "resolu" if accepte else "non_verifie"
            st.clair, st.cle, st.type_chiffre = meilleur["clair"], str(meilleur.get("cle")), meilleur.get("type")

        # 3. Pédagogue (explication + exercice) — jamais bloquant
        if st.clair is not None:
            resume = f"{len(st.tentatives)} hypothèse(s) testée(s) ; famille {st.famille}; score {meilleur['score']:.2f}"
            p = ag["pedagogue"].run(st.clair, {"type": st.type_chiffre, "cle": st.cle, "resume": resume})
            if p is None:
                st.repli += 1
                st.explication = f"Chiffrement {st.type_chiffre}, clé {st.cle}."
                trace.log("orchestrateur", "repli", cible="pedagogue", action="explication gabarit")
            else:
                st.explication = p["final"]["explication"]; st.exercice = p["final"].get("exercice")

        for a in ag.values():
            st.appels_llm += a.stats["llm"]; st.appels_outils += a.stats["outils"]; st.format_invalide += a.stats["format_invalide"]
        st.duree_s = round(time.perf_counter() - t0, 2)
        trace.log("orchestrateur", "fin", statut=st.statut, chiffrement=st.type_chiffre, duree_s=st.duree_s)
        return st, trace
