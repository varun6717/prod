# TASK_VDI.md — Milestone 5B build list (execute on the VDI with Copilot)

**What this is.** The Phase 5B enhancement tasks, packaged to be executed **on the JPMC VDI**
with Copilot (Opus 4.8). The MVP (BRD→FRD, single domain, SharePoint + Bitbucket) is running;
this file adds breadth one task at a time. The canonical specs also live in `TASK_LIST.md`
(TASK-060–081; TASK-063B added here after TASK-063, pending back-port) — this file is the
**VDI operating manual** around them: the rules, the
execute→verify→publish loop, and the environment specifics.

**How to use it.** Pick the first unchecked task, top-down. For each task, follow the
**Execution protocol** below. Tick the box only when every Acceptance condition is true and the
proof + build checks are green. Disk + git are ground truth.

---

## Execution protocol (run this loop for EVERY task)

1. **Read the cited design first.** Each task names the exact `docs/…` §sections and files under
   **Reads** — open them. Do not work from memory; the cited section is the contract.
2. **Verify dependencies exist** (the **Depends on** files). If one is missing, stop and say so.
3. **Implement the GENERIC piece.** Build what is testable here. For anything that must hit a
   **real external API or secret store**, do NOT inline it — isolate it in **its own function**
   carrying a `[TBD — VDI]` placeholder (raises `NotImplementedError`), plus an **offline
   local-path convenience** so the connector runs end-to-end here (see **Hard rules** §S). On the
   VDI you **edit that one placeholder function in place** to add the real call + JPMC auth (the
   way `ingest_sharepoint.py`'s `_download_pdf` was wired). Keeping the env-specific call in its
   own function is what makes that a clean, no-merge-conflict edit.
4. **Verify.** Run the task's **Proof** and then **`python core/scripts/build_checks.py`** — all
   5 §10 checks must be green. A connector also runs its `fixtures/<type>/verify_*.py`.
5. **Publish so the UI run sees it** (only after green):
   `python core/scripts/publish_registry.py <registry-repo-url> --branch feature/pdlc_app`
   then delete the stale run workspace and **re-Generate** from the UI to test end-to-end.
   (Local edits are invisible to the UI until the registry is re-published.)
6. **Tick the box** and (if the VDI can push to GitHub) push so the external copy stays current.

---

## Hard rules (never violate — condensed from `CLAUDE.md` / `docs/`)

- **S. Build-and-port / edit-in-place discipline.** Generic code is shared and built+tested first;
  any real API/secret is **isolated in its own function** carrying a `[TBD — VDI]` placeholder
  (raises `NotImplementedError`) plus an **offline local-path convenience** so the piece runs
  end-to-end in the external build. On the VDI you **edit that one placeholder function in place**
  to add the real call + JPMC auth (the way `ingest_sharepoint.py`'s `_download_pdf` was wired) —
  **no `/vdi` plugin folder, no auto-load hook, no separation.** Keeping the env-specific call in
  its own function is what makes the in-place VDI edit collision-free. (V decision, 2026-06-30 —
  this supersedes the prior `/vdi`-plugin rule.)
- **Two seams only.** The **domain seam** (adapter / profiles / template / vocabulary) and the
  **runtime-tool seam** (instruction file / wrappers / prompts / launch). The per-language
  **extractor** is the one non-domain variation point, governed by the **onboarding gate**.
- **Binding rationales.** The structural extractor is **deterministic + frozen** — never
  model-rewritten at runtime. The map-build gate is **model-free**. The model owns only
  `purpose` + `tags` in the code map. **Ingestion never branches on `domain`.** The **only**
  external mutation of a run is the Jira push. Scope changes are operator-decided.
- **Descriptor parity.** Every source connector emits the **same descriptor shape** as
  `ingest_file.py` (`type, source, url/…, staged_path, auth_ref, ingest_ts`). Downstream
  (`pdf_extract → article_summarize → change_type_assess`) must not change.
- **Onboarding skills: propose-never-bless.** The onboarding aids (extractor/domain/profile/
  adapter) **propose reviewable artifacts**; a human **freezes**. Amendments are **build-time**
  (committed + re-pinned), never runtime mutations. §10 build checks gate every freeze.
- **Cite-or-flag.** Every substantive artifact claim is grounded to a source/frame/operator
  answer or marked `[TBD — unsourced]`. Never invent.
- **§10 must stay green.** No task lands with a red build check. Connectors keep §10.4; the
  domain seam keeps §10.1/10.3/10.5; overlays keep §10.2.

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

# The tasks (TASK-060 – 081, dependency order; + TASK-063B after 063)

> Full canonical spec for each is in `TASK_LIST.md`. Open the **Reads** there if you need more
> than what's below.

## Carried fixes (independent, small — good warm-ups)

- [x] **TASK-060 — Thread `runtime_tool` through G1/G2 telemetry** *(built+verified external; pending VDI port)*
  - **Reads:** `core/scripts/brd_validator.py` / `frd_validator.py` (`record_g1`/`record_g2`); `docs/TECH_SPEC.md` §8.1.
  - **Do:** replace hardcoded `tool="claude"` in the validators' telemetry `Emitter` with `UI_INPUT.runtime_tool`.
  - **Acceptance:** a copilot run's G1/G2 envelopes record `tool: copilot`; build_checks green.
  - **Done (external):** added `_runtime_tool(ledger_dir)` helper to both validators (reads `runtime_tool` from the run's sibling `UI_INPUT.yaml` — same pattern as `_run_id`; falls back to `claude` for the standalone proof). Proofs green; copilot-path test → envelopes carry `tool: copilot`; build_checks 5/5 green.

- [x] **TASK-061 — Reconcile D5 `card_brand`/`message_format` `emitted_by`** *(built+verified external; pending VDI port)*
  - **Reads:** `CLAUDE.md` port note; `docs/REQUIREMENTS.md` D5 table; `vocabulary.payment_brand.yaml` (already r2).
  - **Do:** add `code_map_build` to `emitted_by` for `card_brand` + `message_format` in the D5 table.
  - **Acceptance:** D5 table == `vocabulary.yaml`; §10.5 green.
  - **Done (external):** D5 table updated; table-parse vs `vocabulary.yaml` confirms all 12 tags' `emitted_by` match exactly; §10.5 green. Stale port notes in `vocabulary.yaml` + `CLAUDE.md` updated (external reconciled; JPMC-side D5 still to fix at port).

- [x] **TASK-062 — Align `UI_INPUT.example.yaml` frame with the bundled PDF** *(skipped — cosmetic, V-decided 2026-06-30)*
  - **Reads:** `fixtures/UI_INPUT.example.yaml`; the bundled PDF (Mastercard mandate).
  - **Do:** the frame says "Discover" but the PDF is the Mastercard mandate — align title/intent.
  - **Acceptance:** frame matches the fixture; verify_frontend/backend green.
  - **Skipped (not implemented):** cosmetic only — the Discover/Mastercard mismatch is confined to the static example fixture (and greyed UI placeholder text); it never reaches an operator-driven run (the real `UI_INPUT.yaml` is generated from live UI form input into `<working_path>/UI_INPUT.yaml`, not from this fixture). No code, no runtime effect. Closed without change by V decision; revisit only if the example is used for a demo where coherence matters.

## Connectors

- [x] **TASK-063 — Confluence connector (`ingest_confluence.py`)** *(built+verified external; pending VDI port)*
  - **Depends:** TASK-055 (`ingest_sharepoint.py` pattern), TASK-052 (auth seam).
  - **Reads:** `ingest_sharepoint.py` + `ingest_file.py`; `docs/TECH_SPEC.md` §6.6.2, §3.2; FR-DC-01/11/12.
  - **Do:** generic source-type-keyed connector, same descriptor as `ingest_file.py`, `auth_ref: jpmc_adapters:confluence`, no domain branch. **Real Confluence fetch isolated in its own `_fetch_confluence` placeholder function (`[TBD — VDI]`), edited in place on the VDI** (mirrors `ingest_sharepoint.py`'s `_download_pdf` — no `/vdi` plugin). Offline local-path convenience. One link = one page.
  - **Acceptance:** a `type:confluence` source stages content + contract-valid descriptor (offline local path); §10.4 maps `type:confluence → ingest_confluence.py` green; no domain branch.
  - **Proof:** `fixtures/confluence/verify_confluence.py`.
  - **Done (external):** `core/scripts/ingest_confluence.py` mirrors `ingest_sharepoint.py` — `pull_page()` emits the exact `ingest_file` descriptor keys; `_fetch_confluence` is the lone `[TBD — VDI]` placeholder (edit-in-place; `set_fetcher` seam for tests); offline local-path convenience; auth resolved **lazily** (local path needs no auth). `main()` stages **multiple** `type:confluence` entries (one page each). Fixtures: `fixtures/confluence/{discover_routing_kb,message_format_kb}.html` (real KB pages — reuse for the 063B tag-set decision) + `verify_confluence.py` (13 checks: parity, two-links→two-entries, injected-fetcher auth/no-secret-on-disk, placeholder-fails-loud, §10.4, no-domain-branch). Proof green; build_checks 5/5. **VDI:** edit `_fetch_confluence` with the real REST call + auth; no other change.
  - **Note:** the connector stages Confluence content unchanged; it does **not** tag (emits nothing). Real *processing* of a Confluence page (it is HTML, not a PDF → `pdf_extract` is wrong for it) is **TASK-063B** below — that's where the `confluence` docs_pipeline lane + tagging lands. 063B is **required** for an end-to-end Confluence BRD run (not optional).

- [x] **TASK-063B — Per-source-type doc-pipeline routing in `adapter.yaml`** *(built+verified external; pending VDI port)*
  - **Done (external):** (1) `adapter.yaml` `docs_pipeline` → two-lane mapping (`default` 3-step PDF lane + `confluence: [confluence_tag]`), back-compat bare-list preserved. (2) `confluence_tag.skill.md` authored — tag-only (no extract/summarize/change-type), emits `[brand_rules, card_brand, message_format, routing, transaction_flow, error_handling]` (validated against the two KB fixtures; `certification` deliberately excluded — passing mention only). (3) `vocabulary` `emitted_by` += `confluence_tag` on those 6 tags, `vocab_sha d5frozen-r2 → -r3`. (4) `build_checks` §10.5 + `adapter_emit_tags` now **union across lanes** + require a `default` lane; `source_processor.skill.md` routes the doc arm by `src.type` (`select_docs_pipeline`, never `domain`). (5) UI enabled: removed the Confluence `deferred` flag (PDLCConfigurator ~L335) + wired `buildConfig` in `emit.js` (was sharepoint/bitbucket only) + `sample_form.json` Confluence URL; `verify_frontend` now asserts Confluence emits (Lucid still deferred). (6) TECH_SPEC §6.6.3 + §10.5 amended. **Proofs:** `fixtures/adapter_routing/verify_adapter_routing.py` (11 checks: distinct lanes, back-compat, union, `default`-required guard, real-seam green), `build_checks` 5/5, `verify_confluence`/`verify_sharepoint`/`§10.1`/validators green. `verify_frontend` emit-path green; its Generate-to-G0 leg needs `fastapi` (not installed here — runs on VDI/full env). **VDI:** re-publish registry; rebuild the SPA (`vite build`) so the un-deferred Confluence row ships; then a `type:confluence` source runs end-to-end once `_fetch_confluence` is wired (TASK-063).
  - **Depends:** TASK-063 (`ingest_confluence.py` — the motivating 2nd doc type), TASK-017/019 (the `payment_brand` adapter pack already authored).
  - **Reads:** `docs/TECH_SPEC.md` §6.6.3 (`adapter.yaml` schema + the pack contract), §10.5 (adapter coverage/no-drift check); `core/skills/source_processor.skill.md` (the doc/code routing, lines 79–92); the **Descriptor parity** hard rule above; FR-XS-01, D7.
  - **Why / when.** Today `docs_pipeline` is a **single flat list** run on *every* doc-class source regardless of `type`. That breaks for Confluence: a page is **HTML, not a PDF**, so `pdf_extract` is wrong/inert for it, and a KB page wants a different (tag-only `confluence_tag`) step, not `article_summarize`/`change_type_assess`. There is currently **no routing within the doc class** — `source_processor` picks the pipeline by *class* (doc vs code) only, never by `src.type`. This task adds that missing routing **additively** (the generic worker stays domain-blind) and authors the Confluence lane. **Required** for an end-to-end Confluence BRD run (063 only stages the page).
  - **Do (ladder amendment — this touches a pinned contract; amend the design as part of the task):**
    1. **Extend the `adapter.yaml` `docs_pipeline` schema** (§6.6.3) to allow either form, back-compatibly:
       - a **bare list** (current form) → treated as the `default` pipeline (every existing pack stays valid, byte-for-byte); **or**
       - a **mapping** keyed by source `type` with a required `default` fallback, e.g.
         ```yaml
         docs_pipeline:
           default:    [pdf_extract, article_summarize, change_type_assess]   # PDFs / files
           confluence: [confluence_tag]                                        # Confluence KB pages — tag-only
         ```
       Each entry still carries its `emits:` per skill. Routes by **type**, never `domain`.
    2. **Update `core/skills/source_processor.skill.md`** step 2 (the doc arm): within the doc class, select the pipeline variant by `src.type`, falling back to `default` when no variant matches. Still no `domain` branch; descriptor parity is **preserved** — only the *processing* pipeline differs, never the connector's descriptor shape.
    3. **Update build check §10.5** (`core/scripts/checks/`) so the coverage + no-drift assertions run across the **union** of all variants' `emits` (a `required: true` topic must be produced by *some* reachable pipeline), not just a single flat list. Amend the §6.6.3 + §10.5 prose to match.
    4. **Author `core/profiles/payment_brand/adapter/confluence_tag.skill.md`** — the Confluence lane's single tagging skill. **Tag-only** (no `pdf_extract` — Confluence is already text; no `article_summarize` — a KB is reference, not an article; no `change_type_assess` — a KB page is steady-state, not a change). It reads the staged KB page and assigns the "how it works" tag subset. **Cite the page, don't paraphrase** (grounding fidelity for reference material).
    5. **Amend the vocabulary `emitted_by` (the §10.5 no-drift consequence — DO THIS, it is required).** `confluence_tag` is a new *emitting* skill, so every tag it emits must add `confluence_tag` to its `emitted_by` in `vocabulary.payment_brand.yaml`, or §10.5(c) per-tag set-equality drifts red. `emitted_by` is the **contract**; derive `adapter.yaml`'s `confluence_tag.emits` *from* it. **Bump `vocab_sha`** (`d5frozen-r2 → -r3`). Candidate emit set (DECIDE against the fixtures, don't blind-copy): `[brand_rules, card_brand, message_format, routing, transaction_flow, error_handling]` — the steady-state "how it works" tags the KB fixtures actually carry; **not** `mandate`/`compliance_deadline`/`certification` (change/compliance-driven, from mandate PDFs). NB `error_handling` is code-only today → adding `confluence_tag` makes it doc-emittable; confirm the fixture page truly describes it before claiming the tag.
    6. **Enable Confluence in the UI (coordinated — do NOT do in 063).** Remove `deferred badge="5B — deferred"` from the Confluence `SourceRow` in `app/frontend/src/PDLCConfigurator.jsx` (~line 335) so multi-link Confluence works exactly like PDFs (add/remove rows; each URL → its own `type: confluence` source entry — emit + backend validation + auth already support this). **Update `fixtures/frontend/verify_frontend.py`** (currently asserts at ~lines 94–95 that `confluence` is NOT emitted / deferred) to assert Confluence **is** emitted. The served UI needs a `vite build` to pick up the source change (dist/ is stale otherwise).
  - **Design decisions (concluded with V, 2026-06-30 — DO NOT re-derive):** (a) **063B is required**, not optional — Confluence is HTML, so `pdf_extract`/the default lane is wrong for it; a Confluence BRD run needs the lane. (b) **Tag-only, single `confluence_tag` skill** — no summarize/no change_type (rationale in step 4). (c) **One link = one page**; multiplicity is per source-entry fan-out (each page → own slice → own topics → retrieved per section via `file.topics ∩ section.topics`), already handled by 063 + the existing orchestrator — no special "multiple" code needed. (d) **Optional digest sub-decision:** if real KB pages prove **large**, give the lane a bounded `confluence_extract` (emits `[]`, size-control only) before `confluence_tag` — summarize is the per-source size lever that keeps section context bounded; start tag-only, add only if proven. (e) The BRD profile already lists `sources: [confluence, sharepoint]` and the auth seam already has `confluence` — **no profile/auth change needed**.
  - **Acceptance:** a 2nd doc `type` (confluence) routes to a **distinct ordered pipeline** (`[confluence_tag]`); a bare-list `adapter.yaml` still parses identically (back-compat proven); §10.5 coverage/no-drift green across **all** variants (incl. the new `emitted_by` for `confluence_tag`); `source_processor` still never branches on `domain`; the connector descriptor shape is unchanged (parity holds); `payment_brand` PDF runs unaffected; UI offers Confluence and `verify_frontend` asserts it emits.
  - **Proof:** an adapter fixture with two doc types → two pipelines (add `fixtures/adapter_routing/`); a fixture KB page (`fixtures/confluence/discover_routing_kb.html`) through the `confluence` lane → `confluence_tag`'s tags land on its manifest entry; `python core/scripts/build_checks.py` → 5 green; `verify_frontend.py` green with Confluence emitted.
  - **Already in place from 063 (reuse):** `core/scripts/ingest_confluence.py` (stages pages), `fixtures/confluence/{discover_routing_kb,message_format_kb}.html` (the two KB pages to tag), `verify_confluence.py`.
  - **Port note:** this amends `docs/TECH_SPEC.md` §6.6.3 + §10.5 — carry the schema extension into the JPMC-side spec at port time.
  - **Sequencing:** numbered `063B` (not `079`) on purpose — it is the routing half of the Confluence work and should run **immediately after TASK-063**, not at the end of the list.

## Jira (the only external mutation + G3)

- [ ] **TASK-064 — Jira authoring + validation skills + `jira_template`**
  - **Reads:** `docs/TECH_SPEC.md` §9.4, §10.3; FR-JR-*, FR-XS-17.
  - **Do:** `core/skills/jira_author.skill.md` + `jira_validator.skill.md`; add `jira_template` to the `payment_brand` seam (then §10.3 requires it).
  - **Acceptance:** a fixture FRD → jira plan authored + gated; §10.3 checks `jira_template` (green); no push yet.

- [ ] **TASK-065 — Jira push seam + `jira_plan/` + `trace.json` + G3**
  - **Depends:** TASK-064, TASK-052.
  - **Reads:** `docs/TECH_SPEC.md` §3.8, §7, §9; FR-JR-*.
  - **Do:** generic Jira-push connector with the real JPMC Jira REST call isolated in its own `[TBD — VDI]` placeholder function, edited in place on the VDI (no `/vdi` plugin); emit `jira_plan/` + `trace.json`; gate **G3** before push. Push is the **only** external mutation — operator-confirmed.
  - **Acceptance:** G3 gates; stub push records `trace.json`; no secret on disk; build_checks green.

## Code-impact enhancements (real-corpus value)

- [ ] **TASK-066 — `purpose`-as-discovery in the coarse pass**
  - **Reads:** the TASK-040 coarse pass; ADR-005.
  - **Do:** let the coarse pass use `purpose` for semantic candidate **discovery** (surface a component whose `purpose` fits the requirement even when the tag wasn't applied). Advisory + cite-or-flag; never silently widen scope. Refinements (V-approved 2026-07-02): (a) every candidate carries `matched_by: tag | purpose | both`; (b) a `purpose`-only hit also lands in the §5.4.1 vocab-adequacy ledger (under-applied/missing-tag evidence — links to TASK-067); (c) module-first descent (`components[].purpose` first, file purposes only within matched modules); (d) the semantic query is the `UI_INPUT.frame` **text** (+ relevant `context_set/`, + drafted BRD reqs), not just topic names.
  - **Acceptance:** a mis-tagged-but-`purpose`-relevant component surfaces as a flagged candidate with `matched_by: purpose`; the hit also lands in the vocab-adequacy ledger; no file-level compare outside matched modules; deep-pass closure unchanged.

- [ ] **TASK-067 — Doc-side semantic-gap signal**
  - **Reads:** ADR-005 open-Q #2; the code-side `uncovered_concepts`.
  - **Do:** add a doc-arm analog of `uncovered_concepts` so §5.4.1 vocab-adequacy is symmetric across both arms.
  - **Acceptance:** the doc arm emits a leftover-meaning signal; §5.4.1 considers both.

## Multi-repo

- [ ] **TASK-068 — Multi-repo cross-repo closure**
  - **Reads:** `docs/TECH_SPEC.md` §3.3 (`external_calls`/`exposes`); FR-DC-18.
  - **Do:** populate the reserved cross-repo fields in `code_map.json` + cross-repo closure; multi-repo clone (N repos/run).
  - **Acceptance:** a 2-repo run maps cross-repo calls; closure surfaces cross-repo impact; single-repo unaffected.

## Domain onboarding (proposer skills → orchestrator)

- [ ] **TASK-069 — `extractor_onboard` skill + a 2nd language extractor**
  - **Reads:** `docs/TECH_SPEC.md` §5.7, ADR-001, FR-DC-19; `docs/ENV_PRECHECK.md`.
  - **Do:** skill proposes/refines an extractor against a sample → reviewable artifact for human **freeze**; onboard a 2nd language (Java/Python). Structural-only, **model-free build**.
  - **Acceptance:** a 2nd-language extractor onboarded + frozen vs an oracle; §10 green; build stays model-free.

- [ ] **TASK-070 — `domain_onboard` skill (propose a new domain's vocabulary)**
  - **Depends:** TASK-069. **Reads:** ADR-003, FR-DC-20; `vocabulary.payment_brand.yaml`.
  - **Do:** propose a new domain's first `vocabulary.<domain>.yaml` from sample docs + the untagged (`purpose`-only) code-map → reviewable artifact (propose-never-bless).
  - **Acceptance:** 2nd-domain samples → a freezable `vocabulary.<domain>.yaml`; §10.1 holds once frozen.

- [ ] **TASK-071 — `profile_onboard` skill**
  - **Depends:** TASK-070. **Reads:** ADR-004, FR-DC-22, FR-BR-08.
  - **Do:** route approved tags into profile sections — surface unconsumed tag, propose section `id` + `must_capture`/`probe_if_missing` → reviewable **profile diff**. Bulk + incremental. Build-time only (§6.6.1).
  - **Acceptance:** an unconsumed tag → a freezable profile diff; no runtime mutation.

- [ ] **TASK-072 — `adapter_onboard` skill (+ promote `pdf_extract` to `core/skills/`)**
  - **Depends:** TASK-070, TASK-071. **Reads:** ADR-005, FR-DC-23, §6.6.3; the F1+3 drift class.
  - **Do:** propose the adapter pack by guided conversation; **derive each skill's `emits` from the vocabulary's `emitted_by`** (kills the drift class). Bulk + incremental. Promote `pdf_extract` to `core/skills/` first. Propose-never-bless.
  - **Acceptance:** proposes a pack whose `emits` == `emitted_by` by construction; §10.5 no-drift green.

- [ ] **TASK-073 — Domain-onboarding orchestrator (`onboard.py` + `ONBOARD_INPUT.yaml`)**
  - **Depends:** TASK-069..072, TASK-048. **Reads:** the `onboard.py` design in `TASK_LIST.md`; §6.6.1, §10, Appendix B.
  - **Do:** `mode: onboard` — authoring pull → run the four helpers **in order** with a human **freeze gate** each → `build_checks.py` as a **HARD GATE** (red ⇒ no push) → commit + push to Bitbucket → emit new `registry_sha`. `mode: run` consumes (unchanged). Push = build-time git action, not a runtime mutation.
  - **Acceptance:** a new domain authored end-to-end → §10 green → pushed → `registry_sha` emitted; red §10 blocks push.

- [ ] **TASK-074 — Multi-domain enablement (`domains_index.yaml` + UI)**
  - **Depends:** TASK-073. **Reads:** FR-BR-11/14, FR-XS-21, D2; the UI `DOMAINS` list.
  - **Do:** add `domains_index.yaml` + drive the UI domain dropdown from it (instead of hardcoded `payment_brand`).
  - **Acceptance:** a 2nd domain appears in the UI + Generates a correctly-pruned scaffold; `payment_brand` unaffected.

## Vocabulary adequacy (L2)

- [ ] **TASK-075 — `vocab_gap_assess` + amendment loop**
  - **Depends:** TASK-013 (L1 detector). **Reads:** ADR-003, FR-DC-21.
  - **Do:** model pass over the newly-introduced untagged delta → propose a candidate tag + evidence; human-gated amendment → `vocab_sha` bump → re-tag pass.
  - **Acceptance:** an untagged delta → proposed tag + evidence; amendment bumps `vocab_sha` + re-tags; no auto-mutation.

## Infra / UX (lower priority)

- [ ] **TASK-076 — Metrics store + dashboard (SQLite)** — promote the JSONL ledger to a queryable store + dashboard, additive (JSONL stays source of truth). FR-MX-*, D8.
- [ ] **TASK-077 — Auto-launch** — automate the manual start gesture where the environment permits (Claude-only first). FR-XS-25.
- [ ] **TASK-078 — UI enhancements** — role gating on the configurator + a richer live telemetry/metrics surface. FR-XS-*.

## BRD discovery quality

- [ ] **TASK-079 — Assess discovery-question adequacy (up-front + throughout the BRD)**
  - **Reads:** `core/skills/brd_author.skill.md` — its `## Discovery (FR-BR-02)` framing pass (the *up-front* questions) **and** the per-section `probe_if_missing` loop (the *throughout* questions); `core/profiles/payment_brand/brd_profile.payment_brand.yaml` (`must_capture` / `probe_if_missing` per topic); `docs/REQUIREMENTS.md` **D1** (the `must_capture`/`probe_if_missing` schema), **FR-BR-02** (up-front framing discovery — 2–3 clarifying questions), **FR-BR-03** (throughout gap-fill, limited to unsatisfied `must_capture`), **FR-BR-05** (never re-ask / shared memory), **FR-BR-09** (`brd_validator` coverage score → G1); the `start-brd` prompt and — for the pre-BRD handoff — `start-ingest`.
  - **Why / when.** The BRD's quality is bounded by what the author *asks*. Two question moments exist: an **up-front** pass (what `brd_author` elicits before drafting, seeded from `must_capture`) and a **throughout** pass (the `probe_if_missing` loop as sections fill). Today neither is measured — a `must_capture` topic with no eliciting question, or a frame-relevant topic with no probe, silently becomes a `[TBD]` instead of a question. This task **measures** that coverage, then proposes additive fixes; it does **not** redesign the BRD flow.
  - **Do (assessment-first, then propose — propose-never-bless):**
    1. **Inventory** where discovery questions originate today: the up-front pass and the `probe_if_missing` loop. Write the inventory.
    2. **Evaluate adequacy** against the frame + sources + code surface: for each `must_capture` topic, is there a question that elicits it when the sources are silent? Any frame-relevant topic with **no** probe? Does the author probe before assuming, or drop `[TBD]` without asking?
    3. **Findings artifact:** per-topic coverage (covered / under-probed / missing), each cited to the skill/profile line (**cite-or-flag** — never invent a gap).
    4. **Propose** additive remediation **only in the domain seam** — new/strengthened `probe_if_missing` entries in `brd_profile` and/or sharper elicitation guidance in `brd_author.skill.md` — as a reviewable diff a human **freezes**. No runtime mutation; never branch on `domain`.
  - **Acceptance:** a written up-front + throughout coverage assessment mapping every `must_capture` topic to its eliciting question or flagging the gap; a proposed (human-frozen) profile/skill diff that closes the identified gaps; G1 still gated by the same validator; `build_checks.py` (§10 ×5) green; the `payment_brand` BRD run is unaffected unless the diff is frozen.
  - **Proof:** run a fixture BRD (the bundled Mastercard-mandate PDF) through `brd_author` with deliberately **sparse** sources → the proposed probes fire for the silent topics; the coverage report lists no un-probed `must_capture` topic.

## Code-impact depth (deep-pass ripple / closure)

- [ ] **TASK-080 — Verify the deep-pass code-ripple closure traces correctly and goes deep enough**
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

## BRD completeness loop (source-grounded auto-fill, pre-G1)

- [ ] **TASK-081 — Source-grounded auto-fill loop before G1 (agent closes sourced gaps; human gets the rest)**
  - **Reads:** `core/skills/brd_validator.skill.md` (the soft-gate: score §9.2, section-level gap suggestions, G1 eligibility = `score ≥ threshold` ∧ required-topics-satisfied ∧ flags-resolved); `core/skills/brd_author.skill.md` (the per-section loop, the *"loop back and revise"* rule, **Loop exit**, the hand-off to `brd_validator`); `docs/TECH_SPEC.md` §9.1/§9.2 (G1 + the two **absolute** preconditions); `docs/REQUIREMENTS.md` **D4 / FR-XS-13** (machine soft-gate — informs, never auto-advances), **FR-BR-08/13** (the human-mediated flag loop), the **cite-or-flag** rule; `core/scripts/gate.py` (`G1` evaluate).
  - **Why / when.** Today the `brd_validator → brd_author` re-entry is **human-triggered for *every* gap** — even a gap whose answer **already exists in a source** and the author simply didn't route or cite it. Those are *retrieval misses*, not knowledge gaps: re-reading the source and grounding the claim is the author finishing its own job, **not** invention. This task automates the **return trip for the source-closable subset only**, and leaves everything unsourced (and everything scope-moving) on today's human path. The branch condition **is** cite-or-flag — not a fuzzy "can the agent fix it". This **amends a pinned contract** (the D4 soft-gate interpretation + the validator/author loop) — treat it as a ladder amendment **+ ADR**, not a silent build.
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

---

> ✅ **A task is done when:** Acceptance true · its proof green · `build_checks.py` (§10 ×5) green ·
> the registry re-published (so the UI run uses it) · box ticked. Come back to the external
> Claude Code session for help when a task fights you — paste the failing proof / build-check.
