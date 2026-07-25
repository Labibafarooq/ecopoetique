---
name: project-2026-07-10-session
description: 2026-07-10 session — Task 1 fully complete (animaux+plantes, all 3 gold sets audited, 13 confirmed gold mislabels found), Task 3 fully investigated (no gold set exists, plantes coverage gap fixed, humans bestsellers gap discovered unfixed), Task 2 LOC_IDIOM over-triggering diagnosed+fixed, Task 4.5 CH/P/A confusion diagnosed+fixed (77.9% before 2nd fix), Task 0 extensive gold-set archaeology (two non-comparable gold sets, full v1-v9 hybrid tables built both ways), three reports written
metadata:
  type: project
  originSessionId: 0c40159e-c731-4cf6-a5e9-6c51ee541de1
---

Builds on [[project-2026-07-09_session]], [[project-2026-07-09_session2]], [[project-task0-task1-status]]. Read `~/ecopoetique/CLAUDE.md` fresh — likely updated by a parallel session.

## Task 1 — FULLY COMPLETE (animaux + plantes), full audit done

Plantes finished 2026-07-10 07:28 (19.8h run) + 2 retry passes (376/444, then 36/68 resolved) — **32 rows permanently unresolved**, 0.05% of corpus, in `resultats/task1_plantes_failed_keys_v3.tsv`. Final: 69,468 rows, 59,967 référentiel / 9,501 figuré (13.7%).

**Gold-set accuracy, all 3 sets, verified against live production output** (not cached numbers):
| Gold set | Raw accuracy | Ref acc | Fig acc |
|---|---|---|---|
| Animaux | 90.1% (154/171) | 96.3% | 79.0% |
| Plantes | 96.8% (180/186) | 99.4% | 79.2% |
| Loterre | 85.2% (161/189, from `eval_loterre_v8_results.csv` — NOT current production prompt) | 91.2% | 63.4% |

**Manually audited all 33 rows where gold=figuré but model said référentiel**, full context read for each. Found **13 confirmed gold-set mislabels** (model was actually right): animaux 3 (chiens, pattes de lion ×2 — matches the "boiserie chêne" material-term precedent), plantes 3 (jasmin, palmiers, ananas — all literal), Loterre 7 (forêt, mers, océan, lac ×2, plage, animaux — real geographic features used literally). 4 more borderline (porc, abricotier, désert, incendie) — genuine judgment calls, not counted as errors either way. **Corrected accuracy**: Animaux 91.8%, Plantes 98.4%, Loterre 88.9%.

Also did **100-random-sample manual spot-checks** (50 fig + 50 ref) for both animaux and plantes independent of gold sets — 90/100 and 92/100 clean respectively, corroborating gold numbers. Found recurring patterns: homograph collisions (grenadier=soldier not tree, oedipe=complex not monkey), inconsistent handling of representations (teddy bear→figuré correct per Riccardo's IMAG ruling, but glass figurine/painting/photo of animals wrongly stayed référentiel — same representation logic not applied consistently).

**Report**: `~/ecopoetique/TASK1_FINAL_REPORT_2026-07-10.md` — supersedes `task1_report.md` (June 28).

## Task 3 — fully investigated, confirmed NO gold set exists (verified from transcript, not assumed)

**Explicit transcript confirmation** (second meeting, ~line 529-530), Riccardo looking at `dépendants_HUMAINS.csv` on screen: *"So you didn't have a gold set for this?" / "No, I made it myself because it didn't give me the gold set for humans and I just ran it."* Searched both full transcripts exhaustively for every "gold" mention — nothing else references a Task 3 gold set (role classification or names). Labiba later clarified this specific quote was about the human **names** check only, not active/passive/etc — re-searched specifically for a role-classification gold set too, found none anywhere (transcripts or filesystem).

**Plantes coverage gap found and fixed**: `dépendants_PLANTES.csv` (built May 31, pre-dates Task 1) was missing the entire bestsellers subset (0/87 files) + 2,756 corpus_principal rows — same structural bug the animaux refresh fixed on 2026-07-08. Installed spaCy (`pip install --user --break-system-packages`) + `fr_core_news_lg` model (had vanished from the environment since the last session — no venv exists in this project, packages must be reinstalled each fresh environment). Re-parsed 7,516 missing rows (`morphosyntaxe/reparse_plantes_missing.py`, new script, same head/head-of-head logic as `extract_humains.py`/`get_token_dependencies.py`) — 99.7% match rate, ~60 rows/sec on CPU. Merged into `dépendants_PLANTES_COMPLET.csv` (71,764 rows). Re-joined against référentiel-only plantes → **97.8% coverage** (up from 87.3%), final `dépendants_plantes_référentiels_REFRESH.csv` (58,637 rows). Task 3 plantes final: Agent actif 11.1%, Passif 0.4%, Objet 15.4%, Complément 50.8%.

**New finding, not previously caught**: `dépendants_HUMAINS.csv` (built 2026-06-22) has the **exact same gap for humans, never fixed** — `extract_humains.py`'s `CORPUS_DIR` only points at `CORPUS_TOTAL` (925 novels), never `CORPUS_Bestsellers` (88 novels) — confirmed 0/88 bestsellers files present. The headline 37.2% human active-agent number is unverified against ~9% of the corpus. Not yet fixed — same treatment as plantes/animaux is the obvious next step.

**Manual spot-check (45 rows, 3 per role × 5 roles × 3 populations)** found animaux/plantes clean, but a real issue in humans: all 3 sampled "Récepteur passif" rows (Jésus/blond, Charles/assis, Dan/gêné) are être+adjective predicates, not real passive voice. Checked systematically — top head words for all 3,103 human "passive" rows are dominated by être-auxiliary intransitive verbs (morte, assis, restée, venue, allé, né, devenue...) — likely most of the 1.4% "passive" figure for humans is this parsing artifact, not genuine passive voice. Needs a morphology-based fix before being cited officially.

**Multilingual names**: confirmed still only 72/925 novels done (7.8%), paused, not resumed. Pulled the actual 533 unique multilingual-only names from that partial run and found concrete extra false-positive examples beyond the already-documented Nirvana/Petit Prince/Barbie: common nouns (Tordu, Mauvais, Cicatrice, Dieu), fictional characters (Tintin, Yoda, Don Quichotte), brand/org names (Chanel, Tsahal, Libé), tokenization artifacts (hyphenation breaks).

**Report**: `~/ecopoetique/TASK3_FINAL_REPORT_2026-07-10.md`.

## Task 2 — LOC_IDIOM few-shot examples: real mixed result, root cause found, fixed, re-testing

Resumed the interrupted gold validation (114 rows) — finished at **64.9% (74/114)**, up from 57.7% pre-reorder/pre-few-shot baseline. But diagnosis of the 40 wrong rows found the few-shot idiom examples added last session are a **mixed result**: LOC_IDIOM recall jumped 66.7%→86.7% (genuinely catches more real idioms) but precision dropped 66.7%→56.5% (false positives doubled 5→10). Read full context on all 10 false positives — they cluster into 4 clean patterns: (A) fixed animal-expression attributing a trait to a person should be META_ATTR not LOC_IDIOM (brebis égarée ×2, faire les ânes), (B) compound color idiom should be COUL not LOC_IDIOM (poivre et sel ×2), (C) live "comme" simile where animal still evokes real action should stay COMME_SN, not LOC_IDIOM (tirer comme des lièvres, tomber comme des mouches — this exact confusion was already flagged BEFORE the few-shot fix and persisted through it), (D) representation/symbol context should be IMAG (eau de rose re: photos, fleurs de lis on a flag).

**Root cause**: LOC_IDIOM is question 1 in the decision tree (checked before COUL/IMAG/COMP_DEG/COMME_SN/META_ATTR), so the model locks in LOC_IDIOM before ever reaching the more-specific correct question. **Fix applied**: added an explicit 4-case exclusion clause to question 1 in `métaphore/run_task2_subcategories.py`, redirecting each pattern to its correct question number. Re-test launched (`task2_gold_validation_v5_locidiom_fix.log`), not finished as of this memory save.

## Task 4.5 — CH/P/A disambiguation: fixed once, found a second real bug, fixed again, re-testing

Resumed the interrupted validation (104 rows, was 10/104 from 2026-07-09) — finished at **81/104 = 77.9%**, a huge jump from the pre-truncation-fix 39.4%, and beats the old pre-redesign baseline of 63.5%. Real, confirmed win from the truncation fix.

But read all 23 wrong rows in full and found the CH/P/A disambiguation clause (added 2026-07-09) didn't fully solve the "model defaults to CH" bug — 10/23 errors are still CH-related. Two clean, fixable patterns: (1) **6 rows** — animal-based character/personality traits (stubborn, cruel, vile, agile, dual-role) wrongly default to CH instead of P, even though CH's definition is strictly physiological, not personality; (2) **2 rows** — voice/song/artistic-expression metaphors wrongly default to CH instead of A (art), since voice mechanically involves the body but the metaphor is about aesthetic quality. 5 more rows looked like genuinely questionable gold labels (pâquerettes/lichen/fougère's own stated "cible" text explicitly names art/emotion/thought — none of which match CH — yet gold says CH), flagged for a second annotator opinion rather than "fixed."

**Fix applied**: added two explicit clarifying rules ("Piège fréquent n°1/n°2") to the CH/P/A section of `comparison/run_task45_compare_category.py`. Re-test launched (`task45_gold_validation_v4_chpa_fix.log`), not finished as of this memory save.

## Task 0 — extensive gold-set archaeology, two non-comparable gold sets fully mapped, v10c experiment

User repeatedly pushed back on inconsistent historical numbers (correctly) — did a full, careful re-verification rather than trusting pasted/remembered tables. **Key finding, verified directly (code-vocabulary diff between gold files)**: only FOCALISATION changed completely between the old 60-novel gold (`GOLD_narratologie_60novels_original.csv`) and current 79-novel gold (`GOLD_narratologie_0807.csv`) — old scheme FOC_INT/EXT/ZERO/VAR vs new FOC_RFOC/ELARG/REST/MIXTE, totally different framework, not just renamed. TYPE NARRATEUR gained 2 new codes (NAR_AUTO, NAR_VAR) used on only 3/79 novels — 97% comparable. MODE NARRATIF's proposed MOD_DIA category exists in the schema doc but is used on **zero** of the 79 currently-annotated gold novels — not actually active yet. RÉGIME/ESPACE/INTRIGUE/TEMPORALITÉ are identical code vocabularies (individual novel labels can still be corrected between file versions though — found one real example: `Bienne-Gisele_La-malchimie.txt` ESPACE went ESP_UNIT→ESP_FRAG).

**Traced two specific "remembered number" disputes to ground truth, both real, both explainable**:
- v5's FOCALISATION 77.2% (44/57) — real, but scored under the OLD scheme (verified directly: v5's file contains `FOC_INT`/`FOC_ZERO` codes) — not comparable to current gold, cannot be cited going forward.
- v9's ESPACE 73.3% (11/15) — real, but from `GOLD_narratologie_60novels_original.csv` specifically; scores 66.7% against current gold, because exactly one novel's ESPACE label was corrected between file versions (found by diffing the two gold files directly). Checked exhaustively — every other local ESPACE result across 29 files tops out at 53.3%, so 73.3%/v9 (N=15, unconfirmed at scale) really is the best available, just small-sample.

**Built two full hybrid tables** (all v1-v9 `resultats_*.csv` files, re-scored fresh against each gold set, small-N "winners" explicitly discarded in favor of robust N=60 alternatives):

Against current 79-novel gold: TYPE 91.7% (chunk_classifier_60novels), MODE 71.7% (same), RÉGIME 73.3% (same), ESPACE 55.3% (hybrid_v2/v3/v4/qwen3_30b_mapreduce), INTRIGUE 68.3% (chunk_classifier_60novels), TEMPORALITÉ 71.7% (hybrid.csv/hybrid_v4_60novels), FOCALISATION 60.0% (only v10b even attempts new scheme).

Against old 60-novel gold: TYPE 93.3%, FOCALISATION 77.2% (v5, old-scheme-valid), MODE 71.7%, RÉGIME 76.7%, ESPACE 73.3% (v9, N=15), INTRIGUE 68.3%, TEMPORALITÉ 71.7% — same chunk_classifier/hybrid winners as above for the unchanged criteria.

**`chunk_classifier_60novels.csv` confirmed (again) to use genuine leave-one-out CV** — read `train_chunk_classifier_60novels.py` directly, confirms `sklearn.model_selection.LeaveOneOut` + `cross_val_predict`. The saved CSV is the honest out-of-fold prediction, not leaky/overfit — resolves a doubt from an even older pasted table that claimed it needed a "nested-CV discount to 63.3%."

**v10c experiment** (isolated reduce-step `think=True` for FOCALISATION/RÉGIME/TEMPORALITÉ only, `REDUCE_NUM_PREDICT` 900→3000, map step untouched — same isolation-of-one-variable approach that fixed ESPACE via v9) — launched, ran the full session sharing the GPU with Task 2/4.5 re-tests, **still not finished as of this memory save** (>90 min elapsed on a ~76 min solo estimate, due to 3-way GPU contention). Partial numbers seen mid-run: 50% FOCALISATION / 91.7% TEMPORALITÉ on only 12/20 novels — promising on TEMPORALITÉ but not yet trustworthy (incomplete).

**Report**: `~/ecopoetique/TASK0_FINAL_REPORT_2026-07-10.md`.

**Next step, agreed but not run**: extend v9's ESPACE approach to the remaining 45 novels (60-novel gold) or 64 novels (79-novel gold) to confirm 73.3% at scale. ~6.8 min/novel measured directly from the original run's real per-novel timings → ~5.1h or ~7.3h GPU time.

## Lessons reconfirmed / new this session

- **Always re-score against the live file with the live join, never trust a file's own embedded GOLD_/correct columns or a pasted historical table** — repeated multiple times this session, every single discrepancy the user flagged traced back to a real, explainable cause (old gold scheme, small sample size, a corrected individual label) rather than an error in the current methodology — but only because each was independently re-verified from scratch, not defended from memory. See [[feedback-ecopoetique-experiments]].
- **Two non-comparable gold sets can silently coexist for the same task** — always check for code-vocabulary drift (not just row-count drift) before treating an old and new gold file as interchangeable, even for "unchanged" criteria (individual labels can still be corrected).
- **Small-N "winners" must be explicitly discarded, not just footnoted** — several sweeps this session had a top-ranked file with N=5-8 that was clearly noise; the user has flagged this pattern repeatedly across sessions now, treat it as a standing requirement, not a one-off catch.
- **This environment loses installed Python packages between sessions** (no project venv) — spaCy/fr_core_news_lg had to be reinstalled from scratch this session despite having been used successfully before; expect to reinstall polars/spacy/etc. again next fresh session, budget ~5-10 min setup time.
- **GPU sharing discipline**: ran 3 concurrent GPU jobs simultaneously multiple times this session (v10c + Task2 + Task4.5) at the user's explicit direction each time — this is a deliberate deviation from the standing "ask before sharing" rule, done because the user was actively directing rapid iteration; don't generalize this as new default behavior, still ask first unless the user is in this kind of active back-and-forth mode.
