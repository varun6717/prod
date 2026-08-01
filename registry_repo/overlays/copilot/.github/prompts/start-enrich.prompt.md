---
description: Start the enrichment stage — point a fresh Copilot agent at the frozen v1 and run both arms, the walkthrough, then the apply pass.
---

You are starting the **enrichment (v1 → v2)** stage of this run.

Re-point yourself at this run's inputs: read `UI_INPUT.yaml` and the **accepted, frozen
`solution_intent/v1.md`**. Stay the **orchestrator** for the two assessment arms; you become
interactive only for the walkthrough.

**v1 is frozen. Never edit it.** Every finding goes into `solution_intent/enrichment.json`, and the
apply pass writes v2 from the two together — which is exactly what makes each change in v2
traceable back to a finding (D-A16).

Run the stage in this order:

1. **Arm 1 — `code_impact`** (fan out one subagent per requirement): frozen `v1.md` ·
   `context_set/code_map/{components,files}.json` · `repo/`. Per-assertion impact plus dependency
   closure, both directions, to a fixed point. Files §16 entries and gaps.
2. **Arm 2 — `claim_verifier`**: the same inputs, checking v1's claims against the code. Point
   lookup, then stop. Runs **after** Arm 1, which has usually already pulled the slices its claims
   need. An honest `unverifiable` is a valid verdict.
3. **The disposition walkthrough** — the **one** operator turn of this stage. Only *escalated*
   findings reach it. Provenance decides authority: a source-derived error **auto-corrects**, an
   operator- or frame-derived claim **escalates** (a tool does not overrule a person), an unsourced
   `[TBD]` **auto-fills**. Triage, don't enumerate; call a finding that supersedes others first;
   the walkthrough is **resumable**. You **propose**, the operator **decides**. Rationale goes to
   `decisions.jsonl`.
4. **The apply pass** — `core/scripts/apply_enrichment.py` writes `solution_intent/v2.md`.
   Corrections revise in place with provenance, discoveries append, **nothing is deleted**, §1 is
   regenerated last.

When v2 is accepted at gate **G2**, close by **surfacing** the next-stage transition — do **not**
perform it (FR-XS-11): tell the operator to open a new thread (`Ctrl+N`), then run
`/start-jira`. Never self-issue the transition.
