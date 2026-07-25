---
name: feedback-finding-true-process-output
description: "How to locate where a running process's stdout/logs actually go when launch command/nohup redirection isn't obvious, and the sudo-interactivity limit on this box"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 4ef39eda-39cb-4577-ad6e-4d8a11f2b40f
---

When a background process's real progress/log output isn't in an obviously-named file (no `nohup.out` in the cwd, log file name doesn't match the script name), check what its stdout/stderr file descriptors actually point to:

```bash
ls -la /proc/<PID>/fd | grep -i log
readlink -f /proc/<PID>/fd/1   # stdout target
```

**Why:** wasted time on 2026-07-09 grepping for `*plantes*log*` and computing progress from `wc -l` on raw input CSVs before realizing the running Task1 process had its own internal progress log with authoritative row counts, percentage, speed (s/row), and ETA, redirected to a non-obviously-named file discovered only via `/proc/<PID>/fd/1`. The script's own progress log is always more trustworthy than deriving stats from file sizes/row counts externally — check for one before computing anything.

**Sudo interactivity limit**: this agent's Bash tool runs in a non-interactive shell that cannot supply a sudo password or reuse a user's already-authenticated sudo session, even when the user just typed their password moments earlier in their own terminal. Any `sudo` command needed on `obtic-gpu1` (or similar remote/shared boxes) must be run by the user (Labiba) in her own terminal, with output pasted back — see [[project-dh-humanistica-app]] for the concrete workflow this produced (edit locally as `lfarooq`, hand exact commands to Labiba to run as `labiba` with sudo, she pastes results back).

**How to apply:** before computing a completion percentage or ETA from file sizes, check whether the target script logs its own internal metrics via a progress log first, and locate that log via `/proc/<PID>/fd` if its path isn't obvious. Never assume this session's Bash tool can execute sudo directly — always hand sudo-requiring commands to the user to run themselves.
