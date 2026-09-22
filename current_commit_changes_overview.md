# current_commit_changes_overview.md

**Commit of 2026-09-22 — `neuro_phase1_1_v3.html`, the light-ground version of the Phase 1.1 one-view.**
Baseline: lands on top of `426c45b` (*Phase 1.1 one-view v2: neuro_phase1_1_v2.html — same drawing, no motion or controls*).

This commit carries **no application code**. It adds one published stakeholder artifact and nothing
else. Nothing in `core/`, `overlays/`, `fixtures/` or `runs/` is touched, so nothing needs
re-publishing to the registry.

---

## Files in this commit

| File | State | What it is |
|---|---|---|
| `neuro_phase1_1_v3.html` | new | `neuro_phase1_1_v2.html` re-coloured: white ground, blue in place of gold; drawing and words unchanged |
| `current_commit_changes_overview.md` | rewritten | this briefing |

### What the page is

A palette-only derivative of v2 (`426c45b`), which stays as the dark version. Every layout
coordinate, label and the exit-criteria footer are identical. Changes are confined to colour:

- Ground: white page, pale-grey board, dark-navy ink; rules and dims lightened to match.
- Accent: gold (`#E8B34A`) → blue (`#2563EB`) throughout — the lit layer 01, the 01.1 disc, the
  ingestion pipeline, the 1/2 badges, the citation pills, the eyebrow and thesis pill.
- Other layer hues darkened to hold on white (teal, violet, green, orange); the improve-loop line is
  slate instead of cream.
- Exception: the golden set's *ranked low* status stays amber (`#E0A020`) rather than turning
  blue, so a warning status does not share the accent colour of the *expected* chip beside it.

### Data provenance

Same invented, *illustrative*-labelled content as v1 and v2; nothing measured.

### Behaviour that is newly stricter

None.

### Signature / contract changes

None.

### Conflict hot spots for a VDI wiring session

None. The five `[TBD — VDI]` placeholders and the connectors are untouched. No script, no
`color-mix()`.

### Derived artifacts to regenerate rather than merge

None.

### Green-bar commands

Unchanged — `for f in $(find fixtures -name "verify_*.py"); do python3 "$f"; done` and
`python3 core/scripts/build_checks.py`; neither is affected by this commit.

---

## Port note

Nothing here ships to the VDI as code. The page is a published artifact, read in a browser, not
executed.
