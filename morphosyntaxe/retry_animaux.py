#!/usr/bin/env python3
"""
Retry failed batches from Task 1 animaux run.
Uses EXACT same prompt and batch logic as run_task1_corpus.py v6.
"""
import csv, json, os, re, requests, sys

OLLAMA_URL   = "http://localhost:11435/api/chat"
MODEL        = "qwen3:30b"
FAILED_FILE  = "/home/lfarooq/ecopoetique/resultats/task1_animaux_failed_keys.tsv"
OUTPUT_RETRY = "/home/lfarooq/ecopoetique/resultats/task1_animaux_retry.csv"
BATCH_SIZE   = 4

# ── Exact same examples as evaluate_all_goldsets_v6.py ────────────────────────
EXAMPLES_ANIMAUX = """
EXEMPLES — termes animaux (indépendants du jeu d'évaluation):

référentiel (animal réel):
• "Le fermier nourrissait ses poules chaque matin avant le lever du soleil."
  → poules = référentiel (vraies volailles d'élevage)
• "Un aigle tournoyait lentement au-dessus des rochers calcaires."
  → aigle = référentiel (oiseau réel observé dans la nature)
• "Elle tira le chat par la queue pour le faire descendre de la table."
  → chat = référentiel (animal domestique présent physiquement)
• "Le vétérinaire examina le cheval blessé pendant une heure."
  → cheval = référentiel (animal réel dans contexte vétérinaire)
• "Des moutons paissaient tranquillement dans le pré derrière la maison."
  → moutons = référentiel (vrais animaux dans un vrai pré)

figuré (métaphore, comparaison, expression idiomatique):
• "Monter sur ses grands chevaux — il s'est mis en colère pour rien."
  → chevaux = figuré (expression idiomatique, pas de vrais chevaux)
• "Elle avait un caractère de cochon — personne ne pouvait la supporter."
  → cochon = figuré (expression pour décrire le caractère d'une personne)
• "Les candidats tombaient comme des mouches face aux questions du jury."
  → mouches = figuré (comparaison, pas de vraies mouches)
• "Il était fort comme un bœuf, capable de soulever n'importe quoi."
  → bœuf = figuré (comparaison de force, pas un vrai bœuf)
• "Elle était le bouc émissaire de toute l'équipe depuis des mois."
  → bouc = figuré (expression idiomatique désignant une victime)
• "Ce politicien était un vrai caméléon, changeant d'avis selon les circonstances."
  → caméléon = figuré (métaphore pour quelqu'un d'inconsistant)
• "Paul est fort comme un lion — rien ne peut l'arrêter."
  → lion = figuré (comparaison de force appliquée à un humain)

CAS DIFFICILES — règles décisives:
• Animal + verbe d'action humaine complexe (parler, penser, décider) → figuré
• Expression figée connue (bouc émissaire, tête de linotte, etc.) → toujours figuré
• Animal dans une scène naturaliste/rurale/vétérinaire → référentiel
• "Comme + animal" pour décrire un humain → toujours figuré
• Animal sujet d'un verbe concret (manger, courir, voler) dans contexte réel → référentiel
"""

CORE_DEFINITIONS = """
DÉFINITIONS:
- référentiel: l'animal désigne un être vivant RÉEL — physiquement présent ou mentionné dans un contexte concret (nature, ferme, vétérinaire, zoologie, chasse, etc.)
- figuré: l'animal est utilisé comme métaphore, comparaison (avec "comme"), expression idiomatique, ou symbole abstrait décrivant une situation ou qualité humaine

⚠️ RÈGLES CLÉS:
1. Expression idiomatique connue → toujours figuré
2. Comparaison avec "comme" appliquée à un humain → figuré
3. Animal réellement présent dans la scène narrative → référentiel
4. Contexte scientifique, naturaliste, agricole, vétérinaire → référentiel
5. Animal sujet d'un verbe typiquement humain (parler, décider, voter...) → figuré
"""

def build_prompt_batch(batch):
    items = []
    for i, row in enumerate(batch):
        items.append(f'[{i}] TERME: <terme>{row["token_lexique"]}</terme> | PHRASE: {row["contexte"][:300]}')
    items_str = "\n".join(items)

    return f"""Tu es un expert en sémantique française. Classe chaque terme comme référentiel ou figuré.

{CORE_DEFINITIONS}

{EXAMPLES_ANIMAUX}

TERMES À CLASSER:
{items_str}

Réponds UNIQUEMENT avec ce JSON (un label par terme):
{{"results": [{{"id": 0, "label": "référentiel|figuré"}}, {{"id": 1, "label": "référentiel|figuré"}}, ...]}}"""


def classify_batch(batch):
    prompt = build_prompt_batch(batch)
    try:
        resp = requests.post(OLLAMA_URL, json={
            "model": MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
            "options": {"temperature": 0, "num_predict": 5000},
        }, timeout=180)
        resp.raise_for_status()
        raw = resp.json()["message"]["content"].strip()
        raw = re.sub(r"<think>.*?</think>", "", raw, flags=re.DOTALL).strip()

        m = re.search(r'\{.*\}', raw, re.DOTALL)
        if m:
            data = json.loads(m.group(0))
            labels = {}
            for r in data.get("results", []):
                lid = r.get("id")
                label = r.get("label", "").strip().lower()
                if "ref" in label:
                    labels[lid] = "référentiel"
                elif "fig" in label:
                    labels[lid] = "figuré"
            return labels
        return {}
    except Exception as e:
        print(f"    Batch error: {e}", flush=True)
        return {}


def main():
    # Load failed rows
    failed = []
    with open(FAILED_FILE, encoding="utf-8") as f:
        for row in csv.DictReader(f, delimiter="\t"):
            failed.append(row)

    print(f"Retrying {len(failed)} failed rows in batches of {BATCH_SIZE}", flush=True)
    print(f"ETA: ~{len(failed)*4/3600:.1f}h", flush=True)

    results = []
    fig_count = ref_count = 0
    i = 0

    for batch_start in range(0, len(failed), BATCH_SIZE):
        batch = failed[batch_start:batch_start + BATCH_SIZE]
        labels = classify_batch(batch)

        for j, row in enumerate(batch):
            label = labels.get(j, "référentiel")  # default to ref if failed
            if label == "figuré":
                fig_count += 1
            else:
                ref_count += 1
            i += 1
            results.append({
                "fichier":       row["fichier"],
                "token_lexique": row["token_lexique"],
                "contexte":      row["contexte"],
                "task1_label":   label,
            })

        if i % 100 == 0 or i >= len(failed):
            print(f"  [{i}/{len(failed)}] ref={ref_count} fig={fig_count} ({fig_count/max(i,1)*100:.1f}% fig)", flush=True)

    # Save
    with open(OUTPUT_RETRY, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["fichier","token_lexique","contexte","task1_label"], delimiter="\t")
        w.writeheader()
        w.writerows(results)

    print(f"\nDONE: {ref_count} ref / {fig_count} fig ({fig_count/len(failed)*100:.1f}% fig)", flush=True)
    print(f"Saved: {OUTPUT_RETRY}", flush=True)

if __name__ == "__main__":
    main()
