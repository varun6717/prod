# ADR-002 — Polyglot repos: per-language partition dispatch (majority deterministic + residue model fallback)

**Status:** Accepted — ruled by operator **V**, 2026-06-19.
**Amends:** `TECH_SPEC.md` §5.5 (dispatch is per-language partition, not single whole-repo language); §5.4 (`files_seen` counts all source files; residue is `files_fallback`); `code_map_build.skill.md`; `CLAUDE.md` MVP-scope note (single language → single *primary* language, residue handled).
**Does not reopen:** D1–D10, nor any architectural principle (deterministic-frozen extractor, model-owns-`purpose`/`tags`-only, deterministic `merge_edges`, model-free 3-branch gate, coverage floor — all intact). The model fallback already exists in §5.5; this ADR only changes its **granularity** from whole-repo to file-set.

## Context

`TECH_SPEC.md` §5.5 specifies `dispatch(repo)` around a **single** `L = detect_language(repo)`: one frozen
extractor runs over the whole repo, or — if no extractor exists for `L` — the whole repo falls to the
model. On a **multi-language repo** this is lossy: detection picks the dominant language, the frozen
extractor's `file_globs` (e.g. C's `["*.c","*.h"]`) match only that language, and **every other-language
file is silently absent** from `code_map.json`. `code_impact` then cannot see a genuine second language
(e.g. a C service with a substantial Java or Python module).

Real Merchant Services repos are not always single-language. We need: the majority language goes through
its deterministic frozen extractor (full fidelity), and the **remaining files are not dropped** — they are
covered by the model, marked coarse, and stay **visible** so a real un-onboarded language raises its hand.

## Decision

**Dispatch partitions the repo by language and routes each partition independently.** For each language
present: if a frozen extractor is registered, use it (deterministic); otherwise route those files to the
**model fallback** (forced `coverage: coarse`). `merge_edges` then closes the graph across all partitions
into one `code_map.json`.

```
dispatch(repo) -> code_map.json:                       # revised §5.5
  partitions = partition_by_language(repo)             # {lang: [files]} — DETERMINISTIC, model-free
  entries = []
  for lang, files in partitions:
      E = extractor_for(lang)                          # registry lookup; may be None
      if E:
          entries += normalize(E(files))               # frozen, deterministic, full coverage
      else:
          entries += model_fallback(files)             # model-derived; mark_all coverage="coarse"
  for e in entries:
      e.purpose, e.tags = model_enrich(e)              # MODEL owns purpose + tags ONLY (unchanged)
      assert e.tags ⊆ domain_vocabulary
  edges = merge_edges(entries)                          # DETERMINISTIC closure across partitions
  return assemble(entries, edges, coverage_report)
```

`detect_language(repo)` is **retained** and still returns the single **dominant** language — it remains the
top-level `code_map.language`, the `onboarding_manifest` repo-entry language, and a gate input. Partitioning
is an additional, equally-deterministic view; it does not replace detection.

## The guardrail — residue is *covered* but never *hidden*

`coverage_report.files_seen` counts **all** source files in the repo; extractor-handled files are
`files_extracted`, model-fallback (residue) files are `files_fallback`. So `coverage =
files_extracted / files_seen` (§5.4) **drops in proportion to the residue**, which self-tunes the only real
ambiguity — "ancillary scripts vs a genuine second language":

| Repo | Residue | Coverage | Outcome |
|---|---|---|---|
| C service + 3 Python build scripts | ~3% | ≈ 0.97 | above floor → no flag (residue is noise; correct) |
| Genuine ~50/50 Java + C | ~50% | ≈ 0.50 | below 0.80 floor → **`REONBOARD_FLAG`** names the un-onboarded language → "onboard a Java extractor" |

The *proportion* decides. Either way the residue is mapped (no drop) and the coarse marking keeps it honest:
a real missing extractor surfaces as a re-onboarding decision (FR-DC-16), exactly like any other coverage gap.

## Rationale

1. **No file is ever dropped.** Every file is either deterministically extracted or model-covered; the map
   is complete by construction.
2. **It is the *same* model fallback, just finer-grained.** §5.5 already routes no-extractor cases to the
   model. This ADR changes `model_fallback`'s input from "the repo" to "a file set," so one function serves
   both "no extractor for the dominant language" and "residue alongside an extractor." Additive, not new.
3. **The coverage signal stays meaningful.** Because residue counts as `files_fallback`, a genuinely
   bilingual repo trips the floor and prompts onboarding — the system never silently degrades half a repo
   to model guesses and calls it healthy.
4. **Determinism intact.** `partition_by_language`, `normalize`, `merge_edges`, and the gate remain
   model-free. The model still owns `purpose`+`tags` only (and, flagged coarse, residue structure).
5. **Schema already supports it.** §3.3 `coverage_report` already carries `files_extracted`/`files_fallback`/
   `files_unresolved`; per-file `coverage ∈ {coarse,deep}` already exists. No schema reshape.

## Consequences

- **TASK-008 (amended):** add `partition_by_language(repo) → {lang: [files]}` to `core/extractors/__init__.py`
  (deterministic, reuses the detection extension map; `detect_language` retained for the dominant language).
  Dispatch pseudocode in `code_map_build.skill.md` becomes the per-partition loop above.
- **TASK-009:** the C extractor accepts a **file list** (its language partition) rather than self-globbing
  the whole repo. Structural-field behavior is otherwise unchanged.
- **TASK-010:** `model_fallback(files)` operates over a **file set**; it serves both the no-extractor repo
  and the residue; forces `coverage: coarse`; contributes `files_fallback` to `coverage_report`.
- **TASK-012/013:** `files_seen` counts all source files; residue = `files_fallback` → coverage reflects the
  deterministic share; the floor governs whether a residue language needs onboarding. The gate's Branch A
  (onboard) is still keyed on the **dominant** language; residue languages are surfaced via the coverage
  floor, not a separate branch.
- **Fixtures:** new `fixtures/mixed_repo/` (dominant-C core + a few non-C files) is the polyglot test bed for
  TASK-010. `fixtures/c_repo/` is **untouched** — its signed-off `expected_code_map.json` oracle stays pristine.
- **Scope:** this is a deliberate, operator-ruled expansion of the MVP "single language" note. Multi-*repo*
  breadth and per-subtree language *nesting* remain Phase 5; this ADR covers multi-language **within one repo**.
