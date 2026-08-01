---
description: Start the Solution Intent stage — point a fresh agent at this run's UI_INPUT and act as solution_intent_author.
---

You are starting the **Solution Intent v1** stage of this run.

Read `UI_INPUT.yaml` (run config + the requirement frame; `domain` selects the profile), then
act as the **`solution_intent_author`** agent — load and execute `core/skills/solution_intent_author.skill.md` (via the
`.claude/agents/solution_intent_author` wrapper) against this run's inputs:

- `UI_INPUT.yaml` — including `frame.overview`, the Initiative Overview
- `si_profile.<domain>.yaml` — the 18 sections and their `must_capture` items
- `context_set/index.json` — plus the per-artifact `<doc>.index.json` indexes and the `<doc>.md` extracts

This is the **first** interactive stage — there is no prior artifact. Drive the chat with the
operator to produce a source-grounded `solution_intent/v1.md`.

**Author v1 code-blind.** Do **not** read `repo/` or the code map in this stage. v1 states what the
sources, the frame and the operator say we intend; checking that against the code is enrichment's
job, and a v1 that already knew the code would leave enrichment nothing to find — and no way to
tell a source's claim from a tool's inference.

Run the **human-mediated flag loop** on any scope flag you surface — you **surface**, the operator
**decides** (FR-BR-08). Never apply a scope change yourself.

When v1 is accepted at gate **G1** — which **freezes** it — close by **surfacing** the next-stage
transition; do **not** perform it (FR-XS-11): tell the operator to `/clear` or start a new session,
then run `/start-enrich`. Never self-issue the transition.
