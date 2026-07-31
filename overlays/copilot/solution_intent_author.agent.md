---
name: solution_intent_author
description: Interactive BRD authoring agent — drives a chat with the operator to produce a source-grounded BRD.md for one project; delegates code_impact; gate G1.
skill: core/skills/solution_intent_author.skill.md
user_invocable: true
---

# solution_intent_author — Copilot overlay wrapper (`*.agent.md`)

Thin tool-specific wrapper (FR-XS-08, FR-XS-19, D9), native to Copilot agent mode. **The logic is
not here** — it lives in the one shared skill. Parity twin of the Claude
`.claude/agents/solution_intent_author.md` wrapper: same shared skill, native frontmatter + location.

**Load and execute `core/skills/solution_intent_author.skill.md`** against this run's inputs
(`UI_INPUT.yaml` · `brd_profile.<domain>.yaml` · `context_set/index.json` · `code_map.json`).
Follow that skill verbatim — do not restate, summarize, or fork its procedure here.

- **Executor:** an **interactive Copilot agent-mode session** the operator talks to directly
  (`user_invocable: true`), started via the `start-si` prompt file.
- **Delegates:** the `code_impact` subagent for requirement-level code impact + scope Flags.
- **Gate:** produces `BRD.md`; `solution_intent_validator` scores it → operator gate **G1**.
