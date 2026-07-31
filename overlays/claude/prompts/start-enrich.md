---
description: Start the FRD stage — point a fresh agent at the accepted BRD and act as frd_author.
---

You are starting the **FRD stage** of this run.

Re-point yourself at this run's inputs: read `UI_INPUT.yaml` and the **accepted `BRD.md`** (the
prior artifact), then act as the **`frd_author`** agent — load and execute
`core/skills/frd_author.skill.md` (via the `.claude/agents/frd_author` wrapper) against:

- the **accepted `BRD.md`** — the spine; the FRD locks to its version (BRD-as-spine, FR-XS-14)
- `frd_profile.<domain>.yaml`
- `context_set/`

Drive the chat with the operator to produce `FRD.md`, carrying the detailed code impact forward.

When the FRD is accepted at gate **G2**, close by **surfacing** the next-stage transition — do
**not** perform it (FR-XS-11): tell the operator to `/clear` or start a new session, then run
`/start-jira`. Never self-issue the transition. *(Jira is deferred this slice — see `start-jira`.)*
