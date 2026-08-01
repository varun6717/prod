---
name: solution_intent_author
description: Interactive Solution Intent v1 authoring session — drives a chat with the operator to produce a source-grounded, CODE-BLIND solution_intent/v1.md over the fixed 18-section contract; gate G1 freezes it.
skill: core/skills/solution_intent_author.skill.md
user_invocable: true
---

# solution_intent_author — Claude overlay wrapper

Thin tool-specific wrapper (FR-XS-08, FR-XS-19, D9). **The logic is not here.** It lives in
the one shared skill; this file only points Claude at it and states how this overlay runs it.

**Load and execute `core/skills/solution_intent_author.skill.md`** against this run's inputs
(`UI_INPUT.yaml` · `si_profile.<domain>.yaml` · `context_set/index.json` · the per-artifact
`<doc>.index.json` indexes + their `.md` extracts). **No code map — v1 is authored code-blind.**
Follow that skill verbatim — do not restate, summarize, or fork its procedure here.

- **Executor:** your own **interactive session**, started by the operator via the `/start-si`
  prompt file (`user_invocable: true`). You drive a chat with the operator.
- **Delegates:** nothing. v1 is code-blind (FR-SI-02); `code_impact` is Arm 1 of enrichment and
  runs after G1, not here.
- **Gate:** produces `solution_intent/v1.md`; `solution_intent_validator` scores it → operator
  gate **G1**. Acceptance **freezes** v1 — enrichment then writes `v2.md` and never edits v1.
