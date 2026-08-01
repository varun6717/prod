---
name: solution_intent_author
description: Interactive BRD authoring session — drives a chat with the operator to produce a source-grounded BRD.md for one project; delegates code_impact; gate G1.
skill: core/skills/solution_intent_author.skill.md
user_invocable: true
---

# solution_intent_author — Claude overlay wrapper

Thin tool-specific wrapper (FR-XS-08, FR-XS-19, D9). **The logic is not here.** It lives in
the one shared skill; this file only points Claude at it and states how this overlay runs it.

**Load and execute `core/skills/solution_intent_author.skill.md`** against this run's inputs
(`UI_INPUT.yaml` · `si_profile.<domain>.yaml` · `context_set/index.json` · `code_map.json`).
Follow that skill verbatim — do not restate, summarize, or fork its procedure here.

- **Executor:** your own **interactive session**, started by the operator via the `/start-si`
  prompt file (`user_invocable: true`). You drive a chat with the operator.
- **Delegates:** the `code_impact` subagent for requirement-level code impact + scope Flags.
- **Gate:** produces `BRD.md`; `solution_intent_validator` scores it → operator gate **G1**.
