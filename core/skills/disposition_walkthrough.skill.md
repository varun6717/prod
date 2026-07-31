# disposition_walkthrough — the enrichment stage's one human checkpoint

> ⚠ **Stub (TASK-102).** The full skill lands at **TASK-120**. Role statement only; do not
> execute this stub against a run.

The guided, interactive dispositioning of escalated enrichment findings (ADR-008 D-A16/D-A17):
present one finding with its evidence, recommend a disposition with reasoning, let the operator
interrogate ("show me the code"), record the decision **and rationale** to `decisions.jsonl`.
Four binding constraints: **proposes, never decides** · **triage, don't enumerate** (batch
routine technical consequences; give scope-moving findings and no-code gaps individual
attention) · **sequence dependency chains** (an upstream reversal revisits downstream findings)
· **resumable** (status persists per finding in `enrichment.json`). The defer path is required —
"cannot determine yet" routes the finding to §17 Open questions, never forces a guess.
