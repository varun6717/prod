# fixtures/si_validator — the G1 pass/fail pair

Proof inputs for `core/scripts/solution_intent_validator.py` (TASK-110).

## The pass case is `fixtures/si_author/v1.md`, not a copy here

The task list named a `si_pass.md` alongside `si_fail.md`. There already **is** a real, authored,
18-section v1 — the TASK-109 output — and the proof this task owes is "a G1 accept on the TASK-109
v1". Copying that 35KB document into this directory would create a second source of truth that
drifts the first time either is touched, and the copy would be the one nobody updates.

So the pass case is `../si_author/v1.md`, used directly. It is a genuinely *good* input rather
than a purpose-built one, which makes it the stronger test: it scores **92**, not 100, because it
honestly declares five gaps.

## `si_fail.md` — one defect per precondition

Not "a bad document". Each defect is aimed at exactly one hard precondition, so the failure report
can be checked violation by violation rather than merely asserting that it failed:

| Precondition | How the fixture breaks it |
|---|---|
| `sections_complete` | §11 present but empty; §9 missing entirely |
| `conditionals_dispositioned` | §3 says "Not applicable" with **no reason**; §9 absent |
| `gaps_declared` | two `open` coverage entries, §17 lists no question |
| `trace_15_to_4` | S2 traces to O9 (undeclared); O2 has no criterion |
| `trace_8_to_7` | R2 names D9 (undeclared); D2 has no requirement |
| `assertions_enumerated` | R2 carries no `R2.n` assertions |
| `flags_resolved` | not expressible in a document — passed in by the caller |

The bare-`Not applicable` case is the one that found a real bug while this was being built: the
first cut only recognised `Not applicable — <reason>`, so a conditional with **no** reason slipped
through as ordinary content. That is exactly the "omission with better manners" D-A10 forbids, and
the parser now matches the reasonless form specifically in order to reject it.

## What the proof demonstrates

`python3 core/scripts/solution_intent_validator.py`

- the authored v1 scores 92 and is eligible; every precondition ✓
- the broken v1 names **all six** document-expressible violations
- a **passing** score with one unresolved flag is still ineligible (D4's backstop)
- **declared gaps cost score, not eligibility** — v1 passes at 92 with five gaps declared, because
  a rule that blocked on honest gaps would reward fabricated citations instead
- `accept` on an ineligible v1 is **refused**; `reopen` increments and freezes nothing
- `accept` freezes v1: hashed to `v1.frozen.json`, set read-only, and a post-freeze edit is
  **detected by the digest** — which is what the hash buys over a file mode anyone can flip
