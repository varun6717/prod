# Requirements — Agentic Solution Intent / Jira Generation Pipeline

**Project:** PDLC_App_v2 · JPMC Merchant Services · AI Automation
**Document type:** System requirements specification
**Status:** Draft v2 — **amended by ADR-008 (the Solution Intent pivot), 2026-07-31.** v1 derived from `BUILD_OVERVIEW.md` and resolved the ten §18 questions (D1–D10); v2 supersedes parts of that resolution per **D11** below.
**Owner:** V (Varun Munjal)
**Precedes:** tech spec → task lists → UI design.

> ## ⚡ ADR-008 supersession notice — read before relying on any D-block
>
> The pipeline is now **Solution Intent → enrichment → Jira**. BRD and FRD are retired as artifacts;
> the FRD's content moved into Jira **stories** generated from code-grounded enrichment evidence. The
> **tag chain is removed** (vocabulary → adapter `emits` → profile `topics` → `code_map.tags`); routing
> is by **operator-declared disposition + per-artifact index**, and code impact is a **purpose-based
> tier walk**. Full design record: [`docs/design/ADR-008`](design/ADR-008-solution-intent-pivot.md).
>
> | Decision | Status after ADR-008 |
> |---|---|
> | **D1** | ⛔ **Superseded** — `must_capture`/`probe_if_missing` survive as per-section checklists (D11); the topic⊆vocabulary contract dies with tags |
> | **D2** | ⛔ **Superseded** — the SI has a **fixed 18-section contract** (D11); no baseline+profile merge |
> | **D3a** | ⛔ **Superseded** — the FRD is retired (D-A0/D-A15) |
> | **D3b** | 🔧 **Amended** — the template survives; the plan is now **4-level** (initiative/deliverable/epic/story), epic = an SI §8 requirement (D11.6) |
> | **D4** | 🔧 **Amended** — gates re-mapped: G1 = SI v1, G2 = SI v2 (enrichment), G3 absorbs the old G2 checks (D11.5). GF and the soft-gate principle survive unchanged |
> | **D5** | ⛔ **Superseded** — the vocabulary is removed entirely; nothing tags anything (D11.3, D11.4) |
> | **D6a** | 🔧 **Amended** — `code_map.json` loses `tags`, gains purpose provenance + `members[]`, splits into two files (D11.4) |
> | **D6b/c** | ✅ **Survive** — the Flags schema + material threshold are reused by enrichment escalations (D-A9/D-A16) |
> | **D7** | ✅ **Survives** — ingestion stays source-type-keyed and domain-blind; *disposition* is an operator label, not a domain branch |
> | **D8** | ✅ **Survives, extended** — `solution_intent/` (v1/v2/enrichment.json) replaces `BRD.md`/`FRD.md` in the artifact set (D11.2) |
> | **D9** | 🔧 **Amended** — role list rewritten (`solution_intent_*`, `claim_verifier`, `disposition_walkthrough`; `frd_*` retired); prompt files re-pointed (D11.7) |
> | **D10** | ✅ **Survives** — manual start, co-equal tools, VDI validation all unchanged |
>
> FR-cluster impact: **FR-BR-\* and FR-FR-\* are retired**, replaced by **FR-SI-\*** (Solution Intent)
> and **FR-EN-\*** (enrichment) in A3/A4. FR-DC-08/09 (vocabulary) are retired; FR-DC-19/20/21/22/23
> (the vocabulary/profile/adapter onboarding chain) are retired except FR-DC-19 (extractor onboarding,
> which survives). FR-JR-\* amended per D11.6. Retired text below is kept for history — **do not build
> against a ⛔ block.**

---

## 0. Document control

### 0.1 Relationship to the build overview

`BUILD_OVERVIEW.md` is the authoritative architecture record. Its §1–§17 are **locked decisions**; this document does not re-open them. It does two jobs:

1. **Restate the locked architecture as testable requirements** (Part A) — each requirement carries an ID, a MoSCoW priority, and a back-reference to the overview section it formalizes.
2. **Resolve the ten §18 open questions in order** (Part B) — each resolution (`D1`…`D10`) produces a ruling, a rationale grounded in the core principles, and a concrete artifact (schema, contract, or table). Resolutions emit new requirement IDs where they tighten the system.

Where this document **refines** an example skill (e.g. dropping the standalone `topics:` field in favor of implicit topics, D1), the refinement is called out explicitly so the skill files can be updated to match.

### 0.2 Conventions

- **Requirement IDs:** `FR-<area>-NN` (functional), `NFR-NN` (non-functional), `D-N` (design decision). Areas: `XS` cross-cutting/system · `DC` data & context · `SI` Solution Intent · `EN` enrichment · `JR` Jira · `MX` metrics. *(Retired by ADR-008: `BR` BRD · `FR` FRD.)*
- **Priority (MoSCoW):** **M** must (MVP-blocking) · **S** should · **C** could · **W** won't-for-MVP (recorded, deferred).
- **Schemas** are normative where given as YAML/JSON code blocks; field names are part of the contract.
- **"The session"** = the running Claude Code / Copilot agent session that acts as orchestrator. **"The operator"** = the human in VSCode. **"The agent"** = whichever skill-driven role is active.

### 0.3 Scope (mirrors overview §16)

**In scope (post-ADR-008):** five layers; one domain (Payment Brand Implementations); generic per-source-type ingestion with **operator disposition**; per-source parallel fan-out + deterministic merge; manifest + **per-artifact index**; code clone + purpose-based map (signal profile, tier walk) + human-mediated flag loop; **Solution Intent v1 authoring + enrichment (two arms) + disposition walkthrough**; Jira **4-level plan** (initiative/deliverable/epic/story) with G3 sign-off + adapter push; basic metrics; local VDI; agnostic build (Claude Code + Copilot); AI-session-driven orchestration; stage transitions via prompt files.

**Out of scope (deferred):** sync/freshness; change detection & downstream flagging; embeddings retrieval; template profiles (parked, D-A18); multi-domain breadth; **multi-system / cross-repo / cross-language closure (see C5 + D-A19)**; implementation-vs-SI scope-creep detection (post-build, D-A9); AWS + Snowflake; the Claude-only spine; auto-launch; custom context-refresh; automated impact re-runs.

---

# Part A — Requirements spine

## A1. Cross-cutting / system requirements

| ID | Pri | Requirement | Ref |
|----|-----|-------------|-----|
| FR-XS-01 | M | The system MUST hold a **generic core** constant and isolate variation to exactly two seams: a **domain seam** (data adapter / BRD-FRD profiles / Jira template / tag vocabulary) and a **runtime-tool seam** (instruction file / agent wrappers / prompt files / launch). No other axis of variation is permitted. | §3, §12 |
| FR-XS-02 | M | The **UI MUST collect configuration only** and emit a single canonical `UI_INPUT.yaml`. It MUST NOT perform plumbing or judgment. | §3, §5 |
| FR-XS-03 | M | The **scaffolder/bootstrap MUST be deterministic plumbing** (filesystem, subprocess, git, hydration, merge). It MUST NOT make authoring judgments. | §3, §5 |
| FR-XS-04 | M | **The AI session is the orchestrator.** It reads its instruction file and delegates to native subagents. Python scripts are *called by* agents; Python MUST NOT spin up the AI session. **All generation runs in-session via the selected tool (Claude Code or Copilot) reading skill instruction files; no direct Claude API calls in MVP** — a direct-API execution path is a deferred pivot, taken only if the in-session approach proves insufficient. | §3, §11 |
| FR-XS-05 | M | **Durable state MUST live in files** (`UI_INPUT.yaml`, `context_set/`, `index.json`, `code_map.json`, `BRD.md`, `FRD.md`, `jira_plan.json`, `jira_trace.json`). Context windows are ephemeral working memory only; no single session is required to carry the whole pipeline. | §3 |
| FR-XS-06 | M | The system MUST run an identical shared core on **either Claude Code or Copilot**, selected by a UI switch, with only the thin overlay differing. Skills, profiles, templates, Python plumbing, and artifact contracts MUST NOT be duplicated per tool. | §4 |
| FR-XS-07 | M | On Generate, the system MUST assemble `core/` + `profiles[domain]` + `templates[domain]` + `overlays/<tool>` and emit a self-contained instruction file (`CLAUDE.md` *or* `copilot-instructions.md`) from **one canonical template**. No runtime `AGENTS.md` pointer. | §4, §14 |
| FR-XS-08 | M | Each agent role MUST be a **thin tool-specific wrapper** pointing at **one shared skill**; the logic MUST NOT be copied across tools. Interactive roles (`brd_author`, `frd_author`) are `user-invocable`; workers (`source_processor`, `code_impact`, validators) are subagent-only. | §4, §11 |
| FR-XS-09 | M | **Generate-scaffold and run-workflow MUST be two steps** so the scaffold and `UI_INPUT.yaml` can be inspected before execution. | §5 |
| FR-XS-10 | M | Hydration MUST pull version-pinned content from the Bitbucket registry and record the **registry commit SHA in `UI_INPUT.yaml`** for reproducibility. | §5 |
| FR-XS-11 | M | Stage transitions at interactive boundaries MUST be defined **in the instruction file**, surfaced by the agent as the closing line of the prior stage, and **performed by the operator** (Claude `/clear`/new session; Copilot `Ctrl+N`). The agent MUST NOT self-issue them. Each overlay ships per-stage prompt files (`/start-brd`, `/start-frd`, `/start-jira`), plus a **non-interactive Layer-1 kickoff prompt** (`/start-ingest`) that fires the data-&-context fan-out — an orchestrator trigger, not an interactive stage transition (D9 amendment). | §4 |
| FR-XS-12 | W | No custom context-refresh mechanism is built for MVP; the system relies on each tool's auto-compaction plus operator new-thread at boundaries. | §4 |

## A2. Data & context layer (Layer 1)

| ID | Pri | Requirement | Ref |
|----|-----|-------------|-----|
| FR-DC-01 | M | The layer MUST run four stages — source configuration (UI) → generic ingestion connectors (per source-type) → domain-adapter pre-processing → serve — and **fan out per source**. | §6 |
| FR-DC-02 | M | Ingestion connectors MUST be **generic per source-type** (Confluence, SharePoint, Bitbucket) and reused across every domain; the path/URL/auth parameterizes each connector. For code, "ingest" = **git clone** the repo (by SEAL ID) into `repo/`. | §6, §10 |
| FR-DC-03 | M | Pre-processing MUST be the **domain adapter** (the swappable seam): docs → extract→summarize→classify/assess into provenance-tagged `context_set/`; code → build the coarse `code_map.json`. | §6 |
| FR-DC-04 | M | The layer MUST emit `context_set/index.json` — a manifest listing each file with **provenance tags** (source system, path/URL, ingest time, adapter, change-type) and a one-line descriptor — enabling selective read from day one. | §6 |
| FR-DC-05 | M | Fan-out MUST use **one reusable `source_processor` agent definition**, instantiated once per source in parallel; each owns one source end-to-end and writes its slice + manifest entries; a deterministic **`merge_manifest.py`** assembles `index.json`. Split at the source/source-type boundary, never per file. | §6 |
| FR-DC-06 | M | The MVP MUST use **large-context direct feed with selective read** — **no RAG / vector store**. The manifest is always loaded; agents pull only section-relevant files and expand on demand. | §6, §17 |
| FR-DC-07 | W | Sync/freshness, change detection & downstream flagging, and semantic (embeddings) retrieval are deferred. | §6 |

## A3. Solution Intent layer (Layer 2) — *rewritten by ADR-008; replaces the retired FR-BR-\* cluster*

| ID | Pri | Requirement | Ref |
|----|-----|-------------|-----|
| FR-SI-01 | M | The business artifact is a single **`Solution_Intent.md`** at **initiative level**, conforming to the **fixed 18-section contract** (D11.1). The contract holds at both scales — a PBI change (the change *is* the initiative) and a high-level JPMC initiative; only decomposition depth below §7 varies. | D11.1, D-A3/D-A14 |
| FR-SI-02 | M | **v1 is authored code-blind** from the routed sources + frame + discovery. v1 is **frozen at G1**; enrichment produces **v2** per FR-EN-\*. One document, versioned — never a base + overlay. | D-A2 |
| FR-SI-03 | M | Section selection MUST follow the **two-level funnel**: (1) disposition + routing matrix decide *which artifacts* a section sees (deterministic, D11.3); (2) for artifacts over the whole-read budget, the **per-artifact index** decides *which passages* (model judgment driven by `must_capture`, D11.3). The whole-read check applies to the routed **set**, not per file. | D-A13, D-A18 |
| FR-SI-04 | M | Each §8 business requirement carries **title + description + enumerated `assertions[]`** (the checkable units) + a stable ID + a `deliverable:` reference. Assertions are agent-extracted from sources at v1; G1 reviews their fidelity (cite-or-flag at assertion level). | D-A8 |
| FR-SI-05 | M | §7 Deliverables + §8 Requirements + §16 entries carry **stable IDs** forming the trace chain `D → R → impact entry → story → Jira key`. §8→§7 tracing is **load-bearing** (it builds the Jira hierarchy). | D-A14/15 |
| FR-SI-06 | M | **Conditional sections are dispositioned, never absent** — filled, "None identified", or "Not applicable — <reason>" (agent-proposed, operator-confirmed at G1). | D-A10 |
| FR-SI-07 | M | Cite-or-flag is unchanged and gains **claim provenance**: every claim grounds to a source / the frame / an operator answer or is `[TBD — unsourced]`; provenance drives enrichment correction authority (FR-EN-03). Discovery keeps FR-BR-02/03/05 semantics: framing questions up front, per-section `probe_if_missing` gap-fill, revisiting + never re-ask, executive summary (§1) last. | D-A6, D11.1 |
| FR-SI-08 | M | `solution_intent_validator` scores **`0.7 × section_coverage + 0.3 × citation_integrity`** (topic_coverage is retired with tags); hard preconditions at G1: every required section satisfied or dispositioned, §15→§4 and §8→§7 traces intact, flags resolved. | D-A23 |

## A4. Enrichment layer (Layer 3) — *rewritten by ADR-008; replaces the retired FR-FR-\* cluster*

| ID | Pri | Requirement | Ref |
|----|-----|-------------|-----|
| FR-EN-01 | M | Enrichment runs **two arms** over accepted v1 + the code map. **Arm 1 (`code_impact`)**: per assertion, find landing points + walk `depends_on`/`used_by` to closure → §16 derived system impacts ("what did we miss?"). **Arm 2 (`claim_verifier`)**: verdict factual current-state claims → confirmed / contradicted / unverifiable ("what did we get wrong?"). Arm 2 does not walk closure. | D-A8 |
| FR-EN-02 | M | The **verdict population** is factual current-state claims only — business judgment, intent, and future-state statements are skipped; runtime-shaped claims (NFR latency etc.) are **recognised and skipped**, not marked unverifiable. Implicit current-state assumptions inside §8 assertions ARE verdicted. | D-A5, D-A8 |
| FR-EN-03 | M | Correction authority follows **claim provenance**: source-derived contradiction → auto-correct in place with code citation; operator/frame contradiction → escalate; unsourced `[TBD]` the code answers → auto-fill. **Enrichment never deletes** — contradicted claims are rewritten, not removed. §8 requirements are **extend-only** (code cannot contradict intent). §1 regenerates last. | D-A4/6/7 |
| FR-EN-04 | M | Findings that are grounded and unambiguous **auto-apply**; findings that are ambiguous, scope-moving, or would overrule a human **escalate** to one batched operator turn — the **disposition walkthrough** (triage, ordering-dependency aware, resumable; proposes, never decides). A "no code found" gap always escalates (4-way ambiguous: new-build / search miss / other repo / not code). | D-A16/17, D-A9 |
| FR-EN-05 | M | Execution: Arm 1 batches **retrieval per deliverable** (territory resolved once) and reasons **per assertion, independently** (anti-anchoring: share reference material, never conclusions; fan-out safe). Arm 2 clusters by code region. Findings accumulate in **`enrichment.json`** — the permanent audit record (finding, evidence, auto/escalated, operator call + rationale). v1 + `enrichment.json` reconstruct v2. | D-A8, D-A16 |
| FR-EN-06 | M | §16 entries are per **(assertion × code location)**, organised by requirement, machine-consumable; each yields ≥1 story or is explicitly dispositioned. §16 holds **gaps** ("no code exists — must be built") as well as impacts. | D-A15 |
| FR-EN-07 | M | G2 gates v2: score **`0.5 × verdict_completeness + 0.5 × impact_coverage`** *(amended TASK-121: `impact_coverage` = requirements **Arm 1 reached** / total, not "with §16 entries or dispositioned" — the original scored a complete run at 0.417 because a requirement analysed and found to need no change has neither, and it made manufacturing §16 entries the cheapest way to pass; see §9.3)*; hard preconditions: every escalation dispositioned, every correction carries code provenance. D4's soft-gate principle is preserved — scores inform, the operator accepts. | D-A23 |

## A5. Jira epic creation layer (Layer 4)

| ID | Pri | Requirement | Ref |
|----|-----|-------------|-----|
| FR-JR-01 | M | *(amended by ADR-008)* The plan is **four-level**: Initiative ← the SI itself · Deliverable ← §7 · Epic ← one per §8 requirement · **Story ← derived from §16 evidence + §7 non-code work**. Stories exist **only after G2** (they require enrichment evidence); Jira cannot be authored from v1. | D11.6, D-A15 |
| FR-JR-02 | M | *(amended)* Inputs MUST be `jira_template.<domain>.yaml` + accepted **SI v2** + **`enrichment.json`** (the story evidence). | D11.6 |
| FR-JR-03 | M | *(amended)* `jira_author` MUST emit a reviewable **`jira_plan.json`** covering all four levels — **no write to Jira**. **Every story names the code location it changes, or is explicitly flagged new-build / non-code** (deliverable-derived cert/doc/test work). An impact entry may yield stories; a story must trace to a §16 entry or a §7 deliverable. | D-A15 |
| FR-JR-04 | M | *(amended)* `jira_validator` absorbs the old G2 duty: **`0.5 × traceability + 0.5 × testability`** across the hierarchy (every epic → a deliverable; every story → an epic + a §16 entry or §7; every §16 entry → ≥1 story or dispositioned) + required/controls field completeness. | D-A23 |
| FR-JR-05 | M | A **single human gate** MUST combine validation review and push authorization into one sign-off; no epics are created without it. | §9 |
| FR-JR-06 | M | Push MUST go **via the `jpmc_adapters` seam** and write epic keys to `jira_trace.json` for **idempotent re-runs**. | §9 |

## A6. Metrics layer (Layer 5)

| ID | Pri | Requirement | Ref |
|----|-----|-------------|-----|
| FR-MX-01 | M | Metrics MUST be **auto-computed from pipeline telemetry** (`telemetry.emit()` events), not hand-entered. | §2, wireframe |
| FR-MX-02 | M | *(amended by ADR-008)* MVP MUST compute at minimum: M01 $/SI-v1, M02 $/enrichment, M03 avg completion score at acceptance (G1/G2), M04 first-pass acceptance rate, M05 docs/month, M06 v1→v2 cycle time, M07 agent latency p95, M09 §16→story coverage at push, M10 stories/epic, M11 Jira push success rate, **M12 enrichment yield** (corrections + derived impacts + auto-fills per run — the v1→v2 delta, the stage's value story). (M08 upstream-change alerts → **W**.) | D11 |

---

# Part B — Resolved design questions (§18, in order)

Each resolution states the ruling, the rationale, the resulting artifact, and the requirement IDs it emits.

---

## D1 — `must_capture` / `probe_if_missing`: topic level vs section level

> ⛔ **SUPERSEDED by ADR-008 / D11.** `must_capture` + `probe_if_missing` survive as **per-section
> checklists** in the SI profile (D11.1) — a checklist, not a controlled vocabulary. The `topic` field
> and the topic⊆vocabulary contract die with tags; selective read is replaced by the D11.3 funnel.
> Retained for history — do not build against this block.

**Question.** Do the capture criteria and probe questions attach to a section, or to topics within a section?

**Decision.** **Topic level, canonically.** A *section* is a container; a *topic* is the unit that carries exactly one `{must_capture, probe_if_missing}` pair. The validator scores coverage per topic and the agent's probes are gap-fills tied to an unsatisfied topic. `sources` is a **section-level** routing field. The section's `topics` set is **implicit** — it is the distinct set of `requirements[].topic` values — so there is no separate `topics:` field to drift out of sync with the requirements. An atomic section (one thing to capture) is written with a single requirement whose `topic` equals the section `id`.

**Rationale.** A real section captures several distinct things (the worked example's `business_context` captures both `mandate` and `brand_rules`), each needing its own capture test and its own probe; section-level criteria would force one vague probe. Topic-level also gives the validator the per-topic coverage marks the skill already emits (`satisfied by source / frame / operator / open`). Deriving `topics` from the requirements rather than listing it twice enforces the **adapter-emits ↔ profile-topics contract** at one place.

**Resulting artifact — `brd_profile.<domain>.yaml` section schema (normative):**

```yaml
# brd_profile.<domain>.yaml
domain: payment_brand            # must equal UI_INPUT.domain
sections:
  - id: business_context         # section id; matches a baseline id to override, or new to add
    title: Business context       # optional; inherited from baseline if overriding
    position: null                # null = keep baseline order; "last" = pin last; "after:<id>" = insert
    required: true                # section-level: must be satisfied before BRD acceptance gate
    sources: [confluence, sharepoint]   # section-level routing: index.json source filter
    requirements:                 # one entry per topic (topics are implicit = these .topic values)
      - topic: mandate            # MUST be a tag in the domain's adapter vocabulary (see D5)
        must_capture: "The originating brand mandate, its ID, and the compliance deadline"
        probe_if_missing: "Which brand mandate triggers this work, and what's the deadline?"
        required: true            # topic-level: counts toward the section's required coverage
      - topic: brand_rules
        must_capture: "Brand technical/operational rules constraining the implementation"
        probe_if_missing: "Which brand rules apply — message formats, cert requirements?"
        required: false           # captured if available; not blocking
```

**Routing rule (selective read):** for a section, load `index.json` entries where `source ∈ section.sources` **and** `topic ∈ {requirements[].topic}`; expand on demand.

**Emits:** `FR-BR-10 (M)` — the profile schema above is the contract; the `brd_author` skill MUST treat `topics` as implicit from `requirements[].topic` and MUST NOT require a separate `topics:` field. *(Refinement to the example skill: drop any expectation of a standalone `topics:` field; section `sources` stays explicit.)*

---

## D2 — Baseline sections: in the skill vs `brd_baseline.yaml`

> ⛔ **SUPERSEDED by ADR-008 / D11.** The Solution Intent has a **fixed 18-section contract** (D11.1);
> there is no baseline+profile merge, no `position`/`suppress` machinery, and FR-BR-11/14 are retired.
> Retained for history.

**Question.** Should the universal BRD section list live in `brd_author.skill.md`, or as a separate `brd_baseline.yaml`?

**Decision.** **Keep baseline sections inline in `brd_author.skill.md`** (and `frd_author.skill.md`) for MVP — no separate baseline YAML file. The skill already carries the nine universal sections; that stays. The **profile remains the per-domain substance carrier** — it names the section `id`s it touches and supplies each one's `topics` + `must_capture` / `probe_if_missing`, plus any net-new sections. The baseline+profile merge (skill operating-procedure step 1) is unchanged; it simply merges profile entries over the skill's inline baseline list rather than over a hydrated file.

Extracting baseline to `core/brd_baseline.yaml` (same schema as a profile's `sections:` block) is recorded as a **deferred multi-domain refinement** — see FR-BR-11(W) below.

**Rationale.** At one domain the inline list is equally effective. The only payoff of the YAML extraction — a uniform same-schema baseline+profile merge and a fully content-free skill — is multi-domain hygiene, not worth an extra file and load step now. **MVP-honest:** smallest correct thing; heavier machinery visibly parked. Baseline sections are genuinely universal structure (true for every domain), so holding them in the generic skill is not a "domain content in the engine" violation.

**Baseline (as it lives inline in the skill) + merge semantics.** The skill's baseline block carries, per section, `id` / `title` / `order` / `required` (and `position: last` for the executive summary) — but **no `topics` or `must_capture`**, since what-must-be-covered is inherently domain-specific and lives only in the profile:

```text
# inline in brd_author.skill.md — baseline block (skeleton only; no must_capture)
business_context        order 10  required          out_of_scope            order 80  required
scope_objectives        order 20  required          executive_summary       position last  required (draft LAST)
stakeholders            order 30  required
current_state           order 40
requirements            order 50  required
success_metrics         order 60
constraints_assumptions order 70
```

**Merge algorithm (deterministic, by `id`):**
1. Start from the skill's inline baseline sections (skeleton).
2. For each profile section: if `id` matches a baseline section → **deep-merge** (profile supplies that section's `sources` + `requirements`; profile may raise `required`; the engine warns if a profile tries to drop a baseline-required section). If `id` is new → **insert** at `position` (`after:<id>`) or `order`, default append before `executive_summary`.
3. `executive_summary` is pinned last and **drafted last** (FR-BR-02).
4. The merged list is the authoring plan; the skill iterates it.

> **Non-blocking note (deferred) — per-domain section exclusion.** The profile currently has *add / specialize / mark-required* but **no explicit suppress verb**, so a domain cannot drop a baseline section (e.g. Payment Brand omitting "Current state"). Resolution: add an optional `suppress: [<id>]` (or per-section `include: false`) to the profile schema so a domain can omit a baseline section cleanly. This is **deferred and not blocking MVP** — until it exists a domain simply leaves an unneeded section thinly populated. Independent of where the baseline physically lives. Tracked as FR-BR-14 (W).

**Emits:** `FR-BR-11 (W)` — extracting baseline to `core/brd_baseline.yaml` / `core/frd_baseline.yaml` (same schema as the profile `sections:` block, enabling a uniform data-on-data merge) is **deferred** to when multiple domains stress the merge. For MVP the baseline stays inline in the author skills; the profile carries per-section substance and the merge runs against the inline list. `FR-BR-14 (W)` — an optional profile `suppress: [<id>]` / `include: false` verb to let a domain drop a baseline section is **deferred**; non-blocking for MVP.

---

## D3 — FRD profile + Jira template schemas (BRD-profile treatment)

**Question.** Give the FRD profile and the Jira template the same rigor as the BRD profile.

**Decision.** The **FRD profile reuses the BRD profile schema** plus two FRD-specific fields per topic/section; the **Jira template is a structural contract** (not an authoring profile) defining the epic field schema, controls fields, label/component conventions, and FRD→epic mapping + traceability rules.

### D3a — `frd_profile.<domain>.yaml` ~~(normative)~~

> ⛔ **SUPERSEDED by ADR-008.** The FRD is retired (D-A0). Its content moved to Jira **stories**
> generated from enrichment evidence (D-A15); `functional_kind` vocabulary may be reused in story
> typing. `traces_to` survives conceptually as the FR-SI-05 ID chain. Retained for history.

Same `sections → requirements{topic, must_capture, probe_if_missing}` shape as D1, with additions:
- per section: `functional_kind` ∈ `{actor_flow | system_behavior | data_contract | error_state | nfr}` — lets `frd_validator` check testability coverage by kind.
- per topic: `traces_to` — the BRD section/requirement id(s) this functional item derives from (drives the BRD→FRD traceability check, FR-FR-05).

```yaml
# frd_profile.<domain>.yaml
domain: payment_brand
sections:
  - id: routing_behavior
    functional_kind: system_behavior
    sources: [bitbucket, confluence]
    requirements:
      - topic: routing
        traces_to: [scope_objectives, requirements.routing]   # BRD anchors
        must_capture: "Per-brand routing behavior: inputs, decision logic, outputs, idempotency"
        probe_if_missing: "How is a transaction routed to a brand handler today, and what changes?"
        required: true
  - id: error_handling
    functional_kind: error_state
    sources: [bitbucket]
    requirements:
      - topic: error_handling
        traces_to: [requirements.error_handling]
        must_capture: "Failure modes, error codes, retry/fallback, observable signals"
        probe_if_missing: "What are the failure paths and the expected recovery behavior?"
        required: true
```

FRD baseline sections stay **inline in `frd_author.skill.md`** (same MVP decision as D2): `actor_flows`, `system_behaviors`, `data_contracts`, `error_states`, `nfrs`, plus `traceability` (the BRD→FRD map) and `executive_summary` (last). The profile supplies each section's substance; extraction to `core/frd_baseline.yaml` is deferred with the BRD baseline (FR-BR-11 W).

### D3b — `jira_template.<domain>.yaml` (normative)

```yaml
# jira_template.<domain>.yaml
domain: payment_brand
epic:
  required_fields:
    - { key: summary,     type: string,  source: derived }     # from functional area
    - { key: description, type: markdown, source: derived }    # grounded in FRD reqs
    - { key: project_key, type: string,  source: ui_input }    # operator-supplied
    - { key: issue_type,  type: enum,     value: Epic }
  controls_fields:                                             # JPMC controls — required at push
    - { key: seal_id,            type: string,  required: true,  source: ui_input }
    - { key: risk_classification,type: enum,    required: true,  values: [low, medium, high] }
    - { key: control_owner,      type: string,  required: true,  source: ui_input }
    - { key: change_record_ref,  type: string,  required: false }
  labels:
    fixed:   [agentic-pdlc, payment-brand]
    derived: [functional_area]                                 # one label per FRD area
  components:
    map_from: code_map.module                                  # affected modules → Jira components
  traceability:
    epic_must_link: frd_requirement_ids                        # every epic → ≥1 FRD requirement
    coverage_rule: every_frd_area_has_epic                     # every FRD area → ≥1 epic
mapping:
  cluster_by: functional_area        # author groups FRD reqs into epics by area
  one_epic_per: functional_area      # MVP: 1:1 area→epic unless area is oversized
```

**Rationale.** FRD authoring varies by domain the same way BRD does → same engine + profile. Jira does **not** have section-by-section authoring variation; it has a **field/traceability contract** the author conforms to and the validator scores against → a template, not a profile. `traces_to` (FRD) and `epic_must_link` (Jira) make traceability machine-checkable end to end: BRD req → FRD topic → epic.

**Emits:** `FR-FR-06 (M)` FRD profile schema above is the contract; `traces_to` is mandatory on every FRD topic. `FR-JR-07 (M)` the Jira template schema above is the contract; `jira_validator` scores field completeness + bidirectional traceability against it.

---

## D4 — Gate inventory

> 🔧 **AMENDED by ADR-008 / D11.5.** The six-control-point structure, GF, the soft-gate principle
> ("validators inform, never auto-advance") and versioned locks all **stand**. The gates re-map:
> **G1 = SI v1 accepted (code-blind) · G2 = SI v2 accepted (enrichment gate) · G3 = 4-level Jira plan
> review (absorbs the old G2 traceability/testability duty) + push.** The disposition walkthrough
> (D-A17) is the enrichment-stage operator turn, governed by the same GF surface→wait→apply pattern.

**Question.** Enumerate the gates: BRD acceptance, FRD acceptance, Jira push.

**Decision.** Six control points. Three are **human acceptance gates** (G1–G3), one is a **scaffold inspection checkpoint** (G0), and the per-flag operator decision is a **sub-gate inside BRD authoring** (GF). Validator passes are **machine soft-gates** that feed the human gate's decision but do not themselves block.

| ID | Type | Stage / boundary | Precondition | Action | Output / side-effect | Performed by | Reversible |
|----|------|------------------|--------------|--------|----------------------|--------------|-----------|
| **G0** | Checkpoint | After Generate-scaffold, before Run | Scaffold laid + `UI_INPUT.yaml` written | Operator inspects scaffold + config | Proceed to run, or regenerate | Operator | Yes (regenerate) |
| **GF** | Sub-gate (loop) | Inside BRD code-impact section | `code_impact` returned ≥1 flag | Operator decides each flag (surfaced one at a time w/ recommendation) | Sections updated; decision + rationale recorded; conditional `code_impact` re-run (D6) | Operator | Yes (revise) |
| **G1** | Human acceptance | End of BRD layer | `brd_validator` score ≥ threshold **and** all `required` topics satisfied or explicitly waived **and** all flags resolved/recorded | Operator accepts BRD | `BRD.md` locked as **BRD vN**; downstream may begin | Operator | Re-open → vN+1 |
| **G2** | Human acceptance | End of FRD layer | `frd_validator` passes: every BRD requirement traced or marked out-of-scope; testability coverage met | Operator accepts FRD | `FRD.md` locked (pinned to BRD vN) | Operator | Re-open → re-validate |
| **G3** | Human (combined) | Before Jira push | `jira_validator` bidirectional traceability + field/controls completeness; coverage ≥ threshold | Operator accepts coverage **and** authorizes push in one sign-off | Epics pushed via `jpmc_adapters`; keys → `jira_trace.json` | Reviewer | Idempotent re-push (no dup) |

Notes:
- **G1 is the backstop for any missed flag** (§10): acceptance cannot pass with unresolved flags.
- **Validator soft-gates** (`brd_validator`, `frd_validator`, `jira_validator`) run before G1/G2/G3 respectively, returning the score + gap list the human gate consults; they never auto-advance.
- Gate thresholds (the numeric score bars for G1/G2/G3) are **configurable** and default to a single project-level value; the concrete default is set in the tech spec.

**Emits:** `FR-XS-13 (M)` the six control points above are the complete gate inventory; G1/G2/G3 are operator sign-offs (the agent surfaces, never self-advances). `FR-XS-14 (M)` G1/G2 produce versioned locks (BRD vN; FRD pinned to BRD vN); re-opening increments the version.

---

## D5 — First domain + concrete tag vocabulary

> ⛔ **SUPERSEDED by ADR-008 / D11.3–11.4.** The vocabulary is **removed entirely** — nothing tags
> anything on either arm. Doc routing = disposition + per-artifact index; code matching = purpose-based
> tier walk. FR-DC-08/09 retired; §10.1/§10.5 build checks retired. The first-domain choice
> (**Payment Brand**) stands. Retained for history.

**Question.** Pick the first domain and define its concrete tag vocabulary — the adapter-emits ↔ profile-topics ↔ code_map-tags contract.

**Decision.** First domain = **Payment Brand Implementations** (overview §16 recommendation). Its **canonical tag vocabulary** is the single source of truth: every `requirements[].topic` in `brd_profile.payment_brand.yaml` and `frd_profile.payment_brand.yaml`, and every `tags[]` value the domain adapter and `code_map.json` emit for code sections, **MUST** be drawn from this set. The contract is enforced as a build check (D9 parity tooling).

**Resulting artifact — Payment Brand tag vocabulary (normative for the first domain):**

| Tag | Definition | Emitted by (adapter skill) | Consumed by | Code tag? |
|-----|------------|----------------------------|-------------|-----------|
| `mandate` | The originating brand mandate, its ID and compliance deadline | `article_summarize` | BRD business_context | no |
| `brand_rules` | Brand technical/operational rules constraining implementation | `article_summarize` | BRD business_context, FRD system_behavior | no |
| `card_brand` | Which card brand(s) the work concerns | `article_summarize`, `code_map_build` | BRD scope, code routing | yes |
| `routing` | Transaction routing to brand handlers | `article_summarize`, `code_map_build` | BRD/FRD routing_behavior | yes |
| `message_format` | Message/wire formats and field-level changes | `article_summarize`, `code_map_build` | FRD data_contracts | yes |
| `certification` | Brand certification / conformance requirements | `article_summarize` | BRD requirements, FRD nfrs | no |
| `settlement` | Settlement / reconciliation behavior | `code_map_build` | BRD change-impact, FRD system_behavior | yes |
| `transaction_flow` | End-to-end transaction lifecycle steps | `article_summarize`, `code_map_build` | FRD actor_flows | yes |
| `error_handling` | Failure modes, error codes, retry/fallback | `code_map_build` | FRD error_states | yes |
| `interchange_fees` | Interchange / fee schedule impacts | `article_summarize` | BRD requirements | no |
| `reporting` | Reporting / downstream data obligations | `article_summarize` | BRD success_metrics, FRD data_contracts | no |
| `compliance_deadline` | The hard date(s) the work must meet | `article_summarize` | BRD constraints_assumptions | no |

**Contract invariant (machine-checked):**
- `topics(brd_profile) ∪ topics(frd_profile) ⊆ vocabulary` — every profile topic is a known tag.
- `tags(code_map) ⊆ vocabulary` — code-map tags reuse the same vocabulary (so code sections route correctly).
- The domain adapter's emit set **covers** every `required: true` topic — a required topic with no producing adapter is a build error.

> **Forward-compat note (ADR-003, does not reopen D5).** These twelve tags are frozen. The set MAY later be **extended** — never silently redefined — through the human-gated **vocabulary-adequacy** loop (`FR-DC-21`): a deterministic detector flags when the dictionary is too small for the real corpus (silent `tags: []`), a human approves any addition, and the vocabulary is re-versioned (`vocab_sha`). Adding a tag is an operator-ruled amendment, not an automatic or model-driven act. For the MVP slice the twelve stand as authored.

**Rationale.** Selective read works only if the tag a section routes on is the tag the adapter actually stamped on files (§7 "a profile's topics must match the tags the domain adapter emits"). One published vocabulary per domain, checked at build, makes the contract enforceable rather than aspirational.

**Emits:** `FR-DC-08 (M)` each domain MUST publish a canonical tag vocabulary in `core/profiles/`; the adapter, BRD/FRD profiles, and `code_map.json` MUST draw tags only from it. `FR-DC-09 (M)` the build MUST fail if a profile topic is absent from the vocabulary or a required topic has no producing adapter.

---

## D6 — `code_map.json` schema + Flags schema (+ "material" threshold)

**Question.** Pin the `code_map.json` schema and the Flags schema, including types, fields, and the threshold for a "material" scope change.

### D6a — `code_map.json` ~~(normative)~~

> 🔧 **AMENDED by ADR-008 / D11.4.** `tags[]` is **removed**; `purpose` gains provenance
> (`purpose_source: declared | header_prose | inferred | symbols` + a declared-vs-actual verdict);
> `components[]` gains explicit `members[]`; the map **splits into two files**
> (`code_map/components.json` + `code_map/files.json`) so tier 1 never loads file entries wholesale.
> Everything else below — map-don't-copy, both edge directions, per-file `coverage`, `commit_sha`
> caching, reserved `external_calls`/`exposes` — **stands**. D11.4 is normative; this block is context.

```json
{
  "repo": "merchant-routing-svc",
  "seal_id": "SEAL-12345",
  "commit_sha": "9f3c1ab",
  "generated_at": "2026-06-15T14:02:00Z",
  "coverage": "coarse",
  "components": [
    { "module": "routing", "purpose": "Routes a transaction to the correct card-brand handler" }
  ],
  "files": [
    {
      "path": "src/routing/brand_router.java",
      "module": "routing",
      "purpose": "Routes a transaction to the correct card-brand handler",
      "interfaces": ["routeTransaction(txn)", "registerBrand(brand)"],
      "depends_on": ["settlement/reconciler", "config/brand_rules"],
      "used_by": ["api/transaction_controller"],
      "tags": ["routing", "card_brand"],
      "coverage": "coarse"
    }
  ]
}
```

Rules (from `code_map_build.skill.md`, now contractual): map don't copy (reference by `path`, never inline code bodies); capture **both** dependency directions (`depends_on` + `used_by`) for closure; `tags` MUST be from the domain vocabulary (D5); per-file `coverage ∈ {coarse, deep}` flags honesty so deep impact knows where to drill; top-level `coverage` summarizes the map; `commit_sha` makes the cache key (rebuild only on SHA change).

### D6b — Flags schema (normative)

```yaml
flags:
  - type: scope_ripple            # scope_ripple | complexity | constraint | infeasible
    area: settlement/reconciler   # module/component the finding concerns
    finding: "Brand routing is shared with settlement reconciliation"
    implication: "Adding a brand also changes settlement, not just routing"
    options: [include in scope, phase separately, adjust requirement, accept risk]
    recommended_option: "include in scope"   # code_impact recommends; never decides
    severity: material                        # material | advisory  (see threshold below)
    requirement_ref: requirements.routing     # the BRD/FRD requirement whose assumption diverged
```

The **Flags section is required on every `code_impact` run** (emit "no flags" when none) so deviations are actively checked, not noticed by chance.

### D6c — "Material" scope-change threshold (the re-run trigger)

A flag's resolution is **material** — triggering section revision **and** a conditional `code_impact` re-run — when the operator's decision does **any** of:
1. **Changes the impacted code surface** — adds or removes a module/component from the in-scope set, *or*
2. **Changes a requirement's `must_capture`** that the deep pass depended on, *or*
3. **Moves a boundary** in the Scope / Out-of-scope sections.

Otherwise the flag is **advisory**: recorded with its decision, sections updated if needed, **no re-run**.

`code_impact` proposes `severity`; the **operator's decision confirms it** (a flag proposed `advisory` becomes `material` if the operator's chosen option crosses one of the three lines above). **Re-run scope is narrowed:** re-run only over the *changed* code surface (the added/removed modules), not the whole map — consistent with "deep mode reads only the flagged slice."

**Emits:** `FR-DC-10 (M)` `code_map.json` conforms to D6a; `coverage` and `commit_sha` are mandatory; the map is cached and rebuilt only on `commit_sha` change. `FR-BR-12 (M)` `code_impact` MUST emit the Flags section every run per D6b. `FR-BR-13 (M)` the material-flag threshold (D6c) governs whether `brd_author` re-runs `code_impact`; re-runs are scoped to the changed surface only. `FR-DC-13 (M)` code impact in MVP is **single-repo** — one repo cloned by SEAL ID, one `code_map.json`, within-repo dependency closure only. Multi-system discovery and federated cross-repo impact are **deferred** (see C5). The `code_map.json` schema MAY reserve (unpopulated) boundary-integration fields (`external_calls` / `exposes`) so the later cross-repo extension is additive, not a reshape.

**Deterministic extractor + onboarding gate (code_map).** *Terms used below: an **extractor** is the per-language deterministic utility that pulls structure + dependency edges from code (for C: `tree-sitter` + `tree-sitter-c`; see ADR-001); **onboarding** is the one-time, human-gated step that authors or refines an extractor against real code; **freeze** = commit it as a fixed, version-controlled artifact; the **onboarding manifest** records which extractors are frozen (per language) and the content hash each map was built against.*

`FR-DC-14 (M)` The structural extractor is a **frozen, version-controlled artifact**. The model MAY author or refine it **only via a human-gated onboarding step** that emits a reviewable artifact for a human to freeze and commit; it MUST NOT be generated, modified, or self-refined at map-build runtime. *Why: the extractor is the reproducibility/audit anchor of the code map — a runtime-mutable or model-rewritten extractor would let the same repo yield different maps across runs, which is unacceptable for a traceable BRD input.*

`FR-DC-15 (M)` Map-build MUST be **gated by deterministic checks only** — extractor presence (per language) + repo content hash — with **no model involvement in the gate decision**. Branches: no frozen extractor → onboarding; content hash unchanged → reuse cached `code_map.json`; content changed → rebuild changed files only, extractor stays frozen. *Why: keeps the steady-state decision reproducible and model-free.*

`FR-DC-16 (M)` The extractor MUST emit **coverage/failure signals**; coverage below a defined threshold MUST **flag for human re-onboarding**, never auto-modify the tool — a frozen extractor raises its hand, it does not rewrite itself. *Why: separates "code content changed" (→ rebuild map) from "a structural pattern the tool can't handle" (→ human decides whether to re-bless), so the freeze stays stable without going blind to genuinely new idioms.*

`FR-DC-17 (M)` Code-map construction is a **blend**: deterministic tooling is the **primary source of structure + dependency edges** (resolved from the language's import/include/symbol signals via a per-language extractor, selected by deterministic language detection); the model owns **`purpose` and `tags`** only and MUST NOT be the primary source of dependency edges. A **model-only fallback** is permitted for languages with no extractor, but its output MUST be marked lower-coverage. Static-analysis blind spots (function pointers, macros, config-driven wiring) are marked `coverage: coarse` and confirmed in the deep pass. *Why: deterministic tooling is more accurate and cheaper on resolvable edges, the model is required for the semantics tooling can't infer; using each where it is strong beats model-for-everything on both accuracy and cost.*

`FR-DC-19 (W)` **Agent-assisted extractor onboarding (Branch A).** When the gate (FR-DC-15) detects no frozen extractor for a language, a dedicated human-gated skill (working name `extractor_onboard`) MAY read a representative code sample, propose/refine a per-language extractor + its `onboarding_manifest` entry, and emit a **reviewable enhancement artifact** (proposed extractor + coverage estimate + unresolved-pattern report) for a human to freeze and commit (FR-DC-14); it MUST NOT freeze, self-bless, or modify a frozen extractor. **Deferred** — slice-1's only language (C) is onboarded manually (TASK-009/012) and the model-only fallback (FR-DC-17) covers any unonboarded language meanwhile; first exercise is the second language. **Full design + rationale → [`docs/design/ADR-006`](design/ADR-006-extractor-onboarding.md).**

> ⛔ **FR-DC-20/21/22/23 below are RETIRED by ADR-008** — they exist to author and govern the tag
> vocabulary, which is removed. FR-DC-19 (extractor onboarding) **survives**: the per-language
> extractor freeze is unchanged. The per-repo **signal profile** (D11.4) takes over the "how do we
> read this repo" role at onboarding.

`FR-DC-20 (W)` **Agent-assisted vocabulary onboarding (new domain).** When a **new domain** is registered, a dedicated human-gated skill (working name `domain_onboard`) MAY propose its first `vocabulary.<domain>.yaml` from the domain's sample documents + the **untagged** (`purpose`-only) code-map of a sample repo (`tags` cannot inform it — they would be circular), as a **reviewable proposal** (candidate tags with definition, `emitted_by`, code-tag flag, evidence) for a human to edit, approve, and freeze; it MUST NOT commit or self-bless the vocabulary. **Deferred** — `payment_brand`'s vocabulary is frozen by D5, so there is nothing to propose until domain #2. **Full design + rationale → [`docs/design/ADR-003`](design/ADR-003-agent-assisted-vocabulary.md).**

`FR-DC-21 (S)` **Vocabulary adequacy signal (the coverage-floor twin for the *dictionary*).** Alongside the §10.1/§10.5 **containment** check (`usage ⊆ vocabulary`, the build-time hard gate against tag *invention*), the build MUST also surface an **adequacy** signal — whether the frozen vocabulary is *too small* for the artifacts present — since the model cannot invent a tag, so an uncovered concept is otherwise **silent**; it MUST catch both a fully-uncovered file (`tags: []`) and a **partially**-uncovered one (primary tag assigned, a secondary concept untagged). **L1 (in-slice, built — TASK-011/013):** `model_enrich` emits, in the same pass that assigns tags, an `uncovered_concepts[]` observation per file, routed to the ledger (**not** the `code_map` — it has no tag, so routes nothing); a **deterministic aggregation** raises a `VOCAB_GAP_FLAG` for a concept recurring across the net-new delta, with a model-free `untagged_ratio` floor against `adequacy_threshold` underneath. The detector NEVER auto-grows the vocabulary and never blocks the run (advisory runtime flag, not a build gate). **L2 (deferred to port):** the `vocab_gap_assess` model proposal, the human-gated vocabulary **amendment** (an addition; D5's set is never silently redefined), the `vocab_sha` bump, and the re-tag pass. **Full design + rationale → [`docs/design/ADR-003`](design/ADR-003-agent-assisted-vocabulary.md).**

`FR-DC-22 (W)` **Agent-assisted profile integration (gate 3 — the vocabulary→profile seam).** A tag added to a vocabulary is **inert until a profile section consumes it** — *taggable but unconsumed*: it is stamped onto artifacts but, because no `requirements[].topic` references it, no BRD/FRD section ever surfaces it. Closing that **gate 3** (gate 1 *detects*, FR-DC-21 L1; gate 2 *names a tag*, FR-DC-20/21) is today a manual profile edit. A dedicated human-gated skill (working name `profile_onboard`) MAY close it — **surface** the unconsumed tag (the FR-BR-08 *surface → wait → apply* loop), **propose** a target section `id` + drafted `must_capture`/`probe_if_missing` (`sources` from the tag's `emitted_by`; `functional_kind`/`traces_to` for the FRD, D3a), and emit a **reviewable profile diff**; it MUST NOT decide the section, author `must_capture`, or mutate the profile (the change lands as a committed, re-pinned, build-time amendment, §6.6.1). **Deferred** — MVP profiles are hand-authored (TASK-015/016) with no tag to integrate. **Full design (bulk/incremental modes, vocabulary-first order) + rationale → [`docs/design/ADR-004`](design/ADR-004-agent-assisted-profile-integration.md).**

`FR-DC-23 (W)` **Agent-assisted adapter onboarding (the domain pre-processing seam).** The adapter pack (`adapter.yaml` + its pre-processing skills, §6.6.3) is the last domain-seam artifact with **no** authoring aid (the extractor has FR-DC-19, the vocabulary FR-DC-20, the profiles FR-DC-22); today it is authored manually. A dedicated human-gated skill (working name `adapter_onboard`) MAY, given a domain's **frozen** vocabulary + profiles + sample sources, **propose** the pack by **guided conversation** — showing the fixed frame (generic engine + the fixed `code_pipeline → code_map_build`, D7) and designing the variable `docs_pipeline`, with each skill's `emits` **derived from the vocabulary's `emitted_by` column** so `adapter.yaml` cannot drift from the vocabulary by construction (turning the §10.5 no-drift check into a confirmation, and closing the TASK-017 F1+3 drift class). It proposes-never-blesses: references core skills, authors only domain **pack** skills (never `core/skills/`), never mutates a live pack. **Dependency:** the structural step (`pdf_extract`, domain-agnostic) must live in `core/skills/` before the pack exists (tagging skills authored last). **Deferred** — MVP's pack is hand-authored (TASK-017/018/019); first exercise is a new domain at the port. **Full design (modes, onboarding order, open questions) + rationale → [`docs/design/ADR-005`](design/ADR-005-agent-assisted-adapter-onboarding.md).**

---

## D7 — Does ingestion ever vary by domain?

**Question.** Ingestion is currently generic — does any domain need to fork it?

**Decision.** **No. Ingestion connectors are keyed by source-type, never by domain.** What varies by domain is (a) *which* sources the operator configures and (b) *pre-processing* (the domain adapter, Stage 3). Per-instance differences (a specific Confluence space, a specific repo, that instance's auth) are **configuration** (`UI_INPUT.yaml` paths/URLs + `jpmc_adapters` for auth), not domain logic.

**Edge case rule.** If a future domain needs a **source type that does not yet exist** (e.g. a database source), the response is to add **one new generic connector for that source-type to `core/`** — never to specialize an existing connector for a domain. A connector that branches on `domain` is a defect.

**Rationale.** Keeps the domain seam exactly where the architecture puts it (data adapter / profiles / template / vocabulary). Generic ingestion is explicitly shared core (§6, §12). Folding domain logic into connectors would create a second, illegitimate domain seam and break the "fixed pipeline shape" principle.

**Emits:** `FR-DC-11 (M)` ingestion connectors MUST be domain-agnostic and source-type-keyed; they MUST NOT branch on `domain`. New source types are core additions (one generic connector each), not domain forks. `FR-DC-12 (M)` per-instance auth/crawl parameters are sourced from `UI_INPUT.yaml` + `jpmc_adapters`, not embedded in connector logic.

---

## D8 — Re-run / idempotency / error handling; what `UI_INPUT` + the JSONL ledger persist

**Question.** Define re-run, idempotency, and error handling beyond Jira; and the division of persisted state.

**Decision.** **Files are the durable artifact state; an append-only JSONL ledger + small per-run state/decision files are the run/telemetry record; `UI_INPUT.yaml` is the immutable run config. No SQLite for MVP** — it's deferred (see D8a). Every stage is idempotent at a defined granularity, and failures are stage-scoped with file-checkpoint resume.

### D8a — Persistence division

- **`UI_INPUT.yaml`** (file, canonical, **immutable after Generate**): working path; configured sources + URLs/paths; the requirement/project frame; `domain`; `runtime_tool`; pinned registry `commit_sha`; `run_id`. Re-configuring is a **new run** (new `run_id`, new `UI_INPUT.yaml`) — never an in-place edit.
- **Artifact state** (files): `context_set/` + `index.json`, `code_map.json`, `BRD.md`, `FRD.md`, `jira_plan.json`, `jira_trace.json`. These are the durable handoff between stages and sessions ("state lives in files").
- **Run/telemetry record (MVP) — JSONL + per-run files, not a database.** Three append-only/replaceable files, scoped per run unless noted:
  - **`telemetry.jsonl`** (append-only; the source for every Layer-5 metric) — one JSON object per line, schema in D8a-1. May be per-run or a single global file; metrics are computed by scanning.
  - **`run_state.json`** (per run; replaceable) — current stage, per-stage timestamps and status (for resume + cycle-time). Resume can also be inferred from which artifacts exist; `run_state.json` makes it explicit.
  - **`decisions.jsonl`** (per run; append-only audit) — gate decisions (G1–G3: who, when, outcome, version) and flag decisions (GF: flag, option chosen, rationale). Errors are recorded as `error` events in `telemetry.jsonl`.
  None of these store artifact content (that lives in the artifact files above).
- **SQLite — deferred, not MVP.** Adopt a queryable store only when an Insights/metrics dashboard needs interactive aggregate queries over large history, or multi-operator/high-volume concurrency arrives. The JSONL events become the rows — a clean later swap-in. For MVP, scanning JSONL is sufficient and avoids a database dependency on the VDI.

#### D8a-1 — `telemetry.jsonl` event schema (normative)

One JSON object per line. Common envelope on every event:

```json
{ "ts": "2026-06-16T14:02:00Z", "run_id": "r-2026-06-16-001", "domain": "payment_brand", "tool": "copilot", "event": "<event_type>" }
```

Event types and their payload fields (in addition to the envelope):

| `event` | Payload fields | Feeds metric(s) |
|---------|----------------|-----------------|
| `run_started` | `path`, `registry_sha` | M05 docs/month |
| `stage_started` | `stage` | M06 cycle time, M07 latency |
| `stage_completed` | `stage`, `duration_ms` | M06, M07 (p95) |
| `model_call` | `stage`, `model`, `tokens_in`, `tokens_out`, `cost_usd` | M01 $/BRD, M02 $/FRD |
| `validation` | `artifact` (brd/frd/jira), `score` | M03 completion score, M09 coverage |
| `gate_decision` | `gate` (G1/G2/G3), `outcome` (accept/reopen), `actor`, `version` | M04 first-pass acceptance |
| `flag_decision` | `flag_type`, `option`, `severity` | (audit) |
| `jira_push` | `epics`, `success` (bool), `partial` (bool) | M10 epics/FRD, M11 push success |
| `error` | `stage`, `kind`, `message` | (error log) |

Metrics (Part A6) are derived by filtering/aggregating these events; no metric is hand-entered (FR-MX-01).

### D8b — Idempotency & re-run, per stage

| Stage | Idempotency key | Re-run behavior | Failure handling |
|-------|-----------------|-----------------|------------------|
| Clone / ingest | repo `commit_sha`; source URL+ingest-time | Re-clone/pull to pinned SHA; skip if present & matching | Retry; a failed source is marked failed in the manifest, batch continues |
| Pre-process (per source) | source id | Regenerates that source's slice + manifest entries; `merge_manifest.py` reassembles `index.json` | Source-scoped; one source failing does **not** fail the fan-out; partials + gap list surfaced |
| Code map | repo `commit_sha` | Cached; rebuilt only on SHA change | Rebuild on demand; coarse coverage marked honestly |
| BRD authoring | `run_id` + section id | Resumable: re-entered session loads `UI_INPUT` + manifest + existing `BRD.md` and continues (shared-memory rule); accepted → BRD vN | Mid-stage reset persists gathered facts to the draft first (FR-BR-05); ungrounded items `[TBD — unsourced]` |
| FRD authoring | `run_id`; pinned BRD vN | Resumable like BRD; re-opening BRD → FRD re-validates against new vN | Traceability gaps surfaced by `frd_validator`, not silently dropped |
| Jira push | `jira_trace.json` epic keys | Re-push **updates** existing epics by key — never duplicates | Partial push recorded in `jira_trace.json`; idempotent retry of the remainder |

### D8c — Error-handling principles

1. **Stage-scoped failure + file checkpoint resume** — a failure aborts its stage, not the run; resume from the last good file state.
2. **Fan-out isolation** — a single source's failure is contained; the batch proceeds with partials and a recorded gap list; the operator chooses retry-or-proceed.
3. **No silent gaps** — agent-judgment shortfalls surface as `[TBD — unsourced]` or validator gap items, never invented content.
4. **Idempotent external writes** — Jira push is the only external mutation and is guarded by `jira_trace.json`.

**Emits:** `FR-XS-15 (M)` the run/telemetry/decision record is **append-only `telemetry.jsonl` + per-run `run_state.json` / `decisions.jsonl`** (schema in D8a-1); artifact content lives only in files; **SQLite is deferred** (adopt when a metrics dashboard or multi-operator concurrency requires it). `FR-XS-16 (M)` `UI_INPUT.yaml` is immutable post-Generate; re-config = new `run_id`. `FR-XS-17 (M)` every stage is idempotent at the granularity in D8b. `FR-XS-18 (M)` failures are stage-scoped with file-checkpoint resume; fan-out is failure-isolated; external writes are idempotent.

---

## D9 — Overlay authoring: hand-maintain vs generate from one spec

> 🔧 **AMENDED by ADR-008 / D11.7.** The decision (hand-author, parity by manifest) **stands**; the
> **contents** change: roles become `solution_intent_author`/`solution_intent_validator` (← `brd_*`),
> `claim_verifier` + `disposition_walkthrough` are added, `frd_*` retire; `prompt_files` becomes
> `[start-ingest, start-si, start-enrich, start-jira]`. Still 8 roles; §10.2 parity unchanged.

**Question.** Maintain the two tool overlays by hand, or generate both from one workflow spec?

**Decision.** **Hand-maintain the two overlays for MVP, with parity enforced by a shared checklist spec — not a generator.** Concretely:
- **Generated (one piece only):** the **instruction file** (`CLAUDE.md` / `copilot-instructions.md`) is emitted at Generate from **one canonical template** (already required, FR-XS-07).
- **Hand-authored, native, per tool:** the **agent/subagent wrapper files** and **prompt files** — kept idiomatic (frontmatter + location genuinely differ; §4 says don't abstract). The prompt-file set is the three per-stage transitions (`start-brd`, `start-frd`, `start-jira`) **plus `start-ingest`**, the non-interactive Layer-1 kickoff that fires the data-&-context fan-out (it keeps the orchestrator role rather than handing off to an authoring agent; see the amendment note below).
- **Parity tooling (not generation):** a `core/overlay_manifest.yaml` lists every required role (with its shared skill), every prompt file, and the launch method **per tool**. A build check asserts that each overlay implements every manifest role with a wrapper pointing at the correct shared skill, and ships every required prompt file. Author by hand; **verify by spec**.

**Resulting artifact — `core/overlay_manifest.yaml` (normative):**

```yaml
roles:
  - { name: brd_author,       skill: brd_author,       user_invocable: true }
  - { name: frd_author,       skill: frd_author,       user_invocable: true }
  - { name: brd_validator,    skill: brd_validator,    user_invocable: false }
  - { name: frd_validator,    skill: frd_validator,    user_invocable: false }
  - { name: jira_author,      skill: jira_author,      user_invocable: false }
  - { name: jira_validator,   skill: jira_validator,   user_invocable: false }
  - { name: source_processor, skill: source_processor, user_invocable: false }
  - { name: code_impact,      skill: code_impact,      user_invocable: false }
prompt_files: [start-ingest, start-brd, start-frd, start-jira]
overlays:
  claude:  { instruction_file: CLAUDE.md,                 agents_dir: .claude/agents/, launch: terminal_interactive }
  copilot: { instruction_file: copilot-instructions.md,   agents_glob: "*.agent.md",   launch: agent_mode }
parity_check: every_role_and_prompt_present_in_both_overlays
```

**Rationale.** Only two overlays, both thin; a generator would be machinery for little gain and risks a leaky abstraction over genuinely-divergent native syntax — violating **MVP-honest** and §4's "keep each native, don't abstract." The manifest gives the safety of a single source of truth (no role silently missing from one tool) without the cost of generation. Generating the wrappers once the role set stabilizes is a **deferred** option.

**Emits:** `FR-XS-19 (M)` overlay wrappers + prompt files are hand-authored per tool; the instruction file is generated from one template. `FR-XS-20 (M)` `core/overlay_manifest.yaml` is the parity source of truth; the build MUST fail if either overlay omits a listed role or prompt file. `FR-XS-21 (W)` generating wrappers from the manifest is deferred.

**Amendment (V-approved) — `start-ingest` Layer-1 kickoff prompt.** The original prompt-file set (`start-brd`, `start-frd`, `start-jira`) covered only the interactive authoring stages (Layers 2–3); it shipped **no operator-invocable entry point for Layer 1** (Data & context). The run order assumed the orchestrator would self-fire the `source_processor` fan-out, but the surfaced start gesture pointed at `start-brd` — which overrides the orchestrator role and jumps straight to BRD authoring, so Layer 1 was silently skipped (no `context_set/index.json`, no `code_map.json`). Resolution: add **`start-ingest`** as a fourth prompt file — a **non-interactive kickoff** (distinct in kind from the three stage transitions) that keeps the orchestrator role and executes Run order step 1 (fan out `source_processor` per `UI_INPUT.sources[]`, then `merge_manifest.py`). The per-tool **start gesture** (FR-XS-22) is repointed from `start-brd` to `start-ingest`. `prompt_files` becomes `[start-ingest, start-brd, start-frd, start-jira]`; the §10.2 parity check enforces it in both overlays.

---

## D10 — Auto-launch vs manual start; the Copilot/VDI validation task

**Question.** Per tool/environment, auto-launch or manual start? And the Copilot agent-mode + command-execution policy check in the VDI.

**Decision.** **Manual start for both tools in MVP** (auto-launch deferred, §16). Generate lays the scaffold and opens VSCode where allowed; the operator starts the session — interactive Claude Code in the terminal, or Copilot agent mode — manually, using the per-stage prompt files. The UI **MUST surface the exact start gesture per tool** at hand-off.

**Claude Code and Copilot are co-equal MVP paths.** Both run the same instruction-file-driven orchestration (`CLAUDE.md` / `copilot-instructions.md`) delegating to **internal subagents**; neither uses headless mode on the shared path (headless `claude -p` is only the optional, deferred, Claude-only spine — §4, §16). The single genuine tool asymmetry is **Python-drivability** (Claude Code can be launched/driven locally; Copilot cannot), and that asymmetry maps entirely onto features already deferred from MVP — **auto-launch** and the **Claude-only spine**. For the MVP's manual-start, interactive, internal-subagent path the two tools do the same job, so neither is second-class.

**The Copilot/VDI check is an early validation task, not a feasibility gate.** Executing a script from a Copilot agent is a supported capability; the only environment-dependent residue is whether the VDI's **command-approval policy** lets the agent invoke the plumbing scripts (clone/ingest/hydrate/merge) without per-command approval stalling the loop, plus a couple of agent-mode behaviors. Concretely, VS Code Copilot agent mode controls this via a terminal **allow/deny list** (`github.copilot.chat.agent.terminal.allowList` / `denyList`) or a blanket auto-approve (`chat.tools.terminal.autoApprove`) — set in **user** `settings.json` (validation found workspace `.vscode/settings.json` scope unreliable for these keys; see result). The task confirms these are settable (not locked by managed VDI policy) and that an allow-list lets a multi-step loop run cleanly. A hiccup means **tune the allow-list**, not "drop Copilot from MVP." The task is run **early** to de-risk approval friction before the overlay work depends on it.

**Validation-task scope (see companion `COPILOT_VDI_VALIDATION.md`):**
1. Copilot **agent mode** available/enabled in the target VDI; note selectable models.
2. **Custom agents/subagents** (`*.agent.md`) load and are invocable (user-invocable role + subagent-only worker).
3. **Command-approval policy** — agent can run the plumbing scripts; allow-list (`…agent.terminal.allowList`) is settable and lets a multi-step loop proceed without per-command stalls; deny-list reserved for destructive commands.
4. **Parallel fan-out** via coordinator-instruction phrasing actually parallelizes (or runs as isolated collapsible tool calls), not silent serialization.
5. **Stage transition** via `Ctrl+N` + a prompt file (`/start-frd`) yields a clean fresh context that re-orients from `UI_INPUT.yaml` + the prior artifact.

**Validation result (2026-06-16) — PASSED.** Run in the target VDI. Command execution confirmed (a multi-command sequence ran to completion); **parallel fan-out ran with genuine concurrency** (two workers concurrently), exceeding the "isolated tool calls" bar; custom subagents loaded. Critically, **user-scope** auto-approval settings took effect — so the org's Copilot policy does **not** force manual approval, the one scenario that could have hard-blocked the Copilot path. One scoping detail learned: **workspace** `.vscode/settings.json` did **not** take effect for these keys, while **user-scope** settings did — which fixes the allow-list's home as user scope, not the scaffold (FR-XS-26). Remaining check 5 (fresh-context re-orientation) is low priority; persistence is moot under user-scope settings.

**Rationale.** Once orchestration is instruction-driven (not scripted), the MVP path uses internal subagents on both tools (no headless), and Copilot can execute scripts, the basis for ranking Claude above Copilot in MVP largely disappears. What remains is a concrete, fixable environment question — the VDI command-approval policy — which is a validation/config item, not an existential risk. **MVP-honest:** validate the one uncertain thing early; don't pre-emptively demote a co-equal path on an assumption.

**Emits:** `FR-XS-22 (M)` MVP supports **manual start** for both tools; the UI MUST surface the exact per-tool start gesture. `FR-XS-23 (M)` Claude Code and Copilot are **co-equal MVP paths** (instruction-driven orchestration + internal subagents; no headless on the shared path). `FR-XS-24 (M)` the Copilot/VDI command-approval policy was validated early via `COPILOT_VDI_VALIDATION.md` — **PASSED 2026-06-16** (command execution + concurrent fan-out confirmed; org policy not locking approval); a failure would have been resolved by allow-list tuning, and only a confirmed hard block demotes Copilot. `FR-XS-25 (W)` auto-launch (Claude-only first) and the Claude-only deterministic spine are deferred. `FR-XS-26 (M)` the Copilot terminal allow-list lives in **user-scope** settings, not the workspace/scaffold (workspace scope proved unreliable for these keys); in production it MUST be **provisioned centrally** (MDM / managed VS Code profile / VDI bootstrap) and **surfaced by Generate/onboarding as a VDI prerequisite** — the scaffolder does NOT emit it. The `max-autonomy` skill provides local/dev toggling of the same user-scope keys (`maximum` / `balanced` / `safe default` / add-one-command).

---

## D11 — The Solution Intent pivot (ADR-008, V-approved 2026-07-31)

**Question.** Replace BRD/FRD with a single initiative-level Solution Intent enriched against the
codebase; remove the tag chain; route by operator-declared disposition + per-artifact index.

**Decision.** As recorded across **ADR-008 D-A0–D-A24** (the authoritative design record — this block
is the requirement-level distillation). Clean cutover: the BRD/FRD pipeline is retired in place.

### D11.1 — The 18-section contract (normative)

§1 Executive summary *(regenerated last)* · §2 Problem statement · §3 Client need & demand *(cond.)* ·
§4 Business objectives · §5 Personas & actors · §6 High-level use case *(cond.)* · **§7 Deliverables** ·
**§8 Business requirements** *(title + description + `assertions[]`; extend-only under enrichment)* ·
§9 Strategic alignment *(cond.)* · §10 Constraints & design principles · §11 Stakeholders ·
§12 Out of scope *(two-way door)* · §13 Assumptions & risks *(authored checkable)* · §14 Dependencies ·
§15 Success criteria *(every criterion traces to a §4 objective)* · **§16 Derived system impacts**
*(v2-only; per assertion × code location; holds gaps)* · §17 Open questions *(v1-authored)* ·
**§18 Verification summary** *(v2-only; counts, not a ledger)*.

Enrichment touch types per section (Verdict/Correct/Extend/Regenerate/None), the verdict population
rule, and all binding section rules: **D-A3–D-A5, D-A10–D-A11**. `must_capture`/`probe_if_missing`
attach per section as **checklists** (no topic vocabulary).

### D11.2 — Artifacts

`solution_intent/v1.md` (frozen at G1) · `v2.md` (the deliverable) · `enrichment.json` (permanent
audit: every finding, evidence, auto/escalated, disposition + rationale). Replaces `BRD.md`/`FRD.md`
in FR-XS-05's durable-state list. Corrections revise **in place** with inline code provenance;
discoveries append; enrichment never deletes (D-A2, D-A7).

### D11.3 — Input contract: disposition + routing + the per-artifact index

- **Disposition (operator-declared, multi allowed, per D-A12):** Business Requirement · Technical
  Specification · Product Domain Knowledge · Architecture · Prior Artifact *(reference-only — never
  the primary citation for a new requirement)* · **Reference Table** *(TASK-131 — a lookup, not
  evidence; NEVER_ROUTED, so v1 never reads it and enrichment consults it whole)* · Other
  *(background only — never citable)* ·
  **Codebase** *(auto-set for repo URLs)*. Source **type** ≠ disposition: type is where it came from
  (fetching); disposition is what it is for (routing). PDFs always arrive via `sharepoint`.
- **Routing matrix (D-A13, normative):** section × input source, with **Frame** and **Discovery** as
  first-class sources. Discovery is primary for §9/§12/§13 only. `frame` gains free-form `overview`.
- **Per-artifact index (D-A18):** for artifacts over the whole-read budget — `<doc>.md` full extract
  + `<doc>.index.json` (heading + summary + line range per semantic subsection; summaries always
  generated; entry completeness `lines_total == lines_indexed`). Selection = `must_capture` matched
  semantically against index entries; pull the cited line ranges; widen if unsatisfied. No keyword
  maps, no template profiles (parked), no embeddings.

**Emits:** `FR-DC-24 (M)` every configured source carries an operator disposition per the taxonomy
above; ingestion still never branches on domain. `FR-DC-25 (M)` doc processing is domain-agnostic
(extract + index); the per-artifact index conforms to D-A18. `FR-DC-26 (M)` the routing funnel
(disposition ∈ section.classes → set-level whole-read check → index) replaces the D5 selective-read
rule everywhere.

### D11.4 — Code map without tags (amends D6a; detail D-A19–D-A21)

Two files: `code_map/components.json` (modules: `purpose`, `members[]`, cohesion, confidence) +
`code_map/files.json` (per file: `purpose` + `purpose_source: declared | header_prose | inferred |
symbols`, declared-vs-actual `purpose_verdict`, interfaces, edges, coverage). **No `tags` field.**
Impact matching = **three-tier walk**: assertion-in-context vs module purposes → file purposes within
matched modules → source read + closure. Low purpose-confidence **widens** tier 1, never excludes.
Totality: every file in exactly one module (singletons legal; `unclustered` always passes tier 1);
`unanalyzable[]` declared in the coverage report, surfaced at §18.

Per-repo **signal profile** (`code_profiles/<repo>.profile.yaml`, frozen at a human onboarding gate
with the D-A21 stage-distribution report): module-derivation signal priority (include-graph primary),
hub exclusion, cluster size policy, purpose-label aliases (fuzzy), stage A/B/C/C\* resolution config,
frozen overrides (model-proposed, human-approved, stored as data). Cache = `(commit_sha, profile_sha)`
+ per-file content hash; the D6 gate gains a **4th branch** (profile change ⇒ full rebuild).

**Emits:** `FR-DC-27 (M)` the code map conforms to D11.4; the model owns `purpose` text only (module
membership, edges, and clustering are deterministic; approved overrides are data). `FR-DC-28 (M)` each
repo carries a frozen signal profile; repo onboarding presents the stage-distribution gate report.
`FR-DC-29 (M)` map-build caching keys on `(commit_sha, profile_sha)`; purposes cache per file hash.

### D11.5 — Gates + scoring (amends D4)

G0 unchanged · **G1** = SI v1 (score per FR-SI-08) · **G2** = SI v2 (score per FR-EN-07) · **G3** =
4-level Jira plan review (score per FR-JR-04) + operator-confirmed push. GF + D6b/c flags survive as
the escalation vehicle. D4's principles intact: soft gates inform, operators accept, versions lock.

### D11.6 — Jira mapping (amends D3b/FR-JR)

Initiative ← the document · Deliverable ← §7 · Epic ← §8 requirement · Story ← §16 evidence + §7
non-code work, generated **after G2** by `jira_author`. The FRD's content lives here — technical
requirements per epic, grounded in code evidence rather than authored from business text.

### D11.7 — Roles + manifests (amends D9; detail D-A22–D-A23)

Roles (8): `source_processor` · `solution_intent_author` · `solution_intent_validator` · `code_impact`
(Arm 1) · `claim_verifier` (Arm 2, new) · `disposition_walkthrough` (new, interactive) · `jira_author`
· `jira_validator`. Prompts: `[start-ingest, start-si, start-enrich, start-jira]`.

Manifests: `registry_manifest` (tree-based, no doc enumeration) · `overlay_manifest` (rewritten
contents) · `extractor_manifest` (per-language freeze — was `onboarding_manifest.extractors`) ·
`code_profiles/<repo>.profile.yaml` (per-repo) · `cache/code_maps/index.yaml` (mutable build records —
**outside** the frozen registry). `vocabulary.<domain>.yaml`, `adapter.emits`, and profile `topics`
are deleted. Build checks: §10.1/§10.5 retired; §10.2/10.3/10.4 amended; + disposition-class totality
(**§10 = 4 checks**); context/artifact checks per D-A23 families 2–3.

**Build-and-port discipline for the new surface: D-A24** (mocks per source type; `VDI_WIRING.md`
disjointness).

---

# Part C — Non-functional requirements, acceptance & traceability

## C1. Non-functional requirements

| ID | Pri | Requirement | Ref |
|----|-----|-------------|-----|
| NFR-01 | M | **Reproducibility** — a run MUST be reconstructable from `UI_INPUT.yaml` alone (pinned registry SHA + repo SHA + frame + config). | §5, D8 |
| NFR-02 | M | **Portability** — the codebase MUST remain runnable on both tools by changing only the overlay; no tool-specific logic leaks into the shared core. | §4, D9 |
| NFR-03 | M | **Auditability** — every substantive BRD/FRD claim is provenance-cited; every gate and flag decision is recorded (who/when/outcome/rationale) in the per-run decision log (`decisions.jsonl`). | §6, D4, D8 |
| NFR-04 | M | **JPMC environment fit** — runs on local VDI; models via JPMC Bedrock (`CLAUDE_CODE_USE_BEDROCK`); all external integration (auth, Jira write) is isolated to the `jpmc_adapters` seam. | §15 |
| NFR-05 | M | **Selective-read scalability** — authoring MUST stay within context budget at any corpus size via manifest + on-demand expansion (no load-all path, no size threshold). | §8, §17 |
| NFR-06 | S | **Observability** — `telemetry.emit()` events MUST be sufficient to compute all MVP metrics (Part A6) without manual instrumentation. | §2 |
| NFR-07 | M | **Determinism of plumbing** — scaffolding, hydration, fan-in merge, and idempotency keys MUST be deterministic; only authoring/assessment is model-driven. | §3 |
| NFR-08 | S | **Resumability** — an interrupted run MUST resume from last good file state without redoing completed stages (D8b). | D8 |
| NFR-09 | M | **Security of external writes** — the only external mutation is the Jira epic push, gated by G3 and guarded for idempotency by `jira_trace.json`. | §9, D4 |

## C2. Per-layer acceptance criteria

- **Data & context:** every configured source carries a disposition, produces a `context_set/` slice + manifest entries + (over budget) an index; `index.json` merges deterministically; failed sources marked, not silent; `code_map/` exists with `commit_sha` + `profile_sha` + honest coverage report incl. `unanalyzable[]`. (FR-DC-01…07, FR-DC-24…29)
- **Solution Intent v1:** every required section satisfied or dispositioned; every claim cited or `[TBD]`; assertions enumerated per §8 requirement; §15→§4 and §8→§7 traces intact; score ≥ threshold; **G1** → v1 frozen. (FR-SI-*, D11.5)
- **Enrichment / v2:** both arms complete; every assertion verdicted; every escalation dispositioned via the walkthrough; corrections carry code provenance; §16 machine-consumable; §1 regenerated; **G2** → v2 accepted. (FR-EN-*, D11.5)
- **Jira:** 4-level `jira_plan.json` drafted (no write); every story names its code location or is flagged new-build/non-code; hierarchy + controls completeness pass; **G3** single sign-off → push via `jpmc_adapters`; keys in `jira_trace.json`. (FR-JR-*, D11.6)
- **Metrics:** MVP metric set computes from telemetry with no manual entry. (FR-MX-*)

## C3. Contract traceability (the spine that must hold end to end)

```
operator disposition + routing matrix (D11.3)
      │  section ← only its routed classes; passages via index + must_capture
      ▼
SI §7 Deliverable (D-id) ──► §8 Requirement (R-id, assertions[])
      │  Arm 1: per assertion → landing points + closure          Arm 2: claims → verdicts
      ▼
§16 impact entry (assertion × code location) ──► story (names its code location)
      │  epic = R-id · deliverable = D-id · initiative = the SI
      ▼
jira_plan (4-level) ──► (G3, push) jira_trace.json
```
Each arrow is **machine-checkable**: §10.5′ verifies disposition-class totality at build; the
validators verify §15→§4, §8→§7, assertion-verdict completeness, §16↔story coverage, and
story-names-location (D-A23 families). A break anywhere fails the corresponding gate.

## C4. §18 resolution → requirement map

| §18 Q | Decision | Key emitted requirements |
|-------|----------|--------------------------|
| 1 | Topic-level capture; `topics` implicit; `sources` section-level | FR-BR-10 |
| 2 | Baseline stays **inline** in author skills for MVP; profile carries per-section substance; YAML extraction deferred | FR-BR-11 (W) |
| 3 | FRD profile = BRD schema + `traces_to`/`functional_kind`; Jira = structural template | FR-FR-06, FR-JR-07 |
| 4 | Six control points (G0, GF, G1–G3); validators are soft-gates | FR-XS-13, FR-XS-14 |
| 5 | First domain Payment Brand; published tag vocabulary as contract | FR-DC-08, FR-DC-09 |
| 6 | `code_map.json` + Flags schemas; material = surface/requirement/boundary change | FR-DC-10, FR-BR-12, FR-BR-13 |
| 7 | Ingestion never varies by domain; new source types = core connectors | FR-DC-11, FR-DC-12 |
| 8 | Files = artifacts; append-only JSONL ledger + per-run state/decision files (**SQLite deferred**); `UI_INPUT` immutable; per-stage idempotency | FR-XS-15…18 |
| 9 | Hand-author overlays; parity via `overlay_manifest.yaml`; instruction file generated | FR-XS-19…21 |
| 10 | Manual start MVP; Claude Code + Copilot **co-equal**; Copilot/VDI command-approval **validated — PASSED**; allow-list home = user-scope, centrally provisioned | FR-XS-22…26 |
| **11** | **ADR-008 pivot**: SI 18-section contract; disposition + index routing; purpose-based code impact + signal profile; gates re-mapped; 4-level Jira; tag chain + FRD retired | FR-SI-01…08, FR-EN-01…07, FR-DC-24…29, amended FR-JR-01…04 |

## C5. Handed forward to the tech spec (explicitly not decided here)

- Concrete **gate score thresholds** (G1/G2/G3 numeric bars) and the validator scoring formulas.
- The **`jpmc_adapters` interface** signature for the Jira write (and Bedrock wrapper specifics).
- **Registry hydration** mechanics (clone vs sparse fetch; SHA-pinning implementation).
- The **`telemetry.jsonl` event schema is defined here** (D8a-1), not handed forward. A SQLite schema/DDL is **deferred** — not a tech-spec item for MVP; revisit only if a queryable metrics store is later adopted.
- A **direct Claude API execution path** is **deferred** — MVP generation runs entirely in-session (Claude Code / Copilot); pivot to API only if the in-session approach proves insufficient (FR-XS-04).
- **Telemetry event schema** backing the Part A6 metrics.
- The **Copilot/VDI validation task** is **PASSED** (D10, runbook `COPILOT_VDI_VALIDATION.md`) — not an open question. Production allow-list provisioning (central/MDM) is an onboarding/ops task, not a design decision.
- **Multi-system / cross-repo code impact — deferred (FR-DC-13).** MVP is single-repo. The deferred design reuses the existing patterns one tier up ("fractal"): a **system tier** discovers impacted repos from a cached corpus of coarse code_maps, then the existing **code tier** runs within each; cross-repo analysis happens **only at integration seams** (contract-break detection, descend only on break — never an N×N trace). Staged adoption: single-repo [MVP] → explicit multi-repo → registry-filtered discovery. Forward-compat hook: `external_calls`/`exposes` reserved (unpopulated) in `code_map.json` now (FR-DC-13). **Full staged-adoption design + rationale → [`docs/design/ADR-007`](design/ADR-007-cross-repo-code-impact.md).**
- **Code-map extractor + onboarding gate — mechanics handed to tech spec (FR-DC-14…17).** *Decided:* adapt-at-onboarding-then-**freeze** (the model proposes/refines an extractor against real code, a human freezes & commits it, it runs deterministically thereafter) — **not** runtime self-refinement, because a self-modifying extractor breaks map reproducibility. *Decided:* a content change **rebuilds the map** while the extractor **stays frozen**; only a structural pattern the extractor cannot handle **flags for human re-onboarding** — keeping these two cases separate avoids re-onboarding on every commit yet doesn't go blind to genuinely new idioms. *Decided:* a **blend** (deterministic tooling for edges, model for `purpose`/`tags`) over model-for-everything, because tooling is more accurate/cheaper on resolvable edges and the model is needed for semantics. **Tech spec to define:** the **onboarding-manifest schema** (frozen extractors per language + per-repo content hashes); the **3-branch gate algorithm** (FR-DC-15); the **coverage threshold** that triggers re-onboarding (FR-DC-16); the **dispatcher + per-language extractor normalization contract** (detect language → route to extractor → normalize output to the `code_map` schema → model-only fallback when no extractor exists); and the **external-build → VDI-port** handling (the frozen extractor is plumbing that ports unchanged; verify the per-language tooling exists or is provisioned on the VDI; the model-only fallback covers its absence). *Toolchain amendment (ADR-001, 2026-06-19): the C extractor uses **`tree-sitter` + `tree-sitter-c`** (Python deps), not `ctags`/`cscope` — chosen because the AppLocker-locked VDI cannot cleanly provision the PATH binaries while pip runs in-policy, and tree-sitter preserves every static-analysis blind spot (empirically verified against the TASK-005 oracle). The port check becomes "import succeeds in the venv" rather than "binary on PATH."*
- **Agent-assisted extractor onboarding — named, deferred (FR-DC-19).** The Branch-A "no frozen extractor yet" path gets a dedicated human-gated skill (`extractor_onboard`) that proposes/refines an extractor and emits a reviewable artifact for human freeze — not built this slice (C is onboarded manually, TASK-009/012; the model-only fallback covers the interim), preserving the FR-DC-14 freeze invariant. Full design (incl. the Phase-5 contract to define) + rationale → [`docs/design/ADR-006`](design/ADR-006-extractor-onboarding.md).
---

*End of requirements. Next: tech spec → per-tool task lists → UI design.*
