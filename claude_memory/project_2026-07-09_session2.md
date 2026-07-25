---
name: project-2026-07-09-session2
description: "2026-07-09 evening session — Task 1 plantes continued running healthy (~83% at session end, single process, no duplicate-process recurrence); most of the session was spent on a separate app, DH Humanistica (see [[project-dh-humanistica-app]]), not on the core ecopoetique pipelines"
metadata:
  type: project
  originSessionId: 4399579f-a047-4e1d-80ef-899d3cabef1b
---

Builds on [[project-2026-07-09-session]], [[project-task0-task1-status]], [[feedback-task1-duplicate-process-incident]].

## Task 1 (plantes) — status at session end (~19:30)

**57,631/69,314 rows (83.1%)**, speed 3.8s/row, ETA ~12.3h, single healthy process (PID 3534857, confirmed no duplicates), 8 failed batches (stable count, not growing — needs a small retry pass once the main run finishes, same as noted in the prior session's memory). On track to finish overnight into 2026-07-10. No new restarts happened this session — it just kept running untouched in the background the whole time.

Task 0/Task 2/Task 4.5 work from the prior 2026-07-09 session (queued next steps: REDUCE-step think=True experiment for RÉGIME/TEMPORALITÉ, Task 2 few-shot idiom examples test, Task 4.5 re-test) was **not touched this session** — still exactly where [[project-2026-07-09-session]] left them, pick up from there next time.

## Most of this session was a detour into a separate app: DH Humanistica

Full details in [[project-dh-humanistica-app]] (new memory file, read that first for anything related to this app going forward). Short version: Labiba has a Streamlit RAG app for DH researchers running under a different Linux account (`malrahabi`, root-owned process) on port 8505, originally called "Ask Labiba". This session: pulled a copy of its source out via Labiba's sudo access, found and fixed a real bug (Qwen3 30B was silently returning empty answers — a token-budget/thinking-mode issue, confirmed live against the Ollama server), trimmed the model dropdown to only the models actually downloaded, rebranded it to "DH Humanistica / by Obtic · SCAI", and diagnosed+fixed a light/dark theme inconsistency by adding a `.streamlit/config.toml` theme block. Also built a separate static HTML mockup artifact of the app's UI (onboarding-wizard modal design, contact block, relocated guide button) that has **not yet been ported into the real Python file** — that's the next concrete piece of unfinished work on this app if Labiba wants to continue it.

## Established this session — cross-account deploy pattern for this app

Because `lfarooq` has no access into `malrahabi`'s files, all real deploys to the live app go through Labiba's own sudo-capable `labiba` account on the same machine (`obtic-gpu1`), following the exact backup → copy → kill-verify-dead → relaunch sequence documented in [[project-dh-humanistica-app]]. This is a different access pattern from the rest of the ecopoetique work (which all runs directly as `lfarooq`) — worth remembering so I don't assume direct file access next time this app comes up.
