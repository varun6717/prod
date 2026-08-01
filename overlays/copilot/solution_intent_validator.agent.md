---
name: solution_intent_validator
description: Subagent that scores BRD.md for section coverage and source traceability and returns a score + gap list; feeds gate G1.
skill: core/skills/solution_intent_validator.skill.md
user_invocable: false
---

# solution_intent_validator — Copilot overlay wrapper (`*.agent.md`)

Thin tool-specific wrapper (FR-XS-08, FR-XS-19, D9), native to Copilot agent mode. **The logic is
not here** — it lives in the one shared skill. Parity twin of the Claude
`.claude/agents/solution_intent_validator.md` wrapper: same shared skill, native frontmatter + location.

**Load and execute `core/skills/solution_intent_validator.skill.md`** against this run's inputs
(`BRD.md` · `si_profile.<domain>.yaml` · the sources · the code surface). Follow that skill
verbatim — do not restate, summarize, or fork its procedure here.

- **Executor:** a **subagent** in its own context (`user_invocable: false`), invoked by the
  orchestrator or `solution_intent_author`. Run autonomously and return a concise summary — do not start a chat.
- **Returns:** a score + section gap list that feeds the operator gate **G1** (you do not decide it).
