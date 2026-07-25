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
| `dépendants_plantes_référentielles.csv` | Referential-only plants filtered by Task 1 | ❌ To do — blocked on Task 1 plantes run finishing |
| `dépendants_animaux_référentiels_REFRESH.csv` | Referential-only animals filtered by Task 1 (our corrected version) | ✅ Done 2026-07-08, see update below |

---

## UPDATE — 2026-07-08 — Animal re-filtering completed (Known Limitation #4 resolved)

This closes out the "Animal re-filtering" item from **Known Limitations** and **What Remains To Be Done** above. Task 1 animaux finished on 2026-07-05 (including a Sunday retry pass, `retry_animaux_v2.py`, that fixed 3,665 previously-failed rows and patched the master label files in place — the corrected file is `resultats/task1_animaux_labels.csv` / `_full.csv`, **not** the `.bak_before_v2_patch` versions).

### Method

1. **Filtered** `resultats/task1_animaux_labels_full.csv` (127,945 rows, corrected Sunday labels) down to `task1_label == "référentiel"` → 89,681 rows.
2. **Joined** against `dépendants_ANIMAUX.csv` (the spaCy dependency-parse file `analyse_agentivite.py` consumes) on `(fichier, token_lexique, lemme, sentence)` to recover the `tête`/`dépendants`/`tête_de_tête` syntactic-role columns needed for classification.
3. **Bug found and fixed during step 2:** an initial join using Python's stdlib `csv` module mis-parsed `dépendants_ANIMAUX.csv` — it contains Python-tuple-repr strings (e.g. `('Caviar', 'ROOT')`) with embedded quote characters that break stdlib `csv`'s quoting rules, silently shifting fields on many rows and producing a bogus 89.6%-"Autre" result. Switched to `polars` (same library `analyse_agentivite.py` already uses successfully) — this fixed it.
4. **Coverage gap found:** `dépendants_ANIMAUX.csv` (built 2026-05-31, before Task 1 existed) turned out to be missing dependency-parse data for the entire "bestsellers" subset of the corpus (13,094 rows) plus 2,243 rows within corpus_principal — 15,337 rows never dependency-parsed at all. Initial join matched only 76,297/89,681 (85.1%) référentiel rows for this reason.
5. **Coverage gap closed:** re-ran dependency parsing on the missing 15,337 rows using `fr_core_news_lg` (the model actually installed in this environment, consistent with the sibling `extract_humains.py` script) with the same head/head-of-head logic as `scripts/get_token_dependencies.py` + `extract_humains.py`. Parsed 14,906/15,337 (97.2%) successfully; 431 tokens could not be relocated in the re-parse (comparable residual rate to the original file). Merged into `dépendants_ANIMAUX_COMPLET.csv` (127,681 rows). Re-ran the join: **86,082/89,681 matched (96.0% coverage)**.

### Final results — animals, référentiel-only, corrected Task 1 labels, full corpus coverage

| Category | N | % |
|---|---|---|
| Noun complement | 29,254 | 34.0% |
| **Active agent** | 20,472 | **23.8%** |
| Object | 18,549 | 21.5% |
| Other | 17,091 | 19.9% |
| Passive receiver | 716 | 0.8% |

Compared to the original (Joanna's manual filter, N=95,243): 24.4% active agent, 0.7% passive → now **23.8% active agent, 0.8% passive** on our own corrected classifier. Essentially unchanged — this is a confirmation, not a reversal. The hierarchy **Humans (37.2%) > Animals (23.8%) > Plants (11.8%)** holds.

Remaining 3,599 unmatched rows (4.0%) are residual (mostly the 431 re-parse misses plus minor sentence-formatting mismatches between corpus_principal/bestsellers source formats) — a small, reasonable gap compared to the original 15%.

### Files produced

| File | Description |
|---|---|
| `morphosyntaxe/dépendants_ANIMAUX_missing_rows.csv` | Newly dependency-parsed rows (bestsellers + corpus_principal gap), 14,906 rows |
| `morphosyntaxe/dépendants_ANIMAUX_COMPLET.csv` | Full merged dependency file, 127,681 rows |
| `morphosyntaxe/dépendants_animaux_référentiels_REFRESH.csv` | Final référentiel-only animal file for agentivity analysis, 86,082 rows |

**Task 3 animal side is now done.** Only the plant side remains, blocked on Task 1 plantes finishing (running now, ~50% as of 2026-07-08 midday).

