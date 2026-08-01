# Claude overlay — launch (`terminal_interactive`)

`overlay_manifest.overlays.claude.launch: terminal_interactive`. This is the **launch** piece of
the runtime-tool seam for the Claude overlay (§6.2); kept native, not abstracted (D9).

**Method.** The run executes in an **interactive Claude Code terminal session** opened at the
run's working path (the hydrated scaffold). MVP is **manual start** (D10, FR-XS-22); auto-launch
is **deferred** (FR-XS-25). Generate lays the scaffold, opens VS Code where allowed, and surfaces
the exact start gesture — it does **not** auto-start the session.

**Start gesture** (also surfaced by the generated `CLAUDE.md` tail, FR-XS-22): open a Claude Code
terminal session at the working path and invoke `/start-ingest` — the Layer-1 kickoff that fires
the data-&-context fan-out (`source_processor` ×N → `merge_manifest.py`). It keeps the orchestrator
role and closes by surfacing `/start-si` for the Solution Intent stage.

**Stage advance** (operator-performed, FR-XS-11): `/clear` or a new session, then the next prompt
file — `/start-enrich`, then `/start-jira`. The agent **surfaces** these as the closing line of a
stage; it never self-issues them.

**Environment contract** (NFR-04; §6 model routing): the launch step sets the model-routing
environment variables — `CLAUDE_CODE_USE_BEDROCK=1`, the AWS region, and the Bedrock model id — so
models run via JPMC Bedrock. These are env vars set **at launch**, not a function the skills call;
skills stay model-neutral.

**Prompt files shipped** (`overlays/claude/prompts/`): `start-ingest` (Layer-1 kickoff),
`start-si`, `start-enrich`, `start-jira`.
