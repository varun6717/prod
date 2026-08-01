---
description: Start the BRD stage — point a fresh agent at this run's UI_INPUT and act as solution_intent_author.
---

You are starting the **BRD stage** of this run.

Read `UI_INPUT.yaml` (run config + the requirement frame; `domain` selects the profile), then
act as the **`solution_intent_author`** agent — load and execute `core/skills/solution_intent_author.skill.md` (via the
`.claude/agents/solution_intent_author` wrapper) against this run's inputs:

- `UI_INPUT.yaml`
- `si_profile.<domain>.yaml`
- `context_set/index.json`
- `code_map.json`

This is the **first** interactive stage — there is no prior artifact. Drive the chat with the
operator to produce a source-grounded `BRD.md`. Delegate the `code_impact` subagent for
requirement-level code impact + scope **Flags**, and run the human-mediated flag loop — you
**surface**, the operator **decides** (FR-BR-08).

When the BRD is accepted at gate **G1**, close by **surfacing** the next-stage transition — do
**not** perform it (FR-XS-11): tell the operator to `/clear` or start a new session, then run
`/start-enrich`. Never self-issue the transition.
