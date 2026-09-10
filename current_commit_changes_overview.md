# current_commit_changes_overview.md

**Commit of 2026-09-10 — `pbi_neuro_kickoff.html`, the kickoff presentation page.**
Baseline: lands on top of `4b6acfe` (*Keep animations on under VDI; add Motion toggle and color-mix fallbacks* — the Signal Studio page series).

This commit carries **no application code**. It adds one published stakeholder artifact and nothing
else. Nothing in `core/`, `overlays/`, `fixtures/` or `runs/` is touched, so nothing needs
re-publishing to the registry.

---

## Files in this commit

| File | State | What it is |
|---|---|---|
| `pbi_neuro_kickoff.html` | new | Kickoff deck as a single page: the case for automating PBI with AI, and the Neuro KB → agentic-process stage |
| `current_commit_changes_overview.md` | rewritten | this briefing |

### What the page is

A presentation page in the same instrumentation style as `neuro_overview_v2.html`, built for a
kickoff audience rather than an engineering one. Six blocks, top to bottom:

- **Title + five KPI tiles** — ~19 card brands · ~4,400 articles/yr (2026 projected) · ~14% projected
  growth 2025 → 2026 · $28B pass-through Interchange processed in 2025 · 20% of Stratus PBI capacity.
  Numbers count up on load.
- **01 The case** — four beats on a rail: intake grows ~14%/yr → no team scales at that rate across
  26 engines → automate PBI with AI, starting with Interchange (complex, impactful, majority of the
  impact on Stratus) → reinvest the freed capacity in the backlog (Auth & Clearing).
- **02 Growth** — articles per year 2020 → 2026 (2,881 booked through Aug + dashed extension to
  ~4,400), the 3,855 → ~4,400 projection, and the quarterly chart with Q2 2026 (1,267) as the record.
- **03 Why Interchange, and why Visa + Mastercard** — a three-step funnel: all articles by network
  (Visa + MC = 78.6%) → implemented articles as a two-slice pie (Interchange 18.6%, up from 12.5%, vs
  everything else) → Interchange by network (91.5% Visa + MC). Then three reason cards.
- **04 The journey** — the four phases on the complexity rail; Phase 3 carries the "Neuro starts
  here" badge, Phase 1 carries the measured proof chip (70–80% faster, ~5.9× throughput).
- **05 Neuro** — the knowledge-base → agentic-process stage from the overview, with Stage 0 removed
  and Stage 5 renamed *Code Recommendation & Testing*. Layer 02's sub-label reads *System specs*.

Every section can be brought forward (click, or its pill): the page behind blurs, the section lifts
and enlarges; Esc or a click outside closes it. Layers and stages on the Neuro diagram still open
their own detail panel. Ambient motion only — no player, no step chips.

### Data provenance

Chart values are transcribed from the five source screenshots kept beside the file (`stats.png`,
`trend_over_time.png`, `mop.png`, `type.png`, `journey.png`); those PNGs are **not** committed. The
$28B and 20%-of-capacity figures are V-supplied and appear in no screenshot. The type pie uses the
2026 YTD tightened-scope numbers (n=381; 2025 n=415).

### Behaviour that is newly stricter

None.

### Signature / contract changes

None.

### Conflict hot spots for a VDI wiring session

None. The five `[TBD — VDI]` placeholders and the connectors are untouched.

### Derived artifacts to regenerate rather than merge

None.

### Green-bar commands

Unchanged — `for f in $(find fixtures -name "verify_*.py"); do python3 "$f"; done` and
`python3 core/scripts/build_checks.py`; neither is affected by this commit.

---

## Port note

Nothing here ships to the VDI as code. The page is a published artifact, read in a browser, not
executed.
