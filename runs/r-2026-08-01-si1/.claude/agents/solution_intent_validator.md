---
name: solution_intent_validator
description: Subagent that scores solution_intent/v1.md for section coverage and source traceability (and, at G2, the enrichment record); returns a score + hard-precondition verdicts + gap list.
skill: core/skills/solution_intent_validator.skill.md
user_invocable: false
---

# solution_intent_validator — Claude overlay wrapper

Thin tool-specific wrapper (FR-XS-08, FR-XS-19, D9). **The logic is not here.** It lives in
the one shared skill; this file only points Claude at it and states how this overlay runs it.

**Load and execute `core/skills/solution_intent_validator.skill.md`** against this run's inputs
(`solution_intent/v1.md` · `si_profile.<domain>.yaml` · `context_set/` · `decisions.jsonl`). Follow that skill
verbatim — do not restate, summarize, or fork its procedure here.

- **Executor:** **subagent** in its own context window (`user_invocable: false`), spawned by the
  orchestrator or `solution_intent_author`. Run autonomously and return a concise summary — do not start a chat.
- **Returns:** a score + hard-precondition verdicts + a gap list, feeding the operator gate **G1**
  (you do not decide it). Acceptance at G1 **freezes** v1.
- **Also serves G2:** the same skill scores `enrichment.json` for the v1 → v2 gate. Both gates are
  **soft score + hard preconditions** — the score informs, the preconditions are absolute, and
  neither advances the run on its own (FR-XS-13).
