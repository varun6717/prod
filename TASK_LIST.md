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
- [x] TASK-103 — `UI_INPUT` v2 (D-A12/D-A13): `core/scripts/dispositions.py` is the single taxonomy definition (shared by backend validation + the §10.5′ check at TASK-108); every source carries `disposition` as a **list** (one-or-more, default one), `codebase` auto-set for repo sources and rejected on doc sources (and vice versa); `frame.overview` required (§1 identity, seeds §7, Arm 1's query context); UI gains a per-doc-row disposition selector + Initiative Overview; scaffold gains `solution_intent/`. Proof: 8 validation probes (7 reject, multi-disposition accepts), emit honors operator pick *and* type default, all 8 fixture verifies green, §10 3/3. Also fixed two TASK-100/102 fallouts: `verify_generate`'s stale prompt names, `verify_registry`'s negative test deleting the retired vocabulary
- [x] TASK-102 — Runtime-tool seam re-cut: `overlay_manifest.yaml` transcribed from D11.7 (8 roles — `solution_intent_*` ← `brd_*`, + `claim_verifier`/`disposition_walkthrough`, `frd_*` out; `prompt_files [start-ingest, start-si, start-enrich, start-jira]`; invocability = D-A23 interactive set); renames landed (skills + `solution_intent_validator.py` + wrappers + prompts, both tools) with identifier swaps; 4 new-role wrappers + 4 skill stubs (`claim_verifier`/`disposition_walkthrough`/`jira_author`/`jira_validator` — full content TASK-119/120/122/123); `instruction_file.template.md` stage narrative re-cut to SI→enrichment→Jira; `generate_instruction.py` gestures re-pointed; parity `_demo` re-cut. Proof: §10.2 green (8+4 both tools), demo green, §10 3/3, no `brd_`/`frd_` filename remains, every wrapper pointer resolves

**Phase D · Milestone D1 — Input side**
- [x] TASK-104 — Ledger stages + enrichment event vocabulary: stage vocabulary → `ingest / si_v1 / enrichment / si_v2 / jira` (both schemas + `telemetry.STAGES` + `ledger.SLICE_STAGES`; `code_map` folds into `ingest` as the code lane of the fan-out, `jira` merges authoring+push — the `jira_push` *event* survives); three enrichment events with typed emitters — `verdict` (`finding_id`, `arm` `impact`|`claim`, `verdict`, `route`), `escalation` (`reason` = the four D-A16 triggers, `severity` for D-A17 triage), `disposition` (`call` `accept|reject|reroute|defer` — the D-A16 defer path, `target`); `decisions.py` gains the `disposition` walkthrough record — the **only** place the operator's rationale is written (writer enforces `reject` has no `target`, placing calls do); `runs/_template/ledger/` refreshed to 5 stages. **`verdict.route` is the M12 enrichment-yield feed** (corrections/derived impacts/auto-fills = three counts over one field). Proof: 10 negative + 9 positive schema cases incl. retired-stage rejection in both ledgers, full-pipeline `_demo` (M01 $/SI-v1, M02 $/enrichment, M12 yield, G2's every-escalation-answered precondition all derivable), §10 3/3, all 8 fixture verifies green. *(Left for their owners: `validation.artifact` stays `brd/frd/jira` → TASK-110/121/123; `metrics_scan.py` still pre-pivot → TASK-125, now carrying a STALE banner; `vocab_gap_flag` kept until §3.6 consolidates — its producer died at TASK-100.)*
- [x] TASK-105 — Manifest v2 + disposition routing + adapter shrink: entry shape v2 in `merge_manifest.py` (`topics`/`change_type` out, `disposition` list + `index_path` in; `index_path` **normalized to null** so the field is always present; entries with no/empty/non-list/unknown `disposition` and entries still carrying a retired field are **rejected loudly at fan-in** — an unroutable entry is one silently never read, the exact invisibility the totality rule targets; `merge_manifest` becomes the 4th consumer of `dispositions.py`); `source_processor.skill.md` routing rule replaced — **two keys, neither is `domain`**: `type` → connector + lane, operator `disposition` → which SI sections may read it (copied verbatim, never inferred, never branched on); `adapter.yaml` shrunk to `domain` + `docs_pipeline: [pdf_extract]` + `code_pipeline: [code_map_build]` (the `emits` map, both tag lanes and the F1+3 reconciliation gone with the vocabulary; the 063B per-type mapping *mechanism* still stands — the pack just has one lane); `pdf_extract.skill.md` de-tagged and **takes over the entry `descriptor`** as a *transcribed* identification line (title/ID/part-of-N/printed dates), the interpretive summaries staying with `doc_index` at TASK-106 — ⚠ contract detail the ladder does not pin, flagged for V. Fixtures re-cut: `merge_manifest/` (exercises multi-disposition + a carried `index_path` **and** a normalized null), `pdf/expected_manifest_entries.json` + `gen_fixtures.py` (the two mandate parts now demonstrate the D-A12 BizReq/TechSpec split that motivated the taxonomy), `verify_confluence.py` + both connector docstrings de-tagged. Proof: new `merge_manifest.py --demo` — corpus merge, D8c failed-source row, byte-identical replay vs the committed oracle, 6 rejection negatives; both acceptance greps literally clean; §10 3/3; all 8 verifies green. *(Left for its owner: §10.5's "every `docs_pipeline` skill file exists / mapping carries a `default`" residue was **not** implemented in `build_checks.py` — a dangling pack pointer was unchecked. **Folded into TASK-108's §10.3** by amendment, same session.)*
- [x] TASK-106 — Per-artifact index + completeness (guardrail 7): 🆕 `core/skills/doc_index.skill.md` — the doc arm's twin of `code_map_build`, resolving the D-A18 home question (impact §12 left it open as "source_processor step vs own skill"): a **shared core skill, not a pack skill** (an index describes a document, never a domain — rule 4) and **not an overlay role** (no wrapper, no `overlay_manifest` change, §10.2 untouched — exactly `code_map_build`'s precedent), which also preserves `source_processor`'s "I do not author meaning" principle. 🆕 `core/scripts/checks/check_index_completeness.py` — guardrail 7 (family 2, ingest-time, **not** a §10 check, so `build_checks` stays 3): `lines_total == lines_indexed`, every line in **exactly one** entry (gap *and* overlap), counts reconciled to the real `.md`, subdivisions reconciled **both** directions; also hosts `needs_index_consult()` (over the **SET**, FR-SI-03) + `demote_order()` (largest first). 🆕 `core/retrieval_config.yaml` — `whole_read_threshold_lines: 500`, `max_entry_lines: 25`, `extract_wrap_columns: 100`; not in `UI_INPUT` (§3.1's amendment pins exactly two additions) and not in the pack (retrieval is domain-agnostic). Lane wired: `adapter.yaml` gains `doc_index` after `pdf_extract`; `source_processor` gains the index step, `index_path` population, and guardrail 7 as a **hard gate on its own output** (a gapped index is worse than none → failed/partial slice with a reason). 🆕 `fixtures/doc_index/` (9 files): 4 extracts + 4 index oracles + `verify_doc_index.py`. Extracts were transcribed from the fixture PDFs via an AST replay of `gen_fixtures.py` (**no PDF tooling on this box** — no pdftotext/pypdf/poppler; the PDFs are generated deterministically from those literals, so they are the page text). Proof: `check_index_completeness --demo` — 4 oracles total, 7 negatives each caught **by the named check** (gap, overlap, miscount, unrecorded split, declared-split-no-parts, blank summary, missing index); `verify_doc_index.py` — 18 checks incl. the degraded case, rule-4 destination scan, identifier presence, D-A12 typing, set-level threshold; §10 3/3; all 9 verifies green. **Findings:** (a) *prose must be wrapped* (`extract_wrap_columns`) — an unwrapped extract puts a 200-word clause on one line and makes every `lines` range degenerate; this is now `pdf_extract`'s contract; (b) the **degraded case is real in the existing fixtures** — part 1 §4 is 28 lines with zero sub-headings, split `4a/4b/4c` at the Gate C1/C2/C3 paragraph seams and recorded in `subdivided[]` (the verifier asserts the region genuinely has no headings, so the case can't silently stop being one); (c) *build always* ⇒ `index_path` is populated for **every** doc entry, so TASK-105's fixture was updated and the null-normalization guard moved to a unit case. ⚠ **Two ladder discrepancies flagged, not forked:** D-A18's shape shows `disposition` as a bare **string** — used a **list** per D-A12 and the manifest entry; and its `pages` field is **omitted** (a Markdown extract carries no page boundaries — omitted rather than guessed, per cite-or-flag).
- [x] TASK-107 — `ingest_jira.py` connector (Prior Artifact source type): 🆕 `core/scripts/ingest_jira.py` mirroring TASK-063 — `_fetch_issue` the lone `[TBD — VDI]` placeholder, `set_fetcher` seam, lazy auth via `PDLC_AUTH_JIRA`, local-path convenience, exact descriptor parity with `ingest_file`. **One shape departure, deliberate:** a Jira issue is a JSON *payload*, not a document, so `_fetch_issue` **returns a dict** (the document connectors write bytes to a path) and the connector renders it to the staged `.md` itself. The rendering stays inside "connectors assign no meaning" — a fixed field→heading table, values copied verbatim, nothing summarised or reordered; absent fields **omitted** (never empty-rendered or invented) and fields the table doesn't know collected under "Other fields" rather than dropped (totality). That split also keeps the VDI edit a pure "make the network call" change. 🆕 `fixtures/jira/` — `PBI-4471.json` (rich epic, incl. an unknown `customfield_*` to prove no silent drop) + `PBI-4602.json` (deliberately sparse, to prove omission) + `verify_jira.py` (**39 checks**: descriptor parity, mechanical+total rendering, two issues → two entries, injected fetcher through the auth seam with a canary-leak scan, placeholder fails loud naming the VDI, §10.4 green, no `domain` branch, `prior_artifact` default + its reference-only hazard). UI: Jira row in `PDLCConfigurator.jsx` (+ YAML preview) · `emit.js` (`AUTH_REF`, `DOC_DISPOSITION_DEFAULT.jira = prior_artifact`, source loop) · `sample_form.json` (row deliberately **omits** `disp` so the proof exercises the type default) · `verify_frontend.py`. Also: `app/backend/validation.py` `_SOURCE_REQUIRED_FIELDS` gains `jira` — **not in the task's file list but required**, or the backend 422s the row the UI now emits (proven: POST /generate → 200 with the Jira source); and `SourceRow` gained a `defaultDisp` prop — its select hardcoded `business_requirement` while `emit.js` falls back per type, a latent divergence now closed. `VDI_WIRING.md`'s pre-written Jira item updated with the real fixture paths + the returns-a-dict note. Proof: `verify_jira.py` green · all **10** verifies green · §10 3/3 (§10.4 includes `jira`) · **`npx vite build` clean** (the TASK-103 note — fixture verifies drive `emit.js` through the Node bridge and never compile the JSX).

**✅ Milestone D1 complete** — input side closed: ledger vocabulary, manifest v2 + disposition routing, per-artifact index + guardrail 7, and all four source types connected.

**Phase D · Milestone D2 — Solution Intent v1**
- [x] TASK-108 — `si_profile` (18 sections) + §10.5′ disposition-class totality: 🆕 `core/profiles/payment_brand/si_profile.payment_brand.yaml` — all 18 sections, each carrying `authored` (D-A3) · `touch` + `touch_note` (D-A3/D-A4) · `status` + `conditional_reason` (D-A10) · `classes`/`inputs` (the D-A13 row) · `boundary` (§4/§9/§15, D-A11) · `must_capture[]` · `probe_if_missing[]`. **`classes` and `inputs` are separate keys on purpose:** D-A13 draws one table but its columns are two kinds of thing — `classes` keys are D-A12 dispositions matched against a manifest entry's `disposition` (a routing key), while `frame`/`discovery` are the operator as an input source and never appear on an entry. Splitting them means the §10.5′ class check needs no list of keys to ignore. `brd_profile.payment_brand.yaml` **deleted**; its pointers renamed `brd_profile → si_profile` across both skills, the validator, 4 overlay wrappers and 2 prompt files (pointer rename only — the substantive recasts stay TASK-109/110). 🆕 `core/scripts/checks/check_disposition_totality.py` (§10.5′) — checks **both directions** (section-side alone passes a taxonomy with a dead class; class-side alone passes a profile with a starved section), plus fixed-18 membership, conditional marking, and cell/key well-formedness; registered in `build_checks.py` → **4/4**. §10.3 re-cut: `brd_profile` → `si_profile` **and** the folded-in **pack-pointer assertions** — every `docs_pipeline`/`code_pipeline` skill resolves to a file in the pack *or* shared `core/skills/`, and a mapping-form `docs_pipeline` carries its `default` lane (063B). 🆕 `fixtures/si_profile/verify_si_profile.py` — the **cell-identity oracle** acceptance #1 needed and nothing else covered: D-A13, D-A3 and D-A10 re-typed independently from the ADR and compared cell by cell (§10.5′ proves *totality*, which would happily pass a complete-but-wrong matrix). `dispositions.py` gains `NEVER_ROUTED = {other}` + `NON_DISPOSITION_INPUTS` — **`other` routes nowhere by design** (D-A12: "the empty column IS the definition"), and declaring it as data rather than special-casing it inside the checker matters because that checker's whole job is catching orphan classes; a buried exception would be indistinguishable from the bug it hunts. Proof: `build_checks --demo` 4/4 clean + **5 injected defects each turning the NAMED check red** (incl. the dangling `article_summarize` pointer — the exact TASK-100→105 state that stayed green); `check_disposition_totality --demo` 8 negatives; `verify_si_profile.py` **144/144 cells**; all **11** verifies green.
- [x] TASK-109 — `solution_intent_author` recast: full rewrite of `core/skills/solution_intent_author.skill.md` (the TASK-102 rename had held the old BRD content). **The headline change is that v1 is CODE-BLIND** (FR-SI-02) — the old skill delegated a coarse `code_impact` pass during discovery; that delegation is **deleted**, and the skill now says why: if code informed v1 there would be nothing for enrichment to discover (the v1→v2 diff *is* the stage's value story), the author would anchor requirements to what the code already does, and §13's assumptions — the payload Arm 2 verdicts — are only worth writing if written unseen. `codebase` is `E` in every D-A13 row, so a repo source routes nothing. Also recast: the baseline+profile **merge machinery is gone** (the 18 sections are fixed, not assembled); the two-level funnel replaces topic routing (level 1 deterministic by disposition, level 2 index-guided by `must_capture` over the routed **SET**); sequential groups carrying the draft forward (explicitly contrasted with Arm 1's independent iteration, which would fragment a section); §7-before-§8 with `D<n>`/`R<n>`/`R<n>.<m>` stable IDs and mandatory `Deliverable:`; assertions split until each is independently checkable (**§16 granularity IS story granularity — decided here**); conditional dispositions proposed-not-decided; provenance-tiered citations that determine *who may correct the claim later* (D-A6); §13 authored in checkable form; §17 v1-authored; §1 last. Both wrappers refreshed (code-blind, no delegation, produces `v1.md`, G1 freezes). 🆕 `fixtures/si_author/` — `UI_INPUT.yaml` (MCS-2026-R3 initiative over the 4 doc artifacts + the repo, dispositioned per D-A12) · **`v1.md` — a real authored v1**: 18 sections, 5 deliverables, 12 requirements, **44 assertions**, **118 resolving citations**, 2 conditionals N/A-with-reason + 1 filled, 4 `[TBD — unsourced]` closing into 5 §17 questions · `verify_si_author.py` (**48 checks** across 10 groups). The verifier **assembles the corpus at verify time from `fixtures/doc_index/` and fans it in with the real `merge_manifest.py`**, so the manifest citations are checked against is pipeline-produced and the extracts cannot drift from the doc-index oracles. Proof: every `[src: … L<a>–<b>]` resolves to a manifest entry *and* a line range that exists in that extract; §7↔§8 and §15↔§4 traces intact both directions; code-blindness asserted against a corpus that really does contain a `codebase` source; §10 4/4; all **12** verifies green.
- [x] TASK-110 — `solution_intent_validator` + G1 + v1 freeze: `solution_intent_validator.py` recast — score `0.7×section_coverage + 0.3×citation_integrity` (`must_capture` items satisfied / total; **§16/§18 and dispositioned-N/A conditionals excluded from the denominator**, or a complete v1 would be capped below 90 forever and an honest N/A would be penalised), plus **7 named hard preconditions** (`sections_complete`, `conditionals_dispositioned`, `gaps_declared`, `trace_15_to_4`, `trace_8_to_7`, `assertions_enumerated`, `flags_resolved`), each reporting *every* violation by name. Parsing is now **deterministic** — the SI's structure (fixed 18, `D<n>`/`R<n>`/`R<n>.<m>`, machine-readable footers, explicit line ranges) needs no model, unlike BRD prose; the skill supplies only the **substantive-claim counts**, which are genuine judgment. ⚠ **Design call worth reviewing:** a *declared* gap costs score but does **not** block — if one unsatisfied `must_capture` made v1 ineligible, cite-or-flag would punish honesty and reward a fabricated citation; what blocks is an **undeclared** gap (an `open` that never reaches §17). 🆕 `freeze_v1()` — on accept, v1 is hashed into `v1.frozen.json` and set read-only; the **digest is the real guard** (a file mode anyone can flip makes tampering possible, a recorded hash makes it *detectable*), proven by a post-freeze edit being caught. `record_g1` refuses an accept on an ineligible result; `reopen` freezes nothing. `telemetry.schema.json` `artifact` enum → `si_v1 | enrichment | jira` (the TASK-104 follow-up), `telemetry.py` demo updated. 🆕 `fixtures/si_validator/{si_fail.md, README.md}` — **one defect per precondition** so the failure report is checkable violation-by-violation; the pass case is `fixtures/si_author/v1.md` **used directly rather than copied** (a 35KB duplicate would drift, and the proof owes a G1 accept on *that* artifact — deviation from the task's `si_pass.md`, documented in the README). Building the fail fixture **found a real bug**: a conditional saying bare "Not applicable" with no reason passed as ordinary content, and an absent conditional was skipped entirely — both exactly what D-A10 forbids; the parser now matches the reasonless form specifically in order to reject it. Proof: authored v1 scores **92**, eligible, all 7 ✓; broken v1 names all 6 document-expressible violations; a *passing* score with 1 unresolved flag is still ineligible; §10 4/4; all 12 verifies green.
- [x] TASK-111 — Discovery-question adequacy: the assessment D-A13 forces — *discovery is primary for exactly §9/§12/§13, so retrieval buys them nothing and their quality rests entirely on question quality*. **Inventory:** questions come from exactly two places — the up-front framing exchange (deliberately shallow: "do not try to pre-fill sections") and per-section `probe_if_missing`. So the probes carry essentially all the adequacy burden. **Found 19 unelicited `must_capture` items, 7 in the discovery-primary three** — incl. §9's "how does it advance that program" (the old probe asked what the portfolio would *lose*, which is stakes not mechanism), §12's "what are we excluding **and why**" (never asked directly), §13's "what does each risk hinge on", and §11's per-deliverable accountability — **which the TASK-109 v1 had already hit as its open question Q2 ("Who owns D1–D4?")**, so the assessment predicted a gap the real run demonstrated. Two §13 probes were also *weak*, not absent: "what are we assuming?" reliably elicits general beliefs — the exact shape D-A4 calls worthless to enrichment — so it now says "name the component, system or behaviour each assumption is about, so it can be checked against the code later". **Closing diff (frozen):** `probe_if_missing` entries become `{ ask, elicits: [<must_capture indices>] }` — the load-bearing half, since it turns the mapping from prose someone reads once into **data a check verifies**; an unverified mapping is exactly how 19 gaps accumulated. 🆕 `core/scripts/checks/check_discovery_adequacy.py` — **tiered on purpose**: a gap in §9/§12/§13 is an **error** (unrecoverable — no source can cover it), in an operator-fed section a **warning** (a document may), and probes on derived sections (§1/§16/§17/§18) are a category error. Family-2-style ingest/authoring check, **not** a §10 check (build_checks stays 4). 🆕 `docs/design/discovery-adequacy-assessment.md` — the written assessment, cited to profile/skill sections. Proof: **50/50 elicited, zero §9/§12/§13 gaps**; 5 negatives each caught at the right tier; and the **sparse-corpus proof** — routing only `product_domain_knowledge` starves **nine** sections to zero artifacts (incl. §9 and §12), where probes are not a fallback but the *only* path to content, and all nine remain fully elicitable. Author skill updated to ask by `elicits` rather than reading the probe list out. §10 4/4; all 12 verifies green.

**✅ Milestone D2 complete** — Solution Intent v1 closed: the 18-section profile, the code-blind author, G1 + the v1 freeze, and discovery adequacy proven against a sparse corpus.

**Phase D · Milestone D3 — Code map v2**
- [x] TASK-112 — Extractor declared-purpose extraction + `c_repo` additive pass: `c_extractor.py` gains deterministic declared-purpose extraction (D-A20) — leading comment block → `purpose_declared` + **`purpose_declared_line`** (the point of `declared` over `inferred`: it is **citable to a line**, human ground truth rather than the model's reading) + `declared_version`/`declared_date` + `purpose_quality`. **Label matching is fuzzy (edit-distance ≤1) against an alias SET passed in as profile data**, because assuming one keyword would have been a **5.7× under-report** on the real corpus (`Intention:` is only 17% of declarations → ~10% reported vs a real 58%), and because `Putpose` ×4 is a real typo. One edit is measured, not chosen. Parser noise (`http` from URLs, licence boilerplate) refused; generic purposes **flagged not dropped** (3.3% of the corpus — tier 1 must down-weight them, not confuse them with absence). `coverage_report` gains the declared-purpose split the D-A21 gate reports on. `extractor_sha` re-frozen `125a6ca → ed703ff` (build-time amendment, never a runtime rewrite). Fixture additive pass: **21/35 files (60%) declared under 6 label forms + the typo**, 14 deliberately headerless (the fallback population), and the versioned-duplicate pair `iso8583.c` + `iso8583_v2.c` — **both wired, neither dead**, which is the hazard: an assertion about message parsing must answer v1/v2/both and the code cannot say. The extractor emits **two ordinary files** with no duplicate marking; surfacing the pair is the map build's job (D-A16), never a silent agent pick. Oracle + `SIGNOFF.md` amended: the new entry was **derived by reading the source and predicted before running the extractor** (which then agreed), so the hand-authored-oracle rule holds; SIGNOFF marked **PENDING RE-SIGN-OFF** since the oracle changed. `PATTERN_CATALOG.md` documents both phenomena. Proof: 🆕 `fixtures/c_repo/verify_declared_purpose.py` — **33 checks**: byte-identical double run, every label form incl. the typo, headerless files declaring nothing, the duplicate pair as two ordinary files, each cited line actually containing its purpose, noise refused, and the narrow-alias run reproducing the 5.7× under-report (3 vs 21). §10 4/4; all 13 verifies green.

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

**Milestone D3 — Code map v2**
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

## Milestone D3 — Code map v2

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
- **Open question to settle here (raised 2026-07-31):** `docs/` is **published** to the registry
  (it is in `registry_manifest.trees`) but **not hydrated** into a run workspace — `hydrate.py`
  copies only `core/` + `overlays/<tool>/`. Yet the instruction file and the skills cite paths
  like `docs/TECH_SPEC.md §5.3`, which therefore resolve against the registry checkout rather
  than relative to where the agent is working. Confirm during the real run whether agents can
  actually follow those citations. If not, the fix is adding `docs/` to `hydrate.py`'s copy set
  — a one-line change, not a design change.

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
