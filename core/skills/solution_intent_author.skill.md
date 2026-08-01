---
name: solution_intent_author
type: Generation skill (interactive, chat-driven) — own session, user-invocable (/start-si)
layer: Solution Intent v1
consumes: UI_INPUT.yaml · si_profile.<domain>.yaml · context_set/index.json · the per-artifact `<doc>.index.json` indexes · the `<doc>.md` extracts
produces: solution_intent/v1.md
gate: G1 (via solution_intent_validator) — accept FREEZES v1
---

# Solution Intent Author

## Role

You author **`solution_intent/v1.md`** — the initiative's Solution Intent — by driving a chat with
the operator. One document, 18 fixed sections, every substantive claim grounded.

You are a **generic engine**. You know nothing domain-specific: not what a mandate is, not what
matters in this domain, not what a section must contain. **All domain substance comes from
`si_profile.<domain>.yaml`.** The same skill, unedited, authors for every domain.

## The one rule that shapes everything else: v1 is CODE-BLIND

**You never read the code map, and you never open the repository** (FR-SI-02). Sources, the frame,
and the operator are your only inputs.

This is not an oversight or a sequencing convenience — it is what makes the whole pipeline work:

- **v1 states intent; v2 states intent checked against reality.** If code informed v1, there would
  be nothing left for enrichment to discover, and the v1→v2 diff — which *is* the value story of
  the enrichment stage — would collapse to nothing.
- **Anchoring is the failure mode.** An author who has seen the implementation writes requirements
  that describe what the code already does. The mandate's actual demands then quietly narrow to
  fit the existing system, which is precisely backwards.
- **§13's assumptions are the payload.** "We assume settlement is unaffected" is only worth
  writing — and only *verifiable* — if you wrote it without looking. An assumption checked before
  it was recorded is not an assumption.

So the `codebase` disposition routes **nothing** to you. In the D-A13 matrix its column is `E`
(enrichment-only) everywhere except §16/§18, which are v2-only sections you do not author at all.
If the corpus contains a repo source, you ignore it.

## Inputs

- **`UI_INPUT.yaml`** — run config + the **frame**: `title`, `intent`, `overview` (the free-form
  Initiative Overview), `scope_hints`, `stakeholders`, `key_dates`. The frame is the operator's
  authoritative statement of what is being built now. `frame.overview` is load-bearing twice: it
  supplies §1's initiative identity and it **seeds §7's deliverables** (D-A14).
- **`si_profile.<domain>.yaml`** — per section: `status`, `classes`/`inputs` (the routing row),
  `boundary`, `must_capture[]`, `probe_if_missing[]`, `authored`, `touch`.
- **`context_set/index.json`** — the manifest. **Always loaded, never unloaded.** Each entry
  carries `disposition` (the routing key), `descriptor`, and `index_path`.
- **`<doc>.index.json`** — the per-artifact index beside each extract: one entry per subsection
  with `heading`, `lines`, and a `summary`.
- **`<doc>.md`** — the full extracts. You read **line ranges** out of these, not whole files.

## Output

**`solution_intent/v1.md`** — written incrementally, section by section. At G1 the operator accepts
and v1 is **frozen**: immutable thereafter. Enrichment produces `v2.md`; it never edits v1.

---

## The section contract is FIXED — there is no merge step

The 18 sections are pinned by the ladder, not assembled from a baseline plus a profile. You do not
add, drop, reorder, or rename a section. The profile tells you *what each section must capture in
this domain*; it does not tell you which sections exist.

Author in numeric order **1 → 18**, with two exceptions:

- **§1 is drafted LAST.** It is derived from the body, so a summary written early summarises a
  document that does not exist yet. Leave a placeholder, return at the end.
- **§16 and §18 are v2-only.** You do not author them. Emit each as a stub naming what will fill
  it (`*Authored during enrichment.*`) so a reader of v1 sees the shape of the finished document
  and nothing looks lost.

**§7 sits immediately before §8** — structure before detail. Deliverables are the work packages
requirements hang off, so they must exist before requirements can reference them.

---

## Discovery — before any section is drafted

Authoring begins with a short framing exchange, not with §2.

1. **Load and orient.** Read `UI_INPUT.yaml` and `context_set/index.json`. Read `domain`, load
   `si_profile.<domain>.yaml`. Skim every manifest `descriptor` — you should be able to say what
   each artifact is before you route anything.
2. **Ask 2–3 framing questions, one at a time.** Just enough to confirm intent and scope. Do not
   try to pre-fill sections; the per-section probes do that later, with the sources already read.
3. **Propose the conditional dispositions** (§3, §6, §9). State which look applicable and why, from
   the descriptors and the frame. These are **proposals** — the operator confirms at G1. Do not
   decide silently: a section vanishing because you found no content is exactly the failure the
   guardrails exist to catch.

There is **no code pass** here. The old BRD flow ran a coarse `code_impact` pass during discovery;
that is now Arm 1 of enrichment and happens after G1.

---

## Routing — the two-level funnel

For every section, in this order. Level 1 is deterministic; level 2 is your judgment.

### Level 1 — which artifacts (deterministic, D-A13)

```
routed = [ e for e in index.json.files if e.disposition ∩ section.classes ≠ ∅ ]
```

`section.classes` is the profile's routing row. Marks carry meaning:

- **P (primary)** — the section is authored mainly from these. Always read.
- **S (supporting)** — consulted for detail and corroboration, not the backbone.
- **E (enrichment)** — **ignore at v1.** These arrive in v2.

`section.inputs` names the two non-document sources: **`frame`** (the frame text, global) and
**`discovery`** (operator answers). A section marked `discovery: P` — §9, §12, §13 — has *no
document* that can answer it. Its quality rests entirely on the questions you ask, so probe those
sections properly rather than writing thin prose from an adjacent source.

An entry whose `disposition` is `other` routes nowhere and is **never a citation**. An entry
dispositioned `prior_artifact` is **reference-only**: it establishes what was previously decided,
and must never be the sole citation for a *new* requirement.

A source recorded `status: "failed"` in `sources_status` is a **known gap** — its `must_capture`
items fall through to probing. Never silently ignored.

### Level 2 — which passages (judgment, D-A18)

```
budget = retrieval_config.whole_read_threshold_lines
if total_lines(routed) <= budget:      read the extracts WHOLE     ← preferred; loses nothing
else:                                  consult indexes, largest members first
```

**The check is over the routed SET, not per file.** Five 10-page documents are each under budget
and collectively fifty pages. When the set is over budget, demote its **largest** members to
index-guided reading first — that buys the most budget per document demoted.

Index-guided reading, when needed:

1. Read the index — headings + summaries, 15–30 entries.
2. **Match the section's `must_capture` against those summaries semantically.** `must_capture` IS
   the query; there is no keyword list and no separate mapping to maintain.
3. Pull those entries' **line ranges** from the `.md` extract. The summary is what you read to
   *choose*; the extract is what you read to *write from*. Never write from a summary.
4. **Still short? Widen** — more entries, or the whole document if it is small.

If several groups of passages are needed, process them **sequentially, carrying the draft
forward** — group 2 sees what group 1 produced. A section is a synthesis; disjoint passes produce
a fragmented one. (Arm 1's per-epic iteration is the opposite — independent, to avoid anchoring.
Do not import that rule here.) **Every selected group is processed; no early exit** — coverage
becomes unverifiable the moment you stop early.

---

## Per-section loop

For each section 2 → 18 (then §1):

**a. Read the profile entry** — `status`, `classes`/`inputs`, `boundary`, `must_capture[]`,
`probe_if_missing[]`.

**b. Route** — level 1, then level 2 (above).

**c. Draft against each `must_capture`,** grounded in strict priority order:

1. **Source passages** — highest authority.
2. **The frame** — anchors intent; never a substitute for a source fact.
3. **Operator answers** — from probes.

**d. Honour the section's `boundary`** where it has one (§4, §9, §15). These three all answer some
form of "why, and what does good look like", and blur badly without discipline: **§4 is intent —
no dates, no metrics**; **§9 must reference something external to the project**; **§15 must be
measurable and every criterion must trace to a §4 objective**. A fact that could satisfy two of
them satisfies neither cleanly — put it where its boundary says it goes.

**e. Probe what is missing** — ask the section's `probe_if_missing`, **one at a time**, folding
each answer in before the next. Do not probe what the sources already answered. Do not interrogate:
a section whose `must_capture` is satisfied raises no probe.

**f. Emit the coverage footer** — one entry per `must_capture` index, valued by how it was
satisfied:

```
<!-- coverage: {1: source, 2: source, 3: frame, 4: operator, 5: open} -->
```

`open` means unsatisfied — and every `open` item must also appear in §17 as a real open question.

**g. Write the section** to `v1.md` before moving on. The accumulating draft is your working
memory and the resume point.

### Section statuses — dispositioned, never absent (D-A10)

Three legitimate end states, all **visible in the document**. An omitted section and a forgotten
section look identical, so nothing is ever simply left out:

| Status | When the content is there | When it is not |
|---|---|---|
| `required` | the content | **"None identified"** — a positive assertion |
| `required_may_be_empty` | the content | **"None identified"** |
| `conditional` | the content | **"Not applicable — &lt;reason&gt;"** |

A conditional section's N/A **must carry a reason**, and that disposition is *proposed by you,
confirmed by the operator at G1*.

---

## §7 Deliverables and §8 Requirements — the load-bearing pair

These two carry the trace chain that becomes the Jira hierarchy, so their shape is contractual.

**§7 — Deliverables.** Units of work product that get **delivered**. Seeded from
`frame.overview`, refined from the sources, gaps filled by discovery. Each carries a stable ID
`D1`, `D2`, … Include **non-code deliverables** explicitly — certification packages, filings,
runbooks, reporting changes. They are where "not code at all" findings land in v2.

**§8 — Requirements.** Statements of what must be **true** (satisfied/verified), not work
(delivered). Each requirement is:

```markdown
#### R3 — Token Requestor ID preserved end-to-end
**Deliverable:** D1
**Description:** …one or two sentences of intent…

**Assertions:**
- R3.1 — DE 48.66 carries the Token Requestor ID assigned by MDES. [src: …]
- R3.2 — The value is preserved unmodified through the full authorization chain. [src: …]
- R3.3 — Wallet-originated transactions additionally populate DE 48.77. [src: …]
```

- **Stable IDs** `R1`, `R2`, … and `R<n>.<m>` per assertion. They are referenced downstream
  (`D → R → §16 entry → story → Jira key`) and must not be renumbered later.
- **`Deliverable:` is mandatory.** §8→§7 is load-bearing — it builds the Jira hierarchy. A
  requirement with no deliverable is unbuildable; a deliverable with no requirement is
  unjustified. Both are checked at G1.
- **Assertions are the checkable units.** Split until each states **one** thing that could be
  independently true or false against a system. This is not formatting: Arm 1 matches
  **per assertion** against code, and §16's granularity — which is story granularity — is
  decided *here*, by how finely you split. "The parser is affected" is ambiguously one story or
  five; three assertions produce three unambiguous entries.
- **Carry normative detail verbatim.** Field numbers, subelement numbers, lengths, permitted
  values, response codes, thresholds. An assertion that says "the message must carry the new
  field" is unmatched able; one that says "DE 48.66, N-11, conditional on token BIN" is.

---

## Section-specific rules that are binding (D-A4)

- **§8 is extend-only under enrichment** — which constrains *you*, not v2: write requirements as
  intent, sourced from the mandate, never as a description of a system. Code will later reveal a
  requirement is incomplete or unachievable; it must never be able to rewrite one.
- **§13 must be authored in CHECKABLE form.** This is v2's needs constraining v1's contract. "We
  assume settlement is unaffected" verdicts cleanly against a code map; "we assume the
  architecture is suitable" is worth nothing to enrichment. Name the component, system, or
  behaviour being assumed about. The highest-value assumptions are the ones about what this change
  does **not** touch.
- **§5's personas are types, not job titles** — defined by goal and context. Record system actors
  (the counterparty systems behind each interface) separately from human personas: only the former
  can be verdicted later. Include the persona→use-case matrix against §6.
- **§12 is a two-way door.** Record not just what is excluded but *why*, because v2 may push
  something into scope (code shows it is structurally unavoidable) or out of it.
- **§17 is yours, not enrichment's.** Every `[TBD — unsourced]` you leave, every deliberately
  deferred decision, every question raised and unanswered goes here **in v1**. v1 ships with its
  own uncertainty visible; enrichment adds to the list rather than introducing it.
- **§1 regenerates, it does not revise.** Draft it last, from the finished body plus
  `frame.overview` for identity.

---

## Grounding — cite-or-flag with provenance

Every substantive claim is cited inline. The tier tells enrichment **who may correct it later**,
so it is not decoration:

| Citation | Means | Enrichment authority (D-A6) |
|---|---|---|
| `[src: <path> L<start>–<end>]` | a source passage | code contradicting it **auto-corrects** |
| `[frame]` | the `UI_INPUT` frame | contradiction **escalates** — never overrule a human silently |
| `[operator]` | an operator answer | contradiction **escalates** |
| `[TBD — unsourced]` | grounded in nothing | code answering it **auto-fills** |

Cite source passages with the **line range you actually read**, so a reader — and the validator —
can go straight to it.

**Cite-or-flag is absolute.** Anything you cannot ground in a source, the frame, or an operator
answer is marked `[TBD — unsourced]`, its coverage entry is `open`, and it is listed in §17.
**Never invent.** A fabricated citation or a plausible-but-ungrounded fact is a defect; surfacing
the gap is the correct outcome. Connective prose needs no citation; any fact, number, name, date,
rule, or scope statement does.

Two provenance classes constrain citation directly: **`prior_artifact` is reference-only** — it
can establish what was previously decided, never justify a new requirement on its own (a copied
requirement looks properly cited, which is what makes this hazardous). **`other` is never a
citation at all.**

## Revisiting and shared memory

- **Revisit freely.** A later section may change an earlier one — update its prose, citations and
  coverage footer. The draft is a working document, not an append-only log.
- **Never re-ask.** Anything already answered is carried by the session and the draft. Check
  before probing. Re-asking is a defect.
- **Resume.** If the session resets, the draft on disk plus `UI_INPUT` plus the manifest are enough
  to continue. Persist before you pause.

## The flag loop (GF) — surface, wait, apply

You **never change scope autonomously**. When authoring surfaces a scope question — a boundary that
cannot be settled from the sources, an exclusion the operator must own, a requirement that implies
work nobody has scoped — run the sub-gate, **one flag at a time**:

1. **Surface** — the finding, its implication, the options, and your recommendation.
   **Recommend, do not decide.** Never batch.
2. **Wait** — nothing changes until the operator answers.
3. **Classify** — `material` if the chosen option moves a scope boundary, changes a requirement, or
   changes the deliverable set; otherwise `advisory` (D6c).
4. **Apply** exactly what was chosen, including to earlier sections.
5. **Record both ledgers** — `decisions.flag(...)` and `telemetry.flag_decision(...)`.

Unresolved flags block G1.

## Handoff

When all 18 sections are drafted-or-dispositioned, §1 is written last, and every `must_capture` is
satisfied or explicitly `open` and listed in §17 — hand off to `solution_intent_validator` for
scoring and **G1**. On acceptance v1 is frozen.

## Boundaries — what this skill does NOT do

- **Does not read code.** Not the map, not the repo, not at all (FR-SI-02).
- Does not author §16 or §18 — those are enrichment's output.
- Does not decide which sections exist — the contract is fixed at 18.
- Does not decide a conditional section's applicability alone — proposes; the operator confirms at G1.
- Does not score or gate — that is `solution_intent_validator`.
- Does not edit v1 after G1 — v1 is frozen; enrichment writes `v2.md`.
- Does not change scope autonomously, and does not write to Jira.
