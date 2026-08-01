---
name: jira_author
description: Subagent that drafts jira_plan.json (epics/stories, no external write) from the accepted FRD.md + BRD.md. Deferred this slice (BRD→FRD only).
skill: core/skills/jira_author.skill.md
user_invocable: false
---

# jira_author — Claude overlay wrapper

Thin tool-specific wrapper (FR-XS-08, FR-XS-19, D9). **The logic is not here.** It lives in
the one shared skill; this file only points Claude at it and states how this overlay runs it.

**Load and execute `core/skills/jira_author.skill.md`** against this run's inputs
(`jira_template.<domain>.yaml` · the accepted `FRD.md` · `BRD.md`). Follow that skill verbatim —
do not restate, summarize, or fork its procedure here.

- **Executor:** **subagent** in its own context window (`user_invocable: false`). Run autonomously
  and return a concise summary — do not start a chat.
- **Produces:** `jira_plan.json` only — **no external write** (the Jira push is the single deferred
  external mutation, gated at G3).
- **Slice scope:** **deferred this slice** — present for overlay parity (D9), not invoked in the
  BRD→FRD run.
