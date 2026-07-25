"""
Analyse d'agentivité — animaux et plantes référentiels
"""

import sys
import os
import polars as pl
from ast import literal_eval

def classify_relation(row):
    try:
        tete = literal_eval(row["tête"]) if isinstance(row["tête"], str) else row["tête"]
        tete_de_tete = literal_eval(row["tête_de_tête"]) if isinstance(row["tête_de_tête"], str) else row["tête_de_tête"]
    except:
        return "Autre"
    rel = tete[1] if tete and len(tete) > 1 else None
    if rel == "conj":
        rel = tete_de_tete[1] if tete_de_tete and len(tete_de_tete) > 1 else None
    if rel in ["nsubj", "ROOT", "obl:agent"]: return "Agent actif"
    elif rel == "nsubj:pass": return "Récepteur passif"
    elif rel == "nmod": return "Complément du nom"
    elif rel == "obj": return "Objet"
    else: return "Autre"

def analyse_file(filepath, name):
    if not os.path.exists(filepath):
        print(f"  File not found: {filepath}"); return None
    df = pl.read_csv(filepath, separator='\t', infer_schema_length=0)
    total = len(df)
    categories = [classify_relation(row) for row in df.iter_rows(named=True)]
    df = df.with_columns(pl.Series("catégorie", categories))
    counts = df.group_by("catégorie").len().sort("len", descending=True)
    print(f"\n{'='*55}\n  {name}\n  Total: {total:,}\n{'='*55}")
    results = {}
    for row in counts.iter_rows():
        cat, n = row
        pct = n/total*100
        print(f"  {cat:<25} {n:>7,}  ({pct:>5.1f}%)  {'█'*int(pct/3)}")
        results[cat] = {"n": n, "pct": pct}
    print(f"\n  → Agent actif:     {results.get('Agent actif',{}).get('pct',0):.1f}%")
    print(f"  → Passif:          {results.get('Récepteur passif',{}).get('pct',0):.1f}%")
    print(f"  → Objet:           {results.get('Objet',{}).get('pct',0):.1f}%")
    return results, total

base = os.path.expanduser("~/ecopoetique/morphosyntaxe")
files = [
    (f"{base}/dépendants_animaux_référentiels.csv", "ANIMAUX référentiels"),
    (f"{base}/dépendants_ANIMAUX.csv",              "ANIMAUX (tous)"),
    (f"{base}/dépendants_PLANTES.csv",              "PLANTES (tous)"),
]

print("="*55)
print("ANALYSE D'AGENTIVITÉ — Écopoétique")
print("="*55)
all_results = {}
for fp, name in files:
    r = analyse_file(fp, name)
    if r: all_results[name] = r

print(f"\n{'='*55}\nRÉSUMÉ COMPARATIF\n{'='*55}")
print(f"  {'Catégorie':<30} {'Agent%':>7} {'Passif%':>8} {'Objet%':>7}")
print(f"  {'-'*52}")
for name, (res, total) in all_results.items():
    a = res.get("Agent actif",{}).get("pct",0)
    p = res.get("Récepteur passif",{}).get("pct",0)
    o = res.get("Objet",{}).get("pct",0)
    print(f"  {name:<30} {a:>6.1f}% {p:>7.1f}% {o:>6.1f}%")
