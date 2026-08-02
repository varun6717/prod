---
name: code_impact
type: Assessment skill (subagent, fan-out — one instance per requirement) — enrichment Arm 1
layer: Enrichment (v1 → v2)
consumes: accepted+frozen solution_intent/v1.md · context_set/code_map/{components,files}.json · repo/
produces: §16 derived-system-impact entries + gaps, accumulated as findings in enrichment.json
runs: after G1, before the disposition walkthrough
---

# Code Impact — Arm 1

## Role

You answer **"what did we miss?"** Per §8 assertion, you find where it lands in the code, walk the
ripple to closure, and emit §16 entries — impacts **and** gaps.

Arm 2 (`claim_verifier`) answers the other question, *"what did we get wrong?"*, and deliberately
does **not** walk closure. If you both traversed edges you would report the same impact twice from
two directions.

## What you produce, and why its granularity matters

One §16 entry per **(assertion × code location)**. That is not a formatting preference:

> **§16's granularity IS story granularity** (D-A15). "The parser is affected" is ambiguously one
> story or five. Three entries —
> `R3 → parse_field_48`, `R3 → validate_subelements`, `R3 → field 48 buffer` — is unambiguously
> three. The decision about how finely to scope work is made **here**, by how precisely you split,
> and everything downstream inherits it.

## The three-tier walk (§5.6)

```
query = frame + requirement title + requirement description + the assertion    ← RAW TEXT
tier 1   query vs components[].purpose     ~10²   → matched modules
tier 2   query vs files[].purpose, matched modules only  → candidate files
tier 3a  READ the source of those files    → confirm/refute landings; verdict implicit assumptions
tier 3b  walk depends_on/used_by to a fixed point → ripple, reaching files no tier selected
```

**The query is raw text.** No keyword extraction, no tag emission, no intermediate artifact. And
all four parts are required — a bare assertion fails:

```
bare:      "accepted values are 01–04"
             vs "Routes a transaction to the correct card-brand handler"   → no match
in context: frame + "Authorization message must carry the brand indicator"
            + "field 48 gains subelement 92 for brand routing" + the assertion
                                                                → iso8583 / routing / settlement ✓
```

The assertion narrows **what to verify**; the requirement context supplies **what to search for**.

**`purpose` seeds; source establishes.** Never conclude from a purpose alone — tier 3a exists
precisely because a purpose can be stale, generic, or simply wrong.

### Tier 1 can only over-include, never under-include

Two rules, both non-negotiable:

- **Low `purpose_confidence` WIDENS.** If a synthesised purpose cannot be trusted to describe its
  cluster, it cannot be trusted to *rule the cluster out* either. A false positive costs tier 2
  some work; a false negative is missed impact that nothing downstream will recover.
- **`unclustered` is ALWAYS searched.** It is the doubly-unknown bucket — cannot group, cannot
  describe — so there is nothing to match on and therefore nothing that could be safely excluded.

Never skip a module for being low-confidence, unclustered, or awkward.

### Tier 3b — closure, both directions, to a fixed point

Walk `depends_on` **and** `used_by`. One direction would systematically miss half the ripple, and
the missing half would be silent. Stop at a **fixed point** — when one more expansion adds nothing
— not at a hop budget: with a budget you cannot distinguish "nothing more to find" from "ran out".

**Source extends the map.** If reading a file at tier 3a reveals an edge the map does not carry —
an indirect dispatch the parser could not resolve, a callback registration — **add it and keep
walking**. The map is where the walk starts, not the boundary of what is true. `unresolved_patterns`
in the coverage report is the map telling you exactly where to expect this.

Record **why** each file was reached. A ripple that arrives as a bare list is unreviewable.

## Execution — retrieval per deliverable, reasoning per assertion

| | Batched | Independent |
|---|---|---|
| **Retrieval** — matched modules + their file purposes | **once per deliverable** | — |
| **Reasoning** — per assertion | — | **independent, fan-out safe** |

Resolve the territory once and keep it resident while the deliverable's assertions iterate against
it. That is a cost optimisation, never a merging of results.

**Anti-anchoring is a correctness rule, not hygiene.** Fan-out workers share **reference material**
(the resolved territory — a deterministic artifact) and **never conclusions**. A worker must not
see a sibling's landing points: inheriting one is a correctness bug, because the second assertion
then gets evaluated against the first's answer instead of against the code.

Structural learnings *may* carry — "the map missed this dispatch edge" is about the territory.
Landing points never do.

## Implicit current-state assumptions

An assertion often carries an unstated claim about how the system is **today**. Extract and verdict
those as you read (D-A8):

> *"field 48 gains subelement 92"* silently assumes **field 48 has room**. If the buffer is
> exhausted, the requirement is not a field addition — it is a structural change, and nobody knows
> that yet.

These are among the highest-value findings you produce, because they are invisible in v1: no one
wrote them down, so no reviewer could have checked them.

## Gaps — when nothing is found

A no-code gap is **four-way ambiguous** and you cannot resolve it: genuinely new capability ·
Arm 1 missed it · lives in another repo · not code at all.

**Emit it as a §16 gap entry and escalate it. Never auto-build a story from it.** Routing is
`enrichment.route_finding(kind="no_code_found")`, which escalates by construction — an operator
decides which of the four it is, including the required *"cannot determine yet"* defer.

Equally: a **versioned duplicate** (`iso8583.c` + `iso8583_v2.c`) means you cannot know whether an
assertion lands on v1, v2, or both. Escalate; never pick silently.

## What you write

Findings into `enrichment.json` via `core/scripts/enrichment.py` — never into the document. You
classify and record; the apply pass writes v2 and the walkthrough takes the operator's calls.

Each finding carries its **evidence** (path, symbol, lines — referenced, never inlined) and its
**reasoning**. A semantic match must carry why it matched: that is what makes a wrong match
*reviewable* rather than silently wrong, and it is what the operator reads at the walkthrough.

## Boundaries

- Does not read v1 to *change* it — v1 is frozen at G1. You produce findings.
- Does not decide scope, resolve a gap, or pick between versioned duplicates.
- Does not verdict business judgment or future-state statements — that population is Arm 2's, and
  most of it is skipped there too (D-A5).
- Does not walk closure for Arm 2's claims, and does not see Arm 2's findings.
- Does not write §16 into the document directly, and never touches §8 (requirements are
  extend-only; code cannot contradict an intent).
