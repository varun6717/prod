# ADR-008 — Solution Intent pivot (BRD/FRD → Solution Intent, tag removal, disposition routing)

**Status:** 🚧 **DRAFT — Phase A (decide) COMPLETE, all 8 items locked.** Not yet binding. Becomes
binding when Phase B (ladder re-cut) lands and this ADR is marked Accepted.

**Supersedes (when accepted):** D1, D3a, D5, D7 — and provisionally D4, D6, D9. Exact
supersession list is finalised in Phase B.

**Why this file exists now:** Phase A is a multi-session design discussion. Per `CLAUDE.md`,
durable state lives in files and git, never in the conversation. Decisions are recorded here as
they are made, so Phase B can be executed from disk rather than from memory of a chat.

---

## Context — the five changes driving this

1. **BRD + FRD → a single `Solution_Intent.md`** with a fixed section contract.
2. **Enrichment** — once Solution Intent v1 exists (code-blind, mandate only), a code pass
   corrects it and derives impacts the mandate never mentioned.
3. **Artifact disposition in the UI** — every input artifact is dispositioned by the operator as
   Requirement Doc / Product Domain Knowledge / Codebase / Architecture, plus a deliverable
   overview section.
4. **Information routing** — which input classes feed which Solution Intent sections.
5. **Remove tags** (the `vocabulary` → `adapter.emits` → profile-`topics` chain) for both drafting
   and code-impact; interrogate the remaining manifests.

## Process (agreed)

**A · Decide** (this document) → **B · Re-cut the ladder** (amend `REQUIREMENTS.md` +
`TECH_SPEC.md`, mark this ADR Accepted) → **C · Impact analysis** (classify every file
keep/amend/retire) → **D · Rebuild `TASK_LIST.md` and execute**.

Rationale for B before C/D: every task cites a doc section as its contract. Analysing code or
writing tasks against a superseded spec produces work that must be redone.

### Phase A agenda

| # | Item | Status | Where |
|---|---|---|---|
| 1 | Solution Intent section contract | ✅ **Locked** | D-A3, D-A4, D-A5, D-A10, D-A11, D-A14 |
| 2 | Disposition taxonomy | ✅ **Locked** | D-A12 |
| 3 | Routing matrix (section × input source) — *keystone* | ✅ **Locked** | D-A13 |
| 4 | Retrieval within a class — *was highest risk* | ✅ **Locked** — per-artifact index, no embeddings | D-A18 |
| 5 | Enrichment contract | ✅ **Locked** (§16 schema = per assertion × code location) | D-A6–D-A9, D-A15–D-A17 |
| 6 | Code-impact without tags | ✅ **Locked** — module-first tier walk; `tags` removed from §3.3 | D-A19 |
| 7 | Manifests | ✅ **Locked** — 5 artifacts, 3 granularities | D-A22 |
| 8 | Gates + guardrails | ✅ **Locked** — 3 check families, scoring rework, roles | D-A1, D-A23 |

### Decision index

| | Decision | Item |
|---|---|---|
| **D-A0** | Scope and cutover | — |
| **D-A1** | Gates re-map onto the v1/v2 lifecycle | 8 |
| **D-A2** | v1 → v2 relationship (one versioned doc, v1 frozen) | 1 |
| **D-A3** | Section contract (18 sections + touch types) | 1 |
| **D-A4** | Section rules (binding) | 1 |
| **D-A5** | The verdict population | 1 |
| **D-A6** | Claim provenance drives correction authority | 5 |
| **D-A7** | Enrichment never deletes | 5 |
| **D-A8** | Enrichment has two arms · retrieval/reasoning split · implicit assumptions | 5 |
| **D-A9** | Derived impacts and "reverse gaps" are one concept | 5 |
| **D-A10** | Conditional sections — dispositioned, never absent | 1 |
| **D-A11** | Section boundary statements (§4 / §9 / §15) | 1 |
| **D-A12** | Disposition taxonomy (6 classes + auto Codebase) | 2 |
| **D-A13** | Routing matrix (section × input source) | 3 |
| **D-A14** | Initiative level and the deliverable layer | 1 |
| **D-A15** | Jira mapping · where the FRD went · §16 as the story contract | 5 |
| **D-A16** | **Undispositioned findings live outside the document** · auto-apply vs escalate · `enrichment.json` as permanent record | 5 |
| **D-A17** | **The disposition walkthrough (interactive)** | 5 |
| **D-A18** | **Retrieval — the per-artifact index** · no embeddings · grouping & iteration | 4 |
| **D-A19** | **Code-impact without tags** — module-first tier walk · why it isn't tags · purpose creation order | 6 |
| **D-A20** | **Module derivation + `purpose` provenance** — measured against the real repo: flat tree, declared `Intention:` headers, versioned duplicates | 6 |
| **D-A21** | **Onboarding gate report** (stage distribution) · **the consolidated 3-phase process** | 6 |
| **D-A22** | **Manifests — a split, not a deletion**: 5 artifacts at 3 granularities | 7 |
| **D-A23** | **Gates, guardrails, roles** — 3 check families · scoring rework · confirmed role list | 8 |

> **The enrichment design is split** across **D-A6–D-A9** (arms, provenance, execution) and
> **D-A15–D-A17** (Jira, §16 contract, disposition). Read both groups together.

#### Mechanical guardrails accumulated for item 8

Replacing §10.1 (vocabulary containment) and §10.5 (emit-map no-drift), which die with tags:

1. §15 → §4 — every success criterion traces to an objective; every objective is measurable
2. §7 → §8 — every requirement traces to a deliverable *(load-bearing: builds the Jira hierarchy)*
3. Disposition-class totality — no orphan section, no orphan class
4. Every story names its code location, or is flagged new-build / non-code
5. Every §16 entry yields ≥1 story; every story traces to a §16 entry or a §7 deliverable
6. Every **assertion** in §8 has a verdict *(a requirement with 4 assertions and 3 verdicts is a defect)*
7. **Index completeness** — `lines_total == lines_indexed`; every line inside exactly one entry's range *(what makes "not in the index" a defensible negative)*

---

## Decisions locked so far

### D-A0 · Scope and cutover

- **Clean cutover.** The BRD/FRD pipeline is pre-production; it is retired in place. No shims,
  no parallel path, no compatibility period.
- **Jira authors directly off Solution Intent.** No FRD-shaped artifact survives. The entire
  `frd_*` layer retires (`frd_author`, `frd_validator` skill + `.py`, `frd_profile`, G2 as
  traceability, most of `metrics_scan`).
- **Both runtime tools stay** (Claude Code + Copilot). `overlay_manifest.yaml` and the §10.2
  parity check survive. Guardrail loss from tag removal is 5 checks → 3, not → 2.
- **TASK-056 is parked** — it validates UI → Generate → BRD/FRD, and both ends are moving. Its
  surviving half (*the pipe works end to end*) folds into the new acceptance task at the end of
  Phase D.

### D-A1 · Gates re-map onto the v1/v2 lifecycle

| Gate | Was | Now |
|---|---|---|
| **G0** | Generate — operator inspects the scaffold | unchanged |
| **G1** | BRD accepted | Solution Intent **v1** accepted (code-blind) |
| **G2** | FRD traceability + testability | Solution Intent **v2** accepted (enriched) |
| **G3** | confirm the Jira push | **Review the Jira plan** (all four levels, especially story testability + trace integrity) → *then* push |

G2 does not disappear with the FRD — it becomes the enrichment gate. `gate.py`, the telemetry
events, the validator pattern and the two-gate operator rhythm are all reused unchanged.

**The old G2 checks migrate to G3** (see D-A15): stories do not exist until after enrichment, so
nothing would otherwise review the technical decomposition before it is pushed. `frd_validator`'s
`0.5×traceability + 0.5×testability` formula largely survives inside `jira_validator`. G3 stops
being a rubber stamp and becomes the real technical-quality gate — appropriate, since it is the
last point before the only external mutation of a run.

### D-A2 · v1 → v2 relationship

**One document, versioned, with v1 frozen.** The deliverable is a single `Solution_Intent.md`;
stakeholders read one thing, not a base plus an overlay they must merge mentally.

On disk:

```
solution_intent/
  v1.md              # frozen at G1 — immutable
  v2.md              # the deliverable
  enrichment.json    # structured findings + operator dispositions
```

v1 is snapshotted because (a) auditability — what did we believe before we looked at the code;
(b) the v1→v2 diff **is** the value story of the enrichment stage; (c) G1 accepted v1 — if v1 is
mutated with no snapshot, the artifact the operator accepted no longer exists and the gate loses
its meaning.

**The placement rule: corrections revise in place; discoveries append.** The discriminator is
whether the finding contradicts an existing claim (revise) or adds something absent (append). A
document that goes to stakeholders must never be internally contradictory — a correction sitting
twelve pages from the claim it corrects leaves a false statement in the body.

**Every in-place revision carries provenance** — an inline citation to the code map entry or
`file:function` that drove it, in the same style as the existing cite-or-flag citations. Silent
rewriting of an accepted document is the failure mode this closes; at G2 the operator can see
exactly which sentences enrichment touched and on what evidence.

### D-A3 · Section contract

Enrichment touch types: **Verdict** (claims confirmed / contradicted / unverifiable) ·
**Correct** (contradicted claims rewritten, code-grounded) · **Extend** (new content within the
section) · **Regenerate** (derived from other sections, re-authored after they change) · **None**.

| # | Section | Authored | Enrichment touch |
|---|---|---|---|
| 1 | Executive summary | v1 | Regenerate |
| 2 | Problem statement | v1 | Verdict + Correct |
| 3 | Client need & demand | v1 | None |
| 4 | Business objectives | v1 | None |
| 5 | Personas & actors *(definitions + persona→use-case matrix)* | v1 | Verdict (weak) |
| 6 | High-level use case | v1 | Verdict + Correct |
| **7** | **Deliverables** | v1 | **Extend only** |
| 8 | Business requirements | v1 | **Extend only** |
| 9 | Strategic alignment | v1 | None |
| 10 | Constraints & design principles *(constraints, principles, NFRs)* | v1 | Verdict + Extend |
| 11 | Stakeholders | v1 | None |
| 12 | Out of scope | v1 | Extend (both directions) |
| 13 | Assumptions & risks | v1 | Verdict + Correct |
| 14 | Dependencies | v1 | Verdict + Extend |
| 15 | Success criteria | v1 | None |
| 16 | Derived system impacts | **v2 only** | — |
| 17 | Open questions | v1, extended in v2 | Extend |
| 18 | Verification summary | **v2 only** | — |

§16/§17/§18 sit at the end so a v1 document simply stops rather than carrying gaps mid-body. The
persona→use-case matrix stays inside §5. **§7 Deliverables sits immediately before §8
requirements** — structure before detail (D-A14).

Sections 3, 4, 9, 11, 15 are **never** touched by enrichment — pure business intent that code
cannot speak to. They also need no code input in the D-A13 routing matrix.

### D-A4 · Section rules (binding)

- **§8 Business requirements can only be extended, never corrected.** A requirement is a
  statement of *intent*; code cannot contradict an intent, only reveal that it is incomplete
  (→ escalation) or unachievable (→ that is a risk, §13). Allowing enrichment to rewrite a
  business requirement from code inverts the ladder — the existing implementation would begin
  dictating business intent. This is the worst failure mode available here.
- **v1 must author assumptions in checkable form.** §13 is the section best shaped for the
  verdict mechanism ("we assume settlement is unaffected" verdicts cleanly; "we assume the
  architecture is suitable" does not). The v2 design therefore constrains the v1 authoring
  contract.
- **§1 regenerates, it does not revise.** It is derived from the body; a summary of an
  uncorrected problem statement is silently wrong. Authored last in v1, re-authored in v2.
- **§12 Out of scope is a two-way door.** Escalated derived impacts can land *in* it; code can
  also reveal that something already declared out of scope is structurally coupled and cannot be
  avoided — an escalation *into* scope. Both directions run through the flag loop.
- **§17 Open questions is v1-authored.** v1 already produces unsourced gaps (`[TBD —
  unsourced]`), which today have no home. v1 ships with its own uncertainty visible; enrichment
  adds to the list rather than introducing it.
- **§5's verdict is asymmetric — system actors only.** A persona is a *type* of participant
  defined by goal and context, not a job title (Merchant, Certification analyst, Settlement ops)
  — and nothing in a C code map can confirm a human role exists. What code *can* confirm is the
  **system actor** half: an external interface implies a counterparty system. So Arm 2 verdicts
  actors reachable through interfaces and skips human personas entirely, rather than marking them
  unverifiable. The persona→use-case matrix is a coverage grid against §6 — it catches use cases
  with no participant and personas with nothing to do, and neither check involves code.
- **§18 is a summary, not a ledger.** Counts only (N checked, X confirmed, Y corrected, Z
  unverifiable). The claim-by-claim ledger lives in `enrichment.json`; unverifiable claims
  surface inline in their own sections where a reader needs them.

### D-A5 · The verdict population

When enrichment reads a section, every sentence sorts three ways:

1. **Factual current-state claim** → enters the verdict population
2. **Business judgment or intent** → skipped, never touched
3. **Future-state statement** → skipped (nothing in current code can verify what the system *will* do)

Without this scoping, every business sentence acquires an `[unverified against code]` marker and
the marker stops meaning anything. Code can say *"routing isn't hardcoded, it's a dispatch
table"*; code cannot say *"and that isn't a problem."*

**Structural limit.** The code map knows what calls what, not how fast or how often. Any claim
requiring runtime or behavioural data is unverifiable **by construction** — this hits §10's NFRs
and any §15 success criterion carrying a current-state baseline. Arm 2 must *recognise*
runtime-shaped claims and skip them, not mark them `[unverified against code]`, which would imply
we looked and failed when the pipeline cannot look at all.

### D-A6 · Claim provenance drives correction authority

v1 claims come from different places with different authority. The existing cite-or-flag rule
already tracks this, so no new v1 machinery is required — it simply gains a consumer.

| Claim provenance | Code contradicts it → |
|---|---|
| Source-derived | **Auto-correct** in place |
| Operator answer, or `UI_INPUT.frame` | **Escalate** — never overrule a human silently |
| `[TBD — unsourced]` | **Auto-fill** — not a correction, a gap closure |

The third row is net-new value: an unsourced gap the code can answer is the code arm closing a
`[TBD]` for free (the TASK-081 auto-fill idea arriving via a different door).

### D-A7 · Enrichment never deletes

Contradicted claims are **rewritten, never removed**. Deletion is invisible in a way rewriting is
not — at G2 an operator can see a changed sentence but cannot see a missing one. A claim left
vestigial after correction stays as corrected text.

### D-A8 · Enrichment has two arms

| | **Arm 1 — Requirement → code** | **Arm 2 — Claim → code** |
|---|---|---|
| Asks | *What did we miss?* | *What did we get wrong?* |
| Entry | §8 business requirements | §2, §5, §6, §10, §13, §14 |
| Nature | Generative — produces new content | Corrective — produces none |
| Motion | Walks `depends_on`/`used_by` to closure | Point lookup, then stops |
| Produces | §16 derived impacts; escalations → §8/§12 | In-place corrections; markers; §18 counts |

Arm 2 deliberately does **not** walk closure — that is what keeps it cheap per item and what
makes clustering work. If it traversed edges it would blur into Arm 1 and report the same impact
twice from two directions.

Arm 1 runs first — not because Arm 2 depends on it, but because Arm 1's closure pulls code slices
into context that Arm 2's claims often need.

**The same code fact can legitimately produce a finding in both arms.** If v1 §13 assumes
"settlement is unaffected" and closure shows it is impacted: Arm 1 writes a derived impact in
§16, Arm 2 corrects the assumption in §13. One fact, two findings, two destinations — that is the
ideal outcome, not duplication. The false assumption is corrected where a reader meets it; the
real impact is documented where engineering will scope it.

#### Per-claim verification mechanic

Reuses the existing coarse→deep machinery:

**claim → semantic match against the code map → candidate region → selective read of the slice → verdict**

Three coarse-stage outcomes, only one expensive: strong map-level match (verdict from the map, no
source read) · match needing confirmation (deep-read the slice) · **no match anywhere**
(*unverifiable*, cheaply — and often informative, since it usually means the claim concerns a
partner system or upstream dependency, which is itself worth surfacing to §14).

#### The loop is clustered by code, not by section

Iterating sections in document order means twelve claims about the routing subsystem trigger
twelve separate lookups across five sections.

```
extract claims (all verdict-eligible sections)
  → cluster by code region
    → per cluster: one coarse match, one deep read, N verdicts
      → scatter verdicts back to originating sections
```

Document order is a presentation concern; code locality is the cost driver.

#### Enrichment sequence

1. **Arm 1** — requirements → landing points, no-code-for-it gaps, closure → derived impacts + escalation candidates
2. **Arm 2** — claims extracted, clustered, verdicted → corrections staged
3. **One operator turn** — disposition every escalation and scope-moving finding. **This is a required stage, not an optional review: see D-A16** (what escalates vs auto-applies, and where each disposition routes) **and D-A17** (the interactive walkthrough). Only escalated findings reach it; the rest auto-apply.
4. **Apply** — corrections land in place; §16 written, §17 extended, §18 counted
5. **Regenerate §1** from the corrected body
6. **G2**

Deliberately **one** human turn. Both arms run to completion and accumulate findings in
`enrichment.json` before anything surfaces — otherwise the operator is interrupted mid-pass, and
an escalation that adds a requirement in step 3 would re-trigger Arm 1 in a way that is hard to
bound.

#### Iterate the code pass; batch the operator turn

Requirements are **not** all matched against the code in one shot — that will not fit in context at
real scale, costs more, and dumps an unreviewable pile of findings on the operator. But iteration is
an **execution strategy**, not an interaction one: batches accumulate into `enrichment.json` and the
human still gets a single dispositioning session.

**Retrieval batch ≠ reasoning unit** (V-refined). These are separate concerns and conflating them
costs accuracy:

- **Batch at retrieval — per deliverable (§7).** Resolve the deliverable's code territory **once**,
  at module level, from the map. Its requirements share code territory, so this is where the
  locality win lives.
- **Loop at reasoning — per epic, independently.** Evaluate one requirement at a time against the
  already-resolved territory, descending to its specific files/functions and deep-reading only that
  slice.

```
per deliverable (once):
  resolve code territory from the map — module-level, coarse
    └─ per epic (independent, fan-out safe):
         descend to specific files/functions within that territory
         deep-read only that slice
         map landing points + closure
         → per-requirement result into §16
```

**Why per-epic reasoning rather than a batched "map all of these" prompt.** Three failure modes,
all of which worsen as the code slice grows — and on a JPMC-scale codebase the slice eats the
context, leaving least attention per requirement exactly when each needs most:

- **cross-contamination** — R1's landing point attributed to R2
- **attention dilution** — later requirements in a list get shallower analysis than earlier ones
- **weaker exhaustiveness** — the model satisfices across the set instead of closing each one
- **headline-level matching (the sharpest reason, V-identified)** — an epic is **not atomic**.
  *"Populate field 48 subelement 92 with values 01–04, 2 bytes, EBCDIC"* is a bundle of detailed
  assertions, each with distinct code implications (do we parse field 48 at all · do we handle
  subelements · is the buffer big enough for 2 more bytes · do we already handle any of 01–04).
  Batching pushes toward matching the *headline* — "field 48 stuff → the parser" — because N epics
  are in flight at once, and the sub-details never get resolved.

#### §8 schema: a requirement is title + description + **assertions**

The document-structure consequence of "epics are not atomic." A requirement carries three parts:

```
R3  ·  deliverable: D1
    title:       Authorization message must carry the brand indicator      ← the Jira epic title
    description: Per Visa TL-2027-14, field 48 gains subelement 92 for     ← prose, for humans
                 brand routing on all acquirer-initiated authorizations.
    assertions:                                                            ← the checkable units
      a. subelement 92 is populated on all acquirer-initiated auths
      b. the value is 2 bytes, EBCDIC
      c. accepted values are 01–04
      d. existing field 48 subelements remain unaffected
```

**Assertions are what Arm 1 iterates.** Each gets its own code landing points, its own implicit
current-state assumptions, and its own verdict. Un-enumerated, extraction from prose is lossy — Arm 1
finds three of four and nobody knows which one went missing.

**An assertion is NOT a story** — an easy conflation, since both are "the multiple things that have to
happen":

| | Unit of | Example |
|---|---|---|
| **Assertion** | specification | "accepted values are 01–04" |
| **Story** | work | "extend `parse_field_48` to accept 01–04"; "widen `reconcile_fields` count check" |

The mapping is **many-to-many**. Assertion (c) may produce three stories (parser, validator,
settlement) — or **zero**, if the code already handles 01–04. Assertion (d) may produce only a
regression-test story. Collapsing them loses exactly the discrimination that makes the scope-shrink
case (D-A15) detectable.

**Consequences:**

- **§16's granularity sharpens** to per **(assertion × code location)**, not per (requirement × code
  location). Since §16 determines story granularity (D-A15), stories get more precisely scoped.
- **Guardrail 6 becomes checkable.** It was "every epic's implicit assumptions are verdicted" — fuzzy
  about what an epic's assumptions are. Now: **every assertion has a verdict.** A requirement with
  four assertions and three verdicts is a detectable defect.
- **Authoring cost is near zero** — assertions are **agent-extracted** from the source text during v1
  authoring, not hand-written. And this gives G1 something concrete to review: *are the assertions
  faithful to the tech letter?* Cite-or-flag at assertion level, a tighter check than reviewing prose.

#### Requirement details carry implicit current-state assumptions

D-A5 excludes future-state statements from the verdict population, and *"must populate subelement
92"* is future-state. But it **silently assumes** *"field 48 has room for two more bytes"* — and
that is a current-state claim, which **is** verifiable.

| Implicit assumption | Code says | Finding |
|---|---|---|
| "field 48 has room" | fixed 64 bytes, all 64 in use | **major** — a structural change, not a field addition |
| "we don't support 01–04 yet" | 01–02 already handled | **scope shrink** |
| "we parse subelements" | flat field parse only | a new capability, not an extension |

Without surfacing these, the pipeline emits a story — *"add subelement 92 to the parser"* — that is
**technically impossible as written**, and nobody discovers it until an engineer picks it up.

So **Arm 1's per-epic pass extracts each requirement's implicit current-state assumptions and hands
them into the verdict machinery** (Arm 2's mechanic, applied to Arm 1's material — the arms are not
cleanly separated at the detail level). This is another thing a batched pass structurally cannot do:
implicit assumptions surface only when reasoning closely about one requirement's details.

This mirrors the existing coarse (map-level, broad) → deep (per-requirement, focused) architecture,
applied one level up.

**Batch the reading, keep the results per-requirement.** Each epic needs its own landing points and
closure — stories hang off individual epics and §16 must be machine-consumable per requirement
(D-A15). Batching is a context/cost optimisation, never a merging of results.

**Guard against anchoring.** A sequential loop carrying accumulated context can lazily map epic 2 to
whatever components epic 1 landed on — a correctness risk plain batching does not have. The loop may
carry **structural learnings** ("this module uses macro-based dispatch; closure must follow the
macro") but must **re-derive mappings independently** per epic. Never inherit a landing point.

**Independence makes fan-out preferable.** Because per-epic analysis is deliberately independent, the
loop need not be sequential — fan out per-epic subagents against the shared resolved territory (the
pattern `code_impact` already uses). That eliminates anchoring entirely (no shared context to anchor
on), runs faster, and preserves the single territory resolution. Sequential buys only cross-epic
learning, a nice-to-have; independence is a correctness property.

**Cost:** N model calls per deliverable rather than one. Accepted without much debate — a missed
impact becomes a missed story becomes broken production code, an asymmetry that dwarfs token cost.

**Scale fallback:** if a single deliverable's requirement set still will not fit, split it by **code
locality within the deliverable**, never arbitrarily, so the locality benefit being batched for
survives the split.

Summary of the two arms' units:

- **Arm 1** → retrieval batched per **deliverable**, reasoning looped per **epic**
- **Arm 2** → clustered per **code region**
- findings accumulate → **one** operator turn

### D-A9 · Derived impacts and "reverse gaps" are one concept, not two

**Reverse gaps as originally conceived cannot be detected at Solution Intent time.** Closure walks
outward *from* requirement landing points, so by construction every node it reaches is traceable
to a requirement — there is no untraceable code. More fundamentally, at SI time **there is no
diff**: you have requirements plus a code map of the *current* state, so "code we're touching" is
not a knowable set.

What is real is **one finding type — a derived impact — with one follow-up question**:

> Is this a technical consequence we simply document, or does it change behaviour someone has to
> make a decision about?

| Finding | Disposition |
|---|---|
| Settlement recon's field-count validation must widen | Technical consequence → §16, done |
| Settlement recon will now reject previously-accepted transactions | Business-visible → **escalate** |

Escalated findings run through the flag loop; the operator's decision lands them in §8 (new
requirement) or §12 (explicitly excluded). The "the network's mandate was incomplete" case is not
a separate detector — it is a derived impact that escalated, made visible because a human had to
disposition it.

`enrichment.json` carries `escalated: true|false` per impact, plus the operator's disposition when
true.

**Parked (5C candidate):** true scope-creep detection — "we implemented things nobody asked for"
— is valuable but belongs at a later stage, comparing an *implementation branch* against the
accepted Solution Intent. Different input (a diff, not a code map), different moment (post-build).
**One switch would revive it early:** if `UI_INPUT` ever gains an operator-declared change scope
("we are modifying the payment routing subsystem"), then code inside that declared scope which no
requirement reaches becomes detectable at SI time.

---

### D-A10 · Conditional sections — dispositioned, never absent

Not all 17 sections apply to every change. But **an omitted section and a forgotten section look
identical**, so a conditional section is never simply left out. Three legitimate end states, all
visible in the document:

| State | Renders as |
|---|---|
| Filled | the content |
| Required, nothing to say | *"None identified"* — a positive assertion |
| Conditional, does not apply | *"Not applicable — &lt;reason&gt;"* |

**Applicability is agent-proposed, operator-confirmed at G1.** Not operator-declared at config
time (the operator has not seen the sources yet, and cannot know whether strategic-alignment
content exists); not silently agent-decided (a section vanishing because the agent found no
content is exactly the silent failure the guardrails exist to catch).

| Status | Sections |
|---|---|
| **Conditional** | §3 Client need & demand · §6 High-level use case · §9 Strategic alignment |
| **Required, may be empty** | §5 Personas & actors · §14 Dependencies · §17 Open questions |
| **Required** | all others (§16/§18 required in v2) |

Rationale for the conditional three: a regulatory mandate has no client demand (§3); some changes
modify behaviour without introducing a use case (§6); and §9 is the section most likely to attract
ceremonial filler — making it conditional lets *"not applicable, this is a compliance mandate"* be
an honest answer.

G1's absolute precondition becomes: every **required** section satisfied, and every **conditional**
section either filled or explicitly dispositioned N/A with a reason.

### D-A11 · Section boundary statements (§4 / §9 / §15)

Business objectives, Strategic alignment and Success criteria all answer some form of *"why, and
what does good look like."* They are distinct in principle — **intent · portfolio fit · measurable
outcome** — but blur badly in practice, and overlapping sections make `must_capture` authoring
(item 3) ambiguous: a fact that could satisfy two sections satisfies neither cleanly.

Fix is authoring discipline, enforced by a one-line boundary per section:

- **§4** — what we intend to achieve. **No dates, no metrics.**
- **§9** — why this matters to the portfolio *above* this project. **Must reference something
  external to the project** — a program, strategy, or roadmap commitment.
- **§15** — how we will measure §4. **Must be measurable, and every criterion traces to an
  objective.**

Worked contrast (Mastercard mandate):

| | Written well | Written badly |
|---|---|---|
| §4 | "Maintain Mastercard network compliance and avoid decertification" | "Achieve compliance by Q3 2027" *(a success criterion in disguise)* |
| §9 | "Supports the Merchant Services 2027 single-platform brand-parity program" | "Compliance is critical to the business" *(§4 restated)* |
| §15 | "100% of Mastercard transactions carry the new indicator by 2027-07-01; zero certification defects" | "Remain compliant" *(an objective, not a measure)* |

**§15's boundary doubles as a mechanical guardrail** — an objective with no success criterion is
unmeasurable; a criterion with no objective is orphaned. Both are statically checkable. **Carry to
item 8** as a candidate replacement for the structural checking lost when §10.1 dies.

### D-A12 · Disposition taxonomy (item 2)

Every input artifact carries a **disposition** declaring the role it plays *in this run*.
Disposition is orthogonal to source **type** (`file` / `sharepoint` / `confluence` / `bitbucket`):
type is *where it came from*, disposition is *what it is for*. Today the doc/code class is
**derived** from type; disposition makes it **operator-declared** — a contract change to §3.1 and
to `source_processor`'s routing.

**Operator-selected (documents):**

| Disposition | What it is |
|---|---|
| **Business Requirement** | The ask: article mandates, business requirement docs — obligation, scope, deadline |
| **Technical Specification** | Normative detail: network specs, tech letters, field formats, protocols |
| **Product Domain Knowledge** | How the product works today: Confluence KB, product guides — steady-state reference |
| **Architecture** | System design: architecture docs, diagrams, integration maps |
| **Prior Artifact** | Decisions already made: Jira epics, previous Solution Intents |
| **Other** | Background context only — **not citable as a primary source** |

**Auto-set, non-editable:** **Codebase** — set automatically when the source is a Bitbucket/GitHub
URL. It is the one disposition the operator does not choose, because it is derivable from type, and
it routes down the existing code arm rather than the doc arm.

**Business Requirement vs Technical Specification are split because they route differently.** An
article mandate ("support the new indicator by Q3 2027 or face decertification") feeds §2, §4, §8,
§15. A tech letter ("field 48 subelement 92 carries a 2-byte indicator, values 01–04") feeds §10 and
is the primary input **Arm 1 matches against code**. Same corpus, different destinations.

**Multiplicity is orthogonal to classification.** Multiple requirement documents are multiple UI
rows (the pattern proven by Confluence in TASK-063B — one link per row, each its own source entry).
Each row independently carries its disposition.

**Multi-disposition is allowed but defaults to one.** Mixed documents are real (a 200-page
architecture doc containing three pages of requirements), so forbidding multi would push operators
into adding the same file twice. But most artifacts genuinely have one role, so the narrowing that
disposition exists to provide survives.

**Why `Other` is second-class rather than a plain Misc bucket.** A fallback class has no routing
rule by definition: route it nowhere and the operator uploads something that silently does nothing
(the exact failure mode the guardrails exist to catch); route it everywhere and it pollutes every
section. So `Other` is readable by the discovery pass but **never valid as the sole citation for a
claim**. Frequent use of `Other` is the signal to add a class, not evidence that `Other` works.

**Parked:** *Operational material* (runbooks, incident reports, support tickets — strong input to §2
and to current-state claims) slots in later as its own class without disturbing the rest.

#### Two consequences

- **Prior Artifact carries a grounding hazard.** With a previous BRD or Jira epic in the corpus, the
  agent can **copy** from it instead of deriving from the mandate — and the copy will look properly
  cited. Prior Artifact is therefore **reference-only**: usable to establish what was previously
  decided, never the primary citation for a *new* requirement. Cite-or-flag must distinguish them.
- **Architecture and Technical Specification are the only document classes making code-verifiable
  claims.** Everything else is business intent or the ask. So Arm 2's machinery could verdict *those
  documents* against the code ("does our implementation match the spec?"), with mismatches as
  findings. Out of scope now; **parked as an enhancement** — the disposition split is what unlocks it.

### D-A13 · Routing matrix (item 3 — the keystone)

This replaces tag-based retrieval routing (`file.topics ∩ section.topics`). It is **section ×
input source**, not section × disposition — because the **operator** is an input source, in two
distinct forms.

**Frame vs Discovery.** Both are operator-authored, but they behave differently: the **frame** is
one text, available up front, global in effect; **discovery answers** are many, elicited
per-section, and accrue during authoring. They cannot share a column.

**`frame` gains a free-form `overview`** alongside its existing structured fields — it is *added*,
not a replacement. The structured fields are machine-useful in a way prose is not
(`frame.stakeholders` → §11 directly, `frame.key_dates` → §15 directly, `scope_hints` → Arm 1
scoping). The prose overview has two jobs: it supplies §1's *initiative identity*, and it is a far
better semantic query for Arm 1's code matching than concatenated key-values (per TASK-066
refinement (d)).

**P** = primary (section authored mainly from this) · **S** = supporting (consulted) ·
**E** = enrichment only (v2) · blank = no input

| § | Section | BizReq | TechSpec | DomKnow | Arch | Prior | Frame | Discovery | Code |
|---|---|---|---|---|---|---|---|---|---|
| 1 | Executive summary | | | | | | **P** | | |
| 2 | Problem statement | **P** | | S | S | | | | E |
| 3 | Client need & demand | **P** | | S | | | | | |
| 4 | Business objectives | **P** | | | | | S | | |
| 5 | Personas & actors | | | **P** | S | | | | E |
| 6 | High-level use case | S | | **P** | | | | | E |
| **7** | **Deliverables** | **P** | S | | | | S | S | E |
| 8 | Business requirements | **P** | **P** | | | S | | | E |
| 9 | Strategic alignment | | | | | S | S | **P** | |
| 10 | Constraints & principles | | **P** | | **P** | | | | E |
| 11 | Stakeholders | | | | | S | **P** | S | |
| 12 | Out of scope | **P** | | | | | S | **P** | E |
| 13 | Assumptions & risks | | | S | S | | | **P** | E |
| 14 | Dependencies | | S | | **P** | | | | E |
| 15 | Success criteria | **P** | S | | | | S | S | |
| 16 | Derived system impacts | | | | | | | | **P** |
| 17 | Open questions | | | | | | | | |
| 18 | Verification summary | | | | | | | | **P** |

`Other` has no column: it is never primary and never supporting — background context only, per
D-A12. The empty column *is* the definition.

**Scoping vs sourcing.** The frame **scopes** every section (`scope_hints` + `overview` tell the
agent what is relevant when reading any source for any section) but **sources** only §1, §4, §9,
§11, §12, §15. The table expresses sourcing; scoping is global and cannot be tabulated.

#### What the matrix reveals

- **Discovery is primary for exactly three sections** — §9, §12, §13. No document in the corpus
  answers them, so disposition and retrieval work buys those sections **nothing**; their quality
  rests entirely on discovery-question quality. This promotes TASK-079 (discovery adequacy) from
  nice-to-have to core.
- **`frame.stakeholders` already serves §11**, which is why §11 is frame-primary rather than
  discovery-primary — one fewer section depending on question quality than first drafted.
- **Prior Artifact is never primary anywhere** — always S, always reference-only. Falls out of the
  D-A12 grounding hazard rather than being imposed on top of it.
- **TechSpec is narrow but deep** — primary for only §8 and §10, yet it is the main input Arm 1
  matches against code. Small documentary footprint, large enrichment footprint.
- **§1, §17, §18 take no input class** — §1 is derived from the body (+ frame identity), §17
  accumulates gaps, §18 counts verdicts. No routing rule needed.

#### This sizes item 4

Retrieval precision matters only where a **primary** class carries **large** documents:
**BizReq, TechSpec, DomKnow** — nine sections. Architecture docs and Jira epics are typically small
enough to read whole; the discovery- and frame-primary sections involve no retrieval at all.

So item 4 is not "solve retrieval for six classes across seventeen sections" — it is **three
classes feeding nine sections**, and those three are precisely the classes whose documents are
*structured* (mandates, network specs, KB pages), which is what makes structural segmentation
viable.

### D-A14 · Initiative level and the deliverable layer

**The Solution Intent is authored at the initiative level.** Two scales must both work:

- a **PBI change**, where the change itself *is* the initiative (1–3 deliverables), and
- a **high-level JPMC initiative** spanning many deliverables.

The 18 sections hold at **both** scales — executive summary, problem, objectives, strategic
alignment, stakeholders and success criteria are all naturally initiative-level regardless of size.
**Nothing in the section contract changes with scale.** What varies is decomposition depth below
§7, and the deliverable count is effectively the tell. A metadata field declares the level;
no second document type is needed.

#### Deliverable vs Requirement

| | Definition | Verb |
|---|---|---|
| **Requirement** (§8) | A statement of what must be true — *"the authorization message must carry the 2-byte indicator in field 48, subelement 92"* | **satisfied** / verified |
| **Deliverable** (§7) | A unit of work product built and handed over — *"updated authorization parser", "certification test package"* | **delivered** |

Requirements are normative; deliverables are work packages with an owner and a date. The relation
is many-to-many, but a deliverable typically groups several requirements.

**`frame.overview` (the free-form Initiative Overview) seeds the deliverables; the agent refines
them from the sources, and discovery fills gaps.** There is no separate deliverable-overview input
— hence §7 is BizReq-primary with Frame and Discovery supporting (D-A13).

**Third mechanical guardrail** (with §15→§4 and D-A12's): a deliverable with no requirements is
unjustified; a requirement with no deliverable is unbuildable. Both statically checkable — and per
D-A15 this one is **load-bearing**, not merely a consistency check.

**New escalation type.** A derived impact can now imply a **new deliverable**, not just a new
requirement — arguably the most consequential kind, since it moves cost and schedule rather than
only scope. Hence §7 carries an `E` (extend) in the matrix.

### D-A15 · Jira mapping — and where the FRD actually went

JPMC's Jira hierarchy is **Initiative → Deliverable → Epic → Story** (confirmed): initiative =
strategic, high level; deliverable = high-level deliverables; epic = a business requirement within
a deliverable; story = the technical requirements needed to complete that business requirement.

| Jira level | Source | Available at |
|---|---|---|
| **Initiative** | the document itself — §1 identity, §2 problem, §4 objectives | v1 |
| **Deliverable** | §7 Deliverables | v1 |
| **Epic** | §8 Business requirements — one epic per requirement | v1 |
| **Story** | Arm 1 code landing points + §16 derived system impacts | **v2 only** |

**A business requirement is epic-sized, not story-sized** — "carry the 2-byte indicator in field
48" needs parser changes, validation changes, test updates and certification. That is a body of
work, not a unit.

**The FRD did not die; it moved.** "Technical requirements per epic" *is* FRD content. The old chain
was BRD → FRD → Jira; the new chain is Solution Intent → enrichment → Jira, with **stories carrying
the technical requirement**. The technical layer was never optional — it simply does not need to be
a markdown deliverable, and it now lives where engineers work.

This is **strictly better than the old FRD**, which had to assert technical detail with only the
BRD underneath it. Story authoring instead draws on a grounded input set: the epic it serves
(business intent) + Arm 1's landing points and closure (where the code actually is) + Technical
Specification (field formats, protocol detail). Nothing invented — cite-or-flag holds.

#### Three consequences

- **Jira cannot be authored from v1.** v1 can produce three of the four levels; stories require
  enrichment. G3 must follow G2 — already the gate order, but now for a reason rather than by
  convention.
- **The §7→§8 trace is load-bearing.** It physically builds the Jira parent-child hierarchy; an
  orphan requirement yields an Epic with no parent Deliverable.
- **§16 has a dual role** — a section stakeholders read *and* the substrate story generation draws
  from. It therefore needs enough per-requirement structure to be **machine-consumable**, not just
  readable prose.

#### A Technical Specification is not stories — it is the external contract

A Visa/Mastercard **tech letter** reads as technical requirements but is **not** story-level. It
specifies the *external contract*; a story is a unit of *internal work*. The letter is **code-blind
about our system** by construction — Visa has never seen our codebase — so it cannot name which
module parses field 48, that settlement recon validates field counts and will break, that the cert
harness needs coverage, or whether we already partially support it. Stories are
implementation-specific; the letter cannot be one.

**Flow:** tech letter → §8 requirements (epics) + §10 constraints → Arm 1 against code → stories.
It *drafts* the epics; stories are **derived** from validating those epics against the code, never
read off the letter.

Its content fans out further than a single section (hence TechSpec carries `S` in §7 and §15):

| Tech-letter content | Lands in |
|---|---|
| "must populate subelement 92 with values 01–04" | §8 requirement → epic |
| "2 bytes, positions 1–2, EBCDIC" | §10 constraint |
| "effective 2027-07-01" | §15 success criteria |
| "certification required via VCMS" | implies a §7 deliverable |

**Two things this unlocks:**

- **The tech letter is a verification oracle for the story set.** Because it specifies the external
  contract precisely, completeness can be checked in the *other* direction — taken together, do
  these stories satisfy the letter? A business mandate is too vague to support that check. This is
  where G3's testability review gets real teeth.
- **Verdicting a tech letter against code can *shrink* scope** — the one enrichment finding that
  *reduces* work. The letter says "support 01–04"; Arm 2 finds 01–02 already handled, so the real
  requirement is narrower than the letter implies. Every other finding tends to add (ripple, derived
  impacts, escalations). Only possible because TechSpec makes code-verifiable claims (D-A12).

**Guardrail — every story must name its code location.** The temptation is to transcribe the
letter's language into stories: *"populate field 48 subelement 92"* looks technical but names no code
location, so it carries zero implementation guidance — the spec laundered into Jira without the
analysis. A story must name the code it changes, or be explicitly flagged **new-build** or
**non-code** (cert/doc/test). Mechanically checkable at G3, and it is what distinguishes a real story
from a restated requirement.

#### Where the four levels physically live

| Jira level | Location | Note |
|---|---|---|
| **Initiative** | the document itself — fields from §1, §2, §4 | 1:1 with the SI; no section of its own |
| **Deliverable** | **§7** | v1-authored |
| **Epic** | **§8** — one epic per requirement | v1-authored |
| **Story** | **`jira_plan/`, not the SI** | generated after G2 |

```
Solution_Intent.md (v2)
  §7  Deliverables            → Jira Deliverable
  §8  Business requirements   → Jira Epic
  §16 Derived system impacts  → the evidence stories are derived FROM
                                   ↓
                        (after G2)  jira_plan/ → Stories → G3 → push → trace.json
```

**Stable IDs are required** for the chain to hold: §7 deliverables carry IDs (`D1`…); §8
requirements carry IDs (`R1`…) **plus** a `deliverable:` reference (the load-bearing §7→§8 trace);
§16 entries reference their requirement ID; `jira_plan/` stories reference a requirement ID + a code
location. Full chain: `D1 → R3 → impact entry → story → JIRA-1234`.

**§16 is organised by requirement, not by code area.** Arm 2 clusters by code region, but that is
*processing* order — presentation must be per-requirement, because that is what stories hang off and
what makes §16 machine-consumable. A by-area view is a cross-index, not the primary structure.

No "Jira plan summary" section in the SI — G3 reviews `jira_plan/` directly, so a summary in the
document would be a second copy that drifts.

#### Why stories are not in the SI — stable analysis vs mutable work item

Not because stakeholders reject technical detail: **§16 is already technical**, down to
`file:function`. The actual reason:

- **§16 is a finding** — what the code says today. Stable. Belongs in an accepted, versioned document.
- **A story is a work item** — refined, split, re-estimated, reassigned during delivery. Mutable.
  Belongs in the tracker.

Stories in the SI would mean every sprint-time refinement dirties a document frozen at G2.

**§16 determines the story set; `jira_plan/` specifies each story.** An impact entry says
"`parse_field_48` is affected"; a story says "extend `parse_field_48` to read subelement 92 as a
2-byte value — done when 01–04 parse correctly and the 64-byte path regresses clean." Scope vs
specification: action verb, acceptance criteria, testability, sizing. §16 carries **scope**; the
translation **adds** the rest. It is a transformation, not a copy.

**§16 is not the only story source** — leave this implicit and every non-code deliverable silently
yields zero stories:

| Story source | Comes from | Example |
|---|---|---|
| Code-derived, **modify** | §16 entry — an *impact* | extend `parse_field_48` for a 2-byte subelement |
| Code-derived, **new build** | §16 entry — a *gap* | create subelement-92 range validation (no code exists) |
| **Deliverable-derived** | **§7 only — no §16 entry** | certification test package, documentation update |

**Naming trap: §16 holds gaps as well as impacts.** Arm 1 explicitly asks *"where is there no code
for this requirement"*, and that finding needs a home. It is not an open question (§17) — it is
*known work*; and not a new requirement (§8) — the requirement exists, the code does not. So §16
means "how this change lands on the codebase," **including "nothing exists here, must be built."**

**A "no code found" gap does NOT auto-generate a build story — it escalates.** The story builds the
*code*, never "the requirement" (which already exists in §8). But the finding is ambiguous, and only
one of its four meanings is a build story:

| What "no code found" actually means | Correct outcome |
|---|---|
| Genuinely new capability — the system has never done this | **Build story** ✓ |
| The code exists; Arm 1 missed it | **Search failure** — a build story here duplicates working functionality |
| The code lives in another repo (within-repo boundary, FR-DC-13) | **A dependency** (§14), not a story for this repo |
| The requirement is not code at all — "must be certified by Visa" | **Deliverable-derived** work, no code story |

Auto-converting every gap to "build it" would be wrong in three of four cases, and wrong expensively
— a duplicate-implementation story gets estimated, assigned, and possibly built before anyone notices
the capability already existed.

The reasoning mirrors a principle already in the design: Arm 2 treats "no match anywhere →
**unverifiable**" as an honest, cheap outcome rather than a conclusion. Same here — *"this capability
exists nowhere in our codebase"* is a strong **negative** claim, and negative search results are the
least reliable kind. **Absence of evidence over a large codebase is not evidence of absence.**

So a gap **requires disposition**, and the operator confirms which of the four it is; only the first
becomes a build story. One more item in the single operator turn — and exactly the judgment that
should be human, since on a JPMC-scale codebase "we have never done this" is a claim only someone
with system knowledge can confidently confirm.

### D-A16 · Undispositioned findings live outside the document

**Items awaiting disposition are not in any Solution Intent section.** They sit in
`enrichment.json` with an undispositioned status. The SI contains only **resolved** content —
otherwise v2 would ship with "TBD, awaiting operator" scattered through it.

Routing for a "no code found" gap once dispositioned:

| Operator's call | Lands in |
|---|---|
| Genuinely new capability | **§16** — gap entry, becomes a build story |
| Arm 1 missed it | **dropped** from findings (it was wrong); logged to `decisions.jsonl` |
| Lives in another repo | **§14** Dependencies |
| Not code at all | **§7** Deliverables, as non-code work |
| **Cannot determine yet** | **§17** Open questions |

**The defer path is required.** An operator who genuinely cannot confirm *"have we ever done this?"*
must be able to defer, and deferral converts the finding into a real open question rather than
forcing a guess. Without it the walkthrough pressures people into fabricating certainty at precisely
the point where the design demands honesty.

#### What actually reaches the operator (consolidating D-A6 / D-A9 / D-A16)

Most findings **never** reach the walkthrough. It is not "review all findings" — it is "review the
ones needing judgment":

| Finding | Path |
|---|---|
| Code contradicts a **source-derived** claim | **auto-corrects** in place |
| Code answers an **unsourced `[TBD]`** | **auto-fills** |
| Derived impact, **technical consequence** | **auto-writes** to §16 |
| Code contradicts an **operator answer or the frame** | **escalates** |
| Derived impact, **business-visible** | **escalates** |
| **No code found** for a requirement | **escalates** (four-way ambiguous) |
| Anything **scope-moving** | **escalates** |

The pattern: findings that are **grounded and unambiguous** apply themselves; findings that are
**ambiguous, scope-moving, or would overrule a human** escalate. This filtering happens *before* the
walkthrough, which is what keeps the volume tractable.

Each escalated type carries its own routing table — the four-way one above is specific to no-code
gaps. Business-visible impacts route to §8 or §12; operator-contradictions route back into whichever
section made the claim, or to §17 if deferred.

#### `enrichment.json` is a permanent record, not a scratch file

It survives past disposition as the audit trail: every finding, its evidence, whether it auto-applied
or escalated, the operator's call and their rationale. That is what lets someone at G2 ask *"why does
§13 say this now?"* and get an answer. **The v1 snapshot plus `enrichment.json` together reconstruct
exactly how v2 came to be.**

### D-A17 · The disposition walkthrough (interactive)

The single operator turn is delivered as a **guided conversational walkthrough**, not a handed-over
list: present one finding with its evidence, recommend a disposition with reasoning, let the operator
interrogate ("show me the code", "what else touches this?"), then record the decision **and its
rationale** to `decisions.jsonl`. Reuses the FR-BR-08 surface→wait→apply loop and TASK-042's flag-loop
machinery.

Four binding constraints:

- **Proposes, never decides.** The existing principle, especially load-bearing here — this is the
  *one* human checkpoint in the whole enrichment stage.
- **Triage, do not enumerate.** A one-at-a-time march through 200 findings is unusable and flattens
  importance. Scope-moving findings and no-code gaps get individual attention; routine technical
  consequences batch — *"these 15 are technical consequences with no business visibility — accept all,
  or review?"* This is the existing material-vs-advisory distinction (D6c) applied to the walkthrough.
- **Dispositions have ordering dependencies.** Confirming that a finding was a *search miss*
  invalidates findings derived from that gap. So the walkthrough is not a flat queue — it must
  sequence dependent findings and revisit downstream ones when an upstream call changes.
- **Resumable.** Fifty findings will not be dispositioned in one sitting. Status persists per-finding
  in `enrichment.json`; the file-based model handles this naturally, so the operator can stop and
  resume without losing position.

Likely a **new role in `overlay_manifest`** — the analytical arms are non-interactive; this one is
purely interactive.

**Sixth mechanical guardrail** — because the story set is *determined* rather than invented, it is
checkable both ways:

- every §16 impact entry produces **≥1** story → catches **dropped impacts**
- every story traces to a §16 entry, **or** is explicitly new-build / deliverable-derived → catches
  **invented stories**

#### Story granularity — resolved, not deferred

Previously parked as an item-5 decision ("one story per (requirement × component), or clustered?").
It is **not a separate decision**: **§16's granularity *is* story granularity.** "The parser is
affected" is ambiguously 1 or 5 stories; but

> `R3 → parse_field_48`: must handle a 2-byte subelement
> `R3 → validate_subelements`: must accept subelement 92
> `R3 → field 48 buffer`: capacity exhausted, structural change required

is unambiguously three. The decision therefore moves **upstream** into how Arm 1 structures §16 —
a better home, since that is where the code evidence lives.

### D-A18 · Retrieval within a class — the per-artifact index (item 4)

**No vector embeddings** (V decision — available, but disproportionate). Instead, at ingest each
artifact gets a derived **index file**: one entry per document subsection, carrying its heading, line
range, and a condensed summary. At authoring time a section consults the index and pulls only the
identified passages.

It is a **deepened `descriptor`**, not a new mechanism — §3.2 already carries a one-line summary per
*document*; this is one entry per *subsection*. And `pdf_extract` already emits "the document's heading
hierarchy… section headings and hierarchy, paragraph order, bullet/numbered lists, and tables", so the
index keys on structure **already produced**. No extraction change.

#### Why an index beats tags: sparse vs dense

A tag exists only where someone applied it, so *"no tag matched"* conflates **the content isn't there**
with **the tagger missed it** — indistinguishable, which is the silent-invisibility failure mode. An
index summarises **everything by construction**, so *"not in the index"* is a **defensible negative**.
That is the difference between absence of evidence and evidence of absence, and tags could never have it.

It also makes the two arms **symmetric**: `code_map.json` is a per-component index with a model-written
`purpose`; this is a per-subsection index with a model-written summary. Same architecture both sides —
and it closes ADR-005 open-Q #2 (the doc-side analog), i.e. TASK-067's purpose.

#### Two files per artifact (V-confirmed)

```
context_set/sharepoint/
  mc_mandate_2027.md           ← FULL extract — nothing condensed
  mc_mandate_2027.index.json   ← heading + summary + line range per entry
```

**The summary is never what gets sent.** It is what the agent reads to *choose*; the agent then pulls the
**actual extracted text** at the selected line ranges. So the index is a table of contents with better
descriptions — a routing aid, never a substitute for content, and no information is lost.

```
1. agent reads index         headings + summaries       ← small, selection only
2. agent selects entries     "2.1, 2.2 look relevant"
3. agent reads lines 92–206  the REAL extracted text    ← full fidelity
```

**Summaries are always generated**, not conditional. The alternatives considered were (a) index on
headings alone — free and deterministic, but mandate documents are exactly the genre full of
`General Provisions` / `Background` / `Appendix B` headings, and a heading titled "Background" may hold
precisely what §2 needs; and (b) heading + the section's first N lines — free, but noisy when a section
opens with boilerplate. Summaries also carry specifics no heading can (*"cites 2026 dispute volumes"* is
what §2's `must_capture` "what it costs" is hunting for). Cost is one cheap pass per artifact, cached,
and **only for artifacts over the whole-read threshold**. A uniform rule beats a heading-quality
heuristic that could misfire silently; the conditional remains available later as a pure optimisation.

#### Shape

```json
{ "path": "context_set/sharepoint/mc_mandate_2027.md",
  "disposition": "business_requirement",
  "pages": 40, "lines_total": 1840, "lines_indexed": 1840, "entries": 27,
  "subdivided": ["3.2.2"],
  "index": [
    { "id":"2.1", "heading":"Current Brand Identification", "lines":[92,148],
      "summary":"How brand is identified today: PAN-range lookup at authorization time, where it sits in the flow, which parties depend on it." },
    { "id":"2.2", "heading":"Limitations of PAN-Range", "lines":[149,206],
      "summary":"PAN ranges cannot distinguish co-badged products; causes misrouted interchange. Cites 2026 dispute volumes." }
  ] }
```

Six SI sections drew six *different* slices from that one 40-page document (§2 → 8% of lines, §10 → 7%,
§15 → 7% …). Per-document tagging would have handed all six the same 1840 lines.

#### Four rules

- **Per semantic subsection, never per page.** A page is a layout artifact — a clause spans three pages,
  a page holds four clauses. The document's own numbered structure is a *better* index than pagination
  and is already extracted. **Pages matter only as a size proxy** for deciding whether to subdivide.
- **Subdivide oversized entries along content boundaries.** A 6-page value table is one heading but far
  too big for one entry → `3.2.2a` / `3.2.2b` split at the natural content seam (global vs regional
  codes), never at a page break. Record it in `subdivided[]` so the synthetic split is auditable, not silent.
- **Build always; consult conditionally.** Building is cheap, keeps one code path, and is the audit trail
  for *"did we consider this document for this section?"* But a 3-page document is read whole — no index hop.
- **The index describes the document, never the destination.** If an entry said *"this feeds §2"* it would
  be tags re-invented: a mapping that drifts whenever the section contract changes. Content-keyed keeps it
  SI-blind and serves all 18 sections unmodified.

Structure is deterministic (from extraction); the summaries are a **model pass at ingest** — fine, the
model-free rule governs the code map only.

#### Replaces the §3.2 routing rule

- **was:** `source ∈ section.sources AND topics ∩ section.topics ≠ ∅` → load document/summary
- **now:** `disposition ∈ section.classes` (D-A13) → if over budget, consult the index → pull identified passages

#### The whole-read threshold is derived, not chosen

Not really pages — pages are a proxy. The constraint is **the context budget remaining** after a
section's other inputs (its purpose, the frame, the draft so far). If a document fits comfortably, read
it whole: the index hop adds a step and can only *lose* information. ~400–600 lines (≈10–15 pages) is a
defensible start, but it is a **config value calibrated against real documents**, never hardcoded — it
depends on the model's window.

**It must be checked across the selected *set*, not per document.** Five 10-page documents are each under
threshold but collectively fifty pages. Try whole-read for the set; if the set exceeds budget, switch the
largest members to index-guided retrieval first.

#### Grouping and iteration (the previously-unspecified part)

**Grouping is deterministic, not judgment.** Given selected index entries with known line counts, pack
them into groups under a token budget — bin-packing, reproducible, auditable. Pack in **document order**,
because adjacent entries are usually one argument (2.1 and 2.2 are a single thread; splitting them across
groups fragments it).

**Iteration semantics are the OPPOSITE of Arm 1's** — this was being conflated, and conflating it would
have produced fragmented sections:

| | Iteration | Why |
|---|---|---|
| **Arm 1, per epic** | **Independent** — must not see each other | Anti-anchoring; inheriting a landing point is a correctness bug (D-A8) |
| **Section authoring, per group** | **Dependent** — group 2 sees group 1's draft | A section is a **synthesis**; disjoint passes cannot produce a coherent problem statement |

So Arm 1 fans out; section authoring stays **sequential, carrying the draft forward**. Same
"resolve broadly / reason narrowly" shape, opposite iteration rule.

**Termination:** every selected group is processed. No early exit, or coverage becomes unverifiable.

#### Guardrail 7 — index completeness

`lines_total == lines_indexed`, with every line falling inside exactly one entry's range. This is what
*guarantees* the density property instead of assuming it. Without the check an index could silently skip
twenty pages and you would be back to sparse coverage with no signal — the exact tag failure mode being
escaped.

#### Degraded case to check against real fixtures

A document with **no substructure** — 40 pages, five headings, flat prose beneath. Boundaries must then be
**synthesised** by paragraph grouping to a target size. It works, but it is the weakest case, and it is
what the real `fixtures/pdf/` documents should be checked against before this is considered proven.

### D-A19 · Code-impact without tags — the module-first tier walk (item 6)

`files[].tags` is **removed** from `code_map.json` (§3.3). Nothing on the code side is tagged. Matching
is **model reasoning over prose**, not a set operation.

#### Why this is not "tags with extra steps"

| | Tags | `purpose` |
|---|---|---|
| Form | closed vocabulary, 12 terms | free prose, unbounded |
| Both sides must agree on | **a shared dictionary** | **nothing** |
| Coverage | sparse — only where applied | dense — every module/file has one |
| Maintenance | authored, frozen, `vocab_sha`, amended | derived per repo, never curated |
| Match mechanism | `∩` set intersection (boolean) | model judgment (**explainable**) |

Row 2 is the crux: tags required *both* arms to emit from the same controlled vocabulary, and **that
shared dictionary is the source of everything being removed** — the F1+3 drift class, §10.1 containment,
§10.5 emit-map, and the whole onboarding chain. With prose on both sides, nothing must agree.

Row 5 is a real gain: `{"routing"} ∩ {"routing"}` explains nothing. A semantic match carries its
reasoning — *"module `iso8583` matched: its purpose describes subelement layout, which is where
subelement 92 is read"* — which becomes the evidence trail in `enrichment.json`, is what the operator
sees at the disposition walkthrough, and makes a wrong match **reviewable** rather than silently wrong.
Cite-or-flag applied to code matching, which a set intersection cannot support.

**But the risk is real:** terse purposes (`"handles routing"`) degrade this *into* tag-like behaviour.
**Rich purpose ≠ tags; terse purpose ≈ tags.** Purpose quality is load-bearing and needs a build-time
check, not an assumption.

#### The query side creates nothing

There is **no tag emission, no keyword extraction, no intermediate artifact** on the requirement side.
The query is **raw text**: `frame + requirement title + description + the assertion`.

A *bare* assertion would fail, and this is why the context is required:

```
bare:  "accepted values are 01–04"
         → vs "Routes a transaction to the correct card-brand handler"  → no match
in context:
  frame:       "Support Visa TL-2027-14 brand indicator in authorization"
  title:       "Authorization message must carry the brand indicator"
  description: "field 48 gains subelement 92 for brand routing on acquirer-initiated auths"
  assertion:   "accepted values are 01–04"
         → matches iso8583 / routing / settlement                        → ✓
```

The **assertion narrows what to verify; the requirement context supplies what to search for.** This
generalises TASK-066 refinement (d).

#### Three tiers (5 000-file / 10-module worked example)

`code_map.json` holds **two** purpose arrays — this is what reconciles "5 000 is too many" with
"compare against purpose":

| Tier | Compared against | Count | Outcome |
|---|---|---|---|
| 1 | `components[].purpose` — **module** tier | **10** | 4 modules match (`api` alone eliminates 2 177 files) |
| 2 | `files[].purpose`, **only where module ∈ matched** | **1 340** | 4 candidate files |
| 3 | actual **source** of those files | **4** | findings + `depends_on`/`used_by` closure |

The module tier is the filter that makes the file tier affordable. Beyond cost, it is the **attention**
argument: a model can weigh 10 purposes carefully; over 5 000 the matching is shallow and unreliable.

**`purpose` seeds; source establishes.** Never conclude from purpose alone.

**Amortisation** (per D-A8's retrieval/reasoning split): the territory — matched modules plus their file
purposes — is resolved **once per deliverable** and stays resident while assertions iterate against it,
not re-derived per assertion. This stays compatible with the anti-anchoring rule because what is shared
is **reference material** (a deterministic artifact), never **conclusions**: fan-out workers each receive
the same resolved territory and none sees a sibling's findings.

#### How modules and purposes are created — separate steps, ordered

> ⚠️ **Revised against the real repo (2026-07-29).** The first draft made *directory path* the primary
> module signal. `Stratus_Repo/source/` is a **single flat directory** — every `.c`/`.h` in one folder —
> so directory partition yields **one module** and tier 1 filters nothing. Directory is demoted to one
> signal among several, contributing **nothing** for this repo. See D-A20.

| Step | What | Who |
|---|---|---|
| 1 | Partition by language | deterministic (TASK-008) |
| 2 | Per-file structure + **assign `module`** (D-A20 signals) | **deterministic** (TASK-009) |
| 3 | `merge_edges` | deterministic (TASK-011) |
| 4 | Set `files[].purpose` — **declared `Intention:` where present**, else model-inferred (D-A20) | deterministic + **model** |
| 5 | Write `components[].purpose`, **abstracting over its file purposes** | **model** (TASK-011) |

**Modules exist before any purpose is written.** The model never chooses a file's module; it only
*describes* modules that already exist. Two reasons this is load-bearing:

- **The binding rule** — the structural extractor is deterministic and frozen; the model owns only
  `purpose`. Model-assigned module boundaries would be the model rewriting structure.
- **Cacheability** — `commit_sha` is the whole-map cache key (§5 gate), which requires the same commit
  to yield the same modules every run. Model-assigned boundaries would break reproducibility.

**Order within the model pass matters:** file purposes first, then module purpose synthesised *from
them*. That is what makes "abstract, don't copy" enforceable — coverage of the member file purposes is
checkable. Written independently, it could not be verified.

#### `components[]` carries an explicit `members[]` list

`files[].module` alone is functionally sufficient for tier 2 (filter `files[] where module == matched`)
but forces loading **all** file entries to find a few. `components[]` therefore carries an explicit
`members: [path, …]`, so tier 1 reads only the small `components` array (~10² entries), obtains member
paths, and tier 2 looks up **only those** file entries. The redundancy with `files[].module` is safe —
both are generated together — and a build check asserts they agree.

*Scale option, not taken now:* split the map into a small `components` file and a large `files` file
loaded selectively. That is a §3.3 contract change; only do it if the single map proves too large to hold.

#### Cluster-quality disagreement — detect and report, never auto-pivot

Graph cohesion and semantic coherence are independent signals, so they can disagree: if the graph groups
40 files but their purposes are heterogeneous, the synthesised module purpose comes out vague. **That is
evidence the clustering was wrong, not merely that the text is poor** — two signals agreeing is
confidence, disagreeing is a flag.

**Auto-pivoting the clustering method on that signal is forbidden**: it would break determinism (the map
must be reproducible from `commit_sha`; a method that varies by model judgment is not) and breach the
binding rule (a model judgment driving structure).

| When | Behaviour |
|---|---|
| **Onboarding** (human-gated) | Low-coherence clusters surface in the profile review; the human adjusts the signal profile — clustering parameters or a manual override. **Method changes here, with a person.** |
| **Runtime** (per-commit rebuild) | Profile is frozen; nothing pivots. The module carries `purpose_confidence: low`. |

**Low confidence makes tier 1 *more* inclusive, not less.** If the synthesised purpose cannot be trusted
to describe the cluster, it cannot be trusted to *rule the cluster out* either — and the asymmetry
matters: a false positive costs tier 2 some work, a false negative is missed impact. **Confidence
modulates selectivity, never method.**

A module that repeatedly contains impacts tier 1 failed to predict is evidence to revisit the profile at
the next onboarding review — human-triggered, never an automatic mid-flight switch.

#### Purpose resolution vs module purpose synthesis

| | **Purpose resolution** (stages A/B/C) | **Module purpose synthesis** |
|---|---|---|
| Produces | one purpose per **file** | one purpose per **module** |
| Reads | the file — its header (A/B) or its code (C) | only the **already-resolved file purposes** |
| Count (Stratus) | 6 165 | ~10² |
| Cost | the expensive part — stage C reads source | cheap; short strings, never source |

Synthesis **never re-reads code**. Hence the fixed ordering: **resolution completes before synthesis** —
one cannot abstract over purposes that do not yet exist.

#### Totality, singletons, and the `unclustered` bucket

**Every file must belong to exactly one module.** A file in no module is invisible to tier 1 and can
never be found by any assertion — silent invisibility, the failure mode this whole design exists to
avoid. Singleton modules are therefore legitimate; a singleton's purpose needs no synthesis, it *is* the
file's purpose.

**Confidence tracks purpose quality, not grouping method** — these are different cases:

| Case | Module | Confidence | Tier 1 |
|---|---|---|---|
| Placed alone but **has a specific purpose** | its own singleton | **normal** | evaluated on merit — **can be excluded** |
| **No grouping signal AND no usable purpose** | `unclustered` bucket | **none** | **always** passed to tier 2 |

So a standalone file with a specific stage-B purpose is a normal singleton module, *not* a free pass to
tier 2. The bucket is only for the **doubly unknown** — cannot group, cannot describe — where there is
nothing to match on and therefore nothing that can be safely ruled out.

**Two distinct problems, do not conflate:**

- **Correctness** — can the file be evaluated? Yes if it has a purpose. Singletons are correct.
- **Economy** — 2 000 singleton modules means tier 1 weighs 2 100 entries instead of ~10², and the tier
  stops filtering.

Semantic grouping of singletons (fallback step 3, onboarding-frozen) is an **economy optimisation, not a
correctness fix**. If it fails you pay at tier 1 rather than losing anything — the right failure direction.

**Layered fallback for unplaced files, in order, all deterministic at runtime:**

1. **Include graph** — the connected majority
2. **Prefix family** — weak (903 tokens, cryptic) but non-zero, and only applied to the residue
3. **Semantic grouping of purposes** — model-**proposed** at onboarding, human-approved, **frozen into
   the profile as explicit overrides** (propose-never-bless; frozen output is data, so determinism holds)
4. **`unclustered`** — whatever survives all three

> **Open — needs a follow-up scan.** The survey reports 56.5% of files *use* local includes, but that is
> **not** the isolated count: a header that includes nothing is still connected by everything including
> it (edges run both ways). **The unmeasured number is how many files have degree zero in *both*
> directions** — those are what the include graph cannot place at all, and it decides whether singletons
> are a footnote or a scale problem.

#### The worst case: degree zero **and** no purpose statement

**Stage C-fallback — exported symbol names.** Before declaring defeat there is a signal the extractor
already produces: `interfaces` (§3.3), extracted deterministically. A file with no header, no includes and
no declared purpose but exporting `se_lookup(se_num)` · `se_validate(se_num)` · `se_format(buf, se_num)`
is evidently service-establishment number handling. Free, deterministic, and genuinely informative.

| Rung | Source | Cost |
|---|---|---|
| A | declared label (`PURPOSE:`, `Intention:`, …) | free |
| B | unlabeled header prose | cheap |
| C | whole-file read | expensive |
| **C-fallback** | **exported symbol names** | **free, deterministic** |
| — | nothing left → **unanalyzable** | — |

Symbol names should feed *into* stage C as input regardless (they improve a whole-file read), but they
also stand alone when C is skipped or fails.

**Genuine residue after all rungs:** empty/stub files, pure data files (generated tables, constants),
unreadable files (encoding/binary), and files where the human **declined stage C on cost** at the gate.

**Declare the residue; never hide it.** Two wrong handlings:

- **always pass to tier 3** — reading source for *every* assertion, at ruinous cost, to match against nothing
- **silently exclude** — the invisibility failure mode this design exists to prevent

Correct: surface it **once, at map build**, not per assertion —

```json
"coverage_report": {
  "files_seen": 6165,
  "files_unanalyzable": 34,
  "unanalyzable": [
    { "path": "source/tbl_bin_ranges.c", "reason": "data table, no symbols" },
    { "path": "source/stub_reserved.c",  "reason": "empty stub" }
  ]
}
```

This extends a pattern **§3.3 already has** — `files_unresolved` / `unresolved_patterns` from TASK-009's
extractor blindspots — from structural extraction to purpose resolution.

It then surfaces to the operator in **§18 Verification summary**: *"34 files could not be analyzed;
impact findings do not cover them."* **Cite-or-flag applied to the map itself** — declare the boundary of
what was examined rather than implying complete coverage. It is also actionable: generated tables are
fine, but a 2 000-line file that merely lost its header is a one-time repo-hygiene fix.

#### Multi-language repos

The existing machinery does the hard part: TASK-008 detects languages and partitions, each partition
dispatches to its own frozen extractor, outputs normalise to the §3.3 shape. Unchanged.

What this design adds:

- **One profile per repo, with per-language *sections*** — not separate profiles. The repo is the
  onboarding unit: one gate, one freeze, one `profile_sha`. Each language section carries its own label
  aliases (C `/* PURPOSE: */`, javadoc, docstrings), comment syntax, and hub threshold.
- **Modules are language-scoped**, and that is fine. Include graphs are intrinsically per-language
  (`#include` vs `import`, no shared namespace), so clustering partitions by language naturally. Tier 1
  compares an assertion against **all** module purposes regardless of language, so a requirement touching
  both a C backend and a Java service matches modules in each independently. No cross-language module is
  needed.
- **Closure stops at the language boundary.** Tier 3b walks `depends_on`/`used_by`, and there are no
  edges between a C module and a Java one — JNI, REST hops, shared queues are invisible to both graphs.
  **This is structurally the identical problem to cross-repo closure**: same shape, same fix — the
  reserved `external_calls`/`exposes` fields (§3.3) that TASK-068 was already going to populate.
  Cross-language and cross-repo are **one deferred capability wearing two hats**; building it once covers
  both.
- **Unonboarded languages** degrade into the totality path above: TASK-010's model fallback gives coarse
  structure, no reliable include graph, so those files land in `unclustered` — found at tier 2, just less
  efficiently.

> **Validation requirement (V, carry into Phase D):** multi-language handling must be **thoroughly
> tested**, not assumed. A multi-language fixture repo exercising per-language profile sections,
> language-scoped clustering, cross-language tier-1 matching, and the closure boundary is a required
> acceptance artifact — not a later enhancement.

#### Two purpose-quality requirements (tier 1 depends on both)

- **Module purpose must abstract over its files, not copy one.** §3.3's own example has module and file
  purpose as *identical strings* — harmless in a one-file fixture, fatal at scale: if module purpose is
  one member's purpose, the tier filters nothing.
- **Purpose must be specific enough to discriminate.** `"handles routing"` matches every routing-adjacent
  query and is useless. `"Selects the brand handler from PAN range and applies per-brand fee rules"` is
  matchable.

#### Degraded case — symmetric with the doc arm

A flat `src/` holding 5 000 files yields **one module**, and tier 1 filters nothing. The fallback must
stay **deterministic** — cluster on the `depends_on`/`used_by` graph, or on path-prefix patterns —
because model-proposed boundaries would breach "the model owns only `purpose`."

**Both arms share this failure mode:** flat prose PDF (doc side, D-A18) and flat directory tree (code
side). Both need synthesised grouping; both are what the real fixtures must be checked against.

### D-A20 · Module derivation and `purpose` provenance — measured against the real Stratus repo

Two screenshots of `Stratus_Repo/source/` (2026-07-29) invalidated two assumptions in D-A19's first
draft. Both corrections make the design **more** deterministic, not less.

#### Finding 1 — the repo is flat; directory is not a usable signal

`Stratus_Repo/source/` holds every `.c` and `.h` in **one folder**: `amex_8583.h`,
`amex_industry_map_io.c`, `AmexCryptoFncts.c`, `amx_line_tcp.c`, `AP_ISO_message.c`,
`AP_ISO_message_v2.c`, `ap_io.c`, `ap_dc_server.c`, `ap_srch.c`, `ap_clean_m.c`, `ansi.h`,
`AOAInquiryService.h`, … Directory partition yields **one module**; tier 1 filters nothing.

**Module grouping signals, all deterministic — priority order REVISED by the full survey
(6 165 files, 2026-07-29; `Stratus_Repo/HEADER_SURVEY.md`). The first draft's ordering was close to
inverted:**

| Signal | Draft rank | **Survey verdict** | Measured |
|---|---|---|---|
| **Include / dependency-graph cohesion** | 3rd | **PRIMARY** | 56.5% of files use local includes, avg **9.1** each, **95.1% resolve to a repo file** → graph is derivable and is the strongest deterministic signal |
| **Declared-purpose semantic similarity** | 4th | **strong second** | 96.7% specific where present (finding 2) |
| **Prefix families** — split on `_`/camelCase | **1st** | **weak — tie-break only** | 903 tokens; largest `s` (390), `md` (323), `sb` (142), `pti` (124); **24% singletons**; tokens cryptic. `s`/`md`/`or` are naming noise, not modules |
| **`.c` / `.h` pairing** | 2nd | **unreliable** | **1 157** `.c` files have their `.h` in the *other* directory |
| **Directory path** | 5th | nothing | as expected — flat tree |

So the **include graph carries module grouping**, with declared purpose as the semantic refinement and
prefixes only breaking ties. Grouping must stay deterministic (binding rule + `commit_sha` cache key);
the *label* is cosmetic and may be derived from prefix or purpose.

*(Only **one** purely-numeric filename repo-wide — `722.c`. That worried the draft more than warranted.)*

Worked result — 8 modules from ~30 flat files: `iso_message` · `amex_mapping` · `amex_crypto` ·
`amex_line` · `ap_io` · `ap_server` · `ap_search` · `ap_maintenance`.

#### Finding 2 — most files declare their own purpose, under many different labels

> **Survey result (6 165 files):** purpose-field coverage **58.0%** (3 576) · of those, **96.7% specific**
> (3 457 specific / 119 generic) · leading-comment coverage **96.1%**.
>
> **Net: tier 1 is viable as a HYBRID** — declared purpose where present (high quality), include-graph
> fallback for the 42% without one. **Not "purpose alone."**
>
> The **96.7% specificity is the decisive number**: the terse-purpose failure mode D-A19 warns about is
> essentially **absent** (3.3%). Where a purpose exists, it discriminates.

**The label varies widely — assuming one keyword would have been a 5.7× under-report:**

| Label | Files |
|---|---|
| `PURPOSE` | 2 403 |
| `Intention` | 623 |
| `DESCRIPTION` / `Description` | 363 |
| `Purpose` | 324 |
| `SYNOPSIS` | 126 |
| `Descr` / `Desc` | 23 |
| typos — `Putpose` ×4, `MODFICATION HISTORY` | — |

**`Intention:` is only 623 of 3 576 (17%).** Counting it alone — the two-screenshot assumption — would
have reported ~10% coverage instead of the real 58%, and D-A19 would have been rewritten around the
include graph alone on false evidence. Two mechanical consequences: label matching must be **fuzzy**
(the typos are real), and the extractor needs a **label alias set**, not a single field name. Parser
noise to ignore: `http` (8, from URLs), `conditions are met` (6, license boilerplate).

Files carry a structured header; the original observed form was `Intention:`: 

```c
/* amex_se_map_io.c  v001  210714  mtm  */
/*********************************************
 Name:        amex_se_map_io.c
 Intention:   routines to lookup the amex se number
 MODIFICATION HISTORY:
     v001  210714  mtm  initial version
*/
```

**This is better than a model-written `purpose`** on three counts: it is a **deterministic extraction**
(leading comment block + field regex, no model); it is **human-authored ground truth** — what the
developer *said* the file does, rather than the model's reading — and therefore **citable** to a line
rather than to an inference; and it **shrinks the model's role**, which the binding rules prefer.

```json
{ "path": "source/amex_se_map_io.c", "module": "amex_mapping",
  "purpose": "routines to lookup the amex se number",
  "purpose_source": "declared",
  "declared_version": "v001", "declared_date": "2021-07-14" }
```

**Two caveats, resolving into a feature:**

- **Coverage is "mostly", not all** (V). Files without headers fall back to model-inferred purpose, and
  `purpose_source: declared | inferred` records which — a provenance distinction that matters, since a
  declared intention is citable and an inferred one is the model's reading.
- **Staleness.** `v001 210714` is 2021; four years of change may have moved a file past its stated
  intention. So declared intention is **high-provenance but possibly stale**, while a model reading is
  **current but inferential**.

**Resolution — use both: the model verdicts the declared intention against the actual code.** Same
mechanic as Arm 2, third appearance.

```json
{ "path": "source/ap_io.c",
  "purpose": "record-level I/O for authorization processing",
  "purpose_source": "declared", "purpose_verdict": "diverged",
  "purpose_actual": "record I/O, plus brand-rule table caching added since v001" }
```

**A divergence is a finding, not noise** — and operationally critical: if `ap_io.c` declares "record I/O"
but now also caches brand rules, an assertion about brand rules would **miss it entirely** were matching
based on the declared intention alone.

Net effect: the **code arm now has better provenance than the doc arm** — declared intentions verified
against source, versus model-written summaries on the doc side.

#### Finding 3 — versioned duplicates are an impact hazard, but a bounded one

`AP_ISO_message.c` **and** `AP_ISO_message_v2.c` both exist. If an assertion lands on message parsing,
does it change v1, v2, or both? Getting it wrong means shipping to the dead path. Versioned file pairs
must be surfaced as a **first-class finding requiring disposition** (D-A16), never silently resolved by
the agent.

> **Survey result:** **38** suffix files (`_v2`, `_v6`, `_test`, `_old`) and **no silent duplicate
> stems**. So the hazard is real but **small and fully enumerable** — the 38 can be listed up front
> rather than discovered per run.

#### Two questions the survey did not answer — worth a short follow-up before Phase B

1. **Is the missing 42% uniformly spread, or clustered?** Tier 1 needs good *module* purposes, and those
   are synthesised from member file purposes. A module where 6 of 10 files declare a purpose synthesises
   fine. But if the gap is **concentrated** — an entire subsystem with zero declared purposes — those
   modules get weak purposes and tier 1 fails *specifically there* while the 58% aggregate looks healthy.
2. **The 96.1% / 58.0% gap is a recoverable population.** ~2 300 files have a header block but **no
   purpose-labelled field**. Some of that is very likely usable purpose prose sitting under no label at
   all. Recovering even part of it pushes effective coverage well above 58%.

#### Also recorded

- **Generic purposes must be flagged, not trusted.** Only 119 (3.3%), but they should carry
  `purpose_quality: generic` so tier 1 does not weight them.
- **`.h` placement:** 1 781 in `include/` vs 1 767 in `source/` — a **file-type** convention, not a
  functional one, confirming the split carries no module signal.
- **Available, not built on:** `MODIFICATION HISTORY` is structured, so per-file change history is
  deterministically extractable. Recently-churned files being higher-risk is a plausible ranking input —
  noted, out of scope.

### D-A21 · The onboarding gate report + the consolidated code-map process

#### The gate report (V-requested)

The onboarding gate must show a **stage-distribution breakdown of how the repo was handled**, including
the count for which nothing is derivable. Rationale: the gate is the **only** human checkpoint on map
quality, and without this the operator cannot see *what quality of map they are approving*. A map that is
85% human-authored purposes is a fundamentally better analysis substrate than one that is 60%
model-inferred — and D-A20's "one-time scan bakes in a quality ceiling" risk is only visible here.

```
═══ CODE MAP ONBOARDING — Stratus_Repo @ 9f3c1ab ══════════════════

SIGNAL PROFILE (proposed)
  module derivation   include_graph_cohesion (primary)
  purpose labels      PURPOSE · Purpose · Intention · DESCRIPTION · … (8 aliases, fuzzy)
  hub threshold       fan-in > 200  →  shared_interfaces
  prefix families     tiebreak only
  directory signal    unusable (flat tree)

PURPOSE RESOLUTION — projected distribution
  A   declared label      3,576   58.0%  ████████████░░░░░░░░  human-authored
  B   header prose        1,670   27.1%  █████░░░░░░░░░░░░░░░  human-authored   ← sampled 71/100
  C   whole-file read       890   14.4%  ███░░░░░░░░░░░░░░░░░  MODEL-INFERRED
  C*  symbol names           21    0.3%  ░░░░░░░░░░░░░░░░░░░░  deterministic
  ──  unanalyzable            8    0.1%  ░░░░░░░░░░░░░░░░░░░░  NO COVERAGE
                          ─────
                          6,165
      human-authored 85.4%  ·  model-inferred 14.4%  ·  uncovered 0.1%

MODULE DERIVATION
  clustered by graph     5,102   82.8%   →  104 modules
  singleton (w/ purpose)   892   14.5%   →  892 singleton modules
  unclustered bucket       163    2.6%   →  1 bucket, always passed to tier 2
  hubs                       8    0.1%   →  shared_interfaces
  tier-1 entries: 997   ⚠  above target (~200) — singleton grouping recommended

COVERAGE GAPS
  unanalyzable                8   listed — impact findings will not cover these
  versioned duplicates       38   require disposition (D-A16)
  low-confidence modules      6   tier 1 will widen rather than exclude

ESTIMATED COST   stage C ≈ 890 whole-file reads

[ approve ]  [ adjust profile ]  [ skip stage C ]  [ group singletons ]
```

Three things a plain approval cannot do: distinguish **human-authored from model-inferred** (the quality
ceiling); surface **tier-1 entry count against target** (the economy problem, while still fixable); and
state the **uncovered set explicitly** rather than implying completeness.

#### The gate actions

All three are **pre-freeze only** — after approval the profile is frozen data and none exist at runtime.
That is the determinism guarantee. They compose freely.

**`adjust profile`** — edit signal-profile parameters, then re-review. Cheap to iterate, because
clustering is deterministic graph arithmetic: adjust → recompute → updated distribution → adjust again.
Only the freeze is one-way.

| Parameter | Why change it |
|---|---|
| hub threshold | scan proposes fan-in > 200 but 40 of those are genuinely modular, not shared surfaces |
| cluster size policy | min-merge / max-split bounds — a tail of 2-file clusters, or one 800-file giant |
| purpose label aliases | add a convention the scan missed (`Function:`, a team-specific label) |
| derivation priority | if the graph is weak in *this* repo, promote another signal ahead of it |
| confidence thresholds | what counts as low enough to widen tier 1 |

**`skip stage C`** — decline the expensive whole-file model pass. Those files do **not** vanish: they
fall through to **C\* (symbol names)**, and only what C\* cannot cover becomes unanalyzable.

*When it is right:* cost is real and the population is low-value (test harnesses, generated code); or a
**fast first map** is wanted to validate the pipeline before paying for the full build.
*What it costs:* those files get weaker or no purposes, so tiers 1–2 cannot match them — reachable only
via tier-3b closure, and only if structurally connected. A visible coverage reduction, not a hidden one.
**Reversible** — purposes are cached per file content hash, so running C later fills the gaps
incrementally. Skipping at onboarding is a **deferral, not a permanent exclusion**.

**`group singletons`** — triggers fallback step 3 on the singleton population. The model reads their
purposes (short strings, cheap) and **proposes** groupings by semantic similarity; the human reviews the
proposal **as a diff** — which files move into which group — approving or rejecting per group. Approved
groupings freeze into the profile as explicit membership overrides.

*Effect (worked example):* **997 tier-1 entries → ~250** — the economy problem solved at the only point
it is cheap to solve. *Risk:* a bad grouping yields a module with a vague synthesised purpose — the
cluster-quality problem by another route, which is why it is reviewed as a diff rather than auto-applied,
and why the coherence check still runs on the result.

#### The consolidated process

**PHASE 1 — Onboarding · once per repo · human-gated**

1. Clone repo, pin `commit_sha`
2. **Profile scan** — automated survey: purpose-label variants + coverage · include density and
   resolution rate · prefix-token quality · `.h` placement · versioned duplicates · **graph isolation
   (degree zero both directions)** · **symbol presence**
3. **Stage B sample** — run B on ~100 random files, measure recovery rate
4. **Project** the stage distribution and stage C cost from the sample
5. **⛔ GATE** — human reviews the report above; may adjust thresholds, trigger a **secondary recluster**
   on low-coherence clusters (model proposes → human approves), skip stage C, or request singleton grouping
6. **Freeze** `signal_profile` → `profile_sha`; approved model proposals are baked in as **data**

**PHASE 2 — Map build · per commit · cached per file hash**

7. Partition by language *(TASK-008)*
8. Structural extraction per language — parse, `interfaces`, `depends_on`/`used_by` *(deterministic;
   TASK-009, model fallback TASK-010 marked `coarse`)*
9. **Hub exclusion** — fan-in > threshold → `shared_interfaces`, removed from cluster glue *(deterministic)*
10. **Module clustering** — graph cohesion → prefix family → frozen semantic overrides → `unclustered`
    *(deterministic)*
11. **Purpose resolution** per file — A declared → B header prose → C whole-file → C\* symbols → unanalyzable
12. **Module purpose synthesis** — model abstracts over member purposes *(never re-reads source)*
13. **Confidence scoring** — purpose quality + member coverage + semantic coherence
14. **Coverage report** — stage distribution · unanalyzable list · duplicates · low-confidence modules
15. Write `code_map/components.json` + `code_map/files.json`

> **Recomputed every build:** structure, clustering, hub exclusion *(cheap, deterministic)*
> **Cached per file content hash:** purposes *(expensive, model)*
> **Re-synthesised only for affected modules:** module purposes

#### Build frequency — a FOURTH gate branch

The map is **not** rebuilt per run. TASK-013's 3-branch gate gains a branch, because the signal profile
did not exist when it was written:

| Branch | Condition | Work |
|---|---|---|
| **1 · Onboard** | no profile for this repo | profile scan → gate → freeze → **full build** |
| **2 · Reuse** | `commit_sha` **and** `profile_sha` both match cache | **nothing** — cached map used as-is |
| **3 · Incremental** | `commit_sha` moved, profile unchanged | structure + clustering recomputed (cheap); model purposes **only for changed files** |
| **4 · Full rebuild** | **`profile_sha` changed** | **everything** — the derivation rules themselves changed |

**Branch 4 is the new one.** If re-onboarding moves the hub threshold from 500 to 200, *every* module
boundary can shift, so nothing in the old map is trustworthy. **Profile change invalidates wholesale;
commit change invalidates selectively.**

Cache keys: **`(commit_sha, profile_sha)`** for map validity · **file content hash** for individual purposes.

**Wrinkle:** clustering is global, so a changed file's new includes can shift module membership *beyond*
that file. "Affected modules" is therefore wider than "modules containing changed files" — bounded, but
not purely local.

Practical consequence: onboarding runs once; most subsequent runs hit **branch 2** (no work) or **branch
3** with a handful of changed files. The whole-file stage-C reads are a **one-time cost, not per-run** —
which is what justifies paying for the staged A/B/C investment at all.

**PHASE 3 — Per-assertion impact · run time · reads the map, never writes it**

16. **Tier 1** — assertion (frame + title + description + assertion) vs **module** purposes → matched
    modules *(low confidence **widens**, never excludes)*
17. **Tier 2** — vs **file** purposes within matched modules only → selected files
18. **Tier 3a** — read selected files' **source** → confirm/refute landing points, verdict implicit assumptions
19. **Tier 3b** — walk `depends_on`/`used_by` outward from confirmed landings → **ripple**, reaching files
    no tier selected
20. → §16 entries → `enrichment.json`

**The map is requirement-blind.** Phases 1–2 never see a requirement; "in scope" is computed per
assertion in phase 3 and recorded in `enrichment.json`, never in the map. Same rule as the doc index
(D-A18): *the index describes the artifact, never the destination.*

### D-A22 · Manifests (item 7) — a split, not a deletion

Reading the three files showed they perform **six** distinct jobs. The instinct to remove them was aimed
at the parts that genuinely die, but those were tangled with parts that do not.

#### `onboarding_manifest.yaml` held three unrelated concepts

| Contents | Fate |
|---|---|
| `extractors[]` — per-**language** freeze (path, `extractor_sha`, tools, globs, coverage floor) | **survives** → `extractor_manifest.yaml` |
| `adequacy_threshold` + `vocab_sha` | **dies** — pure tag-chain artifacts |
| `repos[]` — per-**repo** build records (`content_hash`, `built_with_extractor_sha`, `last_built`) | **survives, wrong location** → the cache |

**`repos[]` exposed a design smell:** it is **mutable build state inside a frozen, SHA-pinned registry
artifact**. Every map build wants to update `last_built`/`content_hash`, dirtying the registry that
§6.6.1 requires to stay frozen. It is also exactly where the 4-branch gate reads its cache key and where
`profile_sha` belongs — real and needed, but as cache, not registry config.

**Why `adequacy_threshold` dies specifically:** it measures `untagged_ratio` — the fraction of entities no
vocabulary term covered. With no tagging step nothing can be untagged; the ratio has **no denominator**.
The *concern* survives and is answered better: the D-A21 gate distribution (human-authored vs
model-inferred vs uncovered) plus per-module `purpose_confidence` replace one binary flag with graded
quality carrying provenance. **Direct heir:** a profile-level `warn_if_human_authored_below` threshold.

#### `registry_manifest.yaml` — keep it, shrink it

It has a job nothing else does: telling `hydrate.py` what to copy into a run workspace. Hardcoding those
paths in Python would be worse. But its **17 hand-listed doc files** are a maintenance trap — add an ADR,
forget the manifest, and it silently never reaches a run. That nearly bit already: ADR-006/007 are named
there but were untracked in git.

```yaml
include:
  trees: [core/, overlays/, docs/]
exclude: ["**/__pycache__/**", "**/*.pyc", "**/.git/**", "**/.DS_Store"]
```

Same file, same job, 54 lines → 4.

#### `overlay_manifest.yaml` — survives, contents rewritten

Real work: single source of truth for the runtime-tool seam, and §10.2 parity checks against it. Both
tools stay (D-A0). ADR-008 rewrites its **contents**: `brd_*` → `solution_intent_*`, `frd_*` **retire**,
enrichment + disposition-walkthrough roles added, `prompt_files` re-pointed.

#### End state — five artifacts, three granularities

| File | One per | Function |
|---|---|---|
| `registry_manifest.yaml` | registry | what `hydrate.py` copies into a run, plus excludes |
| `overlay_manifest.yaml` | registry | runtime-tool seam: roles, prompt files, per-tool paths/launch; drives §10.2 |
| `extractor_manifest.yaml` | **language** | frozen extractor per language — one C extractor serves every C repo |
| `code_profiles/<repo>.profile.yaml` | **repo** | how to read *this* repo: labels, signal priority, thresholds, frozen overrides, gate record |
| `cache/code_maps/index.yaml` | repo build | 4-branch gate cache lookup — **mutable, outside the frozen registry** |

The extractor/profile split is what delivers the "dynamic to other codebases" property: a second C repo
**reuses the extractor untouched** and gets its own profile.

**Also dying (not manifests):** `vocabulary.<domain>.yaml` entirely · `adapter.yaml`'s `emits` · the
`topics` layer in the profiles · `frd_profile`.

**Net:** not fewer files — but no hand-maintained enumerations, no mutable state in a frozen artifact, and
every remaining file doing exactly one job.

### D-A23 · Gates, guardrails and roles (item 8)

#### Correction: the guardrails are not all §10 replacements

Earlier notes called the accumulated guardrails "replacements for §10.1/§10.5". That was wrong — they
check **different artifacts at different times**, so they belong to three families. **§10 shrinks 5 → 4;
it does not grow to 12.**

#### Family 1 · Build checks (§10) — *is the registry internally consistent?*

Developer-facing · `build_checks.py` · gates registry publish.

| Check | Fate |
|---|---|
| §10.1 vocabulary containment | **dies** — no vocabulary |
| §10.2 overlay parity | survives — amended role list (below) |
| §10.3 domain artifacts | survives — no vocabulary; SI profile replaces brd/frd; `jira_template` added |
| §10.4 connector coverage | survives unchanged |
| §10.5 adapter emit no-drift | **dies** — no `emits` |
| **§10.5′ disposition-class totality** *(new)* | every SI section has ≥1 input class routed to it; every class the UI offers appears in the D-A13 matrix |

Only **one** new check lands in §10 — it is the only one testing *registry config*. Every other guardrail
needs a produced artifact and therefore cannot run at build time at all.

#### Family 2 · Context checks — *are the ingested artifacts complete?*

Run at ingest · feed the coverage reports · surface at the onboarding gate and §18.

| Check | Guards against |
|---|---|
| **Module totality** | a file in no module is invisible to tier 1 **forever** |
| **Purpose totality** | every file has a purpose **or** appears in `unanalyzable[]` — never silently absent |
| **`members[]` consistency** | `components[].members` must agree with `files[].module` |
| **Index completeness** | `lines_total == lines_indexed`, every line in exactly one entry — what makes *"not in the index"* a defensible negative |

#### Family 3 · Artifact checks — *is the produced work well-formed?*

Run by the validators · enforced at gates.

| Check | Gate |
|---|---|
| §15→§4 — every criterion traces to an objective; every objective measurable | G1 |
| §7→§8 — every requirement traces to a deliverable | G1 *(load-bearing: builds the Jira hierarchy)* |
| Every §8 **assertion** has a verdict | G2 |
| Every §16 entry yields ≥1 story; every story traces to §16 or §7 | G3 |
| Every story names a code location, or is flagged new-build / non-code | G3 |

#### The scoring formulas break — `topic_coverage` is a tag construct

G1 scores `0.7 × topic_coverage + 0.3 × citation_integrity`. **`topic_coverage` counts satisfied profile
topics**, and topics die with the vocabulary — the formula loses its denominator, exactly like
`adequacy_threshold` (D-A22). Successors:

```
G1   0.7 × section_coverage + 0.3 × citation_integrity
        ↑ must_capture items satisfied per section — survives tag removal
          intact, because it is a checklist, not a controlled vocabulary

G2   0.5 × verdict_completeness + 0.5 × impact_coverage        ← PROPOSED, new
        ↑ assertions verdicted / total   ↑ requirements with §16 entries / total
     hard preconditions: every escalation dispositioned ·
                         every correction carries code provenance

G3   0.5 × traceability + 0.5 × testability
        ↑ inherited nearly intact from frd_validator
```

**G1's shape barely changes. G2 needs a formula it never had** — it previously scored the FRD and now
gates enrichment, a different thing entirely. The G2 proposal above is the one piece of item 8 that is
genuine design rather than bookkeeping, and it should be validated against a real run before freezing.

**D4 is preserved throughout:** scores inform, never auto-advance. Every gate stays an operator act.

#### The role list (V-confirmed)

| Role | Change |
|---|---|
| `source_processor` | unchanged |
| `solution_intent_author` | ← `brd_author` |
| `solution_intent_validator` | ← `brd_validator` |
| `code_impact` | unchanged — is enrichment **Arm 1** |
| `claim_verifier` | **new** — enrichment **Arm 2** |
| `disposition_walkthrough` | **new** — D-A17 |
| `jira_author` · `jira_validator` | unchanged |
| ~~`frd_author`~~ · ~~`frd_validator`~~ | **retired** (D-A0) |

Still 8 roles. `prompt_files` re-point to `[start-ingest, start-si, start-enrich, start-jira]`.

**Arm 1 and Arm 2 stay separate roles** — not for taxonomy (both are analytical) but for **independent
re-runnability**: D-A8's conditional re-run means an escalation that adds a requirement re-runs Arm 1 for
*that requirement*, while Arm 2's verdicts on untouched sections remain valid. Merged, that good work
would be discarded.

Execution modes, for overlay generation: **interactive** — `solution_intent_author` (discovery questions),
`disposition_walkthrough`. **Analytical (unattended)** — everything else.

---

# ✅ Phase A complete — all 8 items locked

Next: **Phase B — re-cut the ladder.** Mark this ADR Accepted, finalise the supersession list, then amend
`REQUIREMENTS.md` (D1, D3a, D4, D5, D6, D7, D9 + the FR clusters) and `TECH_SPEC.md` (§3.1 disposition ·
§3.2 the doc index · §3.3 the code-map reshape · §5 code impact · §6.6 adapter/profiles · §9 gates ·
§10 checks).

**Outstanding evidence — neither blocks Phase B, both de-risk Phase D:**

1. **Extended code survey** — graph isolation (degree zero both directions), symbol presence, stage-B
   sample rate. The isolation number is the one that could still change the design, since it decides
   whether tier-1 economy holds.
2. **Doc-side survey** — whether the mandates carry the numbered substructure D-A18's index assumes.
   **The last unmeasured assumption in the design.**

Nothing below is decided. Items 3 and 4 carry the risk: item 3 (the routing matrix) **sizes**
item 4, and item 4 (retrieval within a class) is the only step where the honest answer may be
"we need infrastructure we do not have."

Leading candidate for item 4, to be pressure-tested: **structural segmentation + agent
progressive read** — split each document by its own structure (headings, TOC, numbered clauses),
then let the agent navigate that outline and pull what a section needs. Zero new infrastructure
(material on a VDI, where "we need an approved embedding model" is a procurement conversation);
exploits the fact that network mandates and specs are highly structured; the index is *derived*,
not authored, so the entire F1+3 drift class cannot occur; degrades gracefully (poor outline → the
agent reads more), unlike tags, where an under-applied tag makes content silently invisible.
