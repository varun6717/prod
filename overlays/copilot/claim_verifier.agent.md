---
name: claim_verifier
description: Enrichment Arm 2 — extracts current-state claims from the accepted SI v1, clusters them by code region, verdicts them against the code map/source; stages corrections + escalations into enrichment.json.
skill: core/skills/claim_verifier.skill.md
user_invocable: false
---

# claim_verifier — Copilot overlay wrapper (`*.agent.md`)

Thin tool-specific wrapper (FR-XS-08, FR-XS-19, D9/D11.7), native to Copilot agent mode. **The
logic is not here** — it lives in the one shared skill. Parity twin of the Claude
`.claude/agents/claim_verifier.md` wrapper: same shared skill, native frontmatter + location.

**Load and execute `core/skills/claim_verifier.skill.md`** against this run's inputs
(`solution_intent/v1.md` · `context_set/index.json` + the per-artifact indexes ·
`context_set/code_map/`). Follow that skill verbatim — do not restate, summarize, or fork its
procedure here.

- **Executor:** an **analytical Copilot agent** (`user_invocable: false`) — dispatched during
  the enrichment stage (`start-enrich`), never by an operator gesture.
- **Produces:** verdicts + staged corrections + escalations in `enrichment.json`; §18 counts.
- **Gate:** feeds **G2** via `solution_intent_validator` after the disposition walkthrough.
