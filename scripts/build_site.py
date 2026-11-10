"""Construit site/index.html (page GitHub Pages) à partir de results/metrics.json — aucune valeur écrite à la main."""
import html
import json
import shutil
from pathlib import Path

R = Path(__file__).resolve().parents[1]
m = json.loads((R / "results/metrics.json").read_text(encoding="utf-8"))
env = json.loads((R / "results/ENVIRONMENT.json").read_text(encoding="utf-8"))
(R / "site/figures").mkdir(parents=True, exist_ok=True)
for f in (R / "results/figures").glob("*.png"):
    shutil.copy(f, R / "site/figures" / f.name)
pc = lambda v: "—" if v is None else f"{100 * v:.0f} %"  # noqa: E731


def table(agg, titre):
    ch = list(agg["par_chiffre"]); lg = list(agg["par_longueur"])
    rows = "".join("<tr><th>%s</th>%s</tr>" % (c, "".join("<td>%s</td>" % pc(agg["par_cellule"].get(f"{c}|{l}")) for l in lg)) for c in ch)
    return f"<h3>{html.escape(titre)} — global {pc(agg['succes_global'])} (n={agg['n']})</h3><table><tr><th></th>{''.join(f'<th>{l}</th>' for l in lg)}</tr>{rows}</table>"


llm = m.get("llm", {})
if "statut" in llm:
    llm_html = f"<p><b>LLM local non exécuté</b> dans cette version des résultats ({html.escape(llm.get('raison', ''))}).</p>"
else:
    llm_html = "".join(table(v, f"LLM {k} ({v.get('modele')})") if "n" in v and v.get("n") else f"<p>{k} : non exécuté</p>" for k, v in llm.items())
corps = f"""<!doctype html><html lang=fr><meta charset=utf-8><meta name=viewport content="width=device-width,initial-scale=1">
<title>Vigenère-Squad — résultats</title>
<style>:root{{color-scheme:light dark}}body{{font:16px/1.5 system-ui;max-width:60rem;margin:2rem auto;padding:0 1rem}}
table{{border-collapse:collapse;margin:.5rem 0}}td,th{{border:1px solid #8885;padding:.25rem .6rem;text-align:center}}img{{max-width:100%}}code{{background:#8882;padding:0 .2rem}}</style>
<h1>Vigenère-Squad — résultats</h1>
<p>Version {env['version']} · corpus sha256 <code>{m['meta']['corpus_sha256'][:16]}…</code> · {m['meta']['n_echantillons']} échantillons × {m['meta']['repetitions']} répétitions · profil <b>{m['meta']['profil']}</b>.
Succès = texte retrouvé à ≥ {int(100 * m['meta']['seuil_succes_exactitude'])} % de lettres exactes. Toutes les valeurs proviennent de <code>results/metrics.json</code>.</p>
<h2>Résultats principaux</h2>{table(m['outils_seuls'], 'Outils seuls (baseline sans agents)')}{table(m['agents_scriptes'], 'Agents + outils (politique à règles, sans LLM)')}
<h2>Avec LLM local</h2>{llm_html}
<h2>Figures</h2><img src="figures/succes_par_chiffre_longueur.png" alt="Succès par chiffrement et longueur"><img src="figures/pannes.png" alt="Pannes"><img src="figures/succes_vs_unicite.png" alt="Unicité"><img src="figures/longueur_min_vs_cle.png" alt="Longueur minimale vs longueur de clé">
<h2>Robustesse</h2><ul><li>5 % de lettres erronées : {pc(m['robustesse']['bruit_frappe']['succes_global'])}</li><li>Clair anglais : {pc(m['robustesse'].get('anglais', {}).get('succes_global'))}</li></ul>
<h2>Environnement</h2><pre>{html.escape(json.dumps({k: env[k] for k in ('python', 'plateforme', 'cpu_count', 'ram_go', 'modeles_llm')}, indent=1, ensure_ascii=False))}</pre>
<p><a href="https://github.com/Vyuob/vigenere-squad">Dépôt</a></p></html>"""
(R / "site/index.html").write_text(corps, encoding="utf-8", newline="\n")
print("site/index.html écrit")
