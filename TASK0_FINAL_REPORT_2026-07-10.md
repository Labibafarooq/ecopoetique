# TASK 0 — NARRATOLOGY (7 CRITERIA): RESULTS SO FAR
## Écopoétique — Narratological Classification
**Date:** 2026-07-10
**Author:** Labiba Farooq
**Supervisor:** Riccardo Barontini
**Status:** Active, not finalized — this report captures the state of the hybrid comparison as of today; v10-family experiments (isolated reduce-step `think=True` fix) are still in progress and NOT included here.

Task 0 classifies each novel along 7 narratological dimensions (TYPE NARRATEUR, FOCALISATION, MODE NARRATIF, RÉGIME NARRATIF, ESPACE, INTRIGUE, TEMPORALITÉ) via qwen3:30b map-reduce, scored against a hand-annotated gold set.

---

## ⚠️ IMPORTANT: TWO DIFFERENT, NON-COMPARABLE GOLD SETS EXIST

There are two gold sets in this project, and they are **not interchangeable**:

1. **`GOLD_narratologie_60novels_original.csv`** — the original 60-novel gold set. Uses the **old** narratological schemes throughout.
2. **`GOLD_narratologie_0807.csv`** — the current, 79-novel gold set Riccardo sent later, covering all 60 original novels + 19 new ones.

**Verified directly (code-vocabulary diff between the two files) — what actually changed:**

| Criterion | Changed? | Detail |
|---|---|---|
| **FOCALISATION** | **Yes — completely different scheme** | Old: `FOC_INT`/`FOC_EXT`/`FOC_ZERO`/`FOC_VAR` (whose-consciousness framework). New: `FOC_RFOC`/`FOC_ELARG`/`FOC_REST`/`FOC_MIXTE` (reader-vs-character-knowledge framework). These are not just renamed — they're a different analytical question. Old-scheme predictions score a hard 0% against the new gold, and vice versa. |
| **TYPE NARRATEUR** | **Yes — 2 new codes added** | New gold introduces `NAR_AUTO` and `NAR_VAR`, absent from the old 60-novel gold (used on 3 of the 79 novels: 1× `NAR_AUTO`, 2× `NAR_VAR`). Everything else in this criterion is unchanged. |
| MODE NARRATIF | No | Schema documentation mentions a new `MOD_DIA` category was proposed, but it's **not actually used on any of the 79 currently-annotated gold novels** — exists in principle, not yet exemplified. |
| RÉGIME NARRATIF | No | Identical code vocabulary. |
| ESPACE | No | Identical code vocabulary — but individual novel labels can still be corrected between file versions (see the `Bienne-Gisele_La-malchimie.txt` example below, a real case found this session: `ESP_UNIT`→`ESP_FRAG`). |
| INTRIGUE | No | Identical code vocabulary. |
| TEMPORALITÉ | No | Identical code vocabulary (one stray artifact in the old file, not a real scheme change). |

**Bottom line: FOCALISATION results from the two gold sets can never be compared. TYPE NARRATEUR is 97% comparable (only 3/79 novels touch the 2 new codes). Everything else is directly comparable, modulo occasional individual label corrections.**

---

## HYBRID TABLE — v1 through v9, scored against the OLD 60-novel gold set

This is **not** the current/final gold set — it's the older 60-novel one. Every `resultats_*.csv` file in `narratologie/` (excluding paid GPT-4o runs and the still-in-progress v10-family) was re-scored fresh against `GOLD_narratologie_60novels_original.csv`, joined by filename, ignoring each file's own embedded gold/correct columns.

| Criterion | Best file | Score | N |
|---|---|---|---|
| **TYPE NARRATEUR** | `chunk_classifier_60novels.csv` | **93.3%** | 60 |
| **FOCALISATION** | `resultats_task0_v5.csv` | **77.2%** | 57 |
| **MODE NARRATIF** | `chunk_classifier_60novels.csv` | **71.7%** | 60 |
| **RÉGIME NARRATIF** | `hybrid_v2.csv` / `hybrid_v3.csv` / `hybrid_v4.csv` / `qwen3_30b_mapreduce.csv` | **76.7%** | 60 |
| **ESPACE** | `resultats_task0_mapreduce_v9.csv` | **73.3%** | 15 |
| **INTRIGUE** | `chunk_classifier_60novels.csv` / `hybrid_v2.csv` / `hybrid_v3.csv` / `qwen3_30b_mapreduce.csv` | **68.3%** | 60 |
| **TEMPORALITÉ** | `hybrid.csv` / `hybrid_v4.csv` | **71.7%** | 60 |

**Caveats on this table:**
- **FOCALISATION (v5, 77.2%)** is only valid under the *old* scheme. It cannot be compared to, or combined with, any current-gold FOCALISATION number. `chunk_classifier_60novels.csv` uses genuine leave-one-out cross-validation (verified directly in `train_chunk_classifier_60novels.py` — not a leaky/overfit number).
- **ESPACE (v9, 73.3%)** is on only **15 of the 60** novels — that run was never finished at full scale. Every other local file caps out at 53.3% or below for ESPACE (checked exhaustively, all 29 files with an ESPACE column). 73.3% is the best available local result, kept as the pick, but it's an unconfirmed-at-scale number, not a robust 60-novel score like the rest of the table.
- Several apparent "winners" were discarded for having too few novels to trust: `task0_focalisation_new.csv` scored 100% TYPE NARRATEUR / 83.3% MODE / 83.3% INTRIGUE, all on just 5-6 novels — not used.

**Next step, not yet run**: extend v9's ESPACE run to the remaining novels (45 to complete the 60-novel gold set, or 64 to cover the current 79-novel gold set) to confirm the 73.3% figure at scale. Estimated ~6.8 min/novel (measured directly from the original run's 15 per-novel timings) → **~5.1 hours** (45 novels) or **~7.3 hours** (64 novels), GPU time only, on top of whatever else is sharing the GPU.

---

## STILL TO DO / IN PROGRESS

- **v10c** (reduce-step `think=True` for FOCALISATION/RÉGIME/TEMPORALITÉ, against the *current* 79-novel gold) — running as of this report, not yet finished, not included in the table above. Will get its own comparison against v10b's 60.0% baseline once complete.
- **ESPACE at full scale** — v9's promising 73.3% needs the remaining novels run to confirm it's not a small-sample artifact.
- **FOCALISATION on the current gold set** — only v10-family has ever attempted the new scheme; no v1-v9 comparison is possible there by construction.
