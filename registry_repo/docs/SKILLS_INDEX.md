# Skills Index — PDLC_App_v2

**Project:** PDLC_App_v2 · **Owner:** V (Varun Munjal), JPMC Merchant Services AI Automation Team
**Authoritative source:** `REQUIREMENTS.md` (WHAT/WHY, D1–D11) → `TECH_SPEC.md` (HOW, the pinned
contracts) → `design/ADR-008-solution-intent-pivot.md` (normative for the pivot subsystems).
**This file is a catalog, not a contract.** Where it disagrees with a `.skill.md` frontmatter or a
`TECH_SPEC.md` section, **they win** — and that disagreement is a bug in this file.

**Supersedes:** the BRD/FRD-era catalog (ADR-008, accepted 2026-07-31) and, before it, the v1
8-layer L0–L8 index. Neither is authoritative; `brd_author`, `brd_validator`, `frd_author`,
`frd_validator` and the tag vocabulary no longer exist in any form.

---

## How to read this index

Every skill in the pipeline: **Data & context → Solution Intent v1 → enrichment (v2) → Jira →
Metrics.** Each entry names its **contract pointer** — the `.skill.md` that *is* the instruction
module, plus the spec section and any deterministic script that enforces it.

**Execution model.** A skill is loaded and executed **in-session by the selected agent** (Claude
Code or Copilot) reading its `.skill.md` against runtime input — **no direct Claude API call**
(FR-XS-04). Skills are generic engines; per-domain substance comes from the domain seam. Python is
*called by* agents for deterministic plumbing and scoring; it never drives the session.

### Skill types

| Type | Meaning |
|---|---|
| **Generation (interactive)** | drives a chat with the operator to produce an artifact; its own session, user-invocable |
| **Assessment (subagent)** | autonomous, non-interactive; files findings, decides nothing |
| **Validator (subagent)** | scores an artifact + evaluates hard preconditions; feeds a human gate, never advances it |
| **Worker (subagent)** | deterministic-adjacent fan-out work (per-source processing, code mapping, indexing) |
| **Interactive (operator turn)** | the walkthrough — proposes, never decides |
| **Adapter** | connector logic at a seam: per-source-type ingestion, and the `jpmc_adapters` push/auth seam |
| **Plumbing (Python)** | deterministic, model-free steps. Listed for completeness; not generation skills |
| **Runtime utility** | environment/bootstrap helpers applied locally (`max-autonomy`) |

### Cross-cutting patterns every skill respects

- **Two seams only (FR-XS-01).** The **domain seam** (`si_profile.<domain>.yaml` + `jira_template.<domain>.yaml` + the adapter pack) and the **runtime-tool seam** (instruction file / wrappers / prompt files / launch). Non-domain variation points: the per-language **extractor** (onboarding gate) and the per-repo **signal profile** (D11.4 gate). Nothing else varies.
- **In-session execution, no API** (FR-XS-04).
- **Always-selective read** (FR-DC-06). `context_set/index.json` is always loaded; agents pull only what a section needs — now through the **per-artifact `<doc>.index.json`** (D-A18), which is passage-level retrieval without a vector store.
- **Cite-or-flag.** Every substantive claim is grounded to a source / the `UI_INPUT` frame / an operator answer, or marked `[TBD — unsourced]`. Never fabricated.
- **Ingestion never branches on domain.** Routing is by the operator's **declared disposition** (D-A12), not by content the pipeline inferred.
- **The structural extractor is deterministic and frozen** — never model-rewritten at runtime. The map-build gate is **model-free**. The model owns only `purpose` *text*.
- **v1-as-spine.** G1 acceptance **freezes** `v1.md`; enrichment never edits it. `v1 + enrichment.json` reconstruct `v2` deterministically (D-A16) — which is what makes every touch traceable.
- **Human gates G0–G3**, each = a **soft score (informs)** + **hard preconditions (absolute)**. A validator never auto-advances (FR-XS-13).
- **Telemetry → JSONL → metrics.** Every stage emits to `telemetry.jsonl`; Layer 5 is computed by scanning it. No metric is hand-entered (FR-MX-01).

### The eight overlay roles (D-A23)

These — and only these — get a per-tool wrapper in both overlays. `overlay_manifest.yaml` is the
contract; `check_overlay_parity.py` enforces it (§10.2).

| Role | Skill file | User-invocable |
|---|---|---|
| `source_processor` | `core/skills/source_processor.skill.md` | no |
| `solution_intent_author` | `core/skills/solution_intent_author.skill.md` | **yes** |
| `solution_intent_validator` | `core/skills/solution_intent_validator.skill.md` | no |
| `code_impact` | `core/skills/code_impact_assess.skill.md` | no |
| `claim_verifier` | `core/skills/claim_verifier.skill.md` | no |
| `disposition_walkthrough` | `core/skills/disposition_walkthrough.skill.md` | **yes** |
| `jira_author` | `core/skills/jira_author.skill.md` | no |
| `jira_validator` | `core/skills/jira_validator.skill.md` | no |

Prompt files: `start-ingest`, `start-si`, `start-enrich`, `start-jira`.

**Not roles, deliberately.** `code_map_build`, `doc_index` and `pdf_extract` are real skills with
real contracts, but they are invoked *inside* `source_processor`'s two lanes — they are not operator
surfaces, so giving them wrappers would put eleven agents in front of an operator who needs eight.

---

# Layer 1 — Data & context

**Configure → ingest → pre-process → index → serve.** `source_processor` fans out one instance per
source; `merge_manifest.py` fans in deterministically to `context_set/index.json`.

### source_processor

- **Type:** Worker (subagent, fan-out — one instance per source, in parallel)
- **Consumes:** ONE source (a single `UI_INPUT.sources[]` entry) + the domain `adapter.yaml` (run order / routing only)
- **Produces:** that source's `context_set/<source>/` slice (`_slice.json`) + its manifest entries; code → `repo/` clone handed to `code_map_build`
- **Rules:** Split at the **source boundary**, never per file; failure-isolated (one source failing does not fail the batch); routes on the operator's declared disposition, never on inferred content (FR-DC-05, D-A12)
- **Contract:** `core/skills/source_processor.skill.md` · §6.6

### pdf_extract  *(domain pack — the domain seam)*

- **Type:** Pre-processing skill (`docs_pipeline` step 1)
- **Consumes:** a raw document (PDF) staged by the ingest connector
- **Produces:** `context_set/<source>/<doc>.md` — structural text extraction — plus a manifest-entry stub
- **Rules:** Structure only, no interpretation. It lives in the domain pack because *document formats* are a domain's problem; the indexing that follows is not
- **Contract:** `core/profiles/payment_brand/adapter/pdf_extract.skill.md` · §6.6.2/§6.6.3

### doc_index  *(shared core — the doc arm's twin of `code_map_build`)*

- **Type:** Pre-processing skill (`docs_pipeline` step 2)
- **Consumes:** one `<doc>.md` structural extract
- **Produces:** `<doc>.index.json` beside it — one entry per semantic subsection (heading, line range, summary)
- **Rules:** **Guardrail 7** — `lines_total == lines_indexed`, exactly-once coverage. Every line of the document is in exactly one entry, so "the index missed it" cannot be true (D-A18)
- **Contract:** `core/skills/doc_index.skill.md` · §3.2 · enforced by `core/scripts/checks/check_index_completeness.py`

### code_map_build

- **Type:** Worker (subagent) — invoked by `source_processor`'s code lane
- **Consumes:** the cloned repo · `code_profiles/<repo>.profile.yaml` (frozen at the onboarding gate) · the frozen per-language extractor
- **Produces:** `context_set/code_map/{components.json, files.json}`
- **Rules:** **Map, don't copy** (reference by path, never inline code); both dependency directions; module membership + edges are **deterministic** per the frozen signal profile; the model owns `purpose` **text** only. Cached through the **4-branch gate** keyed on `(commit_sha, profile_sha)` — a profile change invalidates wholesale, a commit change selectively
- **Contract:** `core/skills/code_map_build.skill.md` · §3.3, §5 · `core/scripts/{code_map_build,gate,map_cache}.py` · checked by `check_map_totality.py`

### Plumbing (Python — not generation skills)

| Piece | Does |
|---|---|
| `ingest_sharepoint.py` · `ingest_confluence.py` · `ingest_jira.py` · `ingest_file.py` · `clone.py` | per-source-type connectors. Each isolates its real API call in one `[TBD — VDI]` function (hard rule S); a new source type is a new generic connector, **never** a domain fork |
| `merge_manifest.py` | deterministic fan-in → `context_set/index.json`. Rejects unroutable entries and retired fields |
| `validate_onboarding.py` | the **D-A21 onboarding gate**: scan → report → three operator actions → freeze `extractor_sha` + `profile_sha` |
| `extractors/c_extractor.py` | the frozen tree-sitter-C structural extractor (ADR-001) |
| `hydrate.py` · `generate.py` · `publish_registry.py` | scaffold a run workspace from the published registry |

---

# Layer 2 — Solution Intent v1

Chat-driven authoring + validation → `solution_intent/v1.md`, **18 sections**, gated at G1.
Acceptance **freezes** v1 — everything downstream is a delta against a fixed document.

### solution_intent_author

- **Type:** Generation (interactive, chat-driven; own session, user-invocable via `start-si`)
- **Consumes:** `UI_INPUT.yaml` · `si_profile.<domain>.yaml` · `context_set/index.json` · the per-artifact `<doc>.index.json` indexes · the `<doc>.md` extracts
- **Produces:** `solution_intent/v1.md`
- **Rules:** **Code-blind by design.** v1 states intent from sources, the frame and the operator — it never reads the repo, because a v1 that already knew the code would leave enrichment nothing to *find*, and no way to tell a source's claim from a tool's inference. Generic engine (no domain content); always-selective read; cite-or-flag; §1 drafted last
- **Contract:** `core/skills/solution_intent_author.skill.md` · §3.7 · `core/profiles/payment_brand/si_profile.payment_brand.yaml`

### solution_intent_validator

- **Type:** Validator (subagent) — and, at G2, the enrichment scorer
- **Consumes:** `v1.md` · `si_profile.<domain>.yaml` · `context_set/index.json` + the extracts · `decisions.jsonl`
- **Produces:** a G1 report (score + breakdown + hard-precondition verdicts + gap list) + the G1 ledger records; at G2, the same for `enrichment.json`
- **Rules:** Soft-gate — **informs, never auto-advances**. Acceptance freezes v1 and stamps the freeze digest. Scoring is deterministic and model-free
- **Contract:** `core/skills/solution_intent_validator.skill.md` · §9.2/§9.3 · `core/scripts/solution_intent_validator.py`

---

# Layer 3 — Enrichment (v1 → v2)

Two arms run against the frozen v1, then **one** operator turn, then a deterministic apply pass.
Findings accumulate in `enrichment.json`; **provenance decides authority** (D-A16): a source-derived
error auto-corrects, an operator/frame claim **escalates**, an unsourced `[TBD]` auto-fills.

### code_impact — Arm 1 (requirement → code)

- **Type:** Assessment (subagent, fan-out — one instance per requirement)
- **Consumes:** frozen `v1.md` · `code_map/{components,files}.json` · `repo/`
- **Produces:** §16 derived-system-impact entries + gaps, as findings in `enrichment.json`
- **Rules:** Per-assertion impact plus **dependency closure** (both directions, to a fixed point); recommends, never decides; never auto-applies a scope change
- **Contract:** `core/skills/code_impact_assess.skill.md` · §3.7 · `core/scripts/tier_walk.py`

### claim_verifier — Arm 2 (claim → code)

- **Type:** Assessment (subagent)
- **Consumes:** frozen `v1.md` · `code_map/{components,files}.json` · `repo/`
- **Produces:** verdicts + staged corrections, as findings in `enrichment.json`
- **Rules:** Point lookup then **stop** — Arm 2 answers "is this claim true of the code?", it does not go exploring. Runs after Arm 1, which has already pulled the slices its claims usually need. An honest `unverifiable` is a valid verdict
- **Contract:** `core/skills/claim_verifier.skill.md` · §3.7

### disposition_walkthrough — the one operator turn

- **Type:** Interactive (user-invocable)
- **Consumes:** escalated findings in `enrichment.json` · `code_map/` · `repo/` (for interrogation)
- **Produces:** a disposition + **rationale** per escalated finding, in `enrichment.json` + `decisions.jsonl`
- **Rules:** **Propose, never decide.** Triage, don't enumerate; respect ordering dependencies (a finding that supersedes others is called first); **resumable** across sessions. `decisions.jsonl` is the only place the operator's rationale is written (D-A17)
- **Contract:** `core/skills/disposition_walkthrough.skill.md` · §3.7 · `core/scripts/enrichment.py`

### The apply pass (plumbing)

- **Type:** Plumbing (Python, deterministic)
- **Consumes:** frozen `v1.md` + `enrichment.json` → **Produces:** `solution_intent/v2.md`
- **Rules:** Corrections revise **in place with provenance**; discoveries append; **nothing is deleted**. §16 is organised by requirement, §17 extended never replaced, **§1 regenerated last** from the corrected body. Rejected and superseded findings do not reach v2 but stay in the record
- **Contract:** `core/scripts/apply_enrichment.py` · gated at **G2**

---

# Layer 4 — Jira

Decompose accepted `v2.md` into the **4-level JPMC hierarchy** (Initiative → Deliverable → Epic →
Story), validate the trace, then one gate and the run's **only external mutation**.

### jira_author

- **Type:** Generation (subagent)
- **Consumes:** accepted `solution_intent/v2.md` · `enrichment.json` · `jira_template.<domain>.yaml` · `UI_INPUT.jira`
- **Produces:** `jira_plan.json` — **drafted only; no write to Jira**
- **Rules:** The parent chain is built from the SI's **own ids** — the author never invents one, which is what makes the push idempotent. Assembly is deterministic; the **judgment** is a story's summary and its acceptance criteria
- **Contract:** `core/skills/jira_author.skill.md` · §3.8 · `core/scripts/jira_plan.py`

### jira_validator

- **Type:** Validator (subagent) — surfaces G3
- **Consumes:** `jira_plan.json` · `v2.md` (§16, §7) · `enrichment.json`
- **Produces:** a G3 report (score + hard checks + violations) + the G3 ledger records
- **Rules:** The **operator** accepts; acceptance authorises the push. Deterministic, model-free
- **Contract:** `core/skills/jira_validator.skill.md` · §9.4 · `core/scripts/jira_validator.py`

### jpmc_adapters — the push/auth seam

- **Type:** Adapter
- **Consumes:** an authorised `jira_plan.json` → **Produces:** created/updated issues + `jira_trace.json`
- **Rules:** The **only external mutation of a run**, so an un-gated push is impossible *by construction*: `push_plan` requires a `G3Authorization` that only `authorize()` can mint, and `authorize()` refuses an ineligible result. `dry_run=True` is the default. Parent before child; **idempotent by `local_id`**; each result recorded as it returns, so a mid-batch failure resumes rather than re-creates. The adapter returns data and **never writes the trace** — which keeps a crash between "wrote to Jira" and "wrote the trace" detectable. All auth isolated here; `auth_ref` is a pointer resolved at call time, never a secret on disk
- **VDI:** `_create_issue` / `_update_issue` are the two `[TBD — VDI]` placeholders — everything around them is real and proven offline (`VDI_WIRING.md`)
- **Contract:** `core/adapters/jpmc_adapters/{jira,auth}.py` · §7.1

---

# Layer 5 — Metrics

- **Type:** Derived (no skill)
- **Consumes:** `telemetry.jsonl` → **Produces:** M01–M07, M09–M12 (§8.2)
- **Rules:** Auto-computed by scanning telemetry; **no metric is hand-entered**. Run-properties are computed per run then averaged; M07 and M10 measure the fleet. A metric with no events yields **no value, never 0**. **M12 enrichment yield** — corrections + derived impacts + auto-fills — is the v1→v2 delta, and the reason `verdict.route` is on the event
- **Contract:** `core/scripts/metrics_scan.py` · §8.1/§8.2 · FR-MX-01/02

---

# Runtime / bootstrap

### max-autonomy

- **Type:** Runtime utility (user-invocable; a contract the agent applies locally — not a generation skill)
- **Consumes:** the operator's chosen mode (`maximum` / `balanced` / `safe default` / `add <command>`) + the VS Code **USER** `settings.json`
- **Produces:** updated user `settings.json` (Copilot terminal auto-approval) + one backup
- **Rules:** User scope only; the three presets are an exact contract; treat as JSONC, back up, validate after write, refuse a broken file; `maximum` must surface the risk statement (FR-XS-26)
- **Contract:** `docs/max-autonomy.skill.md`

---

# Build checks that keep this catalog true

| Check | Asserts |
|---|---|
| §10.2 overlay parity | every role + prompt in `overlay_manifest.yaml` is present in **both** overlays |
| §10.3 domain artifacts | the domain pack is complete for the declared domain |
| §10.4 connector coverage | every source type in `UI_INPUT` has a connector |
| §10.5′ disposition-class totality | every disposition routes somewhere, and `other` never routes |

Run: `python3 core/scripts/build_checks.py`. Per-skill behaviour is proven by the fixture verify
scripts under `fixtures/`; `fixtures/docs/verify_docs.py` proves this file's references resolve.

*End of Skills Index.*
