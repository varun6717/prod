# BOOTSTRAP.md — session kickoff

Paste the block below into a fresh session. It orients from zero, then names the two pieces of
work in order. Everything it asserts is checkable on disk — verify rather than trust it.

---

## What we are building

**PDLC_App_v2** — an agentic **Solution Intent → enrichment → Jira** pipeline for JPMC Merchant
Services, governed by **ADR-008** (accepted 2026-07-31; BRD/FRD are retired).

Five layers: **Data & context → Solution Intent v1 → enrichment (v2) → Jira 4-level plan →
Metrics.** The idea worth holding on to is the middle: **v1 says what we intend, authored
code-blind from sources and the operator. Enrichment checks that against the code. v2 is the
reconciliation.** v1 is authored code-blind *on purpose* — a v1 that already knew the code would
leave enrichment nothing to find, and no way to tell a source's claim from a tool's inference. G1
acceptance freezes v1, so everything after is a traceable delta rather than an edit.

This repo is the **external Claude Code build**: everything generic is built and proven here, then
ported to the JPMC VDI, where only environment-specific calls are wired.

## Where it stands

**The external build is complete.** Milestones D0–D6 landed and every build task is ticked; the
only open item is TASK-128 below, which reviews documentation rather than building anything. The
spine is proven end to end (`docs/ACCEPTANCE_SI.md`): a real run from the React UI
through G0 → ingest → v1 → G1 → enrichment → G2 → 4-level plan → G3 → a stub push of 35 issues,
with every gate an operator act and every metric derived from the run's own ledger.

Also landed: eight design calls ruled and executed (`docs/OPEN_RULINGS.md`), and thirteen
code-review findings fixed (`code_review.md`). The registry is published — `code_640011` @ `main`,
126 files, §10 green as a hard gate before the push. **Two repos, and they are not the same one:**
the **registry** (what a run hydrates from) is `https://github.com/varun6717/code_640011.git`, which
holds the published subset and nothing else; the **build repo** (this one) is
`https://github.com/varun6717/prod.git`.

**Green means:** 30 fixture verifies + `python3 core/scripts/build_checks.py` (4/4). Run both
before believing anything is fine.

## How to orient (10 minutes)

1. `CLAUDE.md` — the rules, the ladder, the context-restart protocol.
2. `docs/PROGRAM_OVERVIEW.md` — the process as a diagram: six boxes, the main files in each, what
   every file *is*. Fastest route to "where does X happen".
3. `TASK_LIST.md` — skim the done ledger, then the open index.
4. **Then check disk.** `core/`, `app/`, `fixtures/`. Disk is ground truth over any document,
   including the ones above.

## The two pieces of work, in order

### 1 — TASK-128: review the overview docs against disk

`docs/PROGRAM_OVERVIEW.md` and `docs/BUILD_OVERVIEW.md` were written **before** the eight rulings
and thirteen review fixes landed, and several of those moved things the docs describe —
`descriptor` moved from the extract steps to `doc_index`, `push_epics` flipped its default, the
index's structure became derived rather than authored, `reject` now auto-supersedes its dependents,
`G3Authorization` became plan-bound. So the docs may be stale exactly where a VDI reader will lean
on them hardest.

For every claim either doc makes about *what a file is* or *what a stage does*: open the file and
check. The full spec is in `TASK_LIST.md` under TASK-128. **If nothing needs changing, say so
explicitly** — a review reporting no findings is a result, not a non-answer.

### 2 — The VDI integration

`VDI_WIRING.md` — **16 open items**. Read the disjointness rule at its head first: that file holds
what gets *wired*, `TASK_LIST.md` holds what gets *built*, and no task appears in both. A VDI item
never contains a spec; it names one placeholder function whose surrounding code is already built,
proven offline, and green.

Five placeholders, each one function in one file:

| Placeholder | File |
|---|---|
| `_download_pdf` | `core/scripts/ingest_sharepoint.py` |
| `_fetch_confluence` | `core/scripts/ingest_confluence.py` |
| `_fetch_issue` | `core/scripts/ingest_jira.py` — returns the parsed payload; rendering is already deterministic |
| `_create_issue` + `_update_issue` | `core/adapters/jpmc_adapters/jira.py` |

Plus: bind `auth.py` to the JPMC secret store (one `set_backend()` call — no connector changes),
set the four user-scope env vars, confirm the toolchain (`httpx`, `PyYAML`, `tree-sitter==0.25.2` +
`tree-sitter-c==0.24.2`; `python3 core/scripts/pdf_text.py --which` → `builtin` is acceptable,
`pypdf` preferred), then **re-run each connector's verify script against the live endpoint** and
confirm the descriptor shape is byte-identical to the mock run. Descriptor parity is the contract
everything downstream depends on.

**One acceptance condition is owed by that run:** *"an operator completes the fresh run unaided
through UI + tool."* Every gate in the external run was an operator act, but performed in
conversation rather than through a UI affordance — an agent cannot attest a usability claim about a
human. Record in the VDI run log which gates the operator reached without asking for help. That is
the condition; the run completing is not.

## Rules that are not negotiable

- **Ladder discipline.** Requirements = WHAT/WHY, tech spec = HOW, task list = the sequence. A task
  that would change a pinned contract or reopen D1–D11: **stop and flag it**.
- **Gates are human.** A validator computes a score and hard preconditions; the **operator**
  decides. Never self-accept a gate, and never treat a passing score as permission.
- **Cite-or-flag.** Every substantive claim grounds to a source, the frame, or an operator answer —
  or is marked `[TBD — unsourced]`. Never invent.
- **The Jira push is the only external mutation**, and it is structurally gated: `push_plan`
  requires a plan-bound `G3Authorization` that only `authorize()` can mint.
- **Re-publish after any published-tree change** (`core/`, `overlays/`, `docs/`) —
  `python3 core/scripts/publish_registry.py https://github.com/varun6717/code_640011.git --branch
  main`. §10 red blocks the push. A successful publish **also refreshes `registry_repo/`**, so
  pushed and staged cannot diverge; you only need `--stage registry_repo --force` by hand when you
  want the snapshot current *before* publishing (e.g. committing first). `verify_registry` fails
  if that snapshot drifts from source.
- **Fix generic code here, not there.** If the VDI surfaces a gap in the generic code rather than
  the wiring, change it in this repo and re-publish.

## One thing worth knowing about how this went

Nine integration breaks surfaced during the end-to-end acceptance run, and the worst code-review
finding was sitting in the *accepted* artifacts. **Every one was invisible to a fixture testing the
same component in isolation** — `clone.py` failed into every fresh scaffold because its fixture
cloned into a path that did not exist, the one arrangement a real run never has.

So: when the VDI run finds something, that is the run working, not failing. Expect it, and write
the regression test that would have caught it — a fix without one is not fixed.
