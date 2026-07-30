# Design decision records (ADRs)

Standalone design records for decisions that refine — but do not reopen — the frozen
design in `REQUIREMENTS.md` (D1–D10) and `TECH_SPEC.md`. Each ADR holds the full
context/decision/rationale; the corresponding requirement in `REQUIREMENTS.md` carries
only a **stub** (ID, priority, one-paragraph ruling, trigger) that points here. When an
ADR and a requirement disagree, the requirement's pinned schema wins — the ADR explains
*why*, it does not override the contract.

| ADR | Title | Status | Requirement(s) | Built? |
|-----|-------|--------|----------------|--------|
| [ADR-001](ADR-001-c-extractor-tree-sitter.md) | C extractor toolchain: tree-sitter (not ctags/cscope) | Accepted | FR-DC-14…17 (toolchain) | **built** (TASK-009/012) |
| [ADR-002](ADR-002-polyglot-partition-dispatch.md) | Polyglot repos: per-language partition dispatch | Accepted | FR-DC-17 (dispatch) | **built** (TASK-010) |
| [ADR-003](ADR-003-agent-assisted-vocabulary.md) | Agent-assisted vocabulary: onboarding proposal + every-run adequacy | Accepted | FR-DC-20 (W), FR-DC-21 (S) | L1 built (TASK-013); L2/L3 deferred |
| [ADR-004](ADR-004-agent-assisted-profile-integration.md) | Agent-assisted profile integration (gate 3) | Accepted | FR-DC-22 (W) | deferred (port / domain #2) |
| [ADR-005](ADR-005-agent-assisted-adapter-onboarding.md) | Agent-assisted adapter onboarding | Accepted | FR-DC-23 (W) | deferred (port / domain #2) |
| [ADR-006](ADR-006-extractor-onboarding.md) | Agent-assisted extractor onboarding (Branch A) | Accepted | FR-DC-19 (W) | deferred (2nd language) |
| [ADR-007](ADR-007-cross-repo-code-impact.md) | Multi-system / cross-repo code impact (fractal extension) | Accepted | FR-DC-13 (C5) | deferred (multi-repo, port) |
