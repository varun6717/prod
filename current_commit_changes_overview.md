# current_commit_changes_overview.md

**Commit of 2026-09-22 — `neuro_phase1_1_v2.html`, the quiet version of the Phase 1.1 one-view.**
Baseline: lands on top of `fdc6b9c` (*Phase 1.1 one-view: neuro_phase1_1.html — layer 01 slice, ingestion agent, MCP to VS Code, observability loop*).

This commit carries **no application code**. It adds one published stakeholder artifact and nothing
else. Nothing in `core/`, `overlays/`, `fixtures/` or `runs/` is touched, so nothing needs
re-publishing to the registry.

---

## Files in this commit

| File | State | What it is |
|---|---|---|
| `neuro_phase1_1_v2.html` | new | The Phase 1.1 drawing from `neuro_phase1_1.html` as a single still: same message, no motion, no controls |
| `current_commit_changes_overview.md` | rewritten | this briefing |

### What the page is

A second cut of the Phase 1.1 illustration for audiences who found the first busy. `neuro_phase1_1.html`
(`fdc6b9c`) is unchanged and stays the animated version. The five zones and their content are the
same — layer 01 expanded into four Visa families with 01.1 Payment Brand Articles lit; the ingestion
agent (extract → chunk → load, on a schedule); the read-only MCP server; the VS Code agent-mode
pane with the golden question set; observability with the improve loop back to the agent — and the
footer states the same exit criteria.

What was removed to quiet it: all animation and all JavaScript (walkthrough, step chips, keyboard
shortcuts, Motion toggle, flow lines, packets, spinner, typing loop, glow); per-band sub-labels and
"LATER" tags (replaced by one line per group); the brand chips; the six sparkline tiles (now six
labels in a row); the "after 1.1" box (now a footnote); the board's grid texture and shadow.

### Data provenance

Nothing on the page is measured. The article ids, sample question, golden-set pattern and MCP tool
names are the same invented, *illustrative*-labelled content as `neuro_phase1_1.html`.

### Behaviour that is newly stricter

None.

### Signature / contract changes

None.

### Conflict hot spots for a VDI wiring session

None. The five `[TBD — VDI]` placeholders and the connectors are untouched. The page has no script
and no `color-mix()`, so the VDI-browser accommodations from `4b6acfe` are moot for it.

### Derived artifacts to regenerate rather than merge

None.

### Green-bar commands

Unchanged — `for f in $(find fixtures -name "verify_*.py"); do python3 "$f"; done` and
`python3 core/scripts/build_checks.py`; neither is affected by this commit.

---

## Port note

Nothing here ships to the VDI as code. The page is a published artifact, read in a browser, not
executed.
