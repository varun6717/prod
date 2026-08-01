# Design decision records (ADRs)

Standalone design records for decisions that refine — but do not reopen — the frozen design in
`REQUIREMENTS.md` (D1–D11) and `TECH_SPEC.md`. Each ADR holds the full context/decision/rationale;
the corresponding requirement in `REQUIREMENTS.md` carries only a **stub** (ID, priority,
one-paragraph ruling, trigger) that points here. When an ADR and a requirement disagree, the
requirement's pinned schema wins — the ADR explains *why*, it does not override the contract.

**ADR-008 is the exception, and the reason this note exists.** It did not refine the design; it
**pivoted** it — BRD/FRD retired, Solution Intent v1 → enrichment → v2 in their place, the tag
vocabulary deleted, routing moved to operator-declared dispositions. Its **D-A blocks are normative
for the new subsystems** until the next spec consolidation, and three earlier ADRs died with it.
Read the supersession notice at the head of `REQUIREMENTS.md` before building against any D-block.

| ADR | Title | Status | Requirement(s) | Built? |
|-----|-------|--------|----------------|--------|
| [ADR-001](ADR-001-c-extractor-tree-sitter.md) | C extractor toolchain: tree-sitter (not ctags/cscope) | Accepted | FR-DC-14…17 (toolchain) | **built** (TASK-009/012) |
| [ADR-002](ADR-002-polyglot-partition-dispatch.md) | Polyglot repos: per-language partition dispatch | Accepted | FR-DC-17 (dispatch) | **built** (TASK-010); re-proven post-pivot (TASK-116) |
| [ADR-003](ADR-003-agent-assisted-vocabulary.md) | Agent-assisted vocabulary: onboarding proposal + every-run adequacy | ⛔ **superseded by ADR-008** | — | **dead** — the vocabulary is deleted (D-A19/D-A22). The propose-never-bless pattern survives in the D-A21 onboarding gate |
| [ADR-004](ADR-004-agent-assisted-profile-integration.md) | Agent-assisted profile integration (gate 3) | ⛔ **superseded by ADR-008** | — | **dead** — tags and the topic layer are gone (D-A19); profiles collapse to the SI section contract + `jira_template` |
| [ADR-005](ADR-005-agent-assisted-adapter-onboarding.md) | Agent-assisted adapter onboarding | ⛔ **superseded by ADR-008** | — | **dead** — `adapter.yaml` loses `emits`/tag lanes; the doc pipeline is domain-agnostic extract + index (D-A18) |
| [ADR-006](ADR-006-extractor-onboarding.md) | Agent-assisted extractor onboarding (Branch A) | Accepted | FR-DC-19 (W) | deferred (2nd language) |
| [ADR-007](ADR-007-cross-repo-code-impact.md) | Multi-system / cross-repo code impact (fractal extension) | Accepted | FR-DC-13 (C5) | deferred (multi-repo, port) |
| [**ADR-008**](ADR-008-solution-intent-pivot.md) | **Solution Intent pivot** — BRD/FRD → SI, tag removal, disposition routing | ✅ **Accepted 2026-07-31** | **D11** (+ the FR re-cut) | **built** — Milestones D0–D6 |
| [ADR-008 · Phase C](ADR-008-impact-analysis.md) | Impact analysis: keep / amend / retire, per tracked file | ✅ complete 2026-07-31 | — | the disposition ledger the D-phase tasks executed against |

## Supporting analyses (not ADRs)

| File | What it is |
|---|---|
| [discovery-adequacy-assessment.md](discovery-adequacy-assessment.md) | why discovery adequacy is an **error** for §9/§12/§13 and a **warning** elsewhere — the tiering behind `check_discovery_adequacy.py` |
| [SURVEY-doc-structure.md](SURVEY-doc-structure.md) | the source-document survey the doc pipeline was designed against |
| [SURVEY-stratus-repo.md](SURVEY-stratus-repo.md) | the Stratus C repo survey behind the signal profile and the onboarding gate |
| [PDLC_Configurator.jsx](PDLC_Configurator.jsx) | the UI reference the React configurator was built from |
