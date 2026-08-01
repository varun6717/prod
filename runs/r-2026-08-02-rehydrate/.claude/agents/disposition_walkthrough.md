---
name: disposition_walkthrough
description: Interactive dispositioning of escalated enrichment findings — presents each finding + evidence, recommends, records the operator's call + rationale; triaged, dependency-ordered, resumable.
skill: core/skills/disposition_walkthrough.skill.md
user_invocable: true
---

# disposition_walkthrough — Claude overlay wrapper

Thin tool-specific wrapper (FR-XS-08, FR-XS-19, D9/D11.7). **The logic is not here.** It lives
in the one shared skill; this file only points Claude at it and states how this overlay runs it.

**Load and execute `core/skills/disposition_walkthrough.skill.md`** against this run's inputs
(`enrichment.json` — the escalated findings · `solution_intent/v1.md` · the code evidence each
finding cites). Follow that skill verbatim — do not restate, summarize, or fork its procedure
here.

- **Executor:** your own **interactive session** (`user_invocable: true`) — the one human
  checkpoint of the enrichment stage, reached from `start-enrich` after both arms complete.
- **Records:** every disposition + rationale to `decisions.jsonl`; per-finding status in
  `enrichment.json` (stop/resume safe).
- **Gate:** unresolved escalations block **G2** (hard precondition).
