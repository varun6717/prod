# ADR-008 — Solution Intent pivot (BRD/FRD → Solution Intent, tag removal, disposition routing)

**Status:** 🚧 **DRAFT — Phase A (decide) in progress.** Not yet binding. Becomes binding when
Phase B (ladder re-cut) lands and this ADR is marked Accepted.

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

| # | Item | Status |
|---|---|---|
| 1 | Solution Intent section contract | ✅ **Locked** (below) |
| 2 | Disposition taxonomy | ✅ **Locked** (below) |
| 3 | Routing matrix (section × input source) — *keystone* | ✅ **Locked** (below) |
| 4 | Retrieval within a class — *highest risk* | ⬜ |
| 5 | Enrichment contract (stage 3–4 output schema) | ⬜ (previewed below) |
| 6 | Code-impact without tags | ⬜ |
| 7 | Manifests | ⬜ |
| 8 | Gates + guardrails | ⬜ |

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
3. **One operator turn** — disposition every escalation and scope-moving finding (the existing surface → wait → apply loop)
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

So a gap lands in §16 as **requiring disposition**, and the operator confirms which of the four it is;
only the first becomes a build story. One more item in the single operator turn — and exactly the
judgment that should be human, since on a JPMC-scale codebase "we have never done this" is a claim
only someone with system knowledge can confidently confirm.

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

## Open — Phase A items 4–8

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
