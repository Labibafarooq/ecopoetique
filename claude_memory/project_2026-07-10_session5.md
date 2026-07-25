---
name: project-2026-07-10-session5
description: "2026-07-10 evening session (45-min GPU-window sprint): drafted Riccardo email on Task4.5 P/CH + Task2 DE_PARANGON ambiguities; diagnosed ESPACE drop as pre-existing model bias not a resume bug; added invented few-shot examples to both Task 4.5 and Task 2 prompts and relaunched both"
metadata: 
  node_type: memory
  type: project
  originSessionId: 3256f2bc-4a07-49b8-9f01-a7296bdd2f68
---

Continuation of [[project_2026-07-10_session4]], same day, evening. Labiba got a 45-minute GPU window and asked to move fast.

## Email drafted for Riccardo (not yet sent by Labiba)

Saved to `/tmp/claude-1013/-home-lfarooq/3256f2bc-4a07-49b8-9f01-a7296bdd2f68/scratchpad/email_riccardo_draft.txt` (scratchpad — will not persist across sessions, treat as reference only; regenerate from this memory's content if needed later). Covers two open ambiguities from [[project_2026-07-10_session4]]'s Bucket 3 findings:
- **Task 4.5**: the P vs CH contradiction — 6 person-referent rows (jument/singe/ânes/porc/aigle-Henri-Beyle/chacal-Pierre-Castaneda) gold-labeled P despite matching Riccardo's own rat/il/CH rule exactly, plus the reverse case (fougère/"mon penser" gold=CH despite reading like his own mes-émotions/P example).
- **Task 2**: DE_PARANGON vs DE_PROP (guimauve/"poings de guimauve" and raisins/"raisins de la domination", both gold=DE_PROP but structurally parse like DE_PARANGON) and META_APP vs DE_PARANGON (perroquet, chevreuil).
Labiba has not confirmed sending it yet.

## ESPACE drop investigated — confirmed NOT a resume bug

Labiba suspected the resume (session 4, killing the ESPACE-only detour and going back to the full v9 run) broke something, since ESPACE went from a 72.7% mid-run checkpoint down to 62.7% final. Investigated by splitting the final 60-novel `resultats_task0_mapreduce_v9.csv` into pre-resume (first 33 rows) vs post-resume (last 26 rows):
- Pre-resume ESPACE: 24/33 = 72.7%
- Post-resume ESPACE: 13/26 = 50.0%
- Confirmed via code inspection: zero code changes occurred to `run_task0_mapreduce_v9.py` between the kill and the resume — the ESPACE-only detour (`run_task0_v9_espace_only.py`) wrote to a completely separate output file and never touched `resultats_task0_mapreduce_v9.csv`.
- Root cause: the model has a persistent, pre-existing bias toward over-predicting **ESP_UNIT** (predicted UNIT 51.5% of the time in the pre-resume batch too, vs only 36% gold-UNIT there) — same "default-collapse" failure family as FOCALISATION's FOC_ELARG bug and REGIME/TEMPORALITÉ's FANT/DESORD 0%-recall bug from session 4. The pre-resume batch (novels A-P alphabetically) just had fewer ESP_ITIN gold novels (6/33=18%) to expose this bias; the post-resume batch (Q-Z, includes "Le grand marin," "GPS," "En remontant les ruisseaux," "Buffalo Bill Cody" — genuine travel narratives) had proportionally more (8/26=31%), so the same bias produced more visible errors. **Nothing to fix in the resume mechanism itself** — this is a fourth instance of the same systemic "over-predict the common/default category" bug pattern across FOCALISATION, REGIME, TEMPORALITÉ, and now ESPACE, still undiagnosed/unfixed as of this session.

## 45-minute sprint: few-shot examples added to both Task 4.5 and Task 2

Time-boxed because Labiba had to give the GPU back. Moved fast, minimal discussion.

**Task 4.5** (`comparison/run_task45_compare_category.py`): added one invented (never gold-set) contrastive example per category (CH/P/NH/O/E/A) directly after the category list in the prompt — e.g. "Pierre courait comme un lièvre, le souffle court" → CH (person target); "Sa jalousie rôdait comme un loup affamé" → P (emotion is its own grammatical subject); "Le mariage, cette cage dorée, l'étouffait" → A (institution). Applied ON TOP of session 4's bucket-1/2 fix (which was already mid-run at 20/112 rows, 85% on those). Killed and relaunched with `--resume` semantics (the script's built-in done-id skip) so the first 20 rows stay bucket-fix-only and the remaining ~92 pick up the new few-shot version — **this mixes two methodologies in one output file**, a deliberate tradeoff for speed under the 45-min constraint, not the project's usual clean-methodology-per-file practice. Flag this if the final number looks anomalous — check whether the first-20 vs rest split shows a discontinuity, same technique used to catch the ESPACE resume question above. New log: `task45_gold_validation_v7_fewshot.log`. At last check: 21/25 = 84.0%, still running.

**Task 2** (`métaphore/validate_task2_gold.py`): **caught a real bug before it wasted the time budget** — naively relaunching would have done nothing, because the existing `resultats_task2_gold_validation.csv` already had all 114 gold ids marked done from the earlier META_JUXT-only run, and the script's resume logic skips any id already present in the output file. Killed immediately (PID 46382, <2s old), backed up the stale file to `resultats_task2_gold_validation_PRE_FEWSHOT_20260710.csv`, relaunched fresh (PID 46510) so all 114 rows actually get re-scored with the few-shot prompt additions from earlier in session 4 (the ones that only scored 2/10 on a 10-row targeted smoke test — this is the first time they're being tested on the full gold set rather than just the targeted problem rows). New log: `task2_gold_validation_v8_fewshot.log`. Just started, 0 rows scored yet.

## State at end of this session (both running concurrently, sharing the 45-min GPU window)

- Task 4.5 (few-shot on top of bucket-fix): running, PID 45485, 21/25=84.0% so far — **note the methodology split at row 20** when reading final numbers
- Task 2 (few-shot, fresh run): running, PID 46510, just started
- Task 0 v9 (full 7-criteria): finished this session (final numbers in [[project_2026-07-10_session4]]) — 59.8% overall, TYPE 93.2% strongest, INTRIGUE 42.4%/MODE 39.0% weakest
- Riccardo email: drafted, not sent
- GPU handback deadline: Labiba said ~45 minutes from when she asked (message timestamp context implies around 17:45-18:30ish this session) — check with her whether both runs should be paused/killed if they're not done when she needs to return the GPU, rather than leaving them running unsupervised past the deadline.
