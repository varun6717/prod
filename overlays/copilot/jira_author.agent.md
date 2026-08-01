---
name: jira_author
description: Subagent that drafts the 4-level jira_plan.json (Initiative -> Deliverable -> Epic -> Story, no external write) from the accepted solution_intent/v2.md.
skill: core/skills/jira_author.skill.md
user_invocable: false
---

# jira_author — Copilot overlay wrapper (`*.agent.md`)

Thin tool-specific wrapper (FR-XS-08, FR-XS-19, D9), native to Copilot agent mode. **The logic is
not here** — it lives in the one shared skill. Parity twin of the Claude
`.claude/agents/jira_author.md` wrapper: same shared skill, native frontmatter + location.

**Load and execute `core/skills/jira_author.skill.md`** against this run's inputs
(`jira_template.<domain>.yaml` · the accepted `solution_intent/v2.md` · `enrichment.json`). Follow that skill verbatim —
do not restate, summarize, or fork its procedure here.

- **Executor:** a **subagent** in its own context (`user_invocable: false`). Run autonomously and
  return a concise summary — do not start a chat.
- **Produces:** `jira_plan.json` only — **no external write**. The push is the run's single
  external mutation, gated at **G3**.
- **Ids are not yours to choose:** build the parent chain from the SI's own ids, never invented
  ones — inventing an id is precisely what would break idempotency on a re-push.
