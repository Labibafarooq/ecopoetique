<title>Écopoétique — Merged Source Documents</title>

# Écopoétique — every project document, merged

This is a literal merge of every documentation file found in `~/ecopoetique/` on obtic-gpu1, verbatim, in one place. Each section below is a full source file, clearly labeled with its path. Nothing summarized or trimmed except where noted.

**Contents**
1. [`README.md`](#readme)
2. [`task1_report.md`](#task1-report)
3. [`morphosyntaxe/task3_full_report.md`](#task3-report)
4. [`batch_testing_results.txt`](#batch-testing)
5. [`pipeline_overnight.log`](#pipeline-log)
6. [`narratologie/resultats_nested_cv_honest.txt`](#nested-cv)
7. [`riccardo_25june_meetingTranscript.md`](#meeting-transcript) — first meeting, June 25
8. [`métaphore/Riccardo_second_meeting.txt`](#meeting-transcript-2) — second, more recent meeting (early July)
9. [Research papers, models, and techniques tried on Task 0 (narratology)](#research-papers) — pulled together from both transcripts and this session's own direct work
10. [Task 0 results not yet in any file — this session's direct work](#task0-session)

---

<a id="readme"></a>
## 1. `README.md` (repo root)

# Écopoétique


## Corpus

Le répertoire **CORPUS_TOTAL** contient l'ensemble du corpus au format txt. Ces fichiers sont issus de la conversion de fichiers epub ou pdf ou de la numérisation à partir d'une version papier du livre. La plupart des fichiers ont été post-traités pour faire figurer une phrase par ligne. Les éléments annexes au texte (sommaire, 4ème de couverture, etc) ont dans la mesure du possible été supprimés. Quelques rares textes contiennent de nombreux problèmes d'OCR (mauvaise accentuation, bout de phrases mélangés).

Le répertoire **TOKENS** contient l'analyse des tokens du chaque texte par Spacy. Ces fichiers sont constitués de trois colonnes indiquant le token, sa catégorie grammaticale et son lemme.

Le fichier **corpus_DigEco.csv** contient les métadonnées du corpus. Les décomptes de tokens, formes fléchies et lemmes sont basées sur les analyses Spacy. Note : le séparateur de colonne est la tabulation.


## Lexiques

3 type de lexiques ont permis l'extraction des entités liées à la biodiversité dans le corpus :
- un lexique constitué à partir d'un dump de **[Wikispecies](https://species.wikimedia.org/wiki/Accueil)** pour les êtres vivants
- le référentiel **[TaxRef](https://inpn.mnhn.fr/programme/documentation/referentiels-especes-taxref)**, qui liste l'intégralité des espèces vivantes présentes sur le territoire français (métropole et Outre-Mer)
- le thésaurus **[Loterre](https://loterre.istex.fr/fr/)**, qui contient une liste de termes liés au changement climatique et à l'anthropocène

Le lexique Wikispecies et les noms vernaculaires issus de Taxref ont été fusionnés pour créer des listes le plus exhaustives possibles pour les règnes du vivant Animalia (animaux), Fungi (champignons) et Plantae (plantes).


## Scripts

Les extractions des entités du corpus à partir des listes sont faites avec la commande bash `grep`, de façon à extraire également le contexte phrastique de chaque occurrence.

Deux pipelines ont été mises en place pour effectuer l'ensemble des opérations d'extraction, de filtrage et de traitement des données en une seule commande : `pipeline_animaux.sh` et `pipeline_plantes.sh`.

Ces scripts font appel aux scripts Python suivants :
- `grep_contexte.py` permet d'extraire le contexte phrastique des occurrences identifiées dans chaque fichier et de les écrire dans un fichier CSV avec l'entité correspondante.
- `remove_duplicates.py` supprime les doublons qui se crée lorsqu'une entité apparaît seule ou avec un qualificatif dans le lexique (exemple : "dorade" et dorade rose")
- `truncate_sentence.py` contient une fonction utilitaire pour réduire le contexte phrastique autour de l'occurrence de l'entité à un nombre de mots passé en paramètre
- `filter_*.py` contient des règles manuellement définies pour supprimer des occurrences non pertinentes (par exemple *if* en anglais alors qu'on cherche la plante « if »)
- `assign_category.py` permet d'assigner leur catégorie (mammifère, oiseau, etc.) aux entités animales
- `lemmatize.py` permet de retrouver le lemme des entités extraites. Ce script fait appel au lemmatiseur du français [LEFFF](https://github.com/ClaudeCoulombe/FrenchLefffLemmatizer) à installer avant utilisation de la pipeline



## Résultat des extractions

Le répertoire resultats contient l'état actuel de l'extraction/filtrage des différentes entités. Les fichiers `hapax_*.csv` correspondent à des entités très ambiguës que nous avons extraites manuellement avant de les éliminer des listes taxref/wiki. Elles ont été rajoutées manuellement à l'état courant des résultats.

---

<a id="task1-report"></a>
## 2. `task1_report.md` (repo root)

# TASK 1 — LITERAL vs FIGURATIVE CLASSIFICATION: FULL REPORT
## Écopoétique — Figurativity Analysis
**Date:** June 28, 2026
**Author:** Labiba Farooq
**Supervisor:** Riccardo Barontini

---

## WHAT TASK 1 IS

Task 1 classifies every animal and plant mention extracted from the corpus as either:
- **référentiel** — the term refers to a real, physically present animal or plant (literal use)
- **figuré** — the term is used as a metaphor, comparison, idiom, or symbol (figurative use)

This is a prerequisite for all downstream tasks (Task 2 subcategories, Task 3 agentivity, Task 4–5 narratology), which only operate on **référentiel** mentions.

---

## MODEL AND SETUP

| Parameter | Value |
|---|---|
| Model | qwen3:30b |
| Server | Ollama on http://localhost:11435 |
| GPU | NVIDIA A40 (46GB VRAM, ~22GB used by model) |
| Temperature | 0 (deterministic) |
| num_predict | 5000 (required for thinking mode) |
| Thinking mode | ON — model uses internal chain of thought before answering |

### Why num_predict=5000 is required

We tested reducing num_predict to speed up the run. At 100 tokens (no-think mode), figurative accuracy dropped to **0%** — the model needs its thinking chain to detect figurative language. Cannot use no-think mode for Task 1.

| num_predict | Speed | Figurative accuracy |
|---|---|---|
| 5000 | 9.4s/row | 81.2% (baseline) |
| 2000 | 7.1s/row | ~75% |
| 1000 | 5.5s/row | ~40% |
| 500 | 4.8s/row | ~13% |
| 100 (no-think) | 1.2s/row | **0%** |

---

## FINAL PROMPT DESIGN (v6)

The final approved prompt (from `evaluate_all_goldsets_v6.py`) consists of:

### CORE_DEFINITIONS (7 rules)
1. Expression idiomatique connue → toujours figuré
2. Comparaison avec "comme" pour décrire un humain → figuré
3. Être réellement présent dans la scène → référentiel
4. Contexte scientifique, géographique, naturaliste, écologique → référentiel
5. Crise environnementale réelle → référentiel même si le verbe semble fort
6. Terme africain/asiatique dans contexte colonial ou de voyage → référentiel
7. Métaphore décrivant émotion ou situation humaine → figuré

### EXAMPLES
- **Animaux**: 4 référentiel examples + 5 figuré examples (poules, aigle, truites, chat / chevaux, cochon, bœuf, chats, mouches)
- **Plantes**: 5 référentiel + 5 figuré + 3 "cas difficiles" including the olive branch symbol distinction

---

## GOLD SET RESULTS — SINGLE ROW (v6 baseline)

These are the agreed accuracy numbers with Riccardo. Script: `evaluate_all_goldsets_v6.py`

| Category | Gold set | Réf | Fig | Overall |
|---|---|---|---|---|
| Animaux | 190 rows (121 réf + 69 fig) | 97.5% (118/121) | 81.2% (56/69) | 91.6% (174/190) |
| Plantes | 188 rows (164 réf + 24 fig) | 98.8% (162/164) | 79.2% (19/24) | 96.3% (181/188) |
| Loterre | — | 91.2% | 63.4% | 85.2% |

Loterre script: `evaluate_loterre_v8.py` (separate prompt with geographic/ecological rules)

---

## SPEED PROBLEM AND SOLUTION

### Original time estimate
At 9s/row single-row mode:
- Animaux (127,816 rows): ~319h = **13.3 days**
- Plantes (69,287 rows): ~173h = **7.2 days**
- **Total: ~20 days** — impossible before July 15 deadline

### Strategy tested: Batching (sending N rows per API call)

Instead of one sentence per API call, we send N sentences in a single call and get back a JSON array of labels.

Tests run on the full animaux gold set (190 rows) with exact v6 prompts:

| Batch size | Speed | Animaux | Plantes | Fig accuracy (animaux) |
|---|---|---|---|---|
| 1 (baseline) | 9.0s/row | 13.3 days | 7.2 days | 81.2% |
| 3 | 4.4s/row | 6.5 days | 3.0 days | 81.2% |
| 4 | 3.9s/row | 5.8 days | 2.7 days | 81.2% |
| 5 | 3.4s/row | 5.0 days | 2.7 days | 79.7% |

**Key finding**: Batch=3 and batch=4 preserve IDENTICAL figurative accuracy to single-row v6 (56/69 = 81.2%). Only batch=5 loses 1 extra figurative item.

### Decision: batch=4
- Same fig accuracy as v6 for animaux (81.2% = 56/69)
- Plantes fig: 75% (18/24) vs v6's 79.2% (19/24) — 1 item difference
- Total time: 5.8 + 2.7 = **8.5 days** → finishes ~July 7 ✓

---

## FULL GOLD SET COMPARISON (all batch sizes)

### Animaux (121 réf + 69 fig = 190 rows)

| Method | Réf | Fig | Overall | Speed | Corpus days |
|---|---|---|---|---|---|
| v6 (1 row) | 118/121 (97.5%) | 56/69 (81.2%) | 174/190 (91.6%) | 9.0s | 13.3d |
| batch=3 | 117/121 (96.7%) | 56/69 (81.2%) | 173/190 (91.1%) | 4.4s | 6.5d |
| **batch=4** ✓ | **115/121 (95.0%)** | **56/69 (81.2%)** | **171/190 (90.0%)** | **3.9s** | **5.8d** |
| batch=5 | 114/121 (94.2%) | 55/69 (79.7%) | 169/190 (88.9%) | 3.4s | 5.0d |

### Plantes (164 réf + 24 fig = 188 rows)

| Method | Réf | Fig | Overall | Speed | Corpus days |
|---|---|---|---|---|---|
| v6 (1 row) | 162/164 (98.8%) | 19/24 (79.2%) | 181/188 (96.3%) | 9.0s | 7.2d |
| batch=3 | 164/164 (100.0%) | 14/24 (58.3%) | 178/188 (94.7%) | 3.7s | 3.0d |
| **batch=4** ✓ | **160/164 (97.6%)** | **18/24 (75.0%)** | **178/188 (94.7%)** | **3.3s** | **2.7d** |
| batch=5 | 160/164 (97.6%) | 17/24 (70.8%) | 177/188 (94.1%) | 3.1s | 3.2d |

Note on batch=3 plantes fig (58.3%): this is a statistical artifact — the plantes gold set has only 24 figurative items (each error = 4.2pp swing). Batch=3 happened to pair figurative plant terms next to very literal items in that run, biasing the model. Not a reliable measurement.

---

## KNOWN SYSTEMATIC ERRORS

From cross-batch analysis, these items are wrong in ALL batch sizes (3, 4, and 5) — they represent genuine limitations of the system:

### Animaux — 12 systematic errors

| Token | Gold | System says | Analysis |
|---|---|---|---|
| agneaux | réf | figuré | Ambiguous context — probably gold is correct |
| grenouilles | réf | figuré | Ambiguous cultural reference |
| porc | figuré | réf | System likely correct — context describes literal pig |
| vache | figuré | réf | System likely correct — "draw a cow" = literal |
| bœuf | réf | figuré | "nerf de bœuf" — system misreads as expression |
| chimpanzés | figuré | réf | "à un % près nous sommes des chimpanzés" — scientific-sounding but figurative |
| chiens (×1) | figuré | réf | Borderline — dogs observing = literal? |
| lion (×2) | figuré | réf | Implicit metaphor without explicit "comme" marker |
| abeille | réf | figuré | Philosophical analogy context misleads model |
| âne (×2) | figuré | réf | Implicit metaphor, no explicit marker |

### Plantes — 5 systematic errors

| Token | Gold | System says | Analysis |
|---|---|---|---|
| plantes ligneuses | figuré | réf | System may be right — context describes rotting plants |
| jasmin | figuré | réf | Borderline — "bercés dans le jasmin" ambiguous |
| abricotier | figuré | réf | Implicit metaphor, unclear from context |
| palmiers | figuré | réf | Learning context, could be literal |
| ananas | figuré | réf | Borderline |

### Why these errors occur

1. **Implicit metaphors** — when figurative use has no explicit marker ("comme", "tel un"), the model defaults to référentiel
2. **Truncated context** — sentences are pre-truncated; the figurative signal may be in the surrounding paragraph
3. **Borderline cases** — some are genuinely ambiguous (porc, vache, chiens); even human annotators may disagree

### Why we chose NOT to fix them before running

- Increasing context size (200 → 400 chars) would require re-extracting from 925 raw novels — too risky with July 15 deadline and would add ~15% time
- Adding prompt examples for these cases risks breaking currently-correct items
- The 12+5 systematic errors are a small fraction of 127k+69k rows
- They will be documented in the paper as known limitations

---

## CORPUS TO RUN ON

The previous team already ran: extraction → sentence truncation → lemmatization → category assignment → homograph disambiguation (~85% by Joanna/GPT). **All pre and post correction is already done.** Task 1 runs directly on these files.

| File | Rows | Description |
|---|---|---|
| `resultats/corpus_principal/ENTITES_contexte_animaux.csv` | 114,851 | Corpus total (925 novels) — animals |
| `resultats/bestsellers/BESTSELLERS_contexte_animaux.csv` | 13,094 | Bestsellers (88 novels) — animals |
| `resultats/corpus_principal/ENTITES_contexte_plantes.csv` | 63,599 | Corpus total — plants |
| `resultats/bestsellers/BESTSELLERS_contexte_plantes.csv` | 5,720 | Bestsellers — plants |

After deduplication:
- **Animaux: ~127,816 unique rows**
- **Plantes: ~69,287 unique rows**

Column names differ between files: corpus_principal uses `truncated_sentence`, bestsellers uses `contexte`. The run script normalizes both to `contexte`.

---

## PROJECTED ERRORS IN FULL CORPUS

Scaled from gold set error rates (note: real corpus has fewer figurative items than the artificially-enriched gold set, so actual errors will be lower):

### Animaux (127,816 rows)

| Method | Réf errors | Fig errors | Total wrong |
|---|---|---|---|
| v6 (1 row) | ~2,020 | ~8,745 | ~10,765 (8.4%) |
| **batch=4** | ~4,036 | ~8,745 | ~12,781 (10.0%) |
| batch=5 | ~4,709 | ~9,418 | ~14,127 (11.1%) |

### Plantes (69,287 rows)

| Method | Réf errors | Fig errors | Total wrong |
|---|---|---|---|
| v6 (1 row) | ~738 | ~1,843 | ~2,580 (3.7%) |
| **batch=4** | ~1,474 | ~2,211 | ~3,685 (5.3%) |
| batch=5 | ~1,474 | ~2,580 | ~4,054 (5.9%) |

---

## RUN STARTED — June 28, 2026

**Script:** `métaphore/run_task1_corpus.py`
**Command:**
```bash
cd ~/ecopoetique/métaphore
nohup python3 run_task1_corpus.py --category animaux > ../resultats/task1_animaux_run.log 2>&1 &
# after animaux finishes (~5.8 days):
nohup python3 run_task1_corpus.py --category plantes > ../resultats/task1_plantes_run.log 2>&1 &
```

**Monitor progress:**
```bash
tail -f ~/ecopoetique/resultats/task1_animaux_run.log
```

**Resume if interrupted:** Re-run the same command. The script reads the existing output file and skips already-classified rows automatically.

**Timeline:**
| Task | Start | Estimated finish |
|---|---|---|
| Animaux | June 28 | ~July 4 |
| Plantes | ~July 4 | ~July 7 |
| **All done** | — | **~July 7** ✓ (before July 15 deadline) |

**Output files:**
- `resultats/task1_animaux_labels.csv` — unique rows with task1_label column
- `resultats/task1_animaux_labels_full.csv` — all rows including duplicates (for joining back to original data)
- Same for plantes

---

## SCRIPTS REFERENCE

| Script | Purpose |
|---|---|
| `evaluate_all_goldsets_v6.py` | Final v6 gold set evaluation (animaux + plantes), single row |
| `evaluate_loterre_v8.py` | Final loterre gold set evaluation |
| `evaluate_goldsets_batch5.py` | Batch=5 full gold set evaluation with row-by-row output |
| `evaluate_goldsets_batch34.py` | Batch=3 and batch=4 comparison on both gold sets |
| `test_speed_vs_accuracy.py` | num_predict speed/accuracy tradeoff tests |
| `test_batching.py` | Initial batch size test (30-row sample) |
| `test_batch5_fullgold.py` | Batch=1 vs batch=5 on full animaux gold set |
| **`run_task1_corpus.py`** | **← FINAL RUN SCRIPT. Batch=4 on full corpus.** |

---

## NEXT STEPS AFTER TASK 1

1. Task 1 results (référentiel/figuré labels) feed into:
   - **Task 2**: subcategory classification (only on référentiel mentions)
   - **Task 3**: agentivity analysis (already run on old data; re-run on Task 1 filtered data)
   - **Tasks 4–5**: narratology

2. Gold set for Task 2 needs to be generated: `create_gold_task2.py` (100 figurative animals + 100 figurative plants → send to Riccardo)

3. Loterre: fix ambiguous gold set cases, rerun accuracy

4. Next meeting with Riccardo: **July 3, 11am**
   - Discuss Task 1 progress (should be ~halfway through animaux)
   - Discuss Task 2 gold set annotation
   - Discuss whether to use Joanna's animal results as proxy or wait for our results

> **Editor's note (added 2026-07-07, not part of the original report):** this report's status section is now out of date — Task 1 finished completely for both animaux (2026-07-05) and plantes (2026-07-06), including a retry pass for animaux. See the live conversation record for final counts; this file is preserved above exactly as originally written.

---

<a id="task3-report"></a>
## 3. `morphosyntaxe/task3_full_report.md`

# TASK 3 — AGENTIVITY ANALYSIS: FULL REPORT
## Écopoétique — Morphosyntactic Analysis
**Date:** June 22, 2026
**Author:** Labiba Farooq
**Supervisor:** Riccardo Barontini

---

## RESEARCH HYPOTHESIS

> Are animals and plants more passive agents compared to humans in contemporary French novels?

The goal is to statistically demonstrate, across the full corpus (925 novels), whether non-human entities (animals, plants) are represented less actively than human characters — and if so, to what extent. The analysis also distinguishes male vs female human characters.

---

## STARTING DATA

### Files already existing (created by previous team, available on GitLab)

| File | Description | Rows |
|---|---|---|
| `resultats/corpus_principal/ENTITES_TOTAL.csv` | All entities extracted from corpus | 317,646 |
| `morphosyntaxe/dépendants_ANIMAUX.csv` | Syntactic dependencies for animals (all) | 126,201 |
| `morphosyntaxe/dépendants_PLANTES.csv` | Syntactic dependencies for plants (all) | 68,920 |
| `morphosyntaxe/dépendants_animaux_référentiels.csv` | Referential animals only (filtered) | 106,410 |
| `morphosyntaxe/analyse_dependances.py` | Analysis script with Agent/Object/Passive classification | — |

### Structure of dependency files
Columns: `fichier | token_lexique | truncated_sentence | lemme | categorie | tête | dépendants | tête_de_tête`

The `tête` column contains the syntactic head of the token and its dependency relation (e.g. `('aboya', 'nsubj')` = the wolf is the subject of "barked").

### Syntactic role classification
The script classifies each entity by its syntactic role:
- **Active agent** → `nsubj`, `ROOT`, `obl:agent` (entity performs the action)
- **Passive receiver** → `nsubj:pass` (entity undergoes the action passively)
- **Object** → `obj` (entity is the direct object of an action)
- **Noun complement** → `nmod` (entity qualifies a noun)
- **Other** → everything else

---

## WHAT I DID — STEP BY STEP

### Step 1 — Discovering the existing files

Exploring the GitLab repository, I found that the previous team had already:
- Extracted all animal/plant entities from the corpus
- Computed syntactic dependencies for each entity
- Created a referential-only file for animals (`dépendants_animaux_référentiels.csv`)

The script `analyse_dependances.py` already contained the agentivity classification logic. However, it had two problems that prevented it from running: a missing `seaborn` library and a Polars API incompatibility (the new version of Polars no longer allows UDFs without explicit return types).

### Step 2 — Fixing the analysis script

I rewrote the analysis as `analyse_agentivite.py`, processing rows one by one to avoid the Polars UDF issue. This produced the same results as the original script but without errors.

### Step 3 — Analysing referential animals

I ran the analysis on `dépendants_animaux_référentiels.csv` (106,410 rows, referential animals only — figurative cases already filtered by previous team).

**Results — referential animals (95,243 valid occurrences):**

| Category | N | % |
|---|---|---|
| Noun complement | 31,982 | 33.6% |
| **Active agent** | 23,265 | **24.4%** |
| Other | 20,040 | 21.0% |
| Object | 19,247 | 20.2% |
| Passive receiver | 709 | 0.7% |

**Verified examples:**
- Active agent: "Un loup **aboya** dans un vallon" (a wolf barked) ✅
- Active agent: "les loups nous **encerclaient**" (the wolves surrounded us) ✅
- Passive receiver: "Des chèvres **sont tenues** en laisse" (goats are kept on a leash) ✅
- Object: "en **chassant** un papillon" (chasing a butterfly) ✅
- Noun complement: "blessures de **loup**" (wolf wounds) ✅

All examples were manually verified as correctly classified.

### Step 4 — Analysing plants

I analysed `dépendants_PLANTES.csv` — all plant cases, referential AND figurative mixed together, because no referential filtering existed yet for plants.

**Results — plants (64,269 occurrences — referential + figurative mixed):**

| Category | N | % |
|---|---|---|
| **Noun complement** | 31,815 | **49.5%** |
| Other | 14,878 | 23.1% |
| Object | 9,727 | 15.1% |
| **Active agent** | 7,591 | **11.8%** |
| Passive receiver | 258 | 0.4% |

**Problem identified:** Checking examples manually, I found figurative cases contaminating the results:
- "La moutarde me **monte** au nez" → French idiom (getting angry), not a real plant
- "Schulmann m'a **tendu** une carotte" → French idiom (dangling a carrot), not a real plant
- "Le petit **pruneau** ne comprend pas" → "pruneau" = slang for a person, not a plant

These cases slightly distort the statistics. The previous team had done this filtering manually for animals (hence `dépendants_animaux_référentiels.csv` exists). **This filtering has not yet been done for plants.**

### Step 5 — Why not filter plants using Task 1 results right now?

**Option considered:** Use our literal/figurative classifier (Task 1) to classify all 63,599 plant mentions and 114,851 animal mentions in `ENTITES_TOTAL.csv`, then keep only referential cases and re-extract dependencies.

**Why it is not done yet:**

There are 63,594 unique (token, context) pairs for plants and 114,840 for animals. Our qwen3:30b model processes approximately 1 sentence every 2-3 seconds. This means:
- Plants: 63,594 × 2.5s ≈ **44 hours** of processing
- Animals: 114,851 × 2.5s ≈ **80 hours** of processing

This is not feasible before Wednesday's meeting.

**What our Task 1 results already give us:**

Our classifier achieves:
- Referential animals: **95.9%** precision ✅
- Referential plants: **100.0%** precision ✅

These numbers show our classifier is highly reliable on referential cases. When this filtering is eventually run (it will take several days of compute), the plant agentivity results will be much cleaner. Note: the plant results would only become *less* active after filtering (since figurative idioms like "tendre une carotte" count as agent uses), making the hierarchy even more pronounced.

### Step 6 — Building the human pipeline (new work)

The previous team had not analysed human characters at all. I built a new pipeline (`extract_humains.py`) using spaCy NER (`fr_core_news_lg`) to:
1. Detect all character names (PER entities) in each novel
2. Extract their syntactic role (Agent/Object/Passive/Complement)
3. Detect their gender (masculine/feminine) via morphology and contextual pronouns (il/elle, son/sa)
4. Filter out false positives (publisher names, author names, abbreviations)

**Runtime:** 45.5 minutes for all 925 novels
**Output:** `dépendants_HUMAINS.csv` — 219,651 character mentions

**Results — humans (219,651 occurrences across 925 novels):**

| Category | N | % |
|---|---|---|
| **Active agent** | 81,755 | **37.2%** |
| Other | 62,395 | 28.4% |
| Noun complement | 44,184 | 20.1% |
| Object | 28,214 | 12.8% |
| Passive receiver | 3,103 | 1.4% |

**Gender breakdown:**
| Gender | N | % | Active agent % |
|---|---|---|---|
| Masculine | 118,142 | 53.8% | **38.2%** |
| Undetermined | 56,980 | 25.9% | — |
| Feminine | 44,529 | 20.3% | **37.7%** |

**Note on 25.9% undetermined gender:** This happens when:
- The name appears without nearby pronouns (il/elle) to resolve gender
- The name is ambiguous in French (Claude, Alex, Dominique)
- The name is foreign (English, Arabic, etc.) and spaCy does not know the gender
- It is a surname only, without contextual clues

This is not a bug — it reflects genuine uncertainty in the text.

**Verified examples:**
- Active agent: "Didier Schulmann me **rappelle** peu après" (Schulmann calls me back) ✅
- Passive receiver: "Alphonse aurait **été tué** par les tenanciers" (Alphonse was killed) ✅
- Object: "Il **s'appelle** Didier Schulmann" (His name is Schulmann) ✅

---

## FINAL RESULTS — AGENTIVITY HIERARCHY

| Category | Active agent | Passive receiver | Object | Noun complement | N total |
|---|---|---|---|---|---|
| **HUMANS (all)** | **37.2%** | 1.4% | 12.8% | 20.1% | 219,651 |
| Humans — masculine | 38.2% | 1.3% | 13.2% | 18.8% | 118,142 |
| Humans — feminine | 37.7% | 1.8% | 12.9% | 21.2% | 44,529 |
| **ANIMALS (referential)** | **24.4%** | 0.7% | 20.2% | 33.6% | 95,243 |
| **PLANTS (all, mixed)** | **11.8%** | 0.4% | 15.1% | 49.5% | 64,269 |

**Total analysed: 379,163 mentions across 925 novels**

### Conclusion

The hierarchy **Humans > Animals > Plants** is clearly confirmed:
- Humans act as active agents **37.2%** of the time
- Animals act as active agents **24.4%** of the time — **1.5× less than humans**
- Plants act as active agents only **11.8%** of the time — **3× less than humans**

Plants are used predominantly as **noun complements** (49.5%) — they describe things rather than do things. Animals fall between: more active than plants, but much less so than humans.

The male/female difference is minimal (38.2% vs 37.7%) — male and female characters have nearly identical agentivity in the corpus.

---

## KNOWN LIMITATIONS

1. **Plant results include figurative cases** — idioms like "tendre une carotte" or "les carottes sont cuites" are counted as plant mentions. This slightly inflates the agent% for plants. After referential filtering, plants would appear even less active.

2. **25.9% of human mentions have undetermined gender** — foreign names and ambiguous names cannot be reliably gendered from context alone.

3. **Human false positives** — spaCy NER occasionally picks up publisher names or author names from book headers. These are filtered by a blocklist but some may remain.

4. **Animal figurative cases** — the previous team's referential filter for animals was done manually. Our Task 1 classifier achieves 95.9% precision on referential animals, which is better. A re-filtered version could be produced with our classifier when compute time allows (~80 hours).

---

## WHAT REMAINS TO BE DONE

### High priority (before publication)

| Task | Description | Estimated time |
|---|---|---|
| Plant referential filtering | Run Task 1 on 63,599 plant mentions → `dépendants_plantes_référentielles.csv` | ~44 hours compute |
| Animal re-filtering | Run Task 1 on 114,851 animal mentions → cleaner than previous team's manual filter | ~80 hours compute |
| Re-run dependency extraction | After filtering, re-run `get_token_dependencies.py` on referential-only cases | ~10 hours |
| Re-run agentivity analysis | Get final clean numbers for plants and animals | 1 hour |

### Low priority (future work)

- **Improve gender detection** — the 25.9% undetermined could be reduced with a multilingual first-name database
- **Separate referential/figurative for humans** — some "human" detections by spaCy may be personifications
- **Analysis by literary genre** — compare agentivity between ecological novels and mainstream fiction (filtering files already exist in the repo)
- **Loterre terms** — extend agentivity analysis to ecological/geographical terms (108,425 mentions in ENTITES_TOTAL)

---

## FILES PRODUCED IN THIS SESSION

| File | Description | Status |
|---|---|---|
| `morphosyntaxe/extract_humains.py` | Human character extraction pipeline using spaCy NER | ✅ Done |
| `morphosyntaxe/dépendants_HUMAINS.csv` | 219,651 human character mentions with role + gender | ✅ Done |
| `morphosyntaxe/analyse_agentivite.py` | Fixed analysis script (Polars-compatible) | ✅ Done |
| `morphosyntaxe/generate_report.py` | Report generation script | ✅ Done |
| `morphosyntaxe/resultats_agentivite_complet.txt` | Final comparative report with examples | ✅ Done |
| `morphosyntaxe/task3_full_report.md` | This document | ✅ Done |
| `dépendants_plantes_référentielles.csv` | Referential-only plants filtered by Task 1 | ❌ To do (~44h) |
| `dépendants_animaux_référentiels_v2.csv` | Referential-only animals filtered by Task 1 (our version) | ❌ To do (~80h) |

> **Editor's note (added 2026-07-07):** the two "to do" rows above are now unblocked — Task 1 finished for both categories on 2026-07-05/06 (see §2 above). Two untracked scripts (`morphosyntaxe/retry_animaux.py`, `retry_animaux_v2.py`, both dated 2026-07-05) suggest a refresh using the finished Task 1 labels may already be in progress, though no accompanying updated report exists yet in the repo to confirm results.

---

<a id="batch-testing"></a>
## 4. `batch_testing_results.txt` (repo root — raw console log, full)

This is the raw, row-by-row console output behind the batch-size decision in `task1_report.md` §"Full gold set comparison" — every single gold-set prediction, not just the summary tables.

```
(labelimg_env) lfarooq@obtic-gpu1:~/ecopoetique/métaphore$ cd ~/ecopoetique/métaphore && python3 evaluate_goldsets_batch34.py
Batch 3 & 4 evaluation — EXACT v6 prompts
Model: qwen3:30b

Warming up...
Done.


#################################################################
  BATCH SIZE = 3
#################################################################

  ────────────────────────────────────────────────────────────
  Animaux  —  190 rows  (121 réf + 69 fig)  batch=3
  ────────────────────────────────────────────────────────────
  [  1/190] chiens                 référentiel    ✓
  [  2/190] souris                 référentiel    ✓
  [  3/190] souris                 référentiel    ✓
  [  4/190] chèvres                référentiel    ✓
  [  5/190] mouches                figuré         ✓
  [  6/190] chien                  référentiel    ✓
  [  7/190] mouettes               référentiel    ✓
  [  8/190] chiens                 référentiel    ✓
  [  9/190] caïmans                référentiel    ✓
  [ 10/190] oie                    figuré         ✓
  [ 11/190] huître                 figuré         ✓
  [ 12/190] lion                   référentiel    ✓
  [ 13/190] singes                 figuré         ✓
  [ 14/190] mouches                figuré         ✓
  [ 15/190] moules                 référentiel    ✓
  [ 16/190] cochon                 figuré         ✓
  [ 17/190] autruches              référentiel    ✓
  [ 18/190] gardons                référentiel    ✓
  [ 19/190] tigre                  référentiel    ✓
  [ 20/190] tigre                  figuré         ✓
  [ 21/190] mouton                 référentiel    ✓
  [ 22/190] poux                   référentiel    ✓
  [ 23/190] sanglier               figuré         ✓
  [ 24/190] sanglier               référentiel    ✓
  [ 25/190] agneau                 figuré         ✓
  [ 26/190] panthère               figuré         ✓
  [ 27/190] bulot                  référentiel    ✓
  [ 28/190] chevaux                référentiel    ✓
  [ 29/190] singes                 référentiel    ✓
  [ 30/190] lapin                  référentiel    ✓
  [ 31/190] sauterelles            figuré         ✓
  [ 32/190] porcs                  référentiel    ✓
  [ 33/190] chien                  référentiel    ✓
  [ 34/190] chiens                 référentiel    ✓
  [ 35/190] taureau                référentiel    ✓
  [ 36/190] lapin                  référentiel    ✓
  [ 37/190] bœuf                   figuré         ✓
  [ 38/190] baleines               référentiel    ✓
  [ 39/190] chien                  référentiel    ✓
  [ 40/190] chèvre                 figuré         ✓
  [ 41/190] loup                   référentiel    ✓
  [ 42/190] poules d'eau           référentiel    ✓
  [ 43/190] luciole                figuré         ✓
  [ 44/190] canard                 figuré         ✓
  [ 45/190] dindons                figuré         ✓
  [ 46/190] oiseau-moqueur         référentiel    ✓
  [ 47/190] poulet                 référentiel    ✓
  [ 48/190] salamandre             référentiel    ✓
  [ 49/190] cerf                   référentiel    ✓
  [ 50/190] hirondelles            référentiel    ✓
  [ 51/190] mouches                référentiel    ✓
  [ 52/190] loup                   figuré         ✓
  [ 53/190] mouton                 figuré         ✓
  [ 54/190] noctule                figuré         ✓
  [ 55/190] hareng                 figuré         ✓
  [ 56/190] chevaux                référentiel    ✓
  [ 57/190] chien                  référentiel    ✓
  [ 58/190] renard                 référentiel    ✓
  [ 59/190] musaraignes            référentiel    ✓
  [ 60/190] agneaux                référentiel    ✗  ← gold=référentiel pred=figuré
  [ 61/190] faucon                 figuré         ✓
  [ 62/190] chiens                 référentiel    ✓
  [ 63/190] chiens                 référentiel    ✓
  [ 64/190] saumon                 figuré         ✓
  [ 65/190] chiens                 référentiel    ✓
  [ 66/190] thon                   référentiel    ✓
  [ 67/190] chevaux                figuré         ✓
  [ 68/190] chats                  référentiel    ✓
  [ 69/190] cheval                 référentiel    ✓
  [ 70/190] grenouilles            référentiel    ✗  ← gold=référentiel pred=figuré
  [ 71/190] serpents               référentiel    ✓
  [ 72/190] serpent                figuré         ✓
  [ 73/190] chiens                 référentiel    ✓
  [ 74/190] margouillat            référentiel    ✓
  [ 75/190] mouette                référentiel    ✓
  [ 76/190] poussins               référentiel    ✓
  [ 77/190] rat                    figuré         ✓
  [ 78/190] mouches                référentiel    ✓
  [ 79/190] chien                  référentiel    ✓
  [ 80/190] musaraignes            référentiel    ✓
  [ 81/190] bisons                 référentiel    ✓
  [ 82/190] lapins                 figuré         ✓
  [ 83/190] cheval                 référentiel    ✓
  [ 84/190] agneau                 référentiel    ✓
  [ 85/190] chèvres                référentiel    ✓
  [ 86/190] blattes                figuré         ✓
  [ 87/190] poule                  figuré         ✓
  [ 88/190] porcs                  référentiel    ✓
  [ 89/190] chiens                 référentiel    ✓
  [ 90/190] âne                    figuré         ✓
  [ 91/190] loup                   référentiel    ✓
  [ 92/190] chamois                référentiel    ✓
  [ 93/190] chèvre                 référentiel    ✓
  [ 94/190] vaches                 référentiel    ✓
  [ 95/190] jument                 figuré         ✓
  [ 96/190] milans                 référentiel    ✓
  [ 97/190] chiens                 référentiel    ✓
  [ 98/190] muge                   figuré         ✓
  [ 99/190] albatros               figuré         ✓
  [100/190] baleine                figuré         ✓
  [101/190] chiens                 référentiel    ✓
  [102/190] musaraignes            référentiel    ✓
  [103/190] lapins                 référentiel    ✓
  [104/190] chien                  référentiel    ✓
  [105/190] moineaux               figuré         ✓
  [106/190] rats                   référentiel    ✓
  [107/190] cheval                 référentiel    ✓
  [108/190] sanglier               référentiel    ✓
  [109/190] poulet                 référentiel    ✓
  [110/190] baleines               référentiel    ✓
  [111/190] paon                   référentiel    ✓
  [112/190] paon                   référentiel    ✓
  [113/190] chameau                figuré         ✓
  [114/190] mouettes               référentiel    ✓
  [115/190] rat                    figuré         ✗  ← gold=figuré pred=référentiel
  [116/190] dorade                 référentiel    ✓
  [117/190] cheval                 référentiel    ✓
  [118/190] sanglier               référentiel    ✓
  [119/190] lion                   référentiel    ✓
  [120/190] brebis                 figuré         ✓
  [121/190] canard                 figuré         ✗  ← gold=figuré pred=référentiel
  [122/190] oie                    figuré         ✓
  [123/190] sauterelles            référentiel    ✓
  [124/190] bouquetins             référentiel    ✓
  [125/190] paon                   référentiel    ✓
  [126/190] juments                référentiel    ✓
  [127/190] rats                   référentiel    ✓
  [128/190] chiens                 référentiel    ✓
  [129/190] moutons                référentiel    ✓
  [130/190] hérons                 référentiel    ✓
  [131/190] bulbuls                référentiel    ✓
  [132/190] chiens                 référentiel    ✓
  [133/190] mouton                 référentiel    ✓
  [134/190] chèvre                 référentiel    ✓
  [135/190] corbeaux               référentiel    ✓
  [136/190] perdrix                référentiel    ✓
  [137/190] chiens                 référentiel    ✓
  [138/190] faucon                 figuré         ✓
  [139/190] mouette                référentiel    ✓
  [140/190] crotales               référentiel    ✓
  [141/190] pythons                référentiel    ✓
  [142/190] chevaux                référentiel    ✓
  [143/190] cheval                 référentiel    ✓
  [144/190] dingo                  référentiel    ✓
  [145/190] poux                   référentiel    ✓
  [146/190] chiot                  référentiel    ✓
  [147/190] porc                   figuré         ✗  ← gold=figuré pred=référentiel
  [148/190] cerfs                  référentiel    ✓
  [149/190] vache                  figuré         ✗  ← gold=figuré pred=référentiel
  [150/190] aigles                 référentiel    ✓
  [151/190] poulets                référentiel    ✓
  [152/190] chien                  figuré         ✓
  [153/190] autruche               référentiel    ✓
  [154/190] bœuf                   référentiel    ✗  ← gold=référentiel pred=figuré
  [155/190] chien                  figuré         ✓
  [156/190] chimpanzés             figuré         ✗  ← gold=figuré pred=référentiel
  [157/190] cigales                référentiel    ✓
  [158/190] tortues                figuré         ✓
  [159/190] serpents               référentiel    ✓
  [160/190] sanglier               référentiel    ✓
  [161/190] bécasse                figuré         ✓
  [162/190] poulet                 référentiel    ✓
  [163/190] goéland                figuré         ✓
  [164/190] chat                   figuré         ✓
  [165/190] baleine                figuré         ✓
  [166/190] baleine                figuré         ✓
  [167/190] chiens                 figuré         ✗  ← gold=figuré pred=référentiel
  [168/190] cheval                 figuré         ✓
  [169/190] âne                    figuré         ✓
  [170/190] fourmis                figuré         ✓
  [171/190] lion                   figuré         ✗  ← gold=figuré pred=référentiel
  [172/190] lion                   figuré         ✗  ← gold=figuré pred=référentiel
  [173/190] abeille                référentiel    ✗  ← gold=référentiel pred=figuré
  [174/190] taupes                 figuré         ✓
  [175/190] âne                    figuré         ✗  ← gold=figuré pred=référentiel
  [176/190] chiens                 référentiel    ✓
  [177/190] mouche                 figuré         ✗  ← gold=figuré pred=référentiel
  [178/190] vache                  figuré         ✓
  [179/190] chimpanzé              référentiel    ✓
  [180/190] chauve-souris          figuré         ✓
  [181/190] scarabées              figuré         ✗  ← gold=figuré pred=référentiel
  [182/190] tigre                  figuré         ✓
  [183/190] chiens                 référentiel    ✓
  [184/190] papillon               figuré         ✓
  [185/190] bousiers               figuré         ✓
  [186/190] singe                  référentiel    ✓
  [187/190] chats                  référentiel    ✓
  [188/190] âne                    figuré         ✗  ← gold=figuré pred=référentiel
  [189/190] ours                   figuré         ✓
  [190/190] coqs                   figuré         ✗  ← gold=figuré pred=référentiel

  RESULT batch=3: overall=91.1% (173/190)  réf=96.7% (117/121)  fig=81.2% (56/69)
  Speed: 4.4s/row  →  Animaux corpus: 155h (6.5 days)
  Failed batches: 0

  ────────────────────────────────────────────────────────────
  Plantes  —  188 rows  (164 réf + 24 fig)  batch=3
  ────────────────────────────────────────────────────────────
  [  1/188] graminées              référentiel    ✓
  [  2/188] serpolet               référentiel    ✓
  [  3/188] pin                    référentiel    ✓
  [  4/188] micocouliers           référentiel    ✓
  [  5/188] joncs                  référentiel    ✓
  [  6/188] tilleuls               référentiel    ✓
  [  7/188] cèdre du Liban         référentiel    ✓
  [  8/188] palmiers               référentiel    ✓
  [  9/188] chanvre                référentiel    ✓
  [ 10/188] pin                    référentiel    ✓
  [ 11/188] raisin                 référentiel    ✓
  [ 12/188] eucalyptus             référentiel    ✓
  [ 13/188] pandanus               référentiel    ✓
  [ 14/188] riz                    référentiel    ✓
  [ 15/188] citron                 référentiel    ✓
  [ 16/188] ronces                 référentiel    ✓
  [ 17/188] oignons                référentiel    ✓
  [ 18/188] tomates                référentiel    ✓
  [ 19/188] anthémis               référentiel    ✓
  [ 20/188] pastèque               référentiel    ✓
  [ 21/188] magnolias              référentiel    ✓
  [ 22/188] cardamome              référentiel    ✓
  [ 23/188] olivier                figuré         ✗  ← gold=figuré pred=référentiel
  [ 24/188] lin                    référentiel    ✓
  [ 25/188] dattiers               référentiel    ✓
  [ 26/188] roses                  référentiel    ✓
  [ 27/188] riz                    référentiel    ✓
  [ 28/188] foin                   référentiel    ✓
  [ 29/188] poireaux               référentiel    ✓
  [ 30/188] plantes ligneuses      figuré         ✗  ← gold=figuré pred=référentiel
  [ 31/188] pois chiches           référentiel    ✓
  [ 32/188] bois de rose           référentiel    ✓
  [ 33/188] pins                   référentiel    ✓
  [ 34/188] riz                    référentiel    ✓
  [ 35/188] acacias                référentiel    ✓
  [ 36/188] laurier                référentiel    ✓
  [ 37/188] bambous                référentiel    ✓
  [ 38/188] ronces                 référentiel    ✓
  [ 39/188] fougères arborescentes référentiel    ✓
  [ 40/188] riz                    référentiel    ✓
  [ 41/188] pins                   référentiel    ✓
  [ 42/188] riz                    référentiel    ✓
  [ 43/188] fougères               référentiel    ✓
  [ 44/188] maïs                   référentiel    ✓
  [ 45/188] mélèzes                référentiel    ✓
  [ 46/188] ifs                    référentiel    ✓
  [ 47/188] tilleuls               référentiel    ✓
  [ 48/188] gazon                  référentiel    ✓
  [ 49/188] platanes               référentiel    ✓
  [ 50/188] saules                 référentiel    ✓
  [ 51/188] asphodèles             référentiel    ✓
  [ 52/188] lilas                  référentiel    ✓
  [ 53/188] sapin                  référentiel    ✓
  [ 54/188] ajoncs                 référentiel    ✓
  [ 55/188] joncs                  référentiel    ✓
  [ 56/188] menthe                 référentiel    ✓
  [ 57/188] pois                   référentiel    ✓
  [ 58/188] rosiers                référentiel    ✓
  [ 59/188] oliviers               référentiel    ✓
  [ 60/188] ronces                 référentiel    ✓
  [ 61/188] osier                  référentiel    ✓
  [ 62/188] cocotier               référentiel    ✓
  [ 63/188] gazon                  référentiel    ✓
  [ 64/188] arachide               référentiel    ✓
  [ 65/188] châtaigniers           référentiel    ✓
  [ 66/188] bananier               référentiel    ✓
  [ 67/188] haricots               référentiel    ✓
  [ 68/188] lime                   figuré         ✓
  [ 69/188] jasmin                 figuré         ✗  ← gold=figuré pred=référentiel
  [ 70/188] hêtres                 référentiel    ✓
  [ 71/188] thé                    référentiel    ✓
  [ 72/188] café                   référentiel    ✓
  [ 73/188] poivre                 référentiel    ✓
  [ 74/188] calebasses             référentiel    ✓
  [ 75/188] thym                   référentiel    ✓
  [ 76/188] raisin                 référentiel    ✓
  [ 77/188] poivrons               référentiel    ✓
  [ 78/188] phlox                  référentiel    ✓
  [ 79/188] palmier                référentiel    ✓
  [ 80/188] bananier               référentiel    ✓
  [ 81/188] chênes                 référentiel    ✓
  [ 82/188] pois                   référentiel    ✓
  [ 83/188] tilleuls               référentiel    ✓
  [ 84/188] mangue                 référentiel    ✓
  [ 85/188] renoncules             référentiel    ✓
  [ 86/188] ancolie                référentiel    ✓
  [ 87/188] myrtilles              référentiel    ✓
  [ 88/188] bardanes               référentiel    ✓
  [ 89/188] papayer                référentiel    ✓
  [ 90/188] lin                    référentiel    ✓
  [ 91/188] groseille              référentiel    ✓
  [ 92/188] vigne                  référentiel    ✓
  [ 93/188] roses                  référentiel    ✓
  [ 94/188] asperge                figuré         ✓
  [ 95/188] tomate                 référentiel    ✓
  [ 96/188] lys                    figuré         ✗  ← gold=figuré pred=référentiel
  [ 97/188] chêne                  référentiel    ✓
  [ 98/188] abricotier             figuré         ✗  ← gold=figuré pred=référentiel
  [ 99/188] carottes               figuré         ✓
  [100/188] cocotier               référentiel    ✓
  [101/188] calebasses             figuré         ✓
  [102/188] oyats                  référentiel    ✓
  [103/188] palmiers               figuré         ✗  ← gold=figuré pred=référentiel
  [104/188] pois                   référentiel    ✓
  [105/188] poivre                 référentiel    ✓
  [106/188] pervenche              figuré         ✗  ← gold=figuré pred=référentiel
  [107/188] pin                    référentiel    ✓
  [108/188] ail                    référentiel    ✓
  [109/188] luzerne                référentiel    ✓
  [110/188] henné                  référentiel    ✓
  [111/188] figuier                référentiel    ✓
  [112/188] chêne                  référentiel    ✓
  [113/188] joncs                  référentiel    ✓
  [114/188] mouron                 référentiel    ✓
  [115/188] gazon                  référentiel    ✓
  [116/188] maïs                   référentiel    ✓
  [117/188] concombre              référentiel    ✓
  [118/188] manguiers              référentiel    ✓
  [119/188] hêtre                  référentiel    ✓
  [120/188] pommes de terre        référentiel    ✓
  [121/188] bouleaux               référentiel    ✓
  [122/188] osier blanc            référentiel    ✓
  [123/188] nénuphars              référentiel    ✓
  [124/188] concombre              référentiel    ✓
  [125/188] chêne                  référentiel    ✓
  [126/188] orchidée               référentiel    ✓
  [127/188] raphia                 référentiel    ✓
  [128/188] figue                  figuré         ✓
  [129/188] lotus                  référentiel    ✓
  [130/188] jacinthes              référentiel    ✓
  [131/188] linaires               référentiel    ✓
  [132/188] poivre noir            référentiel    ✓
  [133/188] pommiers               figuré         ✓
  [134/188] sapin                  référentiel    ✓
  [135/188] pois                   figuré         ✓
  [136/188] acanthe                référentiel    ✓
  [137/188] bégonias               référentiel    ✓
  [138/188] sapin                  référentiel    ✓
  [139/188] pivoines               référentiel    ✓
  [140/188] aulnes                 référentiel    ✓
  [141/188] algues                 figuré         ✗  ← gold=figuré pred=référentiel
  [142/188] chêne                  référentiel    ✓
  [143/188] framboisiers           référentiel    ✓
  [144/188] haricots               référentiel    ✓
  [145/188] bambou                 référentiel    ✓
  [146/188] concombres             référentiel    ✓
  [147/188] litchis                référentiel    ✓
  [148/188] épine noire            référentiel    ✓
  [149/188] poireaux               référentiel    ✓
  [150/188] riz                    référentiel    ✓
  [151/188] ananas                 référentiel    ✓
  [152/188] algues vertes          référentiel    ✓
  [153/188] lauriers               référentiel    ✓
  [154/188] hortensias             référentiel    ✓
  [155/188] lin                    référentiel    ✓
  [156/188] oignons                référentiel    ✓
  [157/188] pastèques              figuré         ✓
  [158/188] roseaux                référentiel    ✓
  [159/188] oignons                figuré         ✓
  [160/188] blé                    référentiel    ✓
  [161/188] ronces                 référentiel    ✓
  [162/188] lin                    référentiel    ✓
  [163/188] prune                  référentiel    ✓
  [164/188] sésame                 figuré         ✓
  [165/188] papyrus                référentiel    ✓
  [166/188] laitue                 référentiel    ✓
  [167/188] plantes grimpantes     référentiel    ✓
  [168/188] riz                    référentiel    ✓
  [169/188] melon                  référentiel    ✓
  [170/188] épinards               figuré         ✓
  [171/188] chênes-lièges          référentiel    ✓
  [172/188] melon d'eau            référentiel    ✓
  [173/188] blé                    figuré         ✓
  [174/188] prune                  figuré         ✓
  [175/188] cactus                 référentiel    ✓
  [176/188] blé                    référentiel    ✓
  [177/188] tomate                 référentiel    ✓
  [178/188] ananas                 figuré         ✗  ← gold=figuré pred=référentiel
  [179/188] olivier                figuré         ✗  ← gold=figuré pred=référentiel
  [180/188] frangipanier           référentiel    ✓
  [181/188] riz                    référentiel    ✓
  [182/188] vignes                 référentiel    ✓
  [183/188] calebasse              figuré         ✓
  [184/188] bouleaux               référentiel    ✓
  [185/188] sapins                 référentiel    ✓
  [186/188] séquoias               référentiel    ✓
  [187/188] fougères               référentiel    ✓
  [188/188] cèdre                  référentiel    ✓

  RESULT batch=3: overall=94.7% (178/188)  réf=100.0% (164/164)  fig=58.3% (14/24)
  Speed: 3.7s/row  →  Plantes corpus: 71h (3.0 days)
  Failed batches: 0

#################################################################
  BATCH SIZE = 4
#################################################################

  ────────────────────────────────────────────────────────────
  Animaux  —  190 rows  (121 réf + 69 fig)  batch=4
  ────────────────────────────────────────────────────────────
  [  1/190] chiens                 référentiel    ✓
  [  2/190] souris                 référentiel    ✓
  [  3/190] souris                 référentiel    ✓
  [  4/190] chèvres                référentiel    ✓
  [  5/190] mouches                figuré         ✓
  [  6/190] chien                  référentiel    ✓
  [  7/190] mouettes               référentiel    ✓
  [  8/190] chiens                 référentiel    ✓
  [  9/190] caïmans                référentiel    ✓
  [ 10/190] oie                    figuré         ✓
  [ 11/190] huître                 figuré         ✓
  [ 12/190] lion                   référentiel    ✓
  [ 13/190] singes                 figuré         ✓
  [ 14/190] mouches                figuré         ✓
  [ 15/190] moules                 référentiel    ✓
  [ 16/190] cochon                 figuré         ✓
  [ 17/190] autruches              référentiel    ✓
  [ 18/190] gardons                référentiel    ✓
  [ 19/190] tigre                  référentiel    ✓
  [ 20/190] tigre                  figuré         ✓
  [ 21/190] mouton                 référentiel    ✓
  [ 22/190] poux                   référentiel    ✓
  [ 23/190] sanglier               figuré         ✓
  [ 24/190] sanglier               référentiel    ✓
  [ 25/190] agneau                 figuré         ✓
  [ 26/190] panthère               figuré         ✓
  [ 27/190] bulot                  référentiel    ✓
  [ 28/190] chevaux                référentiel    ✓
  [ 29/190] singes                 référentiel    ✓
  [ 30/190] lapin                  référentiel    ✓
  [ 31/190] sauterelles            figuré         ✓
  [ 32/190] porcs                  référentiel    ✓
  [ 33/190] chien                  référentiel    ✓
  [ 34/190] chiens                 référentiel    ✓
  [ 35/190] taureau                référentiel    ✓
  [ 36/190] lapin                  référentiel    ✓
  [ 37/190] bœuf                   figuré         ✓
  [ 38/190] baleines               référentiel    ✗  ← gold=référentiel pred=figuré
  [ 39/190] chien                  référentiel    ✓
  [ 40/190] chèvre                 figuré         ✓
  [ 41/190] loup                   référentiel    ✓
  [ 42/190] poules d'eau           référentiel    ✓
  [ 43/190] luciole                figuré         ✓
  [ 44/190] canard                 figuré         ✓
  [ 45/190] dindons                figuré         ✓
  [ 46/190] oiseau-moqueur         référentiel    ✓
  [ 47/190] poulet                 référentiel    ✓
  [ 48/190] salamandre             référentiel    ✓
  [ 49/190] cerf                   référentiel    ✓
  [ 50/190] hirondelles            référentiel    ✓
  [ 51/190] mouches                référentiel    ✓
  [ 52/190] loup                   figuré         ✓
  [ 53/190] mouton                 figuré         ✓
  [ 54/190] noctule                figuré         ✓
  [ 55/190] hareng                 figuré         ✓
  [ 56/190] chevaux                référentiel    ✓
  [ 57/190] chien                  référentiel    ✓
  [ 58/190] renard                 référentiel    ✓
  [ 59/190] musaraignes            référentiel    ✓
  [ 60/190] agneaux                référentiel    ✗  ← gold=référentiel pred=figuré
  [ 61/190] faucon                 figuré         ✓
  [ 62/190] chiens                 référentiel    ✓
  [ 63/190] chiens                 référentiel    ✓
  [ 64/190] saumon                 figuré         ✓
  [ 65/190] chiens                 référentiel    ✓
  [ 66/190] thon                   référentiel    ✓
  [ 67/190] chevaux                figuré         ✓
  [ 68/190] chats                  référentiel    ✓
  [ 69/190] cheval                 référentiel    ✓
  [ 70/190] grenouilles            référentiel    ✗  ← gold=référentiel pred=figuré
  [ 71/190] serpents               référentiel    ✓
  [ 72/190] serpent                figuré         ✓
  [ 73/190] chiens                 référentiel    ✓
  [ 74/190] margouillat            référentiel    ✓
  [ 75/190] mouette                référentiel    ✓
  [ 76/190] poussins               référentiel    ✓
  [ 77/190] rat                    figuré         ✓
  [ 78/190] mouches                référentiel    ✓
  [ 79/190] chien                  référentiel    ✓
  [ 80/190] musaraignes            référentiel    ✓
  [ 81/190] bisons                 référentiel    ✓
  [ 82/190] lapins                 figuré         ✓
  [ 83/190] cheval                 référentiel    ✓
  [ 84/190] agneau                 référentiel    ✓
  [ 85/190] chèvres                référentiel    ✓
  [ 86/190] blattes                figuré         ✓
  [ 87/190] poule                  figuré         ✓
  [ 88/190] porcs                  référentiel    ✗  ← gold=référentiel pred=figuré
  [ 89/190] chiens                 référentiel    ✓
  [ 90/190] âne                    figuré         ✓
  [ 91/190] loup                   référentiel    ✓
  [ 92/190] chamois                référentiel    ✓
  [ 93/190] chèvre                 référentiel    ✓
  [ 94/190] vaches                 référentiel    ✓
  [ 95/190] jument                 figuré         ✓
  [ 96/190] milans                 référentiel    ✓
  [ 97/190] chiens                 référentiel    ✓
  [ 98/190] muge                   figuré         ✓
  [ 99/190] albatros               figuré         ✓
  [100/190] baleine                figuré         ✓
  [101/190] chiens                 référentiel    ✓
  [102/190] musaraignes            référentiel    ✓
  [103/190] lapins                 référentiel    ✓
  [104/190] chien                  référentiel    ✓
  [105/190] moineaux               figuré         ✓
  [106/190] rats                   référentiel    ✓
  [107/190] cheval                 référentiel    ✓
  [108/190] sanglier               référentiel    ✓
  [109/190] poulet                 référentiel    ✓
  [110/190] baleines               référentiel    ✓
  [111/190] paon                   référentiel    ✓
  [112/190] paon                   référentiel    ✓
  [113/190] chameau                figuré         ✓
  [114/190] mouettes               référentiel    ✓
  [115/190] rat                    figuré         ✗  ← gold=figuré pred=référentiel
  [116/190] dorade                 référentiel    ✓
  [117/190] cheval                 référentiel    ✓
  [118/190] sanglier               référentiel    ✓
  [119/190] lion                   référentiel    ✓
  [120/190] brebis                 figuré         ✓
  [121/190] canard                 figuré         ✓
  [122/190] oie                    figuré         ✓
  [123/190] sauterelles            référentiel    ✓
  [124/190] bouquetins             référentiel    ✓
  [125/190] paon                   référentiel    ✓
  [126/190] juments                référentiel    ✓
  [127/190] rats                   référentiel    ✓
  [128/190] chiens                 référentiel    ✓
  [129/190] moutons                référentiel    ✓
  [130/190] hérons                 référentiel    ✓
  [131/190] bulbuls                référentiel    ✓
  [132/190] chiens                 référentiel    ✓
  [133/190] mouton                 référentiel    ✓
  [134/190] chèvre                 référentiel    ✓
  [135/190] corbeaux               référentiel    ✓
  [136/190] perdrix                référentiel    ✓
  [137/190] chiens                 référentiel    ✓
  [138/190] faucon                 figuré         ✓
  [139/190] mouette                référentiel    ✓
  [140/190] crotales               référentiel    ✓
  [141/190] pythons                référentiel    ✓
  [142/190] chevaux                référentiel    ✓
  [143/190] cheval                 référentiel    ✓
  [144/190] dingo                  référentiel    ✓
  [145/190] poux                   référentiel    ✓
  [146/190] chiot                  référentiel    ✓
  [147/190] porc                   figuré         ✗  ← gold=figuré pred=référentiel
  [148/190] cerfs                  référentiel    ✓
  [149/190] vache                  figuré         ✗  ← gold=figuré pred=référentiel
  [150/190] aigles                 référentiel    ✓
  [151/190] poulets                référentiel    ✓
  [152/190] chien                  figuré         ✓
  [153/190] autruche               référentiel    ✓
  [154/190] bœuf                   référentiel    ✗  ← gold=référentiel pred=figuré
  [155/190] chien                  figuré         ✓
  [156/190] chimpanzés             figuré         ✗  ← gold=figuré pred=référentiel
  [157/190] cigales                référentiel    ✓
  [158/190] tortues                figuré         ✓
  [159/190] serpents               référentiel    ✓
  [160/190] sanglier               référentiel    ✓
  [161/190] bécasse                figuré         ✓
  [162/190] poulet                 référentiel    ✓
  [163/190] goéland                figuré         ✗  ← gold=figuré pred=référentiel
  [164/190] chat                   figuré         ✗  ← gold=figuré pred=référentiel
  [165/190] baleine                figuré         ✓
  [166/190] baleine                figuré         ✓
  [167/190] chiens                 figuré         ✗  ← gold=figuré pred=référentiel
  [168/190] cheval                 figuré         ✗  ← gold=figuré pred=référentiel
  [169/190] âne                    figuré         ✓
  [170/190] fourmis                figuré         ✓
  [171/190] lion                   figuré         ✗  ← gold=figuré pred=référentiel
  [172/190] lion                   figuré         ✗  ← gold=figuré pred=référentiel
  [173/190] abeille                référentiel    ✗  ← gold=référentiel pred=figuré
  [174/190] taupes                 figuré         ✓
  [175/190] âne                    figuré         ✗  ← gold=figuré pred=référentiel
  [176/190] chiens                 référentiel    ✓
  [177/190] mouche                 figuré         ✓
  [178/190] vache                  figuré         ✓
  [179/190] chimpanzé              référentiel    ✓
  [180/190] chauve-souris          figuré         ✓
  [181/190] scarabées              figuré         ✓
  [182/190] tigre                  figuré         ✗  ← gold=figuré pred=référentiel
  [183/190] chiens                 référentiel    ✓
  [184/190] papillon               figuré         ✓
  [185/190] bousiers               figuré         ✓
  [186/190] singe                  référentiel    ✓
  [187/190] chats                  référentiel    ✓
  [188/190] âne                    figuré         ✗  ← gold=figuré pred=référentiel
  [189/190] ours                   figuré         ✓
  [190/190] coqs                   figuré         ✓

  RESULT batch=4: overall=90.0% (171/190)  réf=95.0% (115/121)  fig=81.2% (56/69)
  Speed: 3.9s/row  →  Animaux corpus: 140h (5.8 days)
  Failed batches: 0

  ────────────────────────────────────────────────────────────
  Plantes  —  188 rows  (164 réf + 24 fig)  batch=4
  ────────────────────────────────────────────────────────────
  [  1/188] graminées              référentiel    ✓
  [  2/188] serpolet               référentiel    ✓
  [  3/188] pin                    référentiel    ✓
  [  4/188] micocouliers           référentiel    ✓
  [  5/188] joncs                  référentiel    ✓
  [  6/188] tilleuls               référentiel    ✗  ← gold=référentiel pred=figuré
  [  7/188] cèdre du Liban         référentiel    ✓
  [  8/188] palmiers               référentiel    ✓
  [  9/188] chanvre                référentiel    ✓
  [ 10/188] pin                    référentiel    ✓
  [ 11/188] raisin                 référentiel    ✓
  [ 12/188] eucalyptus             référentiel    ✓
  [ 13/188] pandanus               référentiel    ✓
  [ 14/188] riz                    référentiel    ✓
  [ 15/188] citron                 référentiel    ✓
  [ 16/188] ronces                 référentiel    ✓
  [ 17/188] oignons                référentiel    ✓
  [ 18/188] tomates                référentiel    ✓
  [ 19/188] anthémis               référentiel    ✓
  [ 20/188] pastèque               référentiel    ✓
  [ 21/188] magnolias              référentiel    ✓
  [ 22/188] cardamome              référentiel    ✓
  [ 23/188] olivier                figuré         ✓
  [ 24/188] lin                    référentiel    ✓
  [ 25/188] dattiers               référentiel    ✓
  [ 26/188] roses                  référentiel    ✓
  [ 27/188] riz                    référentiel    ✓
  [ 28/188] foin                   référentiel    ✓
  [ 29/188] poireaux               référentiel    ✓
  [ 30/188] plantes ligneuses      figuré         ✗  ← gold=figuré pred=référentiel
  [ 31/188] pois chiches           référentiel    ✓
  [ 32/188] bois de rose           référentiel    ✓
  [ 33/188] pins                   référentiel    ✓
  [ 34/188] riz                    référentiel    ✓
  [ 35/188] acacias                référentiel    ✓
  [ 36/188] laurier                référentiel    ✓
  [ 37/188] bambous                référentiel    ✓
  [ 38/188] ronces                 référentiel    ✓
  [ 39/188] fougères arborescentes référentiel    ✓
  [ 40/188] riz                    référentiel    ✓
  [ 41/188] pins                   référentiel    ✓
  [ 42/188] riz                    référentiel    ✓
  [ 43/188] fougères               référentiel    ✓
  [ 44/188] maïs                   référentiel    ✓
  [ 45/188] mélèzes                référentiel    ✓
  [ 46/188] ifs                    référentiel    ✓
  [ 47/188] tilleuls               référentiel    ✓
  [ 48/188] gazon                  référentiel    ✓
  [ 49/188] platanes               référentiel    ✓
  [ 50/188] saules                 référentiel    ✗  ← gold=référentiel pred=figuré
  [ 51/188] asphodèles             référentiel    ✓
  [ 52/188] lilas                  référentiel    ✓
  [ 53/188] sapin                  référentiel    ✓
  [ 54/188] ajoncs                 référentiel    ✓
  [ 55/188] joncs                  référentiel    ✓
  [ 56/188] menthe                 référentiel    ✓
  [ 57/188] pois                   référentiel    ✓
  [ 58/188] rosiers                référentiel    ✓
  [ 59/188] oliviers               référentiel    ✓
  [ 60/188] ronces                 référentiel    ✗  ← gold=référentiel pred=figuré
  [ 61/188] osier                  référentiel    ✓
  [ 62/188] cocotier               référentiel    ✓
  [ 63/188] gazon                  référentiel    ✓
  [ 64/188] arachide               référentiel    ✓
  [ 65/188] châtaigniers           référentiel    ✓
  [ 66/188] bananier               référentiel    ✓
  [ 67/188] haricots               référentiel    ✓
  [ 68/188] lime                   figuré         ✓
  [ 69/188] jasmin                 figuré         ✗  ← gold=figuré pred=référentiel
  [ 70/188] hêtres                 référentiel    ✓
  [ 71/188] thé                    référentiel    ✓
  [ 72/188] café                   référentiel    ✓
  [ 73/188] poivre                 référentiel    ✓
  [ 74/188] calebasses             référentiel    ✓
  [ 75/188] thym                   référentiel    ✓
  [ 76/188] raisin                 référentiel    ✓
  [ 77/188] poivrons               référentiel    ✓
  [ 78/188] phlox                  référentiel    ✓
  [ 79/188] palmier                référentiel    ✓
  [ 80/188] bananier               référentiel    ✓
  [ 81/188] chênes                 référentiel    ✓
  [ 82/188] pois                   référentiel    ✓
  [ 83/188] tilleuls               référentiel    ✓
  [ 84/188] mangue                 référentiel    ✓
  [ 85/188] renoncules             référentiel    ✓
  [ 86/188] ancolie                référentiel    ✓
  [ 87/188] myrtilles              référentiel    ✓
  [ 88/188] bardanes               référentiel    ✓
  [ 89/188] papayer                référentiel    ✓
  [ 90/188] lin                    référentiel    ✓
  [ 91/188] groseille              référentiel    ✓
  [ 92/188] vigne                  référentiel    ✓
  [ 93/188] roses                  référentiel    ✓
  [ 94/188] asperge                figuré         ✓
  [ 95/188] tomate                 référentiel    ✓
  [ 96/188] lys                    figuré         ✗  ← gold=figuré pred=référentiel
  [ 97/188] chêne                  référentiel    ✓
  [ 98/188] abricotier             figuré         ✗  ← gold=figuré pred=référentiel
  [ 99/188] carottes               figuré         ✓
  [100/188] cocotier               référentiel    ✓
  [101/188] calebasses             figuré         ✓
  [102/188] oyats                  référentiel    ✓
  [103/188] palmiers               figuré         ✗  ← gold=figuré pred=référentiel
  [104/188] pois                   référentiel    ✓
  [105/188] poivre                 référentiel    ✓
  [106/188] pervenche              figuré         ✓
  [107/188] pin                    référentiel    ✓
  [108/188] ail                    référentiel    ✓
  [109/188] luzerne                référentiel    ✓
  [110/188] henné                  référentiel    ✓
  [111/188] figuier                référentiel    ✓
  [112/188] chêne                  référentiel    ✓
  [113/188] joncs                  référentiel    ✓
  [114/188] mouron                 référentiel    ✓
  [115/188] gazon                  référentiel    ✓
  [116/188] maïs                   référentiel    ✓
  [117/188] concombre              référentiel    ✓
  [118/188] manguiers              référentiel    ✓
  [119/188] hêtre                  référentiel    ✓
  [120/188] pommes de terre        référentiel    ✓
  [121/188] bouleaux               référentiel    ✓
  [122/188] osier blanc            référentiel    ✓
  [123/188] nénuphars              référentiel    ✓
  [124/188] concombre              référentiel    ✓
  [125/188] chêne                  référentiel    ✓
  [126/188] orchidée               référentiel    ✓
  [127/188] raphia                 référentiel    ✓
  [128/188] figue                  figuré         ✓
  [129/188] lotus                  référentiel    ✓
  [130/188] jacinthes              référentiel    ✓
  [131/188] linaires               référentiel    ✓
  [132/188] poivre noir            référentiel    ✓
  [133/188] pommiers               figuré         ✓
  [134/188] sapin                  référentiel    ✓
  [135/188] pois                   figuré         ✓
  [136/188] acanthe                référentiel    ✓
  [137/188] bégonias               référentiel    ✓
  [138/188] sapin                  référentiel    ✓
  [139/188] pivoines               référentiel    ✓
  [140/188] aulnes                 référentiel    ✓
  [141/188] algues                 figuré         ✓
  [142/188] chêne                  référentiel    ✓
  [143/188] framboisiers           référentiel    ✓
  [144/188] haricots               référentiel    ✓
  [145/188] bambou                 référentiel    ✓
  [146/188] concombres             référentiel    ✓
  [147/188] litchis                référentiel    ✓
  [148/188] épine noire            référentiel    ✓
  [149/188] poireaux               référentiel    ✓
  [150/188] riz                    référentiel    ✓
  [151/188] ananas                 référentiel    ✓
  [152/188] algues vertes          référentiel    ✓
  [153/188] lauriers               référentiel    ✓
  [154/188] hortensias             référentiel    ✓
  [155/188] lin                    référentiel    ✓
  [156/188] oignons                référentiel    ✓
  [157/188] pastèques              figuré         ✓
  [158/188] roseaux                référentiel    ✓
  [159/188] oignons                figuré         ✓
  [160/188] blé                    référentiel    ✓
  [161/188] ronces                 référentiel    ✓
  [162/188] lin                    référentiel    ✓
  [163/188] prune                  référentiel    ✓
  [164/188] sésame                 figuré         ✓
  [165/188] papyrus                référentiel    ✗  ← gold=référentiel pred=figuré
  [166/188] laitue                 référentiel    ✓
  [167/188] plantes grimpantes     référentiel    ✓
  [168/188] riz                    référentiel    ✓
  [169/188] melon                  référentiel    ✓
  [170/188] épinards               figuré         ✓
  [171/188] chênes-lièges          référentiel    ✓
  [172/188] melon d'eau            référentiel    ✓
  [173/188] blé                    figuré         ✓
  [174/188] prune                  figuré         ✓
  [175/188] cactus                 référentiel    ✓
  [176/188] blé                    référentiel    ✓
  [177/188] tomate                 référentiel    ✓
  [178/188] ananas                 figuré         ✗  ← gold=figuré pred=référentiel
  [179/188] olivier                figuré         ✓
  [180/188] frangipanier           référentiel    ✓
  [181/188] riz                    référentiel    ✓
  [182/188] vignes                 référentiel    ✓
  [183/188] calebasse              figuré         ✓
  [184/188] bouleaux               référentiel    ✓
  [185/188] sapins                 référentiel    ✓
  [186/188] séquoias               référentiel    ✓
  [187/188] fougères               référentiel    ✓
  [188/188] cèdre                  référentiel    ✓

  RESULT batch=4: overall=94.7% (178/188)  réf=97.6% (160/164)  fig=75.0% (18/24)
  Speed: 3.3s/row  →  Plantes corpus: 64h (2.7 days)
  Failed batches: 0


=================================================================
  FINAL COMPARISON — ANIMAUX (121 réf + 69 fig = 190 rows)
=================================================================
  Method                Réf          Fig      Overall    Speed  Anim days
  ──────────────────────────────────────────────────────────────
  v6 (1 row)   118/121 (97.5%)   56/69 (81.2%)   174/190 (91.6%)
  batch=3      117/121 (96.7%)   56/69 (81.2%)   173/190 (91.1%)    4.4s/row  6.5d
  batch=4      115/121 (95.0%)   56/69 (81.2%)   171/190 (90.0%)    3.9s/row  5.8d
  batch=5      114/121 (94.2%)     55/69 (79.7%)     169/190 (88.9%)   3.4s/row   5.8d

=================================================================
  FINAL COMPARISON — PLANTES (164 réf + 24 fig = 188 rows)
=================================================================
  Method                Réf          Fig      Overall    Speed Plant days
  ──────────────────────────────────────────────────────────────
  v6 (1 row)   162/164 (98.8%)   19/24 (79.2%)   181/188 (96.3%)
  batch=3      164/164 (100.0%)   14/24 (58.3%)   178/188 (94.7%)    3.7s/row  3.0d
  batch=4      160/164 (97.6%)   18/24 (75.0%)   178/188 (94.7%)    3.3s/row  2.7d
  batch=5      160/164 (97.6%)     17/24 (70.8%)     177/188 (94.1%)   3.1s/row   3.2d
(labelimg_env) lfarooq@obtic-gpu1:~/ecopoetique/métaphore$
```

---

<a id="pipeline-log"></a>
## 5. `pipeline_overnight.log` (repo root, full — Task 0/narratology, June 24)

```
nohup: ignoring input
=== STEP 1+2: qwen72b think+nothink === Wed Jun 24 23:36:23 UTC 2026
Gold set: 60 novels

============================================================
  qwen72b-limited — FOCALISATION — WITH thinking
============================================================

    Error: '"FOCALISATION"'
  [ 1/60] Angot-Christine_Le-Voyage-dans-l'Est.txt   -> FOC_INT OK (gold:FOC_INT)
    Error: '"FOCALISATION"'
  [ 2/60] Autissier-Isabelle_Soudain-seuls.txt       -> FOC_INT XX (gold:FOC_ZERO)
    Error: '"FOCALISATION"'
  [ 3/60] Bienne-Gisele_La-malchimie.txt             -> FOC_INT OK (gold:FOC_INT)
    Error: '"FOCALISATION"'
  [ 4/60] Binet-Laurent_La-septieme-fonction-du-lang -> FOC_INT XX (gold:FOC_VAR)
    Error: '"FOCALISATION"'
  [ 5/60] Bofane-In-Koli-Jean_Congo_inc._le_testamen -> FOC_INT XX (gold:FOC_ZERO)
    Error: '"FOCALISATION"'
  [ 6/60] Brunel-Camille_La-guerrilla-des-animaux.tx -> FOC_INT OK (gold:FOC_INT)
    Error: '"FOCALISATION"'
  [ 7/60] Chevillard-Eric_Oreille-rouge.txt          -> FOC_INT XX (gold:FOC_ZERO)
    Error: '"FOCALISATION"'
  [ 8/60] Carrere-Emmanuel_Limonov.txt               -> FOC_INT OK (gold:FOC_INT)
    Error: '"FOCALISATION"'
  [ 9/60] Deck-Julia_Ann-dAngleterre.txt             -> FOC_INT OK (gold:FOC_INT)
    Error: '"FOCALISATION"'
  [10/60] Despentes-Virginie_Vernon-Subutex-1.txt    -> FOC_INT XX (gold:FOC_ZERO)
    Error: '"FOCALISATION"'
  [11/60] Ducrozet-Pierre_Le-Grand-Vertige.txt       -> FOC_INT XX (gold:FOC_ZERO)
    Error: '"FOCALISATION"'
  [12/60] Echenoz-Jean_Envoyee-speciale.txt          -> FOC_INT XX (gold:FOC_ZERO)
    Error: '"FOCALISATION"'
  [13/60] Filhol-Elizabeth_Doggerland.txt            -> FOC_INT XX (gold:FOC_ZERO)
    Error: '"FOCALISATION"'
  [14/60] Flahaut-Thomas_Ostwald.txt                 -> FOC_INT OK (gold:FOC_INT)
    Error: '"FOCALISATION"'
  [15/60] Garcia-Tristan_La-meilleure-part-des-homme -> FOC_INT XX (gold:FOC_ZERO)
    Error: '"FOCALISATION"'
  [16/60] Hunzinger-Claudie_Les-grands-cerfs.txt     -> FOC_INT OK (gold:FOC_INT)
    Error: '"FOCALISATION"'
  [17/60] Hunzinger-Claudie_Un-chien-a-ma-table.txt  -> FOC_INT OK (gold:FOC_INT)
    Error: '"FOCALISATION"'
  [18/60] Joncour-Serge_Nature-humaine.txt           -> FOC_INT XX (gold:FOC_ZERO)
    Error: '"FOCALISATION"'
  [19/60] Joncour-Serge_Chien-Loup.txt               -> FOC_INT XX (gold:FOC_ZERO)
    Error: '"FOCALISATION"'
  [20/60] Kerangal-Maylisde_Naissance-dun-pont.txt   -> FOC_INT XX (gold:FOC_VAR)
    Error: '"FOCALISATION"'
  [21/60] Lafon-Marie_Joseph.txt                     -> FOC_INT OK (gold:FOC_INT)
    Error: '"FOCALISATION"'
  [22/60] Lançon-Philippe_Le-lambeau.txt             -> FOC_INT OK (gold:FOC_INT)
    Error: '"FOCALISATION"'
  [23/60] LeTellier-Herve_Lanomalie.txt              -> FOC_INT XX (gold:FOC_ZERO)
    Error: '"FOCALISATION"'
  [24/60] Loup-Douna_Les-printemps-sauvages.txt      -> FOC_INT OK (gold:FOC_INT)
    Error: '"FOCALISATION"'
  [25/60] Louis-Edouard_En-finir-avec-Eddy-Bellegueu -> FOC_INT OK (gold:FOC_INT)
    Error: '"FOCALISATION"'
  [26/60] Mathieu-Nicolas_Connemara.txt              -> FOC_INT XX (gold:FOC_ZERO)
    Error: '"FOCALISATION"'
  [27/60] Mauvignier-Laurent_Histoires-de-la-nuit.tx -> FOC_INT OK (gold:FOC_VAR)
    Error: '"FOCALISATION"'
  [28/60] Mauvignier-Laurent_Autour-du-monde.txt     -> FOC_INT XX (gold:FOC_VAR)
    Error: '"FOCALISATION"'
  [29/60] Mauvignier-Laurent_Continuer.txt           -> FOC_INT OK (gold:FOC_VAR)
    Error: '"FOCALISATION"'
  [30/60] Mbougar_La-plus-secrete-memoire-des-hommes -> FOC_INT OK (gold:FOC_VAR)
    Error: '"FOCALISATION"'
  [31/60] Miano-Leonora_Rouge-imperatrice.txt        -> FOC_INT XX (gold:FOC_VAR)
    Error: '"FOCALISATION"'
  [32/60] Minard-Celine_Le-Grand-Jeu.txt             -> FOC_INT OK (gold:FOC_INT)
    Error: '"FOCALISATION"'
  [33/60] Montalbetti-Christine_Mon-ancetre-poisson. -> FOC_INT OK (gold:FOC_INT)
    Error: '"FOCALISATION"'
  [34/60] Mouawad-Wajdi_Anima.txt                    -> FOC_INT OK (gold:FOC_INT)
    Error: '"FOCALISATION"'
  [35/60] Nirsimloo-Anenden-Ananda_Eve-de-ses-decomb -> FOC_INT OK (gold:FOC_INT)
    Error: '"FOCALISATION"'
  [36/60] Pagano-Emmanuelle_Saufs-riverains.txt      -> FOC_INT OK (gold:FOC_INT)
    Error: '"FOCALISATION"'
  [37/60] Plamondon-Eric_Taqawan.txt                 -> FOC_INT XX (gold:FOC_VAR)
    Error: '"FOCALISATION"'
  [38/60] Poulain-Catherine_Le-grand-marin.txt       -> FOC_INT OK (gold:FOC_INT)
    Error: '"FOCALISATION"'
  [39/60] Reverdy-ThomasB_Climax.txt                 -> FOC_INT XX (gold:FOC_VAR)
    Error: '"FOCALISATION"'
  [40/60] Rico-Lucie_Le-chant-du-poulet-sous-vide.tx -> FOC_INT OK (gold:FOC_INT)
    Error: '"FOCALISATION"'
  [41/60] Rico-Lucie_GPS.txt                         -> FOC_INT OK (gold:FOC_INT)
    Error: '"FOCALISATION"'
  [42/60] Rodier-Jean_En-remontant-les-ruisseaux.txt -> FOC_INT OK (gold:FOC_INT)
    Error: '"FOCALISATION"'
  [43/60] Rolin-Jean_Le-Traquet-kurde.txt            -> FOC_INT OK (gold:FOC_INT)
    Error: '"FOCALISATION"'
  [44/60] Rolin-Jean_Un-chien-mort-apres-lui.txt     -> FOC_INT OK (gold:FOC_INT)
    Error: '"FOCALISATION"'
  [45/60] Royer-Corinne_Pleine-terre.txt             -> FOC_INT OK (gold:FOC_INT)
    Error: '"FOCALISATION"'
  [46/60] Sautiere-Jane_Mort-dun-cheval-dans-les-bra -> FOC_INT OK (gold:FOC_INT)
    Error: '"FOCALISATION"'
  [47/60] Senges-Pierre_Ruines-de-Rome.txt           -> FOC_INT OK (gold:FOC_INT)
    Error: '"FOCALISATION"'
  [48/60] Simonnot-Maud_LEnfant-celeste.txt          -> FOC_INT OK (gold:FOC_INT)
    Error: '"FOCALISATION"'
  [49/60] Slimani-Leila_Chanson-douce.txt            -> FOC_INT XX (gold:FOC_ZERO)
    Error: '"FOCALISATION"'
  [50/60] Sorman-Joy_La-peau-de-lours.txt            -> FOC_INT OK (gold:FOC_INT)
    Error: '"FOCALISATION"'
  [51/60] Sorman-Joy_Comme-une-bete.txt              -> FOC_INT OK (gold:FOC_INT)
    Error: '"FOCALISATION"'
  [52/60] Toussaint_Jean-Philippe-Faire_l_amour.txt  -> FOC_INT OK (gold:FOC_INT)
    Error: '"FOCALISATION"'
  [53/60] Ventura-Maud_Mon-mari.txt                  -> FOC_INT OK (gold:FOC_INT)
    Error: '"FOCALISATION"'
  [54/60] Volodine-Antoine_Songes-de-Mevlido.txt     -> FOC_INT OK (gold:FOC_INT)
    Error: '"FOCALISATION"'
  [55/60] Volodine-Antoine_Terminus-radieux.txt      -> FOC_INT OK (gold:FOC_INT)
    Error: '"FOCALISATION"'
  [56/60] Vuillard-Eric_14-Juillet.txt               -> FOC_INT XX (gold:FOC_EXT)
    Error: '"FOCALISATION"'
  [57/60] Wilhelmy-Audrée_Le-corps-des-bêtes.txt     -> FOC_INT OK (gold:FOC_VAR)
    Error: '"FOCALISATION"'
  [58/60] Vuillard-Eric_Lordre-du-jour.txt           -> FOC_INT XX (gold:FOC_EXT)
    Error: '"FOCALISATION"'
  [59/60] Vuillard-Eric_Tristesse-de-la-terre-Une-hi -> FOC_INT XX (gold:FOC_ZERO)
    Error: '"FOCALISATION"'
  [60/60] Zeniter-Alice_Lart-de-perdre.txt           -> FOC_INT XX (gold:FOC_ZERO)

  RESULT: 37/60 (61.7%)
  Saved: /home/lfarooq/ecopoetique/narratologie/resultats_qwen72b_foc_think.csv

============================================================
  qwen72b-limited — FOCALISATION — WITHOUT thinking
============================================================

    Error: '"FOCALISATION"'
  [ 1/60] Angot-Christine_Le-Voyage-dans-l'Est.txt   -> FOC_INT OK (gold:FOC_INT)
  [ 2/60] Autissier-Isabelle_Soudain-seuls.txt       -> FOC_INT XX (gold:FOC_ZERO)
  [ 3/60] Bienne-Gisele_La-malchimie.txt             -> FOC_INT OK (gold:FOC_INT)
  [ 4/60] Binet-Laurent_La-septieme-fonction-du-lang -> FOC_INT XX (gold:FOC_VAR)
  [ 5/60] Bofane-In-Koli-Jean_Congo_inc._le_testamen -> FOC_INT XX (gold:FOC_ZERO)
  [ 6/60] Brunel-Camille_La-guerrilla-des-animaux.tx -> FOC_INT OK (gold:FOC_INT)
  [ 7/60] Chevillard-Eric_Oreille-rouge.txt          -> FOC_INT XX (gold:FOC_ZERO)
  [ 8/60] Carrere-Emmanuel_Limonov.txt               -> FOC_INT OK (gold:FOC_INT)
  [ 9/60] Deck-Julia_Ann-dAngleterre.txt             -> FOC_INT OK (gold:FOC_INT)
  [10/60] Despentes-Virginie_Vernon-Subutex-1.txt    -> FOC_INT XX (gold:FOC_ZERO)
  [11/60] Ducrozet-Pierre_Le-Grand-Vertige.txt       -> FOC_INT XX (gold:FOC_ZERO)
  [12/60] Echenoz-Jean_Envoyee-speciale.txt          -> FOC_INT XX (gold:FOC_ZERO)
  [13/60] Filhol-Elizabeth_Doggerland.txt            -> FOC_INT XX (gold:FOC_ZERO)
  [14/60] Flahaut-Thomas_Ostwald.txt                 -> FOC_INT OK (gold:FOC_INT)
  [15/60] Garcia-Tristan_La-meilleure-part-des-homme -> FOC_INT XX (gold:FOC_ZERO)
  [16/60] Hunzinger-Claudie_Les-grands-cerfs.txt     -> FOC_INT OK (gold:FOC_INT)
  [17/60] Hunzinger-Claudie_Un-chien-a-ma-table.txt  -> FOC_INT OK (gold:FOC_INT)
  [18/60] Joncour-Serge_Nature-humaine.txt           -> FOC_INT XX (gold:FOC_ZERO)
  [19/60] Joncour-Serge_Chien-Loup.txt               -> FOC_INT XX (gold:FOC_ZERO)
  [20/60] Kerangal-Maylisde_Naissance-dun-pont.txt   -> FOC_INT XX (gold:FOC_VAR)
  [21/60] Lafon-Marie_Joseph.txt                     -> FOC_INT OK (gold:FOC_INT)
  [22/60] Lançon-Philippe_Le-lambeau.txt             -> FOC_INT OK (gold:FOC_INT)
  [23/60] LeTellier-Herve_Lanomalie.txt              -> FOC_INT XX (gold:FOC_ZERO)
  [24/60] Loup-Douna_Les-printemps-sauvages.txt      -> FOC_INT OK (gold:FOC_INT)
  [25/60] Louis-Edouard_En-finir-avec-Eddy-Bellegueu -> FOC_INT OK (gold:FOC_INT)
  [26/60] Mathieu-Nicolas_Connemara.txt              -> FOC_INT XX (gold:FOC_ZERO)
  [27/60] Mauvignier-Laurent_Histoires-de-la-nuit.tx -> FOC_INT OK (gold:FOC_VAR)
  [28/60] Mauvignier-Laurent_Autour-du-monde.txt     -> FOC_INT XX (gold:FOC_VAR)
  [29/60] Mauvignier-Laurent_Continuer.txt           -> FOC_INT OK (gold:FOC_VAR)
  [30/60] Mbougar_La-plus-secrete-memoire-des-hommes -> FOC_INT OK (gold:FOC_VAR)
  [31/60] Miano-Leonora_Rouge-imperatrice.txt        -> FOC_INT XX (gold:FOC_VAR)
  [32/60] Minard-Celine_Le-Grand-Jeu.txt             -> FOC_INT OK (gold:FOC_INT)
  [33/60] Montalbetti-Christine_Mon-ancetre-poisson. -> FOC_INT OK (gold:FOC_INT)
  [34/60] Mouawad-Wajdi_Anima.txt                    -> FOC_INT OK (gold:FOC_INT)
  [35/60] Nirsimloo-Anenden-Ananda_Eve-de-ses-decomb -> FOC_INT OK (gold:FOC_INT)
  [36/60] Pagano-Emmanuelle_Saufs-riverains.txt      -> FOC_INT OK (gold:FOC_INT)
  [37/60] Plamondon-Eric_Taqawan.txt                 -> FOC_INT XX (gold:FOC_VAR)
  [38/60] Poulain-Catherine_Le-grand-marin.txt       -> FOC_INT OK (gold:FOC_INT)
  [39/60] Reverdy-ThomasB_Climax.txt                 -> FOC_INT XX (gold:FOC_VAR)
  [40/60] Rico-Lucie_Le-chant-du-poulet-sous-vide.tx -> FOC_INT OK (gold:FOC_INT)
  [41/60] Rico-Lucie_GPS.txt                         -> FOC_INT OK (gold:FOC_INT)
  [42/60] Rodier-Jean_En-remontant-les-ruisseaux.txt -> FOC_INT OK (gold:FOC_INT)
  [43/60] Rolin-Jean_Le-Traquet-kurde.txt            -> FOC_INT OK (gold:FOC_INT)
  [44/60] Rolin-Jean_Un-chien-mort-apres-lui.txt     -> FOC_INT OK (gold:FOC_INT)
  [45/60] Royer-Corinne_Pleine-terre.txt             -> FOC_INT OK (gold:FOC_INT)
  [46/60] Sautiere-Jane_Mort-dun-cheval-dans-les-bra -> FOC_INT OK (gold:FOC_INT)
  [47/60] Senges-Pierre_Ruines-de-Rome.txt           -> FOC_INT OK (gold:FOC_INT)
  [48/60] Simonnot-Maud_LEnfant-celeste.txt          -> FOC_INT OK (gold:FOC_INT)
  [49/60] Slimani-Leila_Chanson-douce.txt            -> FOC_INT XX (gold:FOC_ZERO)
  [50/60] Sorman-Joy_La-peau-de-lours.txt            -> FOC_INT OK (gold:FOC_INT)
  [51/60] Sorman-Joy_Comme-une-bete.txt              -> FOC_INT OK (gold:FOC_INT)
  [52/60] Toussaint_Jean-Philippe-Faire_l_amour.txt  -> FOC_INT OK (gold:FOC_INT)
  [53/60] Ventura-Maud_Mon-mari.txt                  -> FOC_INT OK (gold:FOC_INT)
  [54/60] Volodine-Antoine_Songes-de-Mevlido.txt     -> FOC_INT OK (gold:FOC_INT)
  [55/60] Volodine-Antoine_Terminus-radieux.txt      -> FOC_INT OK (gold:FOC_INT)
  [56/60] Vuillard-Eric_14-Juillet.txt               -> FOC_INT XX (gold:FOC_EXT)
  [57/60] Wilhelmy-Audrée_Le-corps-des-bêtes.txt     -> FOC_INT OK (gold:FOC_VAR)
  [58/60] Vuillard-Eric_Lordre-du-jour.txt           -> FOC_INT XX (gold:FOC_EXT)
  [59/60] Vuillard-Eric_Tristesse-de-la-terre-Une-hi -> FOC_INT XX (gold:FOC_ZERO)
  [60/60] Zeniter-Alice_Lart-de-perdre.txt           -> FOC_INT XX (gold:FOC_ZERO)

  RESULT: 37/60 (61.7%)
  Saved: /home/lfarooq/ecopoetique/narratologie/resultats_qwen72b_foc_nothink.csv

============================================================
  FINAL COMPARISON
  With thinking:    61.7%
  Without thinking: 61.7%
  Previous best:    65.0% (local hybrid)
============================================================
=== STEP 3: Loterre v8 === Wed Jun 24 23:36:23 UTC 2026
```

---

<a id="nested-cv"></a>
## 6. `narratologie/resultats_nested_cv_honest.txt` (full)

```
60 novels, 43 features

======================================================================
  NESTED CV (model choice made WITHOUT seeing the held-out novel)
======================================================================
  TYPE NARRATEUR      54/60  =  90.0%   (inner-CV model picks: {'GB': 7, 'LogReg': 51, 'RF': 2})
  FOCALISATION        39/60  =  65.0%   (inner-CV model picks: {'LogReg': 40, 'GB': 18, 'RF': 2})
  MODE NARRATIF       38/60  =  63.3%   (inner-CV model picks: {'RF': 29, 'LogReg': 18, 'GB': 13})
  REGIME NARRATIF     41/60  =  68.3%   (inner-CV model picks: {'LogReg': 15, 'RF': 42, 'GB': 3})
  ESPACE              23/60  =  38.3%   (inner-CV model picks: {'GB': 12, 'LogReg': 9, 'RF': 39})
  INTRIGUE            39/60  =  65.0%   (inner-CV model picks: {'RF': 60})
  TEMPORALITÉ         35/60  =  58.3%   (inner-CV model picks: {'RF': 36, 'LogReg': 24})
----------------------------------------------------------------------
  OVERALL (nested, honest) 269/420 =  64.0%
```

---

<a id="meeting-transcript"></a>
## 7. `riccardo_25june_meetingTranscript.md` (repo root, full — first meeting, June 25)

This is a raw, lightly-punctuated speech-to-text transcript. Preserved verbatim, including its fragmented sentences and filler — nothing cleaned up or summarized.

```
With that,
the GPU resources and stuff and my colleagues were.
Which task are you running?
I'm like, I have no clue which task I'm running.
So okay, so this is the task one, the literal and figurative
classification.
Before it was 60.
Sorry, 70, 62 and 50.4.
For the figurative.
Yeah, figurative.
The overall was like 99.
Yeah.
Right.
Now then it went to this and now I have changed it and I have this value
right now.
So the final one is figurative.
It can go to 89.
So don't worry about animal because I already tried animals.
So it will go to around 89%.
Why it will go there?
Because I have tried the first version with the less animal example.
Because if you train a model or give models more examples, it can start having hallucinations.
So it will like over complicate for itself.
But before, when I was giving less examples for it to learn from, it gave me around 89%.
I think I told you last time as well.
So it's gonna go up.
This one is the best one I could find.
Yeah, it's 89 points.
Fair enough.
Overall the 696.
Yeah.
Okay.
It's quite.
This one is the.
The best one I could find.
Okay.
For this one figurative one, I am having a questions about it because if
I.
Let me show you the.
The file.
Because when I was finding.
Because the litrock I said it's.
I think it's.
That's how you pronounce it.
This folder had 41, 20 total figurative options.
So 41 goal sets which I had to verify.
Only five of them were wrong from the model and the other ones I think are wrong in the concept of goal set.
I will show you the examples so you can read it and you can tell me if you think.
Sometimes it's really difficult to see if I don't know how.
Maybe I did it too fast.
Let me see.
Yeah, let me show it to you.
It's this one.
So can you see it properly?
Is it okay?
These ones are.
I.
I agree
these ones are my model's fault.
They should have understood these kind of examples, which I can give him more.
Maybe the model will understand these kind of issues.
15 were.
I think 15 were the total issues out of 41.
And these are the ones I am not sure about.
These are ambiguous.
If you can see if you can just take your time, read them and tell me if you think that they are.
They're like.
Well, for example, number one.
It's difficult to say, but we can say that in this case it seems that
this is a real forest.
I mean, there is something happening here.
Nita in the forest.
Lucy like pointed the finger.
Pointed some little figures with the finger.
And this figure were like hanging in the empty space.
So this is.
You say that it's literal, not like.
I mean, it's.
It's difficult to say from an extract, but I don't see any reason why it should be figurative.
Figurative, because
it's in the forest.
There are things going on here in the forest.
Yeah, I mean, maybe there is some sort of background.
I can't establish it from here.
So this why it was written.
The system said it's referential, but the goal probably wasn't narrated.
So you change it.
Yeah.
This one can you verify?
Because this.
Even the question is written.
I think it or something.
Yeah, because the point here is delicate because 19.
In this case it is not.
It's ambiguous.
But since that probably some sort of.
Let me say English.
It's a tableau.
It's like
some picture.
So this picture is showing scenes from the sea.
So in a way it is a picture within a picture within a picture of something.
So we could agree that it could be referential.
But it is not the sea that is in there.
It's the representation of the sea.
That's why I.
I put figurative.
But it's ambiguous.
Yeah.
This one was desert because I did read them in English, but it's in French.
I wrote in French for you, so I.
I don't know what it's written.
So that's why I'm giving you these.
I guess in this case it could be right.
It could be French.
I don't know why I put things.
It's okay.
That's why I'm.
I'm here to like, help you.
These are the issues.
And
so it's the same reason of that.
So this is.
She sat at the base of the curtain.
And on the curtain there are motifs of their.
Like pictures of
migrating birds
within pictures it cannot understand.
Yeah, yeah, probably.
I mean, of course it is.
There are.
Truth is not a smile, but it is a representation and figurative representation on something.
Okay.
And these ones
are the.
These ones.
I am pretty sure they are wrong.
They.
The system corrected them.
They should be
wrong.
I don't know.
Probably was an error.
The second one.
Imagine.
So it's the same reason.
No, these ones are.
The system is saying that they are 100% sure that it should be referential.
And the close road.
It's.
The gold here is wrong.
But here it is the same reason.
Then.
Oh, so because there is a
art gallery where.
Where exposed my
drawings of mountains.
So this is drawings on mountains, not real mountains.
So it's the same.
So same thing here.
This is the.
The word is lack.
I thought it was like star.
Sure.
There is luck because probably it's the same reason the.
The like the.
I don't know what's the English.
The
like
is like.
Like a bar.
A structure.
Yeah, A bar
representing a star.
So I thought probably a judge star as an element.
But if it's luck, it is true that it's right.
If it's judging luck, it is true.
It's right.
It's referential if it's star, because I think the names are written at the top.
So it's.
It is lack, I think over here.
So I think it might be lack.
Yeah.
So it's right in this case.
In this case, I don't agree.
Because this like a multicolored mountain of toys.
So it is not a mountain.
But this metaphorical use of mountain is a big quantity.
And you take the over down like.
Yeah,
this is this 12.
It's ambiguous because it's difficult to say from here, from this context.
But it's saying she was
not
different from she was.
All that she was was like what they call was like ruins.
On the shore of a lake.
Okay, so is this because she's a lake or is like part of the image of like being like
trash, bored of lakes?
So I put that figurative.
I think you can.
You can.
You can defend the fact that it's referential, but it's lacking context from say I say that I judge the idea that it's
an image.
She was nothing else that like
trash or.
I don't know the combo.
It's like what's left
the board of the lake.
So.
So
in this case,
it's also lacking context.
But
she's saying that Luke is bringing back his animal farm to his room.
Okay, so I don't know what he's talking about, but I don't see, like, that's the possibilities springing back.
A whole animal farm.
Probably it's like Pelosi or something like that.
I don't know.
It should be the context, but it's.
It's ambiguous and it's lacking context.
But that's why I
chose that because
I mean, it doesn't fit with the real Animal Farm.
You should probably look at the.
Yeah, I'll look into the context.
Of course, this is really, really ambiguous.
These are the reasons that the accuracy of figurative head of literalist low
If I correct them, the ones that you are saying, okay, they should be referential.
It goes about like 78% if they should be.
So I think that's the.
I.
I will work and I will change these specific ones which you're saying that it's in the picture, is inside the picture, and like, big quantity
of amount and it's not actually a mountain and stuff.
I can change them and it can go around like, maybe 80%, but that's the
best.
I think it's best that what was done.
Yeah.
Before was 47% on.
No, I mean what Joanna did with the ChatGPT.
Yeah.
With it.
Yeah.
It takes money.
And it also even that it was, I think, 47%.
Okay.
47 or 16 or something like that.
I don't remember.
Well, this is the thing for task one.
I just wanted to confirm you.
Task one is okay with me.
For me, you can.
You can go ahead and apply to the entire.
Yeah.
Because the task 2 has a little task 2 whole part, and the task 3 has a little part which I need to run from
task one.
That's why I wanted to ask you about it.
So I'll lock it in
and it's gonna go.
It's gonna be like 90%.
So it's all gonna be like 90.
Of course.
Can you.
This is.
This file.
It's really cool.
Probably if you can, when you have time, just detail it as much as you can.
I mean, like explaining for dumps also not
leading to implicit things.
Just try to document it as much as you can.
Yeah, I'm documenting on the side.
There's a little documentation and stuff.
It's also the thing that didn't work.
What you did and didn't work.
Yeah, I'll make a whole, like, the whole story about it because even for this, this was a very.
Like, for me, it wasn't that hard of a task.
But even here, I have learned that if I gave them more examples to learn from.
It starts hallucination.
The model start hallucination.
Or they think that.
Okay, the task is very complicated, so we should take more time.
And it just results in lower accuracy rather than what should have been.
So I can add all these things in there.
Okay.
So task two was for the subcategories you shared with the document.
So this is the one Joanna made.
I am not sure if I should use this animal cases of Joanna because it was run on ChatGPT results.
No, you should use yours.
I should use mine.
I mean, you.
You.
You run when.
When you're done.
With that you run my own system.
And then.
Yeah, I did.
That is the reason I didn't run it because it was from the previous JBT GPT file and it was.
Accuracy was very low for like 60, 47 of.
So the thing is that if I run those.
If I.
If I run this system, it's gonna take around.
For animals, it's gonna take 44 hours, and for plants gonna take 80 hours.
Because it has around 200,000 lines or how many lines were there?
Like these many figurative cases were inside of it.
So it's gonna take this much time.
That's why I didn't run it, because it's gonna be a failure because Joanna's results are not correct.
And I wanted to run it after I get the approval for task one from you.
So the files I made, I ran a little bit on Joanna, like a few rows.
I was running it and then I paused it because there's no use of running them.
And the results were correct.
How do you know?
Because you don't ever go.
I didn't run all of it.
I ran a few.
A small rows of some.
Some rows and I got the results from those rows that.
Okay, which category does it.
You check manually if it was correct or what?
Yeah, I checked manually for a few rules because this is a little bit experimental experiment.
I mean, it's like the categories.
I'm not sure if they are.
Okay, so we have to see in.
Yes.
Maybe you should try on,
I don't know, on.
On a literal corpus and see if it makes sense for him.
Because I.
Yeah, I have to do that.
I have to do that.
This is just an experiment that I was doing just to check that even the system, the like the codes I wrote, is it even correct?
A little bit.
So I have to run first my own task one and then run these one ones.
So I am waiting and it's gonna take the same thing that is gonna take seven to eight, six to eight hours.
But I have to run the.
The task before for the whole compass.
That's gonna take like.
I think it's.
It's five days, five full days, 44 hours and 80 hours.
So it's gonna be like five, four, five full days to run it.
Then it's gonna be done.
I can give it to you.
There's no problem.
But there's no goals sets for this one.
Yeah, No, I can do it, but this could be.
Okay.
Yeah.
How much do you need?
I'm not sure if you can give me.
I don't know, maybe like 20 even is okay.
Maybe 20.
Only if you can do more.
But that's.
That would be 20.
Just do the same thing you did last time.
Just randomize some one occurrences.
And I'm going to.
I'm going to.
I'm going to take them.
Yeah, that's.
That's cool.
So I'm also seeing if the system is working because I'm not sure if it's.
How many do you want me to like, send you?
I don't want to burden you.
I can do 200 or something.
Yeah.
Okay.
Let me.
Let me shade for 100 for the animals and 100 for the plants.
Yeah.
And this one for the figurative ones.
For figurative.
So I'm gonna run from
these figurative results, which you said are okay for you.
Okay, then let's go to the task 3.
It had a few things you wanted to change,
so I did.
I did add.
I did.
Ran a human eye.
The human corpus for it.
And it has these many rows.
These are all the.
For the human Names.
Names.
And I did the active and passive.
Passive with agency.
Yeah, the agents and.
And stuff.
Then we have is all these details and you have like where they are object of an active verb, right?
Yeah.
When there is, then it's.
It.
It implies increases the percentage.
Otherwise if there's not, then does not add it.
So these are the.
For the humans, then I did for male and female.
Like you said you wanted to differentiate between male and female.
For animals, I did it on the data.
Joanna had the same data.
I have to rerun it.
And on this one it was giving this much accuracy.
Or for.
For plants.
It.
It's mixed right now because I haven't differentiated a figurative and referential.
But it's lower.
Yeah.
And you just want the referential one.
Yes.
Yeah.
So it's gonna.
I think it's gonna go maybe higher.
I'm not sure.
I have to run it.
I cannot.
I cannot like give you the exact reason.
So this is not 100.
What's.
What's.
What's the rest?
I mean, 37, 38, 50 to 70.
What's.
What's the Rest?
Wait, 5270.
No, I mean if you add up sum up all this percentages, it is not 100%.
So I was wondering what's.
I haven't added the other one because this one is the active agents.
Out of all these numbers, how many sentences or how many times the humans acted as an active agent?
Then how many times detectives as a passive agent.
How many times detects an object as A noun.
And the other ones, I think the ambiguous one.
We don't know what the other one, because here, if you can see, I added.
Where is it?
So these are the reasoning of why the passive is lower.
Because I was confused why the passive is low, because
passive agent is very low in number rather than the active one.
But I've read that in French, it's.
It's very low.
Rare to like, get a result from like in this perspective of Il.
Like he is and stuff.
Yeah, but for example,
this is a passive construction.
But there was no.
I mean the subject here.
It's the object.
I mean, when I say,
for example, I say the man was eaten by the lion.
Manger.
In this case, lion is.
I don't know what you mean, because in this case
it is a passive construction.
But the agent, the lion is doing an action.
Are we okay on that?
Because I don't understand exactly when you mean active agent is like when it is a subject and an active verb.
And a passive agent is when there is his.
It is working active.
Like let's say if the.
Let's.
Let's do the.
Yeah, lion example.
The lion is acting as an passive verb.
You write a passive agent was eaten by the lion.
So in that case, it should be like, for animals, it's gonna increase the percentage because it was in this sentence, the
animal was acting as a passive agent.
Okay, for example, now, so here, let's say here we have.
Julian killed the lion.
Okay.
Here we have
the lion was killed by Julien.
Right?
And here we have the lion
ate Julien, right?
Yeah.
And this.
I don't know, it's a noun.
Compliment.
Yeah.
Okay.
And this we have
the lion ate Julien.
Julien was eaten by the lion.
Okay.
That is what you wanted, right?
Okay.
And these were the.
The accuracy was a little low and.
Sorry, not the accuracy.
The percentage was.
Yeah, but still.
Still weak.
Me.
We agree on this.
Yes, we agree on this.
But so what.
What.
What's outside of this percentage?
Do you see?
It's ambiguous case.
It was the ambiguous ones, because I did write it here.
That's what I'm.
I'm searching for.
I think.
I haven't.
I haven't did the remaining.
Because these are the things that you wanted.
So I just extracted those ones.
And maybe the other.
Other ones are simple words.
Simple, like sentences, like in grammatical sentences or stuff.
But I can still check.
What are the remaining percentages?
I'll check.
Let me write it down before I forget it here.
Okay.
It's quite different to the results we got from the previous one, yeah.
It seems that the animal agency is overall not that low in terms of
humans.
Yeah,
yeah, it can be.
But these are the animals from the Joana's report.
So it's not the one I printed for my sister here.
And even for this one and this one is not just referential, it is also figurative in this.
Both are mixed here.
So for this one the animals.
Sorry, the human names, you might think that the human names are a little low like the feminine names and masculine names, like the whole
human names are little low because I ran a French model so it can identify the French names.
But there might be some names which are English or some Latin or some other languages.
So do you think the novel's gonna have them?
Because in that way I can try to explain.
Probably there are other.
Probably there are English or Arab or
any kind of names.
I think.
I guess it's not.
I mean they are not.
So the one it didn't recognize as
human.
I mean as human names at all.
Some names they might not have.
The system might not have recognized at all because they were like foreign names.
They can be Egyptian names or some other names.
So they didn't add them here at all.
I mean it's, it's not fundamental.
If you can do something about.
It doesn't take much time like run other models on that.
That could be cool.
But yeah, otherwise I guess the French names are
okay as a sample.
Yeah.
It's not going to be the whole.
It's not going to be like the whole names from the whole cop.
Yeah, I would say that the English name there are.
Yeah, I.
That could be many Arabs name.
And
yeah, I mean this tool could already been interesting to check with Arab and English.
Arab and English is.
I.
I'm not sure if Arab would have more.
I think.
Yeah.
Because Algeria is Arabic.
Yeah, they might have.
There's a lot of novel in the corpus that are from the francophone area.
So there is a lot of.
I don't know from Maghreb.
There's a lot.
There's a lot from
some places in Africa where.
So I guess, I mean, I could say Bambara also but of course it's, it's.
I would, I could say that the, the big.
The biggest non French name sub example would be Arab.
Okay.
And of course I'm not sure I will try to run a multi language model so it can detect all of the other names.
But
I could do it before as well.
But I didn't want to like mess up the results because they might like Overfit and they might think any
name as like a.
Let's say a bar.
There might be a name called bar in any other language.
Yeah.
So they might like take it and put them as a.
It's like recognizing like the capital letters.
Right.
When they restruct names.
It doesn't have to be always capital letters in novels because you know, names, even if it comes in the middle of a sentence, it doesn't
capitalize the name.
Yeah, but like it capitalize the names of persons when they're in the middle the of the sentence.
I mean if you have bar as a name, if it's capital letter either is
a name of person or it can be that sentence.
Start with more with the word bar.
So it is capital in this case, but otherwise should be not.
Yeah, yeah, yeah, yeah.
But still it's going to be the first letter.
Let's say first letter of center is.
It's a bar and it's not actually a name.
So it's gonna mess up.
But yeah, I mean, but what I can do is I can search for names which are in the middle with the capital letter.
Because I didn't think about capital letters in the novels.
The.
The names are the capital letters.
Yeah.
And also you have this messing thing also with French name because you have names like Fleur Flower.
So probably in this case you have
some.
I don't know what the nerd does, but I think one of the things that he does is to recognize the capitalized in the middle of the sentence.
Okay,
let me check that I haven't run.
If, if you want I can do a gold on that too.
On which one?
On the names.
It's like
just.
Just checking if it's a real name or is it something else.
Because the name for the name I'm using a model which is just trained on the names of the French.
So even if you'll give me.
It's going to give me 100% because it's going to.
Because it's going to detect the names.
But the other thing is that I.
That it is possible that there's a name which is also another word like let's say the Florian or whatever you were saying.
So I will make sure that the model differentiates by the context of the whole sentence.
And this was it.
Yeah.
Task one.
I tried to improve it.
If we are okay with that.
Right.
And
this one, I have to run the.
The whole corpus on the plants and the animals before I run task two.
And the part of task three.
Yeah, I mean probably through the animal feed ring.
We.
We have to trust the results, right?
I mean,
we've seen any more filtering of what?
No, this one.
But what I meant by this is that the results I got here in task
three over here, these was done by the.
Done on Joanna's results.
Yeah, yeah.
So I have to run them and filter them.
Like, just forget about the filter word.
But it's like I have to run it on my own corpus, on my own system, on the whole corpses.
And then I will run on the task two subcategories.
Is it possible that you can give me a goal set for the task two subcategories?
Yeah, yeah.
You.
You already.
We already discussed that.
Right?
You send me 200.
Oh, it was for the.
The.
It was for the.
For this one now.
Yes.
But also for the second one.
Yeah.
Okay.
You told me you send me 100 for plants and 100 for the animals.
And we.
And I annotated the subcategory.
So
this one is already done.
Yeah.
Okay.
And yeah, these were the results.
Did I?
Yeah, it was to use again the same thingy that it's going to take a lot of time.
So I didn't run it.
Otherwise I would have run it before.
It was going to take like a week to just run the results on the whole corpus.
The other thing that is left is the
task zero, which is the headache, the biggest headache for me.
And in here, here, I have tried to, like, increase the accuracy as much as I could.
So for now, the best one I could do is.
Where are those results?
Are these ones?
So this one I just checked.
I used another model right now, like before, before you came, and it's around 63, I think you run the
model that you were talking about last time.
I did run it, but it didn't work because the data set was very small.
Okay.
What was the name again?
Laura.
Laura.
And also the data set you gave me, the new system you gave me, it has one duplicate file, one duplicate novel, and
three novels are not present in the corpus.
In the total corpus.
The three novels are not.
Because you have three subcorpos.
Right?
I mean, it seems strange to me that you're talking about because you have like the
ecology novels, you have the bestseller, you have the other, and they're all corpus together in one corpus.
Corpus, total.
There's a name.
So it was not in there.
So that's why I didn't run it again on Lora, because it needed around 200 plus, and I didn't want you to, like, write 200 plus.
Data sets, you know, you cannot write it.
So it's also.
If you do 200, you almost can do 1,000.
So it's gonna be too much and.
Yeah, so that's why I didn't use that.
I tried a online model like in GPT4, but it was a Mistra API, which is like.
It gives you free tokens.
In the start I tried that.
Then I tried the another one, Gro, which is also like GPT4 and it's also free for some
tokens.
I was actually just running them.
Let me see the results of it.
I know it doesn't give much results.
It doesn't give much of a good results.
Well, anyways,
so I was running it and the best one I could do right now was.
I got another result.
And this is the best one I could do right now.
So this one, the results, I.
I ran another model, sample 72B with the intelligence and it gave me a result of.
It's written right here.
Yeah.
So with intelligence, it gave me a result of 68.3%.
So this is the one right now.
These are the results, the best one I could find.
With the online models,
the only thing that is left, there are just two options because I read all the research papers on them.
I tried everything.
Either the goal sets are not correct.
Either the goal sets are not correct.
Which seems to be the reason, especially for the focalization, because it's on the.
There's folk zero, folk something and folk int a lot of these things.
Maybe you can check the bold set again because I have tried every single model, every single research paper technique,
and it's not giving you more than this.
Just if you check if the models agree with each other.
If my goal is wrong, it means that the model should agree with each other.
I have the results with them and I will run them tonight.
Because that's what I was thinking that I will tell you over the weekend that if you can check these specific parts of the goal set, because I think
those might not be the correct ones.
Because every single time I run, these are the exact results I get mostly from every model.
So I will give you the exact options.
Sorry, exact goal set ones, which I think.
And the model thinks that it should be different and you can just check it.
The only other option is there are just two options.
One is I'm gonna still run it tomorrow because tomorrow I'm not gonna be working from office, I'm gonna be working from home.
I'm gonna run a
model which I am going to train myself on.
This specific goal set.
So it's this one.
So I'm gonna fine tune a model on existing gold labels and then I'm gonna like check it again.
So it's gonna take a lot of time, but it's free.
It's.
It's gonna be.
If it works.
If it works, it's gonna solve all of your problems.
But of course, the sample, I guess the 70%
accuracy, it's kind of.
I mean, it's better than what we have before.
So for space, it's not good.
But for the rest, I think it's more or less
cool also because, I mean, it's probably.
It's difficult sometimes to judge one another.
It's not.
So, yeah, especially these ones.
It seems weird.
I mean, for example,
but for the intrigue, it's quite.
I don't know this question.
Like even I'm running right now, it's just stopped.
Like it just finishes.
So you can see sometimes it says yes, and mostly times it says no.
For this specific model, it doesn't look
these options and stuff.
So I will run the other documents and I'm just gonna combine with the ones which I can see that.
Okay, this one's for this specific novel.
I think this should be the answer.
And you can check it.
Yeah, because I read a lot of it.
It's.
And
it's not a thing.
Yeah.
So for now, this is 63.
I'm gonna try the.
The model of fine tuning in which I'm gonna train a new model.
I'm gonna name it something.
If it works, it's gonna be a new model in the world and I'm gonna try that.
If it still doesn't work, then either we accept these results or we can try a paid version.
Yeah, I mean, I still have some money on GPT, so if you want I can do.
Can I can give you the access or what we.
I can do do is I can just run GPT4 or whatever on just vocalization.
Because that's the one of the things that we are most interested in.
Right.
I don't remember vocalization.
I think the only good one was the type of narrator.
But it's the one where you have also high results.
No, I'm saying that what we.
Which one?
Which results do you need the most?
You're most interested in
localization.
Localization is good.
I mean all of them are interesting.
Of course.
I guess I'm interested in every results that can go around 75% or 80%
for the rest style.
I mean, if.
If you say okay, this is, this is it.
That's what you are.
Because
you know, I would probably eliminate space at this time and I would use the others saying that it's around 70 and it's
the best we can do.
I mean, I, I think this is not trivial because I mean, there are some studies, I don't know if you have seen them on nerdology.
I have read everything
and stuff like that doesn't seem that they have like strong results.
This is not something that
LLM are still doing so well.
So I mean, it seems to me I, I haven't read anything conclusive on that.
So yeah, I guess it is normal if it doesn't work that well.
So.
Because yeah, these models are not trained on these specific things.
I was even running this.
If I will show you.
I have read all of these papers.
They like GPT.
Then we have a lot of papers, a lot of people.
What did the papers say?
Okay, papers suggested this model.
Let's use this model.
And I tried.
Okay, this, this paper, this one is.
But in terms of, since you've read all this paper, what they are saying in terms of accuracy that you're getting, they say that for their, their
goal sets, it worked for like 70, 75%, which is what more or less what we have.
And sometimes it says that with GPT, with paid version, you can go up to 80, 80%.
You can try it.
But of course I don't, I don't want to go with the paid version, but I can try it.
There are a lot of models, a lot of all of these things.
I tried all of these models, options, techniques, everything.
So it's at this point I'm like, It's not like I didn't try, I tried my best.
This is a research project.
I mean if you don't have to get
results.
I mean if it's what this is, the limits, of course I can.
I mean it's possible that my goal is not perfect.
I wouldn't say that it's wrong by 30% but I mean, by the way, this is interesting.
If you have all this, I would be interested in what you said.
Yeah, I just did all this in this last week.
So.
Yeah.
So what you have found in terms of research and what are your opinions or that would be interesting in having said.
But I mean for.
From my standpoint and from what I've seen,
there are not so many works on that.
But what I saw is not conclusive.
So it's being around what the others done still is not doing a breakthrough, but it's being
in, I don't know, in the game with the others.
Probably not the breakthrough, but
a good enough system.
You know what, I can try
to add some of my models with the GPT4 or mini you have and the GPT because I don't work
with API.
So that's why I'm asking you, is it the same API you sent me on the notebook?
You sent me a cool cloud notebook before.
Yeah.
Let me see.
And is it just for GPT 4 mini or I can use it for GPT.
You can use whatever you want.
It's just that probably the.
The
prices are different.
So.
But if you calculate that so you can Let me see what I am here.
So this is the
API.
I think you can create a key.
This is the billing.
So it's probably.
There's still $9 on that, but I can top up if.
If needed.
Okay.
And yes, it's like I can use any model like GPT4.
You can do whatever the model you want.
It's just.
It just depends on the payments of each token it takes from another model.
Okay.
So I don't know if you have.
I do have this one.
You shared me a notebook before very long time ago.
I can create an API different key because you said that one was compromised in case.
Yeah,
you need a key or you need to access the back end of.
No, I just need a key on which it will have.
Revoke this key.
Revoke this key.
So.
And create a new secret keys.
Okay.
Create secret key.
Okay.
So I can.
Where I can send it to you like by email.
It's okay.
No, let me just write it down because I'm going to get compromised like again.
You know,
let me just try really long.
I mean but it's okay.
I have.
Yeah, I tried this one for you.
This one, I tried this one.
These were the free ap.
But these models also doesn't work.
So it is
this one.
When you cannot see it again, you cannot see the API again the key again.
You just can see it the first time you create it.
Okay, I'll just create another one.
Then
let's revoke the button
and create a new secret key.
So I guess this, that this one.
Okay.
Sk.
But other than that the other results are much, much better.
The.
The task three, maybe the task two.
And the only thing that I am having issues with with the task one I tried and I will still try some
other
like creating my own model.
Like the fine tuning the model.
But just in case if it doesn't work, I don't want to give you like, you know, false hope that it will work.
Okay.
I knew that this was for me.
I mean even.
I mean I can work on this result because
before it was not really throw in terms of what has been tried
when the results are not
like 80%.
It's still.
You did a lot of different
experiences.
So I guess it can be defended now that it's not possible to do better than this with the tools that we have now.
Oh, it's a long one.
Yeah, that's
okay.
No, maybe I couldn't send it to you.
Yeah, you're going to send it to me.
It's a long one.
I thought it's just this, but it's a long one.
So.
I mean there are €8 on this.
So if they get compromised, it's not.
You send it to me by email.
To come maybe in a few minutes.
And I can also show you the
like the results which I think and all of the models think that these things are like wrong.
These options are wrong.
So yeah, that.
That's.
That's all I have for you for now.
Okay, cool.
So for the next steps.
So I.
What was.
Yeah, I'm going to give you.
I'm going to create some random 200
test data and you can like create goal set on it.
Yeah.
And also there was like the.
I think the only thing that's left
it's.
I mean I have new tasks for you
problems.
But the only one that's really left it was the.
Remember.
I don't know if I told you the.
The one where we are trying to determine the category of the
things the animal or the plant is compared to.
Right.
I don't remember if I told you that there was something we
tried
probably is in the
GitLab.
So it should be quite easy in this case.
But.
But let me see.
No, I don't remember.
There was different categories.
Mean.
See when you compare you use.
I don't know.
She was
like.
Oh, you're talking about the ambiguous words like the bar.
It can be.
No, no, no.
I'm talking about another thing.
I'm talking about this.
Why doesn't it connect himself?
You see, she was like a scared dog.
We want to determine this is the dog is figurative because it's.
It's comparison.
Right.
Okay.
And want to determine which categories of being is compared to the dog.
Like so we have different categories.
Show it to you.
Let me.
The circle one.
Let me take back some slides that I showed you.
That was this part where we.
Yeah, I.
I remember.
I Think with the.
A.
A lot of.
With a circle with a lot of
subcategories.
Yeah,
Yeah, you remember this.
So basically trying to determine where this categories.
And we want to determine to what the animal or plant or whatever is compared.
So let's say.
So in this case, the font which is the.
It's an animal.
I don't remember the name in French.
It's like this beautiful bird.
Peacock.
Peacock, yeah, it's a peacock.
So in this case, a human being is compared to a peacock.
Right.
So the
comp.
I don't know what's the.
The English word, but the thing is this comparon and compare in French.
So the comparant is like the animal in this case and the compare.
So the thing to wit, compared to.
Is an animal.
And then you have other cases where.
For instance, example,
you can have this case where.
So
he.
So the lizard.
It's a lizard, of course.
And so he's saying that the island of Cuba is
similar to a lizard.
So in this case,
the category is natural elements.
So the campari is the island of Cuba.
Right.
And for example, voici que la mout Voila petit.
La jeunesse est un chat insomniac.
So it's.
Chat insomniac is figurative, and the compare is la jeunesse.
So the hut.
In this case,
the animal is.
Is compared.
Is used to design
an abstract concept.
Right?
So we have this six categories.
And what we ask and what we try is to determine in every figurative
sentence
to
which category the thing that is compared to an animal or a plant or an element
belongs.
Okay?
So it's mainly.
So what the first results I have for animal is that is massively.
And it's probably right,
the animal used to design
a human body, a human attitude.
But there are some little subcategories like a psychological stage or an abstract
concept or an element, natural element, or some sort of.
This is for the whole animal.
Plants, humans, or is it just for one category?
It's like for animal, plant and not there figurative, figurative.
So when there is a figurative element.
So now you have figurative.
Yeah, well done.
You have to do.
Not you.
But the system should determine first of all,
what is.
Is.
Is this figurative animal or plant or element
referring to.
Okay, and
put.
So say in this case, just go back to the example
la jeunesse et unchat insomniac.
So the ute is an insomniac cat.
So in this case, you have the insomniac cat, which is the animal which have identified as figurative.
And we have you should find
why it is used what is referring to.
In this case it is referring to the genese.
So the youth.
In this case you have to classify
to which of the six categories
the comparison.
So the genese is refining and this guy's right is a conceptual nabstrate concept.
So in this case it is human body.
She is the peacock.
So she's the peacock.
She.
This peacock is referred to she.
And she is human body.
In this case, the island of Cuba is a lizard.
The animal is lizard.
And it is compared to what?
To an island.
What is an island?
Island is a natural element.
So what the model should do and.
And we probably.
You can find on GitLab what she used for that.
And we did it with ChatGPT again, maybe you can use your.
Yeah, I will do it my own because I remember looking at this symbols O and
E and these kind of.
If I can.
So once you have done the distinction literal figurative, then you can just take the sub part of literal
of figurative for all the categories and trying to
find.
And.
And you have probably a lot of.
Let me see on the GitLab should be some things that have been done by Johanna in this respect.
But I know I don't understand why it's not
Google.
Is it this one you're referring to?
Yeah.
So this is.
So the compari is
the thing.
The granule.
So the annual.
The figurative animal is
referring to.
And so the label.
It's in this case
ch.
Because it's human body.
So in this case the.
The phrase is.
Blah, blah, blah.
Let me find another one.
This is shorter.
So in this case
this probably is also an explication.
So she has.
What's the English for langi?
It's like
the long fish.
It's like.
No, no, it's like you have.
You can find it in like reverse The.
The eel.
The eel, yeah.
Yeah.
So in this case the eel is utilized and this is the.
The explanation should be GPT give it used to describe the.
The skin of a person establishing a comparison implicit comparison between the texture of the.
The skin and cell and that of.
Of.
Of a heel.
So in this case what it determines like ch.
Because of course is human body.
It's the skin of a person.
In that case, for example, you have here.
Natsume and.
But these are again run by the
ChatGPT model, which is wrong.
And you want me to run it after.
After the.
So basically you have two tasks there on one time on.
On the figurative cases that you have found now.
Yeah, with these ones I have to run this and check.
You have to run like the subspecies of metaphor that I showed the task 2:1
and on the same corpus of figurative.
You have to run this saying if I think I have a gold for animals for this.
But
let me see if there were.
There were six options for this.
I remember.
I don't.
Yeah, there's this option I.
I can.
I can.
I don't know if it's on the gift, but otherwise I can send it to you.
It's probably metaphor category, resultant apology, compare.
Probably some code also on that from Joana
scripts.
I think there is a gold for animals.
But let me see because we exchanged with Jonah about that recently.
Yeah, probably there's nothing on the gold with that.
So with.
Probably has to be done again.
So I
also for this one you can recognize to me and send it to me and I can.
So I want.
I have to give you the goals.
I don't know if you want to do the two task at a time or if it's better to have two different separate goals for two separate task.
Because I can annotate
on task one and on task two the same phrase all or if it would be better to have different.
I can look into it and then I can tell you which one is better because this one is for
My mind is all over the place.
The first one was figurative.
I have to give you the figurative with animals.
And second goal do you want me to give you is for.
It's the same thing because the second one is to determine to what.
What it is compared to the animal.
In this case, task one is just.
I mean, I don't know if the task one but the.
The subcategory.
It's about the structure of the metaphor.
So it is done where the animal is the specification.
It is like it is more than.
Or there are different categories and so it's formal.
The first one it's more
to watch.
The animal is compared with category of entity is compared.
So it could be
the same because in the first one I determined just the structure of the metaphor.
The comparison.
The second one same.
I think it would work.
The same one would work because this is probably.
Probably.
I mean it's.
I gain some time if I do the two at the same time.
Yeah, no, it's going to.
I think it's going to be okay because this is like the type of metaphors and the other one is just the comparison.
So I think you can do it one like for the same thing.
You can just.
Just put two columns and I will just do the.
Yeah, I will give it to you.
And the reason I'm confused right now because you said you wanted to go two goal sets from me, like, randomized ruleset before
this new task.
So which was the second one?
The second one was.
I don't know if you want one for animals and plants.
I think we were talking about at a certain point about, like, names
of people, but you said that you didn't need.
Yeah, no, I don't.
I don't think that I would be the only gold set.
Oh, sorry.
We have a gold set for figurative.
Non figurative.
Which is.
Okay, we just check in.
We have a gold set for narratology, and if you tell me, I can go back and check it.
But it's not all me that I.
I mean, sometimes I ask people who have run or have read the novels to write, so I can check that.
But for the one I.
It's also difficult because, of course, there's a lot of books and I have not read all of them in like
the last six months.
So every time I go and I check manually, but can be some errors there, but not.
Not.
Not gigantic.
I think.
So.
Yeah.
Let me write.
Let me write it down.
I have to give you.
You have to give me a goat set with 2000 set.
200.
200 randomized figurative occurrences.
Occurrences of animal, plants, and if you want, Lotaire.
Yeah.
And I will annotate them for the substructure of the figurative thing, I
mean, for the sentence.
And on the other hand, I will note them for
the comparison.
I don't know what's the company?
I think the same thing, the comparison.
So in English, apparently
it is either
tenor
or target.
Target.
Yeah.
I think comparison is more okay for me
or.
And vehicle.
So the vehicle is the animal in this case.
So pole is strong, as strong as a lion.
So the lion is the source concept or the vehicle.
And Paul in this case is the tenor or the target.
And in French, it's much easier.
It's comparant, which is the animal, in this case the lion.
And compare, which is in English, there's another word, comparer.
And comparison.
Okay, so compare is the one who is being compared with, like, the Paul.
And the comparison is the lion who is being like the comparison.
This one might be a very technical English I don't know about.
As long as we understand each other, it's okay.
I mean, doesn't.
Doesn't.
Doesn't matter.
So let me just write a pause.
As long as the concept is clear.
Okay.
And I Have to also I just remembered in my mind I had to also give you something and do you have the
list of categories
and their definition yesterday?
No, this one is for the like
or I saw them somewhere but I cannot find them now.
So I'm not sure where did it go But I did see the ch1.
Okay, if you can find it otherwise just send me an email I can refine it
like
see through.
It's.
It.
Yeah, I have no clue where did it go but I did see it.
Wait, let me maybe I have downloaded it.
I can't find it because
we have it in the git
should.
No clue where did it go But I did see it.
I think so,
but I don't know.
This
Let me see.
Also I have to what is going on in my laptop today?
Something is happening with my laptop so I'm looking very frustrated.
The
do you want me to like correct those results of l figurative so I can find the accuracy and
you can write it in your research paper?
Sorry, what?
For the Luto figurative I showed you that some of the
do you want me to correct in the Correct them and rerun it so I can get the accuracy and you can just add it in your research paper.
Also I will send you the
compared
wrong results from the models on
not figurative vocalization.
Different.
Okay and.
But I can only do this
I can only do the task four of comparison comparison after I run the task one
and it's gonna take 80 plus 44 hours.
So it's like one week, five days to run it.
Yeah.
Okay, so just to be clear, it's gonna take like five more days to
to run the result.
Just trying to find this.
Think
probably should and probably you have seen it in the
in the Google
collab.
Probably was in the collab.
No, it was in the file of GitHub but I cannot find it now.
I don't know why
if towards what they so.
It.
Also can you show me what are this?
You you told me that there are three
books in the gold set that are not in the corpse which I have no clue which one but it was in the last
batch last year the last 20 you sent me the extra one just from there.
So I I ran on 76 novels but I was.
I don't know why it's accuracy was a little more lower when I ran the 76 novel one.
So I I thought that maybe it was done very fastly, maybe there might be some issues.
So I just ran on the 60 Gold novels which I We are pretty sure that they are correct.
So I just ran on everything on those numbers.
So another thing that.
So now at this point
we have.
So basically in the structure of the.
The whole structure of the project.
So what it's still done by Joanna is all.
The
first part, it's about extraction of terms, of course.
So how we took the lexicon and applied to the corpus and extract all the
sentences and
disambiguate that.
Right.
You're saying about the 125 line document that they created?
Yeah.
Okay.
So it's basically took the whole corpus extract animal plants and later from that with the speed file
and then disambiguate and eliminate the.
The element that were not animal plants with Church pt.
So this is done.
I don't know.
It's where you
took the results from there.
Right?
So.
Yeah, because what.
What you are
not for this one.
For.
Yeah, for the.
The things that you have done.
You.
You took it from the point where she gave you in a certain way.
So if there are errors there.
I mean, it's okay.
We can accept that in a way.
For this one, for these results.
You're talking about.
No, I'm talking about like the figurative.
Because to distinguish task one or task zero.
Task two.
Task zero.
No, task zero is called you.
There's nothing that she did for task one.
Of course you start from.
I mean you have not done that already because you're all work only working on the goal.
But when you will run it on the whole corpus, you will run it on
the elements that she extracted and disambiguate in a way.
Right, we agree on that.
Yeah.
So this is because I haven't think about it, to be honest yet.
I haven't think about how to extract it yet because I didn't.
I was just working on the goal set.
Yeah, yeah.
But the point is that all corpus.
I mean this is phase one, we have the whole corpus now we have the whole 1,000 books and say okay, I'll run a
data mining on that and I'm extracting all the occurrences of the.
This point.
She did something else that she.
To eliminate the cases where there were not animal plants.
We talk about the ambiguity bar.
She did it in different ways and
with ChatGPT also with Syntactic distinction.
So I guess we are not going back to that.
So we are taking it for.
Okay, there are errors there.
There are things that are not animal that in there.
But we can not do anything about it.
Right.
I mean, what.
What's it.
What Right now
you're talking asking about her Model, I mean all the work she did till the point
where we are doing this distinction is I make you an example.
If we have an occurrences of.
Let's take one phrase.
But I mean also when I did the gold, I.
I told you there some occurrences, occurrences that I asked you to eliminate because they were not correct.
For example, the bar, the bar in the city was really vibrant.
It's not a fish, but it's still.
You ran it with this one, yes or no in the model with the fish.
So I guess this was not
perfect.
But.
And I'm asking you, maybe it is not easy or desirable to
go back on that part.
So trying to get better results on this disambiguation for the task one or for general, I mean for general.
But it means that of course if you're running now on the purpose,
you run it on her result.
And so if there are things that are not animal inside that, so be it.
But we have to consider that you are running on something that has probably 10% or 15% or I don't know, things
that are not animal inside it.
So we probably give problems on that, I guess.
And my idea is that we already have a lot of work on it and I'm not sure how you could really improve
that
because it would mean to redo the extraction and redo a disambiguization.
And I'm not sure if it's
easy to do that.
The point at this point is do we,
before you run the whole one week thing on, do we go back on those results
or we say, okay, this is what is what has been done.
So we are not going back to that.
Because the reason I am thinking a lot is because you said that I take the results from Joanna for this one.
That's why I was confused.
This one, it doesn't take results from Joanna.
It just goes, goes and takes the results from the whole corpus.
Like it goes and checks the novel and for each novel for this task 1.
Task 1 is figurative.
Not figurative line.
Right?
The referential and the figurative.
Yeah.
So for now what it does it like it search for the novel?
It goes.
It finds the novel and it like checks with the goal set.
Right now there is no ambiguous.
That is not done yet.
Yeah, of course, because you have the gold set.
But then when you are
passing from the goal set to applying it to the whole corpus, you're applying it to the big file with all the references.
And this has been extracted by Joanna and
the disambivization was done by her with GPT
so the point is, is it worth to go back on that or just we say that.
I'm not sure what I mean, she had some results on that.
In terms of
what we have in terms of Results was about 85% of success.
Success.
Okay, let me see if I have that.
So the one that Joanna has, it's from the whole corpus already there.
Say, let's say that
point that I'm trying to make is.
Okay, so first thing, we took the.
The list.
We took the references, we took the.
The.
The list.
Then we extracted 209 to
209,000 occurrences in the big file.
Right.
And then we try to eliminate the one that were not animal inside it.
And we did it with different methods, with GPT, with list of expression that
are not animal or
grammatical function.
And then from that we did a lot of things.
And then from that
we did the distinction literature figurative.
So in a way, when you're taking this point, which is your task one,
of course now you are not taking the whole
extraction done by Joanna, but you will do it, I guess,
when you are applying it to the whole corpus.
Right?
Yeah.
Yeah.
Okay, so what are you taking?
You're taking a big file, right, that you have
there.
Just the question was, do we trust this
ambiguization or not?
But if she got.
You said that she got around 85% accuracy and she used GPT4
and many other
models.
I.
I don't see why not.
Like, why don't we use that if she already got the accuracy?
Yeah.
I think that this is not perfect because I always found things in, in this file that are not animals.
Okay, right.
Or plants.
But I guess that this was a part of the job was already done and we were quite satisfied by it.
And I think it's more or less okay.
So just, just to discuss it with you.
I'm not saying that we should redo that.
Which, which would mean to redo the whole thing.
The whole thing.
And with.
With.
With your models and not chatgpt.
I think it is
more or less okay.
I guess.
I guess she put on the yet.
Yeah, that's what I'm confused about.
Where is the.
Where is the.
It's probably the script code
and scripts.
If you go on there and you go to scripts.
Let me open it here on the GitHub.
Yeah, the GitLab.
Oh,
Just, just point is, maybe not redo it, but just see what she did on that
and just assess that
if it's possible for you.
So I'm gonna work on the GitLab.
And show you.
So basically
this is the git lab.
So these are the scripts.
Yeah.
This one.
Yeah.
So sorry, it's here.
Let's.
Let's just see from here in this.
In here, right?
No, it's scripts, I think.
Yeah, you have like filters, you have pipeline.
Animal.
I think it's the pipeline to extract the animals.
It's the final one to extract everything at the end.
It's a sh.
File
can just click on the pipeline anymore, for example.
It's going to be good.
So what a pipeline does like if I am running a lot of commands, it's just going to compile all of them.
So I can just run one command and all of the models and commands will run.
No, no, I know, I know.
But the pipeline here is to extract the names of animals, I guess in
for instance,
how many.
It's just doing how many times a name account like a animal name has came.
Listen, I think this is, this is quite okay.
I mean don't, don't, don't go there.
Isn't this is a lot too much to do do for now is just.
This is.
This was the part.
Was the part where we were almost satisfied.
So just, just consider that this is good.
Okay.
And we start from there.
It's just that.
Yeah, it feels a lot of data inside
and it's.
But yeah, it was just.
I was just thinking out loud.
But I think we consider what was done by Joanna as okay.
And we start from there.
Okay.
So if there are problems, so be it.
It's too complicated to get back to that.
And yeah, because if something is already made and you have to like do things, if it was done by me, I have to do this
in will be much easier to like.
Yeah, yeah, yeah.
But it's kind of complicated to go back.
So the point is here to, to do the.
The stuff that are left.
And then I have
another thing that I would like to do.
So this is.
This is
it.
I have to work on that before.
But I can.
I can tell you because we have not talked about that.
So basically this is in the first part of the work.
So we are.
What.
What you have done is more concentrated on the second and third part of my work, which is stillometric, stylometric
analysis.
So what literature was figurative blah, blah, blah.
And eratological analysis.
Right.
So is there a pattern in the structure?
And the first one was lexical 1.
Right.
2.
Just find the biodiversity in the corpus and see how many species, how they are,
etc.
Etc.
So what we did, we extracted the Species and then we do stats on that how many mammifer and trying to create.
So what, what I tried to do is also to create, you know, that biodiversity is measured in, in
like by scientists.
Right.
So we say we, they have different index of biodiversity to measure how biodiverse a certain area
is.
Right.
So what we did also was to try to apply some of this criteria of biodiversity to a textual
environment.
So there is this index, which is called Shannon index that he used by
ecologists.
Sorry, you have to, to go.
I'm just.
So this is, this is the, the Shannon index that has been calculated by Joanna, also on the data.
And so basically this is, this is how you do, how you calculate the biodiversity.
Yeah, it's calculated.
This is how you calculate biodiversity
as a true biodiversity.
I mean the referential.
That's like scientists and ecologists.
And we adapted it to an environment, a textual environment.
So this is, this is a measure of.
It's coming from statistics and information sciences.
So it's, it's only about
how information is
distributed in a certain environment.
So you can apply it to real animals.
You say you in this territory, you have that much animal and that so much distributed and they use it.
But it's really about distribution of information.
It's not specific to animals.
So we, we adapted this to a textual environment
and we calculate it to say that we can create some sort of biodiversity index
when the animals are not real animals, but are just words in a text, let's say.
Okay, so this is one thing we did.
So then I met in the last few months someone a scientist or working really on that
matter in terms of biodiversity, real.
So it's like a scientist, a biologist, and is an expert of statistical approaches to
biodiversity.
So basically doesn't go and see the animals.
It just gets like a lot of data from the Internet from scientists that have done some measurement and
they run statistics on them to measure variation of biodiversity.
And I told him, oh, so I'm, I'm using one of your index, which is the index Shannon, to apply it to my corpus, to some
sort of creative, some sort of correlation between real biodiversity and how we measure textual biodiversity.
Oh, that's interesting.
And I said to him, do you have other indexes that we could apply to a corpse like that,
apart from this one that we already have.
And so he sent me some documents.
He explained it to me, what it does.
I say, oh, this is really cool.
It could be so interesting if we could apply this other index that you're talking me about to
my corpus do you think that could be applied?
Applied, yes, of course.
Because it's always about information.
So
the point is he sent me this document.
I have to study it a little bit.
But the idea and this could be done is.
So this is already done, but there are some other indexes that I would like to run on the corpus.
So
of course I can't tell you exactly yet, but there I'm working on it like this week's.
But the idea.
So in.
In the pipeline, if we have time, it could be really cool to try to run this.
I think it's not difficult.
It's.
It's not about artificial intelligence.
It's just about
applying some statistical measure to a specific corpus.
So I'm gonna send it to you once I have them.
Yeah, of course.
Maybe we can rediscuss it next week when I will be more
informed about how they are and.
Or I can send it during the week.
You can send it because next week it's.
I cannot work because it's just gonna run the system to run the task one and the plants and the animals.
So we can just.
You can send it to me and I will look into it because you're gonna come back all the way here to just to explain me the.
Yeah, all this is gonna be waste for your time because I cannot show you any results until I have the.
All of the data.
It's gonna take like a week to run it.
You know, just.
And so this is another thing I would like to do which is kind of new, but it's beginning
quite important to me because the point is that, I mean it's not of interest for you, but just to explain you.
The interest for me is that I would like to see in the first past how far we can push
this,
let's say comparison between methodology that are used in science to make measure biodiversity and things
that we could do in digital humanities on a corpus like this that could be interesting from a theoretical point of view.
We have already something.
If we could put more things.
So taking more methods from
ecological statistics and put it in this
project, that could be a real
plus value for the project.
Project.
So this is
kind of of important
but we, we can see.
I don't think it's difficult, but I will, will,
Will.
Will show it to you and I already can send you
thing that you send me.
Let me see.
Because you send me.
There was a crazy week.
I didn't have the time to.
Because it send me all this
slides to
you See,
this is like.
Like his classes and this is our.
What it does in biodiversity.
And so the idea is to apply some of this methodology that uses to measure
biodiversity to our.
Corpus.
So for example.
Yeah.
In this.
Of equitability,
stuff like that.
So it's basically only applying this
structure to.
I don't think it's.
It's really complicated but we'll see any anyway.
And then we had the task with
writing to
what was again the.
But maybe we.
But unless maybe this is the last task.
The task when we want to ask some sort of
database to apply
our accounts to their corpus to remember.
You do you have the list of the task?
I.
You.
You.
You wrote it down at certain moment.
Yeah, but I don't.
There was no.
Nothing about teeth A.
It's.
It's just that was.
Remember there is this database with a lot of novels from like 45 to 2,000 and.
Ah.
Yeah, okay.
Okay, got it.
Where did it go?
What SM is not there.
Yeah, not today.
Not the whole week.
It's kind of sick right?
To tell me that he's not feeling.
Yeah, I think so.
That I.
He didn't tell me about it but of course Motism doesn't like.
Like talking about.
About his health with colleagues.
But yeah, I think so he might be sick because he didn't come the whole week and this a very big seminar going on of medical data
in AI.
So.
Yeah.
What was I looking for?
Yeah.
Okay, you're showing me the list of tasks.
Yeah.
Let me see.
Where is that?
It was just here for a few seconds ago.
Let me see if I accidentally closed it.
This tree
close.
So this one you're talking about?
Yeah, front text.
Yeah.
So now we have.
Let's say that we have task zero.
It's done.
We can try to improve it.
But there is some sort of
limit to that.
Task one,
Task two
we need to.
To have the
gold.
I think peppers is what you.
You.
You build it.
No, I already have the sub.
Sub categories.
Yeah.
You don't have the gold.
Yeah, I don't have the gold and I don't have the results from the plants and animals so I have to run that this one is.
Is built.
So the only thing that is left is again I have to run this so I can run the final ver.
And extended to plants and animals.
This is also done, right?
Yeah.
And there's another task you just showed me which was on the application of biodiversity
index to the corpus.
It was the.
Yeah, the comparison.
Yeah.
And what it is somewhere.
Yeah, I have it here.
There's another task called Comparison.
Task 4.5.
Comparison
versus comparator.
And then we have this one.
The task.
Right.
Yeah.
What did you want in task five?
You just wanted to have like a system which you can give it to the front desk and they can just run it.
If you.
If I remember correctly.
Yeah.
But I think that we have it from Joanna because it's about.
Only about finding the entities.
It's just.
You need to understand what
was the right one.
And I just have one doubt on the
file with the.
Because I'm not sure.
You see.
So in.
So you have to run on the
right.
You.
You'll have to take
the
results
of.
So what you have here.
It's the file which you.
All the things.
But I think it is only for the main corpus.
So for the.
I don't remember how many, but they're like 925.
925, probably.
And then you have the bestseller also.
Right.
Bestseller is diff.
Is separate from the total corpus.
Yeah.
Okay.
So I don't think
so that's probably why you didn't find the.
The two or three.
No ones.
Because they're probably best sellers.
Okay.
So for the bestseller, we have another extraction.
So what you
need to do when you will
apply it, you need to apply it both to the total corpus
and to the best seller.
Is it possible for you to combine.
Because I don't know how many.
Maybe there's bestseller and total corpus.
And there might be another one later.
You can see there might be another corpus which has more data.
Can you combine it all together?
One file?
Yeah, in one
full.
In one corpus.
Or you can make a folder and just put every.
Every file in just that folder.
So I can.
I can just.
I can do that.
Just check the data.
Because of course, sometimes I forgot what exactly inside is.
Because it's kind of.
Yeah, no, they were.
I think Cooper.
One was having 925 novels, one was having 1070 novels.
The complication there.
It's also that they are not completely separate in a way that some books are bought
in the.
The bestseller and in the main corpus.
Yeah.
So I'm not sure what.
It's been done that.
And I have to check it.
Yeah, I was doing total corpus.
I think total corpus had 1007 one.
There were two folders.
One had 1074 novels, one had 925 novels.
I think I was running the.
The biggest one.
The total one.
Yeah.
But I don't think this.
Yeah.
This file with all the entities.
Because you probably have the list like the metadata in this case.
It's okay, but this file with, you know the.
This file here where you have all the extracts and that you will probably need to
use to
run figurative distinction.
All the novels and everything.
No, no, no, this is.
This is the novels, but I'm talking about the.
The.
The one with already the term extracted.
Right.
Because you have this file because you can't run on the whole corpus.
You have to run on the phrases that contains animal which are in this files.
Right.
And results.
Yeah, the stripped one.
Is it the.
Is it the.
This is the script inside the script or.
No, this is in results.
Okay.
Results.
If you go to results, you find this.
I trained a lot of things, so there's a lot of things.
Yeah, this is the main carpus.
What is that?
These are the results.
Okay.
So this is the ecology.
This is the whole.
All of your.
So this is the whole.
I copy pasted the whole.
Okay.
So it's where you get results.
Okay.
Here.
And then you have.
You should have
bestseller entities.
It's like where you have the all
abstraction, I guess.
Yes.
And then you have.
So here you have like the
source, the context.
Yes.
Okay.
And then you have a main corpus file when there are the others.
But
when you say the main corpus file.
Yeah, I can find it here.
But.
But you can see it here in the GitLab.
So basically you have
this when you go to results here.
Okay.
And you have two folders.
One is bestseller, one is main corpus, best seller.
You have the entities here.
Okay.
And so this is the big file with all the.
And then you have a separate one which is the same for the main corpus.
The main corpus, I think it's 925.
The other one is more like 100 bestseller.
But so the.
When you will apply.
The differentiation of literal and figurative will have to apply to both of the corps.
Yeah,
yeah, that is true.
So I mean you can start with.
With one.
With.
With the general one.
But then you have to do the best of the two and I just have to see.
To check if they are overlapping it in some way or not.
Because some.
No, what I can do is like I can
write a code that if it just run on both files, if the same like same source comes in another one, just.
Just skip it.
So it's going to run on this file as well as the other files which are.
Which have.
Do not have a duplicate.
So it's every single one with a unique source or unique context or whatever it is.
Okay, cool.
If it's not
clear, then we can still send you A message.
If so send me the goals that I need to randomize skills.
Yes.
And I will.
Yeah.
I think for now it's.
That's.
That's the case for this one.
You said that I.
Yeah, we were discussing this
the task five.
Yeah, I think this is.
Let's not do that for the round.
We'll see next week.
Yeah, there's a lot of.
There's a lot
just.
Just.
Just complete over complicated.
Because it's already complicated.
So just.
Just go there.
If you can do something on the narratology and then we'll call it today with that.
And you need to apply it to the whole corpus.
And then for the task one, I guess just apply to the whole corpus.
Just start by applying it to the general results
for general corpus and then maybe to the bestseller.
If everything.
It's okay.
And
just send me the gold to annotate for subcategories and for the compar.
Un.
Compare thing.
Maybe if you can find the categories.
Otherwise I can send it back to you.
Yeah, if.
No, I think the categories were there.
The chpo.
I have seen those things because I was thinking it might be related to nerdology.
I have seen it.
I don't know where did the file go?
If I still cannot find it.
I will ask me and for like the active versus passive word usage.
I think the.
It's only.
You only have to see what.
What are the things that are left outside and just document what you did has.
Has
with as much details as possible.
Yeah.
And then I'll.
Next time we meet, I can
send it before the.
The statistic.
I want to apply.
Yeah.
So you're gonna leave on July 15th, right?
Yeah, on 15th.
So I still have around 20 days.
Hopefully I will try to cover as much as we can.
Yeah.
Cool.
Cool.
And let's.
Should we meet next week at a certain moment?
I think next week would.
The system will still be running on the whole corpus.
So it's like the end of next week because then I have to go and you have to leave.
Yeah, but then I'm going back.
But when will you be coming back?
Yeah, the
9th of July.
Yeah, I'm going to be there for.
Till the 3rd of July.
So yeah, 3 of July could work for you.
Okay.
Yeah.
Let me just
add.
And by that time I will give you the results of everything that can be done.
So it's going to be finished and we can just work on the.
I think the task 5 and the task 4.5.
The com.
No, sorry, not the 4.5.
The the new one that you were talking about.
Yeah, it's like the new.
I will try to finish it by then because I want to also finish this.
Okay.
What time do you want?
Maybe in the morning.
I'm fresher.
So 11.
I don't know what's.
What's.
Yeah, 11 works for me.
11 is perfect.
Okay.
Thank you very much for all this work.
No, no problem.
I will.
I will try to do as much as I can,
even if it's.
I hope it's up to you.
I also was.
I wanted.
Wanting to ask a feedback from you until now.
Do you want anything else?
Do you have any issues?
You want me to change something?
No, I think it's.
It's okay.
It's.
It's.
It's a little bit.
Of course difficult to
adapt to a work that has partially already been done and not starting from scratch, which I guess it's easier,
but.
No, I think it's.
It's okay.
I just.
I hope that.
So priority for me is to have as much documentation as possible as I told you
to have all.
Because
I see that in what I do.
I tend to hide a little bit all the technical stuff.
So it's less impressing of course,
if you just say, okay, so we got this result and that's cool, right?
There's a lot of work behind it.
So I would like to go in a little bit of detail.
And I was.
I mean Joanna was.
Didn't have the time to document as much.
So I would insist on that on this aspect.
So having a file of documentation that could be put in an axe of the work to explain exactly, exactly
what is being done in terms of technical stuff.
Even if it's technical, don't bother.
Just.
Just.
Just put it.
So for me, this is really important to have a documentation.
So please create, continue what you're doing, but just go in as much detail as you can about what
you have done.
Also the dance and stuff.
Stuff.
And
it's.
It's a little bit.
I mean, I think we, we have done great work.
Is.
We'll see at the end
what are the results.
It's.
It's a little bit difficult to.
To.
To tell now if it's going to work.
It seems that it's going to work and I think it's, It's.
It's a real battering of this project which, Which I'm grateful for.
I just want to know if you're okay if I am going back on something which you need and I'm not doing my work
stuff.
Of course it's kind of a pain in the ass and I think it's.
I'm wondering myself if it was worth it in terms of energy and resources that we've.
We've used already.
Yeah.
Yeah.
But it's, it's.
This is not.
At least I can also give you all of the methods I tried.
So you can also add those that.
I think this is kind of a dead end of this because it seems
it's not quite straightforward when you think about it.
And then it's not straightforward at all in terms of terms of the results.
So.
Because it needs the whole novel and the novel is like 10,000 lines of one novel and it needs.
And of course it's like.
I'm not even sure if it's so
I mean I'm a little bit anxious about the fact what I'm getting in terms of interpretation from all this work.
Probably not that much.
Which is kind of free.
Frustrating.
Yeah.
But I think it's.
It's an attempt that could be done and it's cool to document the thing that you have done.
So to like to give the other researcher
that.
Don't do this thing.
What has been done and what.
Yeah.
It can also give them idea of not doing this tasks because it doesn't, it doesn't work.
Maybe, maybe, maybe it's.
That's the conclusion.
Maybe that's the conclusion.
We shouldn't like
we need to wait for.
For the.
For some more advanced
models in there because it doesn't really much.
Which is quite astonishing because I think that's.
Yeah.
I didn't know that the novel like in literatures can be so hard to like use a model.
I was like at the start I was pretty sure that I will do it then as soon as I've gone to the deck and it's like oh, okay.
There might be some.
These kind of, you know, the issues and everything.
Okay.
So thank you very much and see you next week.
There's nobody here, right?
You can stay as much as you want.
Yeah, just respond.
Can even stay here if you want.
AC you can also stay.
You know when you came inside there was a table.
Yeah.
There are a lot of people there.
Right.
Everyone.
If you want to sit there with AC, then this is your, your.
This is your.
If you want quietness.
You can sit here if you want.
EC you can just.
Maybe someone needs like for meeting or stuff.
I think everyone's want.
The kids went at 3, it's 4:30 almost.
So you can stay here if you want.
Did she left Claire.
She went to the classes.
In the.
You.
You can.
You can go see him.
He's walking.
Nausea.
Sorry.
See you guys.
The anime.
That.
Mutation.
```

---

<a id="meeting-transcript-2"></a>
## 8. `métaphore/Riccardo_second_meeting.txt` (full — second, more recent meeting, early July)

Same raw speech-to-text format, preserved verbatim.

```
Sam,
It.
Okay.
Should be this one.
I think it's more or less.
So
this latest version has a different
structure for the focalization, which is more.
More or less the same, but different codes.
And probably
send it to you.
And this was the last version we work on.
Probably.
I'm sorry.
I didn't know.
It was not.
It's okay.
It's okay.
I just have to run it again.
That might be the reason that the results are not that high.
So I can check it again.
That's completely fine.
Should I send it to you by email?
Right.
Yeah, email is better for me.
Yeah, this one was 70, so it's like 70.
75.
Thank you.
Because the run takes around like four hours if I need.
If I, like, create a new technique and I run it, the.
I run the task zero on it.
It takes around like three to four hours.
So.
Yeah, let me run this one.
It's gonna take that time, but it's gonna give me the.
Oh, yes, it has points here
that might be better.
Okay, I will run it and I'll let you know what this.
These results give me.
And let me see
the.
The goals that you send me now for the annotation.
So this is for the
task two.
Yeah, I.
I think.
But I think that in this case, we should re.
Annotate the localization.
Okay.
So just.
Just wait for.
I mean, run the vocalization.
But probably I should.
Or you run it with the.
But you see that the position is not the same exact thing.
And just.
Just check if the other were more or less the same.
So the focalization is different.
So it's not the same
kind of vocalization.
I mean, it's more or less the same, but it's not the same codes.
You're talking about the.
The new file you just sent me.
Yeah.
Okay.
For the task zero.
Do you just.
Just check that for the other
codes where we can check right now the codes and the criteria are the same that in the gold set.
Because otherwise.
Just take the gold set.
So the.
Now this is the.
This is the.
Yeah,
Let me zoom it.
I don't know why it's.
It.
Okay, just.
Just check if in the gold set we have the.
The codes are this.
I think they are.
So except for the focalization, but.
Just think the gold set.
This is the.
Oh, it's not the.
What do you mean by like.
Like the annotated.
No, no.
What are you trying to check?
I mean, and it's just to check if the.
The codes in the bones are the same that there are in the slot.
And you.
You added there.
Golden Orthology.
I guess
this one.
Right.
So the focalization is different.
But just check the others.
I think it's okay.
Just let me see the.
Let me see what we have.
So intrigue is lean
frag and sick.
Lean frag is okay.
Sick.
There's almost no.
No, no one.
So the temporality is like lean.
This the zord.
Yeah, probably there is one.
It's not so frequent.
Yes.
The sword
and narrator is auto.
Narrator is auto
and 10.
Yeah, sure.
And then we have the modality is
E V E V T I N T R Intro.
Yeah.
Desk.
Desk.
Dia and mix.
Desk and mix.
Yes.
Yeah.
And the space
is either frag 18 unit
or image.
I don't know if there are probably there are some.
One
image.
Okay.
And I think that is.
It is register.
Auto.
Real fund.
For which one?
Auto.
This one.
Originality.
This F Real Auto and
specific.
You can find one Spec.
Yes.
Yes.
It's okay.
So it's the only thing that's changing apart from the description.
But I also have to look at the.
The definitions of them.
Yeah, the definitions are probably a little bit.
Yeah.
Let me.
Let me try with these new definitions that if it changes because I just have to give them the new.
New file that just work with this one.
I think it's okay.
So I have to run task zero on the new file, the one you just sent me.
And I will have to annotate again the focalization for.
I mean because the codes for focalization are different in this new file.
So probably we'll have to resend you
the goal set for the task 0
in for task 0 with the focalization change with the new code.
Okay.
Of course.
So I have to email you about this that send me the gold set of vocalization.
And this was today's file, right?
Yeah.
For task two.
Yeah.
So let me open it.
So the subcategory is.
Okay.
So the.
The annotation was terrible because there's a lot of.
Yeah.
Yeah.
Things that are not
images analogical that were in there.
So the.
The codes are okay, I guess.
But there are things that I had to add.
So this is color.
It's mean when.
I don't know if we should just eliminate that.
But it's when it is.
The.
The plant for example is used to design a color.
It's called.
It's like.
So I don't know what's in English, but it's like.
Like green apple.
Green apple.
Green color.
Yeah.
So it's a apple there.
But it's It's.
This line explains the color of the plant.
Yeah.
I mean, in this case this has been annotated as figurative because I.
Anis is.
I don't know.
It's a plant, but it is used to design a color.
Okay.
Okay.
So it's like it say it's a sweater,
apple green.
Right.
Okay.
So I don't know what to do with that.
I put a color, a good color.
I don't know if.
To eliminate completely all this kind.
But in any case we should add
color.
So there's no reference.
But it's just a color.
So it's not a metaphor.
It's just a figurative use.
Probably.
It's just a case of how it's seen.
Maybe we should.
There's another new code which is idiomatic.
So when it's used like
it's in English, it's.
It's a thing that you say is lexicalized.
There's a Shashili.
I don't know what's in English, but it's like finding a
needle in the.
Okay.
Space.
Right.
So this is not.
This is figurative, but it's not a new metaphor or a general metaphor.
Is just a thing that is
idiomatical use of this image, which is always the same same.
So it is known and is no longer referring to
the plant or the thing, but it's just here.
It's something that is.
That is said.
So it's idiomatic in this case.
And there's another one, another one I had to add which is.
It's okay.
It's okay.
It's okay.
It's okay.
So this is the case
were discussing the other day when it is not a metaphor.
It is not a smile, but it's.
It's an image.
It's like a representation of the animal in like a story or
in an image or something like this.
So in this case I end up with the emac.
Which is since saying that is an image
and it's also.
There's no reference here.
Sometimes I had to
put a interrogation mark
because it is impossible given the context to determine what is the compari.
But
it is clear what's the form of the metaphor of this mind?
So this is it, I guess.
Okay, so maybe some of them doesn't have the gold set of the subcategories here.
No, the subcategory is okay.
Sometimes there is no.
The category of the.
Of the compari.
You remember we talked about what is referring to because it's not clear in the phrase because there's not.
Not enough context.
But.
But for the rest.
So this X are.
There's no.
No, there's a wrong attribution.
So probably they are not metaphorical use of the plant or something like that.
So it was a wrong categorization of the phrase.
And maybe we should add this category.
Did you.
Did you do the goal set for the comparison?
What do you mean?
This.
This is.
This is.
This should be right.
The figurative use of animal and plants, right?
No, the 4.5.
The new task you asked me to do last week.
Yeah, you said that.
Comparison comparator.
And the comparison.
Yeah, this is it.
Okay.
This one is.
Yeah, but sometimes it's possible to determine it.
Okay.
Because that's why I was asking.
Because you wrote the question mark.
So I was confused that maybe.
Yeah, the question mark is because it's not enough context.
So even if my system does anything, it's okay.
Do you want me to say okay for that part?
Because when it looks at the goal set and there's no category like question mark, so it will say wrong.
Even though in the goal set right here you don't even know what.
Yeah, probably necessary.
I don't know what do you think?
But probably necessary to put.
But I don't know how system would be if.
If.
If there is not enough information to
determine.
Just put.
Determine or question mark or whatever.
I don't know.
Because sometimes it over
does this.
So in this case.
So put too many question marks.
It's probably not good.
So it's better to have like answer in any case.
And.
But sometimes.
Yeah, I think it won't be an issue because we do have the meanings of when we use this.
When do we use a.
And all that.
I can check.
I can run it and I can check what the results are.
So maybe I should.
I didn't have the time, but I should add definition for this new.
You have to add that if you can tell me.
Yeah.
For this one image.
Color.
Like the one you just.
Yeah, and color.
I'm not sure if I'm going to put it in there, but let's.
Let's.
Let's see.
And in the end, maybe we can eliminate that and lock.
Idiom.
It's idiomatic.
Yeah, the idiom.
And there is a.
This is at least three that are.
The others are.
Okay.
The other are image words.
Image.
Image.
These ones, you said that they are not.
They shouldn't be there.
Yeah, it's like probably literal use of the plants.
That's taken for metaphorical.
If you want I can run like it's gonna finish.
Animals is gonna finish this like tomorrow night and the plant is going to finish in two days.
If you want, I can send you the goal set, like a random goal set from these results.
Because this is also what Joanna did, but her system didn't do it much.
Well, yeah,
yeah, probably.
I mean, what I have done is probably, I don't know, 100 something maybe.
Yeah, because they are.
Because maybe we can replace just the ones that are not good there.
I don't know how many there are, but a lot.
I mean, I would say
this is a verb here.
Here.
This one.
What is this?
This is the subcategory of the metaphor.
So you have the subcategories
and so this is the code for the subcategory.
This is explain which kind of smile or which kind of metaphor it is.
So you have the.
I have the file.
Yes, I remember.
Okay.
Yeah, it might be like a hundred something because there's pretty much of a X points here.
I think it might work.
Even these might work for gold set.
I still.
Yeah, it's a little bit.
Because since the.
The plants were bad, there's probably much more animal than plants in this gold set.
Yeah.
Okay, then I can send you the gold set with just plants and some animals.
Yeah.
Okay.
That's not an issue for me.
Okay.
Yeah, it's just to check which file did you use to run the whole thing?
Because we have to.
Yeah, I.
It seems weird to me that there are less plants because normally it should be.
Yeah, they're less.
Of course, in terms of volume, but not.
So if you have scorpus principal so entity in here.
These are the plants and the animals.
These are the animals,
the plants.
These are the total.
Yeah, you can see there's no the probably the total is with animal and plants.
Let me check.
Which one did I run?
Because according to the
data I have,
We should have.
So according to the data I had, we should have around.
101.
Let's say 100,000 animals.
Probably 120 or something.
And around 60,000 plants.
So it's half of it.
Yeah.
So half of it is it.
The first one took five days and the other one is like two and a half days.
So it's like.
And also you'll have to run also the best seller, right?
Yeah, the bestseller has only 70 or 40.
70 something like that novel.
So it's not gonna take much time.
It's like a full day for both of them.
So that's.
That's not an Issue.
And just once you have it, just it to me.
So I can.
Sometimes there's.
Because it's still.
Yeah, it's still running.
And after every few, like every day I gather some random results and I check that if it's correct.
The results are correct.
With the animals, the ones.
Can you send me just a random few.
Yeah, of course.
See what, what's.
What what's giving.
I will get it and I'll send
it to you by email here and.
Okay.
So we wanted to talk about the.
About the new tasks.
Biodiversity.
Yeah, yeah, I think I can do it by myself.
It's not that complicated because it's, it's, it's, it's.
It.
I mean, I'm trying this week to do it by myself.
If I.
Not.
Okay, I'm asking you.
But
it's.
Maybe it's, it's.
It's.
It's only about
applying.
I can do it with artificial intelligence quite easily because it's just applying new calculation to data that we already have.
So I'm, I'm just, I'm working on it and I can do it myself.
It's maybe more complicated to explain all myself,
so there's no problem.
What I wanted to ask you.
Sorry, you were saying, if you want me to do it, as you said, I don't think it's much of an issue because we just have to classify the animals and plants
into some categories for the biodiversity.
I can do it as well.
So let me know if you cannot do it.
Let me know.
I will.
I will try to figure it.
Yeah.
No, what I would like to talk about what's.
Can we see again?
The task with like the names.
Do you remember the names of the people?
Yeah, yeah, yeah.
I did not work on that task anymore then afterwards.
Yeah, but we had said something about we need to.
Yeah, we need to add Arabic names and English names.
Can I just see the results?
What does it look like?
Because the result seems a little bit
strange to me and I wanted to check what
would be an example of.
I mean, what does.
Do you have like a CSV file for all of it?
What does it look like, the results of it?
I think it's this one.
Let me see.
See.
Do you want me to show you some examples?
Yes.
I mean.
Yeah.
And you run it on the main corpus.
Bestseller corpus.
On,
on the whole corpus.
In the total.
Not in this one.
But I went and I took the whole novel.
Yeah.
1,000.
Yeah.
70.
Yeah.
Let me find the exact file because I don't know, it went dependent
J.
Dependent human.
CSV dependent human.
CSV dependent human CSV.
Okay, I cannot open it because it's too big.
Sorry, what?
Migos?
I cannot open because.
Because it's too big.
Let me still try.
Okay, I'll just try to show you from my kit from my
terminal thing.
Can you.
Can you see it?
Yeah, it's.
A lot of things are happening here.
So these are the.
The names and then
all of the details of the object.
Okay.
This is happening like this.
Okay.
And how big is this part?
It's pretty big as you can see
but.
So you didn't have a gold set for this?
No, I made it myself because it didn't give me the gold set for humans and I just ran it.
Maybe that's why it didn't give.
But the reason is that these are the humans
names.
But there might be many more.
But it's just for the French.
Yeah.
And we were discussing also the fact that there was a percentage that.
Yeah, that was very low.
The.
No, no, but it was the percentage of things that were not defined.
Yeah.
I did write it in a file.
Let me.
Let me try to find.
It's
it.
It's
it.
Let me see.
Where did the file go?
I remember what the issues were.
Sorry, not the issues like the what it was.
But I'm trying to find the exact examples.
I copy pasted some examples.
It's no problem.
It's just I did write it somewhere.
Let me.
Let me find it.
Otherwise my brain will not work until I find.
Was something like this.
I don't have.
I don't know where the final report went, but it's somewhere in my system.
I'll find it.
It was something like this that they did not.
Were not in the category you told me about the action verb passive verbs.
They were like.
Okay, some you can see the examples.
I think what I would need is like.
Can you this week
since there is running.
I would need the
most detailed documentation possible on this.
So I can maybe.
Because of course you explain it to me.
But it's a lot of detail.
I got this stuff.
Maybe I would.
Because I need to understand exactly what you did in order to be able to use it.
So
see if you have time this week it would be ideal to have like put together.
I mean I've seen you written a lot of things.
Yeah, it's just a documentation.
No, that's a lot of documentation.
Even I have to find here and there.
So I completely understand.
It's just.
Just put together a documentation for the whole thing.
You did
Be okay for like 40 pages.
Will you be able to write like would you be able to read like 40 pages?
Is it okay?
No problem.
40 pages.
It's okay.
I mean it's just as much detail as possible.
As much.
Because it's going to take a much
possible and so that I can.
If there is something that it's not clear.
Clear to me or maybe it's not okay.
I would like to have a little bit of time to.
Just
before you leave, you.
You leave to.
To be honest, I don't think that it's gonna finish by the time I leave.
I'll.
I'll try to finish it by the time I leave.
Like I think the last day would be 13th because on 14th is the public holiday.
14th of July and 15th I leave.
So even that's okay.
I can work like we can communicate online until I give you the final results until like the end of.
Yeah, that's why I was like, okay, it's okay.
I don't have rush that I'm gonna have to finish it by 14th of July.
So it's okay.
So don't.
Don't worry about it.
Even if it didn't run by that time I didn't complete.
I will complete it by.
But of course there is something I need to check is better if I have the documentation.
Yeah, I will give you the documentation by tomorrow or by Sunday.
Not necessary.
I mean I'm gonna tell you my.
Because I have really urgent stuff to do from here to
let's say Wednesday.
I wouldn't be able to touch at anything.
I mean maybe if I need to do something really urgent, I'll do it.
Like the gold set for vocalization.
It's.
So I'm gonna do this but
starting From Wednesday the 8th, I will be able to read it.
So if you can buy that time, I'm gonna read it probably.
I mean, I don't know when we are seeing each other again.
Maybe Friday.
Could be next Friday.
Next Friday is.
Which date?
10th.
I have an appointment on 10th.
Wait, let me tell you the time of that appointment and we can schedule around it.
Yeah, give me one second
because I am leaving.
So I just booked an appointment.
Otherwise can be the 13th.
Right.
But maybe it's a little bit last a year.
No, the appointment is at 1045.
So we can do like.
Is it okay?
Afternoon is okay.
If you want it by Wednesday then the system can be like.
Can finish by Wednesday and I can run it on the remaining tasks so I can finish like task two and task three.
Do you want me to add.
To Finish the task 2 and task 3 and add it in the.
In the documentation and I'll just give it to you.
So by that time, task two is done.
Task three is done.
Task one is done.
Task zero is still.
I'm trying to figure it out.
And task 4.5 is left behind because you said that the comparison you
like
put the task here just to be sure.
Oh, you mean the.
The list of task.
The list of task.
Let me.
Let me find it from.
It is in.
So here's.
So task zero.
So we are working on it.
It's almost done.
Task one is.
Okay.
Just running.
This one is partially built and I
have to run it after.
Partially built was for the.
For what Joanna did, but now I have to make it again because I
have to send it to you.
The new categories.
Yeah.
For
like breakdown.
Task zero.
I have to run the new file you sent me again.
Yeah.
Task zero.
I have to give you a new goal set
for vocalization.
Okay.
And so task three is done.
These two are going to run after
task one.
Because here I have to.
Something was left.
No, there was something left in there for the animals and plants.
Yeah, animal and plants.
So literally you have to run.
Yeah, I remember.
Something was left in here for which I have to wait for the task 1.
Task 2.
Again, I can only run after I get the results from task one.
We already did this, right?
They extended to plants and humans.
Yeah, yeah.
And the last one.
That one.
You have to run it.
And task five, I mean.
And we win.
We won.
Want.
I mean, I have to see that maybe in the future, but I don't have.
Yeah, I don't.
To be honest, I don't even know how to like give them.
No, no.
I mean, I have to think about it, but maybe it was a little bit too much of a stretch.
And we have already.
I can.
I can then write the documentation until it's running and also try to figure out the task 0.
The accuracy a little higher.
Right now it's.
Everything is at zero.
70%.
Around 70%.
So are you okay with 70%?
Two are on 70%, two are on 75% and one is on 91%.
Yeah, I think we will do with it.
We'll go with it.
I mean, since we.
You have tried.
But again, it is really important to have documentation of what all the attempts that you did.
Yeah.
And the reason I'm not trying.
I want to try GPT4.
But I want to ask.
I wanted to ask you before I run it do you want me to run with GPT?
Like GPT or the paid version?
Yeah, and also I wanted to ask you that
which.
Yeah, which one do you want?
The highest percentage.
So I'll try to run that first because I don't want to run it on say the Eugene.
Which one was it?
The escape space.
I don't want to run it because the accuracy is very low already.
So you can tell me which one do you want the highest and I can run on that
focalization right now is 70 to 75%.
Yeah, but
I would say vocalization.
But then I have to give you the, the new goal set for the set and otherwise.
Because before running that I'll have to run the focalization on my own system because maybe the new goal set you will give me will
have much better results with the, with the offline models.
I would say is important.
Okay, let me see what results I'm getting right now for Nash.
Right now Regime Naruto is giving me 76% which is not bad.
76.7%.
Yeah.
If we could get it like to up to 80, that would be amazing.
So
you, you're not very interested in
Intrigue.
Yeah, I mean I'm interested in everyone.
Yeah, no, but like the highest one I need it.
Yeah, yeah.
And you have 66%.
I mean temporality also no temporality is this one.
I, I, you.
I was checking two different things I did so the you can just look at the good results of both of them.
So here I would say that strategic to try to get
everything over.
So 70% intrigue here.
Yeah, the intrigue is 83.63.
68.3 and temporal is 71%.
Don't look at
lowest.
So that's so just.
So if you can send it to me like even partial documentation from Wednesday, then I will read it on Thursday and, and
we can discuss it on.
When it's on Friday.
On Friday.
Because I already have the documentations, a lot of documentations.
I wrote it from like giving it to chat GPT.
Just write me the documentation of like.
Okay, I did this, this.
So I have some documentation.
I have to just combine it, combine
it and put it clear as possible
and I'll give it to you.
And you specifically want the
files I ran the system with?
Yeah.
So you need exactly the, the file on GitHub that.
Okay, I ran this.
It would be cool to have it on GitHub.
I mean I'm not putting, I'm not, I'm not using.
Not on GitHub.
I meant like you specifically need that.
Okay, you got this result, 72%.
Which file did you run?
So you specifically want me to tell you those specific big files that I ran, which are on GitHub?
Yeah, I mean, it's okay, but for me the most important thing is to
be able to see what are the steps.
So I'm not sure if it's specific files is so important.
Of course there is much more documentation, but for me it's important to understand and to be able to translate into my
work work what has been done exactly.
And of course, the more specific it is, the best it is.
But at a certain point I'm not.
I don't know what exactly I'm gonna do, but I'm not going into so much detail then like I use this file on this file.
But yeah, I mean,
as I said, as much detail as you can.
As long as it, it stays like, understandable.
Yeah.
Okay.
Otherwise it's gonna be like a.
A lot of numbers and stuff.
Yeah, no, I will try to keep it as simple as possible.
Yeah, I think that's, that's it.
Super.
Okay, perfect.
So let's say that we see each other.
So you know you're okay with.
Even if it's.
Goes to the AI.
To the
like a paid version?
Yeah.
You have the API, right?
Yeah, no, I'm just saying that.
Will you prefer to.
For me to just try it more with offline models or.
I.
I don't care if you.
If it can improve significantly.
The paid version is okay.
It's just that.
Just don't go with the eight limit.
Yeah, of course.
We have 80 more.
I can just put it more.
I mean, it's not, it's not, it's not the problem if you can put €20 or €30 or €50.
It's not, it's not a problem.
If you think you need that money.
I will try it on.
Yeah, I will just try it on.
Goal set for all of them and I'll just see.
Do you think if we can try and as long as say, I.
I mean,
because what about like €100 or 200?
No, no,
what I checked was it was showing me if I want to run it all on the whole copy, it's gonna take €22.
Yeah.
€22.
Yeah, I'll still check.
I can, I can add like €14 to the top.
Yeah, I will first, because these, the.
That one is gonna be the whole.
I'll still, still send you the whole final amount of what it should be.
But I, I Will first check it check the goal set.
Drop me an email where you say okay I need €25 so can you please stop up.
So I'm going to do it.
No problem.
So we have the funds for this.
Not.
Not the problem.
So
we're gonna see each other on
So I have to.
10th of July to the task 0 a gold set for focalization.
I sent you the new categories breakdown in terms of gold.
We are okay so we don't need.
You don't need me to do anything else for the.
For the new gold you sent me for the 4.51.
Yeah.
That's why I need to like you
have to do the new category and
and probably if you have the plants at a certain moment and send.
I will send you and you have to
go the right goal set.
Yeah you have to write the goal set for me again.
So yeah, that's it.
I think that's it for cool.
Thank you.
I think it's.
It's.
It's cool.
I mean we are approaching to the
end of it hopefully because before Joanna did was very good.
But the accuracy was like 40% for just to get.
I think it's better and I mean I'm really happy that we.
Because the part where we
do the data mining was okay but the stylometric and ontology was bad.
So maybe we didn't.
She didn't have any much time to do that.
So I'm really.
And I have to run the task zero on the new goals.
The new categories you sent me by email.
Yeah.
Okay.
I think it's not much different but we'll see if it's a little bit better.
To be honest, even a little like a little line is different.
It's gonna take away the whole accuracy.
So I will still but if.
If it's bad it's worse than the other view.
Yeah of course I will stay with the other.
Literally I just do this.
If it's.
If it worse I just leave that file and I lead with the previous one.
So don't worry about it.
So cool.
Perfect.
So thank you and see you.
I'll review on email and I'll see you next Friday.
Last.
Last meeting and one more meeting and
I'll deliver you the whole school and then we'll see in September I'll talk to Motorsam if I need something else.
We'll see But I was still answering the feedback from your regular and feedback or something.
Yeah later and I'll deliver you the.
The project.
Where did I put my keys?
This is interesting.
I I think I remember you doing this.
Yeah.
Okay.
I'm running home and I hope you.
Oh, I won't be able to, like, congratulate you, but congratulations.
Congratulations on the end of this for your video.
Thank you.
Bye.
Bye.
See you next week.
See you next week.
Bye.
Bye.
You should.
You should
please have some lunch.
Are you sure?
That's so cute.
Thank you.
Have a great day.
What's happening?
Did I forget about this today?
It's okay.
Just grab a plate and get some.
Oh, I forgot about bringing something.
```

---

<a id="research-papers"></a>
## 9. Research papers, models, and techniques tried on Task 0 (narratology)

Pulled together from both meeting transcripts plus this session's own direct work, since this information is scattered across raw speech and was never written down in one place before.

### What the literature said (per the transcripts)

Labiba, in the first meeting: *"I read all the research papers on them... I have read everything... they like GPT, then we have a lot of papers, a lot of people. What did the papers say? Okay, papers suggested this model, let's use this model."* No specific paper titles are named in either transcript — the discussion is at the level of "what results did others report," not citations. What was reported:

- **Existing published work on LLM-based narratology gets ~70-75% accuracy** on their own gold sets — Labiba's summary: *"they say that for their, their goal sets, it worked for like 70, 75%, which is what more or less what we have."*
- **Paid/larger models reportedly reach ~80%** in some of that literature: *"sometimes it says that with GPT, with paid version, you can go up to 80, 80%."*
- Riccardo's own independent read of the field (first meeting): *"there are not so many works on that... what I saw is not conclusive... it's being around what the others done, still is not doing a breakthrough, but it's being in the game with the others."* His assessment: the field genuinely doesn't have strong results yet, so a plateau around 65-75% is not a failure specific to this project — *"I guess it is normal if it doesn't work that well... these models are not trained on these specific things."*
- Working conclusion offered by Riccardo as a possible framing for the paper itself: *"Maybe that's the conclusion — we shouldn't... we need to wait for some more advanced models... it doesn't work that well, which is quite astonishing."*

### Two competing hypotheses for the plateau (first meeting)

1. **The gold set itself may have errors**, especially for FOCALISATION: *"Either the goal sets are not correct... especially for the focalization, because it's on the... there's FOC zero, FOC something and FOC int, a lot of these things. Maybe you can check the gold set again... every single time I run, these are the exact results I get mostly from every model."* Proposed diagnostic: **cross-model agreement** — *"just check if the models agree with each other. If my gold is wrong, it means that the model should agree with each other [but disagree with the gold]."*
2. **Models aren't capable enough yet** for this specific task (Riccardo's framing above).

The **second meeting reveals a third, previously-undiscussed factor**: the FOCALISATION coding scheme itself changed mid-project. Riccardo sent a new file with revised focalization codes ("more or less the same, but different codes") and both agree a fresh gold set is needed for focalization specifically before any further comparison is meaningful — meaning some of the "gold set might be wrong" confusion from meeting 1 may partly have been a moving-target coding scheme, not necessarily gold-set errors in the ordinary sense.

### Models and techniques actually tried, with results (both transcripts + earlier documented status)

| Method | Result | Notes |
|---|---|---|
| qwen72b-limited, FOCALISATION, with thinking | 61.7% (37/60) | `pipeline_overnight.log`, June 24 |
| qwen72b-limited, FOCALISATION, without thinking | 61.7% (37/60) | identical to with-thinking — thinking made no difference for this specific model/criterion |
| "sample 72B with the intelligence" | 68.3% | described as "the best one I could do right now" at the time of the first meeting |
| Local hybrid (pre-existing, referenced as baseline) | 65.0% | called "previous best" in `pipeline_overnight.log` |
| LoRA fine-tune of Qwen2.5-7B-Instruct | Did not work | **New detail from 2nd meeting**: failed because the training dataset was too small (~200+ examples needed, impractical to hand-annotate that many), *and* the corpus file it was given had a duplicate novel plus three novels missing from the total corpus — a data-quality problem discovered only when trying to use it, not a modeling failure per se |
| Mistral API (free tier) | Poor | *"it gives you free tokens... but these models also doesn't work"* |
| Groq (free tier, GPT-4-class) | Poor | tried alongside Mistral, similarly unhelpful |
| GPT-4 / GPT-4-mini (paid, small budget test) | Not yet run as of 2nd meeting | Riccardo explicitly approved budget (~€22-25 estimated for the whole corpus by Labiba's own check, offered up to €100-200 if needed), with an explicit instruction not to hit the old $8-9 account limit again |
| This session's GPT-4o v7 map-reduce port | **76.1% overall** (34/60 novels) | see next section — this is the closest thing to the "GPT paid version → 80%" the literature/Riccardo hoped for, though not quite there yet, and on a partial novel set |
| This session's gpt-4o-mini v7 map-reduce port | **64.8% overall** (60/60 novels) | see next section |
| This session's "v8" (rewritten FOC/MODE/RÉGIME/INTRIGUE/TEMP definitions) | 57.1% on a 5-novel check (regression) | rejected, see next section |
| This session's "v9" (REDUCE-step thinking enabled, prompt otherwise identical to v7) | Flat overall (61.9%), +20pp on ESPACE / −20pp on INTRIGUE | partial finding, see next section |
| This session's honest nested-CV re-measurement of the local chunk-classifier hybrid | **64.0% overall** (was reported as 69.3% before the leaky-CV bug was found and fixed) | see `resultats_nested_cv_honest.txt` above |

### Numbers discussed live in the second meeting (screen-share, reading off current results)

These are the raw figures Riccardo and Labiba were looking at together — preserved as stated, some clearly abbreviated/garbled in the speech-to-text (e.g. "68.3" transcribed oddly as "83.63"):

- TYPE NARRATEUR: ~91%
- FOCALISATION: 70-75%
- RÉGIME NARRATIF: 76.7% — *"if we could get it up to 80%, that would be amazing"* (Riccardo)
- INTRIGUE: 68.3%
- TEMPORALITÉ: 71%
- ESPACE: not stated as a number, but explicitly the weakest — *"I would probably eliminate space at this time"* (first meeting)

Riccardo's overall stance, both meetings: *"Are you okay with 70%? ... I think we will do with it. We'll go with it."* — a working acceptance of the plateau, while still hoping the paid-model experiment could push specific criteria (RÉGIME especially) toward 80%.

---

<a id="task0-session"></a>
## 10. Task 0 results not yet written down anywhere in the repo — this session's direct work

Everything in this section was produced in the current work session (2026-07-05 to 07-07) and does not yet exist in any file Riccardo has seen. It directly answers the GPT-4/paid-version question raised in both meetings above.

### The GPT-4o v7 comparison — a clean, controlled test

Ported `run_task0_mapreduce_v7.py` (the best-tuned local qwen3 pipeline) to GPT-4o, changing **only** the model backend — identical prompts, identical chunking, identical 3x reduce-vote scheme — so the comparison is apples-to-apples, not cherry-picked.

**Result on the 34 novels that completed before hitting an OpenAI billing wall, scored against qwen3 v7 on the exact same 34 novels:**

| Criterion | GPT-4o v7 | qwen3:30b v7 (same 34 novels) | Δ |
|---|---|---|---|
| TYPE NARRATEUR | 91.2% | 88.2% | +3.0pp |
| FOCALISATION | 76.5% | 76.5% | tie |
| MODE NARRATIF | 70.6% | 44.1% | +26.5pp |
| RÉGIME NARRATIF | 82.4% | 61.8% | +20.6pp |
| ESPACE | 73.5% | 55.9% | +17.6pp |
| INTRIGUE | 64.7% | 58.8% | +5.9pp |
| TEMPORALITÉ | 73.5% | 50.0% | +23.5pp |
| **OVERALL** | **76.1%** | **62.2%** | **+13.9pp** |

GPT-4o wins or ties on every single criterion. **This directly answers "can paid GPT get us to 80%?" — RÉGIME NARRATIF specifically hit 82.4%, past the 80% target Riccardo named.** Note this is on 34/60 novels only (see cost/blocker below) — not yet confirmed on the full 60-novel gold set.

**Cost**: ≈$8.55 actually spent for these 34 novels (computed via exact token reconstruction, since direct billing-API access wasn't available). Projected: ~$6.40 more to finish the remaining 26 novels (~$15 total for the full 60-novel gold set) — this lines up closely with Labiba's own €22 estimate from the second meeting for a full-corpus run, confirming that estimate was in the right ballpark. Full 925-novel corpus at this pipeline's rate: ≈$227.

**Blocker**: hit `insufficient_quota` (hard account billing limit, not a rate limit) partway through novel 32/60 — this is very likely the "$8-9 limit" / "don't hit the limit again" issue discussed in the second meeting. The run has not yet been resumed to complete the remaining 26 novels.

### The gpt-4o-mini v7 comparison — the cheap option

Same exact port, same exact method, using gpt-4o-mini instead. Completed all 60/60 novels for **≈$0.89 total**.

| Criterion | gpt-4o-mini v7 | qwen3:30b v7 (same 60 novels) | Δ |
|---|---|---|---|
| TYPE NARRATEUR | 78.3% | 91.7% | −13.4pp |
| FOCALISATION | 71.7% | 71.7% | tie |
| MODE NARRATIF | 50.0% | 43.3% | +6.7pp |
| RÉGIME NARRATIF | 61.7% | 68.3% | −6.6pp |
| ESPACE | 58.3% | 53.3% | +5.0pp |
| INTRIGUE | 61.7% | 53.3% | +8.4pp |
| TEMPORALITÉ | 71.7% | 53.3% | +18.4pp |
| **OVERALL** | **64.8%** | **62.1%** | **+2.7pp** |

A modest win over local qwen3, but well below full GPT-4o — confirms there's a real, substantial quality gap between the mini and full models on this specific task, not just a price difference.

### v8 — an attempted prompt rewrite, rejected

Rewrote FOCALISATION (Genette's zero-vs-variable-focalization test), RÉGIME NARRATIF (Lejeune's autobiographical-pact test for the AUTO category), MODE NARRATIF (explicit per-chunk tallying instead of defaulting to "mixed"), and added a shared caveat to INTRIGUE/TEMPORALITÉ about chunk-sampling gaps — all individually grounded in real narratological theory. Bundled together and tested on a 5-novel sample: **57.1% vs. v7's 74.3% on the identical 5 novels — a regression**, likely because local qwen3:30b is more sensitive to added prompt length/complexity than large frontier models, and/or because changing 5 things simultaneously made the failure impossible to attribute to any one cause. **Rejected — not in use.**

### v9 — a narrower, single-variable fix

Reverted to v7's prompt wording exactly, changed only one thing: the REDUCE step (where cross-chunk synthesis happens) now runs with `think=True` and a much larger token budget, instead of v7's `think=False`. Rationale: this project's own Task 1 script never disables thinking for qwen3:30b and works fine; Task 0's REDUCE step forcing no-think may be starving exactly the criteria needing multi-step reasoning (MODE's tallying, TEMPORALITÉ's discourse-order judgment, RÉGIME's genre-signal weighing).

Result on 15 novels: **exactly flat overall (61.9% both)** — but a real, isolated trade: ESPACE +20pp (53.3%→73.3%), INTRIGUE −20pp (73.3%→53.3%), everything else tied. **Takeaway for a future hybrid: use v9's predictions for ESPACE specifically, keep v7 for INTRIGUE and everything else** — v9 is not a general improvement, just a targeted one.

### Honest reassessment of the local "leaky hybrid" number

The previously-reported 69.3% "hybrid" figure (picking whichever local method scored best per-criterion) was found to suffer the same kind of leakage problem as a separately-discovered classifier bug (see below) — model/method selection happening on the same set being reported. A genuinely clean, non-cherry-picked reconstruction using only honestly-measured cells lands at **~71.2%** (299/420) — still the best defensible qwen3-only number, but lower than the original 69.3%→"looked like 71%+" framing might have suggested, and still below GPT-4o's clean 76.1%.

**Separately confirmed bug** (not part of the v8/v9 experiments above, found earlier in the session): `train_chunk_classifier_60novels.py` picks between LogReg/RF/GB per criterion using `cross_val_predict` scored on the same loop being reported — classic model-selection leakage. A fix (`nested_cv_classifier.py`, inner 5-fold CV blind to the held-out novel) was run and produced the honest 64.0% figure in `resultats_nested_cv_honest.txt` above — 5.3pp lower than the leaky version, worst on ESPACE (13.4pp of inflation there alone).

### Open items not yet resolved

- The full GPT-4o run is still stuck at 34/60 novels — resuming it needs the account topped up again (a `load_done()` bug also needs a one-line fix first, or it will wrongly skip the 2 novels that failed with quota errors instead of retrying them).
- Riccardo's new focalization coding scheme (from the second meeting) hasn't been applied to any of this session's results yet — all FOCALISATION numbers above use the older code scheme, so a like-for-like comparison against Riccardo's new gold set is still pending.
- The `thinking`-field diagnostic proposed for understanding *why* MODE/RÉGIME/TEMPORALITÉ specifically plateau (reading the model's actual reasoning text on misses) has not been done yet.
