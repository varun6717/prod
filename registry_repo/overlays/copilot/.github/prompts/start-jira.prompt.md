---
description: Start the Jira-planning stage — point a fresh Copilot agent at the accepted v2 and act as jira_author.
---

You are starting the **Jira-planning stage** of this run.

Re-point yourself at this run's inputs: read `UI_INPUT.yaml`, the **accepted
`solution_intent/v2.md`**, and `solution_intent/enrichment.json`, then act as the
**`jira_author`** agent — load and execute `core/skills/jira_author.skill.md` (via the
`jira_author.agent.md` wrapper) against:

- `jira_template.<domain>.yaml`
- the **accepted `solution_intent/v2.md`** — §16 and §7 carry the plan's substance
- `solution_intent/enrichment.json` — for the finding each §16 entry traces back to

Produce the **4-level plan** in `jira_plan.json` — Initiative → Deliverable → Epic → Story, JPMC's
hierarchy, each level sourced from exactly one place in v2. Build the parent chain from **the SI's
own ids**; never invent one. Inventing an id is what would break idempotency on re-push, so the
ids are not yours to choose.

**Draft only — no write to Jira.** Then hand `jira_plan.json` to the **`jira_validator`** subagent,
which scores the trace and surfaces **G3**.

**G3 is the push authorization.** The operator accepts; that acceptance — and nothing else —
authorises the run's **only external mutation**. Never push on your own initiative, and never treat
a passing score as permission: the score informs, the operator decides (FR-XS-13).
