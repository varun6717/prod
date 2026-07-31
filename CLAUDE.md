# CLAUDE.md — PDLC_App_v2 (external Claude Code build)

**Read this file first, at the start of every session.** It tells you what this repo is, where the authoritative design lives, how to execute a task, and the rules you must not break. It is short on purpose; the substance is in `docs/`.

---

## What this repo is

You are building **PDLC_App_v2** — an agentic **Solution Intent → enrichment → Jira** generation pipeline for JPMC Merchant Services (per **ADR-008**, accepted 2026-07-31; BRD/FRD are retired). Five layers: **Data & context → Solution Intent v1 → enrichment (v2) → Jira (4-level plan) → Metrics**. This repo is the **external Claude Code build**; it is validated here, then ported to the JPMC VDI later (see `VDI_WIRING.md`).

**Current slice (post-ADR-008):** single domain `payment_brand`; single repo; **Solution Intent v1 → enrichment → v2** (Jira 4-level plan follows; push behind G3); mock-fixture inputs per source type (D-A24) + one Stratus C repo. Breadth (multi-repo, more languages, multi-domain, cross-language closure) stays deferred.

---

## Authoritative documents (precedence order — do not reopen)

All design docs live in **`./docs/`**. They are authoritative and frozen; you implement against them, you do not redesign them.

1. **`docs/REQUIREMENTS.md`** — WHAT / WHY. FR/NFR IDs, MoSCoW, the resolved decisions **D1–D11**. **Read the ADR-008 supersession notice at its head first**: several D-blocks are ⛔ superseded or 🔧 amended by **D11** (the Solution Intent pivot) — never build against a ⛔ block. **Do not reopen D1–D11**; `docs/design/ADR-008-solution-intent-pivot.md` (Accepted) is normative for the new subsystems.
2. **`docs/TECH_SPEC.md`** — HOW. On-disk schemas, the code-impact subsystem (extractor / dispatcher / onboarding gate), the seams, `jpmc_adapters`, telemetry→metrics, gate thresholds, build checks. **Every YAML/JSON block here is a contract; field names are part of it.** Build directly off these.
3. Supporting context (read when a task cites them): `docs/SKILLS_INDEX.md`, `docs/BUILD_OVERVIEW.md`, `docs/brd_frd_overview.html`, `docs/COPILOT_VDI_VALIDATION.md`, and the seed skills `docs/brd_author.skill.md`, `docs/code_impact_assess.skill.md`, `docs/code_map_build.skill.md`, `docs/max-autonomy.skill.md`.

> The older **v1 8-layer platform (L0–L8)** is **dead**. Ignore any v1 reference.

---

## How to execute a task

**`TASK_LIST.md` is the single task list** — the only one. It opens with the execution protocol, the hard rules, and the VDI environment notes; then a **done ledger** (one line per completed task, TASK-000–063B); then the **open work**. (It was consolidated from `TASK_LIST.md` + `TASK_VDI.md` + `TASK_VDI_BOOTSTRAPS.md` on 2026-07-29 — the completed tasks' full specs and the Copilot bootstrap prompts live in git history at `f8f2ae1` and earlier. Do not recreate those files.)

Work through it in order. Each open task carries:

- **Depends on** — prior tasks + the on-disk artifacts that must already exist. **Verify these exist before starting** (list the files; if a dependency is missing, stop and say so).
- **Reads** — the *exact* doc + section to open (e.g. ``docs/TECH_SPEC.md`` §5.3). **Open and read the cited sections before writing anything.** Do not work from memory of the design; the cited section is the contract.
- **Creates / edits** — the exact output paths (from `docs/TECH_SPEC.md` §2).
- **Acceptance** — concrete, checkable conditions. The task is done only when all are true.
- **Proof** — what demonstrates correctness.

After finishing a task, follow `TASK_LIST.md`'s **Execution protocol** step 5–6: verify, re-publish the registry, **tick the checkbox**, commit. Then collapse the task to a one-line entry in the done ledger. The checkbox state is how a later session knows what is done.

---

## Context-restart protocol (important — context will get large)

It is safe to **start a fresh chat / new context window at any phase boundary** (marked in `TASK_LIST.md`). To re-orient a fresh session:

1. Read this `CLAUDE.md`.
2. Open `TASK_LIST.md`: read its protocol + hard rules, skim the **done ledger** for what already exists, then go to the **first unchecked task under OPEN WORK** — that is where to resume.
3. Inspect the repo on disk (`core/`, `overlays/`, `runs/`, `fixtures/`) to confirm what the ledger claims — disk state is ground truth.
4. Execute the next task per "How to execute a task" above.

Durable state lives in **files and git**, never in the conversation. Never rely on something said in an earlier session; if it matters, it is on disk.

---

## Hard rules (carry these into every task)

- **Ladder discipline.** Requirements define WHAT/WHY; the tech spec defines HOW; the task list defines the build sequence. If a task would change a pinned contract or reopen D1–D11, **stop and flag it** — that is out of scope.
- **Two seams only (FR-XS-01):** the **domain seam** (SI section profile / `jira_template` — the vocabulary is deleted per ADR-008) and the **runtime-tool seam** (instruction file / wrappers / prompt files / launch). Non-domain variation points: the per-language **extractor** (onboarding gate) and the per-repo **signal profile** (D11.4 gate). Nothing else varies.
- **Binding rationales (never violate):** the structural extractor is **deterministic and frozen** — never model-rewritten at runtime; the map-build gate is **model-free**; the model owns only `purpose` **text** in the code map (tags are deleted; module membership + edges are deterministic per the frozen signal profile); ingestion **never branches on domain**; the only external mutation is the (deferred) Jira push; scope changes are **operator-decided** (human-mediated flag loop).
- **MVP scope:** single domain `payment_brand`; single repo; **in-session execution** (no direct Claude API); files-as-artifacts + **JSONL ledger** (no SQLite); **Solution Intent v1 → v2** this slice (ADR-008).
- **Cite-or-flag:** every substantive artifact claim is grounded to a source/frame/operator answer or marked `[TBD — unsourced]`. Never invent.

---

## Resolved flag (F1 + 3, reconciled at TASK-017, V-approved)

**F1 (and three more) — adapter emit-map vs vocabulary drift.** Authoring `adapter.yaml` (TASK-017) surfaced **four** per-tag drifts between §6.6.3's adapter instance and D5/`vocabulary.payment_brand.yaml`'s `emitted_by` column (only `mandate`/F1 was documented). Reconciled holistically against reality, V-approved:
- **Class 1 (vocabulary right → fixed `adapter.yaml`):** `mandate` (F1) and `transaction_flow` — `article_summarize.emits` now includes both (§6.6.3 had omitted them).
- **Class 2 (code skill right → fixed vocabulary, r2):** `card_brand`, `message_format` — `emitted_by` gained `code_map_build` (both are `code_tag: true` and in `CODE_MAP_TAGS`; the column had dropped it for these two). `vocab_sha` bumped `d5frozen → d5frozen-r2`.

All 12 per-tag mappings now match; §10.5 verified green at TASK-017 (re-gated at TASK-021). **Port note:** the external `docs/REQUIREMENTS.md` D5 table is now reconciled (TASK-061 added `code_map_build` to `card_brand`/`message_format`) — carry the same fix into the JPMC-side D5 at port time.

---

## Resolved decision (D9 amendment — `start-ingest` Layer-1 kickoff, V-approved)

**Gap found on VDI:** the prompt-file set (`start-brd`/`start-frd`/`start-jira`) had **no operator entry point for Layer 1** (Data & context). The surfaced start gesture pointed at `start-brd`, which overrides the orchestrator role and jumps to BRD authoring — so running it first silently skipped ingestion (no `context_set/index.json`, no `code_map.json`). **Resolution (full ladder, V-approved):** added **`start-ingest`** — a *non-interactive kickoff* prompt (distinct in kind from the three stage transitions) that keeps the orchestrator role and executes Run order step 1 (`source_processor` fan-out → `merge_manifest.py`), then surfaces `start-brd`. The per-tool **start gesture (FR-XS-22) is repointed** `start-brd → start-ingest`. Amended across the ladder: D9 + FR-XS-11 + §10.2 (`prompt_files: [start-ingest, start-brd, start-frd, start-jira]`), the manifest, both overlays, the generator, both `launch.md`, and the instruction template. §10.2 parity green (8 roles + 4 prompts). **Port note:** carry this amendment into the JPMC-side D9/manifest at port time.

---

## Repo layout (after TASK-000)

```
./CLAUDE.md            ← you are here
./TASK_LIST.md         ← the single task list: protocol + hard rules, done ledger, open work
./docs/                ← authoritative design (REQUIREMENTS, TECH_SPEC, supporting)
./core/                ← the generic core you build (skills, scripts, extractors, adapters, profiles, templates)
./overlays/            ← the two runtime-tool overlays (claude, copilot)
./fixtures/            ← input fixtures (PDF, C repo, signed-off code_map)
./runs/                ← run workspaces created when the spine is exercised (Phase 3+)
```
