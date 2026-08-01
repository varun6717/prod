# SIGNOFF.md — `expected_code_map.json` (TASK-005 regression oracle)

This file records the **human sign-off** that makes `expected_code_map.json` the trusted
grading oracle for TASK-012 (validate the frozen C extractor) and TASK-013 (3-branch gate).
Per TASK-005 acceptance, the oracle is **not** model-self-generated/self-graded: it was
hand-authored by reading the fixture source directly (not by running any extractor, which does
not yet exist), and is valid only once a human signs below.

## What was authored against what

- **Oracle:** `fixtures/c_repo/expected_code_map.json`
- **Fixture state (frozen):** `fixtures/c_repo/**` at commit **`e94c70d`**
  ("TASK-004: finalize brand_rules.c macro-param rename (freeze fixture for oracle)").
- **Contracts:** `docs/TECH_SPEC.md` §3.3 (`code_map.json` schema + `coverage_report`), §5.4/§5.5
  (coverage formula, normalization), `docs/REQUIREMENTS.md` D5 (tag vocabulary), D6a.
- **Source basis:** `fixtures/c_repo/PATTERN_CATALOG.md` (the TASK-004 tier/edge inventory),
  cross-checked against every `.c`/`.h` file.

## Authoring decisions (pinned)

1. **Per-file `coverage` is `coarse` for all 34 files; top-level `coverage` is `coarse`.**
   Rationale: §5.5 line 474 — the deterministic extractor emits `coarse` ("deep pass confirms");
   the §3.3 + D6a normative examples show cleanly-extracted files as `coarse`; `deep` is only ever
   produced by the Stage-2 deep pass (§5.6), which the extractor graded here does not run. The
   `PATTERN_CATALOG.md` §3 labels of "coverage: deep" describe deep-*eligibility* (the bucket def
   hedges "deep candidate"), not extractor output. Confirmed by operator (V), 2026-06-19.

2. **The extracted / fallback / unresolved distinction lives only in `coverage_report`**, not as a
   per-file field (§3.3 has no per-file bucket field). The per-file signal for an unresolved file is
   its **under-reported `interfaces[]`** (e.g. `config/brand_rules.c` lists only `get_brand_rule` —
   the macro-generated `*_route` functions are invisible to the parser — `DECLARE_BRAND_HANDLER`
   is not expanded, the invocation surfaces as an `ERROR` node — and therefore absent).

3. **Volatile top-level fields are informational, NOT part of the structural comparison.**
   TASK-012 must compare `files[]` structural fields (`path/module/interfaces/depends_on/used_by/
   coverage`) + `coverage_report`, and **ignore**: `commit_sha`, `generated_at`, `seal_id`,
   `built_with_extractor_sha`. The latter is set to `PENDING_TASK_012_FREEZE` because the extractor
   SHA does not exist until the freeze at TASK-012.

## Deltas from `PATTERN_CATALOG.md` (surfaced, not silently resolved)

- **D-1 (corrected in oracle): missing `txn_lifecycle → txn_state` edge.** The catalog (§3 edge
  table, §5 used_by) treats `transaction/txn_state` as having no in-tree caller. But
  `src/transaction/txn_lifecycle.c` calls `txn_advance()` (defined in `txn_state.c`) — a clean,
  statically-resolvable edge the parser finds (a direct `txn_advance` call node). The oracle therefore includes
  `transaction/txn_lifecycle` `depends_on` `transaction/txn_state` and the reverse `used_by`.
  **Recommend** patching `PATTERN_CATALOG.md` §3/§5 to match.

- **D-2 (wording only): "coverage: deep" labels.** `PATTERN_CATALOG.md` §3 labels Tier-1 files
  "coverage: deep". Per decision #1 the oracle marks them `coarse`. **Recommend** softening the
  catalog wording to "deep-eligible" to prevent confusing TASK-009/012.

## Validation run (2026-06-19)

`expected_code_map.json` passed automated checks: valid JSON; 34 file entries; all `tags ⊆ D5
vocabulary`; reserved `external_calls`/`exposes` empty on every file; per-file + top-level
`coverage = coarse`; `coverage_report` buckets sum to `files_seen` (28+3+3=34) and
`28/34 = 0.82 ≥ 0.80` floor; `depends_on ↔ used_by` fully bidirectional (19/19 edges).

## Sign-off

By signing, the operator confirms the tier assignments, edge tables, `interfaces[]`, tag
assignments, and the `coverage_report` summary are correct, and that this oracle may grade the
frozen extractor at TASK-012.

- **Signed off by:** V   _(operator)_
- **Date:** 2026-06-19
- **Fixture commit signed against:** `e94c70d`

> Status: **SIGNED OFF** by operator V, 2026-06-19. Authored by Claude (TASK-005), 2026-06-19.
> Catalog deltas D-1 and D-2 patched into `PATTERN_CATALOG.md` in the same commit.

---

## Addendum A — toolchain re-validation (ADR-001, 2026-06-19) — pending operator re-sign-off

The C extractor toolchain changed from `ctags`/`cscope` to **`tree-sitter` + `tree-sitter-c`**
(ADR-001). This addendum records whether the swap invalidates this signed oracle.

**Empirical re-validation.** tree-sitter-c 0.24.2 was run over all 34 `fixtures/c_repo` files
(fixture commit `e94c70d`, unchanged) and compared to `expected_code_map.json`. Findings:

- **All structural values hold unchanged.** `interfaces[]`, `depends_on`/`used_by` (19/19 edges),
  per-file + top-level `coverage: coarse`, and the `coverage_report` (28 extracted / 3 fallback /
  3 unresolved → `0.82`) all reproduce. Verified hazard files: `brand_rules.c` (only `get_brand_rule`
  resolvable; macro region → `ERROR` node), `dispatch.c` (clean `lookup_handler` edge; `fn`/`h->route`
  indirect), `route_table.c` (`entry->handler->route` indirect), `brand_registry.c` (4 interfaces
  match), `field_codec.c` (static `encode_numeric`/`decode_numeric` correctly excluded), `feature_flags.c`
  (STRATUS_SVC/vendor unresolved). The designed macro / function-pointer / `#ifdef` blind spots all
  survive because tree-sitter is purely syntactic, like `ctags`/`cscope`.
- **Only change to the oracle JSON:** one `purpose` string for `brand_rules.c` reworded from
  "invisible to ctags" → "invisible to the parser (DECLARE_BRAND_HANDLER macro not expanded)".
  `purpose` is **not** part of the structural grading set (decision #3), so grading is unaffected.
- **Prose retoolchained** in `PATTERN_CATALOG.md` and §2/§3 of this file (ctags/cscope → parser
  semantics). No tier reassignment, no edge change.

**Conclusion:** the swap is **value-preserving**; the oracle remains valid for grading TASK-012.

- **Re-sign-off by:** V   _(operator — confirms the re-validation above; oracle stays valid under tree-sitter)_
- **Date:** 2026-06-19

> Status: **RE-SIGNED OFF** by operator V, 2026-06-19. Toolchain swap (ADR-001, ctags/cscope → tree-sitter)
> confirmed value-preserving; `expected_code_map.json` remains the valid grading oracle for TASK-012.

---

## Amendment 2 — TASK-112 additive pass (declared purposes + versioned duplicate)

**What changed in the fixture.** Declared-purpose headers added to 21 of 35 files under six label
variants plus one `Putpose` typo (D-A20's measured distribution); one new file
`src/messaging/iso8583_v2.c` seeding the versioned-duplicate hazard (D-A20 finding 3).

**What changed in the oracle.** One new `files[]` entry for `iso8583_v2.c`, and the
`coverage_report` counts moved 34→35 seen, 28→29 extracted, 0.82→0.83.

**How the new entry was authored — the binding rule still holds.** It was derived by *reading the
source*, which this task also wrote: `build_iso8583_v2` and `parse_iso8583_v2` are the two
non-static definitions (so `set_bit_v2` is correctly excluded), and the file makes no cross-file
call, so `depends_on` is empty. That prediction was made **before** running the extractor and the
extractor then agreed — the oracle is not extractor output copied back in.

**What did NOT change.** No existing entry's structural fields moved. Declared-purpose headers are
comments: tree-sitter ignores them for interfaces and edges, which the 0-mismatch structural
comparison over all 35 files confirms.

**Extractor re-freeze.** `extractor_sha` bumped `125a6ca → ed703ff` in `core/extractor_manifest.yaml`.
A re-freeze is a build-time amendment — edit, bump, commit — never a runtime rewrite.

- **Re-sign-off by:** V (Varun Munjal) — operator
- **Date:** 2026-08-01

> Status: **SUPERSEDED** by Re-freeze 3 below. This amendment's content (the `iso8583_v2.c` entry
> and the moved coverage counts) is carried into the reshaped oracle and signed there; recording
> it separately would leave two live signatures over one artifact.

---

## Re-freeze 3 — TASK-114 map reshape (§3.3 amended)

**The oracle shape changed, so the previous sign-off no longer grades anything.** ADR-008 splits
the map into two files, deletes `tags[]`, and adds purpose provenance. `expected_code_map.json` is
**deleted**; `expected_components.json` + `expected_files.json` replace it.

| Was | Now |
|---|---|
| one `expected_code_map.json`, 35 `files[]` with `tags[]` | `expected_components.json` (16 modules with explicit `members[]`, `purpose_confidence`, the coverage report) + `expected_files.json` (35 files with `purpose_source` / `purpose_verdict`) |
| module = directory name | module = **include-graph component** per the frozen signal profile (`profile_sha` 52dd3db) |
| `purpose` model-written for every file | A/B/C/C\* ladder — 21 declared, 5 header prose, 8 symbols, 1 unanalyzable-with-reason |

**How this oracle was produced, and why that is acceptable here.** Unlike TASK-005's, it *is*
generated by the build. That is a deliberate change of kind, and the grading value moves with it:
the old oracle graded a **parser** whose output a human could read off the source, so
hand-authoring it was both possible and the point. This one encodes **module derivation from a
frozen profile plus a purpose ladder** — reproducing that by hand would be transcribing an
algorithm, not checking it.

So what the oracle now guards is **change detection**, not first-principles correctness: any drift
in derivation, resolution, or synthesis fails the diff. First-principles correctness is carried by
`verify_code_map.py`'s property checks (totality, no-copy synthesis, provenance, citability,
requirement-blindness) and by `check_map_totality.py`, which do not depend on the oracle at all.
A human still signs, but is signing *that the map is right*, having read the report — not that
they transcribed it.

**What a reviewer should check before signing:** the module breakdown matches what the onboarding
gate report showed (16 modules, `profile_sha` 52dd3db); the 21 declared purposes read correctly
against their cited lines; the single unanalyzable file is genuinely unanalyzable; and the
versioned pair is reported for disposition rather than resolved.

- **Re-sign-off by:** V (Varun Munjal) — operator
- **Date:** 2026-08-01

> Status: **RE-SIGNED OFF** by operator V, 2026-08-01. Covers Amendment 2 as well (the
> `iso8583_v2.c` entry and the coverage-count move are carried into this shape).

### Basis of this signature — recorded honestly, per the TASK-005 rule's intent

The rule exists so the oracle is not model-self-generated **and** self-graded. Half of that no
longer holds and the record should say so rather than imply a review that did not happen:

- **What V attested to:** the amendment above — 16 modules at `profile_sha` 52dd3db, the 60/40
  declared-purpose split, one genuine unanalyzable, the versioned pair reported for disposition
  rather than resolved — and the decision to accept a **build-generated** oracle for this artifact.
- **What V did not do:** independently re-derive the 35 file entries by hand. For the TASK-005
  parser oracle that was both possible and the point; for module-derivation-from-a-frozen-profile
  plus a purpose ladder it would be transcribing an algorithm.
- **What still carries first-principles correctness:** `verify_code_map.py`'s property checks and
  `check_map_totality.py` — totality, no-copy synthesis, provenance, citability,
  requirement-blindness — none of which depend on the oracle. The oracle guards **change
  detection**; those guard **correctness**.

If that division is ever judged too weak, the fix is to strengthen the property checks, not to
hand-transcribe the oracle.
