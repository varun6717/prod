---
name: disposition_walkthrough
description: Interactive dispositioning of escalated enrichment findings — presents each finding + evidence, recommends, records the operator's call + rationale; triaged, dependency-ordered, resumable.
skill: core/skills/disposition_walkthrough.skill.md
user_invocable: true
---

# disposition_walkthrough — Copilot overlay wrapper (`*.agent.md`)

Thin tool-specific wrapper (FR-XS-08, FR-XS-19, D9/D11.7), native to Copilot agent mode. **The
logic is not here** — it lives in the one shared skill. Parity twin of the Claude
`.claude/agents/disposition_walkthrough.md` wrapper: same shared skill, native frontmatter +
location.

**Load and execute `core/skills/disposition_walkthrough.skill.md`** against this run's inputs
(`enrichment.json` — the escalated findings · `solution_intent/v1.md` · the code evidence each
finding cites). Follow that skill verbatim — do not restate, summarize, or fork its procedure
here.

- **Executor:** an **interactive Copilot agent-mode session** the operator talks to directly
  (`user_invocable: true`) — the one human checkpoint of the enrichment stage, reached from
  `start-enrich` after both arms complete.
- **Records:** every disposition + rationale to `decisions.jsonl`; per-finding status in
  `enrichment.json` (stop/resume safe).
- **Gate:** unresolved escalations block **G2** (hard precondition).
