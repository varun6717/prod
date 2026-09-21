# current_commit_changes_overview.md

**Commit of 2026-09-21 — `neuro_phase1_1.html`, the Phase 1.1 one-view illustration.**
Baseline: lands on top of `c0d12e7` (*Interchange Code Generator brief: interchange-code-generator.html*).

This commit carries **no application code**. It adds one published stakeholder artifact and nothing
else. Nothing in `core/`, `overlays/`, `fixtures/` or `runs/` is touched, so nothing needs
re-publishing to the registry.

---

## Files in this commit

| File | State | What it is |
|---|---|---|
| `neuro_phase1_1.html` | new | Phase 1.1 of the Neuro knowledge base in a single viewport: one slice of layer 01, loaded by an agent, reached from VS Code, measured |
| `current_commit_changes_overview.md` | rewritten | this briefing |

### What the page is

One fit-to-viewport diagram in the instrumentation style of `neuro_kickoff.html` (same palette and
type; that file is still untracked and is **not** in this commit). It takes the kickoff's
knowledge-base cylinder and draws only the first build slice. Five numbered zones:

- **1 Expand** — the five-layer cylinder with only layer 01 lit (02–05 dashed, *LATER*). Layer 01
  opens into four Visa document families: **01.1 Payment Brand Articles** (lit, *building now*),
  01.2 Tech Letters, 01.3 Interchange Guides, 01.4 Auth & Clearing Guides (dashed, *next · same
  pipeline*). Brand chips: Visa on; Mastercard, Amex, Discover parked.
- **2 Ingestion agent** — source PDFs → Extract → Chunk (by section; keeps id, §, page, effective
  date) → Load (embed + upsert, content-hashed, versioned), on a schedule, into 01.1 only.
- **3 MCP server** — read-only, over the KB retrieval API: `search_articles(q, k)`,
  `get_chunk(id)`, `list_articles(since)`. The board states why MCP rather than a bare API.
- **4 VS Code** — a mock agent-mode pane (question → tool call → cited answer) above a golden
  question set scored hit / ranked low / miss.
- **5 Observability** — a trace per tool call and a verdict per question feed six signals (hit
  rate @k, MRR, citation precision, no-answer rate, latency p95, freshness); an improve loop runs
  back to the agent with a person reviewing the misses.

A dock under the board walks the five steps (button, chips, arrow keys, or a click on any zone)
and shows the Phase 1.1 exit criteria at rest. A small dashed box lists what comes after 1.1; the
page draws none of it.

### Data provenance

Nothing on the page is measured. Article ids, the three sample questions, the golden-set dot
pattern and the six metric curves are invented and labelled *illustrative* on the page. The MCP
tool names are a proposed interface, not an existing one. No real Visa content appears.

### Behaviour that is newly stricter

None.

### Signature / contract changes

None.

### Conflict hot spots for a VDI wiring session

None. The five `[TBD — VDI]` placeholders and the connectors are untouched. VDI-browser note: the
page uses no `color-mix()` and its Motion control is a button, not the OS reduced-motion setting —
the same two accommodations as `4b6acfe`.

### Derived artifacts to regenerate rather than merge

None.

### Green-bar commands

Unchanged — `for f in $(find fixtures -name "verify_*.py"); do python3 "$f"; done` and
`python3 core/scripts/build_checks.py`; neither is affected by this commit.

---

## Port note

Nothing here ships to the VDI as code. The page is a published artifact, read in a browser, not
executed.
