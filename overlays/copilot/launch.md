# Copilot overlay — launch (`agent_mode`)

`overlay_manifest.overlays.copilot.launch: agent_mode`. This is the **launch** piece of the
runtime-tool seam for the Copilot overlay (§6.2); kept native, not abstracted (D9). Parity twin of
`overlays/claude/launch.md` (`terminal_interactive`).

**Method.** The run executes in **VS Code Copilot agent mode** at the run's working path (the
hydrated scaffold). MVP is **manual start** (D10, FR-XS-22); auto-launch is **deferred**
(FR-XS-25). Generate lays the scaffold, opens VS Code where allowed, and surfaces the exact start
gesture — it does **not** auto-start the session.

**Start gesture** (also surfaced by the generated `copilot-instructions.md` tail, FR-XS-22): open
Copilot agent mode at the working path and run the `start-ingest` prompt file — the Layer-1
kickoff that fires the data-&-context fan-out (`source_processor` ×N → `merge_manifest.py`). It
keeps the orchestrator role and closes by surfacing `start-si` for the BRD stage.

**Stage advance** (operator-performed, FR-XS-11): press **`Ctrl+N`** for a fresh agent, then run
the next prompt file — `start-enrich`, then `start-jira`. The agent **surfaces** these as the closing
line of a stage; it never self-issues them.

**VDI prerequisite — terminal allow-list (FR-XS-26).** Agent mode runs the plumbing scripts as
terminal commands; the **user-scope** terminal allow-list must be provisioned so a multi-step loop
runs without per-command approval stalls. This is **surfaced by Generate/onboarding and provisioned
centrally — the scaffolder does NOT emit it.** See `overlays/copilot/VDI_PREREQUISITES.md`.

**Prompt files shipped** (`overlays/copilot/.github/prompts/`): `start-ingest` (Layer-1 kickoff),
`start-si`, `start-enrich`, `start-jira`.
