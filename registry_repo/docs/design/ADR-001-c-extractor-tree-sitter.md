# ADR-001 — C extractor toolchain: tree-sitter (not ctags/cscope)

**Status:** Accepted — ruled by operator **V**, 2026-06-19.
**Amends:** `REQUIREMENTS.md` FR-DC-14…17 extractor note; `TECH_SPEC.md` §5.1, §5.2, §5.5, §5.7.
**Does not reopen:** D1–D10, nor any architectural principle (deterministic-frozen extractor,
model-owns-`purpose`/`tags`-only, deterministic `merge_edges`, 3-branch gate, coverage floor — all intact).

## Context

The frozen C extractor was specified to shell out to **`ctags` + `cscope`** (`TECH_SPEC.md` §5.2,
`tools_required: [ctags, cscope]`). On the target **JPMC VDI** (Windows, **AppLocker-locked**), neither
is cleanly provisionable: the MSYS2 installer is AppLocker-blocked, and a formal IT package request is
slow. The available, in-policy path is **Python `tree-sitter` + `tree-sitter-c`** via pip into a venv —
it runs inside the already-allowed `python.exe`, needs no PATH binary, and was verified on the VDI
(tree-sitter 0.25.2 / tree-sitter-c 0.24.2, parsed a real 30 KB Stratus C file, 23 top-level decls).

## Decision

**Standardize the C extractor on `tree-sitter` + `tree-sitter-c` for *both* the external build and the
VDI.** The extractor parses each file to a concrete syntax tree and emits the §5.5 structural fields
(`path/module/interfaces/depends_on/used_by/coverage`); our deterministic `merge_edges` closes the graph
(unchanged). The model still owns `purpose`+`tags` only.

`tools_required` is no longer a PATH-binary list; it becomes a **Python dependency** (`tree-sitter`,
`tree-sitter-c`, pinned versions). The §5.7 port check changes from "binary on PATH" to "import
succeeds in the venv."

## Rationale

1. **One tool replaces two.** tree-sitter's per-file CST yields both symbols (was ctags' job) and
   outbound call/include references (was cscope's job). cscope's cross-file resolution was already
   partly redundant with our deterministic `merge_edges` — tree-sitter fits the §5.5 division of labor
   *more* cleanly, not less.
2. **In-policy, identical in both environments.** Pure pip → no AppLocker fight, and the ext-build and
   VDI run the *same* toolchain, which strengthens the "ports unchanged" guarantee (§5.7) instead of
   straining it.
3. **No loss of fidelity — empirically verified.** tree-sitter is purely syntactic, so it has the
   *same fundamental blind spots* as ctags/cscope on the hard patterns (macro-generated functions,
   function-pointer dispatch, `#ifdef`/vendor escapes). It does **not** regress coverage.
4. **Better hazard signalling.** Where ctags *silently omits* a macro-generated symbol, tree-sitter
   emits a **detectable `ERROR` node** at the unexpanded macro site — a positive signal the extractor
   can route into `coverage_report.unresolved_patterns` rather than missing blind.

## Validation evidence (2026-06-19, `fixtures/c_repo`, real tree-sitter run)

Ran tree-sitter-c over all 34 fixture files and compared to the signed oracle
(`expected_code_map.json`). **Every structural value in the oracle holds:**

| Hazard file | Expected (oracle) | tree-sitter result | Verdict |
|---|---|---|---|
| `config/brand_rules.c` | only `get_brand_rule` resolvable; `*_route` invisible | only `get_brand_rule`; macro region → **ERROR node** | blind spot survives |
| `routing/dispatch.c` | clean `lookup_handler` edge; computed targets unresolved | `lookup_handler` resolved; `fn`/`h->route` flagged indirect | survives |
| `routing/route_table.c` | array seen, target unresolved | `entry->handler->route` flagged indirect | survives |
| `routing/brand_registry.c` | 4 clean interfaces | exact same 4 | match |
| `messaging/field_codec.c` | public codecs only (statics excluded) | + `encode_numeric/decode_numeric` (both `static` → normalized out) | match |
| `config/feature_flags.c` | `#ifdef`/vendor unresolved | STRATUS_SVC/vendor unresolved | survives |

Tier assignments, the 19 `depends_on↔used_by` edges, and `coverage = 28/34 = 0.82` are **unchanged**.
The only `ctags`-naming in the oracle JSON is one `purpose` string (not part of structural grading per
`SIGNOFF.md` decision #3); reworded for accuracy.

## Consequences

- **No code rewrite:** `core/extractors/c_extractor.py` and `core/onboarding_manifest.yaml` did not yet
  exist — they are authored against tree-sitter from the start (TASK-009 onward).
- **Docs updated:** REQUIREMENTS §FR-DC note + Terms; TECH_SPEC §5.1/§5.2/§5.5/§5.7; `code_map_build.skill.md`;
  `ENV_PRECHECK.md` (toolchain = venv); `TASK_LIST.md` TASK-006/009.
- **Fixtures:** `PATTERN_CATALOG.md` / `SIGNOFF.md` prose retoolchained; oracle values **unchanged**
  (one purpose string reworded) — re-validation addendum recorded in `SIGNOFF.md`, pending operator
  re-sign-off.
- **Extractor normalization (TASK-009):** must (a) exclude `static` file-local functions from
  `interfaces[]`, (b) treat `ERROR` nodes and `field_expression`/computed callees as
  `coverage: coarse` + `unresolved_patterns`. Both are toolchain-independent requirements.
