---
description: Start the Jira-planning stage — point a fresh agent at the accepted FRD and act as jira_author. Deferred this slice.
---

> **Deferred this slice (BRD→FRD only).** This prompt ships for overlay parity (D9) and the
> future Jira layer; it is **not invoked** in the current slice and performs **no external write**.

You are starting the **Jira-planning stage** of this run.

Re-point yourself at this run's inputs: read `UI_INPUT.yaml`, the **accepted `FRD.md`**, and
`BRD.md`, then act as the **`jira_author`** agent — load and execute
`core/skills/jira_author.skill.md` (via the `.claude/agents/jira_author` wrapper) against:

- `jira_template.<domain>.yaml`
- the **accepted `FRD.md`** + `BRD.md`

Produce `jira_plan.json` only — **no push**. The single external mutation (the Jira push) is the
operator-gated step **G3** and is out of scope this slice.
