---
name: project-2026-07-10-session4
description: "2026-07-10 afternoon session: Task 4.5 entity-type fix implemented+running, Task 2 META_JUXT eliminated+running, Task 0 v9 narrowed to ESPACE-only per Labiba's request, 4 concurrent GPU jobs"
metadata: 
  node_type: memory
  type: project
  originSessionId: 3256f2bc-4a07-49b8-9f01-a7296bdd2f68
---

Continuation of [[project_2026-07-10_session3]], same day, afternoon. Riccardo sent a follow-up email (2026-07-10, ~15:53) confirming both open items from session 3.

## Riccardo's email — verbatim confirmation

1. **Task 4.5 categories = target entity type, not trait domain** (matches [[feedback_task45_category_is_target_entity_type]] exactly). His example: "Je bats lâchement en retraite... comme un rat" → cible = "il" (person) → **CH**, even though the illustrated trait (lâcheté) is psychological. Contrast: "Mes émotions se cachaient comme des rats" → P. "L'île ressemblait à un rat" → E.
2. **META_JUXT eliminated** — fold everything into META_APP, confirmed explicitly (was already suspected/tested in session 3).

## What was done this session

**Task 4.5** (`comparison/run_task45_compare_category.py`): the old "personality trait → P, not CH" and "voice/artistic quality → A, not CH" patches (⚠ Piège fréquent n°1/n°2) were found STILL LIVE in the prompt despite session 3's diagnosis — never actually implemented. Rewrote the prompt: step 2 (cible) now asks for the literal referent; step 5 (code) classifies that referent's entity type only, with Riccardo's exact rat/il/CH example embedded verbatim as a contrastive illustration, and explicit instruction that fondement_commun (the trait) must NOT be used to pick the category. Old flawed-prompt gold results backed up to `resultats_task45_compare_category_PRE_ENTITYTYPE_FIX_20260710.csv`. Gold validation (112 rows) launched fresh — **running, not yet complete**, log: `comparison/task45_gold_validation_v5_entitytype_fix.log`.

**Task 2** (`métaphore/run_task2_subcategories.py`): removed META_JUXT from `SUBCATEGORIES` dict and merged its decision-tree branch (was question 10) into question 9 (META_APP) — hyphenated compounds/binômes nominaux now classify as META_APP directly. Renumbered questions 10→9, 11→10, 12→11, 13→12, 14→13 for consistency. `validate_task2_gold.py` updated to normalize any gold rows still labeled META_JUXT to META_APP before scoring (2 such gold rows exist: ids 8 and 20). Old gold results backed up to `resultats_task2_gold_validation_PRE_METAJUXT_FIX_20260710.csv`. Gold validation (114 rows) launched fresh — **running, not yet complete**, log: `métaphore/task2_gold_validation_v7_metajuxt_fix.log`.

**Pre-fix Task 2 gold baseline (69.3%, 79/114, all via LLM path)** — analyzed before rerunning, useful reference even though a fresh run is in flight:
- Worst: META_FILEE 0/3, DE_PROP 0/2, META_VERB 40%(2/5), COMME_SI 50%(2/4), COMME_P 50%(2/4)
- Mid: IMAG 57%(4/7), META_APP 57%(4/7), META_ATTR 60%(12/20)
- Best: COMME_SN 83%(20/24), LOC_IDIOM 87%(13/15), DE_PARANGON 100%(7/7), COUL 100%(6/6)
- Top confusion pairs: META_ATTR→LOC_IDIOM (4, biggest single leak — surnommage misread as frozen idiom), and DE_PARANGON as a false-positive sink pulling in DE_PROP(2)/META_APP(2)/COMME_SN(2) — 6 wrong predictions land there, including COMME_SN cases that have an explicit "comme" the model should have caught earlier in the decision tree (evidence the model doesn't reliably respect prompted sequential ordering).
- **Next planned step (queued, held per Labiba until current runs finish)**: add invented (never gold-set/corpus) contrastive few-shot example pairs at these two boundaries. Full writeup in [[project_task2_next_step_fewshot_examples]].

**Task 0**: Labiba explicitly said she does NOT want the full 7-criteria v9 run — only ESPACE (she said "the escape one," meaning ESPACE). Killed the full run (PID 4113039/4113038; 33/45 novels had been scored, ESPACE was at 72.7% there — the standout criterion, consistent with v9's known isolated ESPACE win from thinking-mode-enabled REDUCE). Built `narratologie/run_task0_v9_espace_only.py`: imports every reusable function from `run_task0_mapreduce_v9.py` unchanged (MAP step, call_ollama, chunk_novel, extract_json, load_gold, is_correct, CRITERIA_DEFS) per this project's standing "reuse original functions on a retry" rule — the only new code is a REDUCE step trimmed to ask for ESPACE alone (REDUCE_NUM_PREDICT dropped 3000→1200 since one field needs less reasoning budget than seven), same ESPACE definition text extracted verbatim, not reworded. Output: `resultats_task0_v9_espace_only.csv`. Smoke-testing on 2 novels before scaling to the full 45, per project practice.

Meanwhile **v10c** (new-FOCALISATION-scheme run, 3 criteria: FOC/REGIME/TEMPORALITÉ, targeting the new 79-novel gold set) kept running untouched throughout — Labiba didn't ask to stop it. At last check (67 novels scored): FOCALISATION (new scheme) 37.3% — weak, flagged to her as concerning since this new scheme was the reason Task 0 got unblocked; REGIME 61.2%; TEMPORALITÉ 68.7%.

## GPU contention

Up to 4 qwen3:30b jobs ran concurrently at once this session (v10c + Task 2 gold + Task 4.5 gold + ESPACE-only smoke test) — only one Ollama model instance loaded, so all requests serialize/queue behind each other, meaning each job runs slower than solo. Flagged to Labiba once; she didn't ask to reduce concurrency, so left as-is. Worth checking `curl localhost:11435/api/ps` and `ps aux` at the start of any future session to know what's actually mid-run before assuming state from memory alone.

## State at end of this session (still in progress, not final numbers)

- Task 4.5 gold validation: running, no results yet
- Task 2 gold validation: running, no results yet
- Task 0 v10c: still running, 67/79 novels scored so far (see numbers above)

## Reversal: ESPACE-only script abandoned, full v9 resumed instead

After the above was written, Labiba asked to run "escape" (ESPACE) only, so `narratologie/run_task0_v9_espace_only.py` was built (imports MAP step etc. from v9 unchanged, trims REDUCE to one field, `REDUCE_NUM_PREDICT` cut 3000→1200). A 2-novel smoke test was run and an auto-chain watcher was set up to launch the full 45-novel run automatically once the smoke test exited.

**Bug found in the smoke test**: novel 1 failed completely — all 3 reduce votes returned empty/unparseable JSON ("No valid JSON object found"), novel 2 had 1/3 votes fail the same way. Root cause: cutting `REDUCE_NUM_PREDICT` to 1200 assumed a 1-field answer needs less budget than v9's original 7-field answer, but that's wrong — the model still needs comparable *thinking* tokens to compare 9 sections' locations before it ever reaches the JSON; trimming the field count didn't shrink the reasoning cost. Same failure signature as [[feedback_qwen3_truncation_pattern]]. **The auto-chain watcher already fired and launched the full 45-novel run before this was caught** — it was killed (PID 4169162) once noticed.

**Labiba then reversed course**: she does NOT want the ESPACE-only path continued — she asked to go back to the original full 7-category v9 run and resume it instead. Done: resumed `run_task0_mapreduce_v9.py --resume` (PID 4189458, log `v9_test60_full.log`), continuing from the 33 novels already scored (ESPACE 72.7%, TYPE 90.9% at that point — see numbers earlier in this memory).

**`run_task0_v9_espace_only.py` is now dead code, not deleted** — if ESPACE-only ever comes up again, fix `REDUCE_NUM_PREDICT` back up toward 3000 (or test empirically) before trusting any output from it; the 2-novel smoke test result (1/1 = 100%, from the one novel that didn't fail) is not meaningful given the failure rate.

## Final results of the first-round fixes (all runs completed)

- **Task 4.5 gold (entity-type fix, first round)**: 82/104 = **78.8%**
- **Task 2 gold (META_JUXT eliminated only)**: 84/114 = **73.7%**
- **Task 0 v10c (new FOCALISATION scheme, full 79 novels)**: FOCALISATION 26/79=**32.9%**, REGIME 48/79=**60.8%**, TEMPORALITÉ 54/79=**68.4%**

## Task 4.5 confusion-matrix diagnosis (78.8% run) — 3 buckets

Per-category: CH 93.1%(67/72), O 85.7%(6/7), E 75%(3/4), A 45.5%(5/11), **P 10%(1/10)**.

Pulled full context (not just truncated `raison`) for every wrong A/P row — see `comparison/gold_task2_task45_RB.csv` ids below. Findings split cleanly into 3 buckets, written up in detail in this memory for future reference:

1. **Bug I introduced (fixed this session)**: my own added prompt example "voice/chant attributed to a person → CH" was wrong and caused 2 real errors — id=45 (gnous/"le chant va déferler", gold=A) and id=121 (guimauve/"une voix... annonça", gold=A). Both have the voice/chant itself as the grammatical subject, not a person. Removed the bad example, added correct guidance distinguishing "voice is the subject → A" from "person is the subject, voice is a detail → CH".
2. **Cible-extraction too literal on idioms/rhetoric (fixed this session)**: ids 23 (porc — real cible is "la beauté", an abstract aesthetics discussion, model anchored on the pronoun "elle" instead), 75 (chèvre — "ménager la chèvre et le chou" is a fixed idiom, no literal cible, should resolve to the abstract compromise/indecision concept), 81 (mouton/carpe — rhetorical list of incompatible pairs, cible is the abstract notion of difference, not either animal), 135 (loup/chemin — poetic description of a reading sensation, not a literal path — **still unfixed after this round**), 169 (chien/"être composite" — describes a person's grotesque appearance, cible=that person=CH, model took the composite-creature description too literally as NH). Added guidance: identify what the sentence is REALLY about (idiom's abstract meaning / rhetorical point / the person being poetically described) before taking the nearest noun literally.
3. **Genuine gold P/CH contradiction — NOT fixed by prompting, needs Riccardo's ruling**: 8 of the 10 P-category errors have an explicit human referent (il/elle/tu/ils, or named individuals "Henri Beyle"/"Pierre Castaneda") with a psychological/behavioral fondement — structurally identical to Riccardo's own rat/il/CH worked example, yet gold=P (ids 67 jument, 68 singe, 123 ânes, 172 porc, 173 aigle, 186 chacal). The **exact opposite** contradiction also exists: id=91 fougère ("apparenté en mon penser... à la fougère") reads as a textbook P case (cognitive faculty as cible, matching his own "mes émotions" example) yet gold=**CH**. Also id=17 citrouille (self-image/status delusion — arguably P not A). **Action item, not yet done**: compile these into a question list for Riccardo, same pattern as the COUL/LOC_IDIOM/IMAG and META_JUXT clarifications earlier in the project. Possible hypothesis to test with him: whether the psychological faculty being the sentence's own grammatical *subject/agent* ("mes émotions se cachaient") vs. merely a descriptive attribute of an already-established person ("mon penser apparenté à...") is the real distinguishing factor — but this is speculation, not confirmed.

Bucket 1+2 fix smoke-tested on the 7 affected rows (`comparison/test_task45_bucket_fix.py`, reusable): **6/7 fixed** (only id=135/loup still wrong — the hardest, most poetic case). No regressions observed. Old 78.8% results backed up to `resultats_task45_compare_category_PRE_BUCKETFIX_20260710.csv`; full 112-row rerun launched fresh, log `task45_gold_validation_v6_bucketfix.log` — **running, not yet complete** at end of session.

## Task 2 few-shot fix — implemented, tested weak, NOT scaled to a full rerun

Per [[project_task2_next_step_fewshot_examples]] (queued from earlier this session), added: (a) a "don't skip ahead in the decision tree" discipline reminder after several errors showed COMME_SN cases (explicit "comme" present) still landing on DE_PARANGON; (b) contrastive META_ATTR vs LOC_IDIOM examples (surnommage "on le traite de rat" → META_ATTR vs generic qualifier "un appétit d'ogre" → LOC_IDIOM); (c) a DE_PARANGON vs DE_PROP discriminating test ("replace N1 with 'la qualité de X'" — quality-illustration vs domain/group-membership).

Smoke-tested on the 10 exact rows that drove the original confusion pairs (`métaphore/test_task2_fewshot_fix.py`, reusable): **only 2/10 fixed** (poussin id=62, chien id=200). DE_PROP↔DE_PARANGON: 0/2 fixed. META_APP↔DE_PARANGON: 0/2 fixed. META_ATTR↔LOC_IDIOM: 1/3 fixed, and one case (cheval id=83) changed from one wrong answer to a different wrong answer (LOC_IDIOM→COMME_SN). Weak enough that **the full 114-row rerun was NOT launched** — not worth ~100min of GPU time for likely-marginal gain.

**Root-cause replay** (`métaphore/diag_replay.py`, reusable — calls `make_prompt`/raw Ollama directly on one row to see full output): replayed id=32 (guimauve, "mes poings de guimauve", gold=DE_PROP). Model's actual output: `{"code": "DE_PARANGON", "raison": "Structure 'N1 de N2' illustrant une qualité (douceur) via un exemplaire (guimauve), comme 'mémoire d'éléphant'."}` — this is a **coherent, well-reasoned** parse, not a bug. "Poings de guimauve" (fists as soft as marshmallow) genuinely does structurally resemble "mémoire d'éléphant" (quality exemplified by a noun known for it). But DE_PROP's defined pattern ("vautours de la finance" — domain-membership label for people) doesn't obviously fit this construction either (a body part described via a soft material, not a person categorized by domain). **Conclusion: this looks like a genuine ambiguity in how the DE_PARANGON/DE_PROP schema definitions cover this construction type, not something more few-shot examples can patch.** Recommended action (not yet done): send Riccardo 2-3 concrete boundary cases (this guimauve one, plus the perroquet/chevreuil META_APP↔DE_PARANGON pair) for a ruling, rather than continuing to guess at prompt wording blindly.

## State at end of this session (still in progress, not final numbers)

- Task 4.5 gold validation (bucket-fix round): running, no results yet, PID 40048
- Task 2: NOT rerun — few-shot fix implemented but underperformed on smoke test, left as-is pending either a better prompt idea or Riccardo's input on the DE_PARANGON/DE_PROP ambiguity
- Task 0 v10c: **finished**, final numbers above — FOCALISATION new scheme is badly broken (see next section)
- Task 0 v9 (full 7-criteria, resumed): still running, ~57+/45(orig)+33(prior)≈ novels scored, PID 4189458

## Task 0 v10c FOCALISATION bug — diagnosed, one fix attempt made, still not working

Confusion-matrix analysis (`narratologie/analyze_v10c_focalisation_confusion.py`, reusable) on the 73-novel checkpoint found **all 47 errors landed on FOC_ELARG** — a clean default-collapse, not scattered noise. Root cause found by reading `run_task0_v10c_reduce_think.py`: the REDUCE prompt had an "ANY ONE section showing more_than_characters wins" rule for FOC_ELARG — with 9 independently-judged chunks per novel, at least one nearly always gets misjudged as dramatic irony without seeing the rest of the novel, and that single false positive was overriding everything else. Same failure family as the earlier INTRIGUE per-chunk-categorical-collapse bug (see `feedback_ecopoetique_experiments.md` #10).

**Fix attempted this session**: replaced the noisy 3-way categorical MAP field (`reader_vs_character_knowledge`) with two concrete evidence-extraction fields (`dramatic_irony_evidence` / `info_withheld_evidence`, each "quote a specific instance or say 'none'"), and changed the REDUCE aggregation rule from "≥1 instance" to "≥2 independent instances" before choosing FOC_ELARG or FOC_REST over the FOC_RFOC default. Output moved to a new file (`resultats_task0_v10d_focalisation_evidence.csv`) rather than resuming on top of v10c's buggy-methodology data.

**Test result on 4 novels: 1/4 (25%)** — not a clean win:
- Ernaux `Les-annees`: **fixed**, now correct FOC_RFOC.
- Houellebecq `Soumission`: still wrong (ELARG) — genuinely found 3 concrete irony instances, clearing the new ≥2 bar, but gold isn't ELARG. The evidence is real but apparently not "dominant" enough — the ≥2 absolute-count threshold doesn't capture dominance relative to the novel's length/9 sections.
- Mauvignier `Continuer`: still wrong (ELARG) — 2 irony instances, exactly hit the new threshold, gold is FOC_MIXTE.
- Autissier `Soudain-seuls`: **new regression** — was correct before. One chunk had both irony AND withheld evidence simultaneously, another had only withheld — so withheld hit ≥2 first and REDUCE picked FOC_REST, even though gold is ELARG. Also one of 3 reduce votes failed (empty JSON).

**Not yet resolved.** The ≥2 absolute-count fix isn't sufficient — needs either a relative/dominance threshold instead of an absolute count, or a tie-break rule for chunks where both evidence types co-occur. Left as an open problem for next time; do NOT scale this to a full run yet.

## REGIME and TEMPORALITÉ — separate, undiagnosed problem (opposite failure direction from FOCALISATION)

From the same v10c 73-novel checkpoint: **REG_FANT is 0% recall** (0/10, always predicted REG_REAL or REG_SPEC instead) and **TEMP_DESORD is 0% recall** (0/5, always predicted TEMP_DIS or TEMP_LIN instead). Unlike FOCALISATION's over-triggering collapse, this is **under-triggering** — the model seems too conservative to ever commit to the rarest/most extreme category in either criterion, always falling back to a more common neighbor. Different root cause, needs separate diagnosis (not yet started) — should replay actual MAP/REDUCE calls on specific misclassified FANT/DESORD novels (not guess) before proposing a fix, per this project's standing "investigate first" rule.

## GPU/system notes

- At peak this session, 4 qwen3:30b jobs ran concurrently (only one Ollama instance, all requests serialize/queue).
- User asked whether Task 2/4.5 could run on CPU instead to relieve GPU contention. Answer given: technically possible (qwen3:30b is a mixture-of-experts model, ~3B active params/token, so CPU isn't catastrophic the way it would be for a dense 30B model) but NOT recommended right now — this is a shared machine, only ~10GB RAM free with swap 90% full, almost entirely from other users' processes (a `toolbox_app` gunicorn service alone uses ~113GB RSS). Loading a second ~20GB CPU-only model copy risks destabilizing the shared box. Held off.
