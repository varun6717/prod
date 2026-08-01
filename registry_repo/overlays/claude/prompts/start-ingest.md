---
description: Kick off the run — fire Layer 1 (Data & context). Stay the orchestrator and execute Run order step 1.
---

You are **starting this run** — the **Layer 1 (Data & context)** stage. This is the run's
**kickoff**, not a stage transition.

Stay in your **orchestrator** role (defined in `CLAUDE.md`); do **not** become an authoring agent.
Execute **Run order step 1** exactly as defined there:

1. Read `UI_INPUT.yaml` — `domain` selects the profile; `sources[]` is the work list.
2. **Fan out one `source_processor` subagent per `UI_INPUT.sources[]` entry, in parallel** (via
   the `.claude/agents/source_processor` wrapper). Each runs its source-type connector then the
   domain adapter, writing that source's `context_set/<source>/` slice + manifest entries. For the
   **code** source, `source_processor` hands off to a `code_map_build` subagent (`code_map/{components,files}.json`,
   cached through the 4-branch gate on `(commit_sha, profile_sha)`).
3. After the fan-out completes, run `core/scripts/merge_manifest.py` to deterministically fan in
   `context_set/index.json`.

This stage is **non-interactive** — the subagents run autonomously and return concise summaries;
do **not** start an authoring chat. Emit telemetry per invocation (D8). Ingestion **never branches
on domain** — the connectors are source-type-keyed; the domain adapter is the only domain-aware
step, and it is selected by `UI_INPUT.domain`, not branched in code.

When Layer 1 is complete — `context_set/index.json` and `code_map/{components,files}.json` written — **surface** the
next-stage transition; do **not** perform it (FR-XS-11): tell the operator to `/clear` or start a
new session, then run `/start-si`. Never self-issue the transition.
