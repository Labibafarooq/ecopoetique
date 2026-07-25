---
name: project-dh-humanistica-app
description: "DH Humanistica (formerly 'Ask Labiba') — a separate Streamlit RAG app on port 8505, owned by another Linux account (malrahabi/root); fixed the Qwen3 30B empty-answer bug, trimmed the model dropdown, locked the Streamlit theme to dark, and (later session) ported the rebrand + onboarding modal from mockup into real deployed code"
metadata:
  type: project
  originSessionId: 4399579f-a047-4e1d-80ef-899d3cabef1b
---

## What this is

A Streamlit RAG (retrieval-augmented generation) app for digital humanities researchers, separate from the main [[project-ecopoetique]] work. Built for "Formation HANDS — Sorbonne Université". Runs on `localhost:8505` via `streamlit run pipeline/ask_labiba.py`.

**Ownership/access gotcha**: the app's source lives at `/home/malrahabi/ragHumanistica/pipeline/ask_labiba.py`, owned by a different Linux account (`malrahabi`) and the running process itself is owned by **root**. `lfarooq` (this account) has no read/write access there and no sudo. Labiba has sudo access under her own `labiba` account on the same box (`obtic-gpu1`) and does all the actual privileged file operations herself, pasting the terminal output back — I give her the exact commands each time, she runs them.

**Working copy**: `/home/lfarooq/ask_labiba.py` is a copy `labiba` pulled over and chowned to `lfarooq` so I can read/edit it directly. All edits happen there, then get copied back with `sudo cp` + a restart.

## Fixes applied (2026-07-09/10 session)

1. **Rebrand**: title changed from "Ask Labiba" to "🤖 DH Humanistica", subtitle from "Humanistica RAG · ERC Modern · Sorbonne Université" to "by Obtic · SCAI". Guide/info panel now ends with a Contact — Obtic section linking `labibafarooq23@gmail.com`.

2. **Qwen3 30B returned sources but no LLM answer — root cause found and fixed.** `call_ollama()`'s request to Ollama used `num_predict=max_tokens` (sidebar slider default 512). Qwen3 reasons internally before answering and burns the entire token budget on that reasoning — confirmed live against the actual server: at 512 tokens, `done_reason: "length"`, `response` came back completely empty. Fixed by flooring `num_predict` to at least 1500 specifically for `qwen3:30b` regardless of the slider. **Second layer of the same bug**: even with `"think": false` passed to the Ollama API, Qwen3 still emits raw reasoning text inline in the `response` field (sometimes with no opening `<think>` tag, only a stray closing `</think>`) — first attempted fix (`re.sub(r"<think>.*?</think>", ...)`) silently failed to match this asymmetric case and let the raw chain-of-thought leak straight into the UI. Real fix: `if "</think>" in answer: answer = answer.rsplit("</think>", 1)[1]`. Verified end-to-end against the live server using the actual function from the edited file, not a reimplementation — clean answers now, no leakage, no truncation. Same failure pattern as this account's own ecopoetique Task 2/4.5 qwen3 work — see [[feedback-qwen3-truncation-pattern]].

3. **Model dropdown trimmed to reality.** Checked the actual Ollama server (`ollama list` + `/api/tags` on both 11434 and 11435): only `qwen2.5:7b` and `qwen3:30b` are real, working text models. `qwen2.5vl:72b`/`qwen72b-limited` exist but are vision-language variants, not usable as the plain-text 72B the code expected. No 14B or LLaMA 3.1 model exists on the server at all. Removed Qwen2.5 14B, Qwen2.5 72B, and LLaMA 3.1 8B from both the sidebar `model_options` list and the `call_llm()` routing map — only Qwen2.5 7B and Qwen3 30B remain, each keeping their exact original label text. The greyed-out "🌐 Mistral API — staff use only" banner was untouched — it was never a real dropdown option to begin with (a static disabled-looking `<div>` below the real selectbox, not part of `model_options`).

4. **Onboarding wizard modal** (built first in a standalone HTML mockup artifact, not yet ported into the real `.py` — see below) — the guide/info panel now opens as a forced-read modal on first load; user must click "✓ J'ai lu — Fermer" before it dismisses into the existing right-hand info rail. The "open guide" toggle button was relocated from below the preset-style heading to directly under the language toggle button, top-right.

5. **Light/dark theme inconsistency — found and fixed.** User reported parts of the app staying white regardless of OS/browser dark mode. Root cause: `ask_labiba.py`'s custom CSS only overrides specific classes it targets (title, cards, buttons, banners) — it never defines a full theme pair. Streamlit's own native chrome (the built-in ⋮ menu with Deploy/Settings/Theme picker, and any native widget the custom CSS doesn't touch) falls back to Streamlit's own base theme, which without a `.streamlit/config.toml` follows "Use system setting" by default — so native bits render light when the OS/browser is light, fighting the hardcoded-dark custom CSS elements. Not a client-side bug. Fix: created `/home/malrahabi/ragHumanistica/.streamlit/config.toml` with an explicit `[theme]` block (`base="dark"`, matching the app's own palette: `primaryColor="#c9a96e"`, `backgroundColor="#0f1117"`, `secondaryBackgroundColor="#161b27"`, `textColor="#e6edf3"`) so every native widget locks to the same dark palette regardless of viewer OS/browser preference. Confirmed the file exists and is non-empty on the server; visual confirmation from Labiba still pending as of session end.

## Deploy procedure established this session (repeatable)

1. Edit `/home/lfarooq/ask_labiba.py` (the readable/writable copy).
2. Labiba backs up the live file first: `sudo cp .../ask_labiba.py .../ask_labiba_BACKUP_<timestamp>.py`
3. `sudo cp /home/lfarooq/ask_labiba.py /home/malrahabi/ragHumanistica/pipeline/ask_labiba.py`
4. `sudo pkill -f "streamlit run pipeline/ask_labiba.py --server.port 8505"`, then verify with `ps aux | grep ask_labiba` that nothing is left before relaunching (same discipline as [[feedback-task1-duplicate-process-incident]] — a `pkill`/`kill` step must be verified dead, not trusted blindly).
5. Relaunch via `sudo bash -c 'cd /home/malrahabi/ragHumanistica && source venv/bin/activate && nohup streamlit run pipeline/ask_labiba.py --server.port 8505 > /tmp/ask_labiba.log 2>&1 &'` (needs the `sudo bash -c` wrapper since a plain `cd` into that directory is permission-denied for `labiba`'s own shell).
6. I verify the restart from the `lfarooq` side via `ps aux`/`ss -tlnp`/`curl localhost:8505` — I can see process/port/HTTP state fine even though I can't read the file itself.

## Rebrand + onboarding modal ported to real code (2026-07-09, later session)

Previously only the HTML mockup artifact had the rebrand/onboarding — now actually implemented in `/home/lfarooq/ask_labiba.py` and deployed:

- Title → "🤖 DH Humanistica", subtitle → "by Obtic · SCAI", page title → "DH Humanistica".
- Contact — Obtic block (`labibafarooq23@gmail.com`) added to both the side info-rail (fr/en) and the new onboarding modal.
- Onboarding modal implemented with real `st.dialog()` (Streamlit ≥1.31), not the mockup's fake HTML/CSS/JS overlay — forced-read popup on first load, dismiss button sets `st.session_state.onboarding_seen=True` and reveals the side rail. Includes a feature-detection fallback (`hasattr(st, "dialog")`): if the server's Streamlit predates 1.31, skips the forced popup with no crash and just shows the side rail by default (unconfirmed which path fires on this server as of session end — need to check `streamlit.__version__` in the venv).
- Confirmed the mockup's sidebar model list was stale (still showed the old 5 models) — did NOT copy that back; kept the already-trimmed 2-model list (Qwen2.5 7B, Qwen3 30B) from the earlier fix intact.
- Deployed via the procedure below; new process confirmed listening on 8505 (PID 3757271 at deploy time).
- The static HTML mockup artifact itself was left untouched — it's a separate preview, not source of truth; the .py is now the up-to-date implementation.

## Not yet done as of this session end

- Confirm whether `st.dialog` is actually available in the server's Streamlit version (determines whether the forced onboarding modal or the plain-rail fallback is what's live).
- Visual/UX confirmation from Labiba that the onboarding modal renders and dismisses correctly in the browser.
- Visual confirmation from Labiba that the light/dark theme fix actually resolved the white-patch issue is still pending (carried over from prior session).
