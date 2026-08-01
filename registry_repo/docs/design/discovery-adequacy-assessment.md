# Discovery-question adequacy — coverage assessment (TASK-111)

**Domain:** `payment_brand` · **Assessed against:** `core/profiles/payment_brand/si_profile.payment_brand.yaml`
(TASK-108) and `core/skills/solution_intent_author.skill.md` (TASK-109) · **Date:** 2026-08-01

## Why this assessment exists

D-A13's routing matrix is easy to read as a retrieval design. Its most consequential finding is a
side effect of drawing the table:

> **Discovery is primary for exactly three sections — §9, §12, §13.** No document in the corpus
> answers them, so disposition and retrieval work buys those sections **nothing**; their quality
> rests entirely on discovery-question quality.

That sentence promotes TASK-079 from a deferred nice-to-have into core work. It also inverts the
usual worry: for §9/§12/§13 the risk is not that the agent reads the wrong passage, it is that
**nobody ever asks**, and the section quietly fills with plausible filler or nothing at all.

## 1 · Where questions originate — the inventory

Two places, and only two:

| Origin | Where it lives | Scope |
|---|---|---|
| **Up-front framing exchange** | `solution_intent_author.skill.md` § "Discovery — before any section is drafted" — 2–3 questions, one at a time | Orientation only. Explicitly *not* section pre-fill: "do not try to pre-fill sections; the per-section probes do that later, with the sources already read." |
| **Per-section probes** | `si_profile.<domain>.yaml` → `sections[].probe_if_missing` | The real elicitation surface. Fired in the loop's step (e) for anything the routed sources and the frame did not satisfy. |

A third, non-question input is the **frame** (`UI_INPUT.frame`), which is operator-authored but
available up front and global — D-A13 keeps it in its own column for exactly that reason.

**So per-section `probe_if_missing` carries essentially all of the adequacy burden.** The framing
exchange is deliberately shallow, and the frame supplies only what the operator thought to write
before seeing any source. If a `must_capture` has no probe, nothing in the design will ask for it.

## 2 · The gap analysis

Method: for every section fed by `discovery` or `frame`, map each `must_capture` item to a
`probe_if_missing` entry that would elicit it. Anything unmapped is a gap.

### Findings — discovery-primary first (the unrecoverable tier)

| § | `must_capture` | Before | Finding |
|---|---|---|---|
| **9** | 1 named program/strategy | Q1 | ✅ |
| **9** | 2 how it advances that specifically | — | ❌ **gap.** Q2 asked "what would the portfolio lose", which elicits *stakes*, not *mechanism*. A section can answer it fully and still not say how the work advances the program. |
| **9** | 3 prior decision/artifact that put it on the roadmap | — | ❌ **gap.** `prior_artifact` is `S` here, so a source *may* supply it — but when the corpus has no prior artifact, nothing asks. |
| **12** | 1 what is NOT being done, **and why** | partial | ❌ **gap.** Q1 asked what a reader might wrongly assume is included (that is item 2). The primary "what are we excluding, and why" was never asked directly. |
| **12** | 2 adjacent capabilities assumed included | Q1 | ✅ |
| **12** | 3 deferred + follow-on named | Q2 | ✅ |
| **12** | 4 choice vs dependency on someone else | — | ❌ **gap.** |
| **13** | 1 assumptions in **checkable** form | Q1 (weak) | ⚠️ **weak.** "What are we assuming that we haven't verified?" reliably elicits *general beliefs* — the exact shape D-A4 says is worthless to enrichment ("we assume the architecture is suitable"). The question did not push for the component/system naming that makes an assumption verdictable. |
| **13** | 2 what it does NOT touch | Q2 | ✅ — the strongest probe in the set, and the highest-value one (D-A4). |
| **13** | 3 risks with impact | Q3 (partial) | ⚠️ "What would have to go wrong" elicits the risk; not its impact. |
| **13** | 4 what each risk depends on | — | ❌ **gap.** Without it a mitigation has nothing to attach to. |

### Findings — operator-fed supporting sections

| § | Item | Finding |
|---|---|---|
| **7** | 3 what "delivered" means · 4 ordering | ❌ two gaps |
| **8** | 4 the mandate/rule reference | ❌ gap |
| **11** | 2 accountable per deliverable | ❌ gap — **and it fired in the real run**: the TASK-109 v1 recorded exactly this as open question Q2 ("Who owns D1–D4?"). The assessment predicted a gap the authored fixture had already hit. |
| **15** | 3 hard dates · 4 done-ness for non-code deliverables | ❌ two gaps |
| **5** | 3 persona→use-case matrix | ❌ gap |
| **6** | 3 alternate/failure paths | ❌ gap |
| **10** | 3 design principles · 4 dates constraining *how* | ❌ two gaps |
| **3** | 3 competitive vs novel | ❌ gap |
| **14** | 3 external dependencies with dates · 4 other repo/track | ❌ two gaps |

**Total before: 19 unelicited `must_capture` items, 7 of them in the discovery-primary three.**

## 3 · The closing diff (proposed, then frozen)

Two changes to `si_profile.payment_brand.yaml`:

**(a) `probe_if_missing` entries become `{ ask, elicits }`.** Each question declares which
`must_capture` indices it elicits:

```yaml
probe_if_missing:
  - { ask: "What are we assuming this does NOT affect? Name the systems.", elicits: [2] }
```

This is the load-bearing half of the change. It turns the mapping from prose someone reads once
into **data a check can verify** — and the gap table above is precisely what an unverified mapping
accumulates. `core/scripts/checks/check_discovery_adequacy.py` now enforces it.

**(b) The 19 missing questions were added, and 2 weak ones rewritten.** Notably §13's first probe
now says *"Name the component, system or behaviour each assumption is about, so it can be checked
against the code later"* — pushing for the checkable form D-A4 requires, rather than hoping for it.

**Result: 50/50 `must_capture` items elicited**, with zero gaps in §9/§12/§13.

## 4 · The check, and its tiers

Not every section is elicited the same way, so a single rule would be wrong in both directions:

| Tier | Sections | Rule | Why |
|---|---|---|---|
| **discovery-primary** | §9, §12, §13 | every item MUST be elicited — **error** | No source can cover a gap. It is unrecoverable. |
| **operator-fed** | §4, §7, §11, §15 (+ any `frame`) | SHOULD be elicited — **warning** | A routed document may legitimately supply it. |
| **derived** | §1, §16, §17, §18 | no probes; a probe here is a **warning** | §1 summarises the body, §16/§18 are enrichment's output, §17 accumulates. Asking is a category error. |

## 5 · Sparse-corpus proof

The check proves the mapping is total. This proves it *matters*: route a deliberately thin corpus —
only `product_domain_knowledge` (the two KB pages), no mandate — and count what each section can
still see.

**Nine sections route zero artifacts**, including two of the three discovery-primary ones (§9,
§12). For those, the probes are not a fallback — they are the *only* path to content, and anything
they miss is content that can never be authored at all. All nine are fully elicitable
(3/3, 4/4, 4/4 …), so authoring can still proceed honestly rather than silently producing empty
sections.

This is the concrete version of D-A13's claim. Under a thin corpus the entire retrieval
apparatus — disposition routing, the per-artifact index, the whole-read budget — contributes
**nothing** to those nine sections. Question quality is the only thing standing between the
operator and a document full of blanks.

## 6 · Standing rule for a new domain

`must_capture` and `probe_if_missing` are the two things a new domain rewrites. The adequacy check
runs against whatever it writes, so the guarantee travels: **a new domain cannot ship a profile that
leaves a §9/§12/§13 item unelicited.** The check does not care what the questions say — only that
every item a human must supply has something that asks for it.

**Run:** `python3 core/scripts/checks/check_discovery_adequacy.py --demo`
