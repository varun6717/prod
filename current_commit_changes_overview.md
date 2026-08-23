# current_commit_changes_overview.md

**Commit of 2026-08-23 — the VDI design review: Stages 4 and 5 closed, five new tasks, two
stakeholder artifacts.**

> **Filenames carry a version** — `neuro_architecture_v1.html`, `neuro_overview_v2.html`. The number
> tracks **that file's own revisions**, not a set generation: the architecture page has not changed
> since v1, so calling it v2 would be a lie. Bump the suffix on the next substantive revision rather
> than editing in place; the superseded file leaves the tree, and git history holds it.

This commit carries **no application code**. It is review output: the task catalogue the VDI Copilot
executes from, and two published documents that explain the system at two altitudes. Nothing in
`core/`, `overlays/`, `fixtures/` or `runs/` is touched, so nothing needs re-publishing to the
registry.

---

## Files in this commit

| File | State | What it is |
|---|---|---|
| `VDI_TASK_V2.md` | edited | The deliverable. 11 task specs, 8 PARKED findings, 23 review-log rows |
| `neuro_architecture_v1.html` | new | Engineering reference — 12 sections, what runs and what each step may decide |
| `neuro_overview_v2.html` | new | Exec overview — the knowledge base, the flow, the gates, one worked example. **v2** supersedes v1 |

### Why the overview is at v2

The two arrows that **feed** ingest now leave the cylinder on the left, run over the top, and drop
into the Ingest box — a separate **intake** channel, visually distinct from the query channel every
other stage uses. The distinction is real and the diagram was blurring it: **ingest is the only stage
that builds layers; everything else reads them.** It also removes the long diagonal that crossed most
of the other arrows.

The history layer is relabelled **Change history KB** (`PAST ARTICLES · THEIR STORIES · THE ACTUAL
DIFFS`), which reads as a knowledge base rather than a pipeline fragment.

Worth keeping straight, because it is the first question the diagram invites: **the estate layer is
declared, not ingested.** Nothing in source links two sides of a file interface — `mpt_loader.c`
contains no reference to PeopleSoft and never will — so no tool can extract it and a person who knows
the estate writes it down. That is why the intake channel carries only the articles and the source,
and it is the property that makes the whole crossing mechanism necessary.
| `CLAUDE.md` | edited | Three hard rules added, each earned by a mistake made during the review |

---

## What changed in `VDI_TASK_V2.md`

**Stages 4 and 5 were reviewed for the first time.** The prior hand-off recorded both as *"not
started"*, which was accurate until now. Four tasks came out of it:

- **007a — amend D-A15.** *Front of the queue.* Two table rows and one retired consequence in
  ADR-008, plus FR-JR-01 which restates the same mapping independently. Docs only, no code, and it
  unblocks the three below.
- **007 — the Jira hierarchy.** Initiative and Deliverable are **quarterly containers, referenced
  not created**; one article is one epic with its requirements in the description. The template
  currently authors two issues that already exist.
- **008 — `validation.md`.** The post-install validation document, epic-level. Positive cases ground
  in §16; **negative cases come from the code**, so it is produced at Stage 5 — `jira_author` cannot
  read the repo.
- **009 — Stage 5 validator and fixtures.** Of the two writes that leave the building, only the Jira
  push is guarded. **31 fixtures exist; zero are Stage 5.** Delivers `code_validator.py`, both
  fixture directories, and the multi-repo push design.
- **010 — symbol-level code map.** §16 line ranges are model-produced while tree-sitter already
  computes and discards them. Governing rule: **symbols locate, they never bound what is read** —
  the scan still pulls the whole file.

**Nine decisions landed during the Stage 3 re-review**, each in the revision log with its reasoning:

- `compare` → **`release_shape`**. The name described `cross`'s job; the phase returns a release
  verdict. Renamed while it is still a find-and-replace.
- **§16 gains `kind: verify`** — the reasoned non-change, carrying a `confirm:` condition the way a
  gap carries `basis:`. Makes the run's own assumptions trackable as Jira stories.
- **`flow_plan.py`** — the run order and every load-time rejection are **computed, not reasoned**. A
  wrong sort is invisible: it files fewer findings and every G2 check still passes.
- **Phase totality** — a third G2 denominator. `resolve`/`cross`/`release_shape` were in neither
  existing precondition, so a phase could run, produce nothing, and pass the gate in silence.
- **The interchange floor** settled at `stratus.code` + `resolve` + `interface: mpt`. The MPT entry
  was dropped and then restored: it is the sole invoker of the direct-layout assessment, without
  which the backward-crossing case is structurally uncatchable.
- **`INT-P3` deleted** — it activated a pass that never existed. MCCs need no resolution.
- **Settlement declared** `in_estate: false` — it was a party to `submission` with no application
  entry, an undefined third state.
- **Eight schema rejections** consolidated into one numbered list, including *no derivable
  duplication* and *every interface party resolves to an application*.
- **Type sections gain `title` + `must_capture`**, declared on the pass.

**Three PARKED entries restored.** The review log claimed topics 7 and 9 were parked; neither was
written down, nor was *Stage 5 has no fixtures*. A fresh session read "closed" and moved on. PARKED
went 5 → 8.

**Four open questions closed** — three answered from the repo, one by V:
`refuted` **does** fire (2 of 33 findings, so 004 is not theoretical) · `check_discovery_adequacy.py`
measures the SI profile, **not** the corpus (so 002 does not shrink) · `pdf_extract` is
domain-agnostic **by its own admission** · the scheduler is **Control-M**, a machine-readable second
source of interface truth needing no history.

---

## Why `CLAUDE.md` changed

Three rules, each written because the review broke it:

- **Cite-or-flag cuts both ways.** Two page claims were flagged "unsourced" after grepping only
  `VDI_TASK_V2.md` and `vdi_design.md`. Both were documented in
  `si_profile.payment_brand.yaml` itself. *A false "unsourced" flag is as damaging as an invention.*
- **Never restate a derivable fact.** `activated_by:` on a pass, `acquired:` on an interface party,
  `profile: "[TBD]"` on an unacquired substance — three instances in two days.
- **Change a contract, then sweep its derived views.** The floor changed twice and the diagrams kept
  rendering keys that no longer existed.

---

## Port note

Nothing here ships to the VDI as code. `VDI_TASK_V2.md` is what the VDI Copilot reads; the two HTML
files are published artifacts and are read in a browser, not executed. **Start at 007a** — it is
hours of docs work and unblocks three tasks.
