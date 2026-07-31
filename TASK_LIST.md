# TASK_LIST — PDLC_App_v2 (the single build list)

**The one task list.** Everything open lives here; everything done is a one-line ledger entry
below. Previously split across `TASK_LIST.md` / `TASK_VDI.md` / `TASK_VDI_BOOTSTRAPS.md` —
consolidated 2026-07-29. Full specs of completed tasks (TASK-000–063B) are in git history
(`f8f2ae1` and earlier); the pre-pivot open specs (TASK-056, 064–083) are at `0d7d8aa` and earlier.

**Re-cut 2026-07-31 (ADR-008 Phase D).** The open work below is rebuilt from
`docs/design/ADR-008-impact-analysis.md` (Phase C — every file classified keep/amend/retire).
The pipeline is now **Solution Intent v1 → enrichment → v2 → Jira (4-level)**. New tasks are
numbered **TASK-100+** so the retired numbers keep their historical meaning in git; see
"Disposition of the pre-pivot open tasks" before OPEN WORK.

**Where the work runs.** The cutover is built and proven **here** (external Claude Code build)
end-to-end over mock fixtures per source type (D-A24); the VDI port follows via `VDI_WIRING.md`.

**How to use it.** Pick the first unchecked task, top-down. Follow the **Execution protocol**.
Tick the box only when every Acceptance condition is true and the proof + build checks are
green. **Disk + git are ground truth** — never rely on something said in an earlier session.

---

## Execution protocol (run this loop for EVERY task)

1. **Read the cited design first.** Each task names the exact `docs/…` §sections and D-A blocks
   under **Reads** — open them. Do not work from memory; the cited section is the contract.
   (`ADR-008`'s D-A blocks are **normative** for the new subsystems until the spec's next
   consolidation — the TECH_SPEC banner says which sections they override.)
2. **Verify dependencies exist** (the **Depends on** files). If one is missing, stop and say so.
3. **Implement the GENERIC piece.** Build what is testable here. For anything that must hit a
   **real external API or secret store**, do NOT inline it — isolate it in **its own function**
   carrying a `[TBD — VDI]` placeholder (raises `NotImplementedError`), plus an **offline
   local-path convenience** so the piece runs end-to-end here (hard rule **S**). On the VDI that
   one placeholder function is edited in place (the way `_download_pdf` / `_fetch_confluence`
   were wired).
4. **Verify.** Run the task's **Proof**, then **`python core/scripts/build_checks.py`** — all
   **registered** §10 checks must be green (3 checks during the cutover after TASK-100; 4 from
   TASK-108 when §10.5′ registers). A connector also runs its `fixtures/<type>/verify_*.py`.
5. **Publish — ⏸ SUSPENDED during the cutover.** Re-publishing mid-cutover would ship a
   half-re-cut core; the published `registry_sha` keeps serving the old pipeline until the new
   one is whole. The publish + re-Generate step **resumes at TASK-127** (acceptance), which
   re-publishes and re-tests the UI path end-to-end.
6. **Tick the box** and commit (and push, so the external copy stays current).

> ✅ **A task is done when:** Acceptance true · its proof green · `build_checks.py` (registered
> checks) green · box ticked · committed.

---

## Hard rules (never violate — condensed from `CLAUDE.md` / `docs/` / ADR-008)

- **S. Build-and-port / edit-in-place discipline.** Generic code is shared and built+tested first;
  any real API/secret is **isolated in its own function** carrying a `[TBD — VDI]` placeholder
  (raises `NotImplementedError`) plus an **offline local-path convenience**. On the VDI you **edit
  that one placeholder function in place** — **no `/vdi` plugin folder, no auto-load hook.**
  (V decision 2026-06-30; extended to everything ADR-008 adds by D-A24.)
- **Two seams only (FR-XS-01).** The **domain seam** (adapter pack / `si_profile` /
  `jira_template` — the vocabulary is deleted) and the **runtime-tool seam** (instruction file /
  wrappers / prompts / launch). Non-domain variation points: the per-language **extractor**
  (`extractor_manifest`, onboarding-gated) and the per-repo **signal profile**
  (`code_profiles/<repo>.profile.yaml`, D11.4 gate). Nothing else varies.
- **Binding rationales.** The structural extractor is **deterministic + frozen** — never
  model-rewritten at runtime. Map **structure** (partition, edges, hub exclusion, module
  clustering, membership) is **deterministic**; modules exist **before** any purpose is written;
  the model owns only **text** — file/module `purpose` prose and doc-index summaries. The
  map-build **gate is model-free** (4 branches on `(commit_sha, profile_sha)`). Gate actions are
  **pre-freeze only**: approved model proposals freeze into the profile **as data**
  (propose-never-bless). **Ingestion never branches on `domain`** (routing by operator-declared
  `disposition` is config, not domain logic). **Enrichment never deletes** (corrections rewrite in
  place, with provenance); findings that are ambiguous, scope-moving, or would overrule a human
  **escalate — never auto-apply**. The **only** external mutation of a run is the Jira push
  (G3-gated, operator-confirmed). Scope changes are **operator-decided**.
- **Totality — never silently exclude.** Every file is in exactly one module or `unclustered`;
  every file has a purpose or is listed `unanalyzable[]`; every extract line is inside exactly one
  index entry. Silent invisibility is the failure mode this design exists to prevent — declare
  residue, never hide it (D-A19/D-A18, family-2 checks).
- **Descriptor parity.** Every source connector emits the **same descriptor shape** as
  `ingest_file.py` (`type, source, url/…, staged_path, auth_ref, ingest_ts`).
- **Cite-or-flag.** Every substantive artifact claim grounds to a source/frame/operator answer or
  is `[TBD — unsourced]`. Provenance classes drive enrichment correction authority (D-A6):
  source-derived → auto-correct; operator/frame → escalate; `[TBD]` → auto-fill. `Prior Artifact`
  is reference-only; `Other` is never a sole citation.
- **§10 must stay green.** No task lands with a red **registered** check. §10.2 parity, §10.3
  domain artifacts, §10.4 connectors always; §10.5′ disposition-class totality from TASK-108.
- **Ladder discipline.** If a task would change a pinned contract or reopen **D1–D11** (or an
  ADR-008 D-A block), **stop and flag it** — unless the task explicitly says it is a ladder
  amendment, in which case amend the design *as part of the task* and add the port note.

---

## VDI environment notes

- **Python deps.** Scripts need `httpx` + `PyYAML`; extractor tasks also need
  `tree-sitter==0.25.2` + `tree-sitter-c==0.24.2` (ADR-001). No venv is assumed.
  Check: `python -c "import httpx, yaml"`.
- **Auth (the seam, env backend).** User env vars: `PDLC_AUTH_BITBUCKET` (+ `_USER`),
  `PDLC_AUTH_SHAREPOINT` (+ `_USER`), `PDLC_AUTH_CONFLUENCE`, `PDLC_AUTH_JIRA`. The token never
  lands on disk — `auth_ref` is a pointer.
- **Registry / code repos.** Registry = `feature/pdlc_app`; Stratus code = `feature/c_repo`
  (one Bitbucket repo, two branches). Re-publish resumes at TASK-127.
- **Copilot layout (already fixed).** Generate emits `.github/copilot-instructions.md` +
  `.github/prompts/*.prompt.md`; agents are `*.agent.md` at the run root.

---

## Citation key

`FR-…` / `NFR-…` / `D1`–`D11` → `docs/REQUIREMENTS.md` · `§n.n` → `docs/TECH_SPEC.md` ·
`D-A n` → `docs/design/ADR-008-solution-intent-pivot.md` · `ADR-00n` → `docs/design/` ·
`impact §n` → `docs/design/ADR-008-impact-analysis.md` · **Model key:** `Sonnet` = default ·
`Opus` = deep design artifact or a mistake that propagates far.

---

## Standing port note (not a numbered task)

**Real JPMC host / secret validation.** The auth seam (TASK-052), live Bitbucket clone
(TASK-054), and the SharePoint/Confluence connectors exist; what remains is binding `auth_ref` to
the **real JPMC secret store** and validating live endpoints — an in-place edit of each
connector's placeholder per hard rule **S**, done as connectors land on the VDI (FR-DC-02/11/12,
§7). See `VDI_WIRING.md`.

---

# Done ledger (TASK-000 – 063B)

> One line per completed task. Full specs are in git history (`f8f2ae1` and earlier).
> This is what a fresh session reads to know what exists without re-deriving it.
> ⚠ **Post-ADR-008 reading note:** entries describing vocabulary/tag/BRD/FRD machinery record
> *what was built then*; much of it is retired or recast by the D-milestones below — the impact
> analysis says which. The ledger is history, not current architecture.

**Setup · Phase 0 (UI design, chat/JSX only)**
- [x] TASK-000 — Repo scaffold: directory tree, .gitkeeps, initial git commit
- [x] TASK-001 — UI pattern library: locked interaction patterns every screen composes from
- [x] TASK-002 — UI screens → locked `UI_INPUT.yaml` contract

**Phase 1 — Pre-tasks**
- [x] TASK-003 — PDF fixtures: 2× Mastercard mandate PDFs + `expected_manifest_entries.json` oracle
- [x] TASK-004 — Synthetic Stratus C repo: fn-pointer dispatch, macros, `#ifdef` patterns
- [x] TASK-005 — Hand-authored `expected_code_map.json` — human-signed-off oracle grading TASK-012
- [x] TASK-006 — C extractor tooling check (`tree-sitter`/`tree-sitter-c`, ADR-001) → `ENV_PRECHECK.md`
- [x] TASK-007 — Copilot/VDI validation PASSED 2026-06-16, recorded (no re-run needed)
- [x] TASK-008 — Language detection + partition + dispatcher; normalization contract → §3.3 shape
- [x] TASK-009 — C extractor: tree-sitter → structural fields only; blindspots → `coverage: coarse`
- [x] TASK-010 — Model fallback over a file set (whole-repo + polyglot residue) → `files_fallback`
- [x] TASK-011 — Model enrichment: `purpose`+`tags` only; deterministic `merge_edges`; vocab assert
- [x] TASK-012 — Validate vs oracle; coverage floor 0.80; human freeze; `onboarding_manifest.yaml`
- [x] TASK-013 — 3-branch gate (model-free) + `REONBOARD_FLAG` + L1 vocab-adequacy detector + `vocab_sha`
- [x] TASK-014 — `vocabulary.payment_brand.yaml` — D5 transcribed (12 tags, emitted-by mapping)
- [x] TASK-015 — `brd_profile.payment_brand.yaml` — `must_capture` + `probe_if_missing` per topic
- [x] TASK-016 — `frd_profile.payment_brand.yaml` — same shape + `functional_kind` + `traces_to`
- [x] TASK-017 — `adapter.yaml` pack manifest + `pdf_extract` skill; **F1 (+3) emit-map drifts reconciled** (V-approved; see `CLAUDE.md`)
- [x] TASK-018 — `article_summarize` skill
- [x] TASK-019 — `change_type_assess` skill — **later removed**; `article_summarize` is the sole doc tagger (commit `5c7ac33`)
- [x] TASK-020 — Source-type-keyed connectors: `clone.py` (Bitbucket) + `ingest_file.py` (direct-file PDF)
- [x] TASK-021 — §10.3/10.4/10.5 domain-seam build checks green; F1 reconciled

**Phase 2 — Core scaffold & runtime-tool seam**
- [x] TASK-022 — `runs/_template/` workspace + JSON-schema validators for the 3 ledger files
- [x] TASK-023 — `merge_manifest.py`: deterministic fan-in → `index.json`; failed sources marked, never dropped
- [x] TASK-024 — `hydrate.py`: clone + checkout `registry_sha` + selective copy into the run scaffold
- [x] TASK-025 — `overlay_manifest.yaml` (D9): 8 roles, prompt files, per-tool launch
- [x] TASK-026 — `instruction_file.template.md` → `CLAUDE.md` or `copilot-instructions.md` by `runtime_tool`
- [x] TASK-027 — Claude overlay: 8 thin agent wrappers → shared `core/skills/`
- [x] TASK-028 — Claude overlay: prompt files + `terminal_interactive` launch
- [x] TASK-029 — Copilot overlay: parity twin of TASK-027 (native syntax)
- [x] TASK-030 — Copilot overlay: parity twin of TASK-028 (`agent_mode` launch, `Ctrl+N` gesture)
- [x] TASK-031 — `generate.py`: deterministic Generate → run workspace + instruction file + G0
- [x] TASK-032 — `telemetry.py`: `emit()` + `decisions.jsonl` + `run_state.json` over all §8.1 events
- *(D9 amendment, V-approved: `start-ingest` added as the Layer-1 kickoff; start gesture repointed `start-brd → start-ingest`. See `CLAUDE.md`.)*

**Phase 3 — The spine**
- [x] TASK-033 — `source_processor` skill: failure-isolated fan-out; reads `adapter.yaml`; no domain knowledge
- [x] TASK-034 — Doc pipeline over the PDF fixtures; entries verified vs `expected_manifest_entries.json`
- [x] TASK-035 — Clone SEAL-ID repo + `merge_manifest.py` → `index.json` with `sources_status`
- [x] TASK-036 — `code_map_build` skill: frozen extractor through the 3-branch gate → `code_map.json`
- [x] TASK-037 — `brd_author`: baseline+profile merge + discovery framing + seed coarse code pass
- [x] TASK-038 — `brd_author`: per-section loop; §3.2 selective read; `must_capture`; probes; coverage footer
- [x] TASK-039 — `brd_author`: cite-or-flag grounding; revisit/shared memory (never re-ask)
- [x] TASK-040 — `code_impact` coarse pass: map-only; topics × tags → ranked candidate areas
- [x] TASK-041 — `code_impact` deep pass: flagged-slice read; real closure; Flags every run
- [x] TASK-042 — `brd_author` flag loop: surface→wait→apply→conditional re-run; material vs advisory (D6c)
- [x] TASK-043 — `brd_validator` + G1: `0.7×topic_coverage + 0.3×citation_integrity` + hard preconditions
- [x] TASK-044 — `frd_author`: consume accepted BRD; `traces_to`; carry file/function detail forward
- [x] TASK-045 — `frd_validator` + G2: `0.5×traceability + 0.5×testability`; every BRD requirement traced

**Phase 4 — Build harness & acceptance**
- [x] TASK-046 — §10.1 `check_vocab_containment.py`
- [x] TASK-047 — §10.2 `check_overlay_parity.py`
- [x] TASK-048 — `build_checks.py` runner (all five) + `metrics_scan.py`
- [x] TASK-049 — Spine end-to-end acceptance: PDF + repo → BRD vN → FRD; flag loop + G1 reopen; §10 green
- [x] TASK-050 — Generate backend service (FastAPI): config → `UI_INPUT.yaml` → `generate.py` (G0)
- [x] TASK-051 — React Run Configurator (5 tabs) → emits §3.1 `UI_INPUT.yaml`; Generate + hand-off
- [x] TASK-052 — `jpmc_adapters/auth.py` real `resolve_auth` (auth_ref → secret store)
- [x] TASK-053 — Registry (repo #1) on Bitbucket + hydrate-from-remote at pinned `registry_sha`
- [x] TASK-054 — Live Bitbucket code-source clone (repo #2) through the auth seam; `commit_sha` pinned
- [x] TASK-055 — `ingest_sharepoint.py` — SharePoint PDF connector; `_download_pdf` is the VDI placeholder

**Phase 5 · Milestone 5B — carried fixes + connectors**
- [x] TASK-060 — `runtime_tool` threaded through G1/G2 telemetry — `_runtime_tool(ledger_dir)` helper in both validators reads the run's sibling `UI_INPUT.yaml`; copilot runs record `tool: copilot`. *(built+verified external; pending VDI port)*
- [x] TASK-061 — D5 `card_brand`/`message_format` `emitted_by` reconciled — D5 table now matches `vocabulary.yaml` on all 12 tags; §10.5 green. **JPMC-side D5 still to fix at port.**
- [x] TASK-062 — `UI_INPUT.example.yaml` frame alignment — **skipped by V decision 2026-06-30.** Cosmetic only; superseded by the TASK-103 re-cut.
- [x] TASK-063 — Confluence connector `ingest_confluence.py` — mirrors `ingest_sharepoint.py`; `pull_page()` emits the exact `ingest_file` descriptor; `_fetch_confluence` is the lone `[TBD — VDI]` placeholder (`set_fetcher` seam for tests); lazy auth; `main()` stages multiple pages (one link = one page). Fixtures `fixtures/confluence/{discover_routing_kb,message_format_kb}.html` + `verify_confluence.py` (13 checks). **VDI:** edit `_fetch_confluence` with the real REST call + auth; no other change.
- [x] TASK-063B — Per-source-type doc-pipeline routing — two-lane `docs_pipeline` + `confluence_tag` + §10.5 lane union. *(Mechanism retired by ADR-008/D-A19 at TASK-100/105 — routing is now by operator disposition; the connector + UI row survive.)*

**Phase D · Milestone D0 — Cutover groundwork**
- [x] TASK-100 — Retirement sweep: 41 ⛔ files deleted (`frd_*` skills/validator, vocabulary + taggers, vocab checks, BRD/FRD + tag-lane fixtures, seed docs + `brd_frd_overview.html`, old run workspace); `build_checks.py` re-cut to §10.2/10.3/10.4 (§10.3 requires `brd_profile` transitionally); ADR-003/004/005 superseded-by banners; `--demo` re-cut and green
- [x] TASK-101 — Manifest split (D-A22): `extractor_manifest.yaml` (per-language freeze, schema v2) + `cache/` home (`code_maps/index.yaml` contract in `cache/README.md`; gitignored; old `repos[]` record NOT migrated — it described the pre-profile tagged map); `registry_manifest.yaml` shrunk to `trees: [core/, overlays/, docs/]` (schema v2); `onboarding_manifest.yaml` deleted; `validate_onboarding.py`/`gate.py` repointed (full recasts stay TASK-113/115). Proof: reference grep empty, staged publish 94 files w/ green gate + correct boundary, §10 3/3
- [x] TASK-102 — Runtime-tool seam re-cut: `overlay_manifest.yaml` transcribed from D11.7 (8 roles — `solution_intent_*` ← `brd_*`, + `claim_verifier`/`disposition_walkthrough`, `frd_*` out; `prompt_files [start-ingest, start-si, start-enrich, start-jira]`; invocability = D-A23 interactive set); renames landed (skills + `solution_intent_validator.py` + wrappers + prompts, both tools) with identifier swaps; 4 new-role wrappers + 4 skill stubs (`claim_verifier`/`disposition_walkthrough`/`jira_author`/`jira_validator` — full content TASK-119/120/122/123); `instruction_file.template.md` stage narrative re-cut to SI→enrichment→Jira; `generate_instruction.py` gestures re-pointed; parity `_demo` re-cut. Proof: §10.2 green (8+4 both tools), demo green, §10 3/3, no `brd_`/`frd_` filename remains, every wrapper pointer resolves

---

## Disposition of the pre-pivot open tasks (TASK-056, 064–083 — none carries over verbatim)

Full old specs at `0d7d8aa` and earlier. Per ADR-008 / impact §13:

| Old | Disposition |
|---|---|
| 056 self-serve acceptance | surviving half ("the pipe works via the UI") → **TASK-127** (D-A0) |
| 064 / 065 Jira | re-cut for the 4-level hierarchy → **TASK-122–124** (D-A15) |
| 066 purpose-as-discovery | **absorbed** — D-A19's tier walk *is* purpose-first matching; refinement (d) became the query contract |
| 067 doc-side gap signal | **absorbed** — the per-artifact index is the doc-side symmetry (D-A18 closes ADR-005 open-Q #2) |
| 068 multi-repo closure | **deferred** (candidates below) — merged with cross-language closure: one capability (D-A19) |
| 069 extractor onboarding (2nd language) | **deferred** — cleaner now via `extractor_manifest` + per-repo profiles (ADR-006 stands) |
| 070–074 domain-onboarding chain + multi-domain | **deferred, re-scoped** — no vocabulary step; a new domain = `si_profile` + `jira_template` + adapter pack |
| 075 vocab_gap_assess | **dead** — no vocabulary (D-A22) |
| 076 metrics store · 077 auto-launch · 078 UI enhancements | **deferred** unchanged in spirit |
| 079 discovery adequacy | **promoted to core** by D-A13 → **TASK-111** |
| 080 closure depth verification | **folded** into TASK-118's acceptance (fixed point, both directions, source-extends) |
| 081 pre-G1 auto-fill | **arrived via D-A6** — `[TBD]` auto-fill is enrichment's third authority row (TASK-117/121) |
| 082 section-as-subprocess | **kept deferred** (applies to SI authoring at overflow scale) |
| 083 chunk-level granularity | **dead** — the per-artifact index *is* passage-level retrieval (D-A18) |

---

# OPEN WORK

## Open index (tick here; then collapse the task into the done ledger above)

**Milestone D1 — Input side (UI_INPUT, routing, index, Jira ingest)**
- [ ] TASK-103 — `UI_INPUT` v2: dispositions + `frame.overview` + run scaffold · `Sonnet`
- [ ] TASK-104 — Ledger stages + enrichment event vocabulary · `Sonnet`
- [ ] TASK-105 — Manifest v2 + disposition routing + adapter shrink · `Sonnet`
- [ ] TASK-106 — Per-artifact index + completeness (guardrail 7) · `Opus`
- [ ] TASK-107 — `ingest_jira.py` connector (Prior Artifact source type) · `Sonnet`

**Milestone D2 — Solution Intent v1**
- [ ] TASK-108 — `si_profile` (18 sections) + §10.5′ disposition-class totality · `Opus`
- [ ] TASK-109 — `solution_intent_author` recast · `Opus`
- [ ] TASK-110 — `solution_intent_validator` + G1 + v1 freeze · `Opus`
- [ ] TASK-111 — Discovery-question adequacy (promoted by D-A13) · `Opus`

**Milestone D3 — Code map v2**
- [ ] TASK-112 — Extractor declared-purpose extraction + `c_repo` additive pass · `Sonnet`
- [ ] TASK-113 — Repo profile scan + onboarding gate report (D-A21 phase 1) · `Opus`
- [ ] TASK-114 — Map build recast (two files, modules, purposes) + context checks · `Opus`
- [ ] TASK-115 — 4-branch gate + map cache · `Opus`
- [ ] TASK-116 — Multi-language validation fixture (required, D-A19) · `Opus`

**Milestone D4 — Enrichment (v1 → v2)**
- [ ] TASK-117 — `enrichment.json` contract + finding routes · `Opus`
- [ ] TASK-118 — Arm 1: per-assertion impact (`code_impact` recast) · `Opus`
- [ ] TASK-119 — Arm 2: `claim_verifier` · `Opus`
- [ ] TASK-120 — Disposition walkthrough · `Opus`
- [ ] TASK-121 — Apply pass + G2 + enrichment spine exercise · `Opus`

**Milestone D5 — Jira (4-level plan + the only external mutation)**
- [ ] TASK-122 — `jira_author` + `jira_template` (4-level plan) · `Opus`
- [ ] TASK-123 — `jira_validator` + G3 · `Opus`
- [ ] TASK-124 — Jira push seam + `jira_trace.json` · `Opus`

**Milestone D6 — Metrics, docs, acceptance**
- [ ] TASK-125 — `metrics_scan` re-cut (amended FR-MX-02) · `Sonnet`
- [ ] TASK-126 — Docs re-cut (`SKILLS_INDEX`, `BUILD_OVERVIEW`, `design/README`, `CLAUDE.md`) · `Sonnet`
- [ ] TASK-127 — End-to-end acceptance + registry re-publish (lifts the publish suspension) · `Opus`

---

## Milestone D1 — Input side

### TASK-103 — `UI_INPUT` v2: dispositions + `frame.overview` + run scaffold
- **Depends on:** TASK-102.
- **Model:** Sonnet — the contract is fully specified.
- **Reads:** §3.1 (amended) · §2.2 · D-A12 (taxonomy, `Codebase` auto, `Other` second-class,
  multi-disposition) · D-A13 (`overview`'s two jobs) · impact §6.
- **Creates / edits:** `core/scripts/generate.py` (validate the amended §3.1; scaffold gains
  `solution_intent/`); `app/backend/{app,service,validation}.py`;
  `app/frontend/src/PDLCConfigurator.jsx` (per-source disposition selector — 6 operator classes,
  multi allowed, defaults to one; repo rows show auto-set non-editable `Codebase`; `Other` marked
  "background only — not citable"; Initiative Overview textarea in the frame tab);
  `app/frontend/src/emit.js` + `scripts/emit_cli.mjs`; `fixtures/UI_INPUT.example.yaml`;
  `fixtures/frontend/{sample_form.json,verify_frontend.py}`;
  `fixtures/generate/{verify_generate,verify_backend}.py`; `runs/_template/` (add
  `solution_intent/.gitkeep`).
- **Acceptance:** emitted `UI_INPUT.yaml` carries `disposition:` per doc source + `frame.overview`;
  backend rejects a doc source with missing/unknown disposition; repo rows auto-`Codebase`;
  Generate produces the §2.2 scaffold with `solution_intent/`; all four verifies green.
- **Proof:** `verify_frontend.py` + `verify_generate.py` + `verify_backend.py` green.

### TASK-104 — Ledger stages + enrichment event vocabulary
- **Depends on:** TASK-103.
- **Model:** Sonnet.
- **Reads:** §3.4–3.6 (banner note) · §8.1 · D-A16/17 (what a disposition record carries).
- **Creates / edits:** `core/scripts/telemetry.py` + `schemas/{telemetry,run_state,decisions}.schema.json`
  + `decisions.py`: `run_state` stages → `ingest / si_v1 / enrichment / si_v2 / jira`; new events
  `verdict`, `escalation`, `disposition` (+ enrichment stage start/end); `decisions.jsonl` gains
  the walkthrough record (finding id, operator call, rationale); `runs/_template/ledger/` refreshed.
- **Acceptance:** schema validators accept the new events/stages and reject the old stage names;
  existing emit() call sites still validate.
- **Proof:** schema round-trip on fixture events; template ledger validates.

### TASK-105 — Manifest v2 + disposition routing + adapter shrink
- **Depends on:** TASK-103.
- **Model:** Sonnet.
- **Reads:** §3.2 (amended — entry shape + replaced routing rule) · D-A12/13 · §6.6.3 (amended) ·
  impact §§2, 4, 7.
- **Creates / edits:** `core/scripts/merge_manifest.py` (entries: drop `topics`/`change_type`;
  gain `disposition` — copied from `UI_INPUT`, and `index_path` — populated once TASK-106 emits
  it, null until then; `sources_status` semantics unchanged — failed sources marked, never
  dropped); `core/skills/source_processor.skill.md` (route by source *type* to a connector and by
  the run config's *disposition* into the manifest — code sources → code lane, doc sources →
  extract lane; **no tag lanes; never branches on `domain`**);
  `core/profiles/payment_brand/adapter/adapter.yaml` (drop `emits` + the two-lane
  `docs_pipeline`; keep the pack pointers: `pdf_extract`, `code_pipeline → code_map_build`);
  `pdf_extract.skill.md` (strip emit/tag references — extraction contract itself unchanged,
  D-A18); re-cut `fixtures/merge_manifest/` (5 files) + `fixtures/pdf/expected_manifest_entries.json`
  + `fixtures/confluence/verify_confluence.py` (drop tag assertions).
- **Acceptance:** `index.json` entries carry `disposition` (+ `index_path` field); no `topics`/
  `change_type` anywhere in the ingest path; `grep -rn "emits" core/profiles` empty; fixtures green.
- **Proof:** merge over the mock corpus → expected entries match; verifies green.

### TASK-106 — Per-artifact index + completeness (guardrail 7)
- **Depends on:** TASK-105.
- **Model:** Opus — index/summary quality is what selection quality rests on.
- **Reads:** D-A18 (**whole block**: two files, shape, four rules, always-summarize decision,
  whole-read threshold-over-the-set, grouping/iteration, selection kept simple, degraded case) ·
  FR-SI-03 · §3.2.
- **Creates / edits:** the doc-lane index step in `source_processor.skill.md` — for every doc
  artifact, emit `<extract>.index.json` beside the `.md` (one entry per semantic subsection:
  `id`, `heading`, `lines`, model-written `summary`; `subdivided[]` for synthetic splits; keyed on
  the structure `pdf_extract` already produces — **the index describes the document, never the
  destination**); `core/scripts/checks/check_index_completeness.py` (family 2, run at ingest —
  `lines_total == lines_indexed`, every line in exactly one entry); whole-read threshold as a
  config value (default ~500 lines, checked across the routed **set**); index oracles for the two
  PDF extracts + two Confluence pages; the **degraded case** exercised against the real fixture
  PDFs (flat prose → boundaries synthesised by paragraph grouping, recorded, never silent).
- **Acceptance:** every doc artifact has a complete index (checker green); `index_path` populated
  in `index.json`; summaries carry specifics (spot-check vs the oracle); degraded case produces a
  total index too.
- **Proof:** ingest the mock corpus → 4 `.index.json` files, completeness green, oracles match.

### TASK-107 — `ingest_jira.py` connector (Prior Artifact source type)
- **Depends on:** TASK-103.
- **Model:** Sonnet — mirrors TASK-063's shape.
- **Reads:** D-A24 (mock table) · §6.6.2 · `ingest_confluence.py` (the pattern) · impact §12.
- **Creates / edits:** `core/scripts/ingest_jira.py` (`_fetch_issue` is the lone `[TBD — VDI]`
  placeholder; `set_fetcher` test seam; lazy auth via `PDLC_AUTH_JIRA`; issue payload → staged
  `.md` extract; exact descriptor parity); `fixtures/jira/{issue payload mock(s),verify_jira.py}`;
  UI: a Jira source row (disposition defaults `Prior Artifact`) in `PDLCConfigurator.jsx` +
  `emit.js` + `verify_frontend.py`; §10.4 connector inventory gains the `jira` row.
- **Acceptance:** mock fetch → staged extract + descriptor byte-shape-identical to the other
  connectors; §10.4 green including `jira`; UI emits the row.
- **Proof:** `fixtures/jira/verify_jira.py` green; `build_checks.py` green.

---

## Milestone D2 — Solution Intent v1

### TASK-108 — `si_profile` (18 sections) + §10.5′ disposition-class totality
- **Depends on:** TASK-102.
- **Model:** Opus — `must_capture` authoring quality is load-bearing (it is both the G1 checklist
  and the retrieval query, D-A18).
- **Reads:** D11.1 · D-A3 (section table) · D-A4 (binding rules) · D-A10 (conditional statuses) ·
  D-A11 (boundary statements) · D-A13 (the routing matrix — transcribe exactly) · §10.5′ · §10.3.
- **Creates / edits:** `core/profiles/payment_brand/si_profile.payment_brand.yaml` — per section:
  `id` (1–18), `title`, `authored` (v1 / v2-only / v1-extended-in-v2), `touch` (D-A3 enrichment
  touch type), `status` (required / required-may-be-empty / conditional), `classes` (the D-A13 row:
  each input source marked P/S/E), boundary one-liner (§4/§9/§15), `must_capture[]`,
  `probe_if_missing[]`. Delete `brd_profile.payment_brand.yaml`. New
  `core/scripts/checks/check_disposition_totality.py` (§10.5′: every section has ≥1 routed input
  class; every operator-selectable class in the UI taxonomy appears in ≥1 section row) — register
  in `build_checks.py` (now 4 checks); §10.3 swaps `brd_profile` → `si_profile`.
- **Acceptance:** profile matrix is cell-identical to D-A13; §10.5′ green against the UI's
  taxonomy list; §10.3 green; `build_checks.py` reports 4/4.
- **Proof:** `build_checks.py` 4/4 green; a deliberate matrix-cell deletion turns §10.5′ red.

### TASK-109 — `solution_intent_author` recast
- **Depends on:** TASK-106 (index), TASK-108 (profile).
- **Model:** Opus — the central authoring artifact.
- **Reads:** §3.7 (replaced — on-disk contract) · D-A2 (v1 frozen; placement rule) · D-A3/4
  (sections + binding rules) · D-A8 (the §8 schema: title/description/**assertions**,
  agent-extracted) · D-A10 (dispositions proposed, operator-confirmed at G1) · D-A11 (boundaries)
  · D-A13 (funnel level 1) · D-A14 (initiative level; §7 before §8; stable IDs `D1…`/`R1…` +
  `deliverable:` refs) · D-A18 (funnel level 2: index selection by `must_capture`; whole-read over
  the set; sequential groups carrying the draft; termination) · FR-SI-01…07.
- **Creates / edits:** `core/skills/solution_intent_author.skill.md` full recast (the TASK-102
  rename holds the old BRD content until now): discovery framing carried (FR-BR-02/03/05
  semantics — up-front questions, per-section probes, never re-ask); the two-level funnel;
  section loop over the 18-section contract with coverage footers; assertions extracted per
  requirement; conditional sections dispositioned with reasons; §17 accrues `[TBD]` gaps; §1
  authored last; cite-or-flag with provenance classes (`Prior Artifact` reference-only, `Other`
  never sole citation); the flag loop carried (surface→wait→apply, material vs advisory). Wrapper
  contents ×2 tools refreshed to describe the SI role.
- **Acceptance:** in-session authoring over the mock corpus (2 PDFs + 2 Confluence pages +
  `c_repo`, dispositioned per D-A12) produces a v1 with: all 18 sections present-or-dispositioned;
  every §8 requirement carrying `deliverable:` + enumerated assertions; stable IDs; per-section
  coverage footers; every citation resolving to an index entry/line range or flagged.
- **Proof:** the authored fixture v1 + its citation spot-check.

### TASK-110 — `solution_intent_validator` + G1 + v1 freeze
- **Depends on:** TASK-109, TASK-104.
- **Model:** Opus.
- **Reads:** §9.2 (replaced) · D-A23 family 3 (G1 rows) + scoring · D-A10 (precondition) · D-A2
  (v1 snapshot at G1) · `gate.py` (reused unchanged, D-A1) · FR-SI-\*.
- **Creates / edits:** `core/skills/solution_intent_validator.skill.md` +
  `core/scripts/solution_intent_validator.py` recast: score `0.7×section_coverage +
  0.3×citation_integrity` (section_coverage = satisfied `must_capture` / total, per profile);
  hard preconditions — every required section satisfied; every conditional section filled or
  dispositioned-with-reason; §15→§4 total + every objective measurable; §7→§8 total (no orphan
  requirement/deliverable); every requirement has ≥1 assertion; flags dispositioned. On operator
  G1 accept: snapshot `solution_intent/v1.md` (immutable), telemetry G1 events (`runtime_tool`
  threading kept). New `fixtures/si_validator/{si_pass.md,si_fail.md,README.md}`.
- **Acceptance:** pass/fail fixtures score correctly (fail names each violated precondition);
  the D4 principle holds — score informs, operator accepts; v1 freeze happens exactly at accept.
- **Proof:** validator over both fixtures + a G1 accept on the TASK-109 v1 → `v1.md` snapshot.

### TASK-111 — Discovery-question adequacy (promoted by D-A13)
- **Depends on:** TASK-108, TASK-109.
- **Model:** Opus — assessment-first; propose-never-bless.
- **Reads:** D-A13 ("discovery is primary for exactly §9/§12/§13 — their quality rests entirely
  on question quality") · `si_profile` · the author skill's discovery passes · old TASK-079 spec
  (git `0d7d8aa`) for the method.
- **Do:** Inventory where questions originate (up-front framing + per-section probes). For every
  discovery-primary or frame-supporting section — §9/§12/§13 first — map each `must_capture` to
  an eliciting question or flag the gap; findings artifact cited to profile/skill lines; propose
  the closing profile/skill diff for human freeze.
- **Acceptance:** written coverage assessment; no `must_capture` in §9/§12/§13 without an
  eliciting question after the frozen diff; sparse-source proof below.
- **Proof:** author over deliberately sparse sources → probes fire for the silent topics.

---

## Milestone D3 — Code map v2

### TASK-112 — Extractor declared-purpose extraction + `c_repo` additive pass
- **Depends on:** TASK-101 (`extractor_manifest`).
- **Model:** Sonnet — deterministic parsing + fixture authoring; the contract is precise.
- **Reads:** D-A20 (header form, label variance table, fuzzy matching, parser noise) · D-A19
  (steps 1–2) · §3.3 (amended) · V-flag 4 resolution (targeted subset) · impact §§4, 7.
- **Creates / edits:** `core/extractors/c_extractor.py`: extract the leading comment block; parse
  declared-purpose fields against a **label alias set passed in** (profile data — default set for
  pre-profile runs), fuzzy enough for the real typos; emit `purpose_declared`,
  `declared_version`/`declared_date` where parseable; structural fields unchanged; still no tags.
  Bump `extractor_sha` in `extractor_manifest.yaml` (a build-time re-freeze, never runtime).
  `fixtures/c_repo`: declared headers on ~60% of files under varied labels (`PURPOSE`,
  `Intention`, `Description`, `Desc`, one `Putpose` typo), ~40% left headerless (exercises rungs
  B/C/C\*); one versioned-duplicate pair (e.g. `msg_format.c` + `msg_format_v2.c`, both wired);
  `PATTERN_CATALOG.md` updated.
- **Acceptance:** two extraction runs byte-identical; the typo label is caught; headerless files
  emit no declared purpose; the duplicate pair extracts as two normal files (surfacing is the
  map/build's job); `extractor_sha` recorded.
- **Proof:** deterministic double-run diff + a per-file extraction spot-check.

### TASK-113 — Repo profile scan + onboarding gate report (D-A21 phase 1)
- **Depends on:** TASK-112.
- **Model:** Opus — the gate is the only human checkpoint on map quality.
- **Reads:** D-A21 (**whole block**: report layout, the three things plain approval cannot do,
  the three gate actions, process steps 1–6) · D-A20 (signal priority: include graph primary) ·
  D-A22 (profile file contract) · §5.2/§5.3 · impact §12.
- **Creates / edits:** `code_profiles/<repo>.profile.yaml` contract (label aliases, derivation
  priority, hub threshold, cluster size policy, confidence thresholds, frozen semantic overrides,
  `warn_if_human_authored_below`, gate record) + the first instance for `fixtures/c_repo`;
  `core/scripts/validate_onboarding.py` recast to drive D-A21 phase 1: automated **profile scan**
  (label variants + coverage · include density/resolution · prefix-token quality · `.h` placement
  · versioned duplicates · degree-zero-both-directions isolation · symbol presence), stage-B
  sample, projected stage distribution + stage-C cost, the **gate report** (D-A21 layout), and
  the three actions — `adjust profile` (edit → deterministic recompute → re-review), `skip
  stage C` (files fall to C\*, reversible), `group singletons` (model **proposes**, human reviews
  as a diff, approved groups freeze as overrides). Freeze → `profile_sha`.
- **Acceptance:** the report over `c_repo` shows the seeded ~60/40 split, the duplicate pair, and
  tier-1 entry count; every gate action works and composes; freeze emits `profile_sha`; nothing
  model-driven survives past the freeze except as frozen data.
- **Proof:** the rendered gate report + a freeze → `code_profiles/c_repo.profile.yaml` with sha.

### TASK-114 — Map build recast (two files, modules, purposes) + context checks
- **Depends on:** TASK-113.
- **Model:** Opus — the analysis substrate everything downstream matches against.
- **Reads:** §3.3 (amended: two files, `members[]`, purpose provenance/verdict/quality,
  `coverage_report`) · D-A19 (creation order; totality/singletons/`unclustered`; C-fallback;
  purpose-quality requirements; degraded case) · D-A20 (declared-vs-actual verdict) · D-A21
  (steps 7–15; caching rules) · D-A23 family 2 · impact §§3, 7, 12.
- **Creates / edits:** `core/skills/code_map_build.skill.md` full recast + deterministic helpers:
  hub exclusion (fan-in > threshold → `shared_interfaces`); module clustering (include graph →
  prefix tiebreak → frozen overrides → `unclustered`; language-scoped); purpose resolution per
  file (A declared → B header prose → C whole-file → C\* symbol names → `unanalyzable[]` with
  reasons), cached per file content hash; **purpose verdict** where declared (model verdicts the
  declared intention against the code: `confirmed` | `diverged` + `purpose_actual`); module
  purpose **synthesis** (model abstracts over member purposes — never re-reads source, never
  copies one member); `purpose_confidence` (+ `generic` quality flags); `coverage_report`; write
  `context_set/code_map/{components.json,files.json}` (`components[].members` explicit).
  **Family-2 context checks** enforced in-build: module totality, purpose totality, `members[]` ↔
  `files[].module` consistency. Reshape the oracle → `fixtures/c_repo/{expected_components.json,
  expected_files.json}` + **human re-freeze of `SIGNOFF.md`** (V — the old sign-off graded the
  old shape).
- **Acceptance:** build over `c_repo` matches the re-signed oracle; totality checks green; no
  module purpose is a copy of a member's; two runs produce identical structure (determinism);
  purposes cached (second run does no model purpose work); the versioned pair and the
  low-coherence case surface in the coverage report.
- **Proof:** oracle diff clean ×2 runs; family-2 checks green; cache hit demonstrated.

### TASK-115 — 4-branch gate + map cache
- **Depends on:** TASK-114.
- **Model:** Opus — cache-correctness mistakes propagate silently.
- **Reads:** §5.3 (amended — the 4 branches) · D-A21 (build frequency; cache keys
  `(commit_sha, profile_sha)` + file content hash; the clustering-is-global wrinkle) · impact §12.
- **Creates / edits:** the gate recast (in `validate_onboarding.py` / the map-build entry):
  branch 1 onboard (no profile) · branch 2 reuse (both shas match — no work) · branch 3
  incremental (commit moved — structure/clustering recomputed, model purposes only for changed
  files, module purposes re-synthesised for **affected** modules, which can exceed
  changed-file modules) · branch 4 full rebuild (`profile_sha` changed). `cache/code_maps/index.yaml`
  wiring; `REONBOARD_FLAG` semantics carried.
- **Acceptance:** all four branches exercised and observable in telemetry; branch 2 does zero
  work; branch 3 re-purposes only changed files; branch 4 invalidates wholesale.
- **Proof:** scripted branch walk on `c_repo` (touch nothing / touch a file / bump the profile).

### TASK-116 — Multi-language validation fixture (required, D-A19)
- **Depends on:** TASK-114.
- **Model:** Opus — the ADR marks this a required acceptance artifact, not an enhancement.
- **Reads:** D-A19 (multi-language block + the V validation requirement) · TASK-008/010 machinery
  (ledger) · `fixtures/mixed_repo/` · impact §§7, 12.
- **Creates / edits:** extend `fixtures/mixed_repo/` into a real multi-language repo (C + Java +
  Python, each with a genuine include/import graph); per-language **sections** in its
  `code_profiles/mixed_repo.profile.yaml` (one profile per repo — one gate, one freeze); proof
  that: modules are language-scoped; tier-1 matching runs an assertion against **all** module
  purposes and matches modules in two languages independently; closure stops at the language
  boundary (no cross-language edges; the reserved `external_calls`/`exposes` fields stay
  reserved); an unonboarded language degrades to the `unclustered` totality path via the TASK-010
  fallback.
- **Acceptance:** the four properties above demonstrated over the fixture; single-language
  (`c_repo`) behavior unchanged.
- **Proof:** map build over `mixed_repo` + a cross-language tier-1 match transcript.

---

## Milestone D4 — Enrichment (v1 → v2)

### TASK-117 — `enrichment.json` contract + finding routes
- **Depends on:** TASK-110 (an accepted v1 exists), TASK-104 (events).
- **Model:** Opus — the permanent record every enrichment stage reads/writes.
- **Reads:** §3.7 (replaced — `enrichment.json`) · D-A6 (authority) · D-A7 (never delete) · D-A9
  (escalated impacts) · D-A16 (**the routing tables**: auto-apply vs escalate; the no-code-gap
  four-way; undispositioned findings live outside the document; permanent record) · FR-EN-\*.
- **Creates / edits:** the `enrichment.json` schema + JSON-schema validator (per finding: `id`,
  `arm`, `kind`, requirement/assertion refs, code evidence + reasoning, `verdict?`, `action:
  auto_applied | escalated`, `disposition?`, `rationale?`, `section_target`, status — including
  undispositioned, for resumability); the routing implementation as a shared helper the arms +
  walkthrough consume (provenance → authority per D-A6; the escalate set per D-A16; each
  escalated type's destination table); ledger events wired (`verdict`/`escalation`/`disposition`).
- **Acceptance:** validator accepts/rejects fixture findings correctly; the D-A16 "what reaches
  the operator" table is reproduced by the router on a fixture finding set (grounded+unambiguous
  → auto; ambiguous/scope-moving/human-overruling → escalate).
- **Proof:** router unit-proof over a crafted finding set covering every table row.

### TASK-118 — Arm 1: per-assertion impact (`code_impact` recast)
- **Depends on:** TASK-117, TASK-114 (map).
- **Model:** Opus.
- **Reads:** §5.6 (the three-tier walk) · D-A19 (tiers; query = frame + title + description +
  assertion; low confidence **widens**; territory amortisation) · D-A8 (retrieval per deliverable
  / reasoning per epic; independent fan-out, anti-anchoring; **implicit current-state
  assumptions**) · D-A15/16 (§16 granularity = (assertion × location) incl. **gaps**; no-code gap
  escalates, never auto-builds) · D-A9 · old TASK-080 spec (git `0d7d8aa` — its fixed-point /
  both-directions / source-extends checks fold into Acceptance here).
- **Creates / edits:** `core/skills/code_impact_assess.skill.md` full recast: resolve the code
  **territory once per deliverable** (tier 1 vs module purposes; matched modules + their file
  purposes stay resident); fan out **per epic, independently** (structural learnings may carry;
  landing points never inherited); per assertion — tier 2 (file purposes within matched modules),
  tier 3a (read source; confirm/refute; extract + verdict implicit current-state assumptions),
  tier 3b (closure over `depends_on`/`used_by` **both directions to a fixed point**, extending
  from source where the map missed an edge); emit §16 entries per (assertion × location) — impacts
  **and** gaps; no-code findings route to escalation via TASK-117. New tier-walk oracles
  `fixtures/code_impact/` (salvaging the old closure content from git history).
- **Acceptance:** over the fixture v1 + `c_repo` map: a multi-hop closure reaches its oracle
  fixed point (both directions; a deliberately map-omitted edge recovered from source; a
  single-hop control does not over-report); an implicit-assumption finding surfaces (the "field
  48 has room" class); a no-code assertion escalates rather than emitting a build story;
  `unclustered` and low-confidence modules are searched, never skipped.
- **Proof:** tier-walk oracle diff + the escalation record in `enrichment.json`.

### TASK-119 — Arm 2: `claim_verifier`
- **Depends on:** TASK-117.
- **Model:** Opus.
- **Reads:** D-A5 (the verdict population three-way sort; runtime-shaped claims **skipped**, not
  marked) · D-A4 (§5 system-actor asymmetry; §8 never corrected) · D-A6 (authority) · D-A7
  (rewrite, never delete) · D-A8 (point lookup, no closure; cluster by code region; the coarse
  three outcomes — only one expensive; "unverifiable" as an honest cheap outcome feeding §14).
- **Creates / edits:** `core/skills/claim_verifier.skill.md` (replacing the TASK-102 stub):
  extract factual current-state claims from the verdict-eligible sections (§2, §5, §6, §10, §13,
  §14); sort the population (claims / judgment / future-state); **cluster by code region**; per
  cluster one coarse match → strong-match verdict | deep-read | unverifiable; stage corrections
  (source-derived claims) with inline code provenance; route operator/frame contradictions to
  escalation; auto-fill `[TBD]` gaps the code answers; contribute §18 counts. Wrapper contents ×2
  tools refreshed.
- **Acceptance:** over the fixture v1: a seeded wrong source-derived claim → staged correction
  with provenance; a seeded wrong frame claim → escalation (never silently overruled); a
  runtime-shaped NFR claim → skipped (no marker); an unmatchable claim → unverifiable, cheap,
  surfaced toward §14; §8 never touched.
- **Proof:** the staged-findings set in `enrichment.json` vs the seeded expectations.

### TASK-120 — Disposition walkthrough
- **Depends on:** TASK-117 (+ findings from 118/119 to walk).
- **Model:** Opus — the one human checkpoint of the enrichment stage.
- **Reads:** D-A17 (**the four binding constraints**: proposes-never-decides; triage-not-
  enumerate; ordering dependencies + downstream revisit; resumable) · D-A16 (per-type routing on
  disposition; the defer path is required) · D6c (material vs advisory batching) · FR-BR-08 loop
  (carried machinery).
- **Creates / edits:** `core/skills/disposition_walkthrough.skill.md` (replacing the stub):
  present one finding + evidence + recommended disposition; allow interrogation ("show me the
  code"); batch routine technical consequences ("these 15 — accept all, or review?"); sequence
  dependent findings and revisit downstream when an upstream call changes (a search-miss call
  invalidates derived findings); record decision + rationale → `decisions.jsonl`; persist status
  per finding in `enrichment.json` (stop/resume works); route each disposition per D-A16
  (including **defer → §17**). Wrapper contents ×2 tools refreshed.
- **Acceptance:** a fixture walkthrough covering: an individual scope-moving finding; a batched
  advisory group; a dependency chain revisited after an upstream reversal; a deferral landing in
  §17; an interrupted session resumed without loss.
- **Proof:** the `decisions.jsonl` + `enrichment.json` trail of that walkthrough.

### TASK-121 — Apply pass + G2 + enrichment spine exercise
- **Depends on:** TASK-118, 119, 120.
- **Model:** Opus.
- **Reads:** D-A2 (corrections revise in place with provenance; discoveries append) · D-A8
  (sequence steps 4–6: apply → §16/§17/§18 → regenerate §1) · §9.3 (G2 formula — **flagged
  provisional**) · D-A23 (G2 hard preconditions; "validate against a real run before freezing") ·
  §3.7.
- **Creates / edits:** the apply machinery (in the author skill's v2-assembly section + a small
  deterministic applier): auto-applied + dispositioned findings land — corrections in place with
  inline provenance (never delete), §16 written **organised by requirement**, §12 two-way moves,
  §17 extended, §18 counts (counts only — the ledger is `enrichment.json`); **§1 regenerated**
  from the corrected body; `solution_intent/v2.md` written (v1 untouched).
  `solution_intent_validator.py` gains the G2 duty: `0.5×verdict_completeness +
  0.5×impact_coverage`; hard preconditions — every escalation dispositioned; every correction
  carries code provenance; **every assertion has a verdict** (family 3). Then run the **full
  enrichment spine** over the fixture v1 → v2, and **evaluate the provisional G2 formula against
  that run** — record the verdict in the task commit; if the formula needs change, that is a
  ladder amendment (flag it, amend §9.3 + REQUIREMENTS in-task, add the port note).
- **Acceptance:** v2 exists with every touch traceable (v1 + `enrichment.json` reconstruct it —
  D-A16); G2 scores the run; both preconditions enforceable (a seeded undispositioned escalation
  blocks); §1 reflects the corrected body; formula verdict recorded.
- **Proof:** the v1→v2 diff + `enrichment.json` + the G2 gate record in the ledger.

---

## Milestone D5 — Jira (4-level plan + the only external mutation)

### TASK-122 — `jira_author` + `jira_template` (4-level plan)
- **Depends on:** TASK-121 (an accepted v2 + `enrichment.json`).
- **Model:** Opus.
- **Reads:** §3.8 (amended) · D11.6 · D-A14 (deliverable layer) · D-A15 (**whole block**: level
  sources; stories from §16 impacts *and* gaps *and* §7 non-code work; §16 granularity = story
  granularity; scope-vs-specification — the translation **adds** acceptance criteria/testability;
  every story names its code location or is flagged new-build/non-code; the tech letter as
  completeness oracle) · FR-JR-01/02 · §6.6.1.
- **Creates / edits:** `core/skills/jira_author.skill.md` (new — the wrapper exists since
  TASK-102); `core/profiles/payment_brand/jira_template.payment_brand.yaml` (field mapping per
  level: Initiative ← §1/§2/§4; Deliverable ← §7; Epic ← §8, one per requirement; Story fields
  incl. `code_location | new_build | non_code`, acceptance criteria, trace refs); emit
  `jira_plan.json` (§3.8) — full ID chain `D1 → R3 → §16 entry → story`; §10.3 now requires
  `jira_template` (present → green).
- **Acceptance:** over the fixture v2: four levels emitted; every §16 entry yields ≥1 story or an
  explicit disposition; every story traces to §16 or §7 and names code or carries its flag;
  deliverable-derived (non-code) stories present; nothing story-shaped read straight off the
  tech-letter text.
- **Proof:** `jira_plan.json` structural walk vs the v2's ID inventory.

### TASK-123 — `jira_validator` + G3
- **Depends on:** TASK-122.
- **Model:** Opus.
- **Reads:** §9.4 (amended — absorbs the FRD formula) · D-A1 (G3 = the real technical-quality
  gate) · D-A23 family 3 (the two story guardrails) · D-A15 (the reverse completeness check:
  do the stories, together, satisfy the tech letter?) · the old `frd_validator.py` at git
  `0d7d8aa` (salvage the scoring code, don't rewrite it).
- **Creates / edits:** `core/skills/jira_validator.skill.md` + `core/scripts/jira_validator.py`:
  `0.5×traceability + 0.5×testability` over the 4-level plan; hard checks — every §16 entry →
  ≥1 story (dropped-impact catch); every story → §16/§7 (invented-story catch); every story names
  code or is flagged; parent-chain integrity (no orphan epic/deliverable); the tech-letter
  completeness pass where a TechSpec source exists. G3 wiring through `gate.py`;
  `fixtures/jira_plan/{plan_pass,plan_fail}.json`.
- **Acceptance:** pass/fail fixtures score correctly with named violations; G3 stays an operator
  act (D4).
- **Proof:** validator over both fixtures + the TASK-122 plan.

### TASK-124 — Jira push seam + `jira_trace.json`
- **Depends on:** TASK-123, TASK-052 (auth seam).
- **Model:** Opus — the **only** external mutation; highest care.
- **Reads:** §7.1 (interface signature) · §7.2 (push flow) · §3.8 (`jira_trace.json`) · D-A24 ·
  impact §12.
- **Creates / edits:** `core/adapters/jpmc_adapters/jira.py` — generic push connector; the real
  JPMC Jira REST call isolated in its own `[TBD — VDI]` placeholder function + a **local stub
  target** so the flow proves offline; push order Initiative → Deliverable → Epic → Story with
  parent links; G3-gated + operator-confirmed before any write; emit `jira_trace.json` (issue
  keys per plan node); telemetry.
- **Acceptance:** stub push records a complete trace; an un-gated or unconfirmed push is
  impossible by construction; no secret on disk; the push is the run's sole external mutation.
- **Proof:** stub-target run → `jira_trace.json` + the gate/confirm records in the ledger.

---

## Milestone D6 — Metrics, docs, acceptance

### TASK-125 — `metrics_scan` re-cut (amended FR-MX-02)
- **Depends on:** TASK-121 (enrichment events exist), TASK-124.
- **Model:** Sonnet.
- **Reads:** FR-MX-02 (amended — M01–M07, M09–M12) · §8.2 · impact §2.
- **Creates / edits:** `core/scripts/metrics_scan.py` re-cut: $/SI-v1, $/enrichment, scores at
  G1/G2, first-pass acceptance, docs/month, v1→v2 cycle time, latency p95, §16→story coverage at
  push, stories/epic, push success, **M12 enrichment yield** (corrections + derived impacts +
  auto-fills per run — the v1→v2 delta). Drop the FRD-era metrics.
- **Acceptance:** over the D4/D5 fixture run's ledger, every amended metric derives; no retired
  metric referenced.
- **Proof:** `metrics_scan.py` output over the fixture ledger.

### TASK-126 — Docs re-cut (`SKILLS_INDEX`, `BUILD_OVERVIEW`, `design/README`, `CLAUDE.md`)
- **Depends on:** TASK-122 (the skill roster is final).
- **Model:** Sonnet.
- **Reads:** impact §8 · D-A23 (role list) · the landed D0–D5 state (disk is ground truth).
- **Creates / edits:** `docs/SKILLS_INDEX.md` (SI-era catalog: 8 roles, per-skill contract
  pointers); `docs/BUILD_OVERVIEW.md` (the SI → enrichment → Jira pipeline); `docs/design/README.md`
  (ADR index incl. 008 + the 003/004/005 banners); `CLAUDE.md` (drop retired pointers — seed
  skills, `brd_frd_overview.html`; confirm the current-slice wording matches the landed state).
- **Acceptance:** no doc references a retired file; a fresh-session read of `CLAUDE.md` →
  `TASK_LIST.md` → disk is coherent.
- **Proof:** link/reference sweep (`grep` for retired names) comes back empty.

### TASK-127 — End-to-end acceptance + registry re-publish
- **Depends on:** every task above.
- **Model:** Opus — the full operator path; absorbs old TASK-056's surviving half (D-A0).
- **Reads:** `docs/ACCEPTANCE.md` (the old spine run, as the format model) · §9.5 · every D-A
  gate/guardrail block · the Execution protocol step 5 suspension note.
- **Creates / edits:** `docs/ACCEPTANCE_SI.md` (run log + artifact links); registry re-publish.
- **Do:** From the React UI: configure a run (domain `payment_brand`; sources = SharePoint PDFs +
  Confluence pages + Bitbucket repo + a Jira Prior Artifact, each dispositioned; overview filled)
  → Generate (G0) → open the tool in the scaffold → `start-ingest` (fan-out + indexes + map via
  the 4-branch gate) → `start-si` → v1 → flag loop → G1 accept (v1 freezes) → `start-enrich` →
  Arms 1+2 → walkthrough → v2 → G2 → `start-jira` → 4-level plan → G3 → **stub** push +
  `jira_trace.json`. Then: `build_checks.py` 4/4 green · family-2 checks green ·
  `metrics_scan.py` derives the amended set · **re-publish the registry** (publish suspension
  lifts; both overlays ship) · delete the stale run workspace, re-Generate from the UI, and
  confirm the published registry serves the new pipeline.
- **Acceptance:** an operator completes the fresh run unaided through UI + tool; every gate is an
  operator act; v1 + `enrichment.json` reconstruct v2; the trace chain
  `D→R→§16→story→(stub) key` is intact; checks + metrics green; registry re-published and
  re-hydrated successfully.
- **Proof:** the run workspace + ledger + `docs/ACCEPTANCE_SI.md`.

---

# Deferred / candidate tasks (capture only — promote when the trigger is hit)

- [ ] **Cross-repo + cross-language closure** *(old 068 + ADR-007; D-A19: one capability wearing
  two hats)* — populate the reserved `external_calls`/`exposes` (§3.3); closure crosses repo and
  language boundaries. Trigger: a real multi-repo/multi-language impact need on the VDI corpus.
- [ ] **2nd-language extractor onboarding** *(old 069; ADR-006 stands)* — now cleaner:
  a new language = an `extractor_manifest` entry + per-language profile sections. Trigger:
  a real non-C repo.
- [ ] **Domain onboarding, re-scoped** *(old 070–074; no vocabulary step)* — a new domain =
  `si_profile.<domain>` + `jira_template.<domain>` + adapter pack, proposer skills +
  `onboard.py` orchestration + `domains_index.yaml` + UI dropdown. Trigger: domain #2.
- [ ] **Metrics store + dashboard (SQLite)** *(old 076)* — additive; JSONL stays source of truth.
- [ ] **Auto-launch** *(old 077)* — automate the start gesture where the environment permits.
- [ ] **UI enhancements** *(old 078)* — role gating + live telemetry surface.
- [ ] **Section-as-subprocess SI authoring** *(old 082)* — only at context-overflow scale; the
  D-A18 sequential-group rule and never-re-ask must survive the hop.
- [ ] **Scope-creep detection at implementation time** *(parked in D-A9)* — compare an
  implementation branch against the accepted SI; revives early if `UI_INPUT` gains a declared
  change scope.
- [ ] **Template profiles for recognised doc families** *(parked in D-A18)* — promote only if
  letters arrive on cadence and index selection proves noisy; per-section matching, N samples.
- [ ] **`purpose`-diff as a semantic-drift signal** *(idea)* — diff purposes between commits to
  catch behaviour drift under unchanged structure.

---

# Build-and-port discipline (reminder)

This repo is the **external Claude Code build**. Do not add VDI/Copilot-air-gap accommodations
into the generic core — the port touches only the runtime-tool seam + the placeholder functions.
Real API/secret calls follow hard rule **S**: one isolated placeholder per call, edited in place
on the VDI.

## Build the structure here; defer only the call (V, 2026-07-31 · ADR-008 D-A24)

For **every** source type, the connector script, the agent/skill, and the UI wiring are all built
here. Only the real API call is deferred. A **mock fixture** stands in for what the API would
return, so the full pipeline — ingest → extract → index → route → author — runs end-to-end
offline. **Mocks are per source TYPE, not per disposition** (dispositions are operator labels; no
fetching involved).

| Source type | Mock | Placeholder to fill on the VDI |
|---|---|---|
| `sharepoint` → PDF | ✅ `fixtures/pdf/`, `fixtures/sharepoint/` | `ingest_sharepoint.py :: _download_pdf` |
| `confluence` → HTML | ✅ `fixtures/confluence/` | `ingest_confluence.py :: _fetch_confluence` |
| `bitbucket` → repo | ✅ `fixtures/c_repo/`, `fixtures/code_clone/` | `clone.py` |
| `jira` → issue payload | ⬜ TASK-107 | `ingest_jira.py :: _fetch_issue` |
| Jira **push** | ⬜ TASK-124 | `jpmc_adapters/jira.py` |

**PDFs always arrive via SharePoint** — the `file` source type is local-testing-only, never production.

## Two lists, disjoint by construction

**`VDI_WIRING.md`** holds the environment wiring performed on the VDI. The split is by **kind of
work**, not by audience: this file = what gets **built** (generic, testable here, full specs);
`VDI_WIRING.md` = what gets **wired** (environment-specific, untestable here, **no specs** — an
item merely names a placeholder this list already built). **No task appears in both.** *(A
previous `TASK_VDI.md` drifted precisely by duplicating specs; deleted 2026-07-29.)*

**Port note (standing):** the JPMC-side design docs receive the **whole ADR-008 re-cut** at port
time — Phase B (`REQUIREMENTS.md` v2 + `TECH_SPEC.md` banner/amendments), the accepted ADR-008,
Phase C (`ADR-008-impact-analysis.md`), and this Phase D list. The older per-task port notes
(TASK-061 D5 fix, TASK-063B routing extension) are **moot** — the vocabulary and tag-lane routing
they patch are retired; only the D9 `start-ingest` amendment still carries (re-pointed to
`start-si`).
