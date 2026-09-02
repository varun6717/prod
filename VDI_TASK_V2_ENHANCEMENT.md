# VDI_TASK_V2_ENHANCEMENT.md — operationalising interchange on the VDI

**What this is.** One additional task spec for the VDI build, in the same form as the tasks in
[`VDI_TASK_V2.md`](./VDI_TASK_V2.md). It is kept in its own file because it was agreed after that
catalogue was written, and because it is the first task whose subject is **running the pipeline
against real interchange work** rather than improving a stage of it.

**Relationship to `VDI_TASK_V2.md`.** That file stays the deliverable and the source of truth for
everything it already covers. This file **adds TASK-V2-011** and, where it changes something
`VDI_TASK_V2.md` pins, says so explicitly under *Amendments to existing decisions*. Nothing here
reopens a decision without naming it. When this task is picked up, fold its menu row into
`VDI_TASK_V2.md`'s menu table.

**Frame of reference.** Every path refers to the **VDI build repo** (`PDLC_App_v3`, branch `main`)
as recorded in [`vdi_tree.md`](./vdi_tree.md), with behaviour as described in
[`vdi_design.md`](./vdi_design.md). No path here refers to the external Claude Code build.

**Provenance.** Designed in review 2026-08-28 → 2026-08-30. The proposal was V's; the analysis
below is what came out of working it against the target state. Recovered from the session
transcript 2026-08-31 — it had never been written to disk.

**Menu row** — fold into `VDI_TASK_V2.md`'s menu when this is picked up:

| # | Buys you | Size | Needs first |
|---|---|---|---|
| **011** Operationalise interchange | Turns the framework into a validated process for real MC/Visa interchange work: the change-type matrix from history, the new-mnemonic path closed end to end, and replay scoring against what actually shipped | L | 003.2 (Parts B–D) · 007 (Part E) · 009 (Part F) |

---

## [ ] TASK-V2-011 — operationalise interchange: mine the history, close the new-mnemonic path, replay to validate

> **Candidate** — raised 2026-08-28 in planning the post-migration phase. Parts A–G are separable and
> can be taken in order; Part A is days of desk work with no code and unblocks everything else.

### Why this exists

The framework in TASK-V2-003 is declared against **one worked interchange change**. Nothing has
established that its declared types cover the interchange work that actually arrives, and nothing has
scored a run against what actually shipped. Two specific holes follow from that:

- **The type catalogue is guesswork until the history is read.** `flow.yaml` declares `interchange`
  with two probes. Whether that covers qualification changes, rate changes, new programs and whatever
  else the queue contains is an assumption nobody has tested against the closed Jiras.
- **A new mnemonic has no path through the pipeline.** `designator_to_mnemonic` has
  `on_unresolved: escalate` — unresolved is always an error. But a genuinely new program *cannot*
  resolve, by definition. So the most common greenfield interchange change escalates as a failure,
  and the work of creating the mnemonic, its qualification and its rate row has no route into the
  Jira plan at all.

### The governing insight — the taxonomy is a matrix, not a list

"Qualification / existing mnemonic", "qualification / new mnemonic", "rate update" are not sibling
change types. They are cells on two axes:

| | **existing mnemonic** | **new mnemonic** |
|---|---|---|
| **qualification** | `interchange` + INT-P1 | `interchange` + INT-P1 + *create* |
| **rate** | `interchange` + INT-P2 | `interchange` + INT-P2 + *create* |
| **both** | + INT-P1 + INT-P2 | + INT-P1 + INT-P2 + *create* |

This is already how `flow.yaml` works — one type, probes activating sub-passes. So the history
mining is **not** a search for new change types to declare; it is a **desk exercise to fill this
matrix**, and its real output is the exception list. **A Jira that fits no cell is the finding** —
it names a pass or a probe the flow does not have.

### What this task does *not* do

- No new change type, and no new Stage-3 skill. Everything below is config, one derived activation,
  one template, and drafting behaviour on a skill that already exists.
- No reopening of D-A15 (that is 007a's job), of the §16 / §INT-n split (003.1a), or of the resolve
  barrier (003.5).
- No push automation to PeopleSoft. The rate mod file is produced and attached; a human delivers it.

---

### Part A — mine the history into a matrix and a golden set · *no code* · **S**

Read every closed MC/Visa interchange Jira once, by hand, and write **one row per Jira**. Fixed
columns, so the rows become data rather than a throwaway spreadsheet:

| Column | Example |
|---|---|
| Jira key, network | `PBI-4471`, MC |
| program / designator(s) named in the article | IRD 0537 |
| mnemonic: new or existing | new |
| work: qualification / rate / both / **other** | both |
| systems actually touched | Stratus: `mapping.c`, `qual_rules.c` · PeopleSoft: 1 rate row · MPT: no |
| shipped how, and in what order | PeopleSoft first, Stratus 3 days later |
| effective date on the article | 2026-10-01 |
| article on file? shipped diff on file? | yes / yes |

**Two outputs:**

- **The matrix** — every Jira placed in a cell of `{existing, new} × {qualification, rate, both}`.
  The cells confirm what is already declared; **the `other` column is the deliverable**, because each
  entry is a missing pass or probe.
- **The golden set** — the rows that have *both* the article and the shipped diff (plus the rate
  change, where there is one). Start with **3–5**, chosen to cover the cells replayed in Parts B–G:
  one existing/qualification, one rate-only, one new-mnemonic.

**Do it by hand, and do it before writing config.** The classification is the declared configuration
that Wave 2 runs on, and the design's rule is *classification is evidence, not inference* — a human
placing each Jira with the article and the diff in front of them **is** the evidence. The 003.8 KB
classifier is for *runtime recommendation*; it cannot write the config it will later be scored
against, and 003.7a has not even established the corpus is viable.

**Two side-questions get answered for free — record them as you go:**

1. **How does a rate-table change actually reach PeopleSoft?** Every rate Jira in the corpus has an
   answer in its history. This settles the delivery channel and gives Part E its template.
2. **Did Stratus and PeopleSoft ever ship in the wrong order, and what broke?** Real incidents, not
   reasoning — the evidence for or against the deferred `sequence:` field (see Part D).

**Write the columns to match what 003.9 wants from the history KB.** The sheet is the hand-built
seed of the same rows the KB will later hold automatically; matching columns makes that an **import,
not a re-key**. Two fields the KB needs that a classification-only sheet would omit — the **shipped
diff** and the **rate change** — are exactly what makes a row usable as a golden run, so they are
required here too.

> **Matrix and golden set are different sizes; do not conflate them.** The matrix is **every** Jira,
> classification only — cheap, and completeness is the whole point, because the `other` list only
> means something if nothing was skipped. The golden set is **whichever rows have the full data**,
> which is expensive to assemble by hand. Once the KB carries the diff and the rate change per Jira,
> the golden set becomes *every row the KB has complete*, and 3–5 is simply the first batch verified
> by eye before the rest is trusted.

*Assumption to confirm:* the Jira corpus is reachable from the VDI via the existing connector
(`core/scripts/ingest_jira.py`, `core/adapters/jpmc_adapters/jira.py`), so **pulling** the tickets is
automatable even though **placing** them is not.

---

### Part B — the resolve quadrant: "new mnemonic" is derived, never asked · **M**

`on_unresolved: escalate` treats every unresolved designator as an error. It is an error **only if
the program was supposed to exist already** — which is a fact about the article, not about the code.

That fact already exists in v1. TASK-V2-005 Part A classifies every §8 assertion at Stage 2,
**code-blind**, as `modify_existing` / `new_capability` / `unclear`. Crossing it with the resolve
outcome gives four cells — this is **005 Part D applied to resolve**, not a new mechanism:

| resolve says | assertion says | Meaning | Action |
|---|---|---|---|
| resolved | `modify_existing` | normal — an update to an existing program | proceed |
| **unresolved** | **`new_capability`** | **new mnemonic** | file a §16 gap, activate the create path (Part C) |
| unresolved | `modify_existing` | genuine resolve failure | **escalate** — today's behaviour, unchanged |
| resolved | `new_capability` | article says new, code already has it | **scope finding** (005 Part E) — escalate |

**Nothing is asked and nothing is inferred.** The orchestrator computes the cell. There is no
operator probe for "is this a new mnemonic?" and no model deciding "this looks like a new-mnemonic
change" — which is the point, per *mechanical recall, model precision*.

**`unclear` has no cell, deliberately.** Per 005 Part A it is resolved at Stage 2, and if it survives
to G1 it is treated as `modify_existing` — the cautious direction, because that cell escalates rather
than going quiet. A schema that accepted `unclear` here would let the cautious default be configured
away.

The declaration, on the resolve pass in `change_types/interchange/flow.yaml`:

```yaml
resolve:
  - id: designator_to_mnemonic
    application: stratus
    substance: code
    skill: resolve_mnemonic.skill.md
    reads: [v1.assertions, stratus.code_map, networks.yaml]
    provides: [mnemonic, program_code, interchange_level]
    must_capture:
      - every designator or program name in v1 resolves to a mnemonic, or is
        listed unresolved with why
      - every resolved mnemonic carries the code location that defines it
      - every unresolved designator names the quadrant it fell in and the
        assertion whose type decided it            # NEW
    on_unresolved:                                 # was the scalar `escalate`
      modify_existing: escalate
      new_capability:
        file: gap                                  # §16, kind: gap (005 Part G)
        location: prospective                      # the mapping site resolve already reads
        activates: [qualification_impact]          # the create path — see Part C
    on_resolved:                                   # NEW — the fourth cell needs a home
      modify_existing: proceed
      new_capability: scope_finding                # 005 Part E
```

#### Why `resolved + new_capability` is a scope finding, not a shrug

Two independent sources disagree: the article says the program does not exist, the code says it does.
Worked example —

> Mandate: *"New program Commercial Payments Account – Large Ticket, designator MCPA-LT, IRD 0537,
> effective 2026-10-01."* → 005 Part A types the assertion `new_capability`.
> Resolve greps Stratus's mapping site and finds `{"MCPA-LT", MNEM_CLT}` already there.

Four things it could mean, **each a different piece of work**:

| Cause | What the work actually is |
|---|---|
| **Renamed** — the network re-designated an existing program; the *designator* is new, the mnemonic is not | Edit `MNEM_CLT`'s qualification and rate. Merchants already qualify to it, so there is a migration question |
| **Already built** — a prior phase, or someone implemented ahead of the article | Mapping and qualification stories already exist; the only real work is the rate row |
| **Stale or speculative** — added during a spike, never removed | Remove it, or it qualifies traffic against a rate nobody approved |
| **False match** — resolve matched the wrong thing | Resolve has a bug, and every downstream key is suspect |

Treated silently as new, the run drafts a **second** mapping entry for a designator already mapped,
and the real work — amending existing qualification, and whatever live traffic that affects — is
never located. Nothing in the code or the article settles which of the four it is, and each changes
the plan, which is the definition of scope-moving. The run reports:

> *"article says new; Stratus maps MCPA-LT → MNEM_CLT at `program_map.c:412` — which is it?"*

---

### Part C — the create path is a derived activation and a §16 gap, not a new pass · **M**

No new probe, and no new pass. Three sites already produce everything a new mnemonic needs:

| What must be created | Where its location comes from |
|---|---|
| the designator → mnemonic mapping | **resolve** already reads the one Stratus mapping site — that site is the gap's **prospective** location |
| the qualification criteria | `qualification_impact`, activated by the quadrant instead of by INT-P1 |
| the rate-table row | `pricing_impact` (INT-P2), landing as a **tabular** §16 location per 003.1a |

**Activation now has a second source, and it must be declared rather than implicit.** Today the
orchestrator unions every `activates:` across `probes.yaml`, and a pass no probe names is
unconditional. The quadrant adds activations that come from a **flow** file. Consequences to build:

- **003.2 schema rule 4 widens.** *"Every `activates:` names a pass that exists"* must now scan
  resolve outcomes in `flow.yaml` as well as `probes.yaml`. `flow_plan.py` refuses the plan
  otherwise; `verify_estate.py` gains the rejection case.
- **Derived activation is recorded with its cause**, in the same form as probe activation:
  *"`qualification_impact` activated by resolve outcome (unresolved + `new_capability`, designator
  MCPA-LT), not by probe INT-P1."* Otherwise the run cannot show why a pass ran.
- **Non-activation stays recorded too.** *"Create path not activated: every designator resolved."*
- **G2 counts a derived-activated pass as activated** — findings-or-non-event applies to it, and it
  enters the totality denominator like any other.

**The gap goes to §16, never to a type section.** 003.1a's rule holds: if it would become a Jira
story it belongs in §16. A new mapping entry, new qualification criteria and a new rate row are all
stories. §INT-3 and §INT-5 carry only the *context* — the pricing picture, where criteria live.

---

### Part D — the effective date replaces the ordering rule · **S**

A new mnemonic touches Stratus (mapping + qualification), PeopleSoft (rate row) and possibly MPT
(merchant setup), which raises the question of **order**: Stratus qualifying transactions to a
mnemonic PeopleSoft has no rate for breaks billing, while PeopleSoft carrying a rate nothing
qualifies to is harmless.

**The simpler constraint is the correct one: both sides must be in by the network's effective date.**
That date is when the program goes live, so between PeopleSoft landing and Stratus landing nothing is
live yet and order *inside* the window does not matter.

So `release_shape` gains one obligation rather than a derivation rule:

```yaml
release_shape:
  sections:
    - id: INT-4
      title: Release coordination
      must_capture:
        - the verdict — Stratus-only, PeopleSoft-only or integrated — with the
          interface field and the consumer read site that prove it
        - the effective date, sourced from the article, or [TBD — unsourced]   # NEW
```

The date is a **fact carried**, not a rule derived: cite-or-flag applies unchanged, and an article
with no stated effective date produces `[TBD — unsourced]` rather than a guess. `jira_author` carries
it onto **every story in the epic** as its deadline, which means `jira_template.payment_brand.yaml`
needs the mapping.

> **This keeps `sequence:` deferred, and records why.** `VDI_TASK_V2.md` 003.5 defers
> `sequence: producer_first | simultaneous`, to *"revisit when a second interface is floored"*. The
> new-mnemonic case looked like the trigger to un-defer it; the effective date discharges the same
> risk for less — one sourced fact instead of a derivation rule over three interface change shapes.
> **The seam is unchanged**: the verdict is still one value, so adding `sequence:` later breaks
> nothing. Part A's second side-question supplies real evidence either way.

---

### Part E — the PeopleSoft rate mod file: a Stage-4 artifact attached to the epic · **M** · needs 007

**Delivery, decided:** Stage 4 produces the mod file, it is **attached to the epic**, and a human
processes it through **batch maintenance** into PeopleSoft. An API push comes later.

**It belongs at Stage 4, not Stage 5**, and the reason is not filing convenience. The file's content
is **data** — mnemonics, rates, effective date — fully determined by §16's tabular entries and §INT-3
at the end of Stage 3. No repo read is required, so `jira_author` can produce it, and producing it at
Stage 4 means it is attached **during the G3 push**, keeping **one Jira mutation**. Drafting it at
Stage 5 would require a second write to Jira to attach it.

- **New artifact:** `core/templates/payment_brand/rate_mod_template.payment_brand.yaml`, beside
  `jira_template.payment_brand.yaml` — the batch-maint layout. Its columns come from Part A's first
  side-question; until they are known the template is `[TBD]` and this part does not start.
- **Filled by** `core/scripts/jira_plan.py` from §16 entries whose `location` is tabular
  (`peoplesoft.rate_tables[mnemonic=…]`) plus §INT-3's current/target rates. Written to the run
  workspace, then attached by `core/scripts/jira_push.py` at G3.
- **No push automation.** The place a future API call would go is a **named function in
  `jira_push.py`** that is wired in place when the endpoint exists — not a plugin seam, and not a
  branch. Until then it does not exist and the attachment is the delivery.
- **The rate story is `non_code`.** Already legal per 003.1a: `non_code` means *"work with no code
  location"*, and `evidence` points at the §16 entry. **No `rate_mod` flag** — the story already
  points at a §16 entry whose location says `peoplesoft.rate_tables[…]`, so a flag would restate what
  following the pointer already tells you (schema rule 8).

---

### Part F — `code_author` drafts a prospective-location gap · **S** · needs 009

`VDI_TASK_V2.md` leaves one thing open at Stage 5: *"what does `code_author` do with a
prospective-location gap — draft, refuse, or record?"*, with 009's fixture **S3** forcing the choice.

**The answer is draft**, and the new mnemonic is the case that has no other answer: the mapping entry
does not exist, the prospective location is the site where it must go, and refusing means the most
greenfield work reaches Stage 5 and stops. So this is `code_author` gaining gap-drafting — **not a
new skill and not a new file**.

Two constraints on the draft, both from cite-or-flag:

- **The draft is grounded to the prospective location and to the analogy that produced it.** *"Modelled
  on the adjacent entry at `program_map.c:404`"* — never a free-hand construction.
- **The draft never invents the mnemonic string.** For a genuinely new program, the mnemonic's *name*
  is a naming decision, not a fact in the article or the code. The draft **proposes** one from the
  convention visible at the mapping site and marks it for operator confirmation; it must not present
  an invented identifier as sourced. *(See the open questions — who assigns it may already be
  settled by practice.)*
- `code_validator.py` (009) must accept a hunk whose §16 entry carries a **prospective** location,
  and must still reject one carrying **no** location.

---

### Part G — validation by replay, with the score written first · **L**

**Do not validate against fixtures you wrote.** Validate against **what actually shipped**: the
golden set from Part A has the article on one side and the shipped Stratus commit plus rate change on
the other.

**Define the score before the run, not after.** Same principle as the committed prior in 003.9b and
as 005 Part A's code-blind classification — a metric chosen after seeing the output rationalises it.

| Measure | Definition |
|---|---|
| **§16 recall** | fraction of files in the shipped diff that §16 located |
| **§16 precision** | fraction of §16 locations that appear in the shipped diff |
| **Release shape** | the §INT-4 verdict matched what actually happened (shipped together or apart) |
| **Effective date** | captured and carried to every story, matching the article |
| **New-mnemonic runs** | the drafted mapping entry and rate row match what shipped, modulo the mnemonic string |

> **A run that scores well on synthetic fixtures and badly here means the fixtures were wrong, not
> the code.** That is the finding this part exists to produce, and it is worth more than a green
> sweep.

**Replay order** — cheapest and most isolating first:

1. **Existing mnemonic, qualification only** — Stratus only. No PeopleSoft, no crossing, no create
   path. Proves the spine on real data.
2. **Rate-only** — PeopleSoft only. A tabular story, the mod file generated, and **no code diff to
   compare** — which is precisely why it is a separate case: it is the run shape that would silently
   produce nothing before 003.1a.
3. **New mnemonic** — all three systems, the quadrant, the create path, the effective date, and the
   Part F draft. The only case that exercises everything.
4. **Visa.** Resolve already reads `networks.yaml`, so MC → Visa **should** be a vocabulary addition
   (IRD vs FPI), not a second flow. **Treat any Visa-specific pass you are forced to add as a design
   finding** — it means something declared generic was in fact MC-specific.

---

### Build order

1. **Part A** — desk-mine. Days, no code. Produces the matrix, the `other` list, the golden set, and
   the mod-file layout.
2. **Parts B + C** — the quadrant and the create path, on top of 003.2's files. Synthetic fixtures for
   load-time rejections; the real proof is step 5.
3. **Part D** — the effective date. Small, and independent of the rest.
4. **Replay golden #1** (existing / qualification) — Stratus only.
5. **Replay golden #2** (rate-only) — needs **Part E**, so 007 must be done.
6. **Replay golden #3** (new mnemonic) — needs **Part F**, so 009 must be done. Then Visa.

### Confirm before building

> **The half-hour check with the highest information in the whole task.** Does `start-enrich` today
> run the enrichment arms **before** `interchange_enrich`? `VDI_TASK_V2.md` 003.2 asks for this and
> nobody has answered it.
>
> If it does, the arms have been searching Stratus in the **network's vocabulary** (designators)
> against code that keys on **mnemonics** — finding almost nothing, silently, and filing thin. Then
> resolve-first is a **bug fix, not a reorganisation**, and it changes how much you trust every run
> to date. Record the finding either way.
>
> The plan side is already decided and is stronger than "first": **resolve is a barrier** (003.5,
> decided 2026-08-20) — every resolve pass completes before any impact pass starts. What is not
> confirmed is whether the running code obeys it.

**Resolve-first is not a filter.** Three protections must survive this task, because resolve-first is
exactly the thing someone later optimises into a lookup: every pass still `reads: [v1.assertions]`;
`search.scope: full_repo` stays unbounded, so resolved keys are an **exhaustive obligation, not a
boundary**; and `needs:` sequences without ever scoping. A pure rate change where Stratus contributes
no keys is still fully scanned, and a designator that failed to resolve is searched **by name** and
reported as *"v1 names D, no mnemonic resolved, searched by name, found nothing"* rather than
vanishing with the resolve failure.

*(The barrier binds **Arm 1**. Arm 2 verifies v1's descriptive claims about how the system works
today and does not depend on the key set the same way; it may run in parallel with resolve.)*

### Open questions this task forces

1. **Does clearing have a designator → mnemonic gap like interchange?** Already open in 003.2, and
   Part A's corpus is where the answer is. If yes, `resolve` is a **general pattern** and every type
   needs a dictionary declared; if no, interchange is the odd one out and `resolve: []` is normal —
   which decides whether `authorization` is representative or a stub.
2. **Does PeopleSoft's MPT layout live in a file at all?** If it is an Application Designer record
   definition or PeopleTools metadata rather than source, `layout_at: <path>` cannot address it and
   the field needs a second addressing form. Answer before building the layout parser. Does not block
   this task — PeopleSoft's side stays `[TBD]` as a recorded boundary.
3. **What are the batch-maint columns?** Part A's first side-question. Blocks Part E only.
4. **Who assigns the mnemonic string for a new program?** If there is a convention or an owning team,
   Part F's draft cites it instead of proposing. Answerable from the corpus.

### Amendments to existing decisions

| Where | Amendment |
|---|---|
| **003.2**, resolve pass | `on_unresolved:` becomes a map keyed by assertion type; `on_resolved:` added. Scalar `escalate` no longer legal |
| **003.2**, schema rule 4 | *"every `activates:` names a pass that exists"* widens to scan resolve outcomes in `flow.yaml`, not only `probes.yaml` |
| **003.2**, schema | new rejection: an `on_unresolved` / `on_resolved` map that does not declare exactly `modify_existing` and `new_capability`. `unclear` is not a legal key |
| **003.5**, deferred `sequence:` | **stays deferred.** The effective date (Part D) discharges the risk more cheaply; the seam is unchanged. Recorded here so the deferral is not re-litigated |
| **003.5**, activation | activation has two sources — probes and resolve outcomes. Both are unioned; both are recorded with their cause |
| **005 Part D** | applied, not reopened. The resolve quadrant is Part D specialised to the resolve phase |
| **TASK-V2-009**, fixture S3 | **answered: draft.** See Part F |
| **TASK-V2-007** | unchanged, but Part E depends on it — the mod file attaches to the epic, which 007 defines |

### Depends on

- **Part A** — nothing on disk. `core/scripts/ingest_jira.py` and `core/adapters/jpmc_adapters/jira.py`
  for pulling the corpus; `fixtures/jira/PBI-4471.json` as the shape reference
- **Parts B, C** — 003.2 complete: `core/estate/applications.yaml`, `core/estate/interfaces.yaml`,
  `core/profiles/payment_brand/change_types/interchange/{flow.yaml,probes.yaml}`,
  `fixtures/estate/verify_estate.py` — **and 003.5's `core/scripts/flow_plan.py`**, which is where the
  new rejections are enforced. Plus TASK-V2-005 Part A
  (`assertion_type` on every §8 assertion) and Part G (§16 `kind: gap`, prospective locations)
- **Part D** — 003.2's `release_shape` block; `core/templates/payment_brand/jira_template.payment_brand.yaml`
- **Part E** — TASK-V2-007 (the epic/story hierarchy), which needs **007a**; `core/scripts/jira_plan.py`,
  `core/scripts/jira_push.py`, `core/skills/jira_author.skill.md`
- **Part F** — TASK-V2-009 (`code_validator.py` and its fixtures); `core/skills/code_author.skill.md`
- **Part G** — Parts A–F for the case it replays, and `fixtures/enrichment/verify_interchange_enrich.py`
  still green

### Reads

- `VDI_TASK_V2.md` **Target state §3** (the flow, and the properties worth protecting) and **§6** (run
  order) — the contract this task amends
- `VDI_TASK_V2.md` **003.2** — the eight schema rules and the floor forms, before adding to them
- `VDI_TASK_V2.md` **003.1a** — the §16 / §INT-n split and the tabular-location ruling; **do not
  reopen it**, Parts C and E apply it
- `VDI_TASK_V2.md` **005 Part A, D, E and G** — assertion classification, the four quadrants, scope
  findings, and gaps as §16 entries
- `VDI_TASK_V2.md` **009 Part A** — `code_validator.py`'s checks, and fixture S3
- `vdi_tree.md` — ground truth for every path above
- `core/profiles/payment_brand/interchange_enrich.skill.md` and `interchange_networks.yaml` — which
  003.2 moves to `resolve_mnemonic.skill.md` and `networks.yaml`

### Creates / edits

| Path | Action |
|---|---|
| `docs/design/interchange-change-matrix.md` | create — Part A: the matrix, the `other` list, the two side-question answers |
| `docs/design/interchange_jira_matrix.csv` | create — Part A: one row per Jira, columns aligned to 003.9's KB |
| `docs/design/golden-set.md` | create — the chosen replay cases, each with article + diff + rate change located |
| `core/profiles/payment_brand/change_types/interchange/flow.yaml` | edit — `on_unresolved` map, `on_resolved`, the §INT-4 effective date |
| `core/skills/resolve_mnemonic.skill.md` | edit — report the quadrant per designator, and the prospective mapping site |
| `core/scripts/flow_plan.py` | edit *(created by 003.5)* — derived activation from resolve outcomes; the two new rejections |
| `core/templates/payment_brand/rate_mod_template.payment_brand.yaml` | create — the batch-maint layout |
| `core/templates/payment_brand/jira_template.payment_brand.yaml` | edit — effective date → story deadline; the mod file as an epic attachment |
| `core/scripts/jira_plan.py` | edit — fill the mod file from §16 tabular entries + §INT-3 |
| `core/scripts/jira_push.py` | edit — attach the mod file at G3; named placeholder for a future API push |
| `core/skills/jira_author.skill.md` | edit — carry the effective date to every story |
| `core/skills/code_author.skill.md` | edit — draft a prospective-location gap; never invent the mnemonic string |
| `core/scripts/code_validator.py` | edit *(created by 009)* — accept a prospective location, still reject a missing one |
| `fixtures/estate/verify_estate.py` | edit *(created by 003.2)* — the two new rejections |
| `fixtures/new_mnemonic/` | create — cases + `verify_new_mnemonic.py` (all four quadrants) |
| `fixtures/replay/` | create — the golden-set runs and the scoring script |

### Acceptance

1. **Every closed MC/Visa interchange Jira is placed in a cell or on the `other` list.** A partial
   matrix fails — completeness is what makes the `other` list mean anything.
2. The golden set is chosen, and each member has its article, its shipped diff and (where applicable)
   its rate change located and recorded.
3. Both side-questions have an answer or an explicit *"not recorded in the history"* against them.
4. **All four quadrant cells behave as specified**, including `resolved + new_capability` filing a
   scope finding rather than proceeding.
5. `unclear` reaches Stage 3 as `modify_existing` and therefore escalates; **no configuration can
   make it default to `new_capability`.**
6. A new mnemonic produces §16 gap entries for the mapping site, the qualification criteria and the
   rate row — **and none is dropped for lack of a found location.**
7. `qualification_impact` activated by the quadrant is **recorded with its cause**, is distinguishable
   in the run output from probe activation, and enters the G2 denominator.
8. Non-activation of the create path is recorded: *"every designator resolved."*
9. `flow_plan.py` **refuses the plan** — not warns — when an `activates:` inside a resolve outcome
   names a pass that does not exist, or when a quadrant map is incomplete.
10. §INT-4 carries the effective date with its citation, or `[TBD — unsourced]`; every story in the
    epic carries it as a deadline.
11. The rate mod file is generated at **Stage 4** from §16 + §INT-3 with **no repo read**, and is
    attached to the epic in the **same** Jira mutation as the push.
12. A rate-only change produces a `non_code` story tracing to its §16 entry, and **no `rate_mod`
    flag exists anywhere** (schema rule 8).
13. `code_author` **drafts** a prospective-location gap, grounded to the analogy site, with the
    mnemonic string marked for operator confirmation rather than asserted.
14. **Every replay case has its score recorded before the run**, and the scores are reported
    per case.
15. Golden #1 and #2 replay end to end; #3 replays end to end once Parts E and F are in.
16. Resolve-first is confirmed in the running code, and the finding recorded either way.
17. `verify_interchange_enrich.py` still green; full fixture sweep green; `build_checks.py` green.

### Proof

`fixtures/new_mnemonic/verify_new_mnemonic.py`, one case per cell plus the mechanics:

- `unresolved_new_files_gap` — an unresolved designator whose assertion is `new_capability` files a
  §16 gap at the prospective mapping site and activates the create path. **The core case of Part B**
- `unresolved_existing_escalates` — today's behaviour survives unchanged
- `resolved_new_scope_finding` — the MCPA-LT case: escalates naming all four candidate causes, and
  **no second mapping entry is drafted**. *The most important negative case in this task — without
  it, duplicate work is drafted silently*
- `unclear_treated_as_existing` — an `unclear` assertion surviving to G1 escalates
- `derived_activation_recorded` — `qualification_impact` run by the quadrant is attributed to it, not
  to INT-P1, and counts in the G2 denominator
- `create_path_not_activated_recorded` — all designators resolved, and the non-activation is stated
- `activates_unknown_pass_rejected` — a resolve outcome naming a non-existent pass makes
  `flow_plan.py` refuse the plan (extends `verify_estate.py`'s rule-4 case)
- `quadrant_map_incomplete_rejected` — a map missing `new_capability` is refused at load time
- `rate_only_produces_mod_file` — a pure rate change with no code diff still produces a `non_code`
  story, a tabular §16 location and a filled mod file
- `gap_drafted_not_refused` — 009's fixture **S3**, now with a stated expected outcome
- `mnemonic_string_not_invented` — the draft marks the proposed mnemonic for confirmation and does
  not present it as sourced

`fixtures/replay/` — one directory per golden case, each holding the article, the shipped diff, the
scoring thresholds **committed before the run**, and the achieved scores. A replay that scores below
its committed threshold is a **finding to investigate, not a test to relax**.

> A green sweep that rejects nothing is not proof. Every rejection case above must be shown failing
> for the stated reason.
