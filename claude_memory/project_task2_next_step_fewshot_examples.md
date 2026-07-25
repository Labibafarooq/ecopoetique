---
name: project-task2-next-step-fewshot-examples
description: "Task 2's next planned improvement: add contrastive few-shot examples for its worst confusion pairs, queued after the current 2026-07-10 gold runs finish"
metadata: 
  node_type: memory
  type: project
  originSessionId: 3256f2bc-4a07-49b8-9f01-a7296bdd2f68
---

Next planned change to `métaphore/run_task2_subcategories.py`, explicitly requested by Labiba to hold until the in-flight gold runs settle.

**What**: currently each of Task 2's 18 subcategories gets at most one inline canonical example (e.g. "mémoire d'éléphant" for DE_PARANGON); LOC_IDIOM is the only one with several (~9 across 4 syntactic forms). The 69.3% gold run (114 rows, pre-META_JUXT-fix) showed this is a real gap at two boundaries:
- META_ATTR ↔ LOC_IDIOM (4 of the run's errors — surnommage like "on le traite de macaque" misread as a frozen idiom)
- DE_PARANGON acting as a false-positive sink for DE_PROP / META_APP / COMME_SN (6 errors landing there)

**Why**: single examples per category aren't enough to teach the model the actual discriminator at a boundary; it needs two near-identical-surface-shape cases side by side with different correct answers.

**Constraint**: examples must be hand-written/generic, never pulled from the gold CSV or real corpus novels — a standing rule from Task 0/1 work (`feedback_ecopoetique_experiments.md` #8) to avoid overfitting the prompt to the eval set. Riccardo/Labiba were firm about prompts staying purely definitional.

**How to apply**: once the current Task 2 (META_JUXT-elimination, [[project_2026-07-10_session3]]) and Task 4.5 (entity-type fix) gold runs both finish and are reported, write 2-3 invented contrastive example pairs for each of the two boundaries above directly into the relevant decision-tree question in `make_prompt()`, then re-run `validate_task2_gold.py` fresh (move the prior output aside first, per this project's standard practice) to isolate the effect of just this change.
