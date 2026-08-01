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
- [x] TASK-113 — Repo profile scan + onboarding gate report (D-A21 phase 1): `validate_onboarding.py` recast from oracle-grader to **the gate** — profile scan (label variants + coverage · include density/resolution · prefix tokens · `.h` placement · versioned duplicates · **degree-zero-both-directions** isolation · symbol presence) → deterministic stage-B sample → projected stage distribution + stage-C cost → the **D-A21 report** → the three actions → freeze. The report is built around the *three things a plain approval cannot do*: the **human-authored vs model-inferred split** (the quality ceiling — 85% declared is a fundamentally better substrate than 60% inferred, and invisible without the split), **tier-1 entries against target** (the economy problem while it is still cheap), and the **uncovered set named** rather than implied away. 🆕 `core/code_profiles/` — the per-repo signal-profile contract + README (why it is a *separate* seam from the per-language extractor freeze: two C repos need different *reading rules*, which is per-repo not per-language) + the frozen `c_repo.profile.yaml`. All three actions implemented and proven to **compose**: `adjust profile` (recompute is deterministic graph arithmetic, so iteration is cheap; an unknown parameter **raises** rather than silently doing nothing), `skip stage C` (**deferral not exclusion** — files fall through to C*/unanalyzable, total conserved, reduction visible in the report, reversible via the per-file-hash purpose cache), `group singletons` (model **proposes**, human approves **per group**, approved groups freeze as membership **data**). Freeze emits `profile_sha` keyed on **semantic content only** — it moves on a rule change (what makes **gate branch 4** possible) and **not** on a re-signature (else every cached map would invalidate when someone re-signs). **Two defects the rendered report exposed in my own scan:** a `.c`/`.h` pair sharing a stem was being reported as a versioned duplicate (burying the one real hazard in noise — now keyed on `(base, extension)` *and* requiring a genuine `_v2`/`_old` variant), and a **28-file single cluster scored as ✓** because a low tier-1 count looks good — it is actually the *worse* failure, since tier 1 then filters nothing; both size bounds and the collapse case are now flagged. Proof: 🆕 `fixtures/c_repo/verify_onboarding_gate.py` — **35 checks** across the report, the scan, each action, composition, the freeze, and post-freeze determinism. §10 4/4; all 14 verifies green.
- [x] TASK-114 — Map build recast (two files, modules, purposes) + context checks: 🆕 `core/scripts/code_map_build.py` — the deterministic half (D-A21 steps 7–15) writing `code_map/{components.json,files.json}`; **the derivation is imported from `validate_onboarding`, never reimplemented** — the gate showed a human a specific module breakdown and they approved *that*, so a second implementation that drifted would make the approval meaningless. Purpose ladder **A declared → B header prose → C whole-file → C\* symbols → unanalyzable-with-reason**, cached per **file content hash** (not path: a renamed-but-unchanged file keeps its purpose, a changed one loses it). Model steps are **injectable seams** (`inferrer`/`verdicter`/`synthesizer`) so it is visible where judgment enters and where it does not. Confidence tracks purpose *quality*, and **low confidence widens tier 1 rather than excluding** — a purpose that cannot be trusted to describe a cluster cannot be trusted to rule it out. 🆕 `core/scripts/checks/check_map_totality.py` (family 2, in-build, **not** §10): module totality, purpose totality, `members[]`↔`files[].module`, **no module purpose is a verbatim copy of a member's** (only checkable because synthesis runs after resolution), `unclustered` carries `always_pass_tier1`, low-confidence modules listed. `code_map_build.skill.md` full recast. Oracle reshaped: `expected_code_map.json` **deleted** → `expected_components.json` + `expected_files.json`; **`SIGNOFF.md` re-frozen** with an explicit note that this oracle *is* build-generated — a deliberate change of kind, since hand-transcribing module-derivation-from-a-frozen-profile would be copying an algorithm, not checking it; it now guards **change detection**, while first-principles correctness moved to the property checks. **A defect the build exposed:** stage C\* scanned only for function *bodies*, so all 9 declaration headers fell to `unanalyzable` — a header's prototypes **are** its exported symbols, and the body-only scan was manufacturing the exact silent invisibility C\* exists to prevent (now 1 genuine unanalyzable, named with a reason). Also corrected TASK-113's frozen profile to **not** skip stage C — composing all three actions proved they compose, but skipping C on a 35-file repo is not what an operator would sign. Proof: 🆕 `verify_code_map.py` — **24 checks**: oracle match ×2 (byte-identical), no `tags` anywhere, family-2 green, no copied synthesis, every declared purpose still citable to its line, **35 cache hits / 0 misses on rebuild**, the versioned pair surfaced for disposition rather than resolved, and the map naming **no requirement** (requirement-blind). §10 4/4; all 15 verifies green.
- [x] TASK-115 — 4-branch gate + map cache: `gate.py` recast — **`retag` deleted** (it existed for a vocabulary-only amendment and there is no vocabulary; nothing tags, so nothing can be re-tagged) and `profile_sha` joins the key. Four branches: **1 onboard** (no extractor *or* no repo profile — nothing frozen to build against, and inventing rules at runtime is what the binding rule forbids) · **2 reuse** (both shas match ⇒ literally no work) · **3 incremental** (commit moved — structure/clustering recomputed globally, purposes only for changed content hashes) · **4 full rebuild** (`profile_sha` changed). `GateDecision` gains **`repurpose_all`**, which makes D-A21's asymmetry a machine-readable fact rather than prose: **a profile change invalidates wholesale, a commit change selectively** — if the hub threshold moves, every module boundary can move with it, so nothing in the old map is trustworthy. 🆕 `gate.affected_modules()` implements the wrinkle: re-synthesis is **wider than "modules containing changed files"**, because clustering is global — a module can need re-synthesis because a file *left* it, leaving its synthesised purpose describing a membership that no longer exists. 🆕 `core/scripts/map_cache.py` — `cache/code_maps/index.yaml` upsert + the per-file purpose cache, with the two keys answering different questions: `(commit_sha, profile_sha)` asks *is this map valid at all*, the file content hash asks *is this purpose valid* — and that split is exactly what makes branch 3 incremental. Proof: 🆕 `fixtures/c_repo/verify_gate_branches.py` — **21 checks** walking every branch against a **real repo and a real cache** (cache-correctness mistakes propagate silently, so asserting was not enough): reuse resolves **0/35** purposes, a one-file edit re-resolves **exactly 1** (34 hits) and names the affected module, a profile change **genuinely produces a different map** (16 modules → 7) rather than merely claiming to, and `gate.py` is asserted to contain no model call. §10 4/4; all 16 verifies green.
- [x] TASK-116 — Multi-language validation fixture (required, D-A19): `fixtures/mixed_repo/` extended from 5 token files into **three genuine dependency graphs** (C include graph · Python import graph · Java import graph); 🆕 `code_profiles/mixed_repo.profile.yaml` with **per-language sections** — one repo, one profile, one gate, one freeze (D-A22) — and **Java deliberately given no section**, which is what makes it the un-onboarded case. `build_map` is now **language-partitioned**: step 7 partitions and everything after runs *inside* a partition, with module identity **language-scoped by construction** (`c:settlement`, `python:scripts`). That is not cosmetic — two languages may both have a `settlement`, and merging them would put files with no possible edge between them in one module, after which tier 1 would match a C assertion into Java files and closure would try to walk an edge that cannot exist. Non-C languages get a **generic declared-purpose reader** rather than re-freezing the C extractor to teach it `#` comments (they have no frozen extractor at all — that is what makes them the fallback path), while sharing the same alias set and fuzzy matching, because a purpose label is a human convention rather than a language feature. **A defect this surfaced:** making the build language-aware meant the fixtures' own `verify_*.py` harness files became repo content — inventing a Python partition out of test code and making single-language `c_repo` look polyglot; `build_map` gained a caller-supplied `exclude` (core has no business knowing what a fixture's harness is named). Proof: 🆕 `fixtures/mixed_repo/verify_multilang.py` — **22 checks** over the four required properties incl. a **cross-language tier-1 transcript** (one settlement assertion matching `c:settlement` *and* `python:scripts` independently), zero cross-language edges with `external_calls`/`exposes` still reserved, Java landing in `java:unclustered` as `coarse`/`files_fallback` **with purposes intact** (degraded, never dropped), and `c_repo` asserted **unchanged** in the same run. §10 4/4; all 17 verifies green.

**✅ Milestone D3 complete** — code map v2 closed: declared-purpose extraction, the onboarding gate, the two-file map with totality checks, the 4-branch cache, and polyglot behaviour proven.

**Phase D · Milestone D4 — Enrichment (v1 → v2)**
- [x] TASK-117 — `enrichment.json` contract + finding routes: 🆕 `schemas/enrichment.schema.json` (per finding: id/arm/kind/refs/evidence/reasoning/verdict/action/route/disposition/rationale/**status**) + 🆕 `core/scripts/enrichment.py` — the record **and** the D-A16 router in one place on purpose, since both arms *and* the walkthrough consume it and a table implemented three times drifts twice. **Provenance decides authority, not the finding's content** (D-A6): the same contradiction auto-corrects (source-derived), escalates (operator/frame — never overrule a human silently), or auto-fills (unsourced `[TBD]`). **Scope-moving is tested first**, before grounding, because a perfectly evidenced source contradiction that moves a boundary is *still* an operator decision. `status` is per finding so the walkthrough is **resumable** (fifty findings will not be dispositioned in one sitting), undispositioned findings live **here and not in the document** (or v2 would ship with "TBD, awaiting operator" scattered through it), and no route can remove anything — a contradicted claim is *rewritten*, because at G2 an operator can see a changed sentence but cannot see a missing one. `v1_sha256` pins the frozen v1 the record was computed against, or "v1 + enrichment.json reconstruct v2" stops being true. **A defect the proof caught:** the schema's conditional requirements (`escalated ⇒ reason + severity`) used `if/then`, which `ledger.py`'s minimal validator **does not support** — so those constraints sat in the file *looking* enforced while validating nothing, which is worse than being absent; `if/then/else` added. Proof: 🆕 `fixtures/enrichment/verify_enrichment_router.py` — **38 checks**: every row of D-A16's table, one contradiction under four provenances yielding three routes, the no-code four-way with its **required defer path**, an auto-applied finding **refusing** to be dispositioned, and both ledgers stamped with the **rationale in `decisions.jsonl` and not telemetry** (telemetry counts; decisions explains). §10 4/4; all 18 verifies green.
- [x] TASK-118 — Arm 1: per-assertion impact (`code_impact` recast): skill fully recast around the three-tier walk — query is **raw text** (frame + title + description + assertion; a bare assertion demonstrably matches nothing), **`purpose` seeds and source establishes**, retrieval batched **per deliverable** while reasoning stays **per-assertion and independent** (anti-anchoring is a *correctness* rule: an inherited landing point means the second assertion is evaluated against the first's answer instead of against the code). 🆕 `core/scripts/tier_walk.py` — the deterministic core: `tier1` (low confidence **widens**, `unclustered` **always** searched — so tier 1 can only ever over-include, the correct failure direction), `tier2` (matched modules only), and `closure` (**both directions, to a fixed point**, with a `via` trail so the ripple is reviewable). Fixed point rather than a hop budget, because with a budget you cannot distinguish "nothing more to find" from "ran out". §16 granularity **is** story granularity, decided here. 🆕 `fixtures/code_impact/` tier-walk oracles (salvaging TASK-080's closure semantics). **A determinism hazard the oracle exposed:** `.c` and `.h` share an edge identity, and the resolver was last-wins — so which file an edge reached depended on enumeration order, and the ripple could differ between runs *while looking perfectly stable*; an identity now resolves to **every** file carrying it (one compilation unit). **Two weak checks I had written and replaced:** the "one-directional walk loses reach" control originally stripped `used_by` from the entries, which proves nothing since `merge_edges` derives it from other files' `depends_on` — a genuinely **directed** walk now shows 12 vs 19 files, 7 lost; and the `unclustered`-always-searched check was vacuous on `c_repo` (which places every file), so it moved to `mixed_repo`, whose un-onboarded Java partition genuinely has one. Proof: 🆕 `verify_tier_walk.py` — **28 checks**: multi-hop closure to its oracle fixed point, reverse-only files reached, a single-hop control that does not leak, a **source-recovered edge reaching 2 files the map cannot** (19 → 21), no-code gaps and versioned duplicates escalating rather than auto-building, and an implicit current-state assumption ("field 48 has room") surfacing with evidence. §10 4/4; all 19 verifies green.
- [x] TASK-119 — Arm 2: `claim_verifier`: the TASK-102 stub replaced with the full skill — the **three-way population sort** (factual current-state → verdict; business judgment and future-state → **skip, never touch**, because otherwise every business sentence acquires an `[unverified]` marker and the marker stops meaning anything); **cluster by code region, not by section** (section order is an authoring artifact, the code is what costs); the three coarse outcomes with **only one expensive**; and **no closure** — point lookup then stop, or Arm 2 blurs into Arm 1 and the same impact reports twice from two directions. 🆕 `enrichment.stage_claim()` enforces two rules in code rather than trusting the skill's discipline, since both failures would be invisible in the output: a **skipped sort produces no finding at all** (not an `unverifiable` one — marking a 200ms threshold "unverified against code" claims we looked, when the map knows what calls what and not how fast), and **§8 raises** (code cannot contradict an intent; rewriting a requirement from code inverts the ladder and lets the implementation dictate business intent). **Two defects the proof caught:** the schema required `evidence` on *every* auto-applied finding, which makes an honest `unverifiable` — where the **absence** of a match *is* the finding — literally unrepresentable (now required only for contradiction/gap-fill/derived-impact, where an unreviewable auto-correction is the real risk); and my seeded claims were **paraphrases rather than verbatim v1 text**, so the fixture was testing claims the document never made — now asserted verbatim. Proof: 🆕 `fixtures/enrichment/verify_claim_verifier.py` — **29 checks** over 9 claims lifted from the real fixture v1: a wrong **source-derived** claim corrects with provenance while the **identical** finding escalates when the claim came from an operator (authority follows provenance, not the verifier's confidence), a runtime-shaped NFR is skipped and *distinguishably* so, an unmatchable claim surfaces to §14 rather than being discarded, and §5 verdicts system actors while skipping human personas entirely. Wrappers repointed (code map + repo, **no doc indexes** — Arm 2 verdicts claims against *code*). §10 4/4; all 20 verifies green.
- [x] TASK-120 — Disposition walkthrough: the stub replaced with the full skill — **the one human checkpoint of the entire enrichment stage**. D-A17's four constraints implemented in `enrichment.py` rather than left to the skill's prose: 🆕 `triage()` (material **individually**, advisory **batched** — a one-at-a-time march through 200 findings is unusable *and flattens importance*, so a scope-moving discovery and a routine field-width consequence stop looking identical); 🆕 `walkthrough_order()` (**deterministic topological order** — upstream before what was derived from it, so the operator is never asked to judge a finding whose premise is still undecided, and an interrupted session resumes to the *same* queue rather than a reshuffled one); 🆕 `supersede_dependents()` (a `reject` on an upstream gap withdraws the premise under everything derived from it, **transitively** — and those findings are marked `superseded`, **never deleted**, so the trail still shows what was believed and why it stopped being believed); 🆕 `resume_point()` (per-finding status means the session survives being interrupted, and nothing already answered is re-asked). The **defer path is required, not a courtesy** — an operator who genuinely cannot answer must be able to say so, or the walkthrough pressures people into fabricating certainty exactly where the design demands honesty; it lands in §17 as a real open question. Proof: 🆕 `fixtures/enrichment/verify_walkthrough.py` — **26 checks** over a realistic session (one scope move, a no-code gap with two findings derived from it, an operator contradiction, and a 5-finding advisory batch): **all four call types exercised in one session**, transitive supersession, a lossless disk round-trip mid-session, and both ledgers stamped with the **rationale in `decisions.jsonl` and the counts in telemetry**. *(Also removed a tautological check of my own — `X is False or True` — that could never have failed.)* §10 4/4; all 21 verifies green.
- [x] TASK-121 — Apply pass + G2 + enrichment spine exercise: 🆕 `core/scripts/apply_enrichment.py` — **corrections revise in place with inline `[code: …]` provenance, discoveries append** (a correction twelve pages from the claim it corrects leaves a false statement in the body, and a silent rewrite of an accepted document is what the citation rule closes); nothing deleted; §16 written **by requirement** holding impacts *and* gaps; §17 **extended** never replaced; §18 counts only; **§1 regenerated LAST** from the corrected body (a summary of an uncorrected problem statement is silently wrong). Applying against a v1 whose digest doesn't match the record is **refused** — "v1 + enrichment.json reconstruct v2" only holds against the v1 the findings were computed on. `solution_intent_validator` gains **G2** with three hard preconditions, all shown blocking. ⚠️ **LADDER AMENDMENT — the provisional §9.3 formula was validated against the first real run and FAILED.** `impact_coverage` as written (`requirements_with_§16_entries_or_dispositioned / total`) scored a **complete, correct** run at **0.417** → G2 **71** vs threshold 85, because 7 of 12 requirements were fully analysed and found to need **no change**, so they carried neither a §16 entry nor a disposition. That is the *desirable* outcome — and worse, the formula made **manufacturing §16 entries the cheapest way to pass**, precisely the fabrication the grounding discipline exists to prevent. Amended to *requirements **Arm 1 reached*** (§9.3 + FR-EN-07 amended in-task, **port note added**); the run then scores 100. **Two other defects the spine caught:** an *accepted* escalated contradiction was never applied (the escalation was about **authority**, not about what the correction is — once accepted it lands like any other, and skipping it left the operator's own decision unapplied); and my §8-untouched check compared reassembled whitespace rather than content. Proof: 🆕 `fixtures/enrichment/verify_spine.py` — **31 checks** end-to-end: v1 byte-identical after the run, v2 deterministically reproducible from v1 + the record, rejected **and** superseded findings absent from v2 but present in the record, all three G2 preconditions blocking when seeded broken, and the G2 gate record in both ledgers. **Score discrimination shown separately** (a formula that only ever reads 100 is indistinguishable from none): 25 Arm-2 claims filed without verdicts drive `verdict_completeness` to 0.662 → score **83**, with all three preconditions still green — so the soft score covers Arm 2 claim completeness, which no precondition catches, and is not redundant. §10 4/4; all **22** verifies green.

- [x] *(housekeeping, post-TASK-123)* — three flagged residues closed: **`vocab_gap_flag` removed** from `decisions.py` + its schema + the `telemetry` re-export + the `ledger` demo (its producer died with the vocabulary at TASK-100 and §5.4.1 is retired, so the writer had no caller and the schema branch guarded a record nothing could emit — a record kind that cannot be produced is not backward compatibility, it is a sentence in a contract that reads as if something still works); the retired kind is now **actively rejected** rather than merely absent. **`check_discovery_adequacy` gained a routine caller** in `verify_si_profile.py` — the SI profile is the artifact it checks, and a check with no caller stops being true the first time someone edits what it guards. **`verify_code_map.py` now says loudly that the oracle is UNSIGNED** while `SIGNOFF.md` carries a pending re-sign-off: the run proves the build *matches* the oracle, not that the oracle is *correct*, and an all-green sweep otherwise overstates what has been established. ⚠️ **Still needs an operator signature** — that one cannot be closed from here.

**✅ Milestone D4 complete** — enrichment closed: the record + router, both arms, the walkthrough, the apply pass, and G2 validated against a real run.

**Phase D · Milestone D5 — Jira**
- [x] TASK-122 — `jira_author` + `jira_template` (4-level plan): 🆕 `core/templates/payment_brand/jira_template.payment_brand.yaml` (the second half of the domain seam) + 🆕 `core/skills/jira_author.skill.md` + 🆕 `core/scripts/jira_plan.py`. Each level has **one** source (D-A15): Initiative ← the document · Deliverable ← §7 · Epic ← §8 **one per requirement** · Story ← §16 impacts *and* gaps *and* §7 non-code work, **v2 only** — which is why G3 follows G2 *for a reason* rather than by convention. **A requirement is epic-sized, not story-sized**; **§16's granularity IS story granularity** and is not re-litigated here. The **§8→§7 trace physically builds the parent chain**, so an orphan requirement yields an epic with no parent — which is what made it a G1 hard precondition. Exactly one of `code_location | flag`: a dispositioned gap becomes `new_build` with **no invented path**, and `non_code` carries certification/filing work that would otherwise appear in no plan at all. **The translation ADDS acceptance criteria** — they exist nowhere upstream, which is what makes story authoring a translation rather than a copy; and a **Technical Specification is never read off into stories** (it specifies the *external contract* and is code-blind about our system by construction — the network has never seen our codebase). **A latent bug the plan walk exposed:** the TASK-121 spine fixture generated finding ids like `F-3R11`, which violate the schema's `F-nnn` pattern — and only 2 of 6 §16 entries parsed, so the story-coverage check would have passed on a subset. Root cause: **`verify_spine` never validated its own record**; it does now, plus an explicit id-contract check. Proof: 🆕 `fixtures/jira_plan/verify_jira_plan.py` — **26 checks**: four levels from their declared sources, no orphan at any level, **all 6 §16 entries covered** both directions, gaps as `new_build`, non-code stories present, acceptance criteria absent from v2 (authored, not copied), SI ids carried verbatim as push idempotency anchors. §10.3 green with `jira_template` in scope; all 23 verifies green.
- [x] TASK-123 — `jira_validator` + G3: 🆕 `core/scripts/jira_validator.py` + `core/skills/jira_validator.skill.md` — **G3 is the real technical-quality gate** (D-A1) and the last point at which anything is reviewable before the run's **only external mutation**. Scores `0.4×traceability + 0.3×testability + 0.3×field_completeness` per **§9.4** — noting that the task line item summarised it as `0.5/0.5`; the §9.4 block is normative, so the three-part form is implemented and the discrepancy is **flagged rather than silently resolved either way**. **The two guardrails run in opposite directions on purpose**: every §16 entry → ≥1 story catches a **dropped impact**; every story → §16/§7 catches an **invented story**. Checking only one passes a plan that is perfectly grounded and missing half the work, *or* one padded with fabrications — and both failures are silent. `traceability == 1.0` is **absolute, not "high"**: 0.98 means one piece of work is unaccounted for and there is no cheap way to find which after the push. ⚠️ **Observation worth V's attention (same shape as the G2 finding):** the deliberately-broken plan — broken §8→§7 hierarchy, an invented story, an untestable story, a missing controls field — still **scores 91**, above the 85 threshold. It is refused *only* by the hard checks. So at G3 the soft score is a weak signal and the hard preconditions carry the gate; the proof asserts this explicitly ("the score alone would have let it through"). 🆕 `fixtures/jira_plan/{plan_pass,plan_fail}.json` (one defect per hard check, so the report is checkable line by line). Proof: 🆕 `verify_jira_validator.py` — **22 checks**: each guardrail catching what the other misses, a dispositioned §16 entry legitimately excused, all three hard checks firing with named violations, a near-perfect plan still refused, and accept refused on an ineligible plan because what follows is irreversible. §10 4/4; all **24** verifies green.

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

**Milestone D5 — Jira (4-level plan + the only external mutation)**
- [ ] TASK-124 — Jira push seam + `jira_trace.json` · `Opus`

**Milestone D6 — Metrics, docs, acceptance**
- [ ] TASK-125 — `metrics_scan` re-cut (amended FR-MX-02) · `Sonnet`
- [ ] TASK-126 — Docs re-cut (`SKILLS_INDEX`, `BUILD_OVERVIEW`, `design/README`, `CLAUDE.md`) · `Sonnet`
- [ ] TASK-127 — End-to-end acceptance + registry re-publish (lifts the publish suspension) · `Opus`

---

## Milestone D5 — Jira (4-level plan + the only external mutation)

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
