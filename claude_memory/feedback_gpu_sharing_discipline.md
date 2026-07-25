---
name: feedback-gpu-sharing-discipline
description: "Don't restart/re-run a Task 2/4.5/Task 0 validation job on this project without checking first whether Task 1 (or whichever job is running) is meant to have the shared GPU to itself at that moment."
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 45e552b8-6459-4048-b605-6251b4b21c19
---

Builds on [[project-2026-07-09-session]].

## What happened

Applied a fix to Task 2's decision tree, then re-ran its gold validation to verify the fix worked — without asking first. This put Task 2 back on the shared Ollama/GPU instance alongside Task 1, which Labiba had explicitly wanted running alone. She had to stop me: "why did you start task 2? let the gpu only run on task 1 for now."

**Why this matters**: this machine has one shared GPU (A40, 46GB) and all qwen3 jobs (Task 0/1/2/4.5) queue on the same Ollama instance — running two at once measurably slows both (established pattern, e.g. Task 1 dropping from 4s/row to 8-9s/row whenever another job runs concurrently). Labiba manages this tradeoff deliberately and has stopped/started jobs specifically to protect Task 1's throughput multiple times in one session.

## How to apply

Getting permission to make a code fix (e.g. "yes apply the fix") is NOT the same as getting permission to immediately run/validate it, if doing so shares the GPU with another job currently prioritized. Before launching any qwen3/Ollama job on this project:
- Check whether another job is currently running (`pgrep -af run_task`)
- If so, ask explicitly whether it's OK to share the GPU right now, rather than assuming "I was told to fix this" implies "I was told to test it immediately."
- This applies symmetrically to Task 0, Task 1, Task 2, and Task 4.5 — whichever one currently has priority.
