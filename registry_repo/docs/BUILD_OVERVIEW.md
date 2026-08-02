# Build Overview — Solution Intent → enrichment → Jira

**Project:** PDLC_App_v2 · JPMC Merchant Services · AI Automation
**Purpose:** orientation. What the pipeline is, how the pieces fit, and where each rule actually
lives. Read this to get your bearings, then work from the contracts.

**This file is not authoritative.** The ladder is `REQUIREMENTS.md` (WHAT/WHY — FR/NFR, D1–D11) →
`TECH_SPEC.md` (HOW — the pinned schemas and seams) → `TASK_LIST.md` (the build sequence). Where
this overview and a spec section disagree, **the spec wins**, and this file has a bug.

> **Re-cut 2026-08-01 (TASK-126).** This was the handoff seed from the originating design
> conversation — it ended with "next chat: produce the requirements document," and described a
> BRD → FRD → Jira-epics pipeline. **ADR-008 (accepted 2026-07-31) retired BRD and FRD.** The
> architecture below — the seams, the topology, the orchestration model, the file conventions —
> survived the pivot unchanged and is stated here as it stands. The pipeline layers did not, and
> are restated.

---

## 1. What we are building

An agentic pipeline that turns enterprise product context into a validated **Solution Intent**, a
code-grounded **enrichment** of it, and a controls-tracked **4-level Jira plan** — driven from a
small config UI, executed by an AI coding agent (**Claude Code or GitHub Copilot**) running locally
in VSCode.

The central idea, and the one worth holding on to: **v1 says what we intend, from sources and the
operator. Enrichment checks that against the code. v2 is the reconciliation.** v1 is authored
**code-blind** on purpose — a v1 that already knew the code would leave enrichment nothing to find,
and no way to tell a source's claim from a tool's inference. G1 acceptance **freezes** v1, so every
change after it is a traceable delta rather than an edit.

### Operator journey (end to end)

1. **UI** — the operator enters the working path, the sources (each with a declared **disposition**), the requirement/project frame + overview, the domain, and the runtime tool.
2. **Generate (G0)** — the backend creates the directory, writes `UI_INPUT.yaml`, lays the shared core + the domain pack + the chosen tool's overlay.
3. **VSCode** — the operator starts the agent session (Claude Code in the terminal, or Copilot agent mode).
4. **`start-ingest`** — per-source fan-out → `context_set/` + `index.json` + the per-artifact indexes; the code lane builds the map through the 4-branch gate.
5. **`start-si`** → Solution Intent **v1** (18 sections) → flag loop → **G1 accept, which freezes v1**.
6. **`start-enrich`** → Arm 1 (requirement → code) + Arm 2 (claim → code) → the **one** operator walkthrough → the apply pass writes **v2** → **G2**.
7. **`start-jira`** → the 4-level plan → **G3** → push (the run's only external mutation).
8. **Outputs** — `context_set/`, `code_map/`, `v1.md`, `enrichment.json`, `v2.md`, `jira_plan.json`, `jira_trace.json`, and the JSONL ledger under `ledger/`.

---

## 2. Architecture — the five layers

1. **Data & context** — configure → ingest → pre-process → **index** → serve. Fans out per source. Docs get a structural extract plus a per-artifact `<doc>.index.json`; code gets `code_map/{components,files}.json`.
2. **Solution Intent v1** — chat-driven authoring + validation → `v1.md`. Gated at **G1**; acceptance freezes it.
3. **Enrichment (v1 → v2)** — two assessment arms against the frozen v1, one operator walkthrough, one deterministic apply pass → `v2.md`. Gated at **G2**.
4. **Jira** — decompose v2 into Initiative → Deliverable → Epic → Story, validate the trace, gate at **G3**, push via the `jpmc_adapters` seam.
5. **Metrics** — auto-computed by scanning `telemetry.jsonl`. No metric is hand-entered.

### The gate ladder

| Gate | On | Meaning |
|---|---|---|
| **G0** | the scaffold | the operator inspects the generated run before it executes |
| **GF** | per flag | the operator decides each surfaced scope flag; the agent never decides scope |
| **G1** | `v1.md` | acceptance **freezes** v1 |
| **G2** | `enrichment.json` → `v2.md` | acceptance locks v2 |
| **G3** | `jira_plan.json` | acceptance **authorises the push** |

Every gate is a **soft score (informs)** plus **hard preconditions (absolute)**. A validator never
auto-advances (FR-XS-13) — it reports, and a human decides. The score and the preconditions do
different jobs: preconditions catch what must never ship, the score catches degradation no single
precondition would notice.

---

## 3. Core principles

- **Generic core + thin seams** — a fixed pipeline shape; variation isolated to a **domain seam** and a **runtime-tool seam**, and nowhere else (FR-XS-01).
- **Three responsibilities, kept separate:** UI = config collection only (→ `UI_INPUT.yaml`); scaffolder/bootstrap = deterministic plumbing; agents = judgment only.
- **The AI session is the orchestrator; Python is called-plumbing.** The session reads its instruction file and delegates to subagents; Python is *called by* the agents. Python never spins up the AI (Copilot cannot be Python-driven in the target environment).
- **Plumbing out of the model** — one correct deterministic outcome → code; judgment → model. The structural extractor is deterministic and **frozen**; the map-build gate is **model-free**; the model owns only `purpose` *text*.
- **State lives in files** — context windows are ephemeral working memory. The artifacts and the JSONL ledger are the durable handoff, so no single session must carry the whole pipeline.
- **Cite-or-flag** — every substantive claim is grounded to a source, the frame, or an operator answer, or marked `[TBD — unsourced]`. Never invented.
- **Ingestion never branches on domain** — routing is by the operator's **declared disposition** (D-A12), never by content the pipeline inferred about a source.
- **MVP-honest** — the smallest correct thing; heavier machinery visibly parked.

---

## 4. Runtime-tool agnosticism (Claude Code vs Copilot)

Both tools converged on the same shape: a root instruction file + agent files with YAML frontmatter
+ an orchestrator delegating to subagents in isolated contexts. That is what makes agnosticism cheap.

### The seam: one shared core + two thin overlays

- **Shared core** (authored once, no tool-specific syntax): the **skills**, the **domain profiles/templates**, the **Python plumbing**, and the **artifact contracts**. Never duplicated per tool.
- **Two idiomatic overlays** (native per tool): the instruction file (`CLAUDE.md` vs `copilot-instructions.md`), the agent definition files, the per-stage **prompt files**, and the launch method. These genuinely differ — keep each native, don't abstract them.

### Agent files vs skills (the thin-wrapper rule)

The **skill** carries the substance and is shared. The **agent definition** is a thin tool-specific
wrapper pointing at it — differing only in frontmatter and location (`.claude/agents/<role>.md` vs
`<role>.agent.md`). Two small wrappers per role over one shared skill; never two copies of the logic.
`check_overlay_parity.py` enforces that both overlays carry every role and prompt (§10.2).

**Eight roles** get wrappers: `source_processor`, `solution_intent_author`,
`solution_intent_validator`, `code_impact`, `claim_verifier`, `disposition_walkthrough`,
`jira_author`, `jira_validator`. Two of them are user-invocable — the SI author and the walkthrough,
the only two places a human is *in* the loop rather than *at a gate*.

### Stage transitions

A fresh context at each interactive boundary is needed on both tools (context hygiene), via
tool-native gestures defined **in the instruction file**: Claude `/clear` → kickoff; Copilot
`Ctrl+N` → the prompt file. The gesture is an **operator action** the agent *surfaces* as the closing
line of the prior stage — the agent cannot self-issue it.

Four prompt files ship in each overlay: **`start-ingest`, `start-si`, `start-enrich`, `start-jira`**.
`start-ingest` is different in kind from the other three — it is a *non-interactive kickoff* that
keeps the orchestrator role and runs the fan-out, rather than a stage transition. It exists because
the surfaced start gesture used to point at authoring, which silently skipped ingestion entirely.

### Context refresh — don't build a mechanism

Both tools auto-compact when the window fills, and a hard reset is one keystroke at a boundary where
a human is already present. So for MVP: **no refresh automation**.

---

## 5. Bootstrap

- **UI** collects the working path, sources + dispositions, the requirement frame + overview, the domain, and the runtime tool.
- **Generate** → the local FastAPI backend creates the directory, writes `UI_INPUT.yaml` (the canonical run record), lays the shared core, lays the chosen overlay.
- **Hydration (scripted)** pulls from the Bitbucket registry — shared skills, the domain's adapter pack, `si_profile.<domain>.yaml`, `jira_template.<domain>.yaml`.
- **Version-pin the registry** — the commit SHA goes into `UI_INPUT.yaml`, for reproducibility.
- **Generate-scaffold and run-workflow are two steps**, so the scaffold can be inspected first — that separation is G0.

---

## 6. Data & context layer

Sources are independent, so the shape is **fan-out / fan-in**: one `source_processor` definition
instantiated **once per source in parallel**, each owning its source end to end and writing its slice
plus manifest entries; then a deterministic `merge_manifest.py` assembles `index.json`. Split at the
**source boundary**, never per file. One source failing does not fail the batch.

**The doc lane:** one lane per source *type*, keyed in `adapter.yaml`, and **every lane ends in
`doc_index`** — the extract step differs because the *format* does, the index step never does.
`default` (PDFs) = the domain pack's `pdf_extract`; `confluence` = the core `confluence_extract`
(one product, one DOM, identical across domains, so packing it would make every new domain
duplicate it); `jira` = the index alone, because the connector already renders the issue payload
to `.md` deterministically. The extract produces a structural `<doc>.md`; `doc_index` then produces
`<doc>.index.json` — one entry per semantic subsection, with
**guardrail 7** holding: `lines_total == lines_indexed`, exactly-once coverage. That is what makes
"the index missed it" impossible rather than merely unlikely, and it is why there is no vector store:
the per-artifact index *is* passage-level retrieval.

**The code lane:** `git clone` into `repo/`, then `code_map_build` produces
`code_map/{components,files}.json` through a **4-branch gate** keyed on `(commit_sha, profile_sha)` —
a profile change invalidates the cache wholesale, a commit change only selectively. Module membership
and edges are deterministic per the frozen signal profile; the model contributes `purpose` text.

**Map, don't copy.** Code is referenced by path and read natively on demand — never inlined into
`context_set/`.

**Deferred:** sync/freshness, change detection and downstream flagging, semantic retrieval.

---

## 7. The generation engine — skill + profile

- **`<x>.skill.md`** = the generic engine (process, boundaries, grounding, interaction). It hardcodes no domain content.
- **`si_profile.<domain>.yaml`** = the arguments — the 18 sections with their sources, `must_capture` items and probes. The routing map is the `sections:` block.
- **Composition is `skill(profile) → artifact`** — the skill file is never edited; the profile parameterizes it at runtime, section by section.

Information hierarchy per `must_capture` item: **source documents** (selective-read) → **the UI
requirement frame** → **chat gap-fill**. Questions are gap-fills tied to unsatisfied requirements,
never one-per-file. An answer given once is not re-asked. Order is deliberate — context and scope
before requirements, and the **executive summary is written last**, from the finished body.

---

## 8. Enrichment — the layer ADR-008 added

Both arms run against the **frozen** v1 and file findings into `enrichment.json`. Neither edits v1;
neither decides anything.

- **Arm 1 — `code_impact` (requirement → code).** Per-assertion impact plus **dependency closure**, both directions, to a fixed point. Produces §16 derived-system-impact entries and gaps.
- **Arm 2 — `claim_verifier` (claim → code).** Point lookup, then **stop**. Answers "is this claim true of the code?" — it does not go exploring. Runs after Arm 1, which has usually already pulled the slices its claims need. An honest `unverifiable` is a valid verdict.

**Scope-moving escalates first.** Before provenance is consulted at all, anything that moves a
scope boundary escalates — however well grounded it is. Scope changes are operator-decided, always.

**Provenance then decides authority (D-A16)** — this is the rule that makes the layer safe:

| The claim came from | and the code contradicts it | so |
|---|---|---|
| a **source document** | the source was wrong | **auto-correct**, with provenance |
| the **operator** or the **frame** | a human asserted this | **escalate** — a tool does not overrule a person |
| nothing (`[TBD — unsourced]`) | there was nothing to contradict | **auto-fill** |

Escalations — and only escalations — reach the **disposition walkthrough**, the single operator turn
of the stage. It **proposes, never decides**; triages rather than enumerates; respects ordering
dependencies so a finding that supersedes others is called first; and is **resumable** across
sessions. Rationale is written to `decisions.jsonl`, the only place it lives.

Then a deterministic apply pass writes v2: corrections revise **in place with provenance**,
discoveries append, **nothing is deleted**, §1 is regenerated last. **`v1 + enrichment.json`
reconstruct `v2` exactly** — which is what makes every touch in v2 traceable to a finding.

---

## 9. Jira layer

- **Four levels**, JPMC's hierarchy: Initiative → Deliverable → Epic → Story. Each level has exactly one source in v2.
- The parent chain is built from **the SI's own ids** — the author never invents one, which is precisely what makes the push idempotent later.
- `jira_author` drafts `jira_plan.json` (**no write to Jira**); `jira_validator` scores the trace and surfaces **G3**; the operator accepts, and that acceptance *is* the push authorization.
- **The push is the run's only external mutation**, so it is defended structurally: `push_plan` requires a `G3Authorization` that only `authorize()` can mint, `dry_run=True` is the default, order is parent-before-child, each result is recorded as it returns, and the trace is written by the caller — so a crash between "wrote to Jira" and "wrote the trace" stays detectable.

---

## 10. Agent topology

- **Orchestrator** = the tool's session reading the instruction file. Hub-and-spoke: subagents return summaries to the orchestrator and do not chain to each other.
- **Interactive stages are their own sessions** — the SI author and the walkthrough are the *active agent* of a dedicated window, because a human talks to them directly. Subagents are autonomous workers, not chat surfaces.
- **Autonomous sub-work = subagents** with isolated context: `source_processor` (×N parallel), both enrichment arms, the validators.
- State flows between stages via **files**, never shared context.
- **Don't over-create agents** — eight roles; everything else is a skill invoked inside one.

---

## 11. Seams summary

- **Constant (shared core):** orchestration logic; the generic per-source-type ingestion connectors; the eight roles and their skills, plus `code_map_build` / `doc_index`; the 18-section SI structure; manifest + selective read; Python plumbing; the ledger.
- **Domain-specific (by domain key):** the adapter pack (`pdf_extract` + `adapter.yaml` run order); `si_profile.<domain>.yaml`; `jira_template.<domain>.yaml`.
- **Tool-specific (the overlay, ×2):** instruction file; agent wrappers; the four prompt files; launch.
- **Non-domain variation points** (deliberately *not* seams): the per-language **extractor**, frozen at the onboarding gate; the per-repo **signal profile**, frozen at the same gate.

---

## 12. File & format conventions

Heuristic: **code-parsed → YAML/JSON; model-read-as-instructions → Markdown; both → YAML
frontmatter + Markdown body.**

- **YAML/JSON:** `UI_INPUT.yaml`, `si_profile.<domain>.yaml`, `jira_template.<domain>.yaml`, `<repo>.profile.yaml`, `index.json`, `<doc>.index.json`, `code_map/*.json`, `enrichment.json`, `jira_plan.json`, `jira_trace.json`.
- **JSONL (append-only, the ledger):** `telemetry.jsonl`, `decisions.jsonl`. **No SQLite** — files are the state.
- **Markdown:** skills, agent wrappers, prompt files, `v1.md` / `v2.md`, instruction files.

---

## 13. Registry layout

```
registry/
  core/
    skills/                  # the shared skills both tools read
    scripts/                 # python plumbing (clone, ingest, hydrate, merge, gate, scoring, metrics)
    extractors/              # frozen per-language structural extractors
    code_profiles/           # per-repo signal profiles
    adapters/jpmc_adapters/  # the push/auth seam
    profiles/<domain>/       # si_profile + the adapter pack
    templates/<domain>/      # jira_template
  overlays/
    claude/                  # CLAUDE.md + .claude/agents/*.md + prompts + launch
    copilot/                 # copilot-instructions.md + *.agent.md + prompts + launch
  docs/                      # the authoritative design travels with the registry
```

`registry_manifest.yaml` publishes **whole trees** — `core/`, `overlays/`, `docs/` — rather than a
hand-listed file set, so adding an ADR cannot silently fail to ship (D-A22).

On Generate: scaffold = `core/` + `profiles[domain]` + `templates[domain]` + `overlays/<tool>`.
`docs/` publishes to the registry but is **not** hydrated into a run workspace.

---

## 14. Tech stack & environment

- **Frontend:** React + Vite (the config UI).
- **Backend:** FastAPI (local) — filesystem, subprocess, git. Creates the scaffold, writes `UI_INPUT.yaml`, runs hydration.
- **State:** files + the JSONL ledger. (A metrics *store* — Snowflake or otherwise — is deferred; `metrics_scan.py` reads the ledger directly.)
- **Deploy:** local VDI for MVP; AWS deferred.
- **Models:** Claude via JPMC Bedrock (`CLAUDE_CODE_USE_BEDROCK`); Copilot uses its own selection. Skills stay model-neutral.
- **Execution surfaces:** Claude Code as an interactive VSCode-terminal session; Copilot in **VSCode agent mode** (no CLI in the target environment, not Python-launchable). No custom chat UI — the operator authors in the tool's native session after the UI hands off.

---

## 15. MVP scope vs deferred

**In scope:** the five layers; a single domain (`payment_brand`); a single repo; generic ingestion
across four source types; per-source parallel fan-out; the per-artifact index; code clone + map +
both enrichment arms + the human-mediated flag loop; SI v1 → enrichment → v2; the 4-level Jira plan
with G3 and the adapter push; the amended metric set; local VDI; the agnostic build across both
tools; in-session execution (no direct Claude API); files + JSONL ledger.

**Deferred:** cross-repo / multi-system closure; a second-language extractor; multi-domain breadth
and domain onboarding; a metrics store; auto-launch; UI enhancements; sync/freshness and change
detection; semantic retrieval; AWS.

---

*Where to go next: `REQUIREMENTS.md` for what and why · `TECH_SPEC.md` for the contracts ·
`SKILLS_INDEX.md` for the per-skill catalog · `TASK_LIST.md` for what is built and what is next ·
`design/README.md` for the ADRs.*
