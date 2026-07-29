# TASK_LIST — PDLC_App_v2 (the single build list)

**The one task list.** Everything open lives here; everything done is a one-line ledger entry
below. Previously split across `TASK_LIST.md` / `TASK_VDI.md` / `TASK_VDI_BOOTSTRAPS.md` —
consolidated 2026-07-29. Full specs of completed tasks (TASK-000–055) and the VDI bootstrap
prompts are in git history at commit `f8f2ae1` and earlier.

**Where the work runs.** The MVP (BRD→FRD, single domain, SharePoint + Bitbucket) is running.
Milestone 5B is executed **on the JPMC VDI with Copilot**; the external Claude Code build is
where generic pieces are built and proven first. Both use this file.

**How to use it.** Pick the first unchecked task, top-down. Follow the **Execution protocol**.
Tick the box only when every Acceptance condition is true and the proof + build checks are
green. **Disk + git are ground truth** — never rely on something said in an earlier session.

---

## Execution protocol (run this loop for EVERY task)

1. **Read the cited design first.** Each task names the exact `docs/…` §sections and files under
   **Reads** — open them. Do not work from memory; the cited section is the contract.
2. **Verify dependencies exist** (the **Depends on** files). If one is missing, stop and say so.
3. **Implement the GENERIC piece.** Build what is testable here. For anything that must hit a
   **real external API or secret store**, do NOT inline it — isolate it in **its own function**
   carrying a `[TBD — VDI]` placeholder (raises `NotImplementedError`), plus an **offline
   local-path convenience** so the piece runs end-to-end here (hard rule **S**). On the VDI you
   **edit that one placeholder function in place** to add the real call + JPMC auth (the way
   `ingest_sharepoint.py`'s `_download_pdf` and `ingest_confluence.py`'s `_fetch_confluence`
   were wired). Keeping the env-specific call in its own function is what makes that a clean,
   no-merge-conflict edit.
4. **Verify.** Run the task's **Proof**, then **`python core/scripts/build_checks.py`** — all
   5 §10 checks must be green. A connector also runs its `fixtures/<type>/verify_*.py`.
5. **Publish so the UI run sees it** (only after green):
   `python core/scripts/publish_registry.py <registry-repo-url> --branch feature/pdlc_app`
   then delete the stale run workspace and **re-Generate** from the UI to test end-to-end.
   (Local edits are invisible to the UI until the registry is re-published.)
6. **Tick the box** and commit (and push, so the external copy stays current).

> ✅ **A task is done when:** Acceptance true · its proof green · `build_checks.py` (§10 ×5)
> green · the registry re-published (so the UI run uses it) · box ticked.

---

## Hard rules (never violate — condensed from `CLAUDE.md` / `docs/`)

- **S. Build-and-port / edit-in-place discipline.** Generic code is shared and built+tested first;
  any real API/secret is **isolated in its own function** carrying a `[TBD — VDI]` placeholder
  (raises `NotImplementedError`) plus an **offline local-path convenience** so the piece runs
  end-to-end in the external build. On the VDI you **edit that one placeholder function in place**
  to add the real call + JPMC auth — **no `/vdi` plugin folder, no auto-load hook, no separation.**
  (V decision 2026-06-30 — this supersedes the prior `/vdi`-plugin rule everywhere it appears.)
- **Two seams only (FR-XS-01).** The **domain seam** (adapter / profiles / template / vocabulary)
  and the **runtime-tool seam** (instruction file / wrappers / prompts / launch). The per-language
  **extractor** is the one non-domain variation point, governed by the **onboarding gate**.
- **Binding rationales.** The structural extractor is **deterministic + frozen** — never
  model-rewritten at runtime. The map-build gate is **model-free**. The model owns only
  `purpose` + `tags` in the code map. **Ingestion never branches on `domain`.** The **only**
  external mutation of a run is the Jira push. Scope changes are operator-decided.
- **Descriptor parity.** Every source connector emits the **same descriptor shape** as
  `ingest_file.py` (`type, source, url/…, staged_path, auth_ref, ingest_ts`). Downstream
  (`pdf_extract → article_summarize`, or the routed lane) must not change.
- **Onboarding skills: propose-never-bless.** The onboarding aids (extractor/domain/profile/
  adapter) **propose reviewable artifacts**; a human **freezes**. Amendments are **build-time**
  (committed + re-pinned), never runtime mutations. §10 build checks gate every freeze.
- **Cite-or-flag.** Every substantive artifact claim is grounded to a source/frame/operator
  answer or marked `[TBD — unsourced]`. Never invent.
- **§10 must stay green.** No task lands with a red build check. Connectors keep §10.4; the
  domain seam keeps §10.1/10.3/10.5; overlays keep §10.2.
- **Ladder discipline.** If a task would change a pinned contract or reopen D1–D10, **stop and
  flag it** — unless the task explicitly says it is a ladder amendment (063B, 081), in which case
  amend the design *as part of the task* and add the port note.

---

## VDI environment notes

- **Python deps.** Scripts need `httpx` + `PyYAML`; extractor tasks also need
  `tree-sitter==0.25.2` + `tree-sitter-c==0.24.2` (ADR-001). No venv is assumed — use whatever
  Python you run the repo with. Check: `python -c "import httpx, yaml"`.
- **Auth (the seam, env backend).** Set as **user** env vars so the run inherits them:
  `PDLC_AUTH_BITBUCKET` (+ `_USER`), `PDLC_AUTH_SHAREPOINT` (+ `_USER`), and for new connectors
  `PDLC_AUTH_CONFLUENCE` / Jira likewise. The token never lands on disk — `auth_ref` is a pointer.
- **Registry / code repos.** Registry = `feature/pdlc_app`; Stratus code = `feature/c_repo`
  (one Bitbucket repo, two branches). Re-publish to `feature/pdlc_app` after any `core/` change.
- **Copilot layout (already fixed).** Generate emits `.github/copilot-instructions.md` +
  `.github/prompts/*.prompt.md`; agents are `*.agent.md` at the run root.

---

## Citation key

`FR-…` / `NFR-…` / `D1`–`D10` → `docs/REQUIREMENTS.md` · `§n.n` → `docs/TECH_SPEC.md` ·
`ADR-00n` → `docs/design/` · **Model key:** `Sonnet` = default · `Opus` = deep design artifact
or a mistake that propagates far.

---

## Standing port note (not a numbered task)

**Real JPMC host / secret validation.** 5A built the auth seam (TASK-052), cloned through it
from a local-remote Bitbucket (TASK-054), and pulled SharePoint from a stub (TASK-055). What
remains is binding `auth_ref` to the **real JPMC secret store** and validating against the
**live** Bitbucket / SharePoint / Confluence endpoints. The mechanism is unchanged — only the
secret backend + endpoints differ, and per hard rule **S** that is an in-place edit of each
connector's `_fetch_*` / `_download_*` placeholder. Environment-specific; done as the
connectors land on the VDI, not as its own task. (FR-DC-02/11/12, §7.)

---

# Done ledger (TASK-000 – 063B)

> One line per completed task. Full specs are in git history (`f8f2ae1` and earlier).
> This is what a fresh session reads to know what exists without re-deriving it.

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

**Phase 5 · Milestone 5A — Self-serve run**
- [x] TASK-050 — Generate backend service (FastAPI): config → `UI_INPUT.yaml` → `generate.py` (G0)
- [x] TASK-051 — React Run Configurator (5 tabs) → emits §3.1 `UI_INPUT.yaml`; Generate + hand-off
- [x] TASK-052 — `jpmc_adapters/auth.py` real `resolve_auth` (auth_ref → secret store)
- [x] TASK-053 — Registry (repo #1) on Bitbucket + hydrate-from-remote at pinned `registry_sha`
- [x] TASK-054 — Live Bitbucket code-source clone (repo #2) through the auth seam; `commit_sha` pinned
- [x] TASK-055 — `ingest_sharepoint.py` — SharePoint PDF connector; `_download_pdf` is the VDI placeholder

**Phase 5 · Milestone 5B — carried fixes + connectors**
- [x] TASK-060 — `runtime_tool` threaded through G1/G2 telemetry — `_runtime_tool(ledger_dir)` helper in both validators reads the run's sibling `UI_INPUT.yaml`; copilot runs record `tool: copilot`. *(built+verified external; pending VDI port)*
- [x] TASK-061 — D5 `card_brand`/`message_format` `emitted_by` reconciled — D5 table now matches `vocabulary.yaml` on all 12 tags; §10.5 green. **JPMC-side D5 still to fix at port.**
- [x] TASK-062 — `UI_INPUT.example.yaml` frame alignment — **skipped by V decision 2026-06-30.** Cosmetic only: the Discover/Mastercard mismatch is confined to the static example fixture (and greyed UI placeholder text) and never reaches an operator-driven run. Closed without change; revisit only for a demo where coherence matters.
- [x] TASK-063 — Confluence connector `ingest_confluence.py` — mirrors `ingest_sharepoint.py`; `pull_page()` emits the exact `ingest_file` descriptor; `_fetch_confluence` is the lone `[TBD — VDI]` placeholder (`set_fetcher` seam for tests); lazy auth; `main()` stages multiple pages (one link = one page). Fixtures `fixtures/confluence/{discover_routing_kb,message_format_kb}.html` + `verify_confluence.py` (13 checks). **VDI:** edit `_fetch_confluence` with the real REST call + auth; no other change.
- [x] TASK-063B — Per-source-type doc-pipeline routing — `adapter.yaml` `docs_pipeline` now a two-lane mapping (`default` PDF lane + `confluence: [confluence_tag]`), bare-list back-compat preserved; `confluence_tag.skill.md` authored (tag-only, 6 tags, `certification` excluded); `vocabulary` `emitted_by` += `confluence_tag`, `vocab_sha d5frozen-r2 → -r3`; §10.5 unions across lanes + requires a `default` lane; `source_processor` routes by `src.type` (never `domain`); UI Confluence row un-deferred + `emit.js` wired + `verify_frontend` asserts it emits. Proof `fixtures/adapter_routing/verify_adapter_routing.py` (11 checks). **Port note:** amends §6.6.3 + §10.5 — carry into the JPMC-side spec. **VDI:** re-publish registry + `vite build` so the un-deferred Confluence row ships.

---

# OPEN WORK

## Open index (tick here; then collapse the task into the done ledger above)

**Milestone 5A — remaining**
- [ ] TASK-056 — Self-serve acceptance: UI → Generate → VS Code Claude Code/Copilot → BRD/FRD · `Opus`

**Milestone 5B — Jira (the only external mutation + G3)**
- [ ] TASK-064 — Jira authoring + validation skills + `jira_template` · `Opus`
- [ ] TASK-065 — Jira push seam + `jira_plan/` + `trace.json` + G3 · `Opus`

**Milestone 5B — Code-impact enhancements**
- [ ] TASK-066 — `purpose`-as-discovery in the coarse pass · `Opus`
- [ ] TASK-067 — Doc-side semantic-gap signal · `Sonnet`

**Milestone 5B — Multi-repo**
- [ ] TASK-068 — Multi-repo cross-repo closure · `Opus`

**Milestone 5B — Domain onboarding (proposers → orchestrator; strict dependency order)**
- [ ] TASK-069 — `extractor_onboard` skill + a 2nd language extractor · `Opus`
- [ ] TASK-070 — `domain_onboard` skill (propose a new domain's vocabulary) · `Opus`
- [ ] TASK-071 — `profile_onboard` skill · `Opus`
- [ ] TASK-072 — `adapter_onboard` skill (+ promote `pdf_extract` to `core/skills/`) · `Opus`
- [ ] TASK-073 — Domain-onboarding orchestrator (`onboard.py` + `ONBOARD_INPUT.yaml`) · `Opus`
- [ ] TASK-074 — Multi-domain enablement (`domains_index.yaml` + UI) · `Sonnet`

**Milestone 5B — Vocabulary adequacy (L2)**
- [ ] TASK-075 — `vocab_gap_assess` + amendment loop · `Opus`

**Milestone 5B — Infra / UX (lower priority)**
- [ ] TASK-076 — Metrics store + dashboard (SQLite) · `Sonnet`
- [ ] TASK-077 — Auto-launch (operator-gesture automation) · `Sonnet`
- [ ] TASK-078 — UI enhancements (role gating + telemetry surface) · `Sonnet`

**Milestone 5B — Quality assessments (assessment-first; each proposes a human-frozen diff)**
- [ ] TASK-079 — Assess discovery-question adequacy (up-front + throughout the BRD) · `Opus`
- [ ] TASK-080 — Verify the deep-pass code-ripple closure traces + goes deep enough · `Opus`
- [ ] TASK-081 — Source-grounded auto-fill loop before G1 (ladder amendment + ADR) · `Opus`

---

## Milestone 5A — remaining

### TASK-056 — Self-serve milestone acceptance (UI → Generate → tool → BRD/FRD)
- **Phase:** P5-A · **Depends on:** TASK-050..055.
- **Model:** Opus — the full operator-driven path; highest-stakes of 5A.
- **Reads:** `docs/ACCEPTANCE.md` (the TASK-049 spine run) + every 5A task above.
- **Creates / edits:** `docs/ACCEPTANCE_5A.md` (the self-serve run log + artifact links).
- **Do:** From the React UI, configure a run (Domain `payment_brand`; sources = SharePoint PDF(s) + Bitbucket code repo; registry = Bitbucket) → **Generate** (G0) → open VS Code Claude Code/Copilot in the scaffold → run the spine → accepted BRD + FRD. Nothing outside the seam changes.
- **Acceptance:** an operator completes a fresh run unaided through UI + tool; `UI_INPUT.yaml` carries the real URLs; sources pulled live through the connectors + auth seam; BRD/FRD pass G1/G2; `build_checks.py` green; `metrics_scan.py` derives the run's metrics.
- **Proof:** the run workspace + ledger + `docs/ACCEPTANCE_5A.md`.
- **Satisfies:** FR-XS-02/06/09/16, FR-DC-01/02/11/12.

> 🔁 **Milestone 5A done = self-serve run works.** The 5B tasks below are ordered by dependency;
> tackle top-down.

---

## Milestone 5B — Jira (the only external mutation + G3)

### TASK-064 — Jira authoring + validation skills + `jira_template`
- **Phase:** P5-B · **Depends on:** the BRD/FRD author+validator pattern, the domain seam.
- **Model:** Opus — new authoring + gate semantics.
- **Reads:** `docs/TECH_SPEC.md` §9.4 (jira), §10.3 (seam requires `jira_template`); FR-JR-*, FR-XS-17.
- **Creates / edits:** `core/skills/jira_author.skill.md`, `core/skills/jira_validator.skill.md`; `core/profiles/payment_brand/jira_template.*`.
- **Do:** Author the Jira epic/story generation skill + its validator; add `jira_template` to the domain seam (once present, §10.3 requires it).
- **Acceptance:** a fixture FRD → jira plan authored + gated; §10.3 now checks `jira_template` (green); no external push yet (TASK-065).
- **Proof:** a fixture FRD → jira plan; validator gate runs.
- **Satisfies:** FR-JR-*, FR-XS-17.

### TASK-065 — Jira push seam + `jira_plan/` + `trace.json` + G3 gate
- **Phase:** P5-B · **Depends on:** TASK-064, TASK-052 (auth seam).
- **Model:** Opus — the **only** external mutation; highest care.
- **Reads:** `docs/TECH_SPEC.md` §3.8 (`jira_plan/`, `trace.json`), §7 (push seam), §9 (G3); FR-JR-*, FR-XS-17.
- **Creates / edits:** `core/adapters/jpmc_adapters/jira.py`, `jira_plan/` + `trace.json` emit, the G3 gate.
- **Do:** Generic Jira-push connector with the real JPMC Jira REST call **isolated in its own `[TBD — VDI]` placeholder function, edited in place on the VDI** (hard rule **S** — no `/vdi` plugin); emit `jira_plan/` + `trace.json`; gate **G3** before push. The push is the **only** external mutation — operator-confirmed.
- **Acceptance:** G3 gates the plan; a stub push records `trace.json` (issue keys); no secret on disk; push is the sole mutation; build_checks green.
- **Proof:** stub Jira endpoint; G3 + `trace.json` proof; no secret on disk.
- **Satisfies:** FR-JR-*, FR-XS-17, §7.

---

## Milestone 5B — Code-impact enhancements (real-corpus value)

### TASK-066 — `purpose`-as-discovery in the coarse pass
- **Phase:** P5-B · **Depends on:** TASK-040 (coarse pass).
- **Model:** Opus.
- **Reads:** the TASK-040 coarse pass (`core/skills/code_impact_assess.skill.md`); ADR-005.
- **Creates / edits:** the coarse-pass agent (TASK-040).
- **Do:** Let the coarse pass also use `purpose` for **semantic candidate discovery** (surface a component whose `purpose` describes the requirement even when the matching *tag* wasn't applied) — mitigates the under-applied-tag blind spot. Advisory + cite-or-flag (never silently widen scope; surface via Flags). The model-free rule governs *building* the map, not the already-model-driven coarse consumer. **Refinements (V-approved 2026-07-02):**
  - **(a) provenance per candidate** — every coarse candidate carries `matched_by: tag | purpose | both` (`both` = high confidence; `purpose`-only = flagged candidate for the operator);
  - **(b) feed the adequacy signal** — a `purpose`-only hit is direct evidence of an under-applied/missing tag, so emit it as an `uncovered_concepts`-style observation into the §5.4.1 vocab-adequacy ledger (links to TASK-067 / FR-DC-21; every impact run doubles as vocabulary QA);
  - **(c) module-first descent** — compare the requirement against `components[].purpose` first, descend to file-level purposes only within matched modules (bounds the semantic pass on large repos);
  - **(d) the impact query is text, not topics** — the semantic comparison uses the `UI_INPUT.frame` text (+ relevant `context_set/` content and, once drafted, the BRD requirements section), not just profile topic names; the frame names concepts no topic-level tag ever will.
- **Acceptance:** a mis-tagged-but-`purpose`-relevant component surfaces as a flagged candidate carrying `matched_by: purpose`; the same hit lands in the vocab-adequacy ledger; module-first order holds (no file-level compare outside matched modules); never silently widens scope; deep-pass closure unchanged.
- **Proof:** a fixture with an under-applied tag → coarse pass surfaces it via `purpose`.
- **Satisfies:** ADR-005 (`purpose` leverage); enhances TASK-040/041.

### TASK-067 — Doc-side semantic-gap signal
- **Phase:** P5-B · **Depends on:** §5.4.1 vocab-adequacy.
- **Model:** Sonnet.
- **Reads:** ADR-005 open-Q #2; the code-side `uncovered_concepts`.
- **Creates / edits:** a doc-arm analog to `uncovered_concepts`.
- **Do:** Add a doc-side equivalent of the code side's `uncovered_concepts` so vocabulary-adequacy detection (§5.4.1) is symmetric across both arms, not code-only.
- **Acceptance:** the doc arm emits a leftover-meaning signal symmetric to the code arm; §5.4.1 considers both.
- **Proof:** a doc with vocabulary-uncovered meaning → doc-side gap signal.
- **Satisfies:** ADR-005 open-Q #2.

---

## Milestone 5B — Multi-repo

### TASK-068 — Multi-repo cross-repo closure
- **Phase:** P5-B · **Depends on:** the `code_map` build (TASK-036), TASK-054 (clone).
- **Model:** Opus.
- **Reads:** `docs/TECH_SPEC.md` §3.3 (reserved `external_calls`/`exposes`), FR-DC-18.
- **Creates / edits:** `code_map.json` cross-repo fields + closure logic + multi-repo clone (N repos/run).
- **Do:** Populate the reserved `external_calls`/`exposes` fields and implement cross-repo closure (a requirement spanning >1 repo).
- **Acceptance:** a 2-repo run maps cross-repo calls; closure surfaces impact across repos; single-repo unaffected.
- **Proof:** two linked fixture repos → a cross-repo edge in `code_map` + closure.
- **Satisfies:** FR-DC-18. **See also:** `docs/design/ADR-007-cross-repo-code-impact.md`.

---

## Milestone 5B — Domain onboarding (the proposer skills, then the orchestrator)

### TASK-069 — `extractor_onboard` skill + a 2nd language extractor
- **Phase:** P5-B · **Depends on:** TASK-009/012 (C extractor pattern), the onboarding gate (§5.7 `port_check`).
- **Model:** Opus.
- **Reads:** `docs/TECH_SPEC.md` §5.7, ADR-001 (tree-sitter), FR-DC-19; `docs/ENV_PRECHECK.md`; `docs/design/ADR-006-extractor-onboarding.md`.
- **Creates / edits:** `core/skills/extractor_onboard.skill.md`; a 2nd-language extractor frozen with its own `onboarding_manifest`.
- **Do:** The skill proposes/refines an extractor against a code sample → reviewable artifact for human **freeze**; onboard a 2nd language (e.g. Java/Python) via the same gate. Structural-only, deterministic, **model-free build**; the TASK-010 model fallback covers unonboarded languages meanwhile.
- **Acceptance:** a 2nd-language extractor onboarded + frozen against an oracle; §10 green; the build stays model-free.
- **Proof:** extract a sample repo in the new language; oracle match.
- **Satisfies:** FR-DC-19.

### TASK-070 — `domain_onboard` skill (propose a new domain's vocabulary)
- **Phase:** P5-B · **Depends on:** TASK-069 (an untagged `purpose`-only map), D5 (vocabulary contract).
- **Model:** Opus.
- **Reads:** ADR-003, FR-DC-20; `vocabulary.payment_brand.yaml` (the shape to propose).
- **Creates / edits:** `core/skills/domain_onboard.skill.md`.
- **Do:** Propose a **new** domain's first `vocabulary.<domain>.yaml` from its sample docs + the untagged (`purpose`-only) code-map of a sample repo → reviewable artifact for human freeze (**propose, never bless** — the FR-DC-19 governance applied to the dictionary). Cannot be exercised until domain #2; `payment_brand`'s vocabulary is frozen by D5.
- **Acceptance:** given 2nd-domain samples, proposes a `vocabulary.<domain>.yaml` a human can freeze; never auto-blesses; §10.1 containment holds once frozen.
- **Proof:** a 2nd-domain sample → proposed vocabulary artifact.
- **Satisfies:** FR-DC-20.

### TASK-071 — `profile_onboard` skill
- **Phase:** P5-B · **Depends on:** TASK-070 (a frozen vocabulary).
- **Model:** Opus.
- **Reads:** ADR-004, FR-DC-22, FR-BR-08; the `payment_brand` profiles.
- **Creates / edits:** `core/skills/profile_onboard.skill.md`.
- **Do:** Gate 3 of the adaptive-dictionary chain (detect → name a tag → **route it into a profile section**). When a vocabulary grows (FR-DC-20/21), a newly-approved tag is *taggable but unconsumed* until a profile section references it. **Surface** the unconsumed tag (FR-BR-08 surface→wait→apply loop), **propose** a target section `id` + drafted `must_capture`/`probe_if_missing` (`sources` from the tag's `emitted_by`; `functional_kind`/`traces_to` for the FRD) → reviewable **profile diff**. Two modes: **bulk** (whole first profile at onboarding, right after `domain_onboard` freezes the vocabulary) + **incremental** (one new tag at drift). Vocabulary-first (§10.1 containment). Build-time amendment, never runtime mutation (§6.6.1).
- **Acceptance:** an approved-but-unconsumed tag → proposed profile diff a human freezes; no runtime mutation.
- **Proof:** an unconsumed tag → proposed profile section.
- **Satisfies:** FR-DC-22.

### TASK-072 — `adapter_onboard` skill (+ promote `pdf_extract` to `core/skills/`)
- **Phase:** P5-B · **Depends on:** TASK-070, TASK-071 (frozen vocab + profiles).
- **Model:** Opus.
- **Reads:** ADR-005, FR-DC-23, §6.6.3; the TASK-017 F1+3 drift class (`CLAUDE.md`).
- **Creates / edits:** `core/skills/adapter_onboard.skill.md`; promote `pdf_extract` → `core/skills/`.
- **Do:** The last domain-seam authoring aid. Propose the adapter pack by guided conversation — show the fixed frame (engine + fixed `code_pipeline → code_map_build`), design the variable `docs_pipeline` (reuse shared/structural skills; scaffold net-new ad-hoc skills), and **derive each skill's `emits` from the vocabulary's `emitted_by`** so `adapter.yaml` cannot drift from the vocab **by construction** (kills the TASK-017 F1+3 drift class). Bulk + incremental. **Dependency:** promote domain-agnostic `pdf_extract` into `core/skills/` first, so it is available before a pack exists. Propose-never-bless; references core skills, authors only domain pack skills, never edits `core/skills/` content beyond the promotion, never runtime-mutates.
- **Acceptance:** given frozen vocab+profiles, proposes an adapter pack whose `emits` == `emitted_by` by construction; §10.5 no-drift green; `pdf_extract` in `core/skills/`.
- **Proof:** a 2nd-domain frozen seam → proposed `adapter.yaml` with zero drift.
- **Satisfies:** FR-DC-23. **Open Qs (ADR-005):** #1 answered by TASK-073 (`ONBOARD_INPUT.yaml`); #2 by TASK-067.

### TASK-073 — Domain-onboarding orchestrator (`onboard.py` + `ONBOARD_INPUT.yaml`)
- **Phase:** P5-B · **Depends on:** TASK-069..072 (all four helpers), TASK-048 (`build_checks.py`).
- **Model:** Opus — sequences the authoring chain with hard gates + a registry push.
- **Reads:** §6.6.1, §10, Appendix B (consume-pull vs author-pull); FR-DC-19/20/22/23.
- **Creates / edits:** `core/scripts/onboard.py`, `ONBOARD_INPUT.yaml`.
- **Design (V-proposed, to refine — the four helper *skills* are the proposers; this is the utility that sequences them end-to-end so a new domain can be authored, frozen, and pushed back to the registry as one guided flow, after which a normal `mode: run` proceeds):**
  - **Config = a separate but `UI_INPUT`-shaped envelope with a `mode` discriminator** — `mode: onboard` (authors the registry) vs `mode: run` (consumes it). Deliberately **not** a flag bolted onto run-`UI_INPUT`: run config is the immutable consume-the-registry artifact (§3.1); onboarding carries different fields (`sample_sources[]` corpus, sample repo, `baseline`, the **new** `domain`) and a different output (a registry commit, not a run workspace). One shared schema style / UI affordance, two modes — this is the concrete answer to ADR-005's "sample-input mechanism unspecified (is it `UI_INPUT`-shaped?)".
  - **Flow:** `onboard.py` does the **authoring pull** (clone registry → `onboard_dir/` scratch), runs the four helpers **in the mandated order** (`extractor_onboard` → `domain_onboard` → `profile_onboard` → `adapter_onboard`) with a **human freeze gate at each step** (propose → refine → freeze), then runs **`build_checks.py` (§10) as a HARD GATE** (containment §10.1, emit-map no-drift §10.5, coverage, parity §10.2) — **red ⇒ stop, no push** — then `git commit` + **push to Bitbucket**, and **emits the resulting `registry_sha`** to thread into the subsequent `mode: run` `UI_INPUT`.
  - **Governance (unchanged):** propose-never-bless throughout; the push is a **build-time developer `git` action**, not a runtime agent mutation (distinct from the run-time Jira push, the *only* external mutation of a run); the registry stays human-frozen + SHA-pinned (§6.6.1). Distinct from `hydrate.py` (TASK-024): that is the *consume* pull (copy a frozen SHA into a run); this is the *author* pull (edit the registry, push back).
- **Acceptance:** a new domain authored end-to-end → §10 green → pushed → `registry_sha` emitted; red §10 ⇒ no push; distinct from the `hydrate.py` consume pull.
- **Proof:** onboard a 2nd domain against a local bare-git registry; `registry_sha` emitted; §10 gate enforced (red blocks push).
- **Satisfies:** FR-DC-19/20/22/23; answers ADR-005 open-Q #1.

### TASK-074 — Multi-domain enablement (`domains_index.yaml` + UI)
- **Phase:** P5-B · **Depends on:** TASK-073 (a 2nd domain authored).
- **Model:** Sonnet.
- **Reads:** FR-BR-11/14, FR-XS-21, D2; the UI `DOMAINS` list (`PDLCConfigurator.jsx`).
- **Creates / edits:** `domains_index.yaml`; drive the UI domain dropdown from it.
- **Do:** Add `domains_index.yaml` (the registered domains) + wire the UI's domain dropdown from it instead of the hardcoded `payment_brand`. Generate hydrates the chosen domain (domain-pruned). The YAML baseline extraction stays deferred under D2.
- **Acceptance:** a 2nd domain appears in the UI + Generates a correctly-pruned scaffold; `payment_brand` unaffected.
- **Proof:** a 2-domain index → UI offers both → Generate prunes correctly.
- **Satisfies:** FR-BR-11/14, FR-XS-21.

---

## Milestone 5B — Vocabulary adequacy (L2)

### TASK-075 — `vocab_gap_assess` + amendment loop
- **Phase:** P5-B · **Depends on:** TASK-013 (L1 detector, in-slice), the `vocab_sha` cache hook.
- **Model:** Opus.
- **Reads:** ADR-003, FR-DC-21; the L1 `VOCAB_GAP_FLAG`.
- **Creates / edits:** `core/skills/vocab_gap_assess.skill.md` + the amendment loop.
- **Do:** The model half of vocabulary adequacy — a bounded model pass over the **newly-introduced untagged delta** proposes a candidate tag + evidence; human-gated **amendment** → `vocab_sha` bump → re-tag pass. First meaningful exercise is the real (VDI) corpus: the synthetic fixtures were authored to fit the 12 tags, so the gap cannot manifest externally. The `vocab_sha` cache-key hook is already reserved (TASK-012/013), so the loop drops in additively.
- **Acceptance:** an untagged delta → proposed tag + evidence; human-gated amendment bumps `vocab_sha` + re-tags; never auto-mutates.
- **Proof:** a synthetic untagged delta → proposed amendment artifact.
- **Satisfies:** FR-DC-21.

---

## Milestone 5B — Infra / UX (lower priority)

### TASK-076 — Metrics store + dashboard (SQLite)
- **Phase:** P5-B · **Depends on:** TASK-032 (ledger), `metrics_scan`. · **Model:** Sonnet.
- **Reads:** D8 persistence split; FR-MX-*.
- **Do:** Promote the JSONL ledger to a queryable store + a metrics dashboard — **additive** (JSONL stays source of truth).
- **Acceptance:** ledger events queryable; dashboard renders run metrics; JSONL unchanged.
- **Proof:** ingest a run's ledger → dashboard renders. **Satisfies:** FR-MX-*, D8.

### TASK-077 — Auto-launch (operator-gesture automation)
- **Phase:** P5-B · **Depends on:** the 5A manual-start path (FR-XS-22). · **Model:** Sonnet.
- **Reads:** FR-XS-25 (deferred auto-launch); the overlays' `launch.md`.
- **Do:** Automate the manual start gesture (open the tool + run `start-ingest`) where the environment permits — Claude-only convenience first.
- **Acceptance:** Generate → run starts without the manual step where allowed; the manual path still works.
- **Proof:** an auto-launched run. **Satisfies:** FR-XS-25.

### TASK-078 — UI enhancements (role gating + telemetry surface)
- **Phase:** P5-B · **Depends on:** TASK-050/051. · **Model:** Sonnet.
- **Reads:** the role-gating FRs; the `GET /runs/{id}/status` endpoint.
- **Creates / edits:** `app/frontend/` + `app/backend/`.
- **Do:** Role gating on the configurator + a richer telemetry/metrics surface (live run status, G-gate results).
- **Acceptance:** roles gate actions; the UI surfaces live ledger status.
- **Proof:** a gated action + a live-status view. **Satisfies:** FR-XS-* (UI enhancements).

---

## Milestone 5B — BRD discovery quality

### TASK-079 — Assess discovery-question adequacy (up-front + throughout the BRD)
- **Phase:** P5-B · **Depends on:** TASK-037/038/039 (`brd_author`), TASK-015 (`brd_profile`). · **Model:** Opus.
- **Reads:** `core/skills/brd_author.skill.md` — its `## Discovery (FR-BR-02)` framing pass (the *up-front* questions) **and** the per-section `probe_if_missing` loop (the *throughout* questions); `core/profiles/payment_brand/brd_profile.payment_brand.yaml` (`must_capture` / `probe_if_missing` per topic); `docs/REQUIREMENTS.md` **D1** (the `must_capture`/`probe_if_missing` schema), **FR-BR-02** (up-front framing discovery — 2–3 clarifying questions), **FR-BR-03** (throughout gap-fill, limited to unsatisfied `must_capture`), **FR-BR-05** (never re-ask / shared memory), **FR-BR-09** (`brd_validator` coverage score → G1); the `start-brd` prompt and — for the pre-BRD handoff — `start-ingest`.
- **Why / when.** The BRD's quality is bounded by what the author *asks*. Two question moments exist: an **up-front** pass (what `brd_author` elicits before drafting, seeded from `must_capture`) and a **throughout** pass (the `probe_if_missing` loop as sections fill). Today neither is measured — a `must_capture` topic with no eliciting question, or a frame-relevant topic with no probe, silently becomes a `[TBD]` instead of a question. This task **measures** that coverage, then proposes additive fixes; it does **not** redesign the BRD flow.
- **Do (assessment-first, then propose — propose-never-bless):**
  1. **Inventory** where discovery questions originate today: the up-front pass and the `probe_if_missing` loop. Write the inventory.
  2. **Evaluate adequacy** against the frame + sources + code surface: for each `must_capture` topic, is there a question that elicits it when the sources are silent? Any frame-relevant topic with **no** probe? Does the author probe before assuming, or drop `[TBD]` without asking?
  3. **Findings artifact:** per-topic coverage (covered / under-probed / missing), each cited to the skill/profile line (**cite-or-flag** — never invent a gap).
  4. **Propose** additive remediation **only in the domain seam** — new/strengthened `probe_if_missing` entries in `brd_profile` and/or sharper elicitation guidance in `brd_author.skill.md` — as a reviewable diff a human **freezes**. No runtime mutation; never branch on `domain`.
- **Acceptance:** a written up-front + throughout coverage assessment mapping every `must_capture` topic to its eliciting question or flagging the gap; a proposed (human-frozen) profile/skill diff that closes the identified gaps; G1 still gated by the same validator; `build_checks.py` (§10 ×5) green; the `payment_brand` BRD run is unaffected unless the diff is frozen.
- **Proof:** run a fixture BRD (the bundled Mastercard-mandate PDF) through `brd_author` with deliberately **sparse** sources → the proposed probes fire for the silent topics; the coverage report lists no un-probed `must_capture` topic.

---

## Milestone 5B — Code-impact depth (deep-pass ripple / closure)

### TASK-080 — Verify the deep-pass code-ripple closure traces correctly and goes deep enough
- **Phase:** P5-B · **Depends on:** TASK-041 (deep pass), TASK-005 (the signed-off oracle). · **Model:** Opus.
- **Reads:** `core/skills/code_impact_assess.skill.md` — the **Deep** mode "trace the real dependency closure" step (follow `depends_on` = callees **and** `used_by` = callers **outward until the affected surface is closed**; the map *seeds*, the source *confirms + extends*), the deep output contract (`ripple` + the `scope_ripple` flag), and the guardrails (deep reads **only the flagged slice**; closure **within-repo only**); `docs/TECH_SPEC.md` §5.6 (coarse/deep contract + the D6c material threshold); `context_set/code_map.json` §3.3 (the `depends_on`/`used_by` edges the closure seeds from); `docs/REQUIREMENTS.md` **FR-BR-07**, **FR-BR-12/13**, **D6b/c**, **FR-DC-13** (single-repo within-repo boundary).
- **Why / when.** The deep pass is where requirement→code impact is actually established: it must walk the dependency graph **outward to a fixed point** ("until the affected surface is closed"), in **both** directions (callees via `depends_on`, callers via `used_by`), and it must **extend** the closure from the real source when the map missed an edge — not stop at the map's first-hop neighbours. If it terminates after one hop, follows only one direction, or trusts only map edges, the ripple is **under-reported** → scope-widening `scope_ripple` flags get missed and G1 inherits a too-narrow surface. This task **measures** closure correctness + depth; it does **not** redesign the deep pass.
- **Do (assessment-first, then propose — propose-never-bless):**
  1. **Trace a known fixture through the deep pass.** Use `fixtures/c_repo/` (the signed-off map/oracle): pick a requirement whose true impact is **multi-hop** (A→B→C callees; plus a caller D that `used_by` → A). Record the closure + `ripple` the deep pass actually returns.
  2. **Check correctness:** does it follow **both** `depends_on` and `used_by`? Does it iterate to a **fixed point** (the surface is genuinely closed — no un-expanded frontier node), or stop at depth 1? Does it **extend** the closure from source for a map-omitted edge (seed an oracle edge the map lacks → confirm the source pass recovers it)?
  3. **Check depth adequacy:** any reachable closure node missed (false-negative ripple)? Is the within-repo boundary (FR-DC-13) respected as a *boundary*, not used to stop early *within* the repo?
  4. **Findings artifact:** per requirement, the expected closure (from the oracle) vs the produced closure — nodes hit / missed / over-reached — each cited to the skill line + map edge (**cite-or-flag**; never invent a missed node).
  5. **Propose** additive remediation ONLY where a gap is proven — sharper both-directions / fixed-point / source-extends guidance in the deep-mode prose of `code_impact_assess.skill.md` — as a reviewable diff a human **freezes**. No new seam; ripple still surfaces as a **Flag** (never auto-widen scope); never branch on `domain`.
- **Acceptance:** a written closure-correctness assessment over ≥1 multi-hop fixture requirement showing produced `ripple` == the oracle closure (or each divergence flagged); a demonstration that the deep pass follows **both** edge directions and reaches a **fixed point** (not depth-1); a map-omitted edge proven recovered from source; any proposed skill diff is human-frozen; `build_checks.py` (§10 ×5) green; the deep pass still reads only the flagged slice (no whole-repo read) and stays within-repo.
- **Proof:** a `fixtures/c_repo/` requirement with a 3-hop callee chain + a caller edge → the deep pass's `ripple` lists every node in the oracle closure; a deliberately map-omitted edge is still surfaced (source-extends proven); a single-hop control requirement does **not** over-report.

---

## Milestone 5B — BRD completeness loop (source-grounded auto-fill, pre-G1)

### TASK-081 — Source-grounded auto-fill loop before G1 (agent closes sourced gaps; human gets the rest)
- **Phase:** P5-B · **Depends on:** TASK-043 (`brd_validator` + G1), TASK-042 (the flag loop). · **Model:** Opus.
- **Reads:** `core/skills/brd_validator.skill.md` (the soft-gate: score §9.2, section-level gap suggestions, G1 eligibility = `score ≥ threshold` ∧ required-topics-satisfied ∧ flags-resolved); `core/skills/brd_author.skill.md` (the per-section loop, the *"loop back and revise"* rule, **Loop exit**, the hand-off to `brd_validator`); `docs/TECH_SPEC.md` §9.1/§9.2 (G1 + the two **absolute** preconditions); `docs/REQUIREMENTS.md` **D4 / FR-XS-13** (machine soft-gate — informs, never auto-advances), **FR-BR-08/13** (the human-mediated flag loop), the **cite-or-flag** rule; `core/scripts/gate.py` (`G1` evaluate).
- **Why / when.** Today the `brd_validator → brd_author` re-entry is **human-triggered for *every* gap** — even a gap whose answer **already exists in a source** and the author simply didn't route or cite it. Those are *retrieval misses*, not knowledge gaps: re-reading the source and grounding the claim is the author finishing its own job, **not** invention. This task automates the **return trip for the source-closable subset only**, and leaves everything unsourced (and everything scope-moving) on today's human path. The branch condition **is** cite-or-flag — not a fuzzy "can the agent fix it". **This amends a pinned contract** (the D4 soft-gate interpretation + the validator/author loop) — treat it as a ladder amendment **+ ADR**, not a silent build.
- **Do (assessment-first, then propose the amendment — propose-never-bless):**
  1. **Classify each validator gap** by the cite-or-flag line into three buckets: **(a) source/frame-closable** (a source or the `UI_INPUT` frame answers it — a routing/citation miss); **(b) unsourced** (`[TBD]` — no corpus answer); **(c) scope-moving** (tied to a material / `scope_ripple` flag).
  2. **Add a bounded pre-G1 grounding loop** for bucket (a) **only**: hand the gap back to `brd_author` to re-route the section's source slice, ground the `must_capture`, emit the coverage footer, then re-validate. **Bounded** (cap iterations, e.g. 2–3) **+ monotonic-progress guard** (each pass MUST strictly shrink the source-closable gap set or raise `brd_score`, else stop and flag) — no thrash, no oscillation.
  3. **Route buckets (b) and (c) unchanged:** unsourced → human in-chat fill (today's path); scope-moving → the operator-decided flag loop (FR-BR-08). **Never invent** a value to close a gap (cite-or-flag) — surfacing an unsourced gap stays the correct outcome.
  4. **Keep D4 intact:** the loop runs **before** G1; G1 acceptance stays the operator's act; the two **absolute** preconditions (every required topic satisfied, all flags dispositioned) stay human-gated regardless of score; the validator still **never advances the pipeline**.
  5. **Audit every auto-fill:** each agent-made grounding is recorded to `decisions.jsonl`/telemetry tagged **agent-made**, so the operator at G1 sees auto-filled vs human-filled and can spot-check.
  6. **(Optional) minimal floor:** decide whether a too-sparse draft (below a low floor) skips the auto-loop and goes straight to human — distinct from the G1 acceptance bar (default 85), which is **unchanged**.
  7. **Author the ADR** capturing the D4-interpretation amendment + the loop contract; amend the §9.2 prose to match.
- **Acceptance:** a source-closable `must_capture` gap **auto-closes** (grounded + cited, `brd_score` rises) with **no human turn**; an **unsourced** gap still flags to the human in-chat; a **scope** flag still routes to the operator; the loop **terminates** (iteration cap + monotonic guard — proven not to thrash); every auto-fill is recorded as **agent-made** in the ledger; **D4 preserved** (G1 stays human; the pipeline never self-advances; required-topic + flags-resolved stay absolute); **cite-or-flag never violated** — Goodhart-safe: the score moves only when a real source backs the fill; `build_checks.py` (§10 ×5) green.
- **Proof:** a fixture BRD seeded with three gaps — **(a)** a `must_capture` a bundled source covers but the author missed → **auto-closed in-loop**; **(b)** a `must_capture` with no source answer → **human flag**; **(c)** a `scope_ripple` material flag → **operator flag**; the loop respects its iteration cap and stops on no-progress.
- **Port note:** amends `docs/REQUIREMENTS.md` D4 / FR-XS-13 interpretation + `docs/TECH_SPEC.md` §9.2 + the `brd_validator`/`brd_author` loop contract — back-port with the new ADR.

---

# Milestone 5C — deferred / candidate tasks (not scheduled; capture only)

> Scale-driven or exploratory items surfaced during 5B design discussion. **Not** part of the 5B
> build. Listed so they aren't re-litigated — promote to a numbered task only when the trigger
> condition is actually hit.

- [ ] **TASK-082 (candidate) — Section-as-subprocess BRD authoring with persisted state (context-overflow scale-out)**
  - **Trigger / when.** Only when a single BRD authoring run is large enough that the **continuous
    `brd_author` context window would overflow** (many sections over a big corpus). At MVP / typical
    scale (one PDF + one repo, a handful of sections, comfortably one window) this is **not needed** —
    the single-context loop is both cheaper and safer.
  - **Idea.** Today `brd_author` runs the per-section loop in **one continuous context window**;
    shared memory = the live session **+** the incrementally-written `BRD.md` (FR-BR-05). The candidate:
    run **each section as its own sub-process**, seeded from **persisted state** (the `BRD.md`-so-far
    **plus** the decision/Q&A log), so the run can complete without holding the whole draft + all
    prior source slices resident at once.
  - **Why it's deferred, not done now (the cost/benefit).** Sections are **inherently sequential**
    (section N depends on section N-1's draft) → **no parallelism** to win; the accumulating draft must
    be carried regardless, so context savings are **marginal** (you only shed prior sections' source
    slices, already bounded by selective-read + per-source summarize). And `BRD.md` alone is
    **insufficient** shared memory — the operator Q&A not yet written into a section lives in the live
    session, so a sub-process seeded with only the draft risks **re-asking** (FR-BR-05 violation) unless
    the full decision/Q&A log is persisted + passed too. Net: pay isolation's costs without its benefits
    — **until** the window can't hold the run, which is the one regime that flips it.
  - **Design constraints if promoted.** Keep section authoring **synthetic** (multiple sources still
    co-resident *within* a section — do **not** fan out within a section; that breaks conflict
    reconciliation + coverage). Persist **both** the draft and the decision/Q&A log so "never re-ask"
    and cross-section **loop-back-and-revise** survive the hop. Trigger on a **context-size threshold**,
    not by default. Mirrors the existing `code_impact` subagent pattern (fan out the *independent* work;
    keep the *sequential/synthetic* work in one window).
  - **Reads (when picked up):** `core/skills/brd_author.skill.md` (the per-section loop, "Revisiting &
    shared memory" FR-BR-05, the `code_impact` subagent delegation); `docs/REQUIREMENTS.md` FR-BR-04/05,
    NFR-05 (selective read at any corpus size).

- [ ] **TASK-083 (candidate) — Chunk/segment-level source granularity (finer-than-document tagging + retrieval)**
  - **Trigger / when.** Only for **large individual documents** — a sprawling spec or a big Confluence
    KB page — where **document-level** tagging is too coarse (the whole doc tagged `routing` because one
    passage mentions it, so a section pulls the entire doc/summary). At MVP / normal doc sizes this is
    **over-engineering**: document-level tagging + the per-source summarize already give the right
    granularity for a small curated corpus.
  - **Idea.** Today tagging is **per document** (§3.2: one manifest entry per doc, document-level
    `topics`); per-section retrieval loads whole matching doc bodies/summaries
    (`file.topics ∩ section.topics ≠ ∅`). The candidate: an LLM **pre-chunks/segments** a doc into
    coherent pieces, tagging happens **per chunk**, and per-section retrieval pulls **only the relevant
    chunks** → tighter context, less noise, finer (passage-level) citations. (Allowed: the model-free
    rule governs the **code** map build, not the doc pipeline, which is already model-driven.)
  - **Lighter first rung (prefer this before full chunking).** Make `article_summarize` /
    `confluence_tag` emit a **topic-segmented summary** (the digest organized by topic) so retrieval
    pulls the **relevant segment** of the summary — **no §3.2 schema change** (still one entry per doc),
    document coherence preserved, retrieval still gets finer. Full chunk-level manifest is the heavier
    escalation only if segmented summaries prove insufficient.
  - **Why deferred, not done now (cost/benefit).** The two wins (noise, size) are **already largely
    mitigated** by selective-read-by-section + per-source summarize, so the marginal gain is smaller
    than it looks. Costs: **coherence loss** (chunks drop surrounding context → harder cross-chunk
    synthesis, and authoring is synthesis-heavy); chunking is a **new lossy model-driven step** (a bad
    cut splits a coherent argument — a new failure mode); and full chunk-level retrieval is a
    **§3.2 manifest-contract change + ADR**, not a small edit.
  - **Design constraints if promoted.** Start with the **segmented-summary** rung (additive, no schema
    change); escalate to chunk-level manifest only if needed. Preserve **document-level coherence** as a
    fallback (a chunk must carry enough context to be faithfully citable — cite-or-flag). Same
    **document-size trigger** family as TASK-082 (don't enable by default).
  - **Reads (when picked up):** `core/skills/brd_author.skill.md` (selective-read routing, the
    `file.topics ∩ section.topics` rule); `core/profiles/payment_brand/adapter/article_summarize.skill.md`
    (the summary it produces); `docs/TECH_SPEC.md` §3.2 (manifest entry shape — the contract a chunk
    model would amend); `docs/REQUIREMENTS.md` FR-BR-04 (selective read), the cite-or-flag rule.

- [ ] **`purpose`-diff as a semantic-drift signal (idea, unnumbered).** The code-map cache key is the
  structural `commit_sha`, so a component whose *structure* is unchanged but whose *behaviour* changed
  re-tags identically today. Diffing `purpose` between commits would surface that drift. Noted as
  lower-value than TASK-066/067; promote only if the real corpus shows the miss.

---

# Build-and-port discipline (reminder)

This repo is the **external Claude Code build**. Do not add VDI/Copilot-air-gap accommodations into
the generic core — the port is a separate, later artifact (thin overlay files + `port_check` per §5.7
+ the user-scope allow-list runbook per FR-XS-26). Keep the core agent-agnostic; the runtime-tool seam
is the only thing the port touches. Real API/secret calls follow hard rule **S**: one isolated
placeholder function per call, edited in place on the VDI.

**Carry these port notes forward:** the JPMC-side D5 table still needs the TASK-061 `code_map_build`
fix for `card_brand`/`message_format`; the JPMC-side spec still needs the TASK-063B §6.6.3/§10.5
`docs_pipeline` routing extension and the D9 `start-ingest` amendment.
