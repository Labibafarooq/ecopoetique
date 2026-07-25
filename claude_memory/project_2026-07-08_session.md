---
name: project-2026-07-08-session
description: "2026-07-08 session, ended ~23:15 (Labiba going to sleep, autonomous orchestrator left running): Task 3 animal-side DONE; Task 0 v10 diagnosed overcorrection, v10b calibration queued in orchestrator; Task 2/4.5 redesigned (CMT chain + decision-tree) and re-running now under new prompts; Task 1 plantes running, ETA ~29h as of sleep time; full autonomous sequence script running unattended"
metadata:
  type: project
  originSessionId: 6573064a-0c60-4e94-8c42-332e3860cb06
---

Builds on [[project-task0-task1-status]] and [[project-meeting-notes]]. This file records what changed in the 2026-07-08 session specifically — check `~/ecopoetique/CLAUDE.md` and `task3_full_report.md` for the current canonical state, since both were updated today.

## Environment gotcha — no project-specific venv exists

There is no dedicated ecopoetique virtualenv/conda env. The scripts that need spaCy/polars/transformers (analyse_agentivite.py, extract_humains_multilingual.py, etc.) only run under `/home/lfarooq/digitize_medical_records/labelimg_env/bin/python3` — this happens to be the only environment on the machine with both `spacy` + `fr_core_news_lg` + `polars` + `transformers` installed (found by checking `site-packages` across all envs on the box). Plain `python3` / `pip3` at the system level has none of these. Use this env path for any future ecopoetique spaCy/polars work rather than re-discovering it.

## Task 3 — animal-side agentivity refresh (completed today)

This was the "Animal re-filtering" item from `task3_full_report.md`'s Known Limitations #4 / What Remains To Be Done. Full method and final numbers are now written into `task3_full_report.md` under "UPDATE — 2026-07-08" and into `CLAUDE.md`'s task table — **do not re-summarize from scratch, read those**. Key points worth remembering that aren't just "read the report":

- **A stdlib-`csv`-vs-`polars` parsing bug produced a false result first** (89.6% "Autre" instead of the correct ~20%): `dépendants_ANIMAUX.csv` contains Python-tuple-repr strings with embedded quotes that break stdlib `csv`'s quoting rules and silently shift fields. `analyse_agentivite.py` already avoided this by using `polars` — matching that library choice fixed it. **General lesson**: any script in this project reading `dépendants_*.csv` files must use `polars`, not stdlib `csv`, or verify very carefully.
- **A real coverage gap was found and closed**: `dépendants_ANIMAUX.csv` (built 2026-05-31, before Task 1 existed) never covered the "bestsellers" corpus subset at all (13,094 rows) and was short 2,243 rows even within corpus_principal. Closed by re-parsing those 15,337 rows with `fr_core_news_lg`, reusing the exact head/head-of-head logic from `extract_humains.py` + `scripts/get_token_dependencies.py` (note: `get_token_dependencies.py` as committed references model `fr_dep_news_trf`, which is NOT installed anywhere on this machine — only `fr_core_news_lg` is; the actual production dependency file was almost certainly built with `fr_core_news_lg`, matching `extract_humains.py`, not the model named in that script's source).
- **Final numbers**: animals 23.8% active agent / 0.8% passive / 21.5% object (86,082 référentiel mentions, 96% coverage) — barely moved from the old Joanna-manual-filter number (24.4%/0.7%/20.2%, N=95,243). Hierarchy Humans (37.2%) > Animals (23.8%) > Plants (11.8%) confirmed, not overturned.
- **New files**: `dépendants_ANIMAUX_missing_rows.csv`, `dépendants_ANIMAUX_COMPLET.csv` (127,681 rows, the new merged master), `dépendants_animaux_référentiels_REFRESH.csv` (86,082 rows, final référentiel-only file) — all in `~/ecopoetique/morphosyntaxe/`.
- **Only the plant side is left** for Task 3, same method, blocked until Task 1 plantes finishes.

## Task 1 plantes — GPU contention episode, 2026-07-08

While plantes was running (see [[project-task0-task1-status]] for baseline), a colleague **Martial de Jurquet** (`mdejurquet`) ran a GPU training job (`pipeline1/step3_final_training.py`, ~6.8GB) on the shared A40 from **07:05:12 to ~10:46:34 UTC (~3h41m)**, confirmed via his own world-readable logs at `/data/corpora/mdejurquet/classification_annotation/pipeline1/step3.log`/`step3_nohup.log`. It did NOT finish successfully — it crashed with `RuntimeError: expected scalar type Half but found Float` (an fp16/fp32 mixed-precision mismatch) right after completing Fold 1 Epoch 1's last batch. This measurably slowed Task 1 plantes throughput from 3.7s/row to 4.2-4.3s/row during that window — expected behavior matching the established "sustained GPU load slows Task 1" gotcha already in CLAUDE.md, not a bug in our own pipeline. **Server clock is UTC; user's local time is UTC+2** — worth remembering when discussing elapsed/ETA times with Labiba to avoid confusion.

## Task 3 human-names multilingual test — re-verified today

Re-ran the 5-novel test from the night of 2026-07-07 (using the correct `labelimg_env` python this time, after an initial attempt failed with plain `python3` due to missing `spacy`/`transformers`). Result was reproducible: 897 total rows (fr_model=811, multilingual_model=86 new names) — confirms the four bug fixes documented in CLAUDE.md (subword-splitting, one-sided truncation, animal/plant false positives, place-name false positives) are stable, not a fluke of the first run. Also found a 5th guard already in the code (`is_known_org`, checks against ORG entities like band names) not yet mentioned in CLAUDE.md's "four fixes" writeup — doc is stale on this point. Full 925-novel run (no new filters, per Labiba's call — she noted "Barbie"/"Petit Prince" flagged as residual gaps might actually be legitimate character names, not false positives) started today as background job, ETA ~33h.

## Task 0 — full v1-v9 local-model verification + TEMPORALITÉ/RÉGIME error analysis (2026-07-08)

Labiba asked for a clean, non-paid-GPT rundown of every local model/method tried on narratology (v1-v9) with best-per-category picks. Re-ran the repo's own `verify_hybrid_table.py` (existing verification script) plus a custom scan of every `resultats_*.csv` against the confirmed 60-novel gold set (loaded via `run_task0_mapreduce_v7_gpt4o_mini.load_gold`, semicolon-delimited `GOLD_narratologie.csv`) to get ground truth rather than trust recalled numbers from prior sessions — several of Labiba's own pasted notes from earlier sessions had drifted/conflicted (see below).

### Best local (non-GPT) method per criterion — verified against live files
| Criterion | Best method | Score | N |
|---|---|---|---|
| TYPE NARRATEUR | v3 mapreduce | 93.3% | 56/60 |
| FOCALISATION | v5 (single-shot, pre-mapreduce!) | **77.2%** | 44/57 — beats v7's 71.7%, a real find, but v5's file is missing 3 of the 60 gold novels |
| MODE NARRATIF | classifier (honest, nested CV) | 63.3% | 38/60 (raw/leaky was 70.0%, don't use raw) |
| RÉGIME NARRATIF | v3 mapreduce | 76.7% | 46/60 |
| ESPACE | v7 (confirmed at 60-novel scale); v9 hit 73.3% but only on 15 novels, unconfirmed at scale | 53.3% (v7) | 32/60 |
| INTRIGUE | v3 mapreduce | 68.3% | 41/60 |
| TEMPORALITÉ | v3 mapreduce (**live** re-run) | 68.3% | 41/60 — a "frozen" old file (`resultats_hybrid.csv`) shows 71.7% for the same criterion/novels because v3's own predictions have drifted since that file was generated; trust the live number going forward |
| Combined honest hybrid (mixed N, not a clean single fraction) | — | ~70.7-71.2% | close to the ~71.2% already in PROJECT_DOCUMENTATION.md |

**Lesson confirmed**: Labiba's own pasted historical notes from prior sessions contained real errors (RÉGIME's 75.0% was actually the classifier's score mislabeled as v3's; a TEMPORALITÉ figure of 66.7% couldn't be reproduced against any file at all) — **always re-verify pasted/recalled numbers against the live CSVs before reporting them**, per [[feedback-ecopoetique-experiments]].

### TEMPORALITÉ — found the likely root cause of the error rate
Confusion-matrix analysis on `resultats_qwen3_30b_mapreduce.csv` (v3, 60 novels): **15 of 19 errors (79%) are the single confusion gold=TEMP_LIN → predicted=TEMP_DIS.** Root cause found in `run_task0_mapreduce_v7.py`'s prompt: the TEMP_DIS trigger definition conflates "posture rétrospective" (narrative stance — extremely common in French first-person literary fiction) with actual story-order discontinuity. A retrospective narrator does not imply events are told out of chronological order, but the current rule treats reflective/retrospective tone in multiple chunks as sufficient to trigger TEMP_DIS on its own. **Proposed fix** (not yet applied): remove the retrospective-stance clause from the TEMP_DIS trigger; require an actual order violation (later time-marker before an earlier one, or genuinely separate timelines) as the necessary condition. Labiba wants this tested on a small sample (5-10 novels) before wider rollout — not yet done.

### RÉGIME NARRATIF — confusion pattern (weaker single fix, real precision/recall tradeoff)
Confusions: REG_REAL↔REG_AUTO (5 combined, biggest), REG_SPEC→REG_REAL (4, model under-triggers SPEC). The REG_AUTO trigger ("posture subjective et réflexive constante") is similarly loose — but `run_task0_mapreduce_v7.py`'s own code comments show this was a *deliberate* widening in v7 to fix v3's opposite bug (REG_AUTO used to be too narrow, requiring explicit authorial self-reference, and missed true autobiographical texts). So there's a genuine precision/recall tension already known to the project — tightening it back risks reintroducing the old miss-rate. Not yet resolved; RÉGIME fix was not reached before the session moved to the new gold-set files below.

## Riccardo sent two of the five blocking items today (2026-07-08) — check these first next session

Two brand-new files arrived, resolving 2 of the 5 items in CLAUDE.md's "Currently waiting on Riccardo for" list:

1. **`narratologie/GOLD_narratologie_0807.csv`** — the new Task 0 gold set annotated with the new FOCALISATION scheme. Verified: 80 rows, 79 unique novels, **all 60 of the confirmed gold-set novels are included** plus 19 new ones, **zero blank FOCALISATION values**. New FOCALISATION codes confirmed: `FOC_ELARG, FOC_MIXTE, FOC_REST, FOC_RFOC` (completely different from the old `FOC_INT/FOC_EXT/FOC_ZERO/FOC_VAR` scheme) — matches the "reader-vs-character knowledge" framework described in the meeting transcripts. Other criteria (NAR/MODE/REGIME/ESPACE/INTRIGUE/TEMPORALITÉ) use the same codes as before. **This unblocks Task 0 item #1** — a full FOCALISATION re-comparison against the new codes can now be run.
2. **`métaphore/schema_analogies_vivant_complet_0807.csv`** — formal definitions for Task 2. Contains **19 total categories**: the 16 original ones (already confirmed matching the script) plus the **3 previously-missing ones**: `COUL` (couleur, e.g. "vert pomme"), `LOC_IDIOM` (locution idiomatique, e.g. "avoir la chair de poule"), `IMAG` (représentation, e.g. "un tableau représentant un lion"). **This unblocks Task 2 item #2** (the 3 new category definitions) — combined with fixing Task 2's LLM-fallback bug (still open), Task 2 can now be run with all 19 categories properly defined.

3. **`métaphore/Catégories analyse comparés.docx`** — the Task 4.5 definitions file, previously nonexistent anywhere. Six categories, extracted in full:
   - **O** — Objets et structures artificiels (man-made objects/technological artifacts)
   - **NH** — Créatures non humaines vivantes et processus biologiques (animals, plants, biological processes in non-human living things)
   - **E** — Éléments naturels inanimés et processus naturels (landscapes, geological formations, weather, non-living natural world)
   - **CH** — Corps humain et processus biologiques (human body, physiological functions, biological processes)
   - **A** — Concepts abstraits (politics, religion, art, social institutions like marriage)
   - **P** — États psychologiques et fonctions cognitives (emotions, sensations, memory, imagination)
   **This unblocks Task 4.5 item #4.**

**Not yet done**: none of the three files have been used yet — the FOCALISATION re-comparison, the Task 2 LLM-path fix + full 19-category run, and building a Task 4.5 processing script (none exists yet) using these definitions are the natural next steps. CLAUDE.md's "Currently waiting on Riccardo for" list needs updating to remove items #1, #2, #4 (received today) — 2 items remain open (Task 2 gold blanks 69/200, Task 4.5 gold blanks 88/200 + scoring convention for 4 `?` rows). **3 of 5 blocking items cleared in a single day (2026-07-08).**

## Task 0 — full definitions comparison, old prompt vs. new official scheme (2026-07-08)

Compared all 7 criteria in `run_task0_mapreduce_v7.py`'s embedded `CRITERIA_DEFS` against the new canonical definitions in `narratologie/tableau_narratif_22_08 (1).csv` (the file Riccardo sent alongside the new gold set). Findings:

- **TYPE NARRATEUR, ESPACE, INTRIGUE**: unchanged, same codes and concepts.
- **MODE NARRATIF**: same 4 codes plus a genuinely new 5th official option, **MOD_DIA** (dialogue/polyphonie) — not yet observed in any novel in `GOLD_narratologie_0807.csv`'s 79 rows, but it's real and any updated prompt needs to offer it.
- **FOCALISATION**: completely different scheme (see below) — already known.
- **RÉGIME NARRATIF**: same 4 codes, but the new official REG_AUTO definition ("fondé sur l'expérience de l'auteur ou un double fictionnel") is meaningfully **narrower** than v7's current trigger ("ton confessionnel/réflexif soutenu... posture subjective et réflexive constante"). This directly explains the REG_REAL↔REG_AUTO confusion found in today's error analysis (5 combined misclassifications, the biggest single confusion pair) — v7's prompt is looser than Riccardo's actual definition and over-triggers AUTO.
- **TEMPORALITÉ**: same 3 codes, but the new official TEMP_DIS definition is "analepses ou prolepses **ponctuelles** mais significatives" (concrete, occasional flashback/flash-forward events) and **never mentions narrative stance or retrospection at all.** This directly confirms the root-cause diagnosis from today's confusion-matrix analysis (79% of TEMPORALITÉ errors are gold=TEMP_LIN→predicted=TEMP_DIS) — v7's prompt added a "posture rétrospective" trigger that isn't in Riccardo's actual definition, and that's almost certainly the whole bug.

**Implication**: fixing RÉGIME and TEMPORALITÉ isn't just a proposed tweak anymore — it's now backed by comparing against Riccardo's own canonical definitions, not just error-pattern guessing. Both should be corrected to match `tableau_narratif_22_08` exactly, and MODE NARRATIF's prompt needs MOD_DIA added as a 5th option even though it hasn't appeared in the sample yet.

### Full new FOCALISATION definitions (reader-vs-character knowledge framework)
- **FOC_RFOC** (récit focalisé): narrative centers on one/more characters, reader shares their information — privileged access to what they perceive/think/know
- **FOC_REST** (restreinte): reader knows **less** than the characters — partial/delayed info, creates mystery/curiosity
- **FOC_ELARG** (élargie): reader knows **more** than the characters — dramatic irony, allows anticipating events the characters don't know about
- **FOC_MIXTE**: structured alternation between multiple focalization regimes across chapters/voices/narrative blocks

### New gold set coverage check
`GOLD_narratologie_0807.csv`: 79 novels, all 60 of the confirmed original gold-set novels + 19 new ones. Checked existing v3/v7 prediction files against it: **only 3 novels are missing** from existing predictions (`Werber-Bernard_Nous-les-dieux.txt`, `Tesson-Sylvain_La-panthere-des-neiges.txt`, `Houellebecq-Michel_Soumission.txt`) — so re-scoring the 6 unchanged criteria against the larger gold set is cheap (just needs those 3 novels run), while FOCALISATION needs an entirely fresh prompt + full 79-novel run since no existing prediction file uses the new codes at all.

**Decision (2026-07-08)**: focus on FOCALISATION first, using the new definitions above and `GOLD_narratologie_0807.csv` as gold — validate on a small sample before running all 79, per established workflow. Not yet started as of this memory save.

## Riccardo's email reply (2026-07-08) on Task 2/4.5 gold-set blanks — verified against the actual file

Riccardo emailed clarifying the remaining 2 open items (Task 2/4.5 gold blanks). Checked his claims directly against `comparison/gold_task2_task45_RB.csv` (200 rows):

- **72 rows are marked `X`/`x`** (across `subcategorie_metaphore`, `categorie_compare`, or `notes`) — per Riccardo, these were wrongly classified as figurative by Task 1 in the first place and should be **replaced with freshly-drawn figurative samples once Task 1 (plantes) finishes** — not annotated, by design.
- **Blank `categorie_compare`**: 7 IMAG rows are ALL blank (Riccardo confirmed IMAG has no compare-target, e.g. "a painting of a lion" isn't comparing anything). But found **15 more blanks not explained by IMAG or X** — mostly `LOC_IDIOM` (9 rows, makes sense: idioms like "avoir la chair de poule" don't have a compare-target either, same logic as IMAG) plus a couple `COUL` and one `META_VERB`. **One row (id 56) has both columns entirely blank and isn't X-marked or IMAG — genuinely unexplained, needs to go back to Riccardo.**
- **4 rows have `categorie_compare == "?"`** — Riccardo said "maybe exclude," tentative — get final confirmation before locking the scoring convention.

**Next steps, not yet done**: wait for Task 1 plantes to finish → redraw the 72 X-marked rows; build Task 2/4.5 scoring logic that treats IMAG/LOC_IDIOM/COUL/META_VERB blanks as legitimate N/A rather than missing; exclude the 4 `?` rows (pending final confirmation); flag row id 56 back to Riccardo.

## Task 0 — FOC/RÉGIME/TEMPORALITÉ fix script built and testing (2026-07-08)

Built `narratologie/run_task0_foc_reg_tem_fix.py` — a copy of `run_task0_mapreduce_v7.py` with exactly 3 of 7 criteria's definitions corrected to match Riccardo's canonical `tableau_narratif_22_08` file; NAR/MODE/ESPACE/INTRIGUE are untouched (verbatim from v7), isolating the 3 that actually drifted:

1. **FOCALISATION**: new reader-vs-character-knowledge scheme (FOC_RFOC/FOC_REST/FOC_ELARG/FOC_MIXTE), replacing old whose-consciousness codes (FOC_INT/EXT/ZERO/VAR) entirely. New MAP-step signal added: `reader_vs_character_knowledge` (same_as/less_than/more_than characters).
2. **RÉGIME NARRATIF**: REG_AUTO trigger tightened to require a concrete link to the author's real life (explicit reference or clear biographical resemblance across multiple sections) — not just a reflective/introspective tone, per canonical def and the REG_REAL<->REG_AUTO confusion found earlier today.
3. **TEMPORALITÉ**: TEMP_DIS's "posture rétrospective" trigger removed entirely — now requires a concrete, locatable flashback/jump (`flashback_or_jump_in_section=yes`) or an actual time-marker order contradiction, matching canonical "analepses ou prolepses ponctuelles."

Points at the new gold set (`GOLD_narratologie_0807.csv`, 79 novels). Output: `resultats_task0_foc_reg_tem_fix.csv`.

**Status as of this memory save**: 5-novel validation test launched in background (`test_foc_reg_tem_5.log`), not yet complete — results not yet known. Per established workflow, do NOT scale to the full 79 novels until this small-sample result is checked and confirmed reasonable. NAR/MODE/ESPACE/INTRIGUE were deliberately left alone this pass since they already matched Riccardo's canonical definitions — no need to re-run those against qwen3, only re-score existing v3/v7 predictions against the new gold set (cheap, only 3 novels — `Werber-Bernard_Nous-les-dieux.txt`, `Tesson-Sylvain_La-panthere-des-neiges.txt`, `Houellebecq-Michel_Soumission.txt` — are missing from existing prediction files and would need a fresh run).

## Task 0 v10 — full 20-novel run, diagnosed overcorrection, v10b calibration applied (2026-07-08, later in session)

Ran `run_task0_v10_foc_reg_tem.py` fresh (stripped to only FOC/RÉGIME/TEMPORALITÉ, per Labiba's explicit instruction — NAR/MODE/ESPACE/INTRIGUE dropped entirely, not just left unchanged) on all 20 novels. **Result: 55.0% overall (33/60)** — FOCALISATION 55.0%, RÉGIME 60.0%, TEMPORALITÉ 50.0%. **Below the 60% auto-scale threshold Labiba set**, and not clearly better than the pre-fix baseline (RÉGIME/TEMPORALITÉ both came in lower than their old v3/v7 numbers, though on a different/larger novel set so not perfectly apples-to-apples).

**Confusion-matrix diagnosis found a classic overcorrection pattern in all three** — each fix correctly killed the original bias but swung too far the other way:
- FOCALISATION: 7/9 errors are FOC_ELARG→FOC_RFOC (now under-detecting dramatic irony)
- RÉGIME: now REG_FANT(3x)/REG_AUTO(2x)/REG_SPEC(2x)→REG_REAL (opposite of the original REAL→AUTO over-triggering — tightening REG_AUTO and dropping the non-human-narrator FANT signal went too far)
- TEMPORALITÉ: 9/10 errors are TEMP_DIS→TEMP_LIN (exact mirror of the original TEMP_LIN→TEMP_DIS bug — the fix now under-triggers DIS)

**v10b calibration applied** (in `run_task0_v10_foc_reg_tem.py`, same file, loosened back toward center — NOT reverted to originals): FOC_ELARG no longer needs majority-of-sections support (one clear uncontradicted signal wins); RÉGIME's REG_AUTO now needs only one concrete uncontradicted section (not multiple), FANT's non-human-narrator signal reinstated as a *supporting* (not sole) cue, SPEC accepts partial-world transformation; TEMPORALITÉ's TEMP_DIS keeps the concrete-flashback trigger but adds a secondary path (multiple retrospective sections with non-linear time-markers). Output now points to `resultats_task0_v10b_calibrated.csv` (fresh file, old `resultats_task0_v10_foc_reg_tem.csv`/`resultats_task0_focalisation_new.csv` results are stale/superseded). **Not yet tested** — queued behind Task 1 priority.

## Task 2 and Task 4.5 gold validation (2026-07-08)

Built `métaphore/validate_task2_gold.py` (new, gold-only validator, doesn't touch the 23,327-row full corpus file) and reused the already-fixed `comparison/run_task45_compare_category.py`. Results against gold:

- **Task 2: 40/86 = 46.5%.** Method breakdown is the real finding: **rule-based path scored 16.7% (2/12) — worse than chance** — the surviving regex heuristics (META_ATTR "est un/une X", DE_PARANGON, DE_QUANTIF, META_JUXT) are net-harmful. LLM path alone: 51.4% (38/74). Confusion clusters in structurally-adjacent category pairs: META_ATTR↔META_APP↔META_JUXT (all "metaphor without comparative word" variants), DE_PARANGON↔DE_PROP (both "N de N"). **15% (13/86) came back UNKNOWN** — worth investigating separately, not yet done.
- **Task 4.5: 66/104 = 63.5%**, up substantially from ~30% pre-fix — the tenor/vehicle prompt rewrite genuinely helped. Residual CH↔NH confusion (6x) is the same original bug pattern, just reduced not eliminated. New pattern emerged: P→CH (6x), A→CH (5x) — model defaults to CH (human body) as a catch-all when actually unsure between CH/P/A. 7/104 also came back UNKNOWN.
- **Neither hits Labiba's 75-80% bar for scaling to a full run.**

### Literature research + redesigns applied (not yet tested)

Web search found directly-applicable technique for Task 4.5: **CMT (Conceptual Metaphor Theory) sequential-question prompting** (arxiv 2502.01901) — asking source-domain→target-domain→differ-check as separate explicit steps instead of asking for the answer directly reached F1 up to 82.59 on a comparable task. Combined with tenor-vehicle-ground extraction (arxiv 2010.05633: validate via the shared "ground" property before classifying).

**Task 4.5 redesigned**: `run_task45_compare_category.py`'s prompt now forces the model through 5 explicit JSON fields in order — `vehicule` (literal meaning) → `cible` (real-world referent in context) → `fondement_commun` (shared property/ground) → `verification` (do vehicle/target actually differ) → `code` (classify the CIBLE, not the vehicule). `call_ollama()` updated to capture all four reasoning fields into the `raison` column for audit. Not yet tested.

**Task 2 redesigned**: `run_task2_subcategories.py` — (1) **added the 3 missing categories** (COUL, LOC_IDIOM, IMAG — Labiba caught that these were missing from the 16-category version, now 19 total, matching `schema_analogies_vivant_complet_0807.csv` exactly), (2) **removed the 4 rule-based heuristics that scored 16.7%** (META_ATTR/DE_PARANGON/DE_QUANTIF/META_JUXT regexes) — kept only COMME_SI/COMP_DEG/MOD_ANALOG (genuinely unambiguous fixed phrases), (3) **restructured the LLM prompt from a flat 19-way pick into a sequential 14-step decision tree** mirroring how a linguist would actually parse the sentence (same technique that fixed Task 0's RÉGIME NARRATIF; matches literature on MIPVU rule-script/decision-procedure prompting, arxiv 2603.10784) — LOC_IDIOM/COUL/IMAG checked first (since they override the normal structural analysis), then COMME_*, then DE_*, then META_*. `validate_task2_gold.py` will automatically pick up the new 19 codes and the ~114-row usable gold set (up from 86) next run since it imports `VALID_CODES` dynamically. Not yet tested.

Both syntax-verified, neither run yet — queued for after Task 1, per Labiba's explicit "fix but don't run" instruction each time.

## Task 1 — restarted twice today, root cause of speed drift identified

**First restart** (~16:11, to pick up the `num_ctx` fix): found and fixed a genuine O(n²) resume-scan bug in `run_task1_corpus.py` while doing it (linear scan through all 69K rows per already-done row — ~1.3 billion comparisons, would have hung indefinitely at this scale) — fixed to an O(1) dict lookup. This bug was latent the whole time; only surfaced because this was the first-ever restart of this particular run.

**Speed recovered to 3.8-3.9s/row baseline** after the restart + stopping our own concurrent Task 3 CPU job — confirmed via live monitoring, trend: 5.0→4.8→4.4→4.3→4.1→4.0→3.9s/row.

**Speed drifted back up to 4.5-4.6s/row later** (by ~22:53) even with zero other GPU/CPU jobs of ours running. Root cause investigated and found: **a colleague's CPU job (`step4_alignment.py`, PID 2901956) has been growing its own CPU usage over the course of the day** — measured ~51 cores (5116%) around 16:36, up to ~56 cores (5603-5604%) by 22:53, consistently sampled 3x to confirm it wasn't a fluke. This is external contention outside our control; not a sign of anything wrong with our own process (checked: no memory/resource buildup in Task 1's own process or its Ollama runner).

**Second restart** (~22:57, at Labiba's explicit request despite this diagnosis — she wanted to try it anyway): confirmed resumed correctly, no data loss (43,634 rows preserved, 25,680 remaining, ETA ~28h at that point). As predicted, a restart doesn't fix externally-caused CPU contention — this was done on request, not as a technical recommendation.

## End-of-session state (2026-07-08 ~23:15) — Labiba going to sleep, autonomous orchestrator left running

**Read this section first if picking up cold.** Everything below was true as of ~23:15; check live logs before trusting exact numbers since an unattended script is actively progressing through several steps.

### What's running unattended: `~/ecopoetique/orchestrate_task0_after_2_45.sh`
Launched ~23:11, background job (task ID `bwcbw3irw`, log `~/ecopoetique/orchestrator.log`). Plain sequential bash script, no branching, does exactly this in order and CANNOT skip ahead:
1. Poll (every 30s) `métaphore/task2_decisiontree_run.log` for a `^Final:` line (Task 2 gold validation, decision-tree prompt)
2. Then poll `comparison/task45_cmt_run.log` for a `^Final:` line (Task 4.5 gold validation, CMT-chain prompt)
3. Then run `narratologie/run_task0_v10_foc_reg_tem.py --test 20` synchronously (v10b calibration, fresh 20-novel test) → `narratologie/test_v10b_20.log`
4. **Only after step 3 finishes**: find Task 1's PID via `pgrep -f "run_task1_corpus.py --category plantes"`, kill it, wait 3s, relaunch it (`nohup ... >> resultats/task1_plantes_run.log`)

**Labiba was explicit: do not stop Task 1 before step 4.** The script's linear structure enforces this — there's no way for step 4 to run before steps 1-3 complete since it's a plain top-to-bottom script.

**Why Task 1 gets restarted at all**: purely at Labiba's request after seeing speed drift (4.1→4.5s/row) that was actually caused by a colleague's CPU job (`step4_alignment.py`) growing over the day — restarting doesn't fix external CPU contention (already explained to her), but she wanted it done anyway once the orchestrator's other steps finish.

### UPDATE while Labiba asleep — Task 4.5's CMT-chain redesign REGRESSED, not improved

Task 4.5 finished (background job completed independently of the orchestrator's polling — it was launched as a direct job, the orchestrator just watches its log for a `Final:` line). **Result: 41/104 = 39.4% — WORSE than the pre-redesign 63.5%.** The 5-step CMT vehicle→target→ground→verify→classify chain, despite being backed by the literature (arxiv 2502.01901's F1 82.59 claim), backfired badly here. Contradicts the literature's finding for this specific task/setup — worth investigating why before trusting CMT-style chains again: possibly the extra steps introduce more chances for the model to talk itself into the wrong tenor, or the JSON schema with 5 fields is harder for qwen3:30b to fill in correctly than the literature's presumably larger/different model. **Do NOT scale this to a full run — it needs to be reverted or re-diagnosed, not deployed.** Old (better) prompt's results are preserved in `resultats_task45_compare_category_OLDPROMPT.csv.bak` (63.5%) for comparison/possible revert.

Task 2's decision-tree redesign, by contrast, finished as a modest real improvement: **final 59/114 = 51.8%** (vs. old flat-prompt's 46.5% on 86 rows — note larger N now since 19 categories included). Smaller gain than hoped, but genuine, not a regression. Orchestrator confirmed both jobs done at 2026-07-09 00:41:09 and moved to step 3 (Task 0 v10b, 20-novel test) — in progress as of this note.

### Snapshot of the 3 running/queued jobs at sleep time
- **Task 1 (plantes)**: 43,734/69,314 (63.1%), 4.1s/row, ETA ~28.9h at last check — untouched all evening, healthy
- **Task 2 gold validation (NEW decision-tree prompt, 19 categories incl. COUL/LOC_IDIOM/IMAG)**: running, 10/114 done, **7/10 correct (70.0%) early** — a good sign vs. the old flat-prompt result (46.5%), but very early/small sample, don't trust yet
- **Task 4.5 gold validation (NEW CMT vehicle->target->ground->verify->classify chain)**: queued behind Task 2 on the shared Ollama slot, hasn't started actual LLM calls yet as of sleep time. Old prompt's 104-row result (63.5%) was backed up to `resultats_task45_compare_category_OLDPROMPT.csv.bak` before this run started fresh (same for Task 2 old-prompt results -> `resultats_task2_gold_validation_OLDPROMPT.csv.bak`)
- **Task 0 v10b**: not started yet, waiting in the orchestrator queue (step 3)

### What to check first when Labiba is back
1. `cat ~/ecopoetique/orchestrator.log` — see how far the sequence has progressed, and whether it hit any error (script uses `set -e`, so it will stop early on any command failure rather than silently continuing — if it's not still running and hasn't logged "Orchestration complete", something failed partway)
2. If still mid-Task-2 or mid-Task-4.5: check those logs directly for live progress
3. If it reached Task 0 v10b: check `narratologie/test_v10b_20.log` for the calibration result — this answers whether loosening FOC/RÉGIME/TEMPORALITÉ back toward center fixed the overcorrection found earlier today (v10 scored 55.0%, below the 60% threshold)
4. If it reached the end: Task 1 should show a *third* restart in its log around whenever step 3 finished — verify it resumed correctly (same pattern as the first two restarts: "Resuming: N rows already done" should appear, not a restart from 0)

## File-encoding gotcha, repeated today
`Catégories analyse comparés.docx` and other accented filenames sometimes fail a literal-quoted `ls "filename"` / direct path match despite visibly existing in `ls -la` output — same root cause as the earlier `tête`/`tête_de_tête` CSV column-name encoding issue (precomposed vs decomposed Unicode accents from different upload/scp sources). **Fix**: use a shell glob (e.g. `Cat*.docx`) instead of typing the accented name literally when a direct path access unexpectedly 404s on a file you can see in a directory listing.
