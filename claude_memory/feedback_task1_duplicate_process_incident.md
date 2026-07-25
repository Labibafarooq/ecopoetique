---
name: feedback-task1-duplicate-process-incident
description: "Task 1's orchestrator restart step killed the wrong PID (off-by-one), leaving two run_task1_corpus.py processes writing to the same output CSV for ~7.5 hours — fixed 2026-07-09, but any future automated kill+relaunch of this script needs a verified-dead check."
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 45e552b8-6459-4048-b605-6251b4b21c19
---

Builds on [[project-2026-07-08-session]].

## What happened (2026-07-09 morning)

The overnight orchestrator (`orchestrate_task0_after_2_45.sh`) tried to stop Task 1 (`run_task1_corpus.py --category plantes`, PID discovered via `pgrep -f`) before relaunching it. It logged `"Task 1 (PID 3256944) stopped."` but PID 3256944 never existed — off by one from the real PID 3256945. The `kill` silently no-opped (or hit an unrelated/nonexistent PID) and the script's linear structure didn't verify the process actually died before launching a fresh one at 01:56:59.

Result: **two instances of the same script ran concurrently for ~7.5 hours**, both with the output file open for writing (confirmed via `lsof` — same inode). This produced 3,529+ exact-duplicate rows in `resultats/task1_plantes_labels.csv` (found by full CSV-aware parse, not naive line/awk counting — naive `awk -F'\t'` field-count checks gave false-positive "malformed row" signals because the `contexte` field legitimately contains embedded newlines inside quoted CSV values).

## Fix applied
Killed both PIDs, backed up the corrupted file (`task1_plantes_labels_CORRUPTED_BACKUP_<timestamp>.csv`), deduped via `csv.reader` (not naive text splitting) keeping first-seen rows, replaced the live file, relaunched a single instance, and confirmed via the log's own `"Resuming: N rows already done"` line that N was sane (48,848) rather than assuming success.

**Why:** the resume logic keys done-rows by `(fichier, token_lexique, contexte)` tuple loaded fresh at each process startup — it has no locking or shared state between concurrent instances, so two instances don't just double-process rows, they actively race on file writes and can produce non-atomic partial-row corruption too (though this incident's damage was limited to clean full-row duplicates, not truncated writes).

## How to apply
- **Never trust a script's own "process stopped" log line** for this project's long-running jobs — always independently verify via `ps`/`pgrep` that the PID is actually gone before relaunching, especially in unattended/orchestrator scripts.
- Before trusting any CSV-corruption diagnosis, parse with the real CSV library (respecting quoting/embedded newlines), not `awk`/naive line splitting — the latter produces false corruption signals on any file where free-text fields can contain literal newlines or delimiters.
- If a future orchestrator script needs to kill-and-relaunch `run_task1_corpus.py` (or similar), add an explicit post-kill liveness check (e.g. loop until `pgrep -f <pattern>` returns nothing, with a timeout/abort) rather than a single `kill` + fixed sleep.
