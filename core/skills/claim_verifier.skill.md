# claim_verifier — enrichment Arm 2 (claim → code verification)

> ⚠ **Stub (TASK-102).** The full skill lands at **TASK-119**. Role statement only; do not
> execute this stub against a run.

Arm 2 of enrichment (ADR-008 D-A5–D-A8): extract the factual **current-state claims** from the
verdict-eligible Solution Intent sections (§2, §5, §6, §10, §13, §14), sort the population
(claims / business judgment / future-state — only the first is verdictable), **cluster by code
region**, and per cluster run one coarse match against the code map → strong-match verdict,
deep-read of the slice, or *unverifiable* (cheap, honest, often §14 material). Stage corrections
for source-derived claims with inline code provenance; escalate contradictions of operator/frame
claims; auto-fill `[TBD — unsourced]` gaps the code answers; contribute §18 counts. Point
lookups only — Arm 2 never walks closure (that is Arm 1's job). Findings land in
`enrichment.json`; nothing is applied until the disposition walkthrough resolves escalations.
