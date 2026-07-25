---
name: feedback-qwen3-truncation-pattern
description: "Any qwen3:30b prompt asking for multi-step reasoning (decision trees, CMT-style chains) with num_predict below ~5000 silently returns empty content — diagnose via done_reason/eval_count, not accuracy alone."
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 45e552b8-6459-4048-b605-6251b4b21c19
---

Builds on [[project-2026-07-09-session]].

## The bug pattern

qwen3:30b (run via Ollama, thinking mode on) counts its invisible `<think>...</think>` reasoning against the SAME `num_predict` budget as its visible answer. Any prompt that asks the model to work through several sequential questions before answering (a decision tree, a CMT vehicle→target→ground→verify→classify chain, etc.) gives it a lot to narrate through in `<think>` — and if `num_predict` is set low (Task 2 had 3000, Task 4.5 had 3000), the model can burn the ENTIRE budget reasoning about just the first question and never emit the final JSON answer at all.

Found 2026-07-09 in two places at once: Task 2's 14-step decision-tree prompt (51.8%→had 17/114 UNKNOWN) and Task 4.5's 5-step CMT-chain prompt (39.4%→had 48/104 UNKNOWN, worse than the simpler prompt it replaced). In both cases the "redesign looks worse than before" story was mostly this bug, not a bad idea — Task 4.5's CMT technique (from arxiv 2502.01901) may be totally fine; it was never actually tested because it never got to finish.

## How to diagnose it directly (don't guess from the UNKNOWN rate alone)

Reproduce ONE failing row outside the pipeline:
```python
resp = requests.post(OLLAMA_URL, json={"model": MODEL, "messages": [...],
    "stream": False, "options": {"temperature": 0, "num_predict": N, "num_ctx": 16384}})
data = resp.json()
print(data.get("done_reason"), data.get("eval_count"), repr(data["message"].get("content","")))
```
`done_reason: "length"` + `eval_count == num_predict` + `content: ""` (with `thinking` full of an unfinished train of thought) is the unambiguous signature. This is NOT the same as a genuine parse failure (malformed JSON, wrong code) — those still have content, and NOT the same as `done_reason` being anything else (a connection/timeout issue, seen separately as `ERROR` rows, 3/111 in Task 2's case — different bug, not yet diagnosed).

## How to apply
- Before trusting any accuracy number from a new/redesigned multi-step qwen3 prompt, check the UNKNOWN/ERROR rate first. If it's double-digit percent, suspect truncation before suspecting the prompt logic itself.
- Fix: raise `num_predict` to ~8000 for anything asking for 3+ sequential reasoning steps. This was sufficient for both Task 2 and Task 4.5's redesigns (single call took ~30-80s at that budget, still well under a 300s timeout).
- Re-validate BOTH the old and new prompt at the higher budget before concluding which one is actually better — a "regression" found at low num_predict may just be measuring who happened to burn through their thinking budget faster, not real prompt quality.
