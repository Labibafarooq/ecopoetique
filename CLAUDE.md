# Écopoétique — project context for Claude Code

Digital humanities research project (Sorbonne Université / UPPA), supervised by Riccardo Barontini, worked on by Labiba Farooq (intern, last day **2026-07-15**). Studies how animals, plants, and biodiversity are represented across a 925-novel French corpus. This file is the fast-start summary — the complete history (every report, both full meeting transcripts with Riccardo, and this session's own experimental results) lives in `PROJECT_DOCUMENTATION.md` in this same directory. Read that file for anything not covered here.

## Task status (as of 2026-07-08, evening)

| Task | What it does | Status |
|---|---|---|
| **§0 Foundations** | Corpus, lexicons, homograph disambiguation, extraction pipeline — built by a previous team (Joanna et al.), predates this work cycle | Done, accepted as-is (Riccardo: not worth redoing even with its known ~10-15% impurity) |
| **Task 0** (narratology) | 7 narrative dimensions per novel via qwen3:30b map-reduce, scored against a 60-novel gold set | Active, blocked on Riccardo. Best local result 62-64% honest. GPT-4o hits 76.1% (34/60 novels, quota-limited). Riccardo sent a new FOCALISATION coding scheme (completely different framework — reader-vs-character knowledge, not whose-consciousness) and a new `MOD_DIA` mode category — have the new schema (`tableau_narratif_22_08.csv`) but NOT yet an annotated gold set in the new codes. **Asked Riccardo, not yet received.** GPU cost to test a new technique once unblocked: **~6-8 hours of real qwen3/Ollama time for a 60-novel run** (9 map calls + 3 reduce votes/novel) — this would meaningfully compete with Task 1 if run concurrently. |
| **Task 1** (référentiel/figuré) | Classify every animal/plant mention as literal or figurative, qwen3:30b, batch=4 | Animaux: done (2026-07-05), verified via aggregate-count check. **Plantes: running now**, ~36% done, ETA ~1.9 days. No new GPU cost — already in progress. |
| **Task 2** (metaphor subcategories) | Classify figurative mentions into 16(+3 new) structural categories | **Broken**, blocked on Riccardo. LLM fallback path returns 0 successes the whole way through (only the rule-based fast path works). We DO already have the original 16 categories (embedded in the script, confirmed identical to Riccardo's own reference table). Missing: formal definitions for the 3 new categories (`COUL`, `LOC_IDIOM`, `IMAG`) confirmed in Riccardo's real gold-set annotations but never written down. **Asked Riccardo, not yet received.** Gold set `~/ecopoetique/comparison/gold_task2_task45_RB.csv` has 131/200 rows answered for subcategory (69 blank — asked Riccardo to complete or confirm intentional). GPU cost once fixed: **~15-25 min** for the 131-row gold check (light qwen3 calls, short text each). |
| **Task 3** (agentivity) | Active/passive/object/noun-complement role classification: humans vs. animals vs. plants, via spaCy dependency parsing — **does NOT use the qwen3 LLM at all**, zero GPU contention with Task 0/1 | Core findings done and solid (humans 37.2% active agent > animals 23.8% (refreshed) > plants 11.8%). **Animal-side refresh: done 2026-07-08** — re-filtered using our own corrected Task 1 animaux labels (Sunday retry-v2), closed a dependency-parse coverage gap (dépendants_ANIMAUX.csv was missing bestsellers + 2,243 corpus_principal rows), final: 23.8% active agent / 0.8% passive / 21.5% object on 86,082 référentiel mentions (96% coverage) — see `task3_full_report.md` "UPDATE — 2026-07-08". Two things left: (1) multilingual name detection — in progress, see below; (2) plant-side refresh — same method, blocked on Task 1 plantes finishing. |
| **Task 4.5** (compare-target) | For each figurative mention, classify what it's being compared to (6 categories: CH/P/NH/O/E/A) | **Cannot run yet — blocked entirely on Riccardo**, not just partially. No processing script exists. No written definitions file exists anywhere — only Riccardo's verbal description from the first meeting. Gold set (same file as Task 2) has 112/200 rows answered for `categorie_compare`, plus 4 legitimate `?` rows needing an agreed scoring convention. **All three asked, none received yet.** |
| **"Task 4"** | — | Not a real separate task — confirmed by search, it's just an old name for Task 0/narratology used once in `task1_report.md`. |
| **Task 5** | A deployable front-end system + external novel database | Explicitly deprioritized by Riccardo in both meetings ("too much of a stretch") |

## Currently waiting on Riccardo for (nothing else can proceed on these until he replies)

1. ~~New Task 0 gold set annotated with the new FOCALISATION codes~~ — **received 2026-07-08**: `narratologie/GOLD_narratologie_0807.csv` (80 rows/79 novels, all 60 confirmed gold novels + 19 new, zero blanks, new codes `FOC_ELARG/FOC_MIXTE/FOC_REST/FOC_RFOC`). Not yet used for a re-comparison.
2. ~~Formal definitions for Task 2's 3 new categories (`COUL`, `LOC_IDIOM`, `IMAG`)~~ — **received 2026-07-08**: `métaphore/schema_analogies_vivant_complet_0807.csv`, 19 total categories. Not yet wired into `create_gold_task2.py` (which still references the old 16-category file by name).
3. Completion of Task 2's gold set blanks (69/200 rows) — still open
4. ~~A written Task 4.5 definitions file~~ — **received 2026-07-08**: `métaphore/Catégories analyse comparés.docx` (6 categories: O, NH, E, CH, A, P — full text in memory `project_2026-07-08_session.md`). No Task 4.5 processing script exists yet — still needs to be built.
5. Completion of Task 4.5's gold set blanks (88/200 rows) + a scoring convention for the 4 `?` rows — still open

**3 of 5 items cleared in one day (2026-07-08).** Only #3 and #5 (gold-set blank completion) remain genuinely blocked on Riccardo.

## What can be worked on right now without waiting on anyone (all zero/near-zero GPU)

- Task 3's multilingual name detection (active, see below)
- Task 3's animal-side agentivity refresh (not started)
- Task 2's LLM-path bug fix (code work is free; testing needs ~15-25 min of light qwen3 time once fixed)

## Task 3 multilingual name detection — full debugging history (2026-07-08)

Riccardo asked (both meetings) to extend human-name detection beyond the French-only spaCy model to catch English/Arabic-origin names, explicitly flagging the overfitting risk ("a name called bar in any other language") and separately proposing a mid-sentence-capitalization check as a validation signal.

Built `morphosyntaxe/extract_humains_multilingual.py`: runs `Davlan/xlm-roberta-base-ner-hrl` (multilingual NER, CPU-only — confirmed zero GPU usage, doesn't compete with Task 1) alongside the existing French spaCy pass, keeping only new PER candidates the French model missed, gated by several guards. Iteratively found and fixed real bugs via direct output inspection — do not trust a "looks like it worked" run without checking actual extracted names:

1. **Subword-splitting bug**: XLM-R's tokenizer sometimes splits one name into two adjacent PER spans with zero gap ("Émile" → "É"+"mile", "Théodore" → "Th"+"éodore"). Fix: merge consecutive PER spans with exactly zero character gap.
2. **One-sided truncation**: some names had only HALF tagged as PER at all (the model never labeled the other half as any entity) — e.g. "Mauny" → only "ny" survived, "Lippmann" → only "pmann". Fix: extend any span backward/forward to the nearest word boundary (adjacent alphabetic character) regardless of what the model tagged the rest as.
3. **Animal/plant false positives**: 'Ours' (= bear) was being tagged as a human PERSON — a real risk given this corpus is specifically about animal/plant representation. Fix: cross-check every multilingual-only candidate against `lexiques/ANIMAUX.txt`/`PLANTES.txt`, including spaCy lemma + cheap French gender-variant stripping (catches "Ourse"→"ours", "chatte"→"chat").
4. **Place-name false positives**: 'Sables' (likely Sables-d'Olonne) was passing every filter since it IS a genuine, consistently-capitalized proper noun — the capitalization guard alone can't distinguish a place from a person. Fix: cross-check against every LOC entity the French spaCy model already tags in the same novel (free — same `doc.ents` pass already used for PER).

All four fixes are in the current version of the script. Last test was a 5-novel run to confirm; check `PROJECT_DOCUMENTATION.md` or ask for the latest numbers if picking this up later. **Known residual gap, not yet fixed**: cultural/generic-word false positives that are neither animal/plant terms nor places (e.g. 'Nirvana', 'Petit Prince', 'Barbie') still need human/gold-set judgment — no automated filter can safely resolve these.

**Full-corpus cost estimate**: ~130s/novel on CPU → **~33 hours for all 925 novels**. GPU would likely be much faster (the model is tiny compared to qwen3:30b) but wasn't tested — a decision point before scaling up, not yet made.

## Established lessons / gotchas (don't relearn these the hard way)

- **qwen3:30b needs thinking mode enabled** or accuracy collapses (Task 1: 0% figurative accuracy with thinking off). Task 0's REDUCE step historically disabled thinking — a v9 experiment enabling it there gave an isolated +20pp win on ESPACE only, not a general fix.
- **`wc -l` is unreliable for row counts** on any file where a field might contain embedded newlines (happened on Task 1 corpus sizing, and again on the multilingual names CSV — 951 raw lines vs. 554 real records). Always trust the actual parser's count (`csv.DictReader`) over raw line count.
- **Isolate one variable per experiment.** A "v8" narratology attempt changed 5 prompt definitions at once and made results worse with no way to tell why; "v9" changed exactly one thing and gave a clean, interpretable (if partial) result.
- **For retries/re-runs, import and reuse the exact original functions** rather than re-describing the prompt from scratch — a first Task 1 animaux retry attempt drifted from the production prompt this way and had to be redone.
- **GPU sharing**: this machine has one shared GPU (NVIDIA A40, 46GB). No sudo/MPS access, so true hard resource-splitting isn't possible — the only lever if a colleague needs the GPU back is either pausing entirely, or a sleep-based throttling script (`run_task1_corpus_throttled.py`) that roughly halves duty cycle at the cost of ~2x runtime.
- **Always inspect actual extracted values, not just row counts, before trusting a pipeline.** The multilingual names script "ran successfully" three times in a row while silently producing broken/garbage names each time — only manual inspection of the unique value list caught it.
- **Verify claims (including your own past assumptions) against real files, not summaries or memory.** Several times this session, a remembered claim — "Task 2 was running perfectly," GPU utilization assumptions, "`retry_animaux_v2.py` is probably the Task 3 refresh" — turned out to be wrong on direct inspection. Always check the actual file/log/GPU state before asserting a fact.

## Where things live

- Full detailed history: `~/ecopoetique/PROJECT_DOCUMENTATION.md`
- Task 0 production script: `narratologie/run_task0_mapreduce_v7.py` (v9 has an isolated ESPACE improvement, not a full replacement)
- Task 1 production script: `métaphore/run_task1_corpus.py` (+ `run_task1_corpus_throttled.py` for GPU-sharing scenarios)
- Task 2 script (broken, needs the LLM path fixed + 3 categories added): `métaphore/run_task2_subcategories.py`
- Task 3 scripts: `morphosyntaxe/extract_humains.py` (French-only, working, production), `morphosyntaxe/extract_humains_multilingual.py` (new, multilingual extension, in testing per the debugging log above)
- Task 2/4.5 gold set: `comparison/gold_task2_task45_RB.csv`
- Task 0 new schema: `narratologie/tableau_narratif_22_08.csv`
