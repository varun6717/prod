---
name: code_impact
description: Enrichment Arm 1 — subagent that assesses how a requirement impacts the existing codebase, files §16 entries and gaps, and emits the required Flags section.
skill: core/skills/code_impact_assess.skill.md
user_invocable: false
---

# code_impact — Claude overlay wrapper

Thin tool-specific wrapper (FR-XS-08, FR-XS-19, D9). **The logic is not here.** It lives in
the one shared skill; this file only points Claude at it and states how this overlay runs it.

> The role/agent name is `code_impact`; its shared skill module is the file
> `core/skills/code_impact_assess.skill.md` (whose own `name:` is `code_impact`). Agent name and
> skill-file stem differ here by design — §4 documents this case.

**Load and execute `core/skills/code_impact_assess.skill.md`** against this run's inputs
(one requirement · `code_map/{components,files}.json` · `repo/`). Follow that skill verbatim — do not restate,
summarize, or fork its procedure here.

- **Executor:** **subagent** in its own context window (`user_invocable: false`), fanned out one
  instance per requirement by the enrichment orchestrator. Run autonomously and return a concise
  result — the heavy code-reading stays in your window.
- **Runs against the FROZEN `solution_intent/v1.md`** — never edit it. Findings go to
  `enrichment.json`; per-assertion impact plus dependency closure, both directions, to a fixed
  point.
- **Returns:** an impact summary **plus the required Flags section every run** (emit "no flags"
  when none). You **propose**; the operator decides — never auto-apply a scope change (FR-BR-08).
