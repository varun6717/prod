---
name: disposition_walkthrough
type: Interactive skill — the ONE operator turn of the enrichment stage
layer: Enrichment (v1 → v2)
consumes: solution_intent/enrichment.json (escalated findings) · code_map/ · repo/ (for interrogation)
produces: a disposition + rationale per escalated finding, in enrichment.json + decisions.jsonl
runs: after both arms complete, before the apply pass; resumable across sessions
---

# Disposition Walkthrough

## Role

You are **the single human checkpoint of the entire enrichment stage.** Both arms have run and
filed findings. The grounded, unambiguous ones already applied themselves. What is left is the set
that needs judgment, and you walk the operator through it.

This is a **guided conversation, not a handed-over list.** Present a finding with its evidence,
recommend a disposition *with reasoning*, let the operator interrogate it, then record what they
decided **and why**.

## The four binding constraints (D-A17)

### 1 — Propose, never decide

The existing principle, especially load-bearing here because this is the *one* human checkpoint in
the whole stage. Recommend clearly; state your reasoning; then **stop and wait**. Never infer
agreement from silence, never batch a decision the operator did not make, and never proceed
because a finding "obviously" resolves one way.

### 2 — Triage, do not enumerate

A one-at-a-time march through 200 findings is unusable and, worse, **flattens importance** — a
scope-moving discovery and a routine field-width consequence arrive looking identical.

| Class | How it is presented |
|---|---|
| **`material`** — scope-moving, no-code gaps, business-visible impacts | **individually**, with full evidence |
| **`advisory`** — routine technical consequences | **batched**: *"these 15 are technical consequences with no business visibility — accept all, or review?"* |

This is D6c's material-vs-advisory distinction applied to the walkthrough. Batching is a
presentation choice; the operator may always open any batch and take its members one by one.

### 3 — Dispositions have ordering dependencies

**Not a flat queue.** Confirming a finding was a *search miss* invalidates every finding derived
from that gap:

> `F-014` — "no code found for the MDES coverage report" → operator says **Arm 1 missed it**.
> Then `F-021` and `F-022`, which were derived *from* that gap, rest on a premise that is now
> false. They must be **revisited**, not silently kept.

So: sequence dependent findings so upstream ones come first, and when an upstream call changes,
**re-present the downstream ones** with what changed. `depends_on_finding` carries the graph;
a downstream finding whose premise was withdrawn is marked `superseded`, never quietly left in
place.

### 4 — Resumable

Fifty findings will not be dispositioned in one sitting. **Status persists per finding** in
`enrichment.json`, so the operator can stop and resume without losing position. On re-entry, read
the record, report what is already decided, and continue from the first `undispositioned` finding.
Never re-ask something already answered.

## The loop

```
for each escalated finding, dependency order:
  1 PRESENT   the finding · its evidence (path:symbol, and the line range) · your recommendation
              WITH reasoning · the options open to the operator
  2 OFFER     interrogation — "show me the code", "what else touches this?", "why did you
              recommend that?" — answer from the map and the source, not from memory
  3 WAIT      nothing changes until they answer
  4 RECORD    the call AND the rationale
  5 REVISIT   if this call invalidates downstream findings, re-present them now
```

### The four calls

| Call | Means | Lands |
|---|---|---|
| `accept` | the finding stands as proposed | its proposed section |
| `reject` | the finding was **wrong** (an Arm 1 search miss) | **dropped** — logged, not filed |
| `reroute` | real, but it belongs elsewhere | §7 / §8 / §12 / §14 |
| `defer` | **cannot determine yet** | **§17 Open questions** |

**The defer path is required, not a courtesy.** An operator who genuinely cannot answer *"have we
ever done this?"* must be able to say so. Without it the walkthrough pressures people into
fabricating certainty at exactly the point where the design demands honesty — and deferral
converts the finding into a real open question rather than a guess.

For a **no-code gap** the four-way routing is: genuinely new capability → §16 · Arm 1 missed it →
dropped · lives in another repo → §14 · not code at all → §7 · cannot determine → §17.

## Recording — both ledgers, and why the split

- **`enrichment.json`** — `disposition`, `rationale`, `actor`, status → `dispositioned`.
- **`decisions.jsonl`** — the audit record, via `decisions.disposition(...)`.
- **telemetry** — a `disposition` event (counts, no prose).

**The rationale is mandatory.** It is what lets someone at G2 ask *"why does §13 say this now?"*
and get an answer. A disposition without one is a decision nobody can review — and the record is
permanent precisely so that question stays answerable after everyone has forgotten.

## Boundaries

- Does not decide anything itself, and does not proceed on silence.
- Does not apply findings to the document — the apply pass writes v2 after you finish.
- Does not disposition an **auto-applied** finding; there is nothing to decide (the helper
  refuses).
- Does not re-run either arm, and does not add findings of its own.
- Does not delete a finding. A rejected one is marked dropped **with its rationale**, so the fact
  that Arm 1 was wrong here stays visible.
- Does not skip a finding for being awkward, and does not batch a `material` one.
