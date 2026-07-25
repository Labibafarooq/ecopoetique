"""
Task 2 — Figurative Subcategory Classification
Classifies each figurative case from Johanna's corpus into one of 18 subcategories
defined by Riccardo Barontini (schema_analogies_vivant_complet_0807.csv — 16
original + 3 new: COUL, LOC_IDIOM, IMAG, added 2026-07-08; META_JUXT eliminated
2026-07-10 per Riccardo's confirmation, folded into META_APP).

Prompt restructured 2026-07-08 as a sequential DECISION TREE (mirroring how a
linguist would actually parse the sentence) instead of a flat 19-way pick —
same technique that fixed Task 0's RÉGIME NARRATIF, and matches literature on
LLM-assisted rule-script/decision-procedure prompting for figurative-language
classification (see MIPVU rule-script generation, arxiv 2603.10784). Gold-set
validation (2026-07-08, 86 rows) found several of the old flat-list rule-based
heuristics (META_ATTR/DE_PARANGON/DE_QUANTIF/META_JUXT regexes) were WORSE than
chance (16.7% accuracy) — removed; only kept the handful of unambiguous
fixed-phrase rules (COMME_SI, COMP_DEG, MOD_ANALOG) that don't require
structural judgment calls.

Input:  figuratifs_task1_own.csv — built by build_figurative_cases.py from OUR
        OWN Task 1 (qwen3) référentiel/figuré results, NOT the old
        métaphores_identifiées_gpt.csv (Joanna's ChatGPT-based figurative
        set — wrong input, found 2026-07-09: only ~half overlaps with our
        own Task 1 figuré rows). Per Riccardo (2026-06-25 meeting): "you
        should use yours [not Joanna's ChatGPT results]." Re-run
        build_figurative_cases.py once Task 1 plantes finishes to refresh
        this file before scaling to the full corpus.
Output: resultats_task2_subcategories.csv
"""

import os, csv, re, json, time, requests
from collections import Counter

OLLAMA_URL  = "http://localhost:11435/api/chat"
MODEL       = "qwen3:30b"
INPUT_FILE  = os.path.expanduser("~/ecopoetique/métaphore/figuratifs_task1_own.csv")
OUTPUT_FILE = os.path.expanduser("~/ecopoetique/métaphore/resultats_task2_subcategories.csv")
LOG_FILE    = os.path.expanduser("~/ecopoetique/métaphore/task2_progress.log")
CHECKPOINT  = 50  # save every N rows
TIMEOUT     = 300

# ── 19 SUBCATEGORIES from Riccardo (schema_analogies_vivant_complet_0807) ────
SUBCATEGORIES = {
    "COMME_SN":       ("comparaison similative",       "Adj/V + comme + SN",                    "rusé comme un renard ; courir comme un lièvre"),
    "COMME_P":        ("comparaison phrastique",        "P1 comme P2",                           "les branches craquaient comme les os d'un vieux cerf"),
    "COMME_SI":       ("comparaison hypothétique",      "comme si + P",                          "comme si une forêt entière retenait son souffle"),
    "COMP_DEG":       ("comparaison quantitative",      "plus/moins/aussi/autant que",           "plus lent qu'une tortue ; plus haut qu'un séquoia"),
    "DE_PARANGON":    ("analogie nominale en de",       "N1 de N2, N1 = qualité",                "mémoire d'éléphant ; patience de tortue"),
    "DE_MATIERE":     ("métaphore matérialisante",      "N abstrait + de + matière",             "volonté de granit ; calme de roc"),
    "DE_UNIVERS":     ("analogie d'univers",            "N + de + domaine imaginaire ou naturel","océan de verdure ; montagne de nuages"),
    "DE_QUANTIF":     ("quantification métaphorique",   "N quantifieur + de + N",                "une forêt de pylônes ; un essaim de pensées"),
    "DE_PROP":        ("analogie proportionnelle",      "N1 de N2",                              "vautours de la finance ; loups de la spéculation"),
    "META_ATTR":      ("métaphore attributive",         "N1 est N2",                             "cet homme est un loup ; cette ville est une fourmilière"),
    "META_APP":       ("métaphore appositionnelle",     "apposition / juxtaposition / binôme nominal", "la montagne sentinelle ; le fleuve serpent ; arbre-parapluie ; forêt cathédrale"),
    "META_VERB":      ("métaphore verbale",             "verbe incompatible",                    "la forêt avalait la lumière ; le glacier agonisait"),
    "MOD_ANALOG":     ("analogie modalisée",            "sembler, on dirait, avoir l'air de",    "on aurait dit une meute de nuages"),
    "ANALOG_COMPLEX": ("analogie complexe",             "comparaison enchâssée / filée",         "à côté de cette tempête, les loups semblaient apprivoisés"),
    "META_FILEE":     ("métaphore filée",               "réseau métaphorique continu",           "la rivière serpentait, muait, puis renaissait comme un reptile au printemps"),
    "COUL":           ("couleur",                       "couleur + référent du vivant",          "vert pomme ; bleu ciel"),
    "LOC_IDIOM":      ("locution idiomatique",           "expression figée",                      "avoir la chair de poule ; poser un lapin"),
    "IMAG":           ("représentation",                 "image, dessin, sculpture, motif",       "un tableau représentant un lion ; une robe à fleurs"),
}

VALID_CODES = list(SUBCATEGORIES.keys())

# ── RULE-BASED PRE-FILTER — REMOVED 2026-07-09, then ONE rule reinstated ────
# Gold validation showed the "safe" fixed-phrase regexes (COMME_SI/COMP_DEG/
# MOD_ANALOG) were 0/7 (0%) at gold-check — because `context` is often a full
# multi-sentence paragraph and the regex matches ANY occurrence of the
# trigger phrase anywhere in it, not just the clause around the token. All
# classification was routed to the LLM as a result.
#
# 2026-07-09 (later): found `métaphore/liste_expressions.csv` — a 72-entry
# curated lexicon of genuinely fixed French animal idioms (built by Joanna's
# team pre-Task-2, e.g. "poser un lapin", "rusé comme un renard") with the
# exact token_lexique each maps to, and `filter_idiomatic.py` which already
# used it upstream for a different purpose. This is a real, pre-existing,
# hand-curated resource — not a regex guess — so unlike the removed rules,
# an EXACT case-insensitive substring match of one of these 65 known fixed
# expressions is high-precision by construction (these are established
# idioms, not coincidental phrase co-occurrence). Reinstated as the only
# rule, scoped to require the literal idiom string in the token's own
# sentence-local context (still whole `contexte` field, but the match target
# is a multi-word fixed phrase, not a short generic pattern, so the false-
# positive-from-elsewhere-in-paragraph risk that killed the old rules is
# much lower).
IDIOM_LEXICON_PATH = os.path.expanduser("~/ecopoetique/métaphore/liste_expressions_figées.txt")
try:
    with open(IDIOM_LEXICON_PATH, encoding="utf-8") as _f:
        KNOWN_IDIOMS = [line.strip().lower() for line in _f if line.strip()]
except FileNotFoundError:
    KNOWN_IDIOMS = []

def rule_based_classify(token, context):
    ctx = context.lower()
    for expr in KNOWN_IDIOMS:
        if expr in ctx:
            return "LOC_IDIOM"
    return None  # uncertain → send to LLM

# ── LLM PROMPT — sequential decision-tree, not a flat 19-way pick ───────────
def make_prompt(token, context, category):
    return f"""Tu es expert en stylistique française et en figures de style.

Le mot «{token}» (catégorie: {category}) est utilisé de façon FIGURATIVE dans ce contexte:
«{context}»

Détermine la catégorie structurelle de cette figure en suivant CET ORDRE de
questions (comme un arbre de décision — réponds à la première question qui
s'applique, ne compare pas toutes les catégories en même temps).
⚠ DISCIPLINE D'ORDRE OBLIGATOIRE : teste les questions UNE PAR UNE, dans
l'ordre numéroté. Dès qu'une question s'applique clairement, réponds avec
son code et ARRÊTE-TOI — ne continue pas à évaluer les questions suivantes
"au cas où" une autre catégorie semblerait mieux correspondre. En particulier
si tu vois "comme" dans la phrase, les questions 5 à 7 doivent être
tranchées AVANT de considérer une structure "N de N2" (question 10) — ne
laisse jamais un "de" plus loin dans la phrase te faire remonter vers
DE_PARANGON/DE_PROP si un "comme" pertinent aurait dû répondre à la question
7 en premier.

1. Y a-t-il une expression figée/lexicalisée où «{token}» a perdu son sens
   littéral d'animal/plante ? Quelques exemples illustrant des FORMES variées
   que peut prendre une expression figée (le point commun n'est pas la forme
   syntaxique mais le fait que le sens global est FIXÉ par l'usage, indépendant
   du sens propre de chaque mot) :
   - avec "comme" : "rusé comme un renard", "muet comme une carpe"
   - avec "de" : "larmes de crocodile", "rat de bibliothèque", "travail de fourmi"
   - nom composé : "bouc émissaire", "chant du cygne"
   - locution verbale : "avoir la chair de poule", "poser un lapin",
     "avoir une araignée au plafond"
   ⚠ EXCLUS de LOC_IDIOM — vérifie ces 4 cas AVANT de conclure LOC_IDIOM,
   même si l'expression "a l'air" figée. Si l'un s'applique, va directement
   à la question indiquée plutôt que de répondre ici :
   - L'expression sert à COULEUR (ex: "poivre et sel" pour des cheveux) →
     ne réponds PAS ici, va à la question 2 (COUL).
   - L'expression sert à ATTRIBUER un trait/nom à une personne ou un
     animal PRÉCIS déjà identifié dans le contexte (ex: "brebis égarée"
     pour désigner quelqu'un qui s'écarte du droit chemin, "faire l'âne
     pour avoir du son" pour décrire le comportement de quelqu'un) → ne
     réponds PAS ici, va à la question 11 (META_ATTR).
     ⚠ Test décisif LOC_IDIOM vs META_ATTR : la phrase NOMME-t-elle ou
     SURNOMME-t-elle une personne/un animal PRÉCIS déjà présent dans le
     contexte avec ce mot, même sans copule explicite ? Si oui → META_ATTR,
     même si la tournure "a l'air" d'une expression figée courante.
     Contraste : "on le traite de rat" (un individu précis, désigné par ce
     mot comme une étiquette/un surnom qui lui est directement appliqué) →
     META_ATTR, PAS LOC_IDIOM — même si "traiter qqn de rat" est une
     tournure courante/répétée dans la langue. VS "il a un appétit d'ogre"
     (l'expression décrit une QUALITÉ générique — la voracité — sans
     désigner ou surnommer la personne elle-même comme "un ogre") →
     LOC_IDIOM, PAS META_ATTR. La différence : dans le premier cas le mot
     devient littéralement le nom/l'étiquette de la personne ; dans le
     second, le mot reste un élément d'une locution qualificative sans
     devenir le nom de qui que ce soit.
   - Après "comme", le nom garde un sens LITTÉRAL actif dans la scène
     (l'animal/la plante est réellement en train d'agir ou d'être visé
     dans ce passage précis, même si la comparaison est classique) — ex:
     "se faire tirer comme des lièvres" (de vrais lièvres sont chassés
     dans cette scène), "tomber comme des mouches" (de vraies morts en
     cascade sont décrites) → ce n'est PAS une locution figée mais une
     comparaison vivante, ne réponds PAS ici, va à la question 6 (COMP_DEG
     si "plus/moins/aussi... que") ou 7 (COMME_SN/COMME_P).
     ⚠ AUTO-VÉRIFICATION OBLIGATOIRE avant de répondre LOC_IDIOM : retire
     mentalement "comme" + le mot-clé de la phrase. Reste-t-il un événement
     ou une action CONCRÈTE et LITTÉRALE décrite dans le passage (des morts,
     une chasse, un mouvement réel) ? Si oui, ce n'est PAS LOC_IDIOM, quel
     que soit l'air "figé" de la tournure — c'est une comparaison vivante
     (question 6 ou 7). Ne réponds LOC_IDIOM que si retirer la comparaison
     ne changerait RIEN au sens factuel de la phrase.
   - Le contexte décrit une représentation/symbole (photo, motif, dessin,
     objet décoratif) plutôt qu'un usage figuré de langage (ex: "fleurs de
     lis" sur un drapeau, "à l'eau de rose" en référence à des photos
     sentimentales) → ne réponds PAS ici, va à la question 3 (IMAG).
   Si aucun de ces 4 cas ne s'applique → LOC_IDIOM.
2. «{token}» désigne-t-il une COULEUR (ex: "vert pomme", "bleu ciel") plutôt
   qu'un être vivant ? → COUL
3. Le contexte décrit-il une REPRÉSENTATION du vivant — pas seulement une
   image/dessin/sculpture explicite, mais aussi une simple RESSEMBLANCE DE
   FORME/silhouette avec le vivant (ex: "un tableau représentant un lion" ;
   "une tache en forme de haricot" ; "des motifs à fleurs de lis") — plutôt
   que le vivant lui-même agissant ou étant décrit ? → IMAG
4. AVANT de choisir une catégorie ponctuelle, vérifie d'abord si la figure
   s'étend sur PLUSIEURS PROPOSITIONS/PHRASES avec un réseau d'images
   cohérent qui se DÉVELOPPE ou VARIE (pas juste un mot isolé, ex: "si sous
   lui elle était génisse, devant l'obstacle elle se révélait jument" — deux
   images animales successives pour la même personne) ? Si oui → META_FILEE.
   Sinon, continue aux questions suivantes pour cette occurrence ponctuelle.
5. Y a-t-il "comme si" ? → COMME_SI
6. Y a-t-il une comparaison de degré ("plus/moins/aussi/autant... que") ? → COMP_DEG
7. Y a-t-il "comme" (sans "si") ? Regarde ce qui suit "comme" :
   - Un simple groupe nominal, SANS verbe conjugué propre à la comparaison
     (même si le groupe nominal est un peu long, ex: "comme les tentacules
     d'une pieuvre") → COMME_SN
   - Une proposition complète avec son PROPRE verbe conjugué (ex: "comme les
     os craquent") → COMME_P
8. Y a-t-il "sembler", "on dirait", "avoir l'air de", "faire l'effet de", ou
   une tournure équivalente de perception/auto-perception analogique
   ("se voir", "se sentir devenir", "s'imaginer en") ? → MOD_ANALOG
9. «{token}» est-il placé JUSTE À CÔTÉ d'un nom (sujet ou complément) SANS
   copule ("est/était"), SANS "de" — une simple apposition, épithète directe,
   OU mot composé/juxtaposition directe avec ou sans trait d'union (ex: "la
   montagne sentinelle", "poulpe enfiévré tournoyant dans ma bouche",
   "arbre-parapluie", "forêt cathédrale") ? → META_APP. Ce cas couvre aussi
   ce qu'on appelait autrefois META_JUXT (catégorie éliminée le 2026-07-10
   sur confirmation de Riccardo — tout binôme nominal/juxtaposition va
   désormais dans META_APP). Ce cas doit être écarté AVANT de considérer
   "N1 de N2" ou la copule ci-dessous — ne choisis DE_PARANGON/META_ATTR que
   si une vraie copule ou un vrai "de" relie les deux noms.
10. Y a-t-il une structure "N1 de N2" (sans "comme") ? Regarde la relation entre N1 et N2 :
    - N1 est une qualité/trait exemplifié par N2 (ex: "mémoire d'éléphant" =
      la qualité "mémoire" illustrée par l'éléphant) → DE_PARANGON
    - N1 est un nom abstrait rapporté à une MATIÈRE/substance (ex: "volonté de
      granit") → DE_MATIERE
    - N1 est rapporté à un domaine imaginaire/naturel plus large (ex: "océan
      de verdure") → DE_UNIVERS
    - N1 est un quantifieur collectif (essaim, meute, troupeau...) + N2 (ex:
      "un essaim de pensées") → DE_QUANTIF
    - N1 appartient à la catégorie/le domaine de N2, relation de type
      "membre de" (ex: "vautours de la finance") → DE_PROP
    ⚠ DE_PARANGON vs DE_PROP (souvent confondues) : DE_PARANGON illustre UNE
    QUALITÉ précise (mémoire, patience, ruse...) au moyen d'un animal/une
    plante réputé pour cette qualité — "mémoire d'éléphant" = la qualité
    "mémoire", illustrée par l'éléphant, réputé pour ça. DE_PROP place
    plutôt N2 dans un DOMAINE/UN GROUPE (finance, politique, spectacle...)
    et utilise N1 comme un TITRE/UNE ÉTIQUETTE DE CATÉGORIE pour les
    membres de ce domaine, sans qualité isolée précise — "vautours de la
    finance" ne dit pas "la qualité vautour", ça dit "les gens de la
    finance, qu'on catégorise comme des vautours". Test : peux-tu remplacer
    N1 par "la qualité de X" et garder le sens (mémoire d'éléphant → "la
    qualité mémoire, comme chez l'éléphant") ? Si oui → DE_PARANGON. Si N2
    est plutôt un domaine/groupe social et N1 une étiquette appliquée à SES
    membres → DE_PROP.
    ⚠ EXCLUS de DE_PARANGON (et des autres sous-cas ci-dessus) si le "N de N2"
    est en fait la partie prédicative d'une copule d'IDENTITÉ ("il est LE X
    de N2", "elle est celle de N2" — la phrase affirme une identité, pas
    juste une qualité illustrée) → ne réponds pas ici, va plutôt à la
    question 11 (META_ATTR). Ex: "il est le cerf de ma vie" (affirmation
    d'identité "il EST le cerf") → META_ATTR, pas DE_PARANGON.
11. Y a-t-il une copule "est/était" (N1 est N2, ex: "cet homme est un loup") OU un
    surnommage/désignation identifiante (ex: "on le surnomme le rat", "on l'appelle
    la vipère", "on le traite de macaque" — «{token}» devient littéralement le nom/
    surnom donné à quelqu'un) ? → META_ATTR
    ⚠ EXCLUS de META_ATTR si la copule est au conditionnel/hypothétique
    ("si X était Y, ..." — une hypothèse, pas une affirmation d'identité) :
    si c'est ponctuel → question 5 (COMME_SI) ; si l'image hypothétique se
    prolonge/se développe sur plusieurs phrases → question 4 (META_FILEE).
    ⚠ DISTINCTION AVEC META_VERB (question 12, juste après) : si «{token}»
    est lui-même le SUJET ou l'ATTRIBUT d'une copule d'identité (le mot-clé
    EST ce qu'on affirme) → META_ATTR (ex: "cet homme est un loup",
    "j'ai engendré un chicon" — chicon est l'identité/le produit affirmé,
    pas une action). Si «{token}» est plutôt le sujet d'un VERBE D'ACTION
    normalement incompatible avec lui, même si une copule existe ailleurs
    dans la phrase → META_VERB (ex: "le chêne a répliqué" — chêne accomplit
    l'action humaine de répliquer, ce n'est pas une identité affirmée).
12. Y a-t-il un VERBE dont le sens littéral est incompatible avec son sujet
    (ex: "la forêt avalait la lumière", "le glacier agonisait", "le chêne a
    répliqué" — «{token}» accomplit une ACTION qui lui est normalement
    impossible, plutôt que de simplement RECEVOIR une identité/un nom via
    une copule) ? → META_VERB
13. Plusieurs figures sont-elles imbriquées/enchâssées les unes dans les
    autres (une comparaison DANS une autre comparaison) ? → ANALOG_COMPLEX

Réponds UNIQUEMENT avec ce JSON (indique aussi le numéro de question qui a
déclenché ta réponse, pour vérification) :
{{"code": "CODE", "question_number": N, "raison": "explication courte en français"}}"""

# ── OLLAMA CALL ───────────────────────────────────────────────────────────────
def call_ollama(prompt):
    try:
        resp = requests.post(OLLAMA_URL, json={
            "model": MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
            "options": {"temperature": 0, "num_predict": 8000, "num_ctx": 16384},
        }, timeout=TIMEOUT)
        resp.raise_for_status()
        content = resp.json()["message"]["content"]
        content = re.sub(r'<think>.*?</think>', '', content, flags=re.DOTALL).strip()
        m = re.search(r'\{.*?\}', content, re.DOTALL)
        if m:
            data = json.loads(m.group(0))
            code = data.get("code","").strip().upper()
            raison = data.get("raison","").strip()
            if code in VALID_CODES:
                return code, raison
        # Try to find any valid code in response
        for code in VALID_CODES:
            if code in content:
                return code, ""
        return "UNKNOWN", content[:100]
    except Exception as e:
        return "ERROR", str(e)[:80]

# ── MAIN ─────────────────────────────────────────────────────────────────────
def main():
    # Load input
    with open(INPUT_FILE, encoding='utf-8') as f:
        rows = list(csv.DictReader(f, delimiter='\t'))
    print(f"Total figurative cases: {len(rows)}")

    # Load already done
    done = set()
    existing = []
    if os.path.exists(OUTPUT_FILE):
        with open(OUTPUT_FILE, encoding='utf-8') as f:
            existing = list(csv.DictReader(f))
            done = {(r['fichier'], r['token_lexique'], r['contexte'][:50]) for r in existing}
        print(f"Already done: {len(done)} — resuming")

    # Open log
    log = open(LOG_FILE, 'a', encoding='utf-8')

    fields = ['fichier','token_lexique','contexte','categorie','lemme',
              'decision','subcategory','method','raison']

    # Open output in append mode
    write_header = not os.path.exists(OUTPUT_FILE) or len(existing) == 0
    out_f = open(OUTPUT_FILE, 'a', newline='', encoding='utf-8')
    writer = csv.DictWriter(out_f, fieldnames=fields, extrasaction='ignore')
    if write_header:
        writer.writeheader()

    rule_count = llm_count = error_count = 0
    start = time.time()

    for i, row in enumerate(rows, 1):
        key = (row['fichier'], row['token_lexique'], row['contexte'][:50])
        if key in done:
            continue

        token   = row.get('token_lexique','').strip()
        context = row.get('contexte','').strip()
        cat     = row.get('categorie','').strip()

        # Try rule-based first
        code = rule_based_classify(token, context)
        method = "rule"

        if code is None:
            # Send to LLM
            code, raison = call_ollama(make_prompt(token, context, cat))
            method = "llm"
            if code in ("UNKNOWN","ERROR"):
                error_count += 1
                code = "UNKNOWN"
                raison = raison
            else:
                llm_count += 1
        else:
            raison = "règle syntaxique"
            rule_count += 1

        out_row = {**row, 'subcategory': code, 'method': method, 'raison': raison}
        writer.writerow(out_row)
        out_f.flush()

        # Progress
        if i % 100 == 0:
            elapsed = time.time() - start
            rate = i / elapsed
            eta = (len(rows) - i) / rate / 3600
            msg = f"[{i:>5}/{len(rows)}] rule={rule_count} llm={llm_count} err={error_count} ETA={eta:.1f}h"
            print(msg)
            log.write(msg + '\n'); log.flush()

    out_f.close()
    log.close()

    # Final summary
    print(f"\n{'='*60}")
    print("TASK 2 — SUBCATEGORY DISTRIBUTION")
    print(f"{'='*60}")
    with open(OUTPUT_FILE, encoding='utf-8') as f:
        results = list(csv.DictReader(f))
    counts = Counter(r['subcategory'] for r in results)
    total = len(results)
    for code, n in sorted(counts.items(), key=lambda x: -x[1]):
        pct = n/total*100
        desc = SUBCATEGORIES.get(code, ("?","",""))[0]
        print(f"  {code:<18} {n:>5} ({pct:>5.1f}%)  {desc}")
    print(f"\n  Total: {total} | Rule-based: {rule_count} | LLM: {llm_count}")
    print(f"  Saved to: {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
