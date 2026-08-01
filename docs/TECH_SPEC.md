# Technical Specification — PDLC_App_v2

> ## ⚡ ADR-008 supersession notice (2026-07-31) — read before relying on any section
>
> The pipeline is now **Solution Intent → enrichment → Jira** (see `REQUIREMENTS.md` D11 and
> [`ADR-008`](design/ADR-008-solution-intent-pivot.md), whose **D-A blocks are normative for the new
> subsystems** until this spec's next consolidation). Per-section disposition:
>
> | Section | Status |
> |---|---|
> | §2 layout | 🔧 `BRD.md`/`FRD.md` → `solution_intent/`; `code_map.json` → `code_map/` (2 files); indexes beside extracts; `code_profiles/` + `cache/` added |
> | §3.1 `UI_INPUT` | 🔧 each source gains `disposition:` (D-A12); `frame` gains `overview:`; `runtime_tool` unchanged |
> | §3.2 manifest | 🔧 `topics`/`change_type` retired; entries gain `disposition` + `index_path`; **routing rule replaced** (see amendment in-section) |
> | §3.3 code map | 🔧 amended per D11.4 (no `tags`; purpose provenance; `members[]`; two files; signal profile) |
> | §3.4–3.6 ledger | ✅ survive; event vocabulary gains enrichment events (`verdict`, `escalation`, `disposition`) |
> | §3.7 artifacts | ⛔ **replaced in-section** — SI v1/v2 + `enrichment.json` |
> | §3.8 jira plan | 🔧 4-level plan (D11.6); `trace.json` unchanged |
> | §4 wiring | 🔧 role table per D11.7 (`solution_intent_*`, `claim_verifier`, `disposition_walkthrough`; `frd_*` retired) |
> | §5 code impact | 🔧 extractor freeze + model fallback + dispatcher **stand**; `onboarding_manifest` splits (D-A22); gate gains 4th branch (profile change); §5.4.1 vocab detector ⛔ retired; §5.6 becomes the 3-tier walk (D-A19) |
> | §6.6 seams | 🔧 `vocabulary.yaml` ⛔ deleted; `adapter.yaml` loses `emits` (doc pipeline is domain-agnostic: extract + index); profiles collapse to the SI section contract + `jira_template` |
> | §7 adapters | ✅ survives unchanged |
> | §8 telemetry | ✅ survives; metric names per FR-MX-02 (amended) |
> | §9 gates | 🔧 **replaced in-section** — G1/G2/G3 re-scored per D-A23 |
> | §10 checks | 🔧 **replaced in-section** — §10.1/§10.5 retired; §10.5′ added; net 4 checks |

**Project:** PDLC_App_v2 · JPMC Merchant Services · AI Automation
**Document type:** Technical design specification
**Status:** Draft v1 — resolves everything `REQUIREMENTS.md` hands forward (kickoff §"What TECH_SPEC.md MUST resolve" + Part C5).
**Owner:** V (Varun Munjal)
**Precedes:** per-tool build task list (Chat B) → UI design.
**Reading order:** `REQUIREMENTS.md` is authoritative for WHAT/WHY (FR/NFR IDs, D1–D10). This document is HOW. It does **not** reopen D1–D10 and treats every requirement *rationale* as a binding design constraint.

---

## 0. How to read this spec

- **Ladder discipline.** Requirements define WHAT/WHY; this defines HOW. Resolved decisions D1–D10 are not reopened. Where a requirement carries a *Why*, this design preserves it — most importantly: the structural extractor is **deterministic and frozen** (never model-rewritten at runtime); the map-build gate is **model-free**; **no SQLite** for MVP; **no direct Claude API** for MVP; ingestion never branches on domain.
- **Two seams only (FR-XS-01).** Everything that varies lives in exactly one of: the **domain seam** (`adapter` / `brd_profile` / `frd_profile` / `jira_template` / tag vocabulary) or the **runtime-tool seam** (instruction file / agent wrappers / prompt files / launch). The per-language **extractor** is a third, *non-domain* variation point that lives inside the code-impact subsystem; it is not a new seam in the architectural sense — it is the one place language (not domain, not tool) varies, and it is governed by the onboarding gate (§5).
- **Normative blocks.** Every YAML/JSON code block below is a contract; field names are part of it. The Chat B task list is built directly from these.
- **Scope (MVP).** Single domain (**Payment Brand Implementations**); **single-repo** code impact; **in-session** execution (Claude Code or Copilot reading skill files — no API); files-as-artifacts + **JSONL ledger** (no SQLite); Jira layer is **epic-only**.

---

## 1. Overview — the five layers and the two seams

```
                          ┌────────────────────────── runtime-tool seam ──────────────────────────┐
                          │  instruction file (CLAUDE.md | copilot-instructions.md)                │
                          │  agent wrappers (.claude/agents/*.md | *.agent.md) · prompt files · launch│
                          └────────────────────────────────────────────────────────────────────────┘
   UI ──► UI_INPUT.yaml ──► [ L1 Data & context ] ──► [ L2 BRD ] ──► [ L3 FRD ] ──► [ L4 Jira epics ] ──► [ L5 Metrics ]
                                  │  fan-out per source            G1            G2              G3 (push)        (derived)
                                  │  + code_map build
                          ┌───────┴──────────── domain seam ───────────────┐
                          │  pre-processing adapter · brd_profile · frd_profile
                          │  jira_template · tag vocabulary                  │
                          └──────────────────────────────────────────────────┘
```

**The five layers (PDLC_App_v2 — the v1 8-layer L0–L8 platform is dead and not referenced):**

1. **Data & context** — configure → ingest (generic per source-type) → pre-process (domain adapter) → serve `context_set/` + `index.json`; code path builds `code_map.json`. Fans out per source.
2. **BRD** — `brd_author` (interactive) + `code_impact` (subagent) + `brd_validator` → `BRD.md`, gated at **G1**.
3. **FRD** — `frd_author` + `frd_validator` → `FRD.md`, gated at **G2**, pinned to BRD vN.
4. **Jira epics** — `jira_author` → `jira_plan.json` + `jira_validator` → single **G3** sign-off → push via `jpmc_adapters` → `jira_trace.json`. Epic-only.
5. **Metrics** — derived by scanning `telemetry.jsonl`. No skill; no hand entry.

**The two seams, concretely.** The **domain seam** is the set of files under `core/profiles/` + `core/templates/` + the domain pre-processing adapter. The **runtime-tool seam** is the two `overlays/<tool>/` trees plus the generated instruction file. The generic core (skills, plumbing, contracts) is identical across both axes. This spec's job is to pin the contracts at those seams so the core stays constant.

---

## 2. Repo / on-disk layout (the artifact contract)

Two distinct trees: the **registry** (version-controlled source, hydrated at Generate) and the **run workspace** (created per run, holds artifacts + ledger).

### 2.1 Registry (`registry/`, Bitbucket, SHA-pinned)

```
registry/
  core/
    skills/                         # *.skill.md — shared engines (both tools read these)
      brd_author.skill.md  frd_author.skill.md
      brd_validator.skill.md  frd_validator.skill.md
      jira_author.skill.md  jira_validator.skill.md
      source_processor.skill.md  code_map_build.skill.md  code_impact_assess.skill.md
      max-autonomy.skill.md
    scripts/                        # python plumbing — called BY agents, never drives the session
      clone.py  ingest_confluence.py  ingest_sharepoint.py  ingest_bitbucket.py
      hydrate.py  merge_manifest.py  validators_score.py  metrics_scan.py
    extractors/                     # FROZEN, version-controlled per-language extractors (§5)
      c_extractor.py  (+ headers/tool shims)   # MVP: C. others added by onboarding.
    adapters/
      jpmc_adapters/                # the push/auth seam (§7) — the only external mutation
        jira.py  auth.py
    profiles/                       # DOMAIN SEAM
      payment_brand/
        brd_profile.payment_brand.yaml
        frd_profile.payment_brand.yaml
        vocabulary.payment_brand.yaml
        adapter/                    # domain pre-processing pack (the swappable domain seam)
          adapter.yaml              # pack manifest: skills + run order + emit-tags (§6.6.3)
          pdf_extract.skill.md  article_summarize.skill.md  confluence_tag.skill.md
    templates/                      # DOMAIN SEAM
      payment_brand/
        jira_template.payment_brand.yaml
    instruction_file.template.md    # ONE canonical template → CLAUDE.md | copilot-instructions.md (§6)
    overlay_manifest.yaml           # parity source of truth (D9)
    onboarding_manifest.yaml        # frozen extractors + per-repo content hashes (§5)
  overlays/                         # RUNTIME-TOOL SEAM (×2, hand-authored, native)
    claude/   { CLAUDE.md template-part, .claude/agents/*.md, prompts/, launch }
    copilot/  { copilot-instructions.md template-part, *.agent.md, prompts/, launch }
```

### 2.2 Run workspace (created at Generate, one per run)

```
<working_path>/
  UI_INPUT.yaml                     # immutable run config (§3.1) — the run's identity
  CLAUDE.md | copilot-instructions.md   # generated instruction file (§6)
  .claude/agents/ | *.agent.md      # hydrated overlay wrappers
  prompts/                          # start-ingest, start-brd, start-frd, start-jira
  core/                             # hydrated shared core (skills, scripts, extractors, profiles[domain], templates[domain])
  repo/                             # git clone of the SEAL-ID repo (code source) — single repo, MVP
  context_set/
    index.json                      # manifest (§3.2)
    <provenance-tagged summary files>
    code_map.json                   # coarse code index (§3.3)
  BRD.md                            # incremental artifact (§3.7)
  FRD.md                            # incremental artifact (§3.7)
  jira_plan.json                    # drafted epic set, pre-push (§3.8)
  jira_trace.json                   # epic keys after push (§3.8) — idempotency record
  ledger/
    telemetry.jsonl                 # append-only events (§3.4, §8)
    run_state.json                  # current stage + per-stage status (§3.5)
    decisions.jsonl                 # gate + flag audit (§3.6)
```

**Invariant (FR-XS-05).** Durable state lives in files. The ledger holds the *run record* (events/state/decisions); the artifacts hold *content*. No artifact content is duplicated into the ledger. No session is required to carry the whole pipeline — any stage re-enters from files (§9 resume).

**SQLite confirmed OUT (FR-XS-15, C5).** The ledger is JSONL + two small per-run JSON files. Metrics scan the JSONL (§8). A queryable store is adopted only when an interactive dashboard or multi-operator concurrency requires it; the JSONL rows become its rows — a clean later swap-in, not an MVP dependency.

---

## 3. Data model & schemas

Each schema is normative. Types are JSON/YAML scalar types unless noted.

### 3.1 `UI_INPUT.yaml` — immutable run config (FR-XS-02, FR-XS-16, NFR-01)

> 🔧 **ADR-008 amendment (normative).** Each `sources[]` entry gains **`disposition:`** — one or more
> of `business_requirement | technical_specification | product_domain_knowledge | architecture |
> prior_artifact | other` (FR-DC-24; `codebase` is auto-set for repo sources, non-editable; multi
> allowed, default one). `frame:` gains **`overview:`** — the free-form Initiative Overview (feeds §1
> identity, seeds §7 deliverables, and is Arm 1's semantic query context). Everything else below
> stands; immutability + `run_id` semantics unchanged.

The UI collects configuration only and emits exactly this. Immutable after Generate; re-configuring is a **new run** (new `run_id`, new file) — never an in-place edit.

```yaml
run_id: r-2026-06-16-001            # unique; names the run
schema_version: 1
working_path: /work/pbi/SEAL-12345-routing
domain: payment_brand               # selects profiles/templates/adapter/vocabulary
runtime_tool: copilot               # claude | copilot  (the UI switch, FR-XS-06)
registry_sha: 7d2e9a1               # pinned registry commit (FR-XS-10, NFR-01)

# project identity / governance metadata — config only; feeds traceability + later Jira controls
project_metadata:
  project_name:     "Discover Brand Routing"   # also seeds frame.title
  application_name: "MerchantRoutingSvc"        # JPMC application; replaces a project-level Seal ID for MVP
  line_of_business: "Merchant Services"
  requestor:        "Varun Munjal"
  requestor_sid:    "vmunjal"                    # user / LDAP id

# requirement / project frame — the operator's authoritative "what we're building now"
frame:
  title: "Add Discover brand routing to merchant settlement"
  intent: "Implement Discover as a routable card brand end-to-end"
  scope_hints: ["routing", "settlement reconciliation touchpoints"]
  stakeholders: ["Payments Eng", "Brand Compliance"]
  key_dates: { compliance_deadline: 2026-09-30 }

# configured sources — per-instance config only; connectors are generic (FR-DC-02/11/12)
sources:
  - type: confluence
    url: "https://confluence.jpmc.net/display/PBI/Discover"
    auth_ref: jpmc_adapters:confluence    # auth resolved at the seam, never inline
  - type: sharepoint
    url: "https://sharepoint.jpmc.net/sites/PBI/Specs"
    auth_ref: jpmc_adapters:sharepoint
  - type: bitbucket                       # code source → git clone into repo/
    seal_id: SEAL-12345
    repo_url: "https://bitbucket.jpmc.net/scm/pbi/merchant-routing-svc.git"
    auth_ref: jpmc_adapters:bitbucket

# Jira push config (consumed only at L4) — controls fields per jira_template
jira:
  project_key: PBIROUTE
  controls:
    seal_id: SEAL-12345
    control_owner: "vmunjal"
    risk_classification: medium           # low | medium | high

# gate thresholds — single project-level default (§9); per-gate override optional
gates:
  score_threshold: 85                     # applies to G1/G2/G3 soft-gate (default)
```

**Reproducibility (NFR-01).** A run is reconstructable from this file alone: `registry_sha` pins the core/profiles; each source pins its instance; the repo is pinned by `commit_sha` recorded in `code_map.json`/`run_state.json` at clone time. `auth_ref` values point at the seam; **no secret ever appears in this file**.

### 3.2 `context_set/index.json` — the manifest (FR-DC-04, FR-DC-05)

Always loaded by authoring agents; selective read routes off it. Assembled deterministically by `merge_manifest.py` from per-source fan-out slices.

```json
{
  "run_id": "r-2026-06-16-001",
  "domain": "payment_brand",
  "generated_at": "2026-06-16T13:40:00Z",
  "files": [
    {
      "path": "context_set/confluence/discover_mandate.md",
      "source": "confluence",
      "url": "https://confluence.jpmc.net/display/PBI/Discover",
      "ingest_ts": "2026-06-16T13:31:02Z",
      "adapter": "article_summarize",
      "topics": ["mandate", "compliance_deadline"],
      "descriptor": "Discover routing mandate; ID DSC-2231; deadline 2026-09-30"
    }
  ],
  "sources_status": [
    { "source": "confluence", "status": "ok",     "files": 4 },
    { "source": "sharepoint", "status": "ok",     "files": 7 },
    { "source": "bitbucket",  "status": "ok",     "note": "code_map.json built" }
  ]
}
```

> 🔧 **ADR-008 amendment (normative — replaces the rule below).** Manifest entries drop `topics` +
> `change_type` (retired with tags) and gain `disposition` (operator-declared, D-A12; multi allowed)
> and `index_path` (the per-artifact index, present when the artifact exceeded the whole-read budget).
>
> **Routing rule (the two-level funnel, FR-SI-03 / FR-DC-26):** for an SI section, (1) load entries
> where `disposition ∈ section.classes` per the D-A13 matrix — deterministic; (2) check the routed
> **set** against the whole-read budget — under: read the extracts whole; over: consult each large
> artifact's `index.json` (heading + summary + line range per subsection, D-A18), select entries by
> matching the section's `must_capture` semantically, pull the cited line ranges from the `.md`
> extract, and widen if `must_capture` remains unsatisfied. Selections are recorded as the citation
> trail. The manifest is always in view; no load-all path.

~~**Routing rule (selective read, FR-BR-04, FR-DC-06).** For a profile section, load entries where `source ∈ section.sources` **and** `topics ∩ section.topics ≠ ∅`; expand on demand for cross-references. `topics[]` values are drawn from the domain vocabulary (§10 build check).~~ A **failed source** is recorded in `sources_status` with `status:"failed"` and a reason — never silently dropped (FR-DC-05, D8c — unchanged).

### 3.3 `context_set/code_map/` — coarse code index (D6a as amended by D11.4, FR-DC-10/13/27)

> 🔧 **ADR-008 amendment (normative — D11.4 / D-A19–D-A22).** The map **splits into two files** so
> tier 1 never loads file entries wholesale: **`code_map/components.json`** (modules — `purpose`,
> explicit `members[]`, `cohesion`, `purpose_confidence`, + the signal-profile ref `profile_sha`, the
> coverage report incl. `unanalyzable[]`, and `duplicates_requiring_disposition[]`) and
> **`code_map/files.json`** (per file — `purpose`, **`purpose_source: declared | header_prose |
> inferred | symbols`**, `purpose_verdict` (declared-vs-actual, `diverged` ⇒ `purpose_actual`),
> `interfaces`, `depends_on`/`used_by`, `coverage`). **`tags[]` is deleted.** Module assignment is
> deterministic per the repo's frozen signal profile (`code_profiles/<repo>.profile.yaml` — include-graph
> primary, hub exclusion, size policy, frozen overrides); the model writes **purpose text only**.
> Totality: every file in exactly one module; `unclustered` always passes tier 1. Cache key becomes
> **`(commit_sha, profile_sha)`** + per-file content hash (FR-DC-29). Everything else in the block
> below stands (map-don't-copy, both edge directions, per-file coverage, reserved
> `external_calls`/`exposes`).

Finalizes D6a. Adds the reserved cross-repo fields (unpopulated in MVP) and the extractor coverage report.

```json
{
  "repo": "merchant-routing-svc",
  "seal_id": "SEAL-12345",
  "commit_sha": "9f3c1ab",
  "generated_at": "2026-06-16T13:38:00Z",
  "coverage": "coarse",
  "language": "c",
  "built_with_extractor_sha": "4a91c0f",
  "components": [
    { "module": "routing", "purpose": "Routes a transaction to the correct card-brand handler" }
  ],
  "files": [
    {
      "path": "src/routing/brand_router.c",
      "module": "routing",
      "purpose": "Routes a transaction to the correct card-brand handler",
      "interfaces": ["route_transaction(txn)", "register_brand(brand)"],
      "depends_on": ["settlement/reconciler", "config/brand_rules"],
      "used_by": ["api/transaction_controller"],
      "tags": ["routing", "card_brand"],
      "coverage": "coarse",
      "external_calls": [],          // RESERVED (FR-DC-13) — cross-repo, unpopulated in MVP
      "exposes": []                  // RESERVED (FR-DC-13) — integration seam, unpopulated in MVP
    }
  ],
  "coverage_report": {               // emitted by the extractor every build (§5, FR-DC-16)
    "files_seen": 120,
    "files_extracted": 110,
    "files_fallback": 6,
    "files_unresolved": 4,
    "coverage": 0.917,
    "unresolved_patterns": ["function-pointer dispatch in dispatch.c"]
  }
}
```

**Contract (D6a rules, now normative).** Map don't copy (reference by `path`, never inline code bodies); both dependency directions (`depends_on` + `used_by`) for closure; `tags ⊆ domain vocabulary` (§10); per-file `coverage ∈ {coarse, deep}`; top-level `coverage` summarizes; `commit_sha` is the **whole-map cache key** (§5 gate). `language` + `built_with_extractor_sha` tie the map to the frozen extractor that produced it. `external_calls`/`exposes` exist now so the deferred cross-repo extension (C5) is additive, not a reshape.

### 3.4 `ledger/telemetry.jsonl` — event stream (D8a-1, finalized — §8)

One JSON object per line. Common envelope on every event; event-specific payload appended. Full event table and metric mapping in §8.

```json
{ "ts": "2026-06-16T14:02:00Z", "run_id": "r-2026-06-16-001", "domain": "payment_brand", "tool": "copilot", "event": "stage_completed", "stage": "brd_authoring", "duration_ms": 412000 }
```

### 3.5 `ledger/run_state.json` — current state (D8a, NFR-08)

Per run; replaceable (last-write-wins). Makes resume explicit (it can also be inferred from which artifacts exist).

```json
{
  "run_id": "r-2026-06-16-001",
  "repo_commit_sha": "9f3c1ab",
  "current_stage": "frd_authoring",
  "stages": {
    "ingest":         { "status": "done",    "started": "…", "completed": "…" },
    "code_map":       { "status": "done",    "started": "…", "completed": "…" },
    "brd_authoring":  { "status": "done",    "started": "…", "completed": "…", "version": 1 },
    "frd_authoring":  { "status": "running", "started": "…" }
  }
}
```

`status ∈ {pending, running, done, failed}`. On resume, the session reads this + the existing artifacts and continues from `current_stage` without redoing `done` stages (§9).

### 3.6 `ledger/decisions.jsonl` — gate + flag audit (NFR-03)

Per run; append-only. Every gate and flag decision: who, when, outcome, rationale.

```json
{ "ts": "…", "kind": "gate",  "gate": "G1", "outcome": "accept", "actor": "vmunjal", "version": 1 }
{ "ts": "…", "kind": "flag",  "flag_type": "scope_ripple", "area": "settlement/reconciler", "option": "include in scope", "severity": "material", "rationale": "Settlement shares the brand table; in-scope per ops.", "actor": "vmunjal" }
{ "ts": "…", "kind": "reonboard_flag", "language": "c", "coverage": 0.71, "floor": 0.80, "decision": "re-onboard", "actor": "vmunjal" }
{ "ts": "…", "kind": "vocab_gap_flag", "arm": "code", "concept": "tokenization", "evidence": ["payment/tokenize.c", "payment/vault.c"], "decision": "amend-vocab", "actor": "vmunjal" }
{ "ts": "…", "kind": "vocab_gap_flag", "arm": "code", "untagged_ratio": 0.34, "threshold": 0.20, "decision": "accept-as-is", "actor": "vmunjal" }
```

`vocab_gap_flag` (ADR-003 / FR-DC-21, §5.4.1) records the vocabulary-adequacy detector raising its hand. Two shapes, one record kind: the **primary** signal names a recurring `concept` the vocabulary lacks (with `evidence` files) — caught from the model's `uncovered_concepts`, so it covers a file that was *partially* tagged as well as one fully untagged; the **floor** signal records that `untagged_ratio` for an `arm` (`code` | `docs`) crossed `adequacy_threshold` (the deterministic, model-free safety net). Both carry the operator's disposition (`amend-vocab` | `accept-as-is`). It is the dictionary's twin of `reonboard_flag`; like it, the artifact is **never** auto-modified — a human decides.

### 3.7 `solution_intent/` — the business artifact (FR-SI-\*, FR-EN-\*) *(replaces `BRD.md`/`FRD.md` per ADR-008)*

```
solution_intent/
  v1.md              # code-blind draft — FROZEN at G1, immutable thereafter
  v2.md              # the deliverable — v1 + enrichment applied per the D-A2 placement rules
  enrichment.json    # permanent audit: every finding, its evidence, auto-applied|escalated,
                     # operator disposition + rationale; v1 + this file reconstruct v2
```

- **`v1.md` / `v2.md`** — one `##` per section of the **fixed 18-section contract** (D11.1), in order;
  §1 executive summary authored/regenerated **last**. Every substantive claim carries `[src: <provenance>]`
  / `[frame]` / `[operator]` or `[TBD — unsourced]` (FR-SI-07); v2 in-place corrections carry
  `[code: <path:symbol>]` provenance; unverifiable current-state claims carry `[unverified against code]`.
  Per section, the machine-readable coverage footer keys on **`must_capture` items** (not topics):
  ```
  <!-- coverage: {what_is_broken_today: source, what_it_costs: source, why_now: operator} -->
  ```
- **§7/§8/§16 carry stable IDs** (`D1…`, `R1…` + `deliverable:`, entries keyed `R-id × code location`) —
  the FR-SI-05 trace chain. §8 requirements enumerate `assertions:` (a./b./c.…) per FR-SI-04.
- **Conditional sections** render filled, `None identified`, or `Not applicable — <reason>` (FR-SI-06).
- **`enrichment.json`** — per finding: `{id, arm, type, assertion_ref|claim_ref, evidence[],
  verdict?, action: auto_applied|escalated, disposition?, rationale?, section_target}`. Escalated
  scope-moving findings reuse the D6b Flags schema. Schema detail: D-A16.

### 3.8 `jira_plan.json` / `jira_trace.json` — plan + push record (FR-JR-\* as amended, D11.6)

> 🔧 **ADR-008 amendment.** The plan is **four-level**: `initiative` (from the SI) → `deliverables[]`
> (D-ids) → `epics[]` (R-ids) → `stories[]`. Each story: `{epic: R-id, evidence: §16 entry id | "D-id
> non-code", code_location | flag: new_build|non_code, acceptance_criteria}`. Authored **after G2**
> from v2 + `enrichment.json`. `jira_trace.json` semantics unchanged (idempotent keys, now at all
> pushed levels).

```json
// jira_plan.json — drafted by jira_author; NO write to Jira
{
  "run_id": "r-2026-06-16-001",
  "project_key": "PBIROUTE",
  "epics": [
    {
      "local_id": "E1",                         // stable idempotency anchor (→ jira_trace key)
      "summary": "Discover brand routing",
      "description": "…grounded in FRD requirements…",
      "issue_type": "Epic",
      "functional_area": "routing_behavior",
      "frd_requirement_ids": ["routing_behavior.routing", "error_handling.error_handling"],
      "controls": { "seal_id": "SEAL-12345", "risk_classification": "medium", "control_owner": "vmunjal" },
      "labels": ["agentic-pdlc", "payment-brand", "routing_behavior"],
      "components": ["routing"]                  // mapped from code_map.module
    }
  ]
}
```

```json
// jira_trace.json — written after G3 push; idempotency record (FR-JR-06, NFR-09)
{
  "run_id": "r-2026-06-16-001",
  "epics": {
    "E1": { "key": "PBIROUTE-417", "url": "https://jira…/PBIROUTE-417", "action": "created", "pushed_ts": "…" }
  }
}
```

**Idempotency.** `local_id` is the stable key. Re-push: if `local_id` already maps to a `key` in `jira_trace.json` → **update** that epic; else **create**. Never duplicates (§7).

---

## 4. Skill ↔ agent ↔ profile wiring (per layer)

> 🔧 **ADR-008 amendment (D11.7 — normative role list, 8 roles).** `source_processor` (unchanged) ·
> `solution_intent_author` ← `brd_author` (interactive) · `solution_intent_validator` ← `brd_validator`
> · `code_impact` (Arm 1; §5.6) · **`claim_verifier`** (Arm 2, new — extracts current-state claims from
> verdict-eligible sections + implicit assumptions from §8 assertions, clusters by code region,
> verdicts; never walks closure) · **`disposition_walkthrough`** (new, interactive — §9.5) ·
> `jira_author` · `jira_validator` (§9.4). **`frd_author`/`frd_validator` retired.** Arms 1+2 stay
> separate roles for independent re-runnability (a conditional re-run touches one arm's work, not
> both). Prompts: `[start-ingest, start-si, start-enrich, start-jira]`. The wiring table below is
> superseded where it references brd/frd roles.

**Skill vs agent — the distinction this table makes explicit (FR-XS-08, BUILD_OVERVIEW §11).** A **skill** is the shared instruction module (`core/skills/<name>.skill.md`) — the substance: procedure, rules, sections. It is authored once and is tool-agnostic. An **agent** is the *actor that executes a skill*: it loads the skill and runs it against runtime input. The two usually share a name (`brd_author` the agent runs `brd_author.skill.md`) but are different artifacts in different places — the agent is realized as a **thin per-tool wrapper** in each overlay (`.claude/agents/brd_author.md` or `brd_author.agent.md`) whose body just points at the shared skill. Not every row is an agent-runs-skill pair: **plumbing** (`merge_manifest`, `metrics`) is a Python script with **no skill and no agent of its own**, and **`jpmc_adapters`** is an adapter **module** called at the push step — also not a skill.

**Executor taxonomy (the "Agent (executor)" column).** Four ways work runs:
- **orchestrator** — the tool's session reading the instruction file (`CLAUDE.md`/`copilot-instructions.md`); it fires the run order and delegates. One per run.
- **own session (user-invocable)** — an interactive agent the operator talks to directly in its own window (`brd_author`, `frd_author`), started via a prompt file (`/start-brd`).
- **subagent** — an isolated context window the orchestrator or an authoring agent spins up; autonomous, returns a summary (`source_processor`, `code_impact`, the validators, `code_map_build`).
- **script (no agent)** — deterministic Python called *by* an agent; loads no skill (`merge_manifest`, `metrics_scan`, `jpmc_adapters`).

| Layer | Agent (executor — how it runs) | Skill / module it runs | Consumes | Produces / delegates | Domain input | Gate |
|-------|-------------------------------|------------------------|----------|----------------------|--------------|------|
| 1 | `source_processor` **subagent** (×N parallel) invokes the connector | ingestion connector `core/scripts/ingest_<type>.py` (code → `clone.py`) — source-type keyed | `UI_INPUT.sources` + auth (seam) | raw content; code → `git clone` to `repo/` | — (source-type keyed) | — |
| 1 | `source_processor` **subagent** runs the domain adapter (code → hands to `code_map_build`) | domain adapter skills `profiles/<domain>/adapter/*.skill.md` (`pdf_extract`, `article_summarize`; `confluence_tag` for KB pages) | raw content | `context_set/` slices + manifest entries | `profiles/<domain>/adapter` (**domain seam**) | — |
| 1 | `source_processor` — **worker subagent**, spawned by orchestrator | `core/skills/source_processor.skill.md` | one source | that source's slice + manifest entries | — | — |
| 1 | `code_map_build` — **worker subagent** (spawned for the code source) | `core/skills/code_map_build.skill.md`; *calls* the **frozen extractor** `core/extractors/<lang>_extractor.py` (a tool, not a skill) | `repo/` + frozen extractor | `code_map.json` (cached by `commit_sha`) | vocabulary (tags) | — |
| 1 | **script (no agent)** — called by orchestrator after fan-out | `core/scripts/merge_manifest.py` | per-source entries | `index.json` (deterministic fan-in) | — | — |
| 2 | `brd_author` — **own interactive session** (user-invocable; `/start-brd`) | `core/skills/brd_author.skill.md` | `UI_INPUT` · `brd_profile` · `index.json` · `code_map.json` | `BRD.md`; **delegates** `code_impact` subagent | `brd_profile.<domain>.yaml` | G1 |
| 2 | `code_impact` — **worker subagent**, spun up by `brd_author` | `core/skills/code_impact_assess.skill.md` | requirement · `code_map.json` · `repo/` | impact summary + **required Flags** (returns to caller) | vocabulary | (feeds GF) |
| 2 | `brd_validator` — **validator subagent** | `core/skills/brd_validator.skill.md` | `BRD.md` · profile · sources · code surface | score + section gaps | `brd_profile` | feeds G1 |
| 3 | `frd_author` — **own interactive session** (user-invocable; `/start-frd`) | `core/skills/frd_author.skill.md` | accepted `BRD.md` · `frd_profile` · `context_set/` | `FRD.md` (detailed code impact carried forward) | `frd_profile.<domain>.yaml` | G2 |
| 3 | `frd_validator` — **validator subagent** | `core/skills/frd_validator.skill.md` | `FRD.md` · `BRD.md` | score + BRD→FRD traceability + testability | `frd_profile` | feeds G2 |
| 4 | `jira_author` — **subagent or own session** | `core/skills/jira_author.skill.md` | `jira_template` · accepted `FRD.md` · `BRD.md` | `jira_plan.json` (no write) | `jira_template.<domain>.yaml` | — |
| 4 | `jira_validator` — **validator subagent** | `core/skills/jira_validator.skill.md` | `jira_plan.json` · `FRD.md` | bidirectional traceability + field completeness + coverage | `jira_template` | feeds G3 |
| 4 | **module (no agent)** — called at the push step after G3 | `core/adapters/jpmc_adapters/{jira,auth}.py` (push/auth **seam**, §7) | approved `jira_plan.json` | pushed epics + `jira_trace.json` | — | G3 push |
| 5 | **script (no agent)** — run on demand | `core/scripts/metrics_scan.py` | `telemetry.jsonl` | MVP metric set | — | — |
| rt | `max-autonomy` — **user-invocable utility**, applied locally by the active agent | `core/skills/max-autonomy.skill.md` | VS Code **user** `settings.json` | updated user settings (+ backup) | — | — |
| all | **orchestrator** — the tool **session** reading the instruction file | the generated instruction file (`CLAUDE.md` / `copilot-instructions.md`), §6 — *not* a `core/skills/` file | `UI_INPUT.yaml` + manifest | fires run order; delegates to every subagent above | — | drives G0–G3 |

Read a row as: *this agent loads/runs this skill-or-module.* Where the agent column says **script (no agent)** or **module (no agent)**, the orchestrator (or the named caller) invokes it directly as deterministic plumbing — there is no skill and no wrapper.

**Wrapper parity** (every agent realized in both overlays, pointing at the correct shared skill) is enforced by the build check in §10.2 against `overlay_manifest.yaml`. Plumbing scripts and `jpmc_adapters` are **not** in the parity manifest — they are shared core with no per-tool wrapper.

---

## 5. Code-impact subsystem (the deterministic extractor + onboarding gate)

This is the newest and densest block (FR-DC-14…17, handed forward in C5). It resolves: the **onboarding-manifest schema**, the **3-branch gate algorithm**, the **coverage threshold**, the **dispatcher + normalization contract**, and **external-build → VDI-port** handling. It preserves the binding *Why*: the extractor is the reproducibility anchor — **deterministic, frozen, never model-rewritten at runtime; the gate is model-free**.

### 5.1 Terms (from REQUIREMENTS D6 note)

- **Extractor** — the per-language deterministic utility that pulls structure + dependency edges from code (for C: `tree-sitter` + `tree-sitter-c`, per ADR-001), wrapped by a committed `extractors/<lang>_extractor.py`.
- **Onboarding** — the one-time, human-gated step that authors/refines an extractor against real code.
- **Freeze** — commit it as a fixed, version-controlled artifact (recorded by `extractor_sha`).
- **Onboarding manifest** — records which extractors are frozen (per language) and the content hash each map was built against (per repo).

### 5.2 `core/onboarding_manifest.yaml` ~~(normative)~~

> 🔧 **ADR-008 amendment (D-A22): this file SPLITS.** `extractors[]` → **`extractor_manifest.yaml`**
> (per-language freeze — unchanged in content; FR-DC-14 stands). `repos[]` → **`cache/code_maps/
> index.yaml`** (mutable build records, **outside** the frozen registry — it was mutable state inside
> a SHA-pinned artifact). `adequacy_threshold` + `vocab_sha` ⛔ die with tags; the quality question
> they answered is now the **onboarding gate's stage-distribution report** (D-A21) + per-module
> `purpose_confidence`. New sibling: **`code_profiles/<repo>.profile.yaml`** (per-repo signal profile,
> frozen at the gate — schema per D-A20/D-A21).

```yaml
schema_version: 1
extractors:
  - language: c
    extractor: core/extractors/c_extractor.py
    extractor_sha: 4a91c0f                 # content hash of the frozen extractor file
    tools_required: [tree-sitter==0.25.2, tree-sitter-c==0.24.2]   # pip deps imported in-venv (ADR-001); not PATH binaries
    file_globs: ["*.c", "*.h"]
    coverage_floor: 0.80                   # below this on a repo build → re-onboarding flag (FR-DC-16)
    frozen_at: 2026-06-10T00:00:00Z
    frozen_by: vmunjal
adequacy_threshold: 0.20                    # untagged_ratio above this → VOCAB_GAP_FLAG (ADR-003 / FR-DC-21, §5.4)
vocab_sha: d5frozen                         # version of the domain vocabulary the maps below were tagged under
                                            #   (reserved now per ADR-003; constant while the single domain's
                                            #   vocabulary is frozen — a future human-gated amendment bumps it)
repos:
  - repo: merchant-routing-svc
    seal_id: SEAL-12345
    language: c
    content_hash: 9f3c1ab                  # == repo commit_sha the cached map was built against
    built_with_extractor_sha: 4a91c0f
    built_with_vocab_sha: d5frozen         # vocabulary version the map's tags were assigned under (ADR-003);
                                           #   a mismatch invalidates the cache → re-tag pass (§5.3 Branch B)
    code_map_path: context_set/code_map.json
    last_built: 2026-06-15T14:02:00Z
```

`content_hash` is the repo **git commit_sha** (matches D6a/D8b's cache key). Incremental rebuild (below) derives the changed-file set by diffing commits, so a finer per-file hash is not stored — the commit pair is sufficient and deterministic.

### 5.3 The ~~3~~ **4**-branch gate algorithm (deterministic, model-free — FR-DC-15 as amended)

> 🔧 **ADR-008 amendment.** A **4th branch** joins the three below: **`profile_sha` changed ⇒ full
> rebuild** — a signal-profile change can move every module boundary, so profile change invalidates
> wholesale while commit change invalidates selectively. Branch 3 (incremental) recomputes structure +
> clustering globally (cheap, deterministic; clustering is global, so "affected modules" is wider than
> "modules containing changed files") and re-runs model purposes **only** for changed file hashes;
> module purposes re-synthesise only for affected modules.

Inputs are **only** deterministic signals: language detection, extractor presence, content hash, extractor sha. **No model participates in the branch decision.**

```
GATE(repo @ commit C_new, manifest):
  L  = detect_language(repo)                      # deterministic: file-glob histogram + build-manifest signals
  E  = manifest.extractor_for(L)                  # may be None
  R  = manifest.repo_for(repo, seal_id)           # may be None

  # ── BRANCH A — no frozen extractor for L → ONBOARD (human-gated)
  if E is None:
      request_onboarding(L)                        # model proposes/refines extractor vs real code →
                                                   #   reviewable artifact → human freezes+commits →
                                                   #   manifest.extractors gains an entry (new extractor_sha)
      # until onboarded: build via MODEL-ONLY FALLBACK, mark coverage:coarse + lower (FR-DC-17)

  # ── BRANCH B — cache hit → REUSE
  elif R and R.content_hash == C_new and R.built_with_extractor_sha == E.extractor_sha \
            and R.built_with_vocab_sha == manifest.vocab_sha:        # vocab version part of the cache key (ADR-003)
      return load(R.code_map_path)                 # no rebuild

  # ── BRANCH C — new repo OR content changed OR extractor re-blessed OR vocabulary amended → REBUILD/RE-TAG
  else:
      if R and R.content_hash == C_new and R.built_with_extractor_sha == E.extractor_sha:
          retag_only(R.code_map_path, vocab_sha=manifest.vocab_sha)  # vocab-only change: re-tag, structure reused
          map = load(R.code_map_path)
      elif R is None or R.built_with_extractor_sha != E.extractor_sha:
          changed = ALL_FILES(repo, E.file_globs)  # full build
          map = build(repo, changed, extractor=E)   # FROZEN E; model only for purpose/tags (§5.5)
      else:
          changed = git_diff_names(R.content_hash, C_new, E.file_globs)   # rebuild changed files only
          map = build(repo, changed, extractor=E)
      manifest.update_repo(repo, content_hash=C_new, built_with_extractor_sha=E.extractor_sha,
                                 built_with_vocab_sha=manifest.vocab_sha)
      check_coverage(map, E.coverage_floor)         # §5.4 — extractor adequacy (REONBOARD_FLAG)
      check_vocab_adequacy(map, manifest.adequacy_threshold)         # §5.4 — vocabulary adequacy (VOCAB_GAP_FLAG)
      return map
```

The `extractor_sha` guard in Branch B is deliberate: if the frozen extractor was re-blessed (new sha), the cache is stale and Branch C rebuilds — so a re-onboarding always invalidates affected maps. The `vocab_sha` guard (ADR-003) is the same mechanism for the **dictionary**: a human-gated vocabulary amendment bumps `vocab_sha`, invalidating affected maps so their `tags` are recomputed — but because only `tags` depend on the vocabulary, a *vocab-only* change takes the cheap `retag_only` path (structure + `purpose` reused, only the tag pass re-runs), not a structural rebuild. While the single domain's vocabulary is frozen, `vocab_sha` is constant and this guard is inert (the reserved-hook discipline of FR-DC-13).

### 5.4 Coverage signal + re-onboarding threshold (FR-DC-16)

Every build emits `coverage_report` (§3.3). `coverage = files_extracted / files_seen`.

```
check_coverage(map, floor):
  if map.coverage_report.coverage < floor:
      raise REONBOARD_FLAG(language=L, coverage=…, floor=…, patterns=unresolved_patterns)
      # surfaced to operator like a GF flag, but distinct: it asks "re-bless the extractor for new idioms?"
      # the extractor is NEVER auto-modified — a frozen tool raises its hand, it does not rewrite itself.
```

Unresolved files are written to `code_map.json` with `coverage: coarse` and confirmed in the **deep pass** (`code_impact`). The re-onboarding decision is recorded in `decisions.jsonl` as `reonboard_flag` (§3.6). This cleanly separates "content changed → rebuild map" (Branch C) from "a structural pattern the tool can't handle → human decides" (this flag).

#### 5.4.1 ~~Vocabulary adequacy detector~~ — ⛔ RETIRED (ADR-008; no vocabulary, nothing untagged)

> The concern ("is our semantic layer adequate for this corpus?") survives and is answered better:
> the **stage-distribution report** at the repo onboarding gate (human-authored vs model-inferred vs
> uncovered, D-A21), per-module `purpose_confidence`, and the declared `unanalyzable[]` list surfaced
> at §18. Purpose-only tier-1 misses recurring in one module are the drift signal (D-A19), reviewed at
> re-onboarding — human-triggered, never auto-pivoted.

`check_coverage` (above) is *extractor* adequacy — "does the frozen **tool** cover this repo's languages?". `check_vocab_adequacy` is the exact twin for *vocabulary* adequacy — "does the frozen **dictionary** cover this corpus's concepts?". It runs in the gate's post-build path beside `check_coverage`, reading two signals (a model byproduct + a deterministic floor):

```
check_vocab_adequacy(entries, uncovered_concepts, threshold):
  # ── PRIMARY signal — leftover meaning (catches BOTH fully- and partially-uncovered files) ──
  # uncovered_concepts[] was emitted per file by model_enrich (§5.5) — concepts present in a file
  # that NO vocabulary tag covers, independent of how many tags the file did get.
  recurring = concepts in uncovered_concepts appearing in >= MIN_RECUR net-new files   # deterministic aggregate
  for c in recurring:
      raise VOCAB_GAP_FLAG(arm="code", concept=c, evidence=files_naming(c))   # names the missing concept

  # ── FLOOR — deterministic, model-free safety net (catches the fully-uncovered case alone) ──
  untagged_ratio_code = count(files where tags == []) / max(1, count(files))
  # doc arm (when the doc manifest exists — §3.2): entries with no topics / total entries
  emit telemetry(vocab_adequacy: {code: untagged_ratio_code, docs: untagged_ratio_docs})   # every run → trend
  if untagged_ratio_code > threshold or untagged_ratio_docs > threshold:
      raise VOCAB_GAP_FLAG(arm=…, ratio=…, threshold=…)   # systematic gap, even if model emission was absent
  # NEVER auto-grows the vocabulary — a frozen dictionary raises its hand, exactly like REONBOARD_FLAG.
```

**Why two signals.** A plain empty-`tags` count catches only the *fully*-uncovered file (`tags: []`); it misses the **partially**-uncovered one (the file got its primary tag, e.g. `[routing]`, but a *secondary* concept — `tokenization` — has no tag, so the file is non-empty and the count waves it through). `uncovered_concepts` (the model naming leftover meaning during the same enrichment pass) catches **both**, because it does not depend on the tag count. The deterministic `untagged_ratio` is kept **underneath** as a model-free floor: it still fires on a systematic fully-uncovered gap even if the model's emission is missing/unreliable, and it is the cheap always-on trend line. Direction: `untagged_ratio = untagged / total`, so a **high** ratio is the bad one; `adequacy_threshold` (§5.2; default `0.20`) separates a few legitimately-untaggable files (a utility header, a vendor shim — `tags: []` is *correct*) from a systematic gap.

A `VOCAB_GAP_FLAG` is recorded in `decisions.jsonl` (§3.6) for a human to decide whether to amend the vocabulary; **the run is not blocked** — adequacy is an advisory **runtime flag**, not a build hard-gate (§10 containment remains the hard gate). **L1 (in-slice)** is the `uncovered_concepts` emission + this deterministic aggregation/flag. The model **proposal** that turns a recurring uncovered concept into a well-formed candidate tag (`vocab_gap_assess`), the human-gated **amendment**, the `vocab_sha` bump, and the **re-tag pass** are the deferred **L2** half (FR-DC-21, Phase 5 / port-time).

### 5.5 Dispatcher + per-language normalization contract (FR-DC-17)

```
dispatch(repo) -> code_map.json:
  L = detect_language(repo)                          # deterministic
  E = manifest.extractor_for(L)
  if E:
      raw     = E.run(repo)                           # frozen tool (tree-sitter-c for C; …) → raw symbols+edges
      entries = normalize(raw)                        # → code_map FILE-ENTRY shape (the contract below)
      cov     = "coarse"                              # per D6a; deep pass confirms
  else:
      entries = model_fallback(repo)                  # model derives structure; FR-DC-17 lower-coverage
      mark_all(entries, coverage="coarse"); force_top_level_coverage("coarse")
  uncovered = []
  for e in entries:
      e.purpose, e.tags, unc = model_enrich(e)        # MODEL owns purpose + tags ONLY (FR-DC-17);
      uncovered += unc                                #   unc = uncovered_concepts → ledger, NOT the map (ADR-003)
      assert e.tags ⊆ domain_vocabulary               # D5 / §10 (containment)
  check_vocab_adequacy(entries, uncovered, threshold) # ADR-003 / §5.4.1 — VOCAB_GAP_FLAG (adequacy); never blocks
  edges = merge_edges(entries)                        # DETERMINISTIC: match depends_on ↔ used_by (closure)
  return assemble(entries, edges, coverage_report)
```

**Normalization contract (the seam that lets language vary without touching the core).** Every extractor — deterministic or fallback — MUST emit file entries conforming to the `code_map.json` file schema (§3.3): `path, module, interfaces[], depends_on[], used_by[], coverage`. Division of labor is fixed: the **extractor owns structural fields** (`path/module/interfaces/depends_on/used_by`); the **model owns `purpose` + `tags` only** and MUST NOT be the primary source of dependency edges. `merge_edges` (matching one file's outbound refs to another's exposed interfaces) is a deterministic merge step, not a per-file model judgment. Static-analysis blind spots (function pointers, macros, config-driven wiring) are marked `coverage: coarse` and confirmed deep.

The **dispatcher is the only place language varies.** Adding a language = "write one more extractor + onboard it"; the core, the schema, and `code_impact` are untouched.

**`purpose`/`tags` separability (ADR-003).** The two model-owned fields have different dependencies: `purpose` is free text and needs **no** vocabulary, while `tags` is gated by `assert tags ⊆ vocabulary`. In a normal run `model_enrich` writes both back-to-back. The vocabulary-onboarding path (FR-DC-20, deferred) exploits the split — it runs a `purpose`-first pass (vocabulary-independent) to help *propose* a new domain's dictionary, then assigns `tags` last against the frozen result.

**`uncovered_concepts` — the adequacy byproduct (ADR-003 / FR-DC-21).** Because the model cannot invent a tag, a concept the vocabulary lacks would otherwise vanish silently. So `model_enrich` returns a **third** value alongside `purpose`/`tags`: `uncovered_concepts[]`, the concepts it recognized in the file that **no** vocabulary tag covers. This is emitted in the same pass (the model already read the file), is **independent of the tag count**, and so catches both a fully-uncovered file (`tags: []`) *and* a partially-uncovered one (`tags: [routing]` but a secondary concept un-nameable). It does **not** land on the `code_map` entry — it routes nothing, so it goes to the ledger (§3.6) and feeds the adequacy detector (§5.4.1), not the map. The map's `tags` therefore stay exactly the in-vocabulary set.

### 5.6 `code_impact` — the three-tier walk (FR-EN-01/05, D6b/c; replaces coarse/deep framing)

> 🔧 **ADR-008 amendment (normative — D-A19).** The topics×tags coarse join is retired. Per
> **assertion** (query = frame + requirement title + description + assertion, raw text — no keyword
> extraction): **tier 1** vs `components[].purpose` (matched modules; low `purpose_confidence`
> **widens**, never excludes) → **tier 2** vs `files[].purpose` within matched modules only → **tier
> 3a** read selected source, confirm/refute landing points + verdict implicit assumptions → **tier
> 3b** walk `depends_on`/`used_by` outward to closure (reaches files no tier selected). `purpose`
> seeds; source establishes. Retrieval batches per **deliverable** (territory resolved once);
> reasoning is per-assertion, independent, fan-out safe (anti-anchoring: share reference material,
> never conclusions). Matches are **explainable** — each carries its reasoning into `enrichment.json`.
> The old coarse/deep guardrails below stand where not superseded: deep reads only the flagged slice;
> closure within-repo (FR-DC-13); Flags every run (D6b); material threshold (D6c).

Unchanged from `code_impact_assess.skill.md`, now contractual:
- **Coarse (early, map-only):** requirement topics × `code_map.json` tags/purpose → ranked candidate areas. Reads the map only. Threads high-level code context into early BRD sections.
- **Deep (at the code-impact section, flagged areas only):** selective-reads real code from `repo/` for the flagged slice, traces the real dependency closure, assesses precise change, and emits the **required Flags** section every run (§3.6 / D6b schema). Recommends `severity` (`material`/`advisory`); **never decides scope**.
- **Material threshold (D6c):** the operator's decision is **material** — triggering section revision **and** a re-run scoped to the *changed surface only* — iff it changes the impacted code surface, changes a `must_capture` the deep pass depended on, or moves a Scope/Out-of-scope boundary. Otherwise **advisory** (recorded, sections updated, no re-run). `brd_author` runs the human-mediated flag loop (surface → wait → apply → conditional re-run); G1 is the backstop for any missed flag.

### 5.7 External-build → VDI-port handling (FR-DC-14, C5)

The frozen extractor is plumbing committed to `core/extractors/`; it **ports unchanged** (it is version-controlled, not regenerated). At port time a **tooling-availability checkpoint** runs:

```
port_check(manifest, VDI):
  for E in manifest.extractors:
      for tool in E.tools_required:                 # C: tree-sitter, tree-sitter-c (pip, in-venv) — ADR-001
          if not available(tool):                   # importable in the venv (or, for a PATH-binary tool, on PATH)
              if provisionable(tool):   provision(tool)        # ops task (e.g. pip install into the VDI venv)
              else:                     enable_model_fallback(E.language)   # marks coverage lower, flags
```

For the C extractor the tools are **Python packages** (`tree-sitter` + `tree-sitter-c`, per ADR-001), so `available(tool)` is "import succeeds in the venv," not "binary on PATH" — chosen because the AppLocker-locked VDI cannot cleanly provision PATH binaries (`ctags`/`cscope`) while pip runs in-policy. This is surfaced at Generate/onboarding as a **VDI prerequisite** (the same shape as the FR-XS-26 allow-list provisioning: a prerequisite Generate names, not something the scaffolder emits). The model-only fallback (§5.5) is the safety net when a tool is absent and unprovisionable — correctness degrades to coarse-coverage, never to a hard failure.

---

## 6. Seams — domain + runtime-tool; parity mechanics

### 6.1 Domain seam

Variation confined to: the **pre-processing adapter** (`profiles/<domain>/adapter/`), **`brd_profile.<domain>.yaml`**, **`frd_profile.<domain>.yaml`**, **`jira_template.<domain>.yaml`**, and the **tag vocabulary** (`vocabulary.<domain>.yaml`). Schemas are fixed by D1 (BRD profile), D3a (FRD profile), D3b (Jira template), D5 (vocabulary). The generic skills never carry domain content; composition is `skill(profile) → artifact`. Baseline sections stay **inline in the author skills** for MVP (D2); the profile carries per-section substance and merges over the inline baseline (D2 merge algorithm). Ingestion **never** branches on domain (D7) — a new source type is one new generic connector in `core/`, never a domain fork.

### 6.2 Runtime-tool seam

Two hand-authored overlays (D9): `overlays/claude/` and `overlays/copilot/`. Each carries the agent/subagent **wrapper files**, the **prompt files** (`start-ingest` Layer-1 kickoff + the per-stage `start-brd`, `start-frd`, `start-jira`), and the **launch** method — kept native (frontmatter + location genuinely differ; not abstracted). The **only generated piece** is the instruction file.

### 6.3 Instruction-file generation (FR-XS-07, D9)

One canonical `core/instruction_file.template.md`. At Generate, the scaffolder fills placeholders and emits **`CLAUDE.md`** *or* **`copilot-instructions.md`** by `runtime_tool` — no runtime `AGENTS.md` pointer.

```
placeholders filled from UI_INPUT + overlay_manifest:
  {{domain}} {{runtime_tool}} {{registry_sha}} {{run_id}}
  {{roles}}            ← overlay_manifest.roles (name → skill, user_invocable)
  {{prompt_files}}     ← overlay_manifest.prompt_files
  {{stage_transition}} ← overlay_manifest.overlays[tool].launch + gesture
                          claude → "/clear or new session"   copilot → "Ctrl+N + /start-<stage>"
  {{start_gesture}}    ← exact per-tool start gesture surfaced at hand-off (FR-XS-22)
```

The template body is identical across tools except the gesture/launch lines pulled from `overlays[tool]` — so the instruction file is single-source with a thin per-tool tail, satisfying NFR-02 (portability: change only the overlay).

### 6.4 Stage transitions (FR-XS-11)

Defined in the instruction file, **surfaced by the agent** as the closing line of the prior stage, **performed by the operator** (Claude `/clear`/new session; Copilot `Ctrl+N` + prompt file). The agent never self-issues them. Each overlay ships the three stage prompt files; each just re-points a fresh agent at `UI_INPUT.yaml` + the prior artifact. The fourth prompt, **`start-ingest`**, is not a stage transition: it is the run's **kickoff**, fired by the operator as the start gesture (FR-XS-22) to drive **Layer 1** (Run order step 1 — `source_processor` fan-out, then `merge_manifest.py`). It keeps the orchestrator role rather than handing off to an authoring agent, and closes by surfacing `start-brd` (the Layer-2 transition).

### 6.5 Parity build-check (FR-XS-20) — see §10.2

### 6.6 Registration & inventory contracts (how the domain seam is populated)

**Principle — registration is build-time, not runtime.** Domains, ingestion connectors, and adapter skills are added by **authoring artifacts into the registry and committing them** — human-authored, build-checked, SHA-pinned — never invented by the agent at runtime. The session reads `UI_INPUT.domain` and loads only what already exists at the pinned `registry_sha`. This is the same author-then-freeze discipline as the extractor onboarding gate (§5): the registry is the catalog, and the build checks (§10) are the gate. Consequently a new domain or connector touches **only seam artifacts** — never the generic core.

**MVP runs one domain: `payment_brand` (PBI — Payment Brand Implementations).** The domain *key* stays `payment_brand` (already used by D5, the profiles, and the vocabulary); **"PBI" is the human label** surfaced in the UI. The key is not renamed — renaming would ripple through D5 and every pinned profile for no benefit.

#### 6.6.1 Domain registration (convention; no catalog manifest for MVP)

A domain **exists iff** its seam artifacts are present in the registry:

```
core/profiles/<domain>/
  brd_profile.<domain>.yaml
  frd_profile.<domain>.yaml
  vocabulary.<domain>.yaml
  adapter/adapter.yaml + <adapter skills>.skill.md
core/templates/<domain>/
  jira_template.<domain>.yaml      # required once L4 (Jira) is in scope; NOT needed for the BRD→FRD slice
```

> **Forward-compat note (ADR-004 / FR-DC-22, W — deferred, does not change this slice).** Authoring a profile is human work today (TASK-015/016). When the adaptive-dictionary loop grows the vocabulary (FR-DC-20/21), a newly-approved tag is *taggable but unconsumed* until a profile section references it — **gate 3**. A deferred, human-gated skill (`profile_onboard`) MAY then **propose** the target section + drafted `must_capture`/`probe_if_missing` (sources derived from the tag's `emitted_by`; `functional_kind`/`traces_to` for the FRD) and emit a **reviewable profile diff** for a human to approve and commit. It runs in two modes: **bulk** — at onboarding, right after `domain_onboard` freezes the vocabulary, it proposes the *whole* first profile (sections + topics) from that vocabulary + the baseline, refined and frozen in one session; and **incremental** — at drift, one new tag at a time. Vocabulary-first is mandatory (§10.1 containment), so the profile is always generated *from* a frozen vocabulary — the onboarding order is `domain_onboard` → `profile_onboard` (bulk) → human refine/freeze. It proposes, never blesses: the profile stays a build-time, SHA-pinned, human-frozen artifact — the agent never mutates it at runtime, exactly as this section requires. No in-slice plumbing or reserved hook is needed (the D1/D3a schema already admits a new `requirements[]` entry additively).

Presence **is** registration; `UI_INPUT.domain` selects it. There is **no explicit `domains_index.yaml` catalog for MVP** — a `domains_index.yaml` would be an *index of which domains exist* (one entry per domain: key, label, dir), read by the UI to populate the domain selector and looped over by a build check; it is **not** a config fed to any skill (the per-domain `brd_profile`/`frd_profile`/`vocabulary`/`adapter.yaml` files are, and those exist in MVP). At one domain the index is a one-line list stating the obvious, and the directory's existence already registers the domain — so the index is **deferred to the second domain** (§11), consistent with the D2 "defer extraction until the multi-domain need is real" pattern: the second domain is what proves the engine is generic ("write one more profile + pack, zero core changes"), and it is also where the index earns its place (a real dropdown to enumerate). Build check **§10.3** asserts a selected domain has its required artifacts.

#### 6.6.2 Ingestion connector inventory + contract

Connectors are **generic, source-type-keyed, never per-domain** (D7). Each is one script `core/scripts/ingest_<type>.py` (code → `clone.py`). A connector that branches on `domain` is a defect; a new source type is **one new generic connector in core**, never a domain fork.

Per-connector contract: consumes `UI_INPUT.sources[]` entries of its `type` + auth via the seam (`auth_ref`, never inline); produces raw content (code → clone into `repo/`). Per-instance parameters (URL, path, repo, auth) come from `UI_INPUT.yaml` + `jpmc_adapters` (FR-DC-12).

**MVP-honest inventory — author only what the first slice consumes.** The first slice is one PDF document + one Bitbucket-cloned Stratus repo, so the slice authors **two** connectors: the **document/PDF source** (SharePoint connector, or a direct file path) and **Bitbucket** (`clone.py`). **Confluence and every other source-type are "write one more connector" follow-ons** (§11), not first-slice work. Build check **§10.4** asserts every `UI_INPUT.sources[].type` has a registered connector.

#### 6.6.3 Adapter pack contract + `adapter.yaml` (the domain pre-processing seam)

> 🔧 **ADR-008 amendment.** **`emits:` is deleted from every pipeline entry** (tags are gone), and the
> doc pipeline becomes **domain-agnostic**: per-type lanes route to *extract* skills (`pdf_extract`,
> `confluence_extract`, `jira_extract`) followed by the shared **`doc_index`** skill (builds the
> per-artifact index for artifacts over the whole-read budget, D-A18; summaries always generated; the
> extract/index two-file pairing per §3.2). Tagging skills (`article_summarize`-as-tagger,
> `confluence_tag`) are retired. The pack's remaining domain content is the **SI section profile**
> (`must_capture`/`probe_if_missing` per section) + **`jira_template`** — whether `adapter.yaml`
> remains per-domain at all is a Phase-C/D consolidation call (D-A18 note). `docs_pipeline` per-type
> routing + required `default` lane (063B) stand.

The domain's pre-processing adapter is a **pack** of skills under `profiles/<domain>/adapter/`, declared by `adapter.yaml`. This pack is the swappable domain seam (docs → extract then tag; code → hand to `code_map_build`). The generic `source_processor` reads `adapter.yaml` to know the run order and routing; it carries no domain knowledge itself.

**Contract.** (a) every skill's `emits` tags ⊆ the domain vocabulary (D5); (b) the pack collectively produces **every `required: true` topic** across `brd_profile` + `frd_profile` (a required topic with no producing skill is a build error); (c) `adapter.yaml`'s emit-map agrees with the vocabulary's "emitted by" column (no drift). Run order is declared per source class (`docs_pipeline` ordered; `code_pipeline` routes to `code_map_build`). **`docs_pipeline` per-type routing (TASK-063B):** `docs_pipeline` may be a **bare list** (legacy form == the `default` lane) **or** a **mapping** keyed by source `type` with a required `default` fallback (e.g. `confluence:` routes Confluence pages to a tag-only lane, distinct from the PDF `default`). Routing is by **source `type`, never `domain`** (D7), and the connector descriptor + manifest-entry shapes are unchanged across lanes (**descriptor parity** — only the *processing* differs). The §10.5 checks below run across the **union** of all variants' emits.

**Schema (normative) + the `payment_brand` instance:**

```yaml
# core/profiles/payment_brand/adapter/adapter.yaml
domain: payment_brand                # PBI
docs_pipeline:                       # ordered; runs per non-code (document) source
  - { skill: pdf_extract,        emits: [] }                                   # structural extraction; no tags
  - { skill: article_summarize,  emits: [brand_rules, message_format, interchange_fees, reporting, mandate, transaction_flow, card_brand, routing, certification, compliance_deadline] }  # SOLE doc tagger — all 10 doc-side tags
code_pipeline:                       # code sources route here
  - { skill: code_map_build,     emits: [routing, settlement, transaction_flow, error_handling, message_format, card_brand] }
```

The `emits` sets reproduce the D5 vocabulary "emitted by" mapping; build check **§10.5** cross-checks the two so they cannot drift, and confirms every required topic is covered.

**Per-type routing form (TASK-063B, back-compatible).** The `docs_pipeline` above is a bare list — equivalent to the `default` lane below. To process a doc `type` differently (e.g. a Confluence KB page is HTML, not a PDF, so `pdf_extract` is wrong for it), `docs_pipeline` may instead be a mapping keyed by source `type` with a required `default`:

```yaml
docs_pipeline:                       # routed by source `type`; bare-list form still valid (== default)
  default:                           # type: file, sharepoint (PDFs) — the ordered 2-step lane
    - { skill: pdf_extract,        emits: [] }
    - { skill: article_summarize,  emits: [brand_rules, message_format, interchange_fees, reporting, mandate, transaction_flow, card_brand, routing, certification, compliance_deadline] }  # SOLE doc tagger — all 10 doc-side tags
  confluence:                        # type: confluence — tag-only KB lane (no extract/summarize)
    - { skill: confluence_tag,     emits: [brand_rules, card_brand, message_format, routing, transaction_flow, error_handling] }
```

`source_processor` selects the lane by `src.type`, falling back to `default`. A new emitting skill (e.g. `confluence_tag`) must be added to the vocabulary's `emitted_by` for each tag it emits (the §10.5 union check enforces this); descriptor parity is preserved — only the processing pipeline differs by type, never the descriptor or manifest shape.

**`change_type_assess` removed (change_type_removal, V-approved).** The `default` lane was originally three steps: `pdf_extract → article_summarize → change_type_assess`. The third skill produced (a) a `change_type` classification field on the manifest entry, which **nothing downstream consumed** (no code or profile branched on it), and (b) five doc-side tags (`mandate`, `card_brand`, `routing`, `certification`, `compliance_deadline`). It was a **second full model pass over the same extracted text** for those five tags, so it was consolidated into `article_summarize` — now the **sole tagger**, owning all ten doc-side tags. The `change_type` field is dropped entirely (removed from the §3.2 entry shape and `merge_manifest.py`'s key order). The D5 `emitted_by` column re-homes those five tags `change_type_assess → article_summarize` (`vocab_sha → d5frozen-r4`). **Port note:** carry this into the JPMC-side §6.6.3 / D5 at port time; see `notes/change_type_removal.md`.

**Where the concrete files are authored.** This subsection fixes the *contracts and homes*. The concrete `payment_brand` instances (`brd_profile`, `frd_profile`, `vocabulary` [already pinned in D5], `adapter.yaml` + the four pack skills, the two slice-1 connectors) are **authored during the build as Chat B pre-tasks**, each gated by the build checks above — not pre-authored in this spec.

> **Forward-compat note (ADR-005 / FR-DC-23, W — deferred, does not change this slice).** Authoring the adapter pack is human work today (TASK-017/018/019). For a *new* domain, a deferred, human-gated skill (`adapter_onboard`) MAY then **propose** the pack by guided conversation — showing the fixed frame (the generic engine + the fixed `code_pipeline → code_map_build`) and designing the variable `docs_pipeline`: reusing shared/structural skills, scaffolding net-new domain-specific skills, and **deriving each skill's `emits` from the vocabulary's `emitted_by` column** so this emit-map cannot drift from the vocabulary by construction (the §10.5 check above becomes a confirmation rather than a manual reconciliation). It runs last in the onboarding order (`domain_onboard` → `profile_onboard` → `adapter_onboard`), in two modes (bulk = whole first pack; incremental = one tag at drift), and proposes-never-blesses: the pack stays a build-time, SHA-pinned, human-frozen artifact — the agent references core skills and authors only domain **pack** skills, never `core/skills/`, and never mutates at runtime. Dependency: the structural step (`pdf_extract`, domain-agnostic) must be a **core** skill available before the pack exists (tagging skills are authored last). No in-slice plumbing or reserved hook is needed (this `adapter.yaml` schema already admits additional `docs_pipeline` skills additively).



The seam isolates **all** external integration: Jira write + auth. It is the **only external mutation** (NFR-09). Skills/agents never see raw credentials; the adapter is the only module importing the credential SDK.

### 7.1 Interface signature (normative)

```python
# core/adapters/jpmc_adapters/jira.py
def push_epics(plan: dict, trace: dict, *, project_key: str, dry_run: bool = False) -> dict:
    """
    plan    : parsed jira_plan.json (epics[] with stable local_id)
    trace   : parsed jira_trace.json (existing local_id→key map; may be empty)
    returns : updated trace dict { local_id: {key, url, action: created|updated, pushed_ts} }
    Idempotent (NFR-09): if local_id already maps to a key → UPDATE that epic; else CREATE.
                         Never duplicates. Each epic's result is recorded as it returns, so a
                         mid-batch failure leaves prior successes in trace; retry resumes the remainder.
    Side effects: Jira REST writes only. Does NOT write jira_trace.json — the caller persists it
                  (keeps the file-as-state rule; the adapter returns data).
    dry_run : when True, validates field/controls completeness and returns the planned actions
              WITHOUT writing — used by jira_validator and the G3 preview.
    """

# core/adapters/jpmc_adapters/auth.py
def auth_context(service: str) -> "AuthHandle":
    """Resolve credentials for {confluence|sharepoint|bitbucket|jira} from the JPMC secret store / env.
       All secret handling is isolated here. Referenced by UI_INPUT.sources[].auth_ref. Never logged,
       never written to artifacts or telemetry."""
```

### 7.2 Push flow (G3)

`jira_validator` runs `push_epics(..., dry_run=True)` to score field/controls completeness + bidirectional traceability. On the single **G3** sign-off (review + authorize in one), the session calls `push_epics(..., dry_run=False)`, then persists the returned dict to `jira_trace.json` and emits a `jira_push` telemetry event. Re-runs are idempotent by `local_id`.

### 7.3 Model backend (Bedrock) — environment, not a runtime seam call

Models run via JPMC Bedrock (NFR-04): `CLAUDE_CODE_USE_BEDROCK=1` + region + model id are **environment variables set at launch** by the overlay's launch step — not a function the skills call. Copilot uses its own model selection (it can run Claude models). Skills stay model-neutral. This is an environment contract, documented here so it isn't mistaken for an adapter call.

---

## 8. Telemetry → metrics

`telemetry.jsonl` (D8a-1) is finalized below; metrics are derived by `metrics_scan.py` scanning the file (FR-MX-01). No metric is hand-entered.

### 8.1 Event schema (envelope + payloads)

Envelope on every event: `ts, run_id, domain, tool, event`. Payloads:

| `event` | Payload fields | Feeds |
|---------|----------------|-------|
| `run_started` | `path`, `registry_sha` | M05 |
| `stage_started` | `stage` | M06, M07 |
| `stage_completed` | `stage`, `duration_ms` | M06, M07 |
| `model_call` | `stage`, `model`, `tokens_in`, `tokens_out`, `cost_usd` | M01, M02 |
| `validation` | `artifact` (`si_v1`/`enrichment`/`jira`), `score` | M03, M09 |
| `gate_decision` | `gate` (G1/G2/G3), `outcome` (accept/reopen), `actor`, `version` | M04 |
| `flag_decision` | `flag_type`, `option`, `severity` | audit |
| `jira_push` | `epics`, `stories`, `success` (bool), `partial` (bool) | M10, M11 |
| `error` | `stage`, `kind`, `message` | error log |
| `verdict` | `finding_id`, `arm`, `verdict`, `route` | M12 |
| `escalation` | `finding_id`, `reason`, `severity` | G2 precondition |
| `disposition` | `finding_id`, `call`, `actor`, `target` | G2 precondition, audit |

`stage` vocabulary: `ingest`, `si_v1`, `enrichment`, `si_v2`, `jira`.

> **Amended 2026-08-01 (TASK-125) — post-ADR-008 vocabulary.** The stage list, `validation.artifact`
> and the three enrichment events landed with the ledger schemas at TASK-104/110/121; this table had
> not been carried across. `jira_push.stories` is **new here**: the amended M10 is stories/**epic**,
> which `epics` alone cannot express, so the count has to be on the event. **Port note:** carry this
> §8.1/§8.2 amendment into the JPMC-side spec at port time.

### 8.2 Metric derivations (FR-MX-02, amended)

Anything that is **a property of a run** — cost, score, cycle time, first-pass, yield,
coverage-at-push — is computed per run and **then averaged**, never pooled: pooling lets one long
run stand in for the fleet, and M09 in particular is a per-run score. **M07 and M10 are pooled, and
deliberately so** — a p95 of per-run p95s is not a p95, and stories/epic is a ratio of two totals,
so averaging per-run ratios would weight a 1-epic run equally with a 12-epic one. Those two measure
the fleet; the rest measure the run.

A metric with no events yields **no value**, never `0`: a run that never pushed has no push-success
*rate*, and reporting 0% would be a claim rather than a measurement. The exception is M12, where a
run that enriched and yielded nothing genuinely yielded 0 — that is a finding about the run.

| Metric | Derivation (scan of `telemetry.jsonl`) |
|--------|----------------------------------------|
| M01 $/SI-v1 | Σ `model_call.cost_usd` where `stage = si_v1` per run; mean across the runs that authored |
| M02 $/enrichment | Σ `model_call.cost_usd` where `stage ∈ {enrichment, si_v2}` per run; mean across the runs that enriched. **Both stages** — the apply pass is enrichment's cost, not a separate one |
| M03 avg score at acceptance | mean `validation.score` standing at each `gate_decision(accept)`, over G1/G2/G3. A score that was reopened never counts |
| M04 first-pass acceptance | count(`gate_decision G1` `accept` at `version=1` with no prior `reopen`) / count(runs **reaching** G1). A run that never reached G1 is skipped, not scored 0 |
| M05 docs/month | count(`run_started`) per calendar month |
| M06 v1→v2 cycle time | `ts(gate G2 accept) − ts(gate G1 accept)` per run; mean across the runs that reached G2 |
| M07 latency p95 | p95 of `stage_completed.duration_ms` across stages |
| M09 §16→story coverage at push | `validation.score` for `artifact=jira` **standing at the moment of `jira_push`** (a later re-score says nothing about what shipped); mean across the runs that pushed |
| M10 stories/epic | Σ `jira_push.stories` / Σ `jira_push.epics` |
| M11 push success rate | count(`jira_push.success=true`) / count(`jira_push`). A run that never pushed is not a failed push |
| M12 **enrichment yield** | count(`verdict.route ∈ {auto_correct, auto_write, auto_fill}`) per run, broken out as corrections / derived impacts / auto-fills; mean across the runs that enriched. **This is the v1→v2 delta** — the stage's value story, and the reason `verdict.route` is on the event |
| M08 upstream-change alerts | **W** — depends on deferred change-detection; not computed in MVP |

---

## 9. Gates & thresholds

Six control points (D4): **G0** scaffold checkpoint, **GF** per-flag sub-gate, **G1/G2/G3** human acceptance gates. Validators are **machine soft-gates** that feed the human gate's score but never auto-advance. This section pins the **validator scoring formulas** and the **single project-level threshold default** handed forward in C5.

### 9.1 Single threshold default

`UI_INPUT.gates.score_threshold` defaults to **85** and applies to G1/G2/G3 (the single project-level value D4 calls for). On top of the soft score, each gate has **absolute hard preconditions** (non-scored) that must hold regardless of score.

### 9.2 `solution_intent_validator` score (feeds G1) *(replaces `brd_validator` per ADR-008/D-A23)*

```
section_coverage   = satisfied_required_must_capture_items / total_required_must_capture_items
                     # per-section checklists (D11.1) — a checklist, not a topic vocabulary;
                     # "satisfied" = grounded by source/frame/operator, not [TBD — unsourced]
citation_integrity = cited_substantive_claims / total_substantive_claims
si_score = round(100 * (0.7 * section_coverage + 0.3 * citation_integrity))
```
**G1 passes iff:** `si_score ≥ threshold` **AND** (hard) every required section satisfied and every
conditional section dispositioned (FR-SI-06) **AND** (hard) §15→§4 + §8→§7 traces intact **AND**
(hard) all flags resolved/recorded. Accept → `v1.md` **frozen**; reopen → v1.1 pre-freeze.

### 9.3 enrichment score (feeds G2) *(new duty per ADR-008 — the old §9.3 FRD formula moved to §9.4)*

```
verdict_completeness = assertions_and_claims_verdicted / total_in_verdict_population
                       # population per D-A5 (factual current-state only; runtime-shaped skipped)
impact_coverage      = requirements_ARM_1_REACHED / total_requirements     # ← AMENDED, TASK-121
g2_score = round(100 * (0.5 * verdict_completeness + 0.5 * impact_coverage))
```

> 🔧 **Amendment (TASK-121, 2026-08-01) — the provisional formula was validated and failed.**
> D-A23 marked this formula provisional pending "validation against the first real run". That run
> happened at TASK-121 and the original `impact_coverage` —
> ~~`requirements_with_section16_entries_or_dispositioned / total_requirements`~~ — scored a
> **complete, correct** run at **0.417**, giving G2 **71** against a threshold of 85.
>
> **Cause:** 7 of 12 requirements were fully analysed by Arm 1 and found to need **no change**, so
> they carried neither a §16 entry nor a disposition. That is the *desirable* outcome, not a
> coverage gap — and the formula made the cheapest route to a passing score the **manufacture of
> §16 entries for requirements that need none**, which is exactly the fabrication the grounding
> discipline exists to prevent.
>
> **Resolution:** `impact_coverage` measures what it was always for — whether Arm 1 **reached**
> every requirement (produced ≥1 finding of any kind for it). Verdict completeness already
> measures per-assertion thoroughness; this measures per-requirement reach, so the two halves stay
> independent. **Port note:** carry this into the JPMC-side §9.3 + FR-EN-07 at port time.
**G2 passes iff:** `g2_score ≥ threshold` **AND** (hard) every escalated finding dispositioned via the
walkthrough **AND** (hard) every in-place correction carries `[code:]` provenance **AND** (hard) §1
regenerated after all corrections. Accept → `v2.md` accepted; Jira authoring may begin. *(Provisional
formula — validate against the first real run before freezing, per D-A23.)*

### 9.4 `jira_validator` score (feeds G3) *(absorbs the old FRD traceability/testability duty per D-A23)*

```
traceability = valid_links / total_links_required
               # every epic → its §7 deliverable; every story → its epic AND (a §16 entry OR §7
               # non-code work); every §16 entry → ≥1 story or an explicit disposition
testability  = stories_with_acceptance_criteria_and_code_location / total_stories
               # each story names the code it changes, or is flagged new-build / non-code
field_completeness = issues_with_all_required_and_controls_fields / total_issues
jira_score = round(100 * (0.4 * traceability + 0.3 * testability + 0.3 * field_completeness))
```
**G3 passes iff:** `jira_score ≥ threshold` **AND** (hard) hierarchy traceability complete
(`traceability = 1.0`) **AND** (hard) all controls fields present. Accept = one combined sign-off
(review the 4-level plan + authorize push). Push is idempotent (§7). G3 **requires G2** — stories
derive from enrichment evidence and cannot be authored from v1 (FR-JR-01).

### 9.5 G0 / GF / the disposition walkthrough

- **G0** (checkpoint): after Generate-scaffold, before Run; operator inspects scaffold + `UI_INPUT.yaml`; proceed or regenerate. Reversible.
- **GF** (sub-gate, loop): per surfaced flag, operator decides (one at a time, with a recommendation); `material` decisions trigger a changed-surface-only re-run (§5.6). Recorded in `decisions.jsonl`.
- **Disposition walkthrough** (enrichment-stage operator turn, D-A17): the same surface→wait→apply
  pattern applied to escalated enrichment findings — triaged not enumerated, ordering-dependency
  aware, resumable (status per finding in `enrichment.json`); proposes, never decides.

---

## 10. Build checks

Five deterministic checks run at Generate/CI; any failing fails the build. 10.1–10.2 are the original contract checks; 10.3–10.5 enforce the registration contracts of §6.6.

### 10.1 ~~Vocabulary containment~~ — ⛔ RETIRED (ADR-008; the vocabulary is deleted)

> Replaced by **§10.5′** below at build time, plus the D-A23 **context checks** (module/purpose
> totality, `members[]` consistency, index completeness — run at ingest, reported in coverage) and
> **artifact checks** (§15→§4, §8→§7, assertion verdicts, §16↔story — run by validators at gates).

### 10.2 Overlay parity (D9, FR-XS-20)

```
load M = core/overlay_manifest.yaml
for tool in [claude, copilot]:
    for role in M.roles:
        assert a wrapper exists at tool's agents location (.claude/agents/<role>.md | <role>.agent.md)
        assert that wrapper's body references skill: <role.skill>
        assert wrapper frontmatter user_invocable == role.user_invocable
    for p in M.prompt_files:
        assert prompts/<p> exists in tool's overlay
FAIL → name the missing role/prompt and the overlay.
```

`overlay_manifest.yaml` is the D9-normative block (8 roles, 4 prompt files — `start-ingest` + the three stage prompts, per-tool launch) and is reproduced unchanged from REQUIREMENTS D9.

### 10.3 Domain artifact presence (§6.6.1)

```
let d = UI_INPUT.domain
assert exists core/profiles/<d>/brd_profile.<d>.yaml
assert exists core/profiles/<d>/frd_profile.<d>.yaml
assert exists core/profiles/<d>/vocabulary.<d>.yaml
assert exists core/profiles/<d>/adapter/adapter.yaml
assert exists core/templates/<d>/jira_template.<d>.yaml   # ONLY when L4 (Jira) is in run scope
FAIL → name the missing seam artifact for domain <d>.
```

### 10.4 Connector coverage (§6.6.2, D7)

```
for s in UI_INPUT.sources:
    assert exists core/scripts/ingest_<s.type>.py   (code type → clone.py)
    assert that connector does NOT branch on `domain`      # source-type keyed only (D7)
FAIL → name the source type with no registered connector.
```

### 10.5 ~~Adapter coverage + consistency~~ — ⛔ RETIRED (ADR-008; `emits` is deleted)

The pipeline-routing residue survives inside §10.4/§10.3: every `docs_pipeline` skill file exists;
a `docs_pipeline` mapping carries a `default` lane (063B). The emit-map assertions die with tags.

### 10.5′ Disposition-class totality (D11.3, D-A23 — the new §10 check)

```
load M = the D-A13 routing matrix (declared with the SI section contract)
load T = the disposition taxonomy offered by the UI (D-A12)
assert every SI section (except §1/§17/§18) has ≥1 input source routed in M   # no orphan section
assert every disposition class in T appears in ≥1 M cell                      # no orphan class
assert every conditional section is marked conditional in the SI profile      # FR-SI-06 renders
FAIL → name the orphan section or class.
```

**§10 net: four checks** — 10.2 parity (amended roles) · 10.3 domain artifacts (SI profile +
`jira_template`; no vocabulary) · 10.4 connector coverage (+ pipeline-file residue) · 10.5′ totality.

---

## 11. Explicitly still deferred (do not re-scope)

Named here so the task list does not pull them in:

- **SQLite / queryable metrics store** — JSONL ledger only for MVP (§2.2). Swap-in later when a dashboard or multi-operator concurrency requires it.
- **Direct Claude API execution path** — MVP runs entirely in-session (Claude Code / Copilot reading skills). API is a deferred pivot only if in-session proves insufficient (FR-XS-04).
- **Multi-system / cross-repo code impact** — MVP is single-repo (FR-DC-13). `external_calls`/`exposes` are reserved-but-unpopulated (§3.3) so the later fractal extension (system tier → coarse-map discovery → contract-seam stitching) is additive.
- **Jira stories** — epic-only for MVP (FR-JR-01); stories extend the same layer later.
- **Multi-domain breadth** — one domain (`payment_brand` / PBI). Deferred to the second domain: the explicit **`domains_index.yaml`** (an index of which domains exist — UI dropdown + all-domains build check; not a skill input, §6.6.1); baseline-YAML extraction (FR-BR-11 W); profile `suppress` verb (FR-BR-14 W); generated overlay wrappers (FR-XS-21 W). Each is justified only when a second domain stresses the merge.
- **Additional ingestion connectors + adapter packs** — the first slice authors only the document/PDF connector + Bitbucket clone (§6.6.2) and the PBI adapter pack (§6.6.3). The **Confluence connector**, any new source-type connector, and every additional domain's adapter pack are added later via the §6.6 registration contract ("write one more connector / pack"), never by changing the core.
- **Sync/freshness, change detection & downstream flagging (M08), semantic retrieval** — deferred (FR-DC-07); selective-read manifest only.
- **Auto-launch + Claude-only deterministic spine** — deferred (FR-XS-25); manual start, co-equal tools, no headless on the shared path.
- **Automated (non-human-mediated) impact re-runs** — every scope change stays operator-decided (FR-BR-08).
- **Custom context-refresh mechanism** — rely on tool auto-compaction + operator new-thread at boundaries (FR-XS-12).

---

## Appendix A — requirement coverage map (what this spec resolves)

| Handed-forward item (kickoff / C5) | Resolved in |
|------------------------------------|-------------|
| Data model: files + JSONL ledger, all schemas | §2, §3 |
| `code_map.json` finalize (D6a) + reserved cross-repo fields | §3.3 |
| `telemetry.jsonl` finalize (D8a-1) | §3.4, §8.1 |
| `run_state.json` / `decisions.jsonl` | §3.5, §3.6 |
| `jpmc_adapters` interface signature + auth isolation + idempotent re-push | §7 |
| Telemetry event schema → MVP metrics (FR-MX-02) | §8 |
| Gate score thresholds + validator scoring formulas | §9 |
| Overlay/parity mechanics (D9) + instruction-file generation | §6, §10.2 |
| Onboarding-manifest schema | §5.2 |
| 3-branch gate algorithm (FR-DC-15) | §5.3 |
| Coverage threshold → re-onboarding (FR-DC-16) | §5.4 |
| Dispatcher + per-language normalization (FR-DC-17) | §5.5 |
| External-build → VDI-port handling (FR-DC-14) | §5.7 |
| Build checks: vocabulary (D5) + overlay parity (D9) | §10.1–10.2 |
| Registration & inventory contracts (domain / connector / adapter pack) | §6.6, §10.3–10.5 |
| Registry hydration mechanics (clone vs sparse; SHA pin) | Appendix B |
| Confirm SQLite out / API out | §2.2, §11 |

## Appendix B — registry hydration mechanics (C5)

Hydration pulls version-pinned content from the Bitbucket registry and records the pin in `UI_INPUT.registry_sha` (FR-XS-10, NFR-01).

- **MVP (simple, deterministic):** `git clone --depth 1` the registry, `git checkout <registry_sha>`, then **selectively copy** `core/` + `profiles/<domain>/` + `templates/<domain>/` + `overlays/<tool>/` into the run scaffold. Deterministic and easy to audit.
- **Optimization (noted, not required for MVP):** partial + sparse checkout to materialize only the needed paths —
  `git clone --filter=blob:none --sparse <registry>` → `git sparse-checkout set core profiles/<domain> templates/<domain> overlays/<tool>` → `git checkout <registry_sha>`.
- **SHA-pinning:** `registry_sha` is the single pin; re-hydrating the same SHA reproduces the scaffold byte-for-byte (modulo the generated instruction file, itself a pure function of `UI_INPUT` + manifest). Repo source is separately pinned by `commit_sha` in `code_map.json` / `run_state.json`.
- **Determinism (NFR-07):** hydration is plumbing — `hydrate.py`, called by the session, never making authoring judgments.

---

*End of tech spec. Next: per-tool build task list (Chat B) → UI design.*
