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
3. **Domain enrichment passes**, if the domain pack ships any — for `payment_brand`, run
   `core/profiles/payment_brand/fpi_mnemonic_enrich.skill.md` when the corpus carries an
   interchange-level reference table. It resolves the network's **FPIs** to our **interchange
   level / mnemonic** codes and stages `gap_fill` findings. It runs **here, before the
   walkthrough**, for two reasons: any escalation it raises must join the single operator turn
   rather than needing a second one, and its findings must reach §16 **before G2** — a mnemonic
   that arrives after v2 is accepted never becomes a Jira story, so the boarding-system work
   would be identified and then silently dropped. **This is the only pass that can surface
   PeopleSoft/boarding work**; both code arms are blind to it, since none of it lives in `repo/`.
4. **The disposition walkthrough** — the **one** operator turn of this stage. Only *escalated*
   findings reach it. Provenance decides authority: a source-derived error **auto-corrects**, an
   operator- or frame-derived claim **escalates** (a tool does not overrule a person), an unsourced
   `[TBD]` **auto-fills**. Triage, don't enumerate; call a finding that supersedes others first;
   the walkthrough is **resumable**. You **propose**, the operator **decides**. Rationale goes to
   `decisions.jsonl`.
5. **The apply pass** — `core/scripts/apply_enrichment.py` writes `solution_intent/v2.md`.
   Corrections revise in place with provenance, discoveries append, **nothing is deleted**, §1 is
   regenerated last.

When v2 is accepted at gate **G2**, close by **surfacing** the next-stage transition — do **not**
perform it (FR-XS-11): tell the operator to open a new thread (`Ctrl+N`), then run
`/start-jira`. Never self-issue the transition.
