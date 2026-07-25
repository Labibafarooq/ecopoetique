---
name: project-gpu-freeze-20260710
description: No GPU access for the écopoétique project from 2026-07-10 for 12 days (until ~2026-07-22) — do not launch any qwen3/Ollama job during this window without checking with Labiba first
metadata: 
  node_type: memory
  type: project
  originSessionId: 3256f2bc-4a07-49b8-9f01-a7296bdd2f68
---

Starting 2026-07-10 (end of day), Labiba does **not have GPU access for the next 12 days** (until approximately **2026-07-22**).

**Why**: she had a temporary 45-minute GPU window borrowed from someone else that evening and had to hand it back — implies the shared A40 GPU is now unavailable to her for an extended period.

**How to apply**: do NOT launch, resume, or relaunch any script that calls Ollama/qwen3:30b (`localhost:11435`) during this window without explicitly checking with Labiba first, even if it looks like a quick validation. This affects every pipeline in [[project_ecopoetique]] that depends on the shared GPU:
- Task 0 (narratology, all variants: v9, v10c/v10d)
- Task 1 (référentiel/figuré)
- Task 2 (metaphor subcategories)
- Task 4.5 (compare-target classification)
- The DH Humanistica Streamlit app ([[project_dh_humanistica_app]]) also uses Qwen3 — likely affected too, worth confirming with Labiba before assuming it's fine to touch.

**Task 3** (agentivity, spaCy dependency parsing) does NOT use the GPU/LLM at all — safe to continue working on freely during this window.

**What can still be done without GPU during the freeze**:
- Prompt/code editing and static review (no live testing)
- Data analysis on already-collected results (gold validation CSVs, confusion matrices, etc.)
- Writing up findings, drafting emails to Riccardo
- Task 3 work
- Planning the next round of fixes so they're ready to launch the moment GPU access returns

## State of each GPU-dependent task when the freeze began (2026-07-10 evening)

- **Task 4.5**: finished its few-shot-examples round at **85/104 = 81.7%** (final, not partial) — best result of the session, up from 78.8% baseline. See [[project_2026-07-10_session4]] and [[project_2026-07-10_session5]] for the full fix history (entity-type rule, bucket-1/2 voice/idiom fixes, few-shot examples). Post-hoc analysis of these 104 rows found 4 more error buckets (Bucket 2: my own voice/chant→A fix over-firing on bodily-effect passages; Bucket 3: missed idioms like "sa pomme"/"les chiens ne font pas des chats"; Bucket 4: genuinely ambiguous E/O/A boundary cases) — not yet fixed. **Riccardo answered the P/CH question same day**: it's not simply "target=person→CH" — a further physical-vs-psychological/behavioral split applies when the cible is a person (physical body/movement → CH, character/behavior/conduct → P). Implemented in the prompt (`comparison/run_task45_compare_category.py`) but **NOT YET TESTED** — full details and his exact wording in [[feedback_task45_category_is_target_entity_type]]. This is the first thing to validate once GPU access returns.
- **Task 2**: **paused mid-run** at 43/114 rows (few-shot version, `métaphore/resultats_task2_gold_validation.csv`) — progress saved, resumable via `validate_task2_gold.py`'s built-in done-id skip once GPU access returns. Early signal was weak/flat (69.8-74.2%, not clearly above the 73.7% baseline) — the DE_PARANGON/DE_PROP ambiguity likely needs Riccardo's input more than further prompt tuning; see the drafted email in [[project_2026-07-10_session5]]. **Riccardo replied same day**: he needs to check his own references and will answer "first thing tomorrow" (2026-07-11) — follow up if nothing arrives by then.
- **Task 0 v9** (full 7-criteria): finished, 59.8% overall (TYPE 93.2% strongest, MODE 39.0%/INTRIGUE 42.4% weakest). See [[project_2026-07-10_session4]].
- **Task 0 v10c** (new FOCALISATION scheme): finished, 32.9%/60.8%/68.4% (FOC/REG/TEM). The FOC_ELARG-collapse bug was diagnosed and a first fix attempted but only scored 1/4 on smoke test with a regression — not resolved, needs more work once GPU returns. REG_FANT and TEMP_DESORD both showing 0% recall (opposite failure direction, under-triggering) — diagnosed but not yet root-caused (need to replay actual misclassified novels' raw observations before proposing a fix, per this project's "investigate first" rule).
- **ESPACE** in the full v9 run showed the same default-collapse pattern (over-predicts ESP_UNIT) — confirmed via investigation this session to be a real pre-existing model bias, not a resume bug. Undiagnosed/unfixed.

**Recommended next steps for whenever GPU access returns**: prioritize (1) sending Riccardo's email and waiting for his answers on the two ambiguities before touching Task 2/Task 4.5 further, and (2) the FOCALISATION/REGIME/TEMPORALITÉ/ESPACE default-collapse family of bugs in Task 0, which is now a confirmed recurring pattern across 4 different criteria and probably deserves a general architectural fix (e.g., evidence-count-based aggregation like the FOCALISATION attempt, but tuned better) rather than one-off patches per criterion.
