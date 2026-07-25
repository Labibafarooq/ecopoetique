# TASK 3 — AGENTIVITY ANALYSIS: FINAL RESULTS
## Écopoétique — Morphosyntactic Analysis
**Date:** 2026-07-10
**Author:** Labiba Farooq
**Supervisor:** Riccardo Barontini
**Method:** spaCy (`fr_core_news_lg`) dependency parsing, classified by syntactic relation (`nsubj`/`ROOT`/`obl:agent` → Agent actif, `nsubj:pass` → Récepteur passif, `nmod` → Complément du nom, `obj` → Objet, else → Autre)

This supersedes the earlier `morphosyntaxe/task3_full_report.md` (2026-06-22 + 2026-07-08 update), which predates the plantes refresh and the discovery of a bestsellers coverage gap in the humans file.

---

## 1. "GOLD-SET" EQUIVALENT — there isn't one, here's why, and what stands in for it

Unlike Task 1 (an LLM classifying référentiel/figuré, validated against Riccardo's hand-annotated gold sets), Task 3's classification is **deterministic**: it's a fixed rule applied to spaCy's dependency-parse output, not a model prediction. There's no human-annotated "correct answer" file to score against — the only way errors enter is (a) spaCy mis-parsing a sentence, or (b) the fixed rule mapping a dependency label to the wrong category.

**What stands in for gold-set accuracy**: a manual spot-check, reading 45 randomly sampled rows (3 per category × 5 categories × 3 populations: humains, animaux référentiels, plantes référentiels) against their actual sentence context, to check whether the syntactic label spaCy assigned is semantically sane.

### 1a. Spot-check results

| Population | Sampled | Clearly correct | Issues found |
|---|---|---|---|
| **Humains** | 15 | 12 | **3 — see below, a real systematic issue** |
| **Animaux référentiels** | 15 | 15 | none |
| **Plantes référentiels** | 15 | 15 | none |

Animaux and plantes came back clean — every sampled Agent actif/Passif/Objet/Complément/Autre row matched its sentence correctly, including genuine passive constructions for plants (e.g. "ce gazon serait... remplacé", "l'orme était désigné", "ce gui est... révélé" — all real passive-voice, not ambiguous).

### 1b. Real issue found: humans' "Récepteur passif" category is contaminated

All 3 sampled "Récepteur passif" human rows (Jésus/"blond", Charles/"assis", Dan/"gêné") turned out to be **être + adjective predicates** ("Jésus n'était pas blond", "Charles est assis", "Dan est gêné"), not genuine passive voice. I checked this systematically — pulled the head word for all 3,103 human rows tagged `nsubj:pass`, and the most frequent heads are dominated by **être-auxiliary intransitive verbs** (aller, venir, rester, naître, devenir, mourir — French verbs that conjugate with être in compound tenses, not true passives):

| Head word | Count | Real meaning |
|---|---|---|
| morte / mort | 63+ | died (état, not passive) |
| assis / assise | 100 | seated (predicate adjective) |
| restée | 44 | stayed |
| venue / venu | 40 + 35 | came |
| rentré | 39 | went home |
| allée / allé | 36 + 35 | went |
| revenue | 36 | came back |
| entrée | 33 | entered |
| né | 32 | born |
| devenue | 30 | became |

A minority (surpris, arrêté, pris) could be genuine passives ("was arrested by", "was surprised by") — but the majority of the 1.4% "passive receiver" figure for humans is very likely this auxiliary-être/adjectival-predicate confusion, not real passive voice. **This wasn't caught in the original 2026-06-22 report** (which only spot-checked 3 examples total, none from this category). Worth a proper fix (checking `token.tag_`/morphology to exclude être-intransitive verbs from the passive bucket) before this number goes anywhere official.

One more spot-checked issue: an Objet sample ("Allez les enfants, susurra **Ibrahim Santos**...") shows spaCy mis-tagging a subject-verb inversion after reported speech (very common in French dialogue: "dit-il", "murmura-t-elle") as an object instead of a subject — a known hard case for French dependency parsers, not something worth chasing down for the whole corpus but worth knowing the "Objet" numbers likely have some contamination from this pattern too.

---

## 2. FULL RESULTS TABLE — all subtasks

| Category | N | Active agent | Passive | Object | Noun complement |
|---|---|---|---|---|---|
| **HUMANS** (all, French-only names) | 219,651 | 37.2% | 1.4% | 12.8% | 20.1% |
| Humans — masculine | 118,142 | 38.2% | 1.3% | 13.2% | 18.8% |
| Humans — feminine | 44,529 | 37.7% | 1.8% | 12.9% | 21.2% |
| **ANIMALS** (référentiel, coverage-refreshed 2026-07-08) | 86,082 | 23.8% | 0.8% | 21.5% | 34.0% |
| **PLANTS** (référentiel, coverage-refreshed 2026-07-10) | 58,637 | 11.1% | 0.4% | 15.4% | 50.8% |

(Rows don't sum to 100% — remainder is "Autre"/unclassified: ~28.4% humans, ~19.9% animals, ~22.3% plants.)

**Hierarchy confirmed: Humans (37.2%) > Animals (23.8%) > Plants (11.1%)** — same conclusion as the original report, now on properly coverage-checked data for animals and plants. Humans still needs the same treatment (see §3).

---

## 3. HUMAN NAMES — current numbers, what's about to change, and what's untestable

### 3a. Current numbers (French-only spaCy model, built 2026-06-22)

Gender breakdown, **as it stands right now**:

| Gender | N | % | Active agent % |
|---|---|---|---|
| Masculine | 118,142 | 53.8% | 38.2% |
| Undetermined | 56,980 | 25.9% | — |
| Feminine | 44,529 | 20.3% | 37.7% |

These numbers come from `extract_humains.py`, which uses a **French-only** spaCy NER model (`fr_core_news_lg`). It cannot recognize English- or Arabic-origin names it hasn't seen in French-language training data, and it never processed the 88 `CORPUS_Bestsellers` novels at all (0/88 present in `dépendants_HUMAINS.csv` — a newly-discovered gap, separate from the multilingual issue, not yet fixed).

### 3b. What's about to change: the multilingual re-run

A second pipeline (`extract_humains_multilingual.py`) adds a multilingual NER pass (`Davlan/xlm-roberta-base-ner-hrl`, CPU-only) alongside the French model, specifically to catch English- and Arabic-origin character names the French-only model misses — motivated by Riccardo's own observation that the corpus (many Francophone-Africa/Maghreb-set novels) likely undercounts non-French names. **It computes gender the same way for every name** (French pronoun context + morphology), so gender detection isn't inherently smarter for foreign names — it just means names that were previously invisible to the pipeline now get a gender guess attempt at all, where before they contributed to nothing.

**Status: incomplete, not yet resumed.** Only 72 of 925 novels were processed (7.8%) before being stopped for cost reasons — full-corpus estimate is **~33-52 hours of CPU time** (estimates vary; the actual partial run's ETA at the point it was stopped was ~52h, worse than the original ~33h estimate, likely due to CPU contention with other work at the time).

**What that partial run found** (72 novels): 16,676 names via the French model, plus **1,407 additional names** caught only by the multilingual pass — real new catches include Hajar, Ourida, Rachid Hchicha, Si Salah, Fatima (plausible Arabic-origin names the French model would likely have missed) alongside expected French names it also happened to catch differently.

**No formal accuracy test exists for the multilingual approach** — what exists instead is the debugging history already in `CLAUDE.md`: four concrete bugs were found and fixed by manually inspecting extracted names (not a numeric accuracy score):
1. Subword-splitting (e.g. "Émile" → "É" + "mile") — fixed by merging zero-gap adjacent PER spans
2. One-sided truncation (e.g. "Mauny" → only "ny" survived) — fixed by extending to word boundaries
3. Animal/plant false positives (e.g. "Ours" tagged as a person) — fixed via cross-check against the animal/plant lexicons
4. Place-name false positives (e.g. "Sables" as in Sables-d'Olonne) — fixed via cross-check against spaCy's own LOC entities in the same novel

### 3c. Names that look bad and likely can't be fixed automatically

I pulled the actual 533 unique names the multilingual-only pass added in the 72-novel partial run and scanned them. Beyond the "Nirvana / Petit Prince / Barbie"-style examples already flagged in `CLAUDE.md`, real additional false positives found in the actual output:

| Type | Examples |
|---|---|
| Common nouns/adjectives mistaken for names | Tordu ("twisted"), Soigne ("take care"), Mauvais ("bad"), Cicatrice ("scar"), Martyr, Mademoiselle, Dieu ("God") |
| Fictional/mythological characters | Tintin, Yoda, Minotaure, Schtroumpf Grognon ("Grumpy Smurf"), Don Quichotte |
| Brand/organization/artwork names | Chanel, Tsahal (Israeli Defense Forces), Libé (shorthand for the newspaper Libération), Pietà |
| Tokenization artifacts (line-break hyphenation not rejoined) | "Ra-  chid Hchicha", "Veil-lette" |

None of these have a safe automated fix — distinguishing "Dieu" (God, a common noun here) from a legitimate character literally named that, or "Tintin" (a fictional character, arguably still a valid "human" agentivity subject in a literary-analysis sense) from noise, needs human/gold-set judgment, same conclusion `CLAUDE.md` already reached. Worth deciding with Riccardo whether fictional-character mentions (Tintin, Yoda, Don Quichotte) should even count as "human" for this analysis, since they're clearly intentional literary references, not extraction noise.

---

## 4. WHERE THE FILES LIVE

**Scripts:**
- `morphosyntaxe/extract_humains.py` — French-only human extraction (production, 925 novels — but see §3a's bestsellers gap)
- `morphosyntaxe/extract_humains_multilingual.py` — multilingual extension (in progress, 72/925 novels)
- `morphosyntaxe/analyse_agentivite.py` — agentivity classifier (animaux + plantes)
- `scripts/get_token_dependencies.py` — original single-purpose dependency-parse script
- `morphosyntaxe/reparse_plantes_missing.py` — new, built today, re-parses the plantes coverage gap

**Data — humans:**
- `morphosyntaxe/dépendants_HUMAINS.csv` — 219,651 rows, French-only, missing all 88 bestsellers novels
- `morphosyntaxe/dépendants_HUMAINS_multilingual.csv` — 18,083 rows, partial (72/925 novels only)

**Data — animals:**
- `morphosyntaxe/dépendants_animaux_référentiels_REFRESH.csv` — 86,082 rows, final, coverage-refreshed 2026-07-08

**Data — plants (built today):**
- `morphosyntaxe/dépendants_PLANTES_missing_rows.csv` — 7,516 re-parsed rows (bestsellers + corpus_principal gap), 99.7% match rate
- `morphosyntaxe/dépendants_PLANTES_COMPLET.csv` — 71,764 rows, merged (original + re-parsed)
- `morphosyntaxe/dépendants_plantes_référentiels_REFRESH.csv` — 58,637 rows, final, référentiel-only, 97.8% coverage

---

## 5. OPEN ITEMS

- **Humans' "Récepteur passif" (1.4%) is likely mostly être-auxiliary/adjectival-predicate contamination, not real passive voice** (§1b) — needs a proper fix (exclude être-intransitive verbs via morphology check) before being cited anywhere official.
- **Humans were never checked for the bestsellers coverage gap** that animaux/plantes both had — `dépendants_HUMAINS.csv` has 0/88 bestsellers novels. Should get the same re-parse treatment.
- **Multilingual name run is 7.8% done, not resumed** — full run is ~33-52 hours CPU time, zero GPU contention, so it can run alongside any GPU work. Decision needed on whether/when to resume.
- **Fictional-character names** (Tintin, Yoda, Don Quichotte) are being counted as "human" — worth asking Riccardo whether that's intended.
- **No formal accuracy number exists for the multilingual pipeline** — only qualitative bug-fixing via manual inspection. If a defensible accuracy claim is needed, would require a small hand-annotated sample.
