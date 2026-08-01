---
name: source_processor
description: Worker subagent (one per source, ×N parallel) — runs the source-type connector then the domain adapter, writing that source's context_set slice + manifest entries.
skill: core/skills/source_processor.skill.md
user_invocable: false
---

# source_processor — Claude overlay wrapper

Thin tool-specific wrapper (FR-XS-08, FR-XS-19, D9). **The logic is not here.** It lives in
the one shared skill; this file only points Claude at it and states how this overlay runs it.

**Load and execute `core/skills/source_processor.skill.md`** against **one** `UI_INPUT.sources[]`
entry (plus auth via the seam). Follow that skill verbatim — do not restate, summarize, or fork
its procedure here.

- **Executor:** **worker subagent** in its own context window (`user_invocable: false`), spawned
  by the orchestrator — **one per source, fanned out in parallel**. Run autonomously and return a
  concise summary — do not start a chat.
- **Produces:** that source's `context_set/<source>/` slice + manifest entries (code → runs the
  connector clone, then hands off to a `code_map_build` subagent). Fan-in to `index.json` is a
  separate deterministic step (`merge_manifest.py`).
