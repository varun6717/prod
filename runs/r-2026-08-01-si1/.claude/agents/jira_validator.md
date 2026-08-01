---
name: jira_validator
description: Subagent that checks jira_plan.json for bidirectional FRD↔Jira traceability, field completeness, and coverage; feeds gate G3. Deferred this slice.
skill: core/skills/jira_validator.skill.md
user_invocable: false
---

# jira_validator — Claude overlay wrapper

Thin tool-specific wrapper (FR-XS-08, FR-XS-19, D9). **The logic is not here.** It lives in
the one shared skill; this file only points Claude at it and states how this overlay runs it.

**Load and execute `core/skills/jira_validator.skill.md`** against this run's inputs
(`jira_plan.json` · `FRD.md`). Follow that skill verbatim — do not restate, summarize, or fork
its procedure here.

- **Executor:** **subagent** in its own context window (`user_invocable: false`). Run autonomously
  and return a concise summary — do not start a chat.
- **Returns:** bidirectional traceability + field completeness + coverage that feed the single Jira
  push gate **G3** (you do not decide it).
- **Slice scope:** **deferred this slice** — present for overlay parity (D9), not invoked in the
  BRD→FRD run.
