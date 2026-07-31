# ADR-008 · Phase C — Impact analysis (keep / amend / retire)

**Status:** ✅ complete 2026-07-31 · **Feeds:** Phase D (rebuild `TASK_LIST.md` + `VDI_WIRING.md`, then execute)
**Authorities:** `ADR-008` D-A0–D-A24 (normative) · `TECH_SPEC.md` supersession banner (per-section dispositions) · `REQUIREMENTS.md` D11.

Every tracked file is classified against the accepted ADR-008 design. **321 tracked files = 230
classified individually below + 91 under `registry_repo/` (derived tree, dispositioned wholesale —
see §11).** Grouped rows state their file count so the totals are checkable.

**Verdict key**

| | Meaning |
|---|---|
| ✅ **keep** | survives as-is (at most reference touch-ups when a neighbour renames) |
| 🔧 **amend** | file survives but its contract/content changes; *recast* = renamed + rewritten wholesale, function survives |
| ⛔ **retire** | deleted from the tree; git history preserves it |
| 🆕 **new** | does not exist yet; Phase D creates it (§12 roster) |

**Tally:** ✅ 99 · 🔧 84 · ⛔ 47 (= 230) + `registry_repo/` 91 wholesale-refresh.

---

## 1 · Repo root (5)

| File | Verdict | Driver / note |
|---|---|---|
| `.gitignore` | ✅ | pending uncommitted edit (`notes/` ignore) is housekeeping, orthogonal to the pivot |
| `CLAUDE.md` | 🔧 | already ADR-008-aligned (commits `064aa0a`, `696db71`); Phase D touch: drop pointers to retired seed docs (§8) and re-point "How to execute" at the rebuilt task list |
| `TASK_LIST.md` | 🔧 | **rebuilding it *is* Phase D** — done ledger survives as history; open work re-cut from this analysis |
| `VDI_WIRING.md` | 🔧 | gains the two new VDI items (Jira fetch + Jira push placeholders, D-A24); stays a wiring list, never a spec |
| `NOTES.md` | ⛔ | already deleted in the working tree (moved to untracked `notes/`); prior-session housekeeping, commit pending |

## 2 · `core/scripts/` (26)

| File | Verdict | Driver / note |
|---|---|---|
| `.gitkeep`, `_refs/README.md` | ✅ ×2 | connector-reference discipline unchanged (D-A24) |
| `clone.py`, `ingest_file.py`, `ingest_sharepoint.py`, `ingest_confluence.py` | ✅ ×4 | source types + `[TBD — VDI]` placeholder discipline unchanged (D-A24); disposition is carried by `UI_INPUT`/manifest, not the connectors |
| `gate.py` | ✅ | D-A1: gate machinery reused unchanged; G1/G2/G3 re-map is validator-side |
| `ledger.py` | ✅ | §3.4–3.6 survive |
| `decisions.py` | 🔧 | light — gains walkthrough disposition record kinds (D-A16/17) |
| `telemetry.py` | 🔧 | light — event vocabulary gains `verdict` / `escalation` / `disposition` (banner §3.4–3.6) |
| `schemas/telemetry.schema.json` | 🔧 | same events |
| `schemas/decisions.schema.json` | 🔧 | disposition + rationale records (D-A17) |
| `schemas/run_state.schema.json` | 🔧 | stages `brd/frd` → `si_v1 / enrichment / si_v2 / jira` |
| `generate.py` | 🔧 | scaffold: `solution_intent/` replaces `BRD.md`/`FRD.md`; `code_map/` (2 files); indexes beside extracts; `UI_INPUT` gains per-source `disposition:` + `frame.overview` (banner §2/§3.1) |
| `merge_manifest.py` | 🔧 | entries lose `topics`/`change_type`, gain `disposition` + `index_path`; routing rule replaced (banner §3.2, D-A18) |
| `hydrate.py` | 🔧 | reads the shrunk trees-based `registry_manifest` (D-A22) |
| `publish_registry.py` | 🔧 | light — same manifest change |
| `generate_instruction.py` | 🔧 | role/stage renames (D-A23) |
| `brd_validator.py` | 🔧 | **recast → `solution_intent_validator.py`**: G1 = `0.7×section_coverage + 0.3×citation_integrity`; hard preconditions: conditional sections dispositioned (D-A10), §15→§4 and §7→§8 traces (D-A23 family 3) |
| `frd_validator.py` | ⛔ | D-A0; its `0.5×traceability + 0.5×testability` scoring is salvaged into the new `jira_validator.py` (G3) — port the code, don't rewrite it |
| `metrics_scan.py` | 🔧 | heavy — "most of metrics_scan" dies with FRD-era metrics (D-A0); metric names per amended FR-MX-02 |
| `validate_onboarding.py` | 🔧 | heavy — onboarding gate becomes the D-A21 report (stage distribution, module derivation, coverage gaps, 4 actions); validates the two-file map shape |
| `build_checks.py` | 🔧 | §10.1 + §10.5 dropped, §10.5′ disposition-class totality added; net 4 checks (D-A23 family 1) |
| `checks/check_overlay_parity.py` | 🔧 | new role list + `prompt_files: [start-ingest, start-si, start-enrich, start-jira]` (D-A23) |
| `checks/check_vocab_containment.py` | ⛔ | §10.1 dies with the vocabulary (D-A22/23) |
| `checks/vocab_adequacy.py` | ⛔ | §5.4.1 retired — `untagged_ratio` loses its denominator; heir is the D-A21 gate distribution + `purpose_confidence` + `warn_if_human_authored_below` (D-A22) |

## 3 · `core/skills/` (8)

| File | Verdict | Driver / note |
|---|---|---|
| `.gitkeep` | ✅ | |
| `brd_author.skill.md` | 🔧 | **recast → `solution_intent_author.skill.md`**: 18-section contract (D-A3/4), agent-extracted assertions (D-A8), conditional sections (D-A10), boundary statements (D-A11), routing matrix (D-A13), index-guided retrieval with sequential draft-carrying groups (D-A18). Discovery framing, `must_capture`, cite-or-flag, flag loop all carry forward |
| `brd_validator.skill.md` | 🔧 | **recast → `solution_intent_validator.skill.md`** (pairs with the `.py` recast, §2) |
| `code_impact_assess.skill.md` | 🔧 | heavy — becomes enrichment **Arm 1**: 3-tier module-first walk (D-A19), territory per deliverable + independent per-epic fan-out with anti-anchoring (D-A8), implicit current-state assumptions, §16 at (assertion × code location) granularity, four-way no-code-gap escalation (D-A15/16) |
| `code_map_build.skill.md` | 🔧 | heavy — D-A19/20/21 consolidated process: hub exclusion, deterministic clustering (include graph primary), purpose rungs A/B/C/C\*, module-purpose synthesis (never re-reads source), confidence scoring, coverage report, two-file output |
| `frd_author.skill.md` | ⛔ | D-A0 — the FRD layer moved into stories (D-A15) |
| `frd_validator.skill.md` | ⛔ | D-A0 — formula content salvaged into the new `jira_validator.skill.md` |
| `source_processor.skill.md` | 🔧 | routes by operator `disposition` instead of tag lanes (D-A12); doc lane becomes extract + index (D-A18); still never branches on domain |

## 4 · `core/` — manifests, extractors, adapters, profiles, templates (18)

| File | Verdict | Driver / note |
|---|---|---|
| `adapters/jpmc_adapters/__init__.py`, `auth.py` | ✅ ×2 | §7 survives unchanged |
| `extractors/.gitkeep`, `__init__.py` | ✅ ×2 | |
| `extractors/c_extractor.py` | 🔧 | adds deterministic declared-purpose extraction (leading comment block, fuzzy label aliases from the repo profile) feeding rungs A/C\*; §3.3 shape without `tags` (D-A19/20). Amend = versioned re-freeze with an `extractor_sha` bump — never a runtime rewrite |
| `instruction_file.template.md` | 🔧 | role/stage renames (D-A23) |
| `onboarding_manifest.yaml` | ⛔ | **split** (D-A22): `extractors[]` → 🆕 `extractor_manifest.yaml`; `adequacy_threshold` + `vocab_sha` die; `repos[]` → 🆕 `cache/code_maps/index.yaml` (mutable, outside the frozen registry) |
| `overlay_manifest.yaml` | 🔧 | contents rewritten: `brd_*` → `solution_intent_*`, `frd_*` out, `claim_verifier` + `disposition_walkthrough` in (still 8 roles), prompt files re-pointed, execution modes marked interactive/analytical (D-A22/23) |
| `registry_manifest.yaml` | 🔧 | shrink to `trees: [core/, overlays/, docs/]` + excludes (D-A22). The pending uncommitted edit hand-adds 8 ADR paths — the exact maintenance trap D-A22 kills; the shrink supersedes it (and makes docs/ ship wholesale, another reason §8's stale seeds must retire) |
| `profiles/payment_brand/adapter/.gitkeep` | ✅ | |
| `profiles/payment_brand/adapter/adapter.yaml` | 🔧 | loses `emits` and the tag-lane `docs_pipeline` (banner §6.6); shrinks to the surviving domain-pack pointers |
| `profiles/payment_brand/adapter/pdf_extract.skill.md` | 🔧 | light — extraction (headings/hierarchy/tables) survives and is what the index keys on ("no extraction change", D-A18); strip any emit/tag references |
| `profiles/payment_brand/adapter/article_summarize.skill.md` | ⛔ | the doc tagger dies with tags; summarisation re-appears as the domain-agnostic per-artifact index pass (D-A18), not a domain adapter skill |
| `profiles/payment_brand/adapter/confluence_tag.skill.md` | ⛔ | pure tagger (D-A19: nothing on either side is tagged) |
| `profiles/payment_brand/brd_profile.payment_brand.yaml` | 🔧 | **recast → `si_profile.payment_brand.yaml`**: 18 sections × `must_capture` (doubles as G1 checklist and retrieval query, D-A18) + `probe_if_missing` + section input classes (D-A13) + conditional marks (D-A10) + boundary statements (D-A11); the `topics` layer dies |
| `profiles/payment_brand/frd_profile.payment_brand.yaml` | ⛔ | D-A0/D-A22 |
| `profiles/payment_brand/vocabulary.payment_brand.yaml` | ⛔ | D-A22: dies entirely (with it the F1+3 drift class, `vocab_sha`, `d5frozen-r3`) |
| `templates/payment_brand/.gitkeep` | ✅ | 🆕 `jira_template.*` lands here (§10.3 then requires it) |

## 5 · `overlays/` (30)

Parity twins — every verdict applies to both tools (D-A0: both stay; §10.2 enforces).

| File (× both tools where paired) | Verdict | Driver / note |
|---|---|---|
| `claude/.claude/agents/.gitkeep`, `claude/prompts/.gitkeep`, `copilot/.gitkeep` | ✅ ×3 | |
| `copilot/VDI_PREREQUISITES.md` | ✅ | tool prereqs unaffected by the pivot |
| `brd_author.*` | 🔧 ×2 | recast → `solution_intent_author.*` |
| `brd_validator.*` | 🔧 ×2 | recast → `solution_intent_validator.*` |
| `code_impact.*` | 🔧 ×2 | Arm 1 framing (analytical, fan-out) |
| `jira_author.*` | 🔧 ×2 | 4-level plan; stories authored from §16 + §7 (D-A15) |
| `jira_validator.*` | 🔧 ×2 | G3 absorbs traceability/testability + the two story guardrails (D-A23 family 3) |
| `source_processor.*` | 🔧 ×2 | disposition routing + index step |
| `frd_author.*` | ⛔ ×2 | D-A0 |
| `frd_validator.*` | ⛔ ×2 | D-A0 |
| `launch.md` | 🔧 ×2 | stage names; start gesture still points at `start-ingest` (D9 amendment survives) |
| `prompts/start-brd*` | 🔧 ×2 | recast → `start-si*` |
| `prompts/start-frd*` | 🔧 ×2 | recast → `start-enrich*` |
| `prompts/start-ingest*` | 🔧 ×2 | light — surfaces `start-si` instead of `start-brd` |
| `prompts/start-jira*` | 🔧 ×2 | follows G2; reviews the 4-level plan |

🆕 per tool: `claim_verifier` + `disposition_walkthrough` wrappers (§12).

## 6 · `app/` (17)

| File | Verdict | Driver / note |
|---|---|---|
| `__init__.py`, `backend/__init__.py`, `backend/requirements.txt` | ✅ ×3 | |
| `frontend/index.html`, `main.jsx`, `api.js`, `vite.config.js`, `package.json`, `package-lock.json` | ✅ ×6 | transport/scaffold untouched |
| `backend/app.py`, `service.py`, `validation.py` | 🔧 ×3 | `UI_INPUT` contract: per-source `disposition:` (multi allowed, default one; `Codebase` auto-set for repo URLs, non-editable), `frame.overview`; validation asserts disposition ∈ D-A12 taxonomy |
| `backend/README.md`, `frontend/README.md` | 🔧 ×2 | light |
| `frontend/src/PDLCConfigurator.jsx` | 🔧 | disposition selector per source row + Initiative Overview textarea; `Other` rendered second-class (never sole citation, D-A12) |
| `frontend/src/emit.js`, `scripts/emit_cli.mjs` | 🔧 ×2 | emit the amended §3.1 shape |

## 7 · `fixtures/` (82)

| Files | Verdict | Driver / note |
|---|---|---|
| `UI_INPUT.example.yaml` | 🔧 | disposition + overview; the TASK-062 cosmetic mismatch dies with the re-cut |
| `adapter_routing/verify_adapter_routing.py` | ⛔ | verifies the tag-lane `docs_pipeline` + `confluence_tag` emission — mechanism dies (D-A19); heir is 🆕 index-generation verification |
| `auth/verify_auth.py` · `code_clone/verify_clone.py` · `sharepoint/verify_sharepoint.py` | ✅ ×3 | seams unchanged |
| `registry/verify_registry.py` | 🔧 | light — asserts against the trees-based manifest |
| `brd_author/` (4) · `brd_validator/` (3) | ⛔ ×7 | BRD-shaped oracles; 🆕 SI author/validator fixtures replace them (18 sections, assertions, conditional dispositions) |
| `frd_author/` (2) · `frd_validator/` (3) | ⛔ ×5 | D-A0 |
| `code_impact/` (2) | ⛔ ×2 | coarse oracle is topics×tags (dies); deep-flag closure semantics survive in spirit — salvage content into the 🆕 tier-walk oracles |
| `c_repo/` — `Makefile`, `include/`, `src/`, `PATTERN_CATALOG.md` (36) | ✅ ×36 | the synthetic Stratus repo survives as the code fixture (D-A24). 🆕 additive pass (V-flag 4): declared-purpose headers under varied labels + typos, a versioned-duplicate pair, a flat-directory slice — the D-A20 phenomena the current fixture cannot exercise |
| `c_repo/expected_code_map.json` | 🔧 | heavy — reshape to `components.json` + `files.json`: no `tags`; `members[]`; `module`, `purpose_source/verdict/quality`; `coverage_report` (D-A19/20/21) |
| `c_repo/SIGNOFF.md` | 🔧 | oracle re-shape voids the sign-off; human re-freeze required (binding rule) |
| `confluence/` — 2 HTML | ✅ ×2 | mock pages survive (D-A24) |
| `confluence/verify_confluence.py` | 🔧 | drop tag-lane assertions; descriptor otherwise unchanged |
| `frontend/` (2) | 🔧 ×2 | disposition emission asserts |
| `generate/` (2) | 🔧 ×2 | new scaffold shape |
| `merge_manifest/` (5) | 🔧 ×5 | entries gain `disposition` + `index_path`, lose `topics`/`change_type` |
| `mixed_repo/` (7) | ✅ ×7 | polyglot partition/dispatch stands (banner §5); seed of the 🆕 **required** multi-language validation fixture (D-A19: per-language profile sections, cross-language tier-1, closure boundary) |
| `pdf/` — `.gitkeep`, 2 PDFs, `gen_fixtures.py` | ✅ ×4 | mocks survive; check the D-A18 degraded case (flat prose, few headings) against these before the index design is considered proven |
| `pdf/expected_manifest_entries.json` | 🔧 | disposition + `index_path`, no topics |

## 8 · `docs/` (24)

| File | Verdict | Driver / note |
|---|---|---|
| `REQUIREMENTS.md`, `TECH_SPEC.md` | ✅ ×2 | re-cut in Phase B; spec's in-section consolidation of D-A blocks is deferred ("next consolidation"), not Phase D work |
| `ACCEPTANCE.md`, `ENV_PRECHECK.md`, `COPILOT_VDI_VALIDATION.md` | ✅ ×3 | immutable build/run records |
| `max-autonomy.skill.md` | ✅ | tool discipline, domain-neutral |
| `design/ADR-001` … `ADR-008` | ✅ ×8 | records + normative (008). V-flag 3: ADR-003 (vocabulary), ADR-004 (profile integration), ADR-005 (adapter `emits`) deserve one-line superseded-by-ADR-008 banners; ADR-006/007 stand (extractor onboarding; cross-repo = cross-language, one deferred capability) |
| `design/README.md` | 🔧 | light — index gains 008 status + banners |
| `design/PDLC_Configurator.jsx`, `SURVEY-doc-structure.md`, `SURVEY-stratus-repo.md` | ✅ ×3 | working evidence; SURVEY open items feed Phase D (§13) |
| `SKILLS_INDEX.md` | 🔧 | still catalogues the BRD/FRD 5-layer pipeline; re-cut to the SI catalog + new roles |
| `BUILD_OVERVIEW.md` | 🔧 | re-cut to SI → enrichment → Jira |
| `brd_frd_overview.html` | ⛔ | the BRD/FRD wireframe — subject retired (V-flag 2) |
| `brd_author.skill.md`, `code_impact_assess.skill.md`, `code_map_build.skill.md` | ⛔ ×3 | pre-build *seed* skills, superseded twice over (by `core/skills/`, then by the pivot); retiring also keeps the trees-based registry clean (V-flag 2) |

## 9 · `runs/` (20)

| Files | Verdict | Driver / note |
|---|---|---|
| `.gitkeep` | ✅ | |
| `_template/` (6) | 🔧 ×6 | scaffold gains `solution_intent/` (+ `enrichment.json` home); ledger template survives |
| `r-2026-06-17-001/` (13) | ⛔ ×13 | BRD/FRD-era acceptance workspace (TASK-049); evidence preserved in git history + `ACCEPTANCE.md`; its "pipe works end-to-end" duty folds into the Phase-D acceptance task (D-A0). V-flag 1 |

## 10 · Untracked working files

`notes/` (4 files, untracked by design) — outside scope; no verdict.

## 11 · `registry_repo/` (91) — wholesale

Derived working copy of the published registry (TASK-053). Not classified per-file: its contents
are regenerated by `publish_registry.py` at the next re-publish after Phase D lands. Mechanism ✅;
contents 🔧 wholesale. Until then the published `registry_sha` keeps serving the *old* pipeline —
correct during the cutover, since no run should target a half-rebuilt registry.

## 12 · 🆕 New artifacts (Phase D roster)

Core:

| Artifact | Driver |
|---|---|
| `core/extractor_manifest.yaml` | D-A22 — per-language freeze, out of the retired onboarding manifest |
| `core/code_profiles/<repo>.profile.yaml` | D-A22 — per-repo signal profile (labels, priority, thresholds, frozen overrides, gate record); one for `fixtures/c_repo`, later Stratus |
| `cache/code_maps/index.yaml` | D-A22 — 4-branch gate cache, mutable, **outside** the registry (gitignore decision at Phase D) |
| `core/skills/claim_verifier.skill.md` | D-A8/23 — Arm 2 |
| `core/skills/disposition_walkthrough.skill.md` | D-A17 — interactive; triage, ordering deps, resumable |
| `core/skills/jira_author.skill.md` + `jira_validator.skill.md` | D-A15 — never built (old TASK-064); now 4-level, stories from §16 + §7 |
| `core/scripts/jira_validator.py` | G3 scorer — salvage `frd_validator.py`'s formula |
| Per-artifact index generation (home decided in Phase D: `source_processor` step vs own skill) | D-A18 — summaries at ingest, `.index.json` beside each extract |
| Family-2 context checks (module/purpose totality, `members[]` consistency, index completeness) | D-A23 — live in map build + ingest, not §10 |
| `core/profiles/payment_brand/jira_template.*` | §10.3 requires it once present |
| `core/scripts/ingest_jira.py` (`_fetch_issue` placeholder) | D-A24 — the one genuinely new source type |
| `core/adapters/jpmc_adapters/jira.py` (push placeholder) | D-A24 — the only external mutation, behind G3 |

Overlays: `claim_verifier` + `disposition_walkthrough` wrappers × both tools (§10.2 parity).

Fixtures: `fixtures/jira/` (issue payload mock + verify) · SI author/validator oracles ·
enrichment oracles (claim clusters → verdicts → dispositions) · doc-index oracles (completeness =
guardrail 7) · multi-language repo (extend `mixed_repo`; **required acceptance artifact**, D-A19) ·
the `c_repo` declared-header/duplicate additions (§7).

## 13 · Handoff to Phase D

- **Task-cut rule:** every 🔧/⛔/🆕 row above becomes (part of) a task citing its driver decision;
  the *build* list and the *VDI wiring* list stay disjoint by kind of work (D-A24 §3).
- **Outstanding evidence** (de-risks, does not block): extended code survey — graph isolation
  degree-zero-both-directions, symbol presence, stage-B sample rate; doc-side extraction fidelity
  (does `pdf_extract` preserve hierarchy?) — see `SURVEY-doc-structure.md`.
- **Sequencing constraint:** G2's proposed formula (`verdict_completeness` + `impact_coverage`) is
  flagged provisional — validate against a real run before freezing (D-A23).
- **Old open tasks (TASK-056, 064–081):** none carries over verbatim. 064/065 re-cut for the
  4-level hierarchy; 056's surviving half folds into the new acceptance (D-A0); 066's refinement (d)
  and 067's purpose are absorbed into D-A19/D-A18; 079 is promoted to core by D-A13 (discovery is
  primary for §9/§12/§13); 081 arrived via D-A6 auto-fill; the domain-onboarding cluster (069–075)
  re-scopes against the new seam set. Phase D re-cuts each explicitly rather than inheriting.

**V-flags (operator confirmation wanted, none blocks starting Phase D):**

1. Delete `runs/r-2026-06-17-001/` from the tree (history + `ACCEPTANCE.md` retain the evidence)?
2. Retire the three seed docs + `brd_frd_overview.html` (they'd otherwise ship in the trees-based registry)?
3. Add superseded-by banners to ADR-003/004/005?
4. Scope of the `c_repo` additive header pass (which files get declared purposes; one versioned-duplicate pair suffices?).
