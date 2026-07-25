---
name: project-task0-task1-status
description: "Full task status as of 2026-07-07 ~23:45 (deep re-read of CLAUDE.md + PROJECT_DOCUMENTATION.md, both freshly written by another Claude Code session at 23:07): Task 1 animaux done, plantes running (~36%); Task 0 GPT-4o hits 76.1%/34novels, honest local hybrid ~71.2%; Task 2 broken; Task 3 multilingual names in testing; Task 4.5 has no script yet"
metadata: 
  node_type: memory
  type: project
  originSessionId: 2d9b78d8-cf80-46a7-a1d0-4b5063db6529
---

Builds on [[project-meeting-notes]] and [[project-ecopoetique]]. **Supersedes all earlier snapshots of this file** (the 2026-07-03 hybrid-recipe numbers below are now superseded by fresher work, kept only as history).

**⚠️ This entire file is now superseded by [[project-2026-07-10-session]] and the three report files it produced: `TASK1_FINAL_REPORT_2026-07-10.md`, `TASK3_FINAL_REPORT_2026-07-10.md`, `TASK0_FINAL_REPORT_2026-07-10.md`.** Task 1 is fully complete (both animaux and plantes). Task 0's hybrid numbers below are stale — two non-comparable gold sets now exist, see the 2026-07-10 session for the corrected, verified tables. Read that memory first.

## Canonical up-to-date source now exists — read this first in future sessions

As of 2026-07-07 23:07, another Claude Code session wrote two files that are now the maintained, authoritative project status — check these BEFORE trusting this memory for anything code/status-related:
- `~/ecopoetique/CLAUDE.md` — fast-start task-status table + gotchas, actively kept current
- `~/ecopoetique/PROJECT_DOCUMENTATION.md` — full merged doc (~207KB, 10 sections): every source report verbatim (README, task1_report.md, task3_full_report.md, batch_testing_results.txt, pipeline_overnight.log, nested-CV results), both full Riccardo meeting transcripts verbatim, a synthesized research-papers/techniques-tried section, and a "results not yet written anywhere else" section for this session's own unpublished work (GPT-4o comparison, v8/v9 narratology experiments, honest hybrid reassessment).

This memory file should now record only things NOT already captured in those two files (deltas, corrections, feedback-relevant framing) rather than re-duplicating their content — check them fresh each session since they're being actively updated by parallel sessions.

## Current task status (per CLAUDE.md as of 2026-07-08, cross-checked against live logs 2026-07-07 23:42)

| Task | Status |
|---|---|
| §0 Foundations (extraction/lexicons/homograph disambig, by prior team "Joanna et al.") | Done, accepted as-is — Riccardo explicitly said not worth redoing even with its known ~10-15% impurity |
| **Task 0** (narratology, 7 dims via qwen3:30b map-reduce) | Active. Best local honest ~62-64%. **GPT-4o hits 76.1% on 34/60 novels** (quota-limited, not yet resumed to finish remaining 26). Riccardo sent a brand-new FOCALISATION coding scheme (reader-vs-character knowledge framework, replacing the old whose-consciousness framework) + new `MOD_DIA` mode category (`narratologie/tableau_narratif_22_08.csv`) — **no annotated gold set exists yet in the new codes**, blocking any further FOCALISATION comparison |
| **Task 1** (référentiel/figuré, qwen3:30b batch=4) | Animaux: **done 2026-07-05** (incl. a retry pass). **Plantes: running now** — live-checked 2026-07-07 23:42: 25,134/69,314 rows (36.3%), speed 3.7s/row, ETA ~45h (~2026-07-09 night), failed_batches=8 (low/steady, needs retry pass later) |
| **Task 2** (metaphor subcategories, 16+3 categories) | **Broken** — LLM fallback path returns 0 successes throughout, only the rule-based fast path works. 3 new categories confirmed by Riccardo in his actual gold annotations (`COUL`=color use e.g. "vert pomme", `LOC_IDIOM`=lexicalized idiom no longer read as animal/plant, `IMAG`=representation-of-a-thing not the thing itself e.g. embroidered birds on a curtain) but have no formal written definitions yet — asked Riccardo. Gold set 131/200 rows answered for subcategory |
| **Task 3** (agentivity, spaCy dependency parsing — NOT qwen3, independent of Task 0/1 GPU contention) | Core findings solid and Riccardo-approved (humans 37.2% active agent > animals 24.4% > plants 11.8%). Plant numbers stale (mixed fig+ref, refreshable now Task1-plantes is finishing). **New: multilingual human-name extraction** (`extract_humains_multilingual.py`) to catch English/Arabic-origin names beyond French-only spaCy — small 2-novel test just completed successfully 2026-07-07 23:39: 438 fr-model rows + 34 new multilingual-model rows found. A separate **XLM-RoBERTa NER subword-splitting bug** was found and fixed this session (`Davlan/xlm-roberta-base-ner-hrl` sometimes splits one name into two adjacent PER spans with zero gap, e.g. "Émile"→"É"+"mile" — fix: merge consecutive zero-gap PER spans before accepting) |
| **Task 4.5** (compare-target classification, 6 categories CH/P/NH/O/E/A) | No processing script exists yet. No written definitions file exists anywhere — only Riccardo's verbal description from the meetings. Gold set (same file as Task 2) has 112/200 rows answered for `categorie_compare`, plus 4 legitimate `?` rows needing a scoring convention from Riccardo |
| Task 5 (deployable front-end + external novel DB) | Explicitly deprioritized by Riccardo in both meetings — "too much of a stretch" |

## Task 0 — new findings not in the old (2026-07-03) snapshot below

- **GPT-4o v7 port** (identical prompts/chunking/reduce-vote to the best local qwen3 pipeline, only the model backend changed) on 34/60 novels that completed before hitting `insufficient_quota`: **76.1% overall**, beats qwen3:30b v7 on every single criterion, RÉGIME NARRATIF hit 82.4% — past Riccardo's named 80% target. Cost: ~$8.55 for 34 novels; ~$15 projected for full 60; ~$227 for the full 925-novel corpus. This directly answers the "can paid GPT get us to 80%?" question raised in both meetings.
- **gpt-4o-mini v7 port**, all 60/60 novels, **$0.89 total**: 64.8% overall — real but modest win over local qwen3 (62.1%), confirms a genuine quality gap vs. full GPT-4o, not just a price difference.
- **v8** (rewrote FOC/RÉGIME/MODE/INTRIGUE/TEMP definitions simultaneously, grounded in real narratological theory): regressed to 57.1% on a 5-novel check vs v7's 74.3% — rejected. Consistent with the standing "isolate one variable" lesson.
- **v9** (single change: enable `think=True` on the REDUCE step only): flat overall (61.9%) but an isolated, real trade — ESPACE +20pp (53.3%→73.3%), INTRIGUE −20pp. Not a general fix; use only for ESPACE in a future hybrid.
- **Honest hybrid reassessment**: the previously-reported 69.3% "leaky" hybrid and even the 71.2% figure from the 2026-07-03 recipe below were re-derived cleanly at **~71.2% (299/420)** — this number now supersedes the 69.3% one directly; still below GPT-4o's 76.1%.
- **Open blockers**: GPT-4o run stuck at 34/60 (needs account top-up + a `load_done()` one-line fix so it retries the 2 quota-failed novels instead of wrongly skipping them); new FOCALISATION codes not yet applied to any of this session's numbers; a "read the model's reasoning on misses" diagnostic for MODE/RÉGIME/TEMPORALITÉ plateaus proposed but not yet done.

## Timeline / deadline context

- Labiba's internship ends **2026-07-15**; July 14 is a public holiday (Bastille Day) so effectively last working day is **2026-07-13**.
- Second meeting with Riccardo (transcript: `métaphore/Riccardo_second_meeting.txt`) happened before 2026-07-08 — exact date uncertain from transcript alone, but content places it shortly after Task 1 animaux started finishing, consistent with ~2026-07-03/04. Riccardo asked for a full written documentation (up to ~40 pages) of everything tried, wants it partial-by-Wednesday(~07-08)/full before a **next meeting mentioned as "10th of July"** (a Friday) — that meeting has not yet happened as of 2026-07-07.
- Riccardo explicitly approved a paid-GPT budget (€22-25 estimated for a full corpus run, offered up to €100-200 if needed) — this funded the GPT-4o v7 experiment above.

---

## [HISTORICAL — 2026-07-03 session, kept for reference, largely superseded by the GPT-4o/honest-hybrid numbers above]

**The correct gold set is 60 novels, not 76/79/80.** GitLab `origin/main` (`gitlab.com/rumiwarmi/ecopoetique`, `narratologie/GOLD_narratologie.csv`) has 60 novels — verified via `git fetch origin && git show origin/main:...`. Local file `GOLD_narratologie_60novels_original.csv` holds the correct 60-novel set matching GitLab.

**Classifier overfitting bug (found+fixed 2026-07-02 evening):** `train_chunk_classifier_60novels.py` picks between LogReg/RF/GB per criterion using `cross_val_predict` scored on the same loop being reported — model-selection leakage. Fix: `nested_cv_classifier.py` (inner 5-fold CV blind to the held-out novel). This produced `resultats_nested_cv_honest.txt`: **64.0% overall (269/420)** — this is the number now cited in CLAUDE.md as "best local honest ~62-64%."

Leaky vs honest (nested CV) per criterion, 60-novel set:
| Criterion | Leaky | Honest | Inflation |
|---|---|---|---|
| TYPE NARRATEUR | 93.3% | 90.0% | +3.3pp |
| FOCALISATION | 66.7% | 65.0% | +1.7pp |
| MODE NARRATIF | 70.0% | 63.3% | +6.7pp |
| RÉGIME NARRATIF | 75.0% | 68.3% | +6.7pp |
| ESPACE | 51.7% | **38.3%** | **+13.4pp (worst)** |
| INTRIGUE | 68.3% | 65.0% | +3.3pp |
| TEMPORALITÉ | 60.0% | 58.3% | +1.7pp |
| **OVERALL** | **69.3%** | **64.0%** | **+5.3pp** |

**Full drift check finding (still true, worth remembering as a pattern):** comparing a "frozen" result file's predictions to a live rerun of its claimed source is NOT uniformly old-worse or live-worse — it was genuinely mixed per-criterion (3 improved live, 3 regressed live, 1 tied), traced to real pipeline/model changes between runs, not just noise. Always gold-check the specific drifted novels before concluding which version is "right."

**train_chunk_classifier.py has the SAME leaky best-of-3 bug** as the 60novels variant (confirmed by reading the code) — any script in this project with "try N sklearn classifiers, report the best" pattern is a candidate for the same check.

## Task 1 — historical notes (animaux run, now complete)

- Must be launched from `~/ecopoetique/métaphore/`, not `~/ecopoetique/` — `run_task1_corpus.py` uses relative paths resolved against CWD. Wrong directory → 0 rows found → crash, but doesn't touch the real checkpoint (safe to just `rm -rf` stray output and relaunch correctly).
- Fully resumable (loads done rows from output CSV automatically) — this same resumability is what let the plantes run be "resumed 2026-07-08" per CLAUDE.md.
- Sustained Task 0 GPU load (15+ min) measurably slows Task 1 throughput (~4.1s/row → 4.3-4.4s/row); brief tests are negligible. A sleep-based throttling script (`run_task1_corpus_throttled.py`) exists for GPU-sharing scenarios, roughly halving duty cycle at ~2x runtime cost — used when a colleague needs the shared A40 GPU back (no sudo/MPS access for hard partitioning on this machine).

## Useful background research
- ["Says Who? Effective Zero-Shot Annotation of Focalization"](https://arxiv.org/html/2409.11390) — GPT-4o gets 84.79% F1 on a similar focalization task; "zero focalization" was their hardest category too (36% F1).
- [LLM×MapReduce](https://arxiv.org/html/2410.09342v1) — inspired the mapreduce reduce-step design.
