# jira_validator — G3, the last gate before the only external mutation

> ⚠ **Stub (TASK-102).** The full skill lands at **TASK-123**. Role statement only; do not
> execute this stub against a run.

Scores the 4-level plan (§9.4, D-A23): `0.5 × traceability + 0.5 × testability` (the formula
inherited from the retired FRD validator), plus the hard story guardrails — every §16 entry
yields ≥1 story (dropped-impact catch); every story traces to §16 or §7 (invented-story catch);
every story names code or carries its `new_build`/`non_code` flag; parent-chain integrity
across all four levels; and, where a Technical Specification source exists, the reverse
completeness check (do the stories, together, satisfy the letter?). G3 stays an operator act
(D4) — the score informs, the human confirms the push.
