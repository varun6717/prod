# fixtures/mixed_repo — polyglot dispatch test bed (ADR-002)

A deliberately **multi-language** repo for exercising per-language partition dispatch
(ADR-002). It is **separate** from `fixtures/c_repo/` on purpose: `c_repo` carries the
human-signed-off `expected_code_map.json` oracle (TASK-005) and must stay pristine, so
polyglot behavior is proven here instead.

## Layout

```
src/routing/router.c      ┐
src/routing/router.h      ├─ C — the majority language (→ frozen tree-sitter-c extractor, TASK-009)
src/config/config.c       ┘
scripts/report.py            Python — residue (→ model fallback, marked coarse, TASK-010)
tools/Validate.java          Java   — residue (→ model fallback, marked coarse, TASK-010)
```

## What it proves (TASK-010)

- `detect_language(.)` → **`c`** (majority); top-level `code_map.language = "c"`.
- `partition_by_language(.)` → `{c: [3 files], python: [report.py], java: [Validate.java]}`.
- Dispatch routes the **C partition** through the deterministic extractor (full coverage)
  and the **Python + Java residue** through the model fallback (`coverage: coarse`).
- Residue files count as `files_fallback` in `coverage_report`, so `coverage` reflects the
  deterministic share — and a residue-heavy variant would trip the 0.80 floor →
  `REONBOARD_FLAG` (TASK-013) naming the un-onboarded language. No file is dropped.

This fixture intentionally has **no signed oracle** — it is a behavioral test bed for the
fallback path, not a regression oracle for the C extractor.

## Extended at TASK-116 — the required multi-language acceptance artifact (D-A19)

D-A19 marks polyglot behaviour a **required acceptance artifact**, not an enhancement, because
every failure mode here is silent: a module that quietly merged two languages, or closure that
quietly crossed a boundary, produces a map that looks entirely normal.

Each language now carries a **genuine dependency graph**, not one lonely file:

```
src/routing/router.{c,h}      ┐
src/config/config.{c,h}       ├─ C       — include graph, frozen extractor, ONBOARDED
src/settlement/post.{c,h}     ┘
scripts/report.py             ┐
scripts/report/formatter.py   ├─ Python  — import graph, model fallback, ONBOARDED (profile section)
scripts/report/ledger_read.py ┘
tools/Validate.java           ┐
tools/validation/*.java       ┘  Java    — import graph, NOT onboarded (no profile section)
```

**One repo, one profile, one gate, one freeze** (D-A22): `code_profiles/mixed_repo.profile.yaml`
carries per-language sections. Java deliberately has none — that is what makes it the
un-onboarded case.

### The four properties it proves

1. **Modules are language-scoped**, in the identity itself (`c:settlement`, `python:scripts`).
   Not cosmetic: two languages may both have a `settlement`, and merging them would put files
   with no possible edge between them into one module — tier 1 would then match a C assertion
   into Java files.
2. **Tier 1 runs an assertion against ALL module purposes** and matches languages independently.
   The transcript shows one settlement assertion matching `c:settlement` *and* `python:scripts`,
   neither aware of the other.
3. **Closure stops at the language boundary** — there is no cross-language edge to walk, and
   `external_calls`/`exposes` stay **reserved** (they are the deferred cross-repo seam, FR-DC-13).
4. **The un-onboarded language degrades to `unclustered`** — Java files are `coverage: coarse`,
   counted as `files_fallback`, always passed to tier 2, and still carry purposes. **Degraded,
   never dropped**: silently omitting a language is the same invisibility failure as a file in no
   module, one level up.

Proof: `python3 fixtures/mixed_repo/verify_multilang.py` (single-language `c_repo` behaviour is
asserted unchanged in the same run).
