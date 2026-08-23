# VDI_TASK_V2.md — enhancement task list for the VDI build

**What this is.** Design changes agreed in review, written as executable task specs for the Copilot
on the JPMC VDI. Authored outside the VDI, carried across, and executed there.

**Frame of reference.** Every path in this file refers to the **VDI build repo** (`PDLC_App_v3`,
branch `main`) as recorded in [`vdi_tree.md`](./vdi_tree.md), with behaviour as described in
[`vdi_design.md`](./vdi_design.md). No task here refers to the external Claude Code build.

**Relationship to the VDI's existing lists.** `TASK_LIST.md` is the original build sequence and
`VDI_WIRING.md` is environment wiring. This file is neither: it is *new work agreed after the
architecture review*. Where a task changes something those files pin, it says so explicitly and
names the amendment.

**How to execute.** Same protocol the VDI Copilot already follows: verify **Depends on** exists
before starting, open and read every **Reads** section, produce exactly the **Creates / edits**
paths, and treat the task as done only when every **Acceptance** condition is true and the
**Proof** is green. Then tick the checkbox and commit.

---

## This is a catalogue, not a plan

**Everything below is a candidate.** These are improvements identified in review, written up so they
*can* be picked up — in any order, in chunks, over time. **Some will never be implemented, and that
is the intended use.** Nothing here is committed work, and no task assumes another was done unless its
Depends-on says so.

### The menu

Sizes are **rough relative effort**, not estimates: **S** = a day or two · **M** = about a week ·
**L** = several weeks · **XL** = a month or more.

| # | Buys you | Size | Needs first |
|---|---|---|---|
| **001** Run Brief | Catches a wrong disposition, ref or sha *before* the run starts — the cheapest errors to fix, currently unreviewed | M | — |
| **002A** Ingest Report | Makes silent under-delivery visible: partial extracts, fallbacks, weak indexes | M | — |
| **002B** Stage 2 precondition | Stops Stage 2 building on a broken corpus | S | 002A |
| **002C** Vision smoke test | Catches endpoint / model / cert / quota rot before it degrades runs | S | — |
| **003.1** Section consumption map | Tells you what the 18 sections are actually *for*. Analysis only, no code | S | — |
| **003.2** Declare estate + interchange flow | `applications.yaml`, `interfaces.yaml`, `flow.yaml` — including the per-type **floor**. No behaviour change. **Foundation for all of Stage 3** | M | 003.1 |
| **003.3** Declare change types | Types chosen and validated at config time | M | 003.2 |
| **003.4** Type probes + Change Classification | Type-specific questions asked while authoring | M | 003.2 |
| **003.5** Flow orchestrator + estate walk | resolve → impact → cross → release_shape → consolidate; order derived from `provides`/`needs`, crossing derived from `interfaces.yaml` | XL | 003.2, 003.4 |
| **003.6** Every application scanned | Full repo scan per application in scope, not one repo. **Independent of the change-type work** | XL | — |
| **003.7a** Two go/no-go checks | Tells you whether the history KB is viable *at all*. Can kill Wave 4 cheaply | S | — |
| **003.7** Jira↔commit corpus | The corpus, resolved to engines | L | 003.7a passes |
| **003.7b** Engine profiles | Per-engine characterisation of what changes touch it | M | 003.7 |
| **003.8** KB classification | Change type recommended from precedent instead of declared blind | L | 003.7b, 003.2 |
| **003.9** History reconciliation | Catches engines the scan missed *and* engines it over-claimed | M | 003.6, 003.7 |
| **003.9b** Graded reconciliation | Frequency prior + scan strength + cited judgement | M | 003.9, 003.7b |
| **003.10a** Crossing over declared interfaces | Field-level impact crossing MPT / PTI Gen / submission — the coupling that actually exists here | M | 003.2 |
| **003.10b** Interface discovery + drift | Finding the interfaces nobody declared, plus totality and layout drift | L | 003.10a, **003.7** |
| **004** Reconciliation pass | Stops stories being built on findings another arm refuted | M | — |
| **005** Expectation-aware absence | Stops a requirement being silently deleted; catches "update X" where X isn't found | M | — |
| **006** Enrichment Report | Tells the operator how much of v2 to trust, on one page at G2 | S | — |
| **007a** Amend D-A15 | **Do this first.** Two table rows and one retired consequence in ADR-008 + FR-JR-01. Unblocks 007, 008 and 009 — all three are otherwise stalled | S | — |
| **007** Jira hierarchy | The plan authors two issues that already exist and splits one article into N epics | M | **007a** |
| **008** `validation.md` | The post-install validation document. Negative cases need the code, so it is produced at Stage 5 | M | 007 |
| **009** Stage 5 validator + fixtures | Of the two external mutations, only the Jira push is guarded. **31 fixtures exist; zero are Stage 5** | M | 007 |
| **010** Symbol-level code map | §16 line ranges are model-produced while tree-sitter already computes and discards them | S | — |

### Interactions worth knowing when picking

- **001, 002, 003.1, 003.6, 004, 005 and 006 each stand entirely alone.** None needs any other built
  first.
- **001, 002 and 006 are one family** — a report per stage, read at that stage's gate, saying how well
  the stage performed. Build them to look and read alike; three reports that feel like three different
  products is worse than any one of them missing. 006 is the cheapest of the three and grows richer as
  003.5, 004 and 005 land.
- **004 and 005 are cheaper together** — both edit `dispositions.py` and
  `enrichment.schema.json`, so doing them separately pays the schema-change cost twice.
- **003.3 folds into 001** if the Run Brief exists, and works standalone if it does not.
- **003 Wave 2 makes 004 more valuable**, because type passes add producers that can contradict the
  arms.
- **003.6 is the one large item with no prerequisites** — worth knowing, since it is otherwise easy to
  read it as part of the change-type project. It is not.
- **But the dependency runs the other way round:** a type pass may need code 003.6 has not brought
  into scope. If the clearing engine lives outside Stratus, a clearing pass with one repo scanned is
  half-blind. 003.6 does not need the type work; the type work may well need 003.6 to be *useful*.
- **003.2 is the real foundation.** Nothing else in Stage 3 is scoped correctly without the estate and
  flow declarations, because they define what an application *is made of* and what a change type
  actually runs. It is also the cheapest place to discover whether the arms currently search in the
  wrong vocabulary.
- **003.10 split.** The interfaces you already know — MPT, PTI Gen, submission — are declarable today, so
  **003.10a** (crossing over declared interfaces) sits right behind 003.2 and needs no history. Only
  **003.10b** — *finding the interfaces nobody thought to declare* — needs 003.7, because that is what
  history is actually good for. Declaring from memory captures the obvious ones; co-change finds the rest.
- **Build for multi, run as one.** Every large item here is scoped so the *machinery* is generic from day
  one while the *configuration* stays at one application and one change type. The second of each ships as
  a declared stub, so the multi paths execute and are asserted on before the second repo exists (Target
  state §10). A build-order discipline rather than a task — but it changes how 003.2, 003.5 and 003.6 are
  written.
- **Probe-driven sub-passes change the "is it worth it for one type" calculus** (003.4 + 003.5).
  Because probes activate specialised sub-passes *within* a type, the package machinery earns its keep
  even if interchange is the overwhelming majority of your volume — it is buying specialisation, not
  just multi-type support.

### Where to start *(revised 2026-08-23)*

**First — three small items that remove obstacles. Independent of each other, so they parallelise.**

| | Why first |
|---|---|
| **007a** | Hours, docs only. Unblocks 007, 008 **and** 009 in one edit |
| **003.1** | Pure analysis, and it **gates 003.2** — it defines what "base" means, and 003.1a (the §16/§INT-n split) lives inside it. 003.2 writes `sections:` entries that 003.1a governs |
| **010** | S, no dependencies. Makes §16 locations **derived rather than model-asserted**, and §16 locations flow into stories, `code_author`, the analogy search and the validator — so everything built afterwards inherits real line numbers |

**Then the foundation — 003.2.** The estate, the interchange flow, the eight schema rejections and
`verify_estate.py`. Everything in Stage 3 resolves ids against it. It is the highest-value single item
in the catalogue and is fourth only because 003.1 gates it.

**Then the machine — 003.5.** `flow_plan.py`, the orchestrator, the estate walk. The largest item, and
what makes `flow.yaml` actually run.

**After that, order matters much less:** 007 → 009 → 008, with two worth slotting in whenever there is
room. **005**, because a requirement silently corrected out of existence is the worst failure in this
catalogue — it fails in the direction of doing *less* than the mandate asked, and nothing downstream
notices. And **002C**, because it is an afternoon and catches an entire class of failure that arrives
from outside your repository.

> **Do not start in Wave 4.** 003.7, 003.7b, 003.8 and 003.9 are all gated on 003.7a's two cheap
> go/no-go checks, and everything through Wave 3 stands and delivers without any of it. The historical
> KB is an **upgrade, not a foundation** — it turns declaration from an instruction into a hypothesis
> the system tests.

---

## Review log

| Stage reviewed | Date | Outcome |
|---|---|---|
| Stage 0 — config / Generate / G0 | 2026-08-14 | TASK-V2-001 raised |
| Stage 1 — ingest | 2026-08-14 | TASK-V2-002 raised (proposed); two findings still parked |
| Stage 2 — Solution Intent v1 | 2026-08-15 | TASK-V2-003 raised (target-state framework); two findings parked |
| Stage 3 — enrichment | 2026-08-16 | topics 1–5 closed → TASK-V2-004, 005, 006 |
| Stage 3 — structure | 2026-08-17 | **Target state rewritten** — estate/flow model; 003 sub-tasks need re-scoping |
| Stage 3 — estate & flow | 2026-08-17 | **§2/§3 rewritten again** — code-first estate, the floor, two search obligations, the estate walk, `provides`/`needs` as a contract; 003.10 split |
| KB — the diffs | 2026-08-23 | **003.7c** — the corpus holds actual diffs and nothing used them. Split: **which files changed** is a scope fact (unions into enrichment, reaches Stage 5 through §16); **how they changed** is a shape example (cited Stage-5 drafting grounding, never absorbed). Makes Part G.2's prospective gap locations *evidenced* rather than inferred. **003.9c** raises file-level reconciliation as a candidate, gated on measured noise |
| Code map — symbols | 2026-08-23 | **TASK-V2-010 raised.** §16 line ranges are model-produced while tree-sitter already computes and discards them. Add `symbols[{name,start,end}]` per file entry, additive; `coverage` becomes `"symbol"`. **Governing rule: symbols locate, they never bound what is read — the scan pulls the whole file.** Purpose-per-function and call graphs deferred |
| Stage 5 — the third kind | 2026-08-22 | **§16 gains `kind: verify`** (005 Part G.3c) — the reasoned non-change, carrying a `confirm:` condition the way a gap carries `basis:`. Makes the run's own assumptions trackable as Jira stories instead of invisible. Every kind now maps to a story action: impact/gap → EDIT, verify → VERIFY. 003.9 still counts only `impact`; `code_validator` blocks a hunk on a verify |
| Stage 5 — validator + fixtures | 2026-08-22 | **TASK-V2-009 raised.** Of the system's two external mutations, only the Jira push is guarded — Stage 5 has **no per-run validator and no fixtures** (31 `verify_*.py` exist; zero are Stage 5). Deliverable is `code_validator.py` — citation, routing, repo-qualifier and non_code checks, plus a **parse** of every modified file using the extractor toolchain already present. Fixtures prove the validator, sharing one implementation |
| Stage 4 — tabular stories | 2026-08-22 | **A pure rate change could not become a story.** `story_classification` required `code_location | new_build | non_code`, and `non_code` meant "a §7 document". Fixed with no new vocabulary: §16 `location` gains a tabular form; `non_code` widens to "work with no code location"; `evidence` decouples from the flag (§16 id **or** D-id). No `rate_change` flag — it would restate the §16 entry's own location (rule 8) |
| Stage 3 — rename | 2026-08-22 | **`compare` → `release_shape`.** The name described `cross`'s job — parsing and matching layouts — while the phase actually returns a release verdict (Stratus-only / PeopleSoft-only / integrated). Renamed before 003.2 builds it, when it is still a find-and-replace. §INT-4's title *"Release coordination"* now matches its phase |
| Stage 3 — fixture coverage | 2026-08-22 | Recorded that **the topological sort and layout drift detection have no executable case** — no impact pass declares `provides:`, and every interface has exactly one acquired party. Both need synthetic fixtures; the real declarations exercise neither |
| Stage 3 — type-section contract | 2026-08-22 | **Type sections gain `title` + `must_capture`**, declared inline on the pass (no `sections.yaml`). Four base-section fields stay absent by design. New rule: a type section's `must_capture` may never require anything reducible to a located impact — if it names a file and a change it belongs in §16 |
| Stage 3 — profile/acquired | 2026-08-22 | **`profile:` presence derived from `acquired:`** — absent when false, required when true. Tandem's `"[TBD]"` removed; it restated what `acquired: false` already said. Open: confirm whether the onboarding gate allows an acquired-but-unprofiled state, which would need a third case |
| Stage 3 — compare wording | 2026-08-22 | Compare's non-event fixed to *"no impact reached a declared interface site; no interface assessed"*. The old *"no interface fields changed"* asserted a check that never ran — which matters now that phase totality makes the record mandatory |
| Stage 3 — phase totality | 2026-08-22 | **Third G2 denominator adopted.** `resolve`/`cross`/`release_shape` were in neither existing precondition, so a phase could run, produce nothing and pass in silence. Every declared non-empty phase now owes findings or an explicit non-event; empty phases owe nothing. Non-events are records, not operator decisions — the walkthrough baseline is unaffected |
| Stage 3 — determinism | 2026-08-22 | **`flow_plan.py` adopted** — the run order and the load-time rejections are **computed, not reasoned**. A wrong sort is invisible (empty key set → fewer findings → every G2 check still green). The agent executes the returned plan and never reorders it; rejections stop the run rather than warning. `check_vdi_docs.py` is a working prototype of the rejection half |
| Stage 3 — estate completeness | 2026-08-22 | **Settlement declared** `in_estate: false, acquired: false` — it was a party to `submission` with no application entry, an undefined third state. First use of `in_estate: false`; the two "not now" states must produce different boundary text. New 003.2 schema rule: every `parties[].system` resolves to an application |
| Stage 3 — MCC scope | 2026-08-22 | **INT-P3 deleted.** It activated `mcc_mapping_impact`, which never existed — the one live `check_vdi_docs.py` failure. MCCs need no resolution (numeric, identical both sides) and are carried by ordinary assertion enrichment. The run-order line claiming resolve handles MCCs is corrected; `must_capture` deliberately left unchanged |
| Stage 3 — the section model | 2026-08-20 | **§16/§INT-n split decided** (003.1a): §16 is the sole impact spine and the only route to Jira stories; §INT-n carries specialist *context* only; `release_shape` writes §INT-4 and never §16; the generic arm drops `sections:` entirely. Opens one question — §16's `location` shape cannot express a tabular impact |
| Stage 3 — interchange floor | 2026-08-19/20 | **Floor narrowed to Stratus** (code + resolve); PeopleSoft rate tables become `pricing_impact`, probe-activated by INT-P2; `peoplesoft_code` dropped. `interface: mpt` dropped, then **restored 2026-08-20** — it is the sole invoker of the direct-layout assessment, without which the backward-crossing case is structurally uncatchable. PeopleSoft stays unfloored: closure reaches it. Consequences at 003.2 |
| Stage 3 — **closed** | 2026-08-18 | topics 7–10 reviewed and **closed with no new tasks**. 7 (reconstruction invariant) and 9 (scope-break path) recorded as PARKED; 8 (non-event convention) confirmed as an established pattern needing no separate task; 10 (runtime) is a VDI measurement, not a design question. Topic-5 loose ends dismissed — see PARKED. |

---

## Target state — where the design is going

Agreed across the design sessions of 2026-08-15/16/17. This is the **framework** the tasks below build
toward, recorded here so they have a shared destination. It supersedes nothing already built; it is
where the pipeline is heading.

> **Two naming collisions, resolved once here.**
>
> **Wave ≠ Stage ≠ Phase.** *Stages 0–5* are the pipeline stages inside a run. *Waves* are build order
> in TASK-V2-003. *Phases* (resolve / impact / cross / release_shape) are the internal structure of Stage 3. A build
> wave routinely spans several stages.
>
> **Two different things are called "sections."** The **Change Classification section** is written at
> **Stage 2, into v1** — the confirmed types, the reasoning behind them, and the probe answers. It is
> an **input to** enrichment. The **type sections** (`§INT-1`, `§CLR-1`, …) are written at **Stage 3,
> into v2** — the **output of** enrichment, which cannot exist code-blind.

### 1. One domain, many change types

`payment_brand` is now the **only** domain — the multi-domain ambition is retired. Variation moves down
a level, to the **type of change**: interchange, clearing, authorization, network fees. A single change
may be **more than one type**, so types compose by union, never by merge.

This is not a new seam. The `si_profile` already varies by domain; it now varies by
`(domain, change_type[])`. Widening an existing seam's key, not adding a third axis — which matters,
because "two seams only" is a hard rule.

Change type is also **already latent**: `interchange_enrich` self-gates today by sniffing content.
Making the type explicit replaces that inference with a declared, human-confirmed fact, and the
self-gating can be deleted.

### 2. The estate — what exists, and how impact crosses it

Two files describe the world. They do not vary by change type.

**`core/estate/applications.yaml`** — what applications exist and **what each is made of**. This is the
declaration that lets enrichment generalise past "analyse one repo":

```yaml
applications:
  - id: stratus
    in_estate: true
    acquired:  true
    repo: stratus-core
    substances:
      - { id: code,       kind: code, profile: c_repo.profile.yaml }
      - { id: submission, kind: file_layout, layout_at: include/submission_record.h }

  - id: peoplesoft
    in_estate: true
    acquired:  false                    # repo clonable later; declared now
    repo: peoplesoft-core
    substances:
      - { id: code,        kind: code }      # no `profile:` — unacquired (see rule below)
      - { id: rate_tables, kind: tabular }
      - { id: mpt,         kind: file_layout }

  - id: tandem
    in_estate: true
    acquired:  false
    repo: "[TBD]"                       # repo exists; name and language pending
    substances:
      - { id: code,    kind: code }          # no `profile:` — unacquired, same as peoplesoft
      - { id: pti_gen, kind: file_layout }

  - id: settlement
    in_estate: false                    # outside the estate — a party we do not analyse
    acquired:  false
    substances:
      - { id: submission, kind: file_layout }
```

> **Every application is code-first — PeopleSoft included.** Every application in the estate has a
> `code` substance and receives the same full repo scan Stratus receives today. PeopleSoft is not an
> exception dressed up as a lookup: a **PeopleSoft code change is what alters what MPT carries**, and
> that is the origin of most boarding-side impact. Treating it as a queryable table would make it
> permanently invisible as a *producer* and observable only as somebody else's consequence.

**`in_estate` and `acquired` are different questions.** *Do we analyse this system?* versus *can we
currently read its code?* A declared-but-unacquired application is a **reported boundary**, never a
silent stop — which is what lets the multi-application machinery be exercised before the second repo
arrives (§10).

**Every interface party must be a declared application** (added 2026-08-22). `settlement` was a party
to `submission` with no entry here at all, which is a **third state the design has no rule for**: not
`acquired: true` (scan it), not `acquired: false` (record a boundary), but *undeclared* — so crossing
to it had undefined behaviour, and *"outside the estate deliberately"* was indistinguishable from
*"somebody forgot"*. It is now declared `in_estate: false`, the first use of that flag, and the two
states must **read differently in the report** because they mean different things:

| Declaration | Meaning | The boundary says |
|---|---|---|
| `in_estate: true, acquired: false` | we intend to analyse it, cannot yet | *"repo not acquired; producer-side impact **undetermined**"* |
| `in_estate: false` | we deliberately do not analyse it | *"**outside the estate**; not assessed"* |

A schema check belongs with the others in 003.2: **every `parties[].system` resolves to an
application id.** This is live for interchange today — `stratus_code` scans the whole repo every run,
`src/settlement/submission_writer.c` is in it, and promotion fires on any declared site regardless of
the floor.

**`profile:` presence is derived from `acquired:`, never stated twice** (decided 2026-08-22). The
draft had three spellings of one state: Stratus `profile: c_repo.profile.yaml`, Tandem
`profile: "[TBD]"`, PeopleSoft no key at all — with Tandem and PeopleSoft in the *same* state. The
rule:

```
acquired: false  →  `profile` ABSENT, always
acquired: true   →  `profile` REQUIRED, naming a real file in core/code_profiles/
```

`profile: "[TBD]"` restates what `acquired: false` already says, so it is the same derivable-
duplication error as `activated_by:` and a party-level `acquired:`. Schema-checkable in one line.

> **Confirm on the VDI before pinning this:** does the onboarding gate (D11.4) guarantee a profile
> exists *before* a repo is first read? If a repo can be **acquired but not yet profiled**, that is a
> real third state and the rule needs a third case — `acquired: true, profile: absent` meaning
> *cloned, onboarding gate not yet run*. Adopted as a two-state rule because it is right for
> everything known today, and a third case is an **addition** to it rather than a rewrite.

**Non-code substances are additional instruments, never replacements:**

| Substance | Instrument | What only it can do |
|---|---|---|
| `code` | **scan** — full repo, code map, dependency closure | everything the code arms do today |
| `file_layout` | **field diff** between the two declared definitions | field-level crossing; layout drift detection |
| `tabular` | **keyed lookup** by resolved identifier | originate an impact with **no code change anywhere** |

That last row earns its place on exactly one case, and it is a real one: a **pure rate change** touches
no code in any repo. The PeopleSoft scan files a non-event, no layout moves, nothing crosses — and the
change is still real, visible only through the rate-table lookup keyed by the resolved mnemonics.

**`core/estate/interfaces.yaml`** — the file interfaces between systems. In this estate the coupling is
**file-based, not API-based**: Tandem hands pinless-debit billing to Stratus via PTI Gen; Stratus emits
a submission file to Settlement for billing; PeopleSoft pushes merchant setup to Stratus daily via MPT,
which determines who qualifies for which special program rates.

```yaml
interfaces:
  - id: mpt
    name: Merchant Profile Transfer
    carries: merchant setup; special program eligibility
    cadence: daily batch
    parties:
      - { system: peoplesoft, role: producer,          # acquired: false — from applications.yaml,
          writes_at: [TBD — repo not acquired],         #   never restated here
          layout_at: [TBD — repo not acquired] }        # SQR side; NOT the consumer's C header
      - { system: stratus,    role: consumer,
          reads_at:  src/config/mpt_loader.c,
          layout_at: include/mpt_record.h }

  - id: pti_gen
    name: PTI Gen
    carries: pinless-debit transactions handed to Stratus for billing
    parties:
      - { system: tandem,  role: producer, writes_at: src/billing/pti_writer.c,
          layout_at: include/pti_record.h }
      - { system: stratus, role: consumer, reads_at: src/intake/pti_reader.c,
          layout_at: include/pti_rec.h }

  - id: submission
    name: Stratus submission file
    carries: billed transactions for settlement
    parties:
      - { system: stratus,    role: producer, writes_at: src/settlement/submission_writer.c,
          layout_at: include/submission_record.h }
      - { system: settlement, role: consumer, reads_at: src/intake/submission_reader.c,
          layout_at: include/sub_rec.h }
```

**`parties` with roles, not a producer plus a list of consumers.** Crossing is symmetric — a consumer
that needs a field the interface does not carry propagates *backward* to the producer's write site
(below). A file shaped around one direction quietly makes the other direction a special case.

**Fields are derived, never hand-listed.** Field-level crossing needs fields addressable, and parsing
the declared layout on each side beats declaring them: mechanical recall rather than a list that goes
stale, and the layout-drift check falls out of the same parse instead of being separate work.

**`layout_at` is per-party because the two definitions are independent — that is the whole point.** In a
file-based estate there is no shared schema: each side hand-maintains its own record definition, in its
own language, and they drift. That drift is what the parse detects. **Two parties pointing at the same
path is therefore a smell, not a shortcut** — legitimate only where both sides genuinely compile from
one file, which cross-language coupling (SQR producer, C consumer) does not permit. `pti_gen` and
`submission` above model this correctly with distinct per-side layouts; MPT did not, and the error
silently reduced drift detection to a no-op on the one interface interchange depends on most.

**Why declaration is the only option, and why it is also cheap.** Nothing in the source connects the
two sides — Stratus opens a dataset, Settlement opens a differently-named local copy, and no analysis
links them. But because the estate is file-based rather than API-based, the set is **small, static and
enumerable**: a handful of interfaces, written once, edited rarely. That also makes it *checkable* —
scan each repo for external file I/O and every one must map to a declared interface or be marked
internal. **Undeclared external file I/O is a finding.** With APIs none of that would be possible.

Three properties fall out. **Boarding work becomes structurally derivable** — an impact on MPT implies
PeopleSoft work, without `interchange_enrich` having to know anything about boarding. **Layouts on both
sides give drift detection**, since duplicated layouts are the norm and drift is silent. And **co-change
history validates the declarations**: two systems that always move together with no declared interface
is a hole in the file.

#### The estate walk — how impact crosses systems

`flow.yaml` says which applications to assess. The **walk** expands that set, and it is entirely
**generic** — driven by `interfaces.yaml`, never re-declared per change type.

```
for every application in scope:
    scan its code (full repo)
      → does an impact land on a declared interface site?   (reads_at / writes_at / layout_at)
          → PROMOTE: interface impact, at FIELD level
              → CROSS to every other party to that interface
                  → that field's read/write sites in their code = new impacts
                      → which re-enter that application's own dependency closure
                          → repeat until nothing new enters.  FIXED POINT.
```

**Promotion is mechanical.** An impact promotes when its `file:line` falls inside a site declared in
`interfaces.yaml`. Not a judgement, and not a model deciding whether something looks interface-shaped.

**Crossing runs both ways.** *Producer-side:* PeopleSoft changes what it writes into MPT → Stratus's
read sites are impacted. *Consumer-side:* Stratus needs a field MPT does not carry → the impact crosses
**backward** to PeopleSoft's write site and layout. The second direction is a PeopleSoft code change
originating from a Stratus requirement, and it is the case nobody currently discovers until
implementation.

**Two entry paths to an interface node**, and both are needed:

1. **Promoted from a code hit** — the ordinary path, wherever the application's code is acquired.
2. **Assessed directly against the layout** — a field diff with no code scan involved. This is the only
   path available while an application is declared-but-unacquired, and it is what keeps a boundary
   informative rather than blank.

**Three properties the walk must have:**

- **Cycle protection.** Stratus → submission → Settlement → … can return. Visited set on
  `(application, substance, field)`.
- **Substance-level nodes.** The unit is `(application, substance)`, never application. *"We assessed
  PeopleSoft"* is not a statement — rate tables and the MPT layout are separate assessments with
  separate outcomes, and one must never stand in for the other.
- **Termination is reported.** Where the walk stopped and what it did not explore:
  *"Estate walk closed at depth 3. MPT crossing reached PeopleSoft (producer); repo not acquired;
  0 sites scanned; producer-side impact undetermined."* Silent truncation reads exactly like complete
  coverage. Surfaced in the Enrichment Report (TASK-V2-006).

### 3. The flow — what runs, per change type

**`change_types/<type>/flow.yaml`** declares the analysis. The framework stays generic; all branching
lives in data. Authorization not looking at interchange codes is not a special case — it is a shorter
flow file.

The full file set for one change type:

```
core/profiles/payment_brand/change_types/interchange/
├── flow.yaml                  ← the rules: floor, resolve, impact, release_shape
├── probes.yaml                ← the questions, and which passes each answer activates
├── resolve_mnemonic.skill.md  ← the reading (moved from interchange_enrich.skill.md)
└── assess_qualification.skill.md   ← a specialised reader, activated by a probe
```

```yaml
# change_types/interchange/flow.yaml
id: interchange

# ── FLOOR: assessed on every interchange change, whatever the scan finds and
#    wherever the estate walk reaches. A floor, never a ceiling.
floor:
  - { application: stratus, substance: code }
  - { phase: resolve,       application: stratus }   # the dictionary is always read
  - { interface: mpt }                               # assessed against its layouts every run,
                                                     #   code hit or not. PeopleSoft is NOT floored:
                                                     #   closure pulls it in when MPT is impacted.

resolve:                                   # external vocabulary → internal identifiers
  - id: designator_to_mnemonic
    application: stratus                   # Stratus is the dictionary
    substance: code
    skill: resolve_mnemonic.skill.md
    reads: [v1.assertions, stratus.code_map, networks.yaml]
    provides: [mnemonic, program_code, interchange_level]
    must_capture:
      - every designator or program name in v1 resolves to a mnemonic, or is
        listed unresolved with why
      - every resolved mnemonic carries the code location that defines it
    on_unresolved: escalate                # never proceed silently on a partial key set

impact:
  - id: stratus_code
    application: stratus
    substance: code
    skill: code_impact_assess.skill.md     # the generic arm — also the default if omitted
    needs: [mnemonic]                      # identifiers, not pass ids
    search:
      keys:  [mnemonic, program_code, interchange_level]  # exhaustive — each accounted for
      scope: full_repo                                    # unbounded — keys never narrow this
    reads: [v1.assertions]
    # no `sections:` — the generic arm produces ordinary impacts, and every
    # impact goes to §16 regardless of which pass found it. See 003.1.

  - id: pricing_impact                     # conditional — see probes.yaml INT-P2.
    application: peoplesoft                #   NOT declared here: the pass names no probe
    substance: rate_tables
    needs: [mnemonic]
    search: { keys: [mnemonic], scope: full_table }
    reads: [v1.assertions]
    must_capture:
      - every resolved mnemonic has a current rate recorded, or is reported
        absent from the table
    sections:
      - id: INT-3
        title: Pricing
        must_capture:
          - every resolved mnemonic has its current and target rate, or is
            reported absent from the rate table

  - id: qualification_impact               # probe-activated, specialised reader
    application: stratus
    substance: code
    skill: assess_qualification.skill.md
    needs: [mnemonic, program_code]
    search: { keys: [program_code], scope: full_repo }
    reads: [v1.assertions]
    must_capture:
      - every program code has its qualification criteria located, or reported absent
    sections:
      - id: INT-5
        title: Qualification criteria
        must_capture:
          - where criteria are defined for each affected program code, and how
            this change moves them
          - program codes checked and unaffected, so "not affected" is
            distinguishable from "not checked"

release_shape:
  # The crossing and the separate/integrated determination are GENERIC — driven by
  # core/estate/interfaces.yaml, not re-declared per type. This only binds the output.
  sections:
    - id: INT-4
      title: Release coordination
      must_capture:
        - the verdict — Stratus-only, PeopleSoft-only or integrated — with the
          interface field and the consumer read site that prove it
```

```yaml
# change_types/authorization/flow.yaml — the minimal second type
id: authorization
floor:
  - { application: stratus, substance: code }
resolve: []                                 # no external→internal translation needed
impact:
  - id: stratus_code
    application: stratus
    substance: code
    search: { keys: [], scope: full_repo }
    reads: [v1.assertions]
    # no `sections:` — generic arm, and no specialised reader means no context
    # section either. authorization produces §16 entries and nothing else (003.1a).
release_shape: []
```

```yaml
# change_types/interchange/probes.yaml
probes:
  - id: INT-P1
    ask: Is this change specific to qualification criteria?
    answer_from: corpus_first        # operator asked only where the documents don't settle it
    activates: [qualification_impact]
  - id: INT-P2
    ask: Does this change pricing for existing programs?
    answer_from: corpus_first
    activates: [pricing_impact]
```

**Properties worth protecting:**

- **The floor is a floor, never a ceiling.** Declaring that interchange always assesses Stratus — its
  code, and its dictionary via resolve — guarantees a minimum; it must never become the *definition* of
  where an interchange change can land. This is the one degradation somebody will later introduce as an optimisation, so it is
  written as a rule rather than left as an assumption.
- **Two search obligations per pass, and neither substitutes for the other.** `search.keys` is a closed
  set that must be searched **exhaustively**, each key accounted for as found-here or not-found.
  `search.scope: full_repo` is **unbounded** — the whole repo, anchored to v1's assertions, looking for
  everything else this change touches. Resolution creates a *search obligation, not a search boundary*.
  The failure to design against is "we resolved the mnemonics, so search for those," which silently
  converts the scan into a lookup.
- **Resolution is a phase, not a pass.** Stratus plays **two roles**: the **dictionary** (only it knows
  which mnemonic a network program name or designator maps to) and a **target** (code that changes).
  Everything downstream needs the lookup already done — the rate tables are keyed by mnemonic, and code
  impact must search for *mnemonics, not network program names*. Resolution therefore precedes all of
  it.
- **`needs` names identifiers, not pass ids**, and the orchestrator matches `needs` against `provides`
  to build the graph. Three things fall out: a `needs` naming something nothing `provides` is a **config
  error at load time** rather than a pass that silently runs empty; a second resolve pass providing the
  same identifier requires no downstream edit; and **`provides` becomes an identifier-only vocabulary**,
  which makes *join keys forward, never conclusions* mechanically enforceable — a pass physically cannot
  declare `provides: [mpt_is_impacted]`, because that is not an identifier and the schema rejects it.
- **`needs` sequences; it never scopes.** It decides *when* a pass runs, nothing more. The pass still
  reads every v1 assertion, still searches every key, still scans the whole repo.
- **`provides` is a contract, enforced before the dependents start.** If v1 names three designators and
  resolve produces zero mnemonics, the orchestrator refuses to start the passes that need them rather
  than running three thin scans against an empty key set. Today that failure is invisible — the scans
  simply find less.
- **Order is derived, never written.** The topological sort falls out of `provides`/`needs`. No
  hand-maintained run order to drift, and parallelism falls out wherever `needs` is empty.
- **Every pass also `reads: [v1.assertions]`.** Upstream keys narrow nothing; v1 anchors everything.
  This is what keeps a **pure rate change visible** when Stratus contributes no keys at all, and what
  makes an upstream miss *detectable* — a designator named in v1 but absent from the key set is
  reportable as *"v1 names D; no mnemonic resolved; searched by name directly, found nothing"* instead
  of vanishing along with the resolve failure that caused it.
- **`skill:` is the variation point, and omitting it means the generic arm.** A probe-activated sub-pass
  can point at a specialised reader — `assess_qualification.skill.md` rather than the generic
  `code_impact_assess` — with everything else unchanged. **One skill per pass:** wanting both the
  generic arm and a specialised look means declaring two passes, so each is individually accountable for
  findings-or-non-event and you can see which one found what.
- **Type-specific skills live with their flow**, in the change-type directory — `core/skills/` stays
  generic. Adding a specialised reader therefore adds nothing to the generic core.
- **Sections are declared on the pass that produces them**, replacing a separate `sections.yaml` and its
  `produced_by` cross-reference. The binding becomes structural rather than a pointer that goes stale.

> **The line to hold: YAML declares obligations and wiring; the skill does the reading.** `flow.yaml`
> says *a mnemonic must come out of Stratus, here is what happens if one does not, and here is who needs
> it.* `resolve_mnemonic.skill.md` says *how to read C source and recognise a program-name-to-mnemonic
> mapping.* The moment the YAML starts describing **how** to search, it has become a programming
> language in a config file — the same failure as branching on domain inside a skill, arriving from the
> other direction.

**Checks are declared up front, and each has an enforcement point.** Declaring them only pays if
something stops on them:

| Check | Declared as | Enforced |
|---|---|---|
| Resolve produced its identifiers | `provides:` | **before** any pass needing them starts |
| Every designator resolved or explained | `must_capture:` | at pass completion |
| Every key exhaustively searched | `search.keys:` | at pass completion |
| The scan was not quietly narrowed to the keys | `search.scope: full_repo` | fixture assertion |
| Every floor item assessed | `floor:` | **G2 precondition** |
| Every activated pass filed findings or a non-event | `activates:` | G2 precondition |

**The release-shape step's real output is a release-coordination finding**, and it may be the most valuable
thing the restructure produces:

- **Stratus-only** — code logic with no MPT dependency; ships on Stratus's schedule
- **PeopleSoft-only** — rate table updates; ships on PeopleSoft's schedule
- **Integrated** — an MPT field and its Stratus consumer must change *together*, or the daily file breaks

Today nobody learns which is which until implementation.

### 4. The base Solution Intent gets shorter, decided by consumption

Eighteen sections were designed to serve any domain. With one domain some are dead weight — but the
section set is coupled to `jira_template.payment_brand.yaml`, so cutting by judgement breaks the Jira
plan silently.

Cut by **consumption**: for each of the eighteen, list what reads it. No reader → clean cut.
Type-specific reader → move into a type package. Expect the answer to be *"nine shared, plus three or
four per type"* rather than a flat shorter list.

### 5. Stage 2 — the type is worked out, then v1 freezes

1. Author base v1 from the documents only — generic questions, the existing flag loop
2. Match v1 against the history KB → **recommend change type(s)** with past Jira keys as evidence
3. Operator accepts or substitutes their own — recorded, **including whether they differed**
4. **Probes fire** for the confirmed types — capturing requirement-shaped facts, and **refining within
   the type** (qualification? pricing? MCC?), each activating the sub-passes its answer implies
5. **G1 — v1 freezes**, now complete with its Change Classification section

**G1 comes last.** Freezing before step 4 would put the probe answers post-freeze, which has no clean
home. Still five gates — step 3 is a flag-gate interaction, not a sixth.

**Classification is evidence, not inference.** The agent hands over a *recommendation with reasoning*,
with the precedents it rests on **cited by Jira key**. *"Interchange and clearing, because PBI-4471 and
PBI-4602 both involved IRD changes and settlement-window shifts, and this requirement mentions both"* is
reasoning on evidence. *"This looks like interchange because it mentions fees"* is what the mechanism
exists to avoid. Stage 0 declaration is kept as a **hypothesis**, not replaced — and disagreement is the
most valuable output, because it is a scope catch.

### 6. Stage 3 — the flow executes

6. Load `flow.yaml` for the confirmed type(s), including probe-activated sub-passes. **Scope opens at
   the floor**, unioned with whatever the KB proposed
7. **Resolve** — program names and designators become mnemonics, program codes, interchange levels
8. **Impact** — every pass whose `needs` are satisfied, in derived order; each searching its keys
   exhaustively, scanning its whole repo, and reading v1
9. **Cross** — impacts landing on declared interface sites promote and cross, field-level, into the
   other parties' code; new applications enter scope and are scanned in full; repeat to fixed point (§2)
10. **Release shape** — the crossed field set → separate vs integrated
11. **Reconcile** — findings that contradict each other (TASK-V2-004)
12. **Walkthrough** — the one operator turn
13. **Consolidate → v2**, then G2

**Scope comes from four places, and only one of them is advisory:**

| Source | What it does | Can it remove anything? |
|---|---|---|
| **Floor** — declared per change type | Interchange always assesses Stratus and PeopleSoft | no |
| **Scan** — full repo, per application in scope | Finds what nobody predicted | no |
| **Closure** — interface crossings | Expands the application set to a fixed point | no |
| **Prior** — the Jira KB | Proposes type and applications; challenges the result at G2 | **no — it widens only** |

The KB determining *which applications are impacted* is right, under one constraint: it **unions into**
the scope set and never subtracts. It may say *"comparable changes also touched Tandem, add it"*; it may
never say *"no comparable change touched Settlement, skip it."* Monotone-increasing, for the reason in
§9 — history records what people did, not what was correct.

**Per-application enrichment files, deterministically merged.** Each pass writes its own findings file;
`enrichment.json` is the consolidated artifact and **every input file is retained, not consumed**. The
merge is fixed-order, **model-free**, and surfaces conflicts rather than resolving them — so
`v1 + enrichment → v2` still reconstructs exactly.

**Worked example — an MCC change.** v1 says MCC 7011 and 7512 move to a new qualification tier. Resolve
asks Stratus which programs cover those MCCs, and therefore which mnemonics. PeopleSoft then gives
current and target rates for those mnemonics. Only then does code impact run, finding where MCC-to-
program mapping lives in Stratus and where MPT carries it. Release shape says whether the MPT field and its
Stratus consumer must move together.

> **Suspected current defect.** The architecture diagram shows Arm 1 and Arm 2 running *before*
> `interchange_enrich`, which is what resolves designator → mnemonic → level. If accurate, the arms are
> searching Stratus **in the network's vocabulary rather than the internal one** — looking for program
> names in code that identifies things by mnemonic. Confirm against `start-enrich` before treating it as
> fact; if it holds, moving resolution to the front is not a restructure but a fix.

### 7. Probes — candidates that route

A probe fires at **Stage 2** if any Stage 3 pass reads its answer. Decidable per probe by one question:
*does anything downstream consume this?*

**Probes are candidates, not a script.** The author answers each from the corpus first and puts only the
unanswered ones to the operator. Asking what the documents already state invites an answer from memory
to compete with a source, manufacturing an escalation that was never open.

> **MCCs are deliberately not a resolve concern (decided 2026-08-22).** An earlier draft carried
> `INT-P3 — does this change MCC-to-program mapping?` activating `mcc_mapping_impact`, a pass that was
> never written. It is **deleted** rather than built: MCCs are industry-standard numeric codes used
> identically on both sides, so unlike a network *designator* they need no external→internal
> translation. An MCC change is carried by ordinary assertion enrichment — v1 names the MCC, every
> pass `reads: [v1.assertions]`, and `stratus_code`'s unbounded `full_repo` scan finds it by value.
> Re-add a probe **and** a pass together if that ever proves wrong; never a probe alone.

**Probes activate passes by id, in one direction only:**

```yaml
- id: INT-P1
  ask: Is this change specific to qualification criteria?
  activates: [qualification_impact]
```

The pass says nothing about probes, so there is one place to keep in sync — **no `activated_by:` on the
pass, ever.** Whether a pass is conditional is *derived*: the orchestrator unions every `activates:`
across the loaded probe files, and a pass named by no probe is unconditional. Putting the back-reference
on the pass would restore exactly the two-places-to-sync problem this rule exists to remove. Where a probe was answered
from the corpus, the activation carries that citation — **the routing decision is sourced**, which is
stronger than either declaration or inference. This also makes a probe's purpose testable: if the answer
changes nothing that runs, it is a note, not a probe.

**Non-activation is recorded**, distinctly from a non-event: *"qualification sub-pass not run — probe
INT-P1 answered no, sourced from mandate §4.2."* Otherwise *we determined this isn't qualification-
related* is indistinguishable from *nobody considered qualification*.

### 8. Every application in scope is scanned in full

No candidate selection, and no partial scans. Every application that enters scope — by floor, by KB, or
by crossing — gets **the same full repo scan Stratus gets today**. This removes the sequencing problem
(nothing discovered late) and the risk of history acting as a filter. The map cache on
`(commit_sha, profile_sha)` makes map-building a one-time cost per repo version.

The cost moves to **enrichment**: more code means more candidate landing sites, and the cache does **not**
cover the assessment passes. Cost therefore scales with *applications entering scope*, not with repo
count — which makes the crossing walk, not the repo list, the real cost driver. Watch §16 for bloat once
there are real runs — and note that `tier_walk`'s tiers likely already map onto the existing
EDIT / VERIFY / VALIDATE story actions, which would make the control cheaper than it looks.

### 9. History — classifier at Stage 2, completeness check at Stage 3

**At Stage 2 it classifies**: what kind of change is this (§5, step 2).

**At Stage 3 it checks completeness** — because `flow.yaml` already determines which applications are
analysed, history never scopes the work:

> *"Your §16 impacts land in Stratus and Settlement. Four of five similar past changes also produced
> commits in system D. Nothing was found there — is that correct?"*

Both directions matter: **under-detection** (an engine history expects and the scan missed) and
**over-detection** (a plan touching engines no comparable change ever did — a far better bloat signal
than counting stories, since it names *which* impacts to doubt).

**Resolved to engines, not repos** — the code map translates commit paths into components, and components
into engines. Finer-grained, and the language the business speaks.

**Prior, then evidence, then judgement, then a human.** History yields a **frequency** (*"8 of 11 similar
changes touched settlement"* — a computed fact, never a percentage), committed to the ledger **before**
the scan so the reconciliation can be audited for whether it actually updated. The scan yields
**strength**, not a yes/no. The agent reconciles with reasoning citing both. The operator decides, and
disagreement is recorded.

**The KB builds itself** — Stage 5 already commits with the Jira key and records it on each story. And
because the Jira prefix identifies the engine, application impact is a field lookup rather than an
extraction problem, which also covers **PeopleSoft work that produces no commit at all.**

> **The limit of generalising from volume.** Co-change history records **what people did, not what was
> correct.** If an engine was genuinely impacted but nobody ever raised a story against it, the corpus
> reports it unimpacted — and more history makes that blind spot *more* confident. This is why history
> must never filter the scan: the scan is the only instrument that can see what past practice missed.

**Guard:** history is a prior, never a filter. It ranks and it challenges; it never defines where the
system may look.

### 10. Build for multi, run as one

The machinery is generic from day one; the **configuration** stays at one application and one change
type, and expands by declaration.

The risk in "build general, configure narrow" is that the single case leaks into the code and the
generalisation never actually arrives — everyone believes the machinery is there because it was designed
that way. The risk in the other direction is building a framework against one real case and being wrong
in ways nothing can reveal.

**The discipline that gets both: N=1 real, plus a deliberate declared stub, from day one.**

- **Applications** — Stratus real and fully acquired. PeopleSoft and Tandem declared in
  `applications.yaml` with their interfaces declared, `acquired: false`.
- **Change types** — interchange real and complete. `authorization` present as the minimal `flow.yaml`
  above, so the type-union path, the empty-`resolve` path and the empty-`release_shape` path all execute.

The stubs exist so the multi-application paths **run and are asserted on** before the second repo exists:

```
CROSS  mpt.consumers → Stratus read sites → §16 impacts                      ✓ real
       mpt.producer  → PeopleSoft: declared, NOT ACQUIRED
       → recorded: "MPT crossing reached PeopleSoft (producer). Repo not yet
          in estate; 0 sites scanned. Producer-side impact undetermined."
```

**The estate boundary is a reported edge, never a silent stop.** A walk that terminates quietly at an
unacquired application is indistinguishable from one with no crossing logic at all — and that
indistinguishability is exactly how *"we'll generalise later"* dies. With the stub, a fixture asserts the
walk reached the boundary and said so, which tests the machinery today and turns PeopleSoft's arrival
into a clone plus a config flag.

**The acceptance criterion, and it is checkable now:** *adding an application or a change type is zero
code change.* A new change type is a directory with a `flow.yaml`, a `probes.yaml` and possibly one
skill. A new application is an entry in `applications.yaml` plus its interfaces. If adding `clearing`
requires touching `core/scripts/` or `core/skills/`, the declaration was not expressive enough and the
fix belongs in the schema, not in a branch.

---

> **Note on TASK-V2-003.** Re-scoped to this model on 2026-08-17: **003.2** is now the estate and flow
> declarations *including the per-type floor*, **003.5** is the flow orchestrator *plus the estate walk*,
> and **003.10** is interface-crossing rather than cross-repo *code* closure — which would find almost
> nothing in a file-coupled estate.
>
> **Second revision, same day.** The estate is **code-first**: every application including PeopleSoft has
> a `code` substance and gets a full repo scan, with `tabular` and `file_layout` as *additional*
> instruments rather than replacements. Crossing is **bidirectional and field-level**. `needs` names
> **identifiers**, not pass ids. And **003.10 split** — 003.10a (crossing over the interfaces you can
> declare today) needs no history and moves up behind 003.2; only 003.10b (*discovering* undeclared
> interfaces, plus totality and drift) stays behind 003.7.

---

## PARKED — raised in review, no task written

**Doc lane has no cache while the code lane does.** Code is cached on
`(commit_sha, profile_sha)` and `reset_run.py` deliberately preserves `repo/` + `code_map/`. The
doc lane gets the opposite treatment: `reset_run.py` explicitly wipes it, so every re-run re-fetches
and re-extracts every document, pushing large PDFs back through vision. In practice the standing
references (`mastercard_mandate_part1_2026.pdf`, `AIP_Description_Discover_Spec.csv`) recur
unchanged across many runs. Note the infrastructure already exists — `cache/` sits at the repo root
holding only a README, and `core/scripts/map_cache.py` implements exactly this pattern for the code
map — so this would extend an established mechanism rather than invent one. Content-address the
extract + index on source identity plus size/etag, and give `reset_run.py` a `--fresh-docs` flag
mirroring `--fresh-code`.

**The SI validator gates G1 and has no verify script.** `fixtures/si_author/` has
`verify_si_author.py` and `fixtures/si_profile/` has `verify_si_profile.py`, but
`fixtures/si_validator/` holds only `README.md` and `si_fail.md` — a failing-SI sample with nothing
that runs it. The component deciding whether v1 is good enough to **freeze permanently** is the one
piece of Stage 2 with no standing proof, and a ready-made negative case sits there unused.

**G1 appears to have weaker enforcement than G2, despite worse consequences.** The Stage 3 validator
is described as *"scores enrichment, hard preconditions → G2"*; the Stage 2 validator as *"scores the
SI and surfaces G1"* — no hard preconditions. If accurate, that is backwards: G2 approves a document
that can still be revised, while **G1 freezes permanently**. A soft score in front of an irreversible
action becomes theatre — the operator sees a number, sees no hard failure, approves.

**Candidate hard precondition — citation resolution.** The dangerous failure is not an honest
`[TBD — unsourced]`, which is visible and does its job; it is a claim carrying a citation that does
not resolve, because that reads as grounded and gets no scrutiny. Unlike most quality questions here
this one is deterministic: `doc_index` gives line-addressable documents, so a script can verify every
citation in v1 points at a document actually in `context_set/index.json` and at a line range that
actually exists. Binary, not a score — every citation resolves or the gate does not open.

**Is the reconstruction invariant actually tested?** *(Topic 7, reviewed 2026-08-18. The review log
recorded it as parked; the entry was never written — restored 2026-08-22.)* **"v1 + `enrichment.json`
reconstructs v2 exactly" is the strongest guarantee in the system** and the whole audit story: every
difference between the code-blind and the code-checked document traces to a numbered finding. Is there
a check that re-runs the apply pass and diffs the result, or is it a convention nobody verifies? Same
shape as the SI-validator finding — if untested it is an **aspiration, not a property**. And **003.5
makes it harder, not easier**: per-application findings files merged deterministically must still
reconstruct exactly, so the merge is now part of what the invariant depends on.

---

**Is there a scope-break path?** *(Topic 9, reviewed 2026-08-18. Recorded as parked; entry never
written — restored and narrowed 2026-08-22.)* Not a correction, and not the ordinary escalation: the
case where enrichment reveals **v1's premise was wrong**. Hard rules say scope changes are
**operator-decided**, but is there a mechanism, or does the run continue on a broken foundation?

**What this session established narrows it considerably.** The ordinary path *is* specified: 005 Part D
routes `modify_existing` + not-found to **ESCALATE**, naming all three candidate causes, and acceptance
criterion 7 makes it a G2 precondition — no unresolved escalation passes the gate. Part E files it as a
scope finding and never auto-corrects the requirement. §17 (Open questions) is the destination for a
finding the operator **defers**.

**So what remains open is only the severe case:** an escalation whose resolution is *"v1 is wrong, this
is a different change than we documented."* Escalating and blocking G2 is right, but blocking is not the
same as a route back to Stage 2 — and nothing describes what re-authoring v1 mid-run would mean for the
freeze, for `enrichment.json`, or for the reconstruction invariant above.

---

**Stage 5 has no fixtures.** *(Recorded as parked in the prior hand-off; entry never written — restored
2026-08-22.)* `fixtures/code_author/` and `fixtures/code_push/` do not exist, so the stage that drafts
the actual code change has no standalone proof. Every other subsystem's fixture directory carries a
`verify_*.py` that is that subsystem's proof and must stay green. Stage 5 is the one that writes code
and the one with nothing holding it.

---

**~~Is `pdf_extract` correctly domain-scoped?~~ ANSWERED 2026-08-23 — the skill says so itself.**
`core/profiles/payment_brand/adapter/pdf_extract.skill.md` states: *"**Domain-agnostic by nature.**
PDF→text carries no `payment_brand` knowledge; the skill lives in the domain pack **only for pipeline
ordering**. It does not branch on `domain` (D7)."* So it is correctly **behaved** and merely
**misplaced** — a second domain inherits a copy it has no reason to change. Whether relocating it is
worth the churn is a separate, low-stakes call; the correctness question is closed. *(Original entry
below.)*

**Is `pdf_extract` correctly domain-scoped?** It sits at
`core/profiles/payment_brand/adapter/pdf_extract.skill.md`. If it encodes how Visa/Mastercard lay
out mandate documents, that is genuine domain knowledge and the placement is right. If it is generic
PDF handling that merely lives there, a second domain inherits a needless copy. Resolvable by
reading the skill; not worth a task until read.

---

# OPEN WORK

## [ ] TASK-V2-001 — the Run Brief: make G0 review the configuration, not the folder

### Why this exists

Today G0 is "scaffold review": after Generate, the operator confirms the run workspace assembled.
That is a **deterministic, mechanically checkable property** — a script confirms it more reliably
than a person reading a directory listing.

Meanwhile the decisions that actually steer the run are made one step earlier, in the six-tab form,
and are **never reviewed by anything**. A source's `disposition` decides which later stage reads it;
the repo ref decides which code the enrichment arm reasons against; `registry_sha` decides which
version of the brains executes. Each is chosen in a dropdown, and a wrong choice is silent — the
file is fetched, staged and catalogued exactly as a correct one would be, and the consequence
surfaces stages later as an absence rather than an error.

Compare the other gates: G1 approves a written Solution Intent, G2 a code-checked v2 with an audit
trail, G3 a scored Jira plan, G4 actual diffs. Every one puts a substantive artifact in front of a
human. G0 alone puts a directory listing in front of them, and the judgment that needed a human went
past unexamined.

This task moves the review to where the risk is. Generate additionally produces **`run_brief.md`** —
a plain-language statement of what this run is configured to do and what will silently degrade —
and **G0 stops on that file** instead of on the folder.

> **Ladder note.** This changes the *meaning* of G0, which is a pinned gate. That amendment is part
> of this task (see Creates/edits: `OPEN_RULINGS.md`, `TECH_SPEC.md`). Nothing else about the gate
> sequence changes: G0 remains operator-performed, remains before `/start-ingest`, and remains
> recorded in `decisions.jsonl`.

### Depends on

Confirm each of these exists on disk before starting. **If any is missing, stop and report it** —
do not create it and do not substitute a similar path.

- `core/scripts/generate.py` — the Generate entry point this hooks into
- `core/scripts/dispositions.py` — the disposition taxonomy
- `core/scripts/ledger.py`, `core/scripts/gate.py` — ledger + gate recording
- `core/profiles/payment_brand/si_profile.payment_brand.yaml`
- `core/templates/payment_brand/jira_template.payment_brand.yaml`
- `core/code_profiles/c_repo.profile.yaml`, `core/code_profiles/mixed_repo.profile.yaml`
- `core/extractor_manifest.yaml`, `core/registry_manifest.yaml`
- `core/instruction_file.template.md`
- `fixtures/UI_INPUT.example.yaml`, `fixtures/generate/verify_generate.py`
- `core/scripts/build_checks.py`, `core/scripts/checks/check_disposition_totality.py`

### Reads

Open and read these before writing anything. Work from the cited text, not from memory.

- `docs/TECH_SPEC.md` — the gate table and the run-workspace layout (where `run_brief.md` belongs)
- `docs/TECH_SPEC.md` — the `UI_INPUT` schema (§3.1 validation), so the Brief reads real field names
- `core/scripts/dispositions.py` — the current taxonomy in full
- `fixtures/UI_INPUT.example.yaml` — the canonical shape of a config
- `docs/OPEN_RULINGS.md` — the format a ruling is recorded in
- `core/scripts/generate.py` — where in the Generate sequence the Brief must be produced

### Part A — make the disposition→consumer relation explicit

The dead-source check needs to know **which stage consumes each disposition**. That relation exists
today only implicitly, inside skill prose. Make it data.

Extend the disposition taxonomy in `core/scripts/dispositions.py` so every disposition declares the
stage(s) that read it — for example `business_requirement → [2]`, `reference_table → [3]`,
`jira_exemplar → [4]`, `codebase → [1, 3, 5]`. Use the stage numbers already used in
`vdi_design.md` §4.

Rules:
- The relation is **data, read by the checker** — never a hardcoded table inside `run_brief.py`.
- A disposition with an **empty** consumer list is legal and meaningful: it declares "nothing reads
  this," which is exactly what makes a dead source detectable.
- `core/scripts/checks/check_disposition_totality.py` **must stay green**. If the added field
  breaks it, extend the check to cover the new field rather than weakening it.

### Part B — `core/scripts/run_brief.py`

A new generic script. It reasons over `UI_INPUT.yaml` plus the **hydrated** `core/` in the run
workspace, and writes `run_brief.md` to the run workspace root, beside `UI_INPUT.yaml`.

It performs **no network calls** and reads nothing outside the run workspace. Source reachability is
deliberately out of scope for this task.

**Blockers** — the run cannot succeed; emit under a `BLOCKERS` heading:

1. No source carries a requirement-bearing disposition → the Stage 2 author has nothing to write from.
2. The configured domain has no `si_profile.<domain>.yaml` under `core/profiles/<domain>/`, or no
   `jira_template.<domain>.yaml` under `core/templates/<domain>/` → the run dies at Stage 2 or 4.
3. A source declares a disposition absent from the `dispositions.py` taxonomy.
4. `registry_sha` is not a full explicit commit sha (a branch name or short sha is a blocker — an
   unpinned registry means the run is not reproducible).

**Warnings** — the run proceeds but degrades; emit under a `WARNINGS` heading:

1. **Dead source** — a source whose disposition has no consuming stage in this configuration. This
   is the wrong-dropdown error and is the single most valuable line in the Brief.
2. **No code source** — no `codebase` source configured. Name the full consequence explicitly:
   Arm 1 (`code_impact`) produces nothing, §16 stays empty, every story lands without a
   `code_location`, and Stage 5 has nothing to author.
3. **No matching code profile** — the configured repo matches no `core/code_profiles/*.profile.yaml`
   / `core/extractor_manifest.yaml` entry, so the onboarding gate will fire at Stage 1.
4. **Exemplar without target** — a `jira_exemplar` source is present but no Jira project is configured.
5. **Duplicate disposition** — two sources claim a disposition the profile expects once.

**Output.** `run_brief.md` is written for a human to check against intent, so it renders prose and
resolved consequences — never a YAML echo. Each source appears on one line with its disposition and
the stage that will read it. Required shape:

```
RUN BRIEF — <run name>
Domain: <domain> · Registry: <sha> (pinned) · Tool: <runtime_tool>

SOURCES (<n>)
  ok   <source>    <disposition>              → read at Stage <n>
  warn <source>    <disposition>              → read at Stage <n>, but <reason>

WILL WRITE EXTERNALLY: Jira at G3 · Bitbucket branch at G4
BLOCKERS <n> · WARNINGS <n>
```

### Part C — wire it into Generate and G0

- `core/scripts/generate.py` calls `run_brief.py` as the **final step** of Generate, after hydration
  and scaffold assembly.
- **A blocker does not crash Generate.** The scaffold still completes and `run_brief.md` is still
  written — the operator must receive the diagnosis, not a stack trace. What a blocker does is make
  G0 **unacceptable**: `gate.py` refuses to record G0 as passed while `run_brief.md` reports one or
  more blockers.
- `core/instruction_file.template.md` — G0's description changes from reviewing the scaffold to
  reviewing `run_brief.md`. This is the generated instruction file, so both tool variants inherit it.
- Check `overlays/claude/launch.md` and `overlays/copilot/launch.md` for any wording that describes
  G0 as a scaffold review, and amend both. **Both overlays must stay behaviourally identical** —
  `check_overlay_parity.py` must stay green.
- The G0 decision recorded in `decisions.jsonl` gains the warning count the operator accepted, so
  the audit trail shows what was knowingly waived.

### Part D — docs

- `docs/TECH_SPEC.md` — amend the gate table so G0 reads against `run_brief.md`; add `run_brief.md`
  to the run-workspace layout; add the blocker/warning list as the checker's contract.
- `docs/OPEN_RULINGS.md` — append a ruling recording the G0 semantics change, and keep the
  alternative that was weighed: *leaving G0 as a scaffold review and adding the Brief as advisory
  only.* That was rejected because an advisory file beside a gate that passes regardless is a file
  nobody reads — the gate has to be the thing that stops.

### Creates / edits

| Path | Action |
|---|---|
| `core/scripts/run_brief.py` | create |
| `core/scripts/dispositions.py` | edit — add the consumer relation |
| `core/scripts/generate.py` | edit — invoke as final Generate step |
| `core/scripts/gate.py` | edit — refuse G0 while blockers exist |
| `core/instruction_file.template.md` | edit — G0 reviews the Brief |
| `overlays/claude/launch.md`, `overlays/copilot/launch.md` | edit — G0 wording, both identically |
| `core/scripts/checks/check_disposition_totality.py` | edit **only if** the new field breaks it |
| `fixtures/run_brief/` | create — configs + expected briefs + `verify_run_brief.py` |
| `docs/TECH_SPEC.md`, `docs/OPEN_RULINGS.md` | edit |

### Acceptance

The task is done only when all of these are true.

1. `run_brief.md` is produced by every Generate run, at the run workspace root.
2. Each of the four blockers is detected, named in the Brief, and prevents G0 from being recorded.
3. Each of the five warnings is detected and named, and does **not** prevent G0.
4. A clean configuration produces a Brief with `BLOCKERS 0 · WARNINGS 0` and one line per source,
   each naming the stage that will read it.
5. The disposition→consumer relation is **read from data**; grep confirms no hardcoded disposition
   list inside `run_brief.py`.
6. G0's `decisions.jsonl` entry records the warning count accepted.
7. `python core/scripts/build_checks.py` is green — including overlay parity and disposition totality.
8. The full sweep is green: every `fixtures/**/verify_*.py`.
9. The registry is re-published, so future runs hydrate the change.

### Proof

`fixtures/run_brief/` holds one configuration per case and its expected Brief:

- `clean` — no blockers, no warnings
- `dead_source` — a source whose disposition has no consumer
- `no_requirement` — blocker 1
- `missing_profile` — blocker 2
- `unknown_disposition` — blocker 3
- `unpinned_sha` — blocker 4
- `no_code` — warning 2, and assert the Brief names all four downstream consequences
- `exemplar_no_target` — warning 4

`verify_run_brief.py` runs each, compares against the expected Brief, and asserts that G0 is
refused for every blocker case and permitted for every warning case. It must be runnable standalone
and must stay green.

---

## [ ] TASK-V2-002 — the Ingest Report: make Stage 1 quality visible before it is built on

> **Candidate** (as is everything in this catalogue). Raised in the Stage 1 review of 2026-08-14.
> Part B (the Stage 2 precondition) is **a recommendation and is separable** — Part A stands alone
> and delivers most of the value if you would rather keep the report advisory.

### Why this exists

Stage 1 sets the ceiling on every later stage. v1 can only be as good as the corpus; §16 impacts can
only be as good as the code map. It is also **the only stage whose quality no human ever reviews**.

The characteristic Stage 1 failure is not a crash — it is **under-delivery that looks like success**.
A 214-page mandate PDF that extracted 187 pages still produces a valid `.md`, a valid
`.index.json`, and a clean entry in `context_set/index.json`. Nothing in any artifact says "I lost a
quarter of this."

Because Stage 1 has no gate, the first human contact with that problem is at **G1** — where it
presents as a v1 that reads confidently and is merely *missing things*. That is the hardest failure
mode to catch, because the operator is reviewing fluent prose with no signal pointing back at
ingest.

**Three signals are being computed and then discarded:**

1. **The vision fallback is silent.** `pdf_extract` is "vision → Markdown, text fallback." A
   fallback firing is a quality event: the primary path failed and output now comes from the
   degraded one. For a table-heavy rate mandate, text fallback flattens exactly the structure that
   carries the meaning.
2. **Index quality is downstream of extract quality, invisibly.** `doc_index` derives structure
   deterministically from headings — the right design — but a document that extracted with weak
   heading structure forces the index to split at content seams rather than section boundaries. The
   index stays schema-valid while the line ranges later stages pull stop aligning to real sections.
3. **The code map's `purpose` text is unverified.** The skeleton is deterministic and checked by
   `check_map_totality.py`. The model-written `purpose` — which is what the enrichment arm reads to
   decide where an assertion lands — is checked by nothing.

**And a fourth gap the same instrumentation closes.** Test coverage of the doc lane is inverted:
`fixtures/pdf/verify_pdf_text.py` proves the *deterministic text reader* — which is the **fallback** —
while `pdf_vision.py` and `gpt_vision_client.py`, the **primary** path that runs on every document,
have no verify script at all. Vision is also the only part of ingest that can break from outside the
repository: it depends on an endpoint, a pinned model, a bundled certificate and a quota, none of
which are under version control. The code will be untouched and correct on the day it stops working,
and its failure mode is the silent downgrade described in signal 1. Part C addresses this.

This task emits **`ingest_report.md`** at fan-in: one page stating what was actually ingested and
what silently degraded, at the moment it is still cheap to fix.

### Step 1 — ~~reconcile with `check_discovery_adequacy.py`~~ **ANSWERED 2026-08-23: it measures something else**

> **This task does not shrink.** `check_discovery_adequacy.py` is a **build-time set-cover check** —
> *does every `must_capture` have an eliciting question, via `probe_if_missing.elicits`?* — tiered so
> that discovery-primary sections (§9/§12/§13) **must** be elicited (error), operator-fed sections
> should be (warning), and derived sections (§1/§16/§17/§18) have no probes by design.
>
> That is a property of the **SI profile**, not of the **corpus**. Nothing in it measures whether the
> documents that arrived were any good. **Corpus quality remains unmeasured**, which is what this task
> exists to fix. Proceed with Part A as written.

### Step 1 (superseded) — reconcile with `check_discovery_adequacy.py`

`core/scripts/checks/check_discovery_adequacy.py` and its design doc
`docs/design/discovery-adequacy-assessment.md` may already measure part of what this task proposes.
**No code is written until this reconciliation is done and recorded.** Building a second,
disagreeing measurement of ingest quality is a worse outcome than not building this task at all.

Read both files in full, then produce a metric-by-metric reconciliation covering, at minimum:

| Metric proposed here | Already computed by the check? | Does it block or only report? | Decision |
|---|---|---|---|
| Page reconciliation (pages in vs extracted) | | | reuse / extend / build |
| Fallback firing + page count | | | |
| Heading density | | | |
| Index entries per document | | | |
| Purpose coverage on the code map | | | |
| Files discovered vs classified | | | |
| Zero-byte / empty-extract detection | | | |

Apply these rules to the Decision column:

- **Reuse** where the check already computes the metric — `ingest_report.py` reads the check's
  output and renders it. It must **not** recompute the value independently. Two components
  computing the same quantity will eventually disagree, and then neither can be trusted.
- **Extend** where the check computes something close but not sufficient — add to the check, and
  have the report read it. Keep the measurement in one place.
- **Build** only where the check does not cover the metric at all.

**Two integration questions that must be answered in writing, because they change Part B:**

1. **Does `check_discovery_adequacy.py` already block anything?** If it is already a hard gate on
   ingest, then Part B's Stage 2 precondition is partly redundant, and the two must be reconciled
   into a single refusal path rather than two independent ones. An operator facing two different
   stop conditions with two different messages is worse off than facing one.
2. **Is the check run at Stage 1, or only as part of `build_checks.py`?** A §10 build check that
   validates the *tool* is a different thing from a per-run check that validates *this corpus*. If
   it is build-time only, its metrics may not be available per-run at all, and "reuse" may not be
   possible even where the logic exists.

**Record the outcome** as a dated addendum section in `docs/design/discovery-adequacy-assessment.md`
titled *"Reconciliation with the Ingest Report (TASK-V2-002)"*, carrying the completed table and the
answers to both questions. That file is the natural home — a future reader arriving at either
component finds the relationship to the other. Summarise it in the commit message as well.

**If the reconciliation shows the check already covers most of this**, say so and stop: the task
shrinks to "surface what the check already knows in `ingest_report.md`," and Parts A.1–A.3 below
should be cut down accordingly rather than implemented as written.

### Depends on

Confirm each exists before starting; if one is missing, stop and report it.

- `core/scripts/merge_manifest.py` — the fan-in, and where the report is emitted
- `core/scripts/doc_index.py`, `core/skills/doc_index.skill.md`
- `core/profiles/payment_brand/adapter/pdf_extract.skill.md` — where the fallback is decided
- `core/scripts/pdf_vision.py`, `core/scripts/pdf_text.py`
- `core/scripts/code_map_build.py`, `core/scripts/checks/check_map_totality.py`
- `core/retrieval_config.yaml` — the existing home of doc-lane tunables
- `core/scripts/checks/check_discovery_adequacy.py`
- `overlays/claude/prompts/start-si.md`, `overlays/copilot/.github/prompts/start-si.prompt.md`

### Reads

- `core/scripts/checks/check_discovery_adequacy.py` — **in full**, for Step 1
- `docs/design/discovery-adequacy-assessment.md` — **in full**, for Step 1
- `docs/TECH_SPEC.md` — the run-workspace layout, and the `context_set/index.json` contract
- `core/scripts/merge_manifest.py` — what data is already in hand at fan-in
- `core/profiles/payment_brand/adapter/pdf_extract.skill.md` — whether the fallback is per-page or
  per-document. **This determines whether page reconciliation is nearly free or needs new plumbing**
- `core/retrieval_config.yaml` — the existing tunables and their format

---

### Part A — `ingest_report.md` (the core of this task)

Emitted by `merge_manifest.py` at fan-in, written to the run workspace root beside
`context_set/`. Deterministic; no model involvement; no network calls.

#### A.1 The three metrics that matter

**Page reconciliation** — for every paginated source: pages in the source versus pages successfully
extracted, and how many arrived via fallback. This is the single most valuable line in the report
and the direct detection of the failure this task exists for. The information already exists —
vision iterates rendered pages and knows which succeeded — it is simply not retained.

**Heading density** — headings per thousand lines of extract, per document.

> Use density, **not** index-entry size. `max_entry_lines` forces splits regardless of document
> quality, so entry size measures the config rather than the document. Density is what actually
> separates "long but properly sectioned" from "wall of text the index had to guess at."

**Purpose coverage** — how many code-map components carry `purpose` text, and which do not. A weak
check by design: it asserts existence, not quality. It is cheap and strictly better than nothing.

#### A.2 Thresholds live in config, never in code

Add an `ingest_report:` block to `core/retrieval_config.yaml` (it already owns doc-lane tunables
such as `max_entry_lines`). If on reading it that file proves narrower in scope than expected,
create `core/ingest_thresholds.yaml` instead and say so in the commit message.

At minimum: the heading-density floor, and the fallback-page count above which a warning is raised.

#### A.3 Blockers and warnings

**Blockers** — Stage 2 would be built on nothing:

1. A source staged zero bytes.
2. A paginated source with a known page count extracted **zero** pages.
3. A source carrying a requirement-bearing disposition produced an empty extract.

**Warnings** — the run proceeds, degraded:

1. Any fallback fired at all. Report the page count and, where pages are contiguous, the range — a
   contiguous block usually means a scanned or heavily tabular section.
2. Heading density below the configured floor.
3. Any code-map component with no `purpose` text — name them.
4. A source staged successfully but produced no index entries.

#### A.4 Required output shape

Written to be scanned in ten seconds, verdict first. This is the target:

```
INGEST REPORT — discover_interchange_debt_repay
2026-08-15 09:14 · domain payment_brand · registry a3f9c21 · tool copilot
7 sources configured · 7 staged · corpus 12,544 lines indexed

BLOCKERS 0 · WARNINGS 3          →  Stage 2 may proceed
─────────────────────────────────────────────────────────────────────────────

DOCUMENTS

  interchange_debt_repay_spec.pdf                       business_requirement
    pages       31 in  →  31 extracted            vision · no fallback
    structure   24 headings / 1,240 lines (1 per 52)  →  38 index entries
    ok

  mastercard_mandate_part1_2026.pdf                product_domain_knowledge
    pages      214 in  →  187 extracted           vision · 27 pages fell back
    structure   61 headings / 7,240 lines (1 per 119) →  142 index entries
    WARN        27 pages via text fallback — contiguous block, pages 88-114

  discover_routing_kb.html                         product_domain_knowledge
    structure    2 headings / 384 lines (1 per 192)   →  17 index entries
    WARN        heading density below floor (1 per 150)

  AIP_Description_Discover_Spec.csv                       reference_table
    rows       412 in  →  412 parsed              deterministic · csv
    ok

CODE

  stratus-core @ feature/interchange_debt_repay
    commit      7e1a44c            cache MISS (profile_sha changed)
    gate        branch 1 — extractor and profile both present, map built
    extract     C via tree-sitter · 1 partition
    files       418 discovered  →  418 classified        totality ok
    map         23 components · 1,106 edges
    purpose     19 of 23 components described
    WARN        4 components carry no purpose text

─────────────────────────────────────────────────────────────────────────────
WARNINGS

  1  mastercard_mandate_part1_2026.pdf — 27 of 214 pages extracted by text
     fallback because vision returned no content. Pages 88-114 are contiguous,
     which usually means a scanned or heavily tabular section. Text fallback
     flattens table structure, and this is a rate-table mandate — v1 will be
     written from degraded text for that span.

  2  discover_routing_kb.html — 2 headings across 384 lines. The index has to
     split at content seams rather than at section boundaries, so line ranges
     pulled by later stages will not align to real sections.

  3  Code map — settlement/, errors/, vendor/stratus/ and config/feature_flags
     have no purpose text. Enrichment reads purpose to decide where an assertion
     lands, so assertions touching these components are less likely to match.

Accepting these warnings is recorded in decisions.jsonl.
```

A warning must always name **the downstream consequence**, not just the measurement. "27 pages fell
back" is a number; "v1 will be written from degraded text for that span" is why anyone should care.

The blocker form:

```
BLOCKERS 2 · WARNINGS 1          →  Stage 2 is BLOCKED
─────────────────────────────────────────────────────────────────────────────
  1  interchange_debt_repay_spec.pdf — 31 pages in, 0 extracted. Vision failed
     on every page and no text layer was found. This is the business_requirement
     source; Stage 2 has nothing to write from.

  2  discover_routing_kb.html — staged 0 bytes. Fetch returned 200 with an empty
     body, most likely an auth redirect to a login page.
```

---

### Part B — the Stage 2 precondition (recommended, separable)

**Recommendation:** `/start-si` refuses to run while `ingest_report.md` carries blockers, and opens
by presenting the report's summary when it does not.

**Why a precondition rather than a sixth gate.** Stage 1 genuinely has nothing to *approve* — it
produces context, not claims — and the five-gate model is load-bearing in how this system gets
explained. A precondition gets the protection without changing the gate model or the safety
narrative, and it reuses the mechanism TASK-V2-001 introduces for G0.

**Why not advisory-only.** A report sitting beside a step that proceeds regardless is a report
nobody reads. The two blocker cases above are both states where Stage 2 cannot produce anything
sound, and letting it run wastes a stage and produces a confident, empty v1.

**If Part B is dropped:** implement Part A alone, and still surface the summary at the top of
`/start-si` so the operator sees it before authoring. Both overlay prompt files must change
identically — `check_overlay_parity.py` must stay green.

---

### Part C — the vision smoke test (separable; small, and mostly free)

`fixtures/pdf/verify_pdf_vision.py` — sibling to the existing `verify_pdf_text.py`, running against
the `mastercard_mandate_part1_2026.pdf` already sitting in that directory.

It depends entirely on the per-page outcome tracking Part A.1 requires from `pdf_vision.py`, so it
is additive rather than new work: Part A builds the instrumentation, Part C asserts on it.

#### C.1 What it asserts

**Structural — deliberately says nothing about model output:**

1. Pages in the PDF equals pages extracted.
2. The fallback counter is **zero**.
3. Every page produced non-empty output.

Vision output is non-deterministic, so exact-match assertion is impossible — that is presumably why
no fixture exists today. It is also unnecessary. These three assertions do not test *what* the model
said; they test that the vision path **succeeded**, which is fully deterministic and catches the
entire class of external failure: credentials rotated, endpoint moved, certificate expired, quota
exhausted, model version retired.

**Invariant strings — proving it read the page rather than answering fluently:**

4. A small set of known strings appears somewhere in the extract.

Store them in `fixtures/pdf/vision_invariants.json`, keyed by document, so strings can be added
without touching code. Choose 3–5 per document by reading the PDF, against three criteria: the
string is certainly present; it is semantically meaningful (a designator, a rate, a table header);
and **a model producing plausible filler would not emit it by chance**. That last criterion is the
one that matters — a specific IRD code is a good invariant, the word "interchange" is worthless
because any hallucinated text about a mandate would contain it.

This upgrades the claim from *did it respond* to *did it respond usefully*, and is the only part of
Part C that catches soft degradation — an endpoint that starts returning fluent but mangled output
while every structural assertion still passes.

#### C.2 Skip versus fail — get this right or the test gets disabled

The script must distinguish two different negatives:

- **Vision credentials absent → SKIP**, printing a loud line naming why. An environment that was
  never going to run vision must not break the full fixture sweep.
- **Credentials present, call fails → FAIL.** This is the signal.

Without that distinction the test either reddens the sweep everywhere or gets quietly commented out
by whoever hits it first.

#### C.3 The docstring must explain why this file is different

State plainly, in the file itself: **this is the only verify script in the repository that can go
red with no code change, and that red is the entire point** — it means the endpoint, model,
certificate or quota moved underneath the build. It is a monitor wearing a test's clothing.

Without that note, the next person to see it fail will "fix" it by loosening the assertion, which
converts the one thing watching an external dependency into decoration.

---

### Creates / edits

| Path | Action |
|---|---|
| `core/scripts/ingest_report.py` | create — the report builder |
| `core/scripts/merge_manifest.py` | edit — emit the report at fan-in |
| `core/scripts/pdf_vision.py` | edit **only if** per-page outcomes are not already retained |
| `core/retrieval_config.yaml` | edit — add the `ingest_report:` threshold block |
| `overlays/claude/prompts/start-si.md` | edit — surface summary; refuse on blockers (Part B) |
| `overlays/copilot/.github/prompts/start-si.prompt.md` | edit — identically |
| `fixtures/ingest_report/` | create — cases + expected reports + `verify_ingest_report.py` |
| `fixtures/pdf/verify_pdf_vision.py` | create — the smoke test (Part C) |
| `fixtures/pdf/vision_invariants.json` | create — per-document invariant strings (Part C) |
| `docs/design/discovery-adequacy-assessment.md` | edit — **Step 1 addendum (required)** |
| `core/scripts/checks/check_discovery_adequacy.py` | edit **only if** Step 1 decided "extend" |
| `docs/TECH_SPEC.md` | edit — add `ingest_report.md` to the workspace layout + its contract |

### Acceptance

0. **Step 1 is complete before any code exists.** The reconciliation table is filled in for every
   listed metric, both integration questions are answered in writing, and the addendum is committed
   to `docs/design/discovery-adequacy-assessment.md`. No metric is computed in two places: for every
   row marked *reuse*, `ingest_report.py` reads the check's output rather than recomputing it, and a
   reviewer can confirm that by reading the two files side by side.
1. `ingest_report.md` is produced by every `/start-ingest` run, at the run workspace root.
2. Page reconciliation is reported for every paginated source, including the fallback page count.
3. Heading density is reported per document and compared against the configured floor.
4. Purpose coverage is reported, naming every component without `purpose` text.
5. All three blockers are detected and named; all four warnings are detected and named.
6. Every warning states its downstream consequence, not only its measurement.
7. Thresholds are read from config — grep confirms no numeric threshold literal in
   `ingest_report.py`.
8. **Part B only:** `/start-si` refuses to run while blockers exist, and the accepted warning count
   is recorded in `decisions.jsonl`.
9. `python core/scripts/build_checks.py` green, including overlay parity.
10. Full `fixtures/**/verify_*.py` sweep green.
11. Registry re-published.
12. **Part C only:** `verify_pdf_vision.py` passes with credentials present, **skips loudly** with
    credentials absent, and fails if the vision call errors or any invariant string is missing. Its
    docstring states that a red result with no code change is the intended signal, not a flake.

### Proof

`fixtures/ingest_report/` holds one case per condition with its expected report:

- `clean` — no blockers, no warnings
- `partial_extract` — the headline case: pages in ≠ pages extracted, contiguous fallback block
- `zero_extract` — blocker 2
- `zero_bytes` — blocker 1
- `empty_requirement` — blocker 3
- `weak_headings` — warning 2
- `missing_purpose` — warning 3

`verify_ingest_report.py` runs each, compares against the expected report, and asserts Stage 2 is
refused for every blocker case and permitted for every warning case. Runnable standalone; must stay
green.

---

## [ ] TASK-V2-003 — change-type framework, multi-repo, and history-driven classification

> **Candidate, and a framework rather than a spec.** This is the umbrella for the target state above, broken into
> sub-tasks sized to be picked up **one at a time over months**. Each sub-task below carries scope,
> dependencies and a deliverable — **not** the full Depends-on / Reads / Acceptance / Proof detail
> that TASK-V2-001 carries. Expand a sub-task into a full spec at the point you pick it up, not now;
> writing ten full specs against a design that will move is waste.

### Sequencing principle — value must not depend on the KB

The waves are ordered so the **change-type framework works end to end with operator declaration
alone** (Waves 1–2). The historical KB (Wave 4) then *upgrades* declaration from an instruction to a
hypothesis it tests. If the KB never gets built, everything through Wave 3 still stands and still
delivers. Do not make Waves 1–2 depend on Wave 4.

**Run Waves 1–3 for real before designing Wave 4 in detail.** Wave 4 is currently specified against
assumptions about outputs that do not exist yet. Real runs will answer questions that change its
design: whether §16 actually bloats across five repos and by how much, whether four change types is
the right cut or two of them never fire, and whether engine granularity matches how impacts really
land. Measurements first, then design — and 003.7a is the gate that enforces it.

---

### Wave 1 — foundation (do these first; both are cheap)

**[ ] 003.1 — The section consumption map** · *analysis only, no code*

For each of the 18 sections in `si_profile.payment_brand.yaml`, list every consumer: mappings in
`jira_template.payment_brand.yaml`, reads by the enrichment arms, reads by
`solution_intent_validator.py`, `must_capture` rules, references in the instruction template.

Classify each section as **base** (every payment-brand change needs it), **type-specific** (belongs
in a package), or **orphan** (no reader — cut). Deliverable: a table in
`docs/design/si-section-consumption.md`.

*Nothing else in this task can be scoped correctly until this exists — it defines what "base" means.*

#### 003.1a — the §16 / §INT-n split (decided 2026-08-20; V's model)

The draft put `sections: [INT-n]` on **every** pass, including the generic arm — which made §INT-1 a
duplicate of the §16 entries the same findings already produce. That is the *"two lists"* Part G.3a
rejects, arriving through a different door. **The rule, in three lines:**

| Pass | Writes |
|---|---|
| Generic arm (`stratus_code`) | **§16 only.** No `sections:` key at all |
| Specialised reader (`pricing_impact`, `qualification_impact`) | **§16** *and* its §INT-n |
| `release_shape` | **§INT-4 only** — a release verdict is not an impact |

**Every impact reaches §16, whoever found it.** Part G.3a settles this: *"§16 is what `jira_validator`
traces both ways. A second home means a second spine."* If a specialist's impacts lived only in
§INT-5, §INT-5 would need its own Jira mapping, its own validator path, its own traceability —
everything §16 already does, built twice. So §INT-n never carries impacts.

**Type sections carry a contract, on the pass** (decided 2026-08-22). A base section declares
`title`, `authored`, `touch`, `status`, `classes`, `must_capture` and `probe_if_missing`; a type
section was **an id in a list**, so nothing said what §INT-3 must contain and nothing scored whether
it did. Four of those fields stay absent *correctly* — `classes` (authored from findings, not routed
documents), `probe_if_missing` (not elicited), `authored` (always v2_only) and `status` (derivable
from whether the pass ran, so rule 8 forbids restating it). The two that were missing are now
required: **`title` and `must_capture`**, declared inline on the pass so the rule *"sections are
declared on the pass that produces them"* still holds and no `sections.yaml` reappears.

> **The rule that makes the split enforceable: a type section's `must_capture` may never require
> anything reducible to a located impact.** If it names a file and a change, it belongs in §16.
> §INT-n holds only what is *not* a story. Without this, a specialist can write a rich §INT-5
> narrative, file no §16 impacts, and the qualification work vanishes from the Jira plan entirely —
> the same failure Part G exists to prevent for gaps.

**Which leaves §INT-n a different job: the specialist's *context*.** The pricing picture (current vs
target rates per mnemonic); where qualification criteria are defined and how this change moves them.
The test is one line:

> **If it would become a Jira story, it belongs in §16. If it is context a human needs to understand
> the change, it belongs in §INT-n.**

**Three things this resolves for free:** §INT-2's orphaning (from dropping `peoplesoft_code`) stops
mattering, because nothing needs a per-application type section; an application entering scope by
crossing has an obvious destination, §16, like every other impact; and the routing question —
*how does a finding know which section it belongs to* — mostly disappears, because impacts do not
need attribution. Only a specialist's context findings do, and they inherit their pass's `sections:`.

**A second question, same shape: where do non-impact findings *render*?** A scope finding
(005 Part E) has a fully specified **behaviour** — escalate naming all three candidate causes, block
G2 until resolved, never auto-correct the requirement — but no stated **destination in v2**. Under the
split above it is not an impact (not §16) and not specialist context (not §INT-n). Same for boundaries
and for `release_shape`'s non-event.

> **Partly answered by the artifact itself** (read 2026-08-21, `core/profiles/payment_brand/si_profile.payment_brand.yaml`).
> **§17 Open questions** — `authored: v1_extended_in_v2` — already claims one of these:
> *"In v2: every finding the operator deferred at the walkthrough, with why it could not be resolved."*
> **§18 Verification summary** — `authored: v2_only` — is *"A SUMMARY, NOT A LEDGER. Counts only —
> N checked, X confirmed, Y corrected, Z unverifiable"*, which also makes it the natural home for
> 005 Part H. So the remaining question is narrow: **a scope finding that is escalated and
> *resolved* — does it render anywhere, or does resolving it dispose of it?** Only a *deferred* one
> has a stated home.

**A third question: what contract does a type section carry?** The asymmetry is stark — a base section
declares `title`, `authored`, `touch`, `status`, `classes`, `must_capture` and `probe_if_missing`; a
type section is **an id in a list** (`sections: [INT-3]`). Three of those are correctly absent (`classes`
— authored from findings, not routed documents; `probe_if_missing` — not elicited; `authored` — always
v2_only). But **no `title` and no `must_capture`** means nothing states what §INT-3 must contain and
nothing scores whether it did. The pass's own `must_capture` does not substitute: that is an obligation
about *searching* ("every program code has its criteria located"), not about what the section must say.
Decide whether the contract hangs off the pass or sits in a small per-type section block beside the
flow — and note that whichever is chosen, `jira_template` needs it too, since nothing currently says
which of the four Jira levels a type section maps to.

**Resolved 2026-08-22 — a tabular impact must be able to become a story.** The gap ran the whole
length of the pipeline: `pricing_impact` reads `peoplesoft.rate_tables`, a **pure rate change touches
no code anywhere**, and Stage 4's `story_classification` requires *exactly one* of `code_location |
new_build | non_code` — with `non_code` defined as *"certification packages, filings, runbooks…
derived from a §7 deliverable"*. So the case the `tabular` substance exists to make visible had no
valid story shape and tripped `forbidden: "a story with neither a code_location nor a flag"`. Three
edits, no new vocabulary:

| Where | Change |
|---|---|
| **§16 `location`** | gains a tabular form — `peoplesoft.rate_tables[mnemonic=VP5X]`, qualified `found` like any other |
| **`jira_template` `non_code`** | widens from *"a §7 document"* to **"work with no code location"** — certification, filings, runbooks, **and data or table changes** |
| **`jira_template` `evidence`** | decouples from the flag: a §16 entry id **or** a D-id, independent of `non_code`. The old wording (*"or the D-id for non-code work"*) hard-wired non_code ⇒ §7, which is wrong — a rate story traces to §16 |

**No `rate_change` flag**, deliberately. The story already points at its §16 entry, whose `location`
says `peoplesoft.rate_tables[…]` — so a flag naming the *kind* of non-code work would restate what
following the evidence pointer already tells you. That is schema rule 8. It would also be too narrow:
a second `tabular` substance would need a second flag, enumerating substances in a file that should
not know about them. Where a story genuinely must be findable by type inside Jira without opening the
SI, that is a **label** (a controls concern), not a schema value.

Worked shape, from the qualification-plus-rate case:

```
Epic    ← §8      raise interchange for fee program X
  Story ← §16.2   qualification criteria      code_location: qual_rules.c:340-380
  Story ← §16.4   update rate table for VP5X  flag: non_code   evidence: §16.4
```

**One question this opens, and 003.1 must answer it.** §16 entries are anchored to
`location: file:line`. But `pricing_impact` reads a **tabular** substance, and the entire point of that
row is that *a pure rate change touches no code anywhere* — a rate-table row is not a `file:line`.
Part G.3a already loosened `location` once, adding `found` / `prospective` / `undetermined` qualifiers
so gaps could live in §16. A tabular impact needs the same accommodation — a table-and-key location
form — or rate changes cannot enter the spine at all, and you are back to a second home for exactly
the case the substance axis was introduced to make visible.

**Reads** — `core/profiles/payment_brand/si_profile.payment_brand.yaml` (all 18 sections and their
`must_capture`) · `core/templates/payment_brand/jira_template.payment_brand.yaml` (which sections each
Jira level consumes) · `core/scripts/solution_intent_validator.py` · **003.1a below**, which is the
ruling this analysis must apply, not re-open.

**Creates / edits** — create `docs/design/si-section-consumption.md`. **No code, no YAML.**

**Proof** — the table itself: every one of the 18 sections classified **base**, **type-specific** or
**orphan**, each with its reader list. A section with no reader and no justification is the finding
this task exists to produce.

---

**[ ] 003.2 — Declare the estate, and the interchange flow** · *foundation for everything in Stage 3*

Declaration files, no behaviour change. **Describe what happens today; change none of it.**

- `core/estate/applications.yaml` — what applications exist and **what each is made of**. Every
  application is **code-first**: Stratus (`acquired: true`), PeopleSoft and Tandem declared with
  `acquired: false` until their repos arrive. `tabular` and `file_layout` substances are declared
  alongside `code`, never instead of it.
- `core/estate/interfaces.yaml` — MPT, PTI Gen, submission as **`parties` with roles**, each carrying its
  read/write site and its layout location. Declaration is the only option (nothing in source links the
  two sides) and it is cheap, because a file-based estate has a small, static, enumerable interface set.

  > **Every PeopleSoft-side path in the worked example is a placeholder.** The repo is not acquired, so
  > `writes_at` and `layout_at` for the MPT producer are `[TBD]` and the backward crossing lands as a
  > **recorded boundary**. Getting the repo upgrades boundaries into located findings; it does **not**
  > gate this task — the Stratus side is real and declarable today, and `acquired: false` is the state
  > 003.10a's fixture is built to prove. **Two things to establish when the repo arrives:** the real
  > per-side layout paths (they must differ from the consumer's C header), and whether PeopleSoft's
  > record layout lives in a **file at all** — if it is an Application Designer record definition or
  > PeopleTools metadata rather than source, `layout_at: <path>` cannot address it and the field needs a
  > second addressing form. Establish that before building the layout parser, not after.
- `core/profiles/payment_brand/change_types/interchange/flow.yaml` — the **floor**, plus the resolve /
  impact / release_shape phases as they run today, with `probes.yaml` beside it. Move
  `interchange_enrich.skill.md` and `interchange_networks.yaml` in as `resolve_mnemonic.skill.md` and
  `networks.yaml`.
- `core/profiles/payment_brand/change_types/authorization/flow.yaml` — the **minimal second type**, so
  the type-union, empty-`resolve` and empty-`release_shape` paths exist from day one (Target state §10).

  > **Open — is `resolve: []` the norm, or is interchange the odd one out?** Interchange needs a resolve
  > phase because the networks publish *designators* and our systems key on *mnemonics*, with Stratus as
  > the only dictionary. **Nobody has checked whether clearing has an equivalent external→internal
  > vocabulary gap.** It decides how the phase is understood: if clearing also needs one, `resolve` is a
  > **general pattern** and the third and fourth types will each need their own dictionary declared. If
  > it does not, interchange is **unusual** and `resolve: []` is the normal case — which makes
  > `authorization` genuinely representative rather than a stub. Cheap to answer, and worth answering
  > before a third type is designed.

**The interchange floor is deliberately narrow (decided 2026-08-19/20): Stratus code, resolve, and the
MPT interface — and nothing else.** Everything PeopleSoft is probe-activated (`pricing_impact`, INT-P2)
and PeopleSoft's *code* is not a declared pass at all — it arrives only by crossing. Three consequences
to build against, not discover:

- **PeopleSoft is always *reached*, never fully *scanned*.** The MPT floor entry assesses the interface
  against both declared layouts every run, so crossing always arrives at PeopleSoft and always files at
  least a boundary — it can never drop out of the report silently. What varies is depth: its `code` is
  never scanned (unacquired, and no declared pass), and its `rate_tables` are read only when INT-P2
  fires, with the non-activation recorded and cited when it does not.
- **`{ interface: mpt }` is back in the floor (decided 2026-08-20), and it is load-bearing.** It is the
  only thing that invokes the **direct-layout assessment** — the interface parsed against both declared
  layouts with no code hit required. Without it the backward case (*Stratus needs an eligibility field
  MPT does not carry*) is structurally uncatchable, because a field that does not exist yet has no read
  site for an impact to land on. Compare cannot substitute: it only ever judges what `cross` hands it,
  so with nothing crossed it returns a null that reads exactly like a clean bill of health.
- **PeopleSoft is deliberately *not* floored.** When MPT is impacted, closure pulls PeopleSoft in — that
  is the crossing rule doing its job, and flooring it as well would be redundant. It would also create a
  floor entry naming an unacquired `code` substance: a guarantee dischargeable only by a boundary.
- **§INT-2's orphaning is moot under 003.1a.** It belonged to `peoplesoft_code`, but under the
  §16/§INT-n split no pass needs a per-application type section: a PeopleSoft impact arriving by
  crossing goes to **§16**, like every other impact. The pass-synthesis gap in 003.5 still stands for
  *id* and *denominator*, but no longer for *section*.

Interchange is the reference implementation every later type is modelled on. Sections are declared **on
the pass that produces them** — there is no separate `sections.yaml`. Behaviour must be identical after
the move; `verify_interchange_enrich.py` is the proof.

**Deliver a schema alongside the files, not just the files.** The declarations are only load-bearing if
malformed ones fail loudly. `verify_estate.py` proves each rejection, and `flow_plan.py` refuses to
return a plan when any of them holds:

1. `provides` restricted to an **identifier vocabulary** — a pass cannot declare a conclusion
2. `needs` resolvable against some pass's `provides` at load time
3. `floor` entries resolvable against `applications.yaml` and `interfaces.yaml`
4. every `activates:` naming a **pass that exists**
5. `search.scope` required on every pass
6. every interface **`parties[].system` resolves to an application id** *(added 2026-08-22 — `settlement` was a party with no application entry)*
7. every `floor` entry **discharged** by a pass or a generic mechanism — resolvability is not enough
8. **no derivable duplication** *(added 2026-08-22)* — see below

**Rule 8 — a field whose value is derivable by following a declared id is a schema violation, not a
convenience.** Three instances appeared within two days, each looking like helpful local context and
each a second place for one fact to drift: `activated_by:` on a pass (derivable from `activates:`),
`acquired:` on an interface party (derivable from the application), `profile: "[TBD]"` (derivable from
`acquired: false`). A rule already existed for the probe case and the pattern still recurred twice —
which is the argument for a schema check rather than vigilance. It is also the rule with the longest
reach: it protects every file added later, not only those that exist today.

> **Two capabilities specified here have no executable case in the current estate** (noted
> 2026-08-22). Neither is broken; both need a **synthetic** fixture, and nobody should assume the
> real declarations exercise them.
>
> - **The topological sort.** No impact pass declares `provides:`, so interchange has zero inter-pass
>   dependencies — all three hang directly off resolve and parallelise. The sort has nothing to sort;
>   a fixture must build a multi-level graph that exists in no real flow.
> - **Layout drift detection.** Every declared interface has exactly one **acquired** party, because
>   Stratus is the only acquired repo and sits on one side of `mpt`, `pti_gen` *and* `submission`. A
>   two-sided layout comparison cannot run on anything today, so the fixture must supply both sides.

> **Carve-out, or the rule eats the floor.** `floor` deliberately restates pass targets — that is
> **double-entry bookkeeping**, not duplication: the obligation is declared independently of the
> machinery so that deleting a pass fails loudly (rule 7) instead of silently deleting the coverage.
> Rule 8 rejects **derived field values**; it must never reject an **independent declaration that
> happens to overlap**. The test: could the two disagree in a way worth catching? Floor vs passes —
> yes, catch it. `activated_by:` vs `activates:` — no, one is simply a stale copy of the other.

**`floor` takes three forms, and every entry must be *discharged*.** `{application, substance}`,
`{interface}`, and `{phase, application}`. Resolvability is not enough — the schema must also reject a
floor entry that **nothing discharges**: no pass covers it, and no generic mechanism (crossing, release_shape)
covers it either. Without that rule the floor is a comment that restates the pass list, and deleting a
pass silently deletes the obligation along with it — which is the exact degradation *"a floor, never a
ceiling"* exists to prevent. Correspondingly, **the G2 totality denominator is realised scope, not
declared scope**: an application that entered by KB union or by crossing is counted too, or it can be
scanned, find nothing, file nothing, and pass the silence check.

> **First, confirm the suspected defect** (Target state §6): does `start-enrich` currently run the arms
> *before* `interchange_enrich`? If so the arms search Stratus in the **network's vocabulary** rather
> than by mnemonic, and putting resolve first is a fix rather than a reorganisation. Record the finding
> either way.

---

**Reads** — `vdi_tree.md` (ground truth for paths) · `core/code_profiles/*.profile.yaml` · **Target
state §2** (the estate model, substances, crossing) and **§3** (the flow) · `core/profiles/payment_brand/interchange_enrich.skill.md`
and `interchange_networks.yaml`, both of which move in this task.

**Creates / edits** — create `core/estate/applications.yaml`, `core/estate/interfaces.yaml`,
`core/profiles/payment_brand/change_types/interchange/{flow.yaml,probes.yaml}` and
`change_types/authorization/flow.yaml` · move `interchange_enrich.skill.md` → `resolve_mnemonic.skill.md`
and `interchange_networks.yaml` → `networks.yaml` · create the schema and `fixtures/estate/verify_estate.py`.

**Proof** — `verify_estate.py` proves **each of the eight rejections** independently, and
`verify_interchange_enrich.py` stays green: behaviour must be identical after the move. A green
fixture that rejects nothing is not proof.

---

### Wave 2 — the framework working, with declared types

**[ ] 003.3 — Declare change types at Stage 0**

`UI_INPUT.yaml` gains `change_types: [...]` — multi-select in the UI, emitted by `emit.js`, validated
by `validation.py` against the packages that exist on disk (**the directory is the registry**; no
second list to drift). Empty list is legal and means base pipeline only.

Fold into the Run Brief (TASK-V2-001): show which passes will run, which sections will be added, and
warn where a package's `requires` is unsatisfied by the configured sources — *"interchange declared,
but no source carries `reference_table`; §INT-2 will be empty."*

**[ ] 003.4 — Type probes at Stage 2, and the Change Classification section in v1**

Add `probes.yaml` per package. The SI author loads probes for the declared types, **answers each from
the corpus first**, and asks the operator only what the documents leave open. Answers land in a new
**Change Classification section in v1** recording: the confirmed types, the reasoning and precedents
behind them, the probe questions, and their answers.

*This section is written at Stage 2 and is an **input to** enrichment — not to be confused with the
type sections (`§INT-1`, …) that enrichment **produces** in v2 at Stage 3, per 003.5.*

Include a probe answer of **"unknown — revisit at enrichment"**, which writes an explicit `[TBD]` into
v1 and seeds a finding for Stage 3. The question stays on the record and v1 is honestly incomplete
rather than silently incomplete.

**Probes carry `activates`.** A probe declares the **pass ids** its answer activates, in one direction
only — the pass says nothing about probes, so there is a single place to keep in sync (Target state §7). This is what makes probes load-bearing rather than decorative, and it gives a test for whether a
probe belongs in a package at all: *does the answer change what runs?* Where a probe was answered from
the corpus, the activation carries that citation — the routing decision is sourced.

A probe answered `unknown` must **not** silently leave its sub-pass unactivated: treat it as activated
(the cautious direction), or escalate. Never go quiet.

**[ ] 003.5 — The flow orchestrator: resolve → impact → cross → release_shape → consolidate**

The core of the restructure, and the largest item in Wave 2. `start-enrich` stops being a fixed
sequence and becomes an interpreter of `flow.yaml`.

**Execution.** Open scope at the **floor**, unioned with whatever the KB proposed. Load the confirmed
types' flows plus probe-activated passes. Run **resolve** first — external vocabulary becomes internal
identifiers — and **enforce its `provides` contract before starting anything that needs it**. Then
**impact**, every pass whose `needs` are satisfied, in an order **derived by topological sort, never
hand-written**; parallel wherever `needs` is empty. Then **cross** (below). Then **release_shape**. Then
consolidate.

**`needs` names identifiers, matched against `provides`.** Not pass ids. A `needs` naming something
nothing provides is a **load-time config error**, not a pass that silently runs empty — and `provides`
is restricted to an identifier vocabulary, which is what makes *join keys forward, never conclusions*
mechanically enforceable rather than a convention. (`activates:` is the one key that *does* name a pass
id, because "which pass runs" is genuinely its question. The two vocabularies never mix.)

**The plan is computed, never reasoned — `core/scripts/flow_plan.py`** (decided 2026-08-22). The
orchestrator is an agent, but **it must not derive the run order itself.** A wrong sort is invisible:
a pass started before its identifiers exist scans an empty key set, files fewer findings, and *every
G2 check still passes* — floor totality, findings-or-non-event, all green. The only symptom is fewer
§16 entries, which is indistinguishable from a change that genuinely touches less. That is exactly
the class the design says to compute rather than judge (*mechanical recall, model precision*).

```
flow_plan.py
  in    flow.yaml (one or more), the activated pass set, applications.yaml, interfaces.yaml
  out   • ordered waves — the execution plan, resolve barrier first
        • rejections — refuse to return a plan if any of these hold:
              · a `needs` identifier nothing `provides`
              · an `activates:` naming a pass that does not exist
              · a `floor` entry unresolvable against applications/interfaces
              · a `provides` value outside the identifier vocabulary (a conclusion)
              · an interface `parties[].system` naming no application
              · a `floor` entry nothing discharges
```

The agent **executes the returned plan and never reorders it**. Rejections are load-time failures, not
warnings — the run does not start.

*Cost note:* `check_vdi_docs.py` in the external review repo already implements the rejection half
against the doc's YAML blocks, so most of this is porting working code rather than writing new logic.
It is also the strongest seam in the restructure: the same script plans **any** flow, so a second
change type needs no new sequencing logic at all.

**Resolve is a barrier: every resolve pass completes before any impact pass starts** (decided
2026-08-20). Not fine-grained topological ordering across the phase boundary. With two resolve passes
both providing `mnemonic`, fine-grained ordering lets an impact pass start the moment the *first*
finishes — searching an **incomplete key set**, finding less, with nothing to indicate why. That is the
empty-key-set failure the `provides` contract exists to prevent, arriving through the multi-provider
door. The barrier costs almost nothing (resolve is one pass today, and nearly everything downstream
needs its output anyway) and removes the failure class outright.

**Within a phase, a pass waits for *every* provider of *every* identifier it needs, and receives the
union.** Never the first provider to finish. Otherwise the key set depends on completion order, which
is non-deterministic and unobservable in the output.

`needs:` keeps both its jobs under the barrier: it is still the **precondition contract** — resolve
having *run* is not resolve having *produced*, and a pass whose identifiers came back empty must not
start — and it still orders passes among themselves where one provides what another needs.

**`needs` sequences; it never scopes.** Every pass carries **two search obligations**: `search.keys`
exhaustively searched with each key accounted for, **and** `search.scope: full_repo` scanned unbounded.
Resolution creates a search obligation, not a search boundary. A pass that only searched its keys has
silently become a lookup.

**The estate walk is part of this orchestrator, and it is generic.** Impacts landing on a site declared
in `interfaces.yaml` promote to field-level interface impacts and cross — in **both** directions — into
the other parties' code, pulling new applications into scope for a full scan, to a fixed point. Cycle
protection on `(application, substance, field)`; boundaries at unacquired applications are **recorded,
never silent**. No change type re-declares any of this (Target state §2).

**Every pass also `reads: [v1.assertions]`.** Upstream keys narrow nothing; v1 anchors everything. This
is what keeps a **pure rate change visible** when Stratus contributes no keys, and what makes an upstream
miss *detectable* — a designator named in v1 but absent from the key set — instead of silently
truncating everything downstream.

**Applications that enter scope dynamically get a synthesised pass.** `impact:` is a static list;
scope is not. An application arriving by KB union or by crossing matches no declared pass, so the
orchestrator must synthesise one — generic skill (`code_impact_assess`), `search.scope: full_repo`, the
resolved identifiers as keys — and must give it an **id** for findings attribution, a **section** to
write to, and a place in the **G2 denominator**. None of that is specified today, which is how an
application can be scanned in full, find nothing, file nothing, and pass the silence check.

**Per-application findings files, deterministically merged.** Each pass writes its own file;
`enrichment.json` is the consolidated artifact and **every input file is retained, not consumed**. The
merge is fixed-order and **model-free**, surfacing conflicts rather than resolving them, so
`v1 + enrichment → v2` still reconstructs exactly.

Delete `interchange_enrich`'s content-sniffing self-gate — passes now run because they were declared.

Rules that carry the safety:
- **Namespaced section ids** (`§INT-1`, `§CLR-1`), never continuing base numbering — presence or
  absence of a type must never renumber anything, or every `§16` reference breaks across runs.
- **The floor is a floor, never a ceiling.** Declared coverage is a guaranteed minimum, never a search
  scope. **G2 precondition — floor totality:** every floor entry filed a finding or an explicit
  non-event. Same mechanism as assertion totality (TASK-V2-005 Part G.4) over a different population,
  so build it once.
- **Non-events are mandatory.** A pass that finds nothing writes "ran, found nothing." G2 precondition:
  every activated pass filed findings **or** a non-event. Silence is not permitted.
- **Phase totality — the third G2 denominator** (added 2026-08-22). Floor totality covers floor
  entries and non-events cover *activated passes*; **`resolve`, `cross` and `release_shape` are neither**, so
  until now a phase could run, produce nothing and pass the gate in silence. Every **declared
  non-empty phase** must file findings or an explicit non-event. An empty phase (`resolve: []`,
  `release_shape: []` in `authorization`) declares nothing and is owed nothing — the escape hatch already
  exists and needs no new machinery.

  This bites immediately rather than theoretically: with PeopleSoft unfloored, *"nothing crossed"* is
  a common interchange outcome, and today it leaves no trace at all.

  ```
  PHASES                      3 of 3 filed
    resolve                   ran · 3 designators resolved, 0 unresolved
    cross                     NON-EVENT · no impact reached a declared interface site
    release_shape             NON-EVENT · no interface assessed
  ```

  **A non-event is a record, not a decision.** The gate checks it *exists*; the operator does not
  dispose of each one. That distinction protects the walkthrough baseline (~4 decisions per run, with
  a growth tripwire in 006) — non-events are there to be readable, not actioned. And the text after
  the label is the substance: *"cross: NON-EVENT"* alone says nothing, while *"no impact reached a
  declared interface site"* says crossing ran, tested every impact against the declared sites, and
  none landed inside one.
- **Non-*activation* is recorded too** — a distinct rule. *"Qualification pass not run: probe INT-P1
  answered no, sourced from mandate §4.2."* Otherwise *we determined this isn't qualification-related*
  is indistinguishable from *nobody considered qualification*.
- **Join keys forward, never conclusions.** A pass may hand downstream *"mnemonic X, program code Y"*;
  it may never hand down *"I think MPT changes"*, which would manufacture the agreement `release_shape` exists
  to discover.
- **Mismatch guard at both levels.** Evidence of an undeclared change type escalates; so does evidence
  that a probe was answered wrongly, because a pass that never ran is otherwise invisible.

`jira_template` maps type sections when present, skips when absent, **never fails on absence**.

> **The verdict says *whether*, never *which goes first*** *(raised 2026-08-22, deferred)*. For a daily
> batch these are different constraints, and today all three come out as "integrated":
>
> - producer **adds** a field, consumer ignores it → usually backward-compatible, producer may ship first
> - consumer **requires** a field the producer does not write → **breaks immediately**; producer must ship first
> - a field's width or meaning changes → genuinely simultaneous, or the batch corrupts
>
> A release manager needs to tell those apart. **The seam is free** — the verdict is one value, so
> adding `sequence: producer_first | simultaneous` later breaks nothing. What is *not* cheap is the
> derivation rule, and with one interchange interface the operator can settle it in the walkthrough.
> **Revisit when a second interface is floored.**

**`release_shape`'s output is a release-coordination finding** — Stratus-only, PeopleSoft-only, or **integrated**
(an MPT field and its Stratus consumer must ship together, or the daily file breaks). Today nobody
learns which is which until implementation.

**Its non-event must not claim a check that did not happen.** Under phase totality it now always
files, so its wording carries weight. *"No interface fields changed"* is a claim **about MPT** — it
reads as *examined and unaffected*. When nothing crossed, nothing was examined. Required text:

> *"no impact reached a declared interface site; no interface assessed"*

Two clauses, each doing work: the promotion test ran and nothing matched, **and** therefore the
interface itself was never looked at. This is what keeps *checked and clean* distinguishable from
*never checked* — without it, phase totality produces a mandatory record that misreports.

---

**Reads** — `core/scripts/` — the current `start-enrich` sequence it replaces · **Target state §6**
(the run order) · **003.2's schema**, which `flow_plan.py` enforces · `check_vdi_docs.py` in the review
repo, which already implements the rejection half against the doc's YAML blocks.

**Creates / edits** — create `core/scripts/flow_plan.py` · edit the `start-enrich` prompt and the
orchestrator role so it **executes the returned plan and never reorders it** · edit
`core/skills/code_impact_assess.skill.md` (the generic arm) · delete `interchange_enrich`'s
content-sniffing self-gate — passes now run because they were declared.

**Proof** — a fixture per rejection (a plan is refused, not warned about), plus one proving the
**resolve barrier**: an impact pass must not start while any resolve pass is outstanding. Note the
sort itself has **no executable case** in interchange — every impact pass hangs directly off resolve —
so its fixture must construct a synthetic multi-level graph.

---

### Wave 3 — breadth (both items are the estate widening; 003.10a needs only 003.2)

**[ ] 003.6 — Every application scanned in full**

Structural, and the largest single change here. `repo/` → `repos/<name>/`; `code_map/` →
`code_map/<repo>/`. Touches `clone.py`, `code_map_build.py`, `map_cache.py`, `merge_manifest.py`,
`reset_run.py`. Every §16 impact entry gains a **repo qualifier**, which flows to the `code_location`
on Jira stories. One signal profile per repo; the onboarding gate fires once per repo on first use.

**Every application in scope gets the same full repo scan Stratus gets today** — including PeopleSoft,
whose code is what determines what MPT carries. Partial or key-only scanning of a "secondary"
application is the failure this task exists to prevent.

> **`acquired` is one boolean gating two capabilities with very different costs** *(raised
> 2026-08-22, deferred)*. **Drift detection** needs only the two `layout_at` files parsed — one small
> file. **Producer-side impact location** needs a full repo scan: an SQR extractor (none exists) plus
> a signal profile, which is the threefold effort swing this task warns about.
>
> So there is a **much cheaper intermediate state than full acquisition**: obtain PeopleSoft's MPT
> *layout file alone*. That unlocks two-sided field comparison on the estate's most important
> interface without touching the extractor question at all — and it is a **procurement ask, not an
> engineering one**. The model cannot express that state today; `acquired: true` implies scannable.
> Revisit only if the layout actually arrives without the repo.

**`acquired: false` is a first-class state, not an error.** An application declared but not yet cloned
must produce a recorded boundary rather than an exception or a silent skip — that is what makes the
machinery testable before the repos arrive (Target state §10), and it is how PeopleSoft behaves until
its repo is available.

**Tandem has a repo** (confirmed 2026-08-17), so PTI Gen crossing is repo-to-repo and symmetric with
submission→Settlement. Both sides of that interface are real code, and neither is layout-only.

Extractor cost is the one open variable: one signal profile per repo if they are all C, a new
tree-sitter extractor per language if not — a threefold effort swing. **Establish the language mix
before scoping this.**

**[ ] 003.10a — Crossing over declared interfaces** *(the half of 003.10 that needs no history)*

The closure rule for a file-coupled estate, over the interfaces you can declare today. Runs inside the
003.5 orchestrator; the mechanics are in Target state §2 and are not repeated here.

**The rule is one line, and it is symmetric:** an impact landing on **any** party's read site, write
site, or layout definition impacts **every other party** to that interface at the next tier. Producer
changes what it writes → consumers' read sites are impacted. Consumer needs a field the interface does
not carry → the producer's write site and layout are impacted. Neither direction is the special case.

Four things it must get right:

- **Promotion is mechanical** — an impact promotes when its `file:line` falls inside a declared site.
  Never a model deciding whether something looks interface-shaped.
- **Crossing is field-level, not file-level.** *"MPT is impacted, therefore Stratus is a consumer"* is
  not a story anyone can pick up. *"Field `special_program_id` changed; read at
  `src/config/mpt_loader.c:214`"* is. Fields come from parsing the declared layout on each side.
- **Two entry paths.** Promoted from a code hit, **or** assessed directly against the layout with no
  code scan — the second is the only path available while an application is `acquired: false`, and it is
  what keeps a boundary informative rather than blank.
- **The release-shape verdict stops being a judgement.** *Integrated* becomes derived: an interface field changed **and** a
  consumer read site is impacted → they must ship together, with the lines to prove it. No model
  deciding whether two systems feel coupled.

Proof: a fixture where a Tandem PTI Gen write-site impact crosses into Stratus read sites; one where a
Stratus-side need crosses backward to an unacquired PeopleSoft and produces a **recorded boundary**
rather than silence; and one asserting the walk terminates on a cycle.

---

### Wave 4 — history (the upgrade; everything above stands without it)

> **Gate this wave on 003.7a. Both checks are cheap and either can say stop.** Everything from 003.7
> onward is a different kind of project from Waves 1–3: those are engineering against a known design;
> this is data work with an evaluation problem attached. Its failure mode is not breaking — it is
> **half-working while nobody can tell**, which is why measurement comes before machinery.

**[ ] 003.7a — Two go/no-go checks, before any of Wave 4 is planned in detail**

*Neither check builds anything. Both are a day's work at most, and each can independently kill or
reshape the wave.*

**Check 1 — corpus coverage.** The corpus does not need historical changes; it needs changes with
**usable Jira ↔ commit linkage**. Grep commit history across all five repositories for parseable Jira
keys and report the proportion of commits carrying one, **by repo and by year**.

The per-repo and per-year split matters more than the headline number: linkage that only exists in
one repo, or only since a convention was adopted two years ago, is a much narrower corpus than the
raw change count implies. Record the finding before planning further — if coverage is thin, the whole
wave changes shape rather than proceeding at reduced quality.

**Check 2 — held-out prediction test.** Take **20 past changes** with good linkage. Hide their
outcomes. Run classification and engine prediction against them, and compare with what those changes
actually touched.

Report two numbers per prediction type: how often the prediction was right, and how often it **missed
an engine that was genuinely impacted** — the second matters far more, because a missed engine is the
failure this whole mechanism exists to prevent.

> **This is the decisive check.** Building 003.8 and 003.9b before knowing the prior carries signal is
> the expensive mistake available in this wave. If prediction is no better than "every engine, every
> time," the corpus is not predictive, and 003.7b onward should not be built — the four-quadrant
> reconciliation degrades to noise that trains operators to ignore it.

Both results recorded in `docs/design/history-kb-feasibility.md`, with an explicit
**proceed / reshape / stop** recommendation. A later session must be able to see what was measured,
not just what was decided.

**[ ] 003.7 — Build the Jira ↔ commit linkage corpus, resolved to engines**

The data prerequisite, and the longest lead item. Mine commit messages for Jira keys to produce, per
past change: its Jira issue, its change type(s), and — **resolved to engine level, not just repo
level** — what it impacted.

**Resolve to engines, not repos.** The chain is: Jira issue → commits → files changed → components
(via `code_map/components.json`) → engines. The code map is the translation layer that makes raw
commit paths legible as structural units; without it you have a pile of file paths. Engine level is
both finer-grained (a sharper completeness check) and the language the business speaks — *"impacts
the settlement and interchange engines"* means something to a stakeholder that *"repos A and C"*
does not.

*Be deliberate about one thing:* an engine taxonomy **is a vocabulary**, and ADR-008 deleted one. The
distinction that makes this legitimate is authorship — what was removed was **model-assigned tags on
code**; this is operator-authored, or derived deterministically from observed commit history. Decide
that consciously rather than discovering later that you rebuilt what you removed on purpose.

Design decisions to make here: where the corpus lives, and how it is searched. **This differs in kind
from everything ingest does today** — current connectors fetch named sources; this searches a corpus.
Also needed: a fallback for historical commits whose paths no longer exist (renames, moves) — count
those at repo level rather than dropping them silently.

*Note the flywheel: Stage 5 already commits with the Jira key and records the commit on each story,
so every completed run feeds this corpus. It sharpens with use.*

> **The limit of generalising from volume.** Co-change history records **what people did, not what
> was correct.** If an engine was genuinely impacted on past changes but nobody ever raised a story
> against it, the corpus will confidently report it as unimpacted — and more history makes that blind
> spot *more* confident, not less, because the pattern is consistent. This is the reason history must
> never filter the scan: the scan is the only instrument in the system capable of seeing what past
> practice missed.

#### 003.7c — the **diffs** themselves, not just which engines were touched *(added 2026-08-23)*

003.7 resolves past changes to **engines** — a coverage fact. But the corpus also holds the **actual
diffs**, and nothing uses them. Two distinct things come out of a past diff, and they belong in
different places:

| From the diff | What it is | Where it belongs |
|---|---|---|
| **which files changed** | a **scope** fact | **enrichment** — unions into scope like any KB proposal |
| **how they changed** | a **shape** example | **code generation** — cited grounding for the draft |

**Keeping that split is what protects the spine.** The files enter scope at Stage 3, get scanned like
anything else, and produce impacts or explicit non-events — so they reach Stage 5 **through §16**, the
way all work does. Stage 5 never consults history for *scope*; it reads §16, which history already
informed. Only the diff's **content** is a Stage-5 input, and only as an example. Two independent
history consultations that could disagree is exactly what this avoids.

> **Why the union matters: closure has a blind spot that structure cannot fix.** The code map covers
> 100% of files, so nothing is *missing* from it — but the **closure walk follows structural edges**,
> and in a file-coupled estate two deeply related files can have **no edge between them at all**. Two
> programs that both touch MPT share no call, no import, no symbol. Dependency traversal correctly
> reports them as unrelated, because by its own measure they are.
>
> **Co-change is the only signal that sees it.** *"Comparable changes touched `brand_registry.c`"* is
> evidence of a relationship nothing structural would surface. That is the union earning its place:
> not a nice-to-have ranking, but coverage of a class the scan is constitutionally unable to reach.
>
> **And the file still has to be assessed.** A KB proposal adds it to scope; it does not conclude
> anything. The pass scans it and files a finding **or an explicit non-event** — the model may decide
> *not impacted*, but it cannot decline to look, and the outcome is recorded either way. 003.9 then
> compares the two: a file the KB expected where the scan found nothing lands in the **gap** quadrant
> and reaches the operator, because the disagreement is the interesting part.

**Use 1 — Part G.2's analogy search becomes evidenced rather than inferred.** When the scan finds a
**gap**, Part G locates the nearest existing instance of the same kind of thing and reports where a new
one would go. Today that prospective location is derived from the code map plus surrounding pattern —
an *inference*. A past diff makes it a *record*: **"when IRD 0334 was registered under PBI-4471, these
three files changed."** Same output shape, far stronger grounding, and the location stays marked
`prospective` either way.

Note this is where similarity is **easiest**, not hardest: *"the last time an IRD was registered"* is a
narrow, checkable class — not fuzzy semantic matching.

**Use 2 — Stage 5 drafting precedent.** The story says *register IRD 0537*; the corpus holds the diff
for *register IRD 0334*. That is the strongest available grounding for what a correct change looks like
**in this codebase** — which is what a competent engineer does: find the last similar change and follow
it.

> **Cited, never absorbed.** The hunk carries *"drafted following PBI-4471 (IRD 0334 registration)"* so
> the human at G4 judges whether the precedent was good. The §9 caution bites hardest here: history
> records **what people did, not what was correct**, so a past diff can encode a bad pattern and
> silently propagate it. Citing it makes the draft *more* reviewable, not less.

**Who decides "similar enough"?** The split is the same as everywhere: **retrieval is mechanical**
(same change type, same designator family, same engine, same assertion type — a model asked to *recall*
what exists misses things invisibly), **judgement is the model's**, and the judgement is **cited by
Jira key** so it is auditable.

A wrong call is bounded in both directions, which is what makes this safe to add:

- **Too loose** — a bad precedent is suggested, arrives cited, the operator dismisses it. The BAU
  findings are untouched.
- **Too strict** — nothing is judged comparable, and you fall back to exactly what you would have had
  anyway. 003.8's cold start already specifies this: *"no similar precedent found"* falls back cleanly.

Neither can suppress a real finding, because **history has no path to remove anything** — it unions
into scope and never subtracts (§9). All of this is supplemental: the code map is built, the whole repo
is scanned, and every v1 assertion is searched, regardless.

**[ ] 003.7b — Engine profiles: characterise each engine's change surface**

The inversion of 003.7, and the more reusable asset. Rather than matching each new change against
past changes one at a time, characterise **each engine once**: the distinct kinds of change that
historically impact it, mined from the corpus, with frequencies.

Stable, improves as history accumulates, and valuable independently of this pipeline — it is
institutional knowledge about the estate that someone joining the team could read.

> **Keep two granularities distinct, or they will be conflated.** **Change types** — interchange,
> clearing, authorization, network fees — are coarse, there are four, and they decide *which
> enrichment passes run*. **Change patterns** are finer, mined per engine (rate-table updates, new
> fee-program onboarding, message-format version bumps), and they feed *impact prediction*. Different
> objects, different jobs; name them differently in the data.

Feeds 003.9b, which turns these profiles into a committed prior.

**[ ] 003.8 — KB-driven change-type classification at Stage 2**

Insert steps 2–3 of the revised Stage 2 flow: after base v1 is authored, scan the KB, propose types
**as a recommendation with reasoning**, operator accepts or substitutes their own, then probes fire,
then G1.

Three guards:

- **The reasoning cites its precedents by Jira key.** A recommendation the operator cannot audit is
  a guess wearing a justification. Every claim in the reasoning traces to a retrieved past change.
- **Precedent anchors classification only, never content** — type sections must derive from this
  change's own documents and code, or a past change's mistakes arrive wearing a citation.
- **Cold start**: "no similar precedent found" falls back cleanly to the Stage 0 declaration rather
  than blocking.

Record in `decisions.jsonl`: what was recommended, what the operator chose, and **whether they
differed**. The disagreement is the useful part — it measures KB matching quality over time, and it
raises the severity of any later mismatch escalation, which is then contradicting an explicit human
decision rather than a default.

**[ ] 003.9 — The history reconciliation at Stage 3 — four quadrants, both directions**

After enrichment, compare the engines the scan actually found impacted against the engines the KB
says similar past changes touched. **Present the result as agreement and disagreement, never as a
flat list.**

| | KB expects it | KB has never seen it |
|---|---|---|
| **Scan found impact** | agreed — high confidence, proceed silently | **novel — present for determination** |
| **Scan found nothing** | **gap — present for determination** | not impacted |

Only the two off-diagonal cells reach the operator, which keeps the decision set small and consistent
with how escalations work elsewhere. *"Three engines confirmed by both, two found by scan only"* is a
far better hand-off than either a flat five or a filtered three.

> **Count only `kind: impact`.** If TASK-V2-005 Part G is built, §16 also contains **gap** entries
> carrying *prospective* locations. A prospective location in an engine is **not** evidence the scan
> found impact there — treating it as such would tell this check the engine was covered when nothing
> was actually found, destroying the signal it exists to produce.

**Both directions matter, and they catch opposite failures:**

- *"Past interchange changes always touched the clearing engine; your impacts have nothing there"* —
  **under-detection**, the failure that survives scanning everything.
- *"Your plan has stories against the messaging engine; no similar past change ever touched it"* —
  **over-detection**, and a far better bloat signal than counting stories, because it names *which*
  impacts to be suspicious of rather than merely reporting that there are too many (see 003.6).

**Never let the KB filter the scan.** The scan is direct evidence about *this* change; the KB is
statistical evidence about *similar* changes. An engine no comparable change ever touched is exactly
where something unusual is happening, so filtering by history suppresses the highest-value finding
the system can produce. The cost asymmetry settles it: a false positive costs an operator seconds to
dismiss; a suppressed true positive costs a production incident.

Each off-diagonal case resolves as a real finding or an explicit non-event — never silence.

Requires 003.6 (all repos scanned) and 003.7 (the corpus). This is the highest-value use of the KB
and should not be skipped as a nice-to-have.

#### 003.9c — file-level reconciliation *(candidate refinement, added 2026-08-23)*

003.9 reconciles at **engine** level. With the diffs (003.7c) the same four-quadrant check runs at
**file and function** level:

> *Past IRD registrations touched `brand_registry.c`, `route_table.c` and `submission_writer.c`. This
> scan found the first two. The third is a **gap** — determine.*

Strictly a sharper completeness check, and it uses a corpus 003.7 builds anyway.

> **Gate it on noise, not on appetite.** 003.7 resolved to engines deliberately — engine level is *"the
> language the business speaks"* and it aggregates away the fact that **files change for many unrelated
> reasons**. Going finer means more off-diagonal cells reaching the operator, against a walkthrough
> baseline of ~4 decisions with a growth tripwire in 006. Measure the false-positive rate on the real
> corpus first; 003.7a's go/no-go checks are the natural place. If it is noisy, engine level stands and
> nothing is lost.

#### 003.9b — graded reconciliation (the refinement of the table above)

The four-quadrant table is the shape; this is the resolution. Both the prior and the evidence are
**graded, not binary**, and the agent reconciles them into a recommendation the human decides on.

**1 · Prior, from the engine profiles (003.7b), committed *before* the scan.**
Per engine, an expectation expressed as a **frequency, never a probability**: *"8 of 11 similar past
changes impacted the settlement engine."* A count is a computed fact anyone can audit; a percentage
is the same judgement wearing decimals, and gets trusted far past its worth. An ordinal band
(high / medium / low) may sit **on top of** the count, never in place of it.

> **Write the prior to `decisions.jsonl` before the scan runs.** If the agent forms an expectation and
> then evaluates the evidence, it can rationalise toward what it already said — confirmation bias in
> sequence, invisible afterwards. Committing the prior first makes the reconciliation auditable: you
> can see whether the final call **updated on evidence** or merely echoed the prior. Over time that is
> the only way to learn whether the KB is genuinely predictive.

**2 · Evidence, from the scan.** Not "found / not found" but **strength**: how many impact matches,
how direct (direct vs transitive per `tier_walk`), and how well each ties to a v1 assertion.

**3 · Reconciliation.** The agent weighs prior against evidence per engine and produces a
recommendation **with reasoning that cites both sides** — the specific scan matches and the specific
past changes. Judgement is welcome; ungrounded judgement is what this architecture exists to exclude.
Include the sense-check the KB uniquely enables: *have changes of this kind ever touched these
components before?*

**4 · The human decides.** The agent recommends; the operator determines. Recorded in
`decisions.jsonl` with **whether it differed from the recommendation** — same disagreement-capture as
the change-type classifier at 003.8, and the same reason: it is the only measure of whether any of
this is working.

---

### Wave 5 — depth

**[ ] 003.10b — Interface discovery, totality and drift** *(the half of 003.10 that needs history)*

> **003.10 split on 2026-08-17.** Crossing over the interfaces you can already declare — MPT, PTI Gen,
> submission — needs no history at all, so it moved into **003.10a**, immediately behind 003.2 and part
> of the 003.5 orchestrator. What genuinely needs history is *discovering the interfaces nobody thought
> to declare*, which is this task.

**Originally written as cross-repo *code* closure per ADR-007. That would find almost nothing in this
estate.** Tandem, Stratus, Settlement and PeopleSoft are coupled by **file**, not by call graph — no
import, no shared symbol. A dependency walker crossing repo boundaries traverses an empty set and
correctly reports the systems as unrelated.

> **Two of the three parts here do not need history at all** (noted 2026-08-23). They are bundled
> under Wave 5 by association rather than by dependency, and the totality check in particular is
> worth pulling forward:
>
> | Part | Actually blocked on | Earliest |
> |---|---|---|
> | **Interface totality** | nothing — it is a code scan | **runnable today against Stratus**; belongs beside 003.10a |
> | **Layout drift** | a **second acquired repo**, not history — every declared interface has exactly one acquired party today | acquisition |
> | **Co-change discovery** | the history corpus | genuinely Wave 5, after 003.7 |
>
> Totality answers a question worth asking early: *is `interfaces.yaml` complete, or did we declare
> the three obvious ones and miss the two that matter?* That is a direct check on the foundation 003.2
> lays down, and it does not need a single line of history.

Two checks, both only possible because the estate is file-based:

- **Interface totality** — scan each repo for external file I/O; every one maps to a declared interface
  or is marked internal. **Undeclared external file I/O is a finding.** Same shape as
  `check_map_totality`.

  > **Control-M is a second source, confirmed to exist** (V, 2026-08-23). Job chains encode
  > producer→consumer relationships in machine-readable form — *`PS_MPT_EXTRACT` completes, condition
  > fires, `STRATUS_MPT_LOAD` runs* — which is the MPT interface stated outright. **This needs no
  > history**, so it belongs beside the totality scan rather than in Wave 5.
  >
  > Three checks fall out, and the third is the valuable one:
  > - every declared interface has a corresponding job chain, or is explained
  > - every job chain crossing two systems maps to a declared interface — **an unmapped chain is an
  >   interface nobody declared**
  > - a declared interface with no chain is dormant, wrong, or driven by clock rather than dependency
  >
  > **Two limits to design against.** Control-M encodes *scheduling* dependency, not *data*
  > dependency: two chained jobs need not share a file, and two jobs sharing a file need not be
  > chained if the timing is by clock. So it is **evidence, not proof**. And it resolves to *jobs and
  > programs*, never to `reads_at: src/config/mpt_loader.c` — it gives you the interface **set**, not
  > the **sites**. Sites still require declaration.
- **Layout drift** — duplicated layouts are the norm here, so compare the two declared definitions
  (`submission_record.h` against `sub_rec.h`). A mismatch is a finding in its own right. Free once
  fields are parsed rather than hand-listed (Target state §2).

**Why this half runs after 003.7.** History is the *discovery* mechanism; declaration is the *precision*
mechanism. Co-change surfaces coupling at zero declaration cost — *"Stratus and Settlement moved
together in eleven of thirteen interchange changes"* — and you then declare those interfaces properly.
Declaring from memory gets the three obvious ones and misses the two that matter. The audit runs both
ways: a declared interface that never co-changes is dormant or wrong; co-change with no declared
interface is a hole in the map.

Read ADR-007 first, and record why its code-closure framing does not fit this estate.

---

### What this task does *not* address

The two Stage 2 findings below are independent of the framework and stay parked. Neither is fixed by
any sub-task above, and the shorter base profile makes both matter *more*, since each surviving
section carries more weight.

---

## [ ] TASK-V2-004 — the reconciliation pass: findings that contradict each other

> **Candidate** — raised in the Stage 3 review of 2026-08-16. Independent of TASK-V2-003 — this fixes a
> gap in the pipeline as it stands today and could be built without any of the change-type work.
> But Waves 2 and 3 make it more urgent, since both add producers filing into the same findings file.

> **Measured 2026-08-23 — Arm 2 does return refuted, so this is not theoretical.** Against run
> `r-2026-08-01-si1`, of 33 findings: 17 `impacted`, 7 `confirmed`, 5 `no_code_found`, **2
> `contradicted`**, 2 `unverifiable`. Roughly **6%**. One run and n=2, so weak evidence — but the open
> question was only ever whether it is *ever* non-zero, and it is. **The cheap correlation version
> will not suffice indefinitely.**

### Why this exists

Arms 1 and 2 run in parallel and neither sees the other's output. Nothing afterwards looks at
**relationships between findings**, so two findings can be individually correct and jointly
incoherent.

Concretely. v1 carries a claim — *"interchange levels are resolved in the settlement engine at batch
close"* — and an assertion in §8 — *"apply the new IRD 0537 rate at settlement."* Arm 1 takes the
assertion, lands in `settlement/`, walks the closure through `ledger_post.c` and `reconciler.c`, and
files four §16 impacts. Arm 2 takes the claim, checks the code, and finds resolution actually happens
in `routing/` at authorisation time: **refuted**.

Both arms did their job correctly. Both findings land in `enrichment.json`. The apply pass writes
both into v2 — four impacts against the settlement engine, and elsewhere in the document, a note that
the premise they rest on is false. Stage 4 turns those four impacts into four Jira stories against
the wrong code.

**The failure is silent because neither finding is wrong.** Only the relationship is, and nothing
inspects relationships.

The arms' independence is deliberate and correct — one arm's error must not contaminate the other.
But independence at analysis time creates an obligation to reconcile afterwards, and that step does
not exist.

### The design — mechanical recall, model precision

A new step running **after every producer has filed** (both arms *and* the type passes, once Wave 2
lands) and **before the walkthrough**.

**Step 1 — enumerate candidates deterministically.** `core/scripts/reconcile_findings.py` computes
the candidate set: every **refuted** or **unverifiable** claim, crossed with every finding sharing
its assertion or any of its code locations. No judgement, no model.

**Step 2 — judge each candidate.** `core/skills/finding_reconciler.skill.md` reads each pair and
decides whether it is a genuine conflict, **citing the specific claim, the specific finding, and the
dependency between them.**

> **Why the split, and do not collapse it.** "Does this impact depend on this claim?" is a semantic
> question a script cannot answer — it can only check whether two things mention the same file. But
> if the model both *finds* and *judges*, a pair it never noticed is invisible: no signal, nothing to
> check, and the reconciliation silently has a hole. Enumerating mechanically makes a missed pair
> **impossible**, while a wrong judgement stays **visible** because it is recorded with its reasoning.
>
> Recall is mechanical, precision is judgement. This is the third instance of the principle the
> architecture already runs on — the same inversion as `doc_index` (structure derived, summary
> model-written) and `code_map` (structure derived, `purpose` model-written).

**Step 3 — record dismissals too.** A candidate judged *not* a real conflict is written down with its
reasoning, never dropped. Otherwise the filter is unauditable and a reconciliation that **found**
nothing is indistinguishable from one that **considered** nothing.

**Step 4 — grade, then escalate only the strong.** A refuted claim and a finding naming the same file
is a strong conflict and worth a human. Sharing only an assertion, with no overlapping code location,
is weak — a note in the document, not an escalation. Strength governs whether a person is
interrupted, as at 003.9b.

### Generalise past refuted claims

Write the rule as **finding versus finding**, not claim-versus-impact. Arm 2 refuting a claim Arm 1
built on is one instance; a type pass concluding something an arm contradicts is another. Stated
generally, it keeps working as producers are added — which Wave 2 does.

### The third escalation category

Genuine conflicts flow into the **existing** walkthrough — no second operator turn. But they are a
category the current provenance model does not cover. Today: source-derived corrections auto-apply;
operator contradictions escalate. This is **tool contradicting tool**. Neither producer has authority
over the other, so it cannot auto-resolve — and it is not "we are overruling you, confirm." It is
*"two analyses disagree, adjudicate."*

`dispositions.py` needs that third routing category. The walkthrough then carries three kinds of
item: source corrections to confirm, human contradictions, and analyses that disagree.

### What the operator sees, and what each outcome does

The flag is a **suspicion, not a verdict** — Arm 1's impacts rest on code it actually found, and may
never have used the claim at all. Present the pair: the refuted claim with its refuting evidence, the
correlated findings with theirs, and the assertion they share. One question: **do these findings
survive?**

| Outcome | Effect |
|---|---|
| Findings stand | Recorded; they proceed to §16 and become stories as normal |
| Findings void | Marked **void with provenance** — never deleted (see below) |
| Refutation is wrong | Arm 2's verdict marked overridden; findings stand |
| Re-trace | Targeted re-run of Arm 1 for that assertion using the correction |

**Re-tracing is more feasible than it looks:** a refutation usually carries its own correction
(*"not settlement — routing, at auth time"*), which is itself a finding with provenance. So Arm 1 is
re-pointed for one assertion, not re-run wholesale.

**The void status has a consequence that must ship with this task.** *Enrichment never deletes*, so
"these findings are wrong" cannot remove them — it marks them void, carrying the operator decision
and the refuted claim that caused it. Which means **`jira_author` must honour void and skip those
impacts.** Without that, an impact voided at Stage 3 becomes a story at Stage 4 anyway, and the whole
mechanism achieves nothing.

### Depends on

Confirm each exists before starting; if one is missing, stop and report it.

- `core/scripts/enrichment.py`, `core/scripts/schemas/enrichment.schema.json`
- `core/scripts/dispositions.py`
- `core/skills/claim_verifier.skill.md`, `core/skills/code_impact_assess.skill.md`
- `core/skills/disposition_walkthrough.skill.md`
- `core/scripts/apply_enrichment.py`
- `core/skills/jira_author.skill.md`, `core/scripts/jira_plan.py`
- `core/scripts/solution_intent_validator.py`
- `overlays/claude/prompts/start-enrich.md`,
  `overlays/copilot/.github/prompts/start-enrich.prompt.md`
- `fixtures/enrichment/verify_enrichment_router.py`

### Reads

- `core/scripts/schemas/enrichment.schema.json` — whether a finding can carry a **void status**, a
  **conflict reference**, and a **reconciliation verdict**. If strict, this is a versioned change
- `core/scripts/dispositions.py` — the existing routing categories, before adding a third
- `core/skills/disposition_walkthrough.skill.md` — how items are presented today, so a third kind
  fits the existing form rather than inventing a second style
- `core/scripts/apply_enrichment.py` — how findings become v2, and where void must be honoured
- `docs/TECH_SPEC.md` — the enrichment contract and G2's preconditions

### Creates / edits

| Path | Action |
|---|---|
| `core/scripts/reconcile_findings.py` | create — deterministic candidate enumeration |
| `core/skills/finding_reconciler.skill.md` | create — the per-candidate judgement |
| `core/scripts/schemas/enrichment.schema.json` | edit — void status, conflict ref, verdict |
| `core/scripts/dispositions.py` | edit — the third routing category |
| `core/skills/disposition_walkthrough.skill.md` | edit — present conflicts as a third item kind |
| `core/skills/jira_author.skill.md` + `core/scripts/jira_plan.py` | edit — **honour void** |
| `core/scripts/apply_enrichment.py` | edit — carry void + conflict records into v2 |
| `overlays/*/…/start-enrich*` | edit — run reconciliation after producers, before walkthrough; **both overlays identically** |
| `core/scripts/solution_intent_validator.py` | edit — G2 precondition (below) |
| `fixtures/reconciliation/` | create — cases + `verify_reconciliation.py` |
| `docs/TECH_SPEC.md`, `docs/OPEN_RULINGS.md` | edit — the step, and the third category as a ruling |

### Acceptance

1. Reconciliation runs after **all** producers and before the walkthrough, in both overlays.
2. Candidate enumeration is deterministic and complete: every refuted/unverifiable claim × every
   finding sharing an assertion or a code location. Grep confirms no model call in
   `reconcile_findings.py`.
3. Every candidate receives a judgement citing the specific claim, the specific finding, and the
   dependency between them.
4. **Dismissed candidates are recorded with reasoning** — a reconciliation that found nothing is
   distinguishable from one that considered nothing.
5. Strong conflicts escalate to the walkthrough; weak ones are recorded as notes and do not.
6. The third routing category exists in `dispositions.py` and is presented as its own item kind.
7. Void findings are marked with provenance, never deleted, and **`jira_author` produces no story
   from a voided impact**.
8. G2 precondition: **no unresolved strong conflict may pass the gate.**
9. `build_checks.py` green including overlay parity; full fixture sweep green; registry re-published.

### Proof

`fixtures/reconciliation/` covering:

- `no_conflict` — refuted claim, no shared assertion or location → dismissed, and **the dismissal is
  recorded**
- `weak_conflict` — shares an assertion only → note, no escalation
- `strong_conflict` — shares a file → escalates
- `void_blocks_story` — an impact voided at Stage 3 produces **no story** at Stage 4 *(the single
  most important case: without it the mechanism is decorative)*
- `refutation_overridden` — operator rules the refutation wrong; findings stand
- `type_pass_conflict` — a type-pass finding contradicting an arm *(add when Wave 2 lands)*

`verify_reconciliation.py` runs each and is runnable standalone.

---

## [ ] TASK-V2-005 — expectation-aware absence: what "not found in the code" actually means

> **Candidate** — raised in the Stage 3 review of 2026-08-16. Pairs with TASK-V2-004 — that task handles
> findings that contradict *each other*; this one handles findings that contradict **the code**, which
> the current authority model does not cover.

### Why this exists

The documented authority rule has two branches: source-derived corrections auto-apply, operator or
frame contradictions escalate. The **central case of the entire stage is missing from it** — v1 says
one thing, the code says another. Code is not a "source" in the disposition sense; it is the repo.

Resolving it requires splitting what v1 is doing, because the same observation carries opposite
meanings:

- **Code is authoritative about the present.** v1 claims interchange levels resolve in the settlement
  engine; the code shows routing, at authorisation. The code wins outright — it *is* the system.
- **Documents are authoritative about the future.** v1 requires support for IRD 0537; the code has no
  IRD 0537. That absence is **not a refutation — it is the work**, and the reason the change exists.

**The failure to design against is a prescriptive gap treated as a refutation.** v1 requires a new fee
program, Arm 2 finds no trace, returns *refuted*, and if refutations auto-apply the requirement is
corrected out of existence. The plan comes out smaller than the mandate, the validator is satisfied
because everything traces, and the missing work surfaces in production. It is the worst silent failure
available in the pipeline, because it fails in the direction of **doing less**.

### The governing principle

> **Absence only means something relative to what you expected to find.**

*"Add support for a new fee program"* finding nothing is a non-event. *"Update the MCC codes for car
rental and hotel"* finding nothing is alarming — MCC handling unquestionably exists in that codebase.
Today those produce the identical signal.

When an expected thing is absent there is no benign reading. Either the search failed, or the code
lives in a repo outside the scanned estate, or the requirement is wrong to assume it exists. All three
need a human.

---

### Part A — classify every assertion at Stage 2, code-blind

Each §8 assertion is classified during authoring as **`modify_existing`**, **`new_capability`**, or
**`unclear`**.

This is reading comprehension on the requirement document — *add* versus *change* — and needs no code.
Done by `solution_intent_author`, recorded with the assertion in v1, and **set before G1**.

> **The ordering is the point, not an implementation detail.** If Stage 3 decided "this was probably a
> new program, then" *after* failing to find anything, the check would be worthless — it would
> rationalise every absence. Committing the expectation in v1, before code is ever consulted, is what
> makes a later mismatch mean anything. Same principle as the committed prior at 003.9b, applied per
> assertion.

**`unclear` must never silently default to `new_capability`.** That default suppresses exactly the
escalation this task exists to raise. `unclear` routes to an operator probe at Stage 2 — and if it
survives to G1 unresolved, Stage 3 treats it as `modify_existing` (the cautious direction: it escalates
rather than going quiet).

### Part B — assertion provenance decides authority

v1 contains statements from several places: the requirement document, other domain sources, operator
answers, and things the author inferred. **Only assertions traceable to a `business_requirement`
source get *documents beat code* protection.** An inferred assertion does not earn it.

This makes citations **load-bearing for routing**, not merely for audit — a change in what the
cite-or-flag rule is *for*, and worth stating in the spec.

### Part C — the three-way authority model

Replaces the two-branch rule in `dispositions.py`:

| Statement kind | Authority order | Routing |
|---|---|---|
| **Descriptive** — what the system does today | code > documents > operator memory | auto-apply, citing the code location |
| **Prescriptive** — what must change *(document-provenanced, per Part B)* | documents > operator > code | code has **no** authority; never auto-corrects |
| **Scope / frame** | operator only | always escalate |

A cheap tell that the arms are correctly scoped: **`unverifiable` is meaningless for a prescriptive
statement** — of course present code cannot verify a future requirement. If Arm 2 ever returns
`unverifiable` on something requirement-shaped, it is pointed at the wrong kind of sentence.

### Part D — the four-quadrant expectation check at Stage 3

| | Found in code | Not found |
|---|---|---|
| **`modify_existing`** | normal — impacts filed | **ESCALATE** |
| **`new_capability`** | **FLAG** — does it already exist? | normal — "not yet developed"; this is the work |

- **Bottom-left (escalate):** name all three candidate causes explicitly. Search failure, coverage gap
  outside the scanned estate, or a requirement mistaken that the thing exists.
- **Top-right (flag):** either someone already built part of it, or there is a naming collision. Worth
  thirty seconds of a human's attention before the plan is written.
- **Bottom-right:** a **recorded non-event**, never silence — "not yet developed in the code" is a
  positive statement, and it is what the change is for.

### Part E — code contradicting a prescriptive assertion is a *scope finding*

Not a refutation, and never discarded. File it as: *"this requirement assumes a capability the code
does not have; the change is larger than v1 states."*

That is the system reporting the estimate is wrong — early warning nobody gets today.

### Part G — gaps must become work, and every assertion must be accounted for

Parts A–F decide what an absence *means*. This part decides what happens to it, because a
`new_capability` gap **is the work to be done** — the requirement is real, the code does not have it,
somebody must build it. Today the story spine is §16 impacts, every impact is anchored to a code
location, and a gap has no code location by definition. So the most greenfield work is the most likely
to fall out of the plan entirely: a new fee program produces more gaps than impacts, and the more novel
the change, the more of it goes missing.

#### G.1 The enabling primitive — stable assertion ids

**Nothing else in this part is checkable without it.** Each §8 assertion carries a stable id, and every
finding carries an `assertion_ref` back to it. Ids are stable across the v1 → v2 rewrite (they are in
frozen v1, so they cannot drift).

#### G.2 A gap is not location-*less*, it is location-*prospective*

This is the technique that makes gaps into writable stories. When Arm 1 fails to find a direct landing,
it performs an **analogy search**: locate the nearest existing instance of the same *kind* of thing and
report where a new one would go.

> IRD 0537 not found. Comparable IRDs are registered in `brand_registry.c:120-180` and rated in
> `route_table.c:88-140`. A new IRD would be added there.

That is a story someone can pick up. *"Not found"* is not. The prospective location comes from the code
map plus the surrounding pattern, and it is marked **prospective** so nobody mistakes it for evidence
that the code exists.

Where analogy fails, say so explicitly — `location: undetermined`, with what was searched. **Never drop
the gap for lack of a location**; an honest "we could not work out where this goes" is itself a finding
worth a human's attention.

#### G.3 §16 carries two entry kinds

Extend §16 to hold **impacts** (code exists — here it is) and **gaps** (code does not exist — here is
where it would go, or undetermined). Same section, same traceability spine, distinguished by kind.

`jira_author` maps both. Stories from gap entries carry a prospective or undetermined `code_location`,
so **`jira_template` and `jira_validator` must both tolerate that** — a validator demanding a concrete
code location on every story will silently reject exactly the greenfield work this part exists to
rescue.

#### G.3a What the marking actually looks like, and where it lives

**One section, one entry shape, one field.** Not two lists and not a second section — §16 stays the
single traceability spine, and `kind` distinguishes the two.

```
§16.3   kind: impact
        assertion: A-4  (modify_existing)
        location: src/routing/route_table.c:88-140    [found]
        finding: IRD 0301 rate entry — rate field set at line 112

§16.7   kind: gap
        assertion: A-9  (new_capability)
        location: src/routing/brand_registry.c:120-180    [prospective]
        basis:    IRDs 0201, 0334, 0512 are registered here
        finding:  IRD 0537 does not exist. A new registration would be added here.
```

Three differences and no others: `kind`, the qualifier on `location` (**found** / **prospective** /
**undetermined**), and `basis` — the analogy citation, which a gap must carry and an impact has no use
for.

The marking lives in **`enrichment.json`** (the finding), is rendered into **v2 §16** (visibly
distinguished, so a human reading v2 sees it at a glance), and rides into the **Jira story**.

*Why not a separate section for gaps:* §16 is what `jira_validator` traces both ways. A second home
means a second spine, and gaps would have to be re-plumbed into every check that already works.

#### G.3c A third kind — `verify`, the reasoned non-change *(added 2026-08-22)*

`impact` and `gap` cover *change this* and *build this*. Neither covers the third thing the run
produces: **a deliberate non-change resting on an assumption.** Not *"we found nothing"* — *"we found
this, concluded it needs no change **because** Y, and Y should be confirmed."*

That assumption can be wrong, and today it is invisible: the pass files a non-event or simply reports
no impact, and the reasoning behind the non-change never reaches anyone. **A VERIFY is a Jira story**
— real, assigned, tracked, closed — so the third kind belongs in the spine like the other two.

```
§16.9   kind: verify
        assertion: A-6  (modify_existing)
        location: src/billing/fee_calc.c:210-240    [found]
        finding:  fee calculation reads the rate at runtime, so a rate change
                  requires no code change here
        confirm:  that fee_calc reads rates dynamically and holds no cached copy
```

`confirm:` does for a verify what `basis:` does for a gap — it is what makes the entry **actionable**
rather than a statement. Without it a verify is an opinion; with it, it is a task.

**The mapping is now total — every `kind` yields a story, and its kind decides the story's action:**

| `kind` | Means | Story action | `code_author` |
|---|---|---|---|
| `impact` | code exists, change it | **EDIT** | drafts a hunk |
| `gap` | code does not exist, add it | **EDIT** (new build) | drafts, or records — see 009 fixture S3 |
| `verify` | code exists, deliberately **not** changed | **VERIFY** | note only, **never a hunk** |

> **This settles the `arch.md` wording.** *"EDIT stories only; VERIFY/VALIDATE become notes"* is about
> **code generation**, not story existence. All three are Jira stories; `code_author` only drafts
> hunks for the EDIT ones. VALIDATE's home is `validation.md` (TASK-V2-008); VERIFY's is a story
> carrying its `confirm:` condition.

**Two rules that must hold with a third kind in play:**

- **003.9 still counts only `kind: impact`** as *scan found impact*. A verify is the opposite of
  evidence — it is a recorded decision that nothing changed there. Counting it would tell the history
  reconciliation an engine was covered when nothing was touched, destroying the signal the check
  exists to produce. The rule already exists for gaps; it now carries more weight.
- **`code_validator.py` blocks a hunk on a `verify` entry** (TASK-V2-009). A story saying *"we
  deliberately did not change this"* arriving with a code edit attached is a self-contradiction, and
  it is exactly the silent kind — the diff looks reasonable at G4.

#### G.3b `kind` must propagate — every consumer branches on it

**A gap is never counted as an impact anywhere downstream.** This is easy to miss and quietly corrupts
checks built later:

- **`jira_author`** — both kinds become stories; gap stories carry a prospective or undetermined
  location.
- **`jira_validator`** — never rejects a story for lacking a concrete location.
- **History reconciliation (003.9)** — counts **only `kind: impact`** as *impact found* in an engine. A
  prospective location in the settlement engine must not make the reconciliation believe the scan found
  settlement impact, or the check loses exactly the signal it exists to produce.
- **Scan strength (003.9b)** — prospective locations contribute nothing to strength; they are the
  absence of evidence, not evidence.
- **Any volume or bloat measure** — report the two counts separately. Forty §16 entries of which
  fifteen are prospective is a different situation from forty real impacts.

#### G.4 Assertion totality — two checks, at two gates

Following the pattern of `check_map_totality` (every file lands in a component):

- **G2 precondition** (`solution_intent_validator.py`): every §8 assertion id appears in **at least
  one** outcome — an impact, a gap, a recorded non-event, or an open escalation. *At least one*, not
  exactly one: an assertion legitimately produces many impacts.
- **G3 precondition** (`jira_validator.py`): every assertion id traces to **at least one story**, or to
  an explicit operator decision that it needs none.

> **Why this closes a real hole.** `jira_validator` today enforces traceability *between impacts and
> stories* — in both directions. But an assertion that no arm ever picked up produces no impact, and no
> impact produces no traceability failure. It passes every check in the system **by being absent.**
> Totality is checked over the *assertions*, which is the only place absence becomes visible.

The "needs no story" case is real and must stay explicit: an assertion in the `new_capability` × found
quadrant (Part D) may already be satisfied by existing code. That is a legitimate no-work outcome — but
a recorded decision, never silence.

### Part H — `unverifiable` must say *why*

Arm 2 answers three ways: true, false, or **"I couldn't tell."** Today the third is one flat verdict,
recorded and then consumed by nothing.

But "couldn't tell" covers four different situations, and one of them is the most actionable output the
arm produces:

> v1 says *"PeopleSoft holds the mnemonic-to-rate mapping."* Arm 2 searches the Stratus code, finds no
> PeopleSoft anything, and returns **unverifiable**.
>
> v1 says *"the system handles interchange correctly."* Arm 2 also returns **unverifiable**.

Same word, unrelated problems. The first is not uncertainty at all — it is the system reporting *"you
pointed me at code that does not contain this."* The second is a v1 writing problem. Flattened into one
verdict, the useful one is invisible.

#### H.1 The four causes

Every `unverifiable` verdict carries a cause:

| Cause | Means | Feeds |
|---|---|---|
| `out_of_scope` | Not in the code that was scanned | **What the estate is missing** — direct, run-sourced evidence for 003.6, naming the systems |
| `not_in_code` | Not the kind of thing source shows — a schedule, config, ops procedure | Whether another instrument is needed |
| `ambiguous` | Genuinely two readings, source cannot settle it | A human look, if the claim is load-bearing |
| `claim_too_vague` | Not testable as written | **Stage 2 authoring quality**, measurable over time from the ledger |

The first and last are the valuable ones, and both are currently thrown away. `out_of_scope` produces
a list of what your scan does not cover, sourced from real runs rather than intuition — and it names
*which* systems. `claim_too_vague` is the only signal in this design that points **backwards** at
authoring quality.

#### H.1a Where verdicts actually live — not §16

**§16 entries become Jira stories.** A verdict on a claim is not work; it is context about the system.
Putting verdicts in §16 pollutes the story spine with things nobody should be assigned.

| Verdict | Where it goes |
|---|---|
| **All** | `enrichment.json` — the audit trail, as with every finding |
| **Refuted** | **Corrected in place**, where the claim was written, with provenance pointing at the finding. The existing "never delete, rewrite with provenance" rule; no new mechanism |
| **Unverifiable** | **Marked in place**, same location — nothing to correct, only something that could not be checked. An inline `[unverified — out of scope]` marker, matching the existing `[TBD — unsourced]` convention |
| **`out_of_scope` roll-up** | **The enrichment report (H.3), not v2 at all** |

That last row is the one worth being firm about. *"Four claims could not be checked because they
concern PeopleSoft, which we do not scan"* is a fact about **this run's coverage**, not about the
change. v2 is a document about the change — someone reading it in six months does not care what the
scanning estate looked like that week.

> **Open:** §17 and §18 are written by the apply pass and one of them may already be the natural home
> for claim verification. Read `si_profile.payment_brand.yaml` before finalising placement rather than
> inventing a section that already exists.

#### H.2 Report it, never block on it

**`unverifiable` must not cost anything at a gate.** Surface the count and the cause breakdown at G2,
and flag specifically where an assertion's impacts rest on an unverifiable claim — but do not refuse
the gate on it.

> If admitting uncertainty blocks progress, the arm will guess to avoid it, and a confident wrong
> verdict is far worse than an honest unknown. The design already treats an honest `unverifiable` as
> valid; this keeps it that way while making it useful. **Safe, but not silent.**

*Already handled elsewhere:* TASK-V2-004 places unverifiable claims in the reconciliation candidate set
alongside refuted ones, so an assertion whose impacts rest on unverified ground is examined there.

#### H.3 The enrichment report — see TASK-V2-006

The `out_of_scope` roll-up and the unverifiable cause breakdown are surfaced in
**`enrichment_report.md`**, which is its own catalogue item (**TASK-V2-006**) rather than part of this
task — it is the third member of the family with the Run Brief (001) and Ingest Report (002), and it
has value with none of this task built.

**What Part H contributes to it:** the assertion accounting (Part G), the four-cause unverifiable
breakdown, and the *not scanned* coverage list.

### Part F — escalations state meaning, not null results

> §8.3 states an **update** to existing MCC handling. No MCC handling was found in any of the five
> repositories. Either the search missed it, it lives outside the scanned estate, or the requirement
> is mistaken that it exists.

That is a question a person can answer. *"0 impacts found"* is not. **Acceptance condition, not style
guidance.**

---

### Depends on

- `core/skills/solution_intent_author.skill.md`
- `core/profiles/payment_brand/si_profile.payment_brand.yaml`
- `core/scripts/dispositions.py`
- `core/skills/claim_verifier.skill.md`, `core/skills/code_impact_assess.skill.md`
- `core/scripts/enrichment.py`, `core/scripts/schemas/enrichment.schema.json`
- `core/scripts/solution_intent_validator.py`
- `core/skills/disposition_walkthrough.skill.md`
- `fixtures/si_author/verify_si_author.py`, `fixtures/enrichment/`

### Reads

- `core/scripts/dispositions.py` — the current two-branch rule, before replacing it
- `core/skills/claim_verifier.skill.md` — **whether Arm 2 is already scoped to descriptive claims
  only.** If it is, the dangerous case may be prevented by construction today; confirm rather than
  assume, and record the finding either way
- `core/scripts/schemas/enrichment.schema.json` — whether a finding can carry `assertion_type`,
  assertion provenance, and a scope-finding kind
- `docs/TECH_SPEC.md` — the §8 contract and G1/G2 preconditions

### Creates / edits

| Path | Action |
|---|---|
| `core/skills/solution_intent_author.skill.md` | edit — classify each assertion |
| `core/profiles/payment_brand/si_profile.payment_brand.yaml` | edit — `must_capture`: every assertion carries a type + provenance |
| `core/scripts/dispositions.py` | edit — the three-way authority model |
| `core/scripts/schemas/enrichment.schema.json` | edit — `assertion_type`, provenance, scope-finding kind |
| `core/skills/code_impact_assess.skill.md` | edit — the four-quadrant check; scope findings |
| `core/skills/claim_verifier.skill.md` | edit — scope to descriptive claims explicitly |
| `core/scripts/solution_intent_validator.py` | edit — G1 and G2 preconditions below |
| `core/skills/disposition_walkthrough.skill.md` | edit — present the two new item kinds |
| `fixtures/expectation/` | create — cases + `verify_expectation.py` |
| `docs/TECH_SPEC.md`, `docs/OPEN_RULINGS.md` | edit — the authority model as a ruling |

### Acceptance

1. Every §8 assertion in v1 carries a classification and a provenance reference. **G1 precondition:
   no assertion is unclassified.**
2. Classification happens at Stage 2, before any code is read — verifiable from the ledger ordering.
3. `unclear` never defaults to `new_capability`; unresolved at G1 it is treated as
   `modify_existing`.
4. All four quadrants behave as specified, including the recorded non-event bottom-right.
5. A prescriptive assertion is **never** auto-corrected by code evidence. Instead, a scope finding is
   filed. *(The critical condition — this is the "requirement quietly deleted" failure.)*
6. Escalation text names the three candidate causes; a bare count is a failure.
7. G2 precondition: no unresolved `modify_existing`-not-found escalation passes the gate.
8. **Every §8 assertion carries a stable id, and every finding carries an `assertion_ref`.**
9. **Gaps appear as §16 entries** of kind *gap*, with a prospective `code_location` where analogy
   succeeds and `undetermined` (with what was searched) where it does not. **No gap is dropped for
   lack of a location.**
10. **`jira_author` produces stories from gap entries**, and neither `jira_template` nor
    `jira_validator` rejects a story for carrying a prospective or undetermined location.
    *(Without this, the most greenfield work is silently excluded from the plan.)*
11. **Assertion totality holds at both gates:** every assertion has ≥1 outcome at G2, and ≥1 story or
    an explicit recorded no-story decision at G3.
12. **Every `unverifiable` verdict carries one of the four causes**; the G2 summary reports the
    breakdown, and **no gate blocks on `unverifiable`.**
13. `out_of_scope` verdicts are collected into a per-run list of systems the scan did not cover —
    consumable as evidence for 003.6.
14. **Verdicts land where H.1a says**: refuted corrected in place, unverifiable marked in place,
    neither listed in §16, and the coverage roll-up in the enrichment report rather than in v2.
    *(The report itself is TASK-V2-006; this task supplies its data, and stands alone without it.)*
15. `build_checks.py` green; full fixture sweep green; registry re-published.

### Proof

`fixtures/expectation/` covering each quadrant, plus:

- `prescriptive_not_deleted` — a requirement absent from code survives enrichment intact, with a scope
  finding filed. **The single most important case in this task**
- `update_absent_escalates` — the MCC case: `modify_existing`, nothing found, escalation raised
  naming all three causes
- `unclear_does_not_default` — an `unclear` assertion surviving to G1 escalates rather than going quiet
- `inferred_assertion_no_protection` — an assertion *not* traceable to a `business_requirement` source
  does not receive document-beats-code authority
- `gap_becomes_story` — a `new_capability` gap produces a Jira story with a **prospective** location
  drawn from analogy. **The most important case in Part G**: without it, greenfield work disappears
  from the plan
- `gap_undetermined_still_story` — analogy fails, location is `undetermined`, and the story is still
  produced rather than dropped
- `orphan_assertion_blocks_gate` — an assertion no arm picked up produces no outcome, and **G2
  refuses**. This is the hole totality exists to close: today it passes every check by being absent
- `already_satisfied_needs_decision` — `new_capability` × found; no story is legitimate, but only as a
  recorded decision, never as silence
- `unverifiable_causes` — the four causes are distinguished, the G2 summary reports the breakdown, and
  **the gate is not blocked** by any of them
- `out_of_scope_collected` — an `out_of_scope` verdict names the system it concerns and reaches the
  per-run coverage list

---

## [ ] TASK-V2-006 — the Enrichment Report: how much to trust v2, at G2

> **Also carry the boundary tally** *(added 2026-08-23)*. Every boundary record names a **system**, an
> **interface** and a **field** that went undetermined — *"MPT crossing reached PeopleSoft; repo not
> acquired; producer-side impact undetermined."* Individually that is a footnote. **Aggregated across
> runs it is a business case for acquiring a repo**, stated in evidence rather than in preference:
> *"MPT crossing reached PeopleSoft on 14 of the last 20 interchange changes; producer-side impact
> undetermined every time."* The records already exist — only the count is missing, and it is the
> cheapest argument available for the one thing that would most improve coverage.

> **Candidate** — raised in the Stage 3 review of 2026-08-16. Third in the family with the **Run
> Brief** (001, read at G0) and the **Ingest Report** (002, read before Stage 2). Same principle each
> time: **a report on how well the stage performed, kept out of the documents about the change.**

### Why this exists

v2 is what G2 approves and what every later stage builds on — yet nothing tells the operator *how much
of it to trust*. Were all the assertions accounted for? How much rests on claims that were never
verified? Did the analysis that should have run actually run? How big is the queue they are about to
work through?

All of that is computed during Stage 3 and then discarded. This surfaces it on one page.

**It stands alone.** Verdict breakdowns, §16 counts, escalation counts and runtime are available from
the pipeline as it is today; a useful first version needs none of the other tasks. The others then
enrich it — 005 adds assertion accounting and unverifiable causes, 004 adds reconciliation counts,
003.5 adds pass activation.

Third in the family with the **Run Brief** (TASK-V2-001, read at G0) and the **Ingest Report**
(TASK-V2-002, read before Stage 2). Same principle each time: **a report on how well the stage
performed, kept separate from the documents about the change.** This one tells the operator how much
to trust v2 before approving it.

```
ENRICHMENT REPORT — discover_interchange_debt_repay
2026-08-16 14:22 · v1 frozen at G1 09:41 · 5 repos scanned

ASSERTIONS                    12 in §8
  accounted for               12 of 12                          ok
  → impacts                    9 assertions → 31 §16 entries (found)
  → gaps                       2 assertions →  4 §16 entries (3 prospective, 1 undetermined)
  → already satisfied          1 assertion  — A-7, operator decision recorded

CLAIM VERIFICATION            23 claims
  confirmed                   14
  refuted                      3   corrected in place; 2 triggered reconciliation
  unverifiable                 6
      out_of_scope                 4   PeopleSoft (3), mainframe scheduler (1)
      claim_too_vague              1   §3.2
      ambiguous                    1   §11.4
      not_in_code                  0

NOT SCANNED — evidence for estate expansion
  PeopleSoft                   4 claims could not be checked
  Mainframe scheduler          1 claim could not be checked

PASSES
  interchange                 ran · 3 sections · 11 findings
    ├─ qualification          ran      probe INT-P1 = yes, sourced mandate §4.2
    └─ pricing                NOT RUN  probe INT-P2 = no,  sourced mandate §2.1
  clearing                    not declared

ESTATE WALK                   closed at depth 3
  scanned                     stratus (floor) · tandem (KB) · settlement (crossed)
  crossings                   pti_gen → stratus (2 fields) · submission → settlement (1)
  BOUNDARY                    mpt → peoplesoft (producer): declared, not acquired.
                              0 sites scanned; producer-side impact undetermined.
  floor                       3 of 3 assessed

RECONCILIATION
  candidates considered       18
  genuine conflicts            2   → walkthrough
  dismissed                   16   recorded with reasoning

WALKTHROUGH QUEUE              7 items
  source corrections           3
  human contradictions         2
  analyses disagreeing         2

RUNTIME                       41 min   arms 28 · interchange 6 · reconciliation 4 · apply 3
```

**What that buys at G2, on one page:** every assertion is accounted for; four claims rest on a system
outside the estate; the pricing sub-pass deliberately did not run, with the source of that decision
visible; sixteen potential conflicts were *considered and dismissed* rather than never noticed; and the
operator's queue is seven items rather than seventy.

Sections drawing on other tasks (reconciliation counts, pass activation, runtime) appear **only when
those tasks are built** — the report degrades gracefully rather than requiring them.


### Where the sections come from

| Section | Source | Available today? |
|---|---|---|
| Claim verification counts | Arm 2 verdicts | **yes** |
| §16 entry counts | Arm 1 output | **yes** |
| Walkthrough queue size | escalations | **yes** |
| Runtime | telemetry.jsonl | **yes** |
| Assertion accounting | TASK-V2-005 Part G | needs 005 |
| Unverifiable causes · not-scanned list | TASK-V2-005 Part H | needs 005 |
| found vs prospective split | TASK-V2-005 Part G | needs 005 |
| Reconciliation counts | TASK-V2-004 | needs 004 |
| Pass / sub-pass activation | TASK-V2-003.5 | needs 003.5 |

### Depends on

- `core/scripts/enrichment.py`, `core/scripts/schemas/enrichment.schema.json`
- `core/scripts/solution_intent_validator.py` — where G2 is surfaced
- `core/scripts/telemetry.py`, `ledger/telemetry.jsonl` — runtime
- `core/scripts/apply_enrichment.py` — runs after it, before G2
- `overlays/claude/prompts/start-enrich.md`,
  `overlays/copilot/.github/prompts/start-enrich.prompt.md`

### Reads

- `core/scripts/run_brief.py` and `core/scripts/ingest_report.py` **if built** — match their form and
  vocabulary; three reports in one family should not read like three different products
- `docs/TECH_SPEC.md` — G2's preconditions and the run-workspace layout

### Creates / edits

| Path | Action |
|---|---|
| `core/scripts/enrichment_report.py` | create |
| `core/scripts/solution_intent_validator.py` | edit — surface the report at G2 |
| `overlays/*/…/start-enrich*` | edit — produce it after apply, before G2; **both overlays identically** |
| `fixtures/enrichment_report/` | create — cases + `verify_enrichment_report.py` |
| `docs/TECH_SPEC.md` | edit — add to the run-workspace layout |

### Acceptance

1. `enrichment_report.md` is produced on every `/start-enrich` run and surfaced at G2.
2. **It degrades gracefully.** Sections whose source task is not built are omitted — never rendered
   empty, never blocking. *(Without this the report cannot exist until half the catalogue is done,
   which defeats a catalogue you pick from.)*
3. Every count it reports is derived, never re-computed independently of the artifact it describes —
   two components counting the same thing will eventually disagree.
4. It reports **only about the run**, never about the change. Nothing here duplicates v2.
5. Where a pass did not run, the report says so **and why**, with the source of that decision.
6. **The walkthrough queue size is flagged when it exceeds a threshold** (start at 15) — a calibration
   signal, never a blocker. *Baseline as of 2026-08-17 is ~4 items per run.* Eight escalation sources
   now exist, each choosing its own threshold independently and nobody owning the aggregate; this is
   the tripwire that catches one of them over-firing before the queue quietly becomes unreadable.
6. `build_checks.py` green including overlay parity; full fixture sweep green; registry re-published.

### Proof

`fixtures/enrichment_report/` covering: a clean run; a run with unverifiable claims of every cause; a
run with gaps both prospective and undetermined; a run where a sub-pass did not activate; and — the
important one — **a minimal run with none of 003/004/005 built**, proving the report renders correctly
from what exists today.

---

## [ ] TASK-V2-007a — amend D-A15 on the ladder *(do this first — it unblocks three tasks)*

### Why this exists

**007, 008 and 009 are all stalled behind one decision.** D-A15 in
`docs/design/ADR-008-solution-intent-pivot.md` pins a Jira mapping that does not match how the team
works, and ADR-008 is **Accepted and normative** — so the template cannot be edited until the ladder
is amended. This task is that amendment and nothing else: a docs change, no code.

It is listed first because it is **small and blocking**. Two table rows and one retired consequence.

### Part A — the source table

```diff
  | Jira level     | Source                                          | Available at |
- | Initiative     | the document itself — §1 identity, §2, §4       | v1           |
- | Deliverable    | §7 Deliverables                                 | v1           |
- | Epic           | §8 Business requirements — one epic per req     | v1           |
+ | Initiative     | REFERENCED — a quarterly container; key at G0    | not authored |
+ | Deliverable    | REFERENCED — a quarterly container; key at G0    | not authored |
+ | Epic           | ONE PER ARTICLE; §8 reqs in its description      | v1           |
  | Story          | Arm 1 landing points + §16 derived impacts      | v2 only      |
```

**In practice** (V, 2026-08-22): Initiative and Deliverable are **standard per quarter** and every
article change hangs from them. They already exist; the run attaches to them. One article is one run,
so **one run produces one epic and its stories**.

### Part B — retire one of the three consequences

```diff
- **The §7→§8 trace is load-bearing.** It physically builds the Jira parent-child
-   hierarchy; an orphan requirement yields an Epic with no parent Deliverable.
+ **RETIRED.** The epic's parent is a referenced key, so the trace no longer builds
+   the hierarchy. The orphan-requirement check it gave as a side effect becomes an
+   EXPLICIT jira_validator check (007) — losing a check silently is worse than
+   never having had it.
```

The other two consequences stand unchanged: *Jira cannot be authored from v1* (so G3 follows G2 for a
reason), and *§16 has a dual role* and must be machine-consumable.

### Part C — clarify the sizing rationale, do not delete it

D-A15 argues **"a business requirement is epic-sized, not story-sized"** — *"carry the 2-byte
indicator in field 48 needs parser changes, validation changes, test updates and certification. That
is a body of work, not a unit."*

**That observation survives; only its issue mapping changes.** A requirement is still far bigger than
a story — it is now represented as a **section of the epic's description** rather than as its own
issue. Add a note saying so, or a later reader will take the retired mapping as a retired argument
and start authoring stories straight off requirements, which is exactly what the paragraph exists to
prevent.

> **Open question for the amendment to settle:** if every requirement is epic-sized, an article
> carrying several of them yields one epic holding several bodies of work. Confirm that matches how
> the team sizes epics in practice — or record that articles typically carry one substantive
> requirement plus minor ones, which makes the concern theoretical.

### Part D — FR-JR-01 says the same thing and must move with it

`docs/REQUIREMENTS.md` **FR-JR-01** restates the mapping independently:

> *The plan is four-level: Initiative ← the SI itself · Deliverable ← §7 · Epic ← one per §8
> requirement · Story ← derived from §16 evidence + §7 non-code work.*

Amend both or they drift — and REQUIREMENTS.md is the WHAT layer, so a stale FR is worse than a stale
ADR. **FR-JR-03** should be checked too: it requires every story to trace to a §16 entry or a §7
deliverable, which is unaffected, but it is worth confirming rather than assuming.

### Acceptance

- D-A15's table and the retired consequence are amended in place, with a dated amendment note in the
  style ADR-008 already uses for its own supersessions.
- The sizing rationale carries its clarifying note.
- FR-JR-01 matches; FR-JR-03 confirmed unaffected.
- No code changes. `jira_template.payment_brand.yaml` is untouched by this task — that is 007.

### Reads

- `docs/design/ADR-008-solution-intent-pivot.md` — **D-A15** in full, including its three consequences
- `docs/REQUIREMENTS.md` — **FR-JR-01**, **FR-JR-03**, and the ADR-008 supersession notice at the head
- `core/templates/payment_brand/jira_template.payment_brand.yaml` — what 007 will change once unblocked

### Creates / edits

- edit `docs/design/ADR-008-solution-intent-pivot.md` — D-A15
- edit `docs/REQUIREMENTS.md` — FR-JR-01

### Proof

A docs change, so the proof is the ladder itself: `python3 core/scripts/build_checks.py` stays green,
and no §10 check regresses. Then 007 becomes executable, which is the point.

### Depends on

Nothing. **This is the front of the queue** — 007, 008 and 009 all wait on it.

---

## [ ] TASK-V2-007 — the Jira hierarchy does not match how the team actually works

### Why this exists

`jira_template.payment_brand.yaml` assumes the run **authors all four levels** from the Solution
Intent, one source each (D-A15):

```
Initiative   ← §1 identity · §2 problem · §4 objectives      created by the run
Deliverable  ← §7, one per D-id                              created by the run
Epic         ← §8, ONE PER REQUIREMENT                       created by the run
Story        ← §16 impacts + gaps, §7 non-code work          created by the run
```

**That is not the shape in use** (V, 2026-08-22). In practice:

```
Initiative   pre-existing, standard for the QUARTER          REFERENCED, not created
Deliverable  pre-existing, standard for the QUARTER          REFERENCED, not created
Epic         ONE PER ARTICLE — all requirements inside it    created by the run
Story        §16 entries                                     created by the run
```

One article is one run, so **one run produces one epic and its stories.** Initiative and Deliverable
are quarterly containers every article change hangs from.

> **This reopens D-A15, a pinned decision, so it is raised rather than applied.** Nothing here is
> edited into the template until **TASK-V2-007a** lands the ladder amendment. The gap is real either way: the
> template as written would author two issues that already exist and split one article into N epics.

### What changes

**A. Two levels are referenced, not authored.** `UI_INPUT.jira` must carry the target **initiative
key** and **deliverable key** for the quarter, validated at G0 by the Run Brief (TASK-V2-001). The
run attaches its epic to them.

*Knock-on:* Deliverable's `local_id: "D-id — the idempotency anchor"` stops applying. We no longer
create it, so it anchors nothing. **Idempotency moves to the epic** — see Part C.

**B. Epic is the article, not the requirement.** Its source becomes the document rather than a single
§8 entry, and **all requirements live in the epic's description**, enumerated with their assertions.
Stories still come straight off §16 entries and trace back by `assertion_ref`.

*What is lost, and should be replaced:* the template makes the §8→§7 `Deliverable:` trace
**load-bearing** — *"it physically builds the parent-child hierarchy, so an orphan requirement yields
an Epic with no parent."* Under the new shape the epic's parent is a given key, so that trace has no
structural role and the **orphan-requirement check disappears with it**. It should be re-added as an
explicit `jira_validator` check rather than lost as a side effect.

*What is gained:* D-A15's rationale — *"a business requirement is epic-sized, not story-sized"* —
still holds; it just no longer needs its own issue to say so. And the run authors two levels instead
of four, which is materially less to get right.

**C. §INT-n maps to the epic description.** With only Epic and Story authored, everything a reader
needs must land in one of them, so the type sections' *context* travels with the epic that explains
it. This also closes the `code_author` gap: it reads *plan + §16 + repo*, never v2, so under any other
mapping the specialist synthesis would be invisible to the stage that writes code.

**D. Idempotency needs an anchor that survives a re-run.** With Deliverable no longer created, the
epic is the top of what the run owns. A second run on the same article must **update** its epic and
stories, not duplicate them. `Story.local_id: "S<n>"` is positional and shifts if §16 renumbers —
`assertion_ref` plus the §16 entry id is the stable pair. *(This is the Stage-4 idempotency finding
raised alongside this one; they resolve together.)*

### Acceptance

- `UI_INPUT.jira` carries initiative and deliverable keys; the Run Brief shows them at G0 and the
  plan fails loudly if either is absent or unresolvable.
- One article yields exactly one epic, whose description enumerates every §8 requirement.
- Every §16 entry still yields exactly one story or an explicit disposition (unchanged).
- `jira_validator` gains an explicit orphan-requirement check to replace the one the §8→§7 trace
  used to provide structurally.
- A re-run on the same article updates the existing epic and stories rather than creating duplicates.

### Reads

- `core/templates/payment_brand/jira_template.payment_brand.yaml` — the four levels, one source each,
  and the `forbidden` list this task amends
- **Target state §3** — the flow and where `sections:` are declared
- **003.1a** — the §16/§INT-n split; §INT-n's Jira destination is decided here
- `docs/` — **D-A15** itself, which must be amended before any of this is applied

### Creates / edits

- edit `core/templates/payment_brand/jira_template.payment_brand.yaml` — Initiative and Deliverable
  become referenced; Epic's source becomes the article; `evidence` decouples from the flag
- edit `core/scripts/jira_plan.py`, `core/scripts/jira_validator.py` — the orphan-requirement check
  that the §8→§7 trace used to provide structurally
- edit `app/frontend` + `UI_INPUT` schema — the initiative and deliverable keys
- edit `core/skills/jira_author.skill.md`

### Proof

`fixtures/jira_plan/verify_jira_plan.py` extended: one article yields exactly one epic; a missing
initiative key fails loudly at G0; a re-run updates rather than duplicates; an orphan requirement is
caught by the explicit check rather than by hierarchy accident.

### Depends on

D-A15 amended on the ladder first. `jira_template.payment_brand.yaml`, `core/skills/jira_author.skill.md`,
`core/scripts/jira_plan.py`, `core/scripts/jira_validator.py`, and TASK-V2-001 (Run Brief) for the G0
validation of the two keys.

---

## [ ] TASK-V2-008 — `validation.md`: the post-install validation document, produced at Stage 5

### Why this exists

The epic needs a **post-install validation document** covering the whole article — positive
validations (the change does what it should) and negative validations (it does **not** do what it
should not: *"MCC 7011 moved to the new tier; confirm 5411 did not"*).

`arch.md` gestures at this as a story-level **`test_matrix`** field, and `jira_validator` hard-checks
*"test cases grounded in §16"* — but `jira_template`'s story fields declare no such field. **The
`test_matrix` framing is wrong** (V, 2026-08-22): this is one **epic-level document**, not per-story
metadata.

### Why Stage 5 and not Stage 4

**Positive cases ground in §16. Negative cases come from the code**, and `jira_author` cannot read it.

| Stage | Reads |
|---|---|
| 4 — `jira_author` | v2 §16 + §7 + `jira_template` — **no repo** |
| 5 — `code_author` | plan + §16 + **repo** |

§16 records what *changed*; the negative set is what sits alongside each impact and deliberately did
not. That is only visible in the source. Stuffing the not-impacted siblings into §16 was considered
and rejected — §16 holds impacts and gaps only (003.1a), and a story-per-entry spine cannot carry
non-impacts.

**So it is generated at Stage 5, from the same read.** `code_author` already opens each impact site to
draft its hunk; the adjacent entities are in that same view. Positive and negative cases fall out of
work already being done, and the document attaches to the epic Stage 4 created.

### Delivery

- Produced alongside `code_changes/`, behind **G4** like everything else Stage 5 writes.
- Attached via the **existing** Jira write path — `code_push.py --confirm --push` already branches,
  commits with the Jira prefix, and records the commit on each story. An attachment is the same door;
  no new integration.
- One document per epic (one per article), not one per story.

### Acceptance

- Every §16 impact yields at least one **positive** case, traceable to its entry id.
- Every impact site yields the **negative** cases visible in its own source read — the adjacent
  entities the scan saw and did not report — or an explicit statement that none exist.
- The document is attached to the epic, not to stories.
- A fixture proves it. **`fixtures/code_author/` and `fixtures/code_push/` do not exist** (see
  PARKED), so this task creates the first Stage-5 fixture rather than extending one.

### Reads

- **005 Part G.3a** — the §16 entry shape; positive cases ground in these
- `core/skills/code_author.skill.md` — what Stage 5 already reads and drafts
- `core/scripts/code_push.py` — the existing Jira write path an attachment rides on
- `vdi_design.md` §7 — `jira_validator`'s *"test cases grounded in §16"* check

### Creates / edits

- create the `validation.md` generation step in `core/skills/code_author.skill.md`
- edit `core/scripts/code_push.py` — attach to the epic on confirm
- create `fixtures/code_author/` (this task or 009, whichever lands first)

### Proof

A fixture where a §16 impact yields a positive case traceable to its entry id, an adjacent
not-impacted entity yields a negative case, and a run with no adjacent entities states that
explicitly rather than emitting an empty section.

### Depends on

TASK-V2-007 (the epic is the article, and is what the document attaches to).
`core/skills/code_author.skill.md`, `core/scripts/code_push.py`.

> **Also settles the `test_matrix` question.** No `test_matrix` field is added to `jira_template`'s
> story fields. If `jira_validator`'s *"test cases grounded in §16"* check exists on the VDI, it
> should be re-pointed at this document; if it does not exist, it and the `arch.md` wording should be
> corrected together rather than one implying the other is built.

---

## [ ] TASK-V2-009 — Stage 5 has no validator and no fixtures; the second external mutation is unchecked

### Why this exists

`arch.md` is explicit that there are **exactly two writes to the outside world — the Jira push (G3)
and the code push (G4)**. Stage 4 guards its write from both sides. Stage 5 guards neither.

| | per-run validator | fixture |
|---|---|---|
| **Stage 4** | `jira_validator.py` — scores the plan, hard checks, surfaces G3 | `verify_jira_validator.py`, `verify_jira_plan.py`, `verify_jira_push.py` |
| **Stage 5** | **none** | **none** |

**31 `verify_*.py` exist across the VDI. Zero are Stage 5.** Between `code_author` drafting a change
and `code_push.py` writing a branch, the only thing standing there is a human reading diffs — which is
the position Stage 4 explicitly refused to accept when it built `jira_validator`.

### Part A — `core/scripts/code_validator.py` (the deliverable)

Runs on **every real run**, against the real repo and the real output, between `code_author` and G4.
Hard checks, in the same spirit as `jira_validator`'s:

- every **EDIT story** yields a hunk, **or an explicit stated reason it does not**
- every hunk **cites a §16 entry that exists** — a dangling citation is a load-time class error, the
  same shape as a probe activating a pass that does not exist
- **no hunk for a `non_code` story** — the rate-table case from TASK-V2-007. *This is the most
  valuable check in the set, because its failure is silent:* a phantom C edit for a rate-table story
  looks like work until somebody reads it at G4
- every file touched lives in **the repo that story named** — 003.6 puts a repo qualifier on every
  §16 entry and flows it to `code_location`; nothing currently checks the draft respects it
- every **prospective-location gap** is disposed of explicitly — drafted, refused, or recorded, never
  dropped (Part G's whole concern is greenfield work falling out of the plan)

**It also parses every modified file.** Nothing anywhere in Stage 5 currently checks the draft is
even *syntactically valid* — a hunk with an unbalanced brace, or applied at a wrong offset producing
garbage, reaches G4 looking exactly like a correct one and costs a human review cycle to find.

- **Parse, not compile.** A real build of Stratus likely needs the mainframe toolchain (`tpf_compat.h`
  is in the fixture repo), so a compile is not proposed. But `.venv` already carries the **tree-sitter
  C toolchain** for the frozen extractor (ADR-001), and parsing a modified file is the same operation
  the code map performs on every file, every run. **Zero new dependencies. A parse failure blocks G4.**
- **Structural delta, for free.** The extractor already yields the file's structure, so the validator
  can also compare before and after: if `route_table.c` had 14 functions and the draft leaves 13, and
  no story asked for a removal, that blocks too. Accidental deletion is the other silent failure a
  human skims past.

**What it does not check:** whether the generated C is any good. That is model output, not
deterministically assertable, and pinning it would make the check brittle. Correctness of the change
is what **G4** is for — a human reads the diffs. The validator guarantees nothing was **misrouted or
silently dropped**; the human judges whether the change is right. Same split as `flow_plan.py`:
compute the thing whose error is invisible, let the model do the reading.

### Part B — the fixtures that prove the validator

Same logic, pinned inputs. `fixtures/c_repo/` already exists and is the model to follow — a small
checked-in C repo with `expected_components.json` holding the answers. Reuse it rather than inventing
a second fake repo.

**`fixtures/code_author/`** — three stories chosen to cover the branches:

| Story | §16 entry | Must produce |
|---|---|---|
| S1 | impact, `code_location: route_table.c:88-140` | a hunk **citing §16.3** |
| S2 | impact, `flag: non_code` (rate table) | **no hunk**, a note with its reason |
| S3 | **gap**, `location: [prospective]` | whatever we decide — **the fixture freezes it** |

S3 is the point of leverage: Stage-5 behaviour on a prospective gap is currently undefined, and
writing the fixture is what forces the decision.

**`fixtures/code_push/`** — the critical assertions are **refusals**:

- without `--confirm`, **no branch and no commit**
- without `--push`, **no remote write** — two separate gates, and both must hold independently
- branch name and commit message carry the Jira key
- each story gets its commit recorded

The push's two REST calls are `[TBD — VDI]` placeholders, so the fixture proves the **decision logic
and the refusals** against a stub, never a network call. `verify_jira_push.py` already does this for
the other mutation — mirror it rather than inventing an approach.

### Part C — the multi-repo push

003.6 puts a **repo qualifier on every §16 entry**, which flows to `code_location`, so one epic can
span two repos — a Stratus story and a PeopleSoft story arriving by crossing. But `code_push.py
--confirm --push` branches, commits and pushes **singular**. This is the first place multi-repo becomes
a **write** rather than a read: everything upstream is read-only, so a partial failure costs nothing;
here it means one repo is pushed, another is not, and the epic claims both.

**Branch naming — config, with per-repo overrides:**

```yaml
push:
  branch_template: "feature/{jira_key}"     # default for every repo
  overrides:
    peoplesoft: "PDLC/{jira_key}"           # where a repo has its own convention
```

Different remotes, so the same name across repos does not collide; the override exists for house
conventions. The commit message carries the Jira key in every repo, unchanged.

**Failure semantics — three phases, no rollback, always report.** There is no transaction across two
remotes, so the design is about what a half-done push leaves behind:

```
PREFLIGHT   every repo: clean tree, branch name free, push rights, target exists
            → ANY failure aborts before anything is written ANYWHERE

COMMIT      every repo, locally — reversible, a local commit can be reset

PUSH        every repo, in order
            → on failure: STOP, do not attempt further repos
              report per-repo status; successful pushes stay pushed,
              unpushed commits remain as local branches for retry
```

**Never delete a pushed branch to "roll back."** If anyone has pulled it that makes things worse, and
a partial push is a **fact to report, not to hide** — the same silence rule as everywhere else:

```
PUSH
  stratus       ✓ pushed   feature/PBI-4471   3 commits
  peoplesoft    ✗ FAILED   auth rejected — local branch retained, retry with --resume
```

**Preflight is what makes this cheap.** Nearly every realistic failure — dirty tree, name taken, no
rights — is catchable before the first write. A genuine mid-push failure is rare, and the retained
local branch makes it recoverable. Effort is grouping `code_changes.json` by repo qualifier and
tracking per-repo status; not a redesign.

### Acceptance

- `code_validator.py` runs in the Stage 5 flow before G4 and blocks on any hard-check failure.
- A draft spanning two repos produces two branches, two commits and a **per-repo push report**; a
  preflight failure in any repo writes nothing anywhere.
- Every modified file **parses** with the frozen extractor, and any structural deletion no story asked
  for blocks the gate.
- Both fixture directories exist, are runnable standalone, and are green.
- The full sweep (`find fixtures -name "verify_*.py"`) covers all five stages, not four.
- The validator and the fixtures **share one implementation** of the checks — written once, called
  with pinned inputs by the fixture and with live output by the validator.

### Reads

- `vdi_design.md` §7 — Stage 5's inputs, and `jira_validator` as the model to mirror
- `fixtures/jira_plan/verify_jira_validator.py` — the per-run validator + fixture pattern to copy
- `fixtures/jira_push/verify_jira_push.py` — how the *other* external mutation proves its refusals
- `fixtures/c_repo/` — the fake-repo pattern; reuse rather than inventing a second one
- **005 Part G.2** — prospective locations, which fixture S3 must pin

### Creates / edits

- create `core/scripts/code_validator.py`
- create `fixtures/code_author/` and `fixtures/code_push/` with their `verify_*.py`
- edit `core/scripts/code_push.py` — preflight, per-repo grouping, branch-template config
- edit `core/skills/code_author.skill.md` — call the validator before surfacing G4

### Proof

Both fixture directories green standalone, and the full sweep
(`find fixtures -name "verify_*.py"`) covers five stages rather than four. The push fixture's
critical assertions are **refusals**: no branch and no commit without `--confirm`; no remote write
without `--push`.

### Depends on

TASK-V2-007 (`non_code` widened, so the rate-table branch exists to test) and TASK-V2-008 (which adds
`validation.md` assertions to `fixtures/code_author/`). `core/skills/code_author.skill.md`,
`core/scripts/code_push.py`.

---

## [ ] TASK-V2-010 — symbol-level code map: locate precisely, still read whole

### Why this exists

**§16 line ranges are model-produced today.** An entry reads
`location: src/routing/route_table.c:88-140` — and 88–140 came from the model reading the file and
reporting a range. That range then flows to the Jira story and on to `code_author`, which drafts
against it.

That is the class the design says to **compute**: a wrong range is invisible. It looks entirely
plausible in a story, and nothing downstream can tell an accurate range from an off-by-forty one.

**And the parser already has it.** The C extractor is tree-sitter (ADR-001), which returns exact node
ranges for every function and then discards them. We are asking a model to derive something a parser
computed and threw away.

### Part A — the record shape

Nested and **additive**; nothing that reads the map today breaks.

```json
{
  "path": "src/routing/route_table.c",
  "module": "c:rating",
  "purpose": "interchange rate table load and lookup",     ← file level, unchanged
  "depends_on": ["include/brand.h"],                        ← file edges, unchanged
  "used_by": ["src/billing/fee_calc.c"],
  "coverage": "symbol",                                     ← was "coarse"
  "symbols": [
    { "name": "load_rate_entry", "start": 88,  "end": 140 },
    { "name": "apply_rate",      "start": 142, "end": 190 }
  ]
}
```

- **File-level `purpose` stays.** *"What is this file for"* is a different question from *"what does
  this function do"*, and the file answer is what makes the map skimmable.
- **File edges stay.** `depends_on`/`used_by` remain file-level. Symbol-level `calls`/`called_by` are
  a **later** addition — call-graph extraction is a materially bigger tree-sitter job than node ranges,
  and ranges alone deliver most of the value.
- **`coverage` already expresses granularity** and currently reads `"coarse"`. It becomes `"symbol"`
  for C. When the other repos land in languages with no extractor yet, their maps stay `"coarse"` and
  **the map says so** — rather than the pipeline assuming a precision it does not have (003.6).

### Part B — the governing rule

> ## Symbols locate. They never bound what is read.
>
> **The scan pulls the whole file, always.** Symbols are used to *identify* which files are impacted,
> to *address* a finding precisely, and to *triage* candidates before reading. They are never used to
> narrow what the assessment actually reads.

This is the same rule as *"resolution creates a search obligation, not a search boundary"*, in a new
place — and it fails the same way if broken. A function does not stand alone: file-level statics,
macros, includes, adjacent functions and the surrounding control flow are all context that decides
whether a location matters. **Read only the function body and the pass has silently become a lookup**
— finding less, and looking exactly like a pass that found less because there was less.

`code_validator.py` (TASK-V2-009) should enforce it: an assessment that pulled a range rather than a
file is a failure, not an optimisation.

### Part C — what it buys

| | Today | With symbols |
|---|---|---|
| **§16 location** | a model-asserted range | **derived** from the parse |
| **Triage** | pull the file to learn if it matters | narrow from the map, then read the ones that survive |
| **§16 granularity** | one entry per file | one per function where they differ — and D-A15 says **§16 granularity *is* story granularity** |
| **Analogy search** (Part G.2) | *"comparable IRDs registered in `brand_registry.c:120-180`"* | *"registered in `register_brand()`"* — a story someone can pick up |
| **Interface sites** | `reads_at: mpt_loader.c` — **any** impact in that file promotes | `reads_at: mpt_loader.c:load_mpt_record` — only impacts in that function do |

That last row is the quiet one: promotion is containment, so a tighter site means fewer false
crossings from a file that both reads MPT *and* does something unrelated.

### Deliberately deferred

- **Purpose per function.** One model call per symbol; a repo with 3,000 functions is 3,000
  generations. Cost lands per-commit rather than per-run (the map is cached on
  `(commit_sha, profile_sha)`), so it is affordable — but add it only if closure proves too loose
  *with* ranges, which is measurable. If it is added, carry `purpose_source` and `purpose_quality`
  down with it: at function level the difference between a purpose read from a declared comment and
  one inferred from the body is the difference between evidence and a guess.
- **`calls` / `called_by`.** Symbol-level closure. Needs call-graph extraction.

### Watch for

**§16 bloat.** Finer granularity means more entries, and §16 entries become stories. A change
touching one file with eight relevant functions goes from one story to eight. Often that is *more
accurate* — those may genuinely be eight units of work — but 003.6 already flags *"watch §16 for
bloat"* and 006 carries a walkthrough-growth tripwire. **Measure it on the first real run** rather
than assuming either way; the granularity being *available* does not oblige using it at story level.

### Acceptance

- Every file entry with `coverage: "symbol"` carries `symbols[]` with `name`, `start`, `end`.
- Every §16 `location` on a symbol-covered file **resolves to a declared symbol range** — no
  model-authored line numbers.
- A fixture proves the scan still reads the **whole file** when assessing, not the symbol range.
- `expected_files.json` and `expected_components.json` in `fixtures/c_repo/` updated; the extractor
  is **re-frozen** through the existing path (a human commits, `extractor_manifest` records the new
  blob sha, and a post-freeze edit cannot pass silently).

### Reads

- `core/extractors/c_extractor.py` — the tree-sitter walk that already computes node ranges
- `core/extractor_manifest.yaml` — the freeze record, and what re-freezing requires
- `fixtures/c_repo/expected_files.json` — the current file-entry shape this extends
- **ADR-001** — why the extractor is frozen and deterministic in the first place
- **005 Part G.2** — the analogy search that gains symbol-level prospective locations

### Creates / edits

- edit `core/extractors/c_extractor.py` — emit `symbols[{name, start, end}]`; set
  `coverage: "symbol"`
- edit `core/extractor_manifest.yaml` — **re-freeze**: new blob sha, recorded by a human commit
- edit `fixtures/c_repo/expected_files.json` and `expected_components.json`
- edit `core/skills/code_impact_assess.skill.md` — triage from symbols, **read whole files**

### Proof

`fixtures/c_repo/verify_code_map.py` asserts every symbol range resolves and matches the parse. A
second assertion is the important one: **a scan against a symbol-covered file reads the whole file**,
not the range — Part B is a fixture, not a comment.

### Depends on

`core/extractors/c_extractor.py`, `core/extractor_manifest.yaml`, `core/code_profiles/c_repo.profile.yaml`,
`fixtures/c_repo/`. Related: 003.6 (language mix and per-repo granularity), 009 (`code_validator.py`
enforces Part B), 005 Part G.2 (analogy search gets symbol-level prospective locations).

---

*Stage 5 review complete. Prospective-gap drafting remains the one undecided behaviour, and 009's
fixture S3 forces that decision when it is written — deliberately, since writing the fixture is what
makes someone choose.*

*(Code-map `commit_sha` drift was reviewed 2026-08-22 and **dismissed** — with the Stage 1 clone
pinned, the local repo does not move mid-run, and the remaining cases are operator-induced re-runs.
Risk judged too low to design against.)*
