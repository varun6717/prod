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
| 3 | Routing matrix (section × disposition) — *keystone* | ⬜ next |
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

| Gate | Meaning |
|---|---|
| **G0** | Generate — operator inspects the scaffold (unchanged) |
| **G1** | Solution Intent **v1** accepted (code-blind) |
| **G2** | Solution Intent **v2** accepted (enriched) |
| **G3** | Jira push (unchanged; the only external mutation) |

G2 does not disappear with the FRD — it becomes the enrichment gate. `gate.py`, the telemetry
events, the validator pattern and the two-gate operator rhythm are all reused unchanged.

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
| 7 | Business requirements | v1 | **Extend only** |
| 8 | Strategic alignment | v1 | None |
| 9 | Constraints & design principles *(constraints, principles, NFRs)* | v1 | Verdict + Extend |
| 10 | Stakeholders | v1 | None |
| 11 | Out of scope | v1 | Extend (both directions) |
| 12 | Assumptions & risks | v1 | Verdict + Correct |
| 13 | Dependencies | v1 | Verdict + Extend |
| 14 | Success criteria | v1 | None |
| 15 | Derived system impacts | **v2 only** | — |
| 16 | Open questions | v1, extended in v2 | Extend |
| 17 | Verification summary | **v2 only** | — |

§15/§16/§17 sit at the end, after §14, so a v1 document simply stops rather than carrying gaps
mid-body. The persona→use-case matrix stays inside §5.

Sections 3, 4, 8, 10, 14 are **never** touched by enrichment — pure business intent that code
cannot speak to. They also need no code input in the step-3 routing matrix.

### D-A4 · Section rules (binding)

- **§7 Business requirements can only be extended, never corrected.** A requirement is a
  statement of *intent*; code cannot contradict an intent, only reveal that it is incomplete
  (→ escalation) or unachievable (→ that is a risk, §12). Allowing enrichment to rewrite a
  business requirement from code inverts the ladder — the existing implementation would begin
  dictating business intent. This is the worst failure mode available here.
- **v1 must author assumptions in checkable form.** §12 is the section best shaped for the
  verdict mechanism ("we assume settlement is unaffected" verdicts cleanly; "we assume the
  architecture is suitable" does not). The v2 design therefore constrains the v1 authoring
  contract.
- **§1 regenerates, it does not revise.** It is derived from the body; a summary of an
  uncorrected problem statement is silently wrong. Authored last in v1, re-authored in v2.
- **§11 Out of scope is a two-way door.** Escalated derived impacts can land *in* it; code can
  also reveal that something already declared out of scope is structurally coupled and cannot be
  avoided — an escalation *into* scope. Both directions run through the flag loop.
- **§16 Open questions is v1-authored.** v1 already produces unsourced gaps (`[TBD —
  unsourced]`), which today have no home. v1 ships with its own uncertainty visible; enrichment
  adds to the list rather than introducing it.
- **§5's verdict is asymmetric — system actors only.** A persona is a *type* of participant
  defined by goal and context, not a job title (Merchant, Certification analyst, Settlement ops)
  — and nothing in a C code map can confirm a human role exists. What code *can* confirm is the
  **system actor** half: an external interface implies a counterparty system. So Arm 2 verdicts
  actors reachable through interfaces and skips human personas entirely, rather than marking them
  unverifiable. The persona→use-case matrix is a coverage grid against §6 — it catches use cases
  with no participant and personas with nothing to do, and neither check involves code.
- **§17 is a summary, not a ledger.** Counts only (N checked, X confirmed, Y corrected, Z
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
requiring runtime or behavioural data is unverifiable **by construction** — this hits §9's NFRs
and any §14 success criterion carrying a current-state baseline. Arm 2 must *recognise*
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
| Entry | §7 business requirements | §2, §5, §6, §9, §12, §13 |
| Nature | Generative — produces new content | Corrective — produces none |
| Motion | Walks `depends_on`/`used_by` to closure | Point lookup, then stops |
| Produces | §15 derived impacts; escalations → §7/§11 | In-place corrections; markers; §17 counts |

Arm 2 deliberately does **not** walk closure — that is what keeps it cheap per item and what
makes clustering work. If it traversed edges it would blur into Arm 1 and report the same impact
twice from two directions.

Arm 1 runs first — not because Arm 2 depends on it, but because Arm 1's closure pulls code slices
into context that Arm 2's claims often need.

**The same code fact can legitimately produce a finding in both arms.** If v1 §12 assumes
"settlement is unaffected" and closure shows it is impacted: Arm 1 writes a derived impact in
§15, Arm 2 corrects the assumption in §12. One fact, two findings, two destinations — that is the
ideal outcome, not duplication. The false assumption is corrected where a reader meets it; the
real impact is documented where engineering will scope it.

#### Per-claim verification mechanic

Reuses the existing coarse→deep machinery:

**claim → semantic match against the code map → candidate region → selective read of the slice → verdict**

Three coarse-stage outcomes, only one expensive: strong map-level match (verdict from the map, no
source read) · match needing confirmation (deep-read the slice) · **no match anywhere**
(*unverifiable*, cheaply — and often informative, since it usually means the claim concerns a
partner system or upstream dependency, which is itself worth surfacing to §13).

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
4. **Apply** — corrections land in place; §15 written, §16 extended, §17 counted
5. **Regenerate §1** from the corrected body
6. **G2**

Deliberately **one** human turn. Both arms run to completion and accumulate findings in
`enrichment.json` before anything surfaces — otherwise the operator is interrupted mid-pass, and
an escalation that adds a requirement in step 3 would re-trigger Arm 1 in a way that is hard to
bound.

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
| Settlement recon's field-count validation must widen | Technical consequence → §15, done |
| Settlement recon will now reject previously-accepted transactions | Business-visible → **escalate** |

Escalated findings run through the flag loop; the operator's decision lands them in §7 (new
requirement) or §11 (explicitly excluded). The "the network's mandate was incomplete" case is not
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
| **Conditional** | §3 Client need & demand · §6 High-level use case · §8 Strategic alignment |
| **Required, may be empty** | §5 Personas & actors · §13 Dependencies · §16 Open questions |
| **Required** | all others (§15/§17 required in v2) |

Rationale for the conditional three: a regulatory mandate has no client demand (§3); some changes
modify behaviour without introducing a use case (§6); and §8 is the section most likely to attract
ceremonial filler — making it conditional lets *"not applicable, this is a compliance mandate"* be
an honest answer.

G1's absolute precondition becomes: every **required** section satisfied, and every **conditional**
section either filled or explicitly dispositioned N/A with a reason.

### D-A11 · Section boundary statements (§4 / §8 / §14)

Business objectives, Strategic alignment and Success criteria all answer some form of *"why, and
what does good look like."* They are distinct in principle — **intent · portfolio fit · measurable
outcome** — but blur badly in practice, and overlapping sections make `must_capture` authoring
(item 3) ambiguous: a fact that could satisfy two sections satisfies neither cleanly.

Fix is authoring discipline, enforced by a one-line boundary per section:

- **§4** — what we intend to achieve. **No dates, no metrics.**
- **§8** — why this matters to the portfolio *above* this project. **Must reference something
  external to the project** — a program, strategy, or roadmap commitment.
- **§14** — how we will measure §4. **Must be measurable, and every criterion traces to an
  objective.**

Worked contrast (Mastercard mandate):

| | Written well | Written badly |
|---|---|---|
| §4 | "Maintain Mastercard network compliance and avoid decertification" | "Achieve compliance by Q3 2027" *(a success criterion in disguise)* |
| §8 | "Supports the Merchant Services 2027 single-platform brand-parity program" | "Compliance is critical to the business" *(§4 restated)* |
| §14 | "100% of Mastercard transactions carry the new indicator by 2027-07-01; zero certification defects" | "Remain compliant" *(an objective, not a measure)* |

**§14's boundary doubles as a mechanical guardrail** — an objective with no success criterion is
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
article mandate ("support the new indicator by Q3 2027 or face decertification") feeds §2, §4, §7,
§14. A tech letter ("field 48 subelement 92 carries a 2-byte indicator, values 01–04") feeds §9 and
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

## Open — Phase A items 2–8

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
