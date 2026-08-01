# PATTERN_CATALOG.md — synthetic Stratus C repo (`merchant-routing-svc`)

**Fixture for:** TASK-004 (this repo) → consumed by TASK-005 (oracle), TASK-009 (C extractor),
TASK-011 (`merge_edges` + enrichment), TASK-012 (validate vs oracle), TASK-013 (3-branch gate),
TASK-036 (onboarding skill).

This catalog is the **sign-off artifact**: it declares, per file, what the deterministic extractor
(`tree-sitter` + `tree-sitter-c` per ADR-001, normalized per §5.5) is expected to resolve, what it is expected to miss, and the
expected `coverage_report`. TASK-005 hand-authors `expected_code_map.json` against the edge tables
and tier assignments below; TASK-012 grades the frozen extractor against that oracle.

Contracts this fixture is built against:
- `docs/TECH_SPEC.md` §3.3 (`code_map.json` file-entry schema + `coverage_report`)
- `docs/TECH_SPEC.md` §5.1–§5.5 (onboarding, 3-branch gate, coverage threshold, dispatcher/normalization)
- `docs/REQUIREMENTS.md` D5 (tag vocabulary — the six **code tags**), D6a (`code_map.json` rules), D6b (scope_ripple flag)

---

## 1. Repository shape

```
fixtures/c_repo/
├── Makefile                 # stub; `make tags` scans src + include ONLY (mirrors the Stratus -I convention)
├── include/                 # shared cross-module contract headers
│   ├── brand.h              # brand_id_t + brand_handler_t vtable (the function-pointer source)
│   ├── txn.h                # txn_t — the record threaded through every module
│   ├── errors.h             # pdlc_status_t + retry/fallback API
│   ├── message.h            # ISO 8583 iso_msg_t + formatter prototypes
│   └── common.h             # simple expression macros (NOT a hazard)
├── src/
│   ├── routing/             # routing, card_brand
│   ├── settlement/          # settlement
│   ├── transaction/         # transaction_flow
│   ├── errors/              # error_handling
│   ├── messaging/           # message_format
│   └── config/              # card_brand (brand rule tables, feature flags)
└── vendor/stratus/
    └── tpf_compat.h         # Stratus shim, pulled via a NON-standard relative path (index-escaping)
```

`make tags` indexes `src` + `include` only. `vendor/` is intentionally **outside** the index roots —
this is the mechanism behind the "Stratus include idiom" hazard (Tier 3): a file that `#include`s
`../../vendor/stratus/tpf_compat.h` references symbols the index never saw.

**Module → D5 code-tag map** (every code tag in the vocabulary is exercised):

| Module dir        | D5 code tag(s)              | Role in the payment flow                         |
|-------------------|-----------------------------|--------------------------------------------------|
| `routing/`        | `routing`, `card_brand`     | Dispatches a txn to the brand handler            |
| `settlement/`     | `settlement`                | Reconciliation; canonical depends_on from routing|
| `transaction/`    | `transaction_flow`          | auth → capture → settle lifecycle                |
| `errors/`         | `error_handling`            | Status codes, retry, fallback                    |
| `messaging/`      | `message_format`            | ISO 8583 parse/build                             |
| `config/`         | `card_brand`                | Brand rule tables, feature flags                 |

---

## 2. Expected `coverage_report` (the TASK-012 / TASK-013 target)

```json
"coverage_report": {
  "files_seen": 34,
  "files_extracted": 28,
  "files_fallback": 3,
  "files_unresolved": 3,
  "coverage": 0.82,
  "unresolved_patterns": [
    "function-pointer table dispatch in routing/route_table.c (entry->handler->route)",
    "callback-registered brand vtables in routing/brand_registry.c -> macro-generated *_route",
    "computed function-pointer dispatch in routing/dispatch.c (lookup_handler() then fn(t))",
    "field-codec function-pointer table in messaging/field_codec.c (codec_table[field].encode)",
    "macro-generated functions in config/brand_rules.c (DECLARE_BRAND_HANDLER token-paste)",
    "#ifdef-gated registration + non-standard Stratus include in config/feature_flags.c"
  ]
}
```

- `coverage = files_extracted / files_seen = 28 / 34 = 0.8235` → **0.82**.
- `coverage_floor` is **0.80** (§5.2). The map sits **0.02 above the floor** by design: moving **one**
  Tier-1 file into the unresolved set drops coverage to `27/34 = 0.794 < 0.80`, which fires the
  `REONBOARD_FLAG` (§5.4) — proving the 3-branch gate (TASK-013) is sensitive at the threshold.

**Bucket definitions used here** (consistent with the §3.3 example where extracted/fallback/unresolved
sum to files_seen, and `coverage = extracted/seen`):

- **extracted** — the deterministic extractor produces a complete structural entry (all interfaces +
  all cross-module edges resolved). **`coverage: coarse`, deep-eligible** — the extractor emits
  `coarse` for *every* file (§5.5; only the Stage-2 deep pass promotes to `deep`). See `SIGNOFF.md`.
- **fallback** — a partial entry: symbols and most edges found, but ≥1 *stored* function-pointer call
  site binds to a known in-tree target the map *ought* to link but cannot. `coverage: coarse`.
- **unresolved** — the file's primary structure is invisible to the index (macro-generated functions,
  `#ifdef`-gated bodies, fully computed call targets). `coverage: coarse`; under-reported interfaces.

> **Note on parameter callbacks vs stored pointers.** `errors/retry.c` calls a caller-supplied `op`
> through a function pointer, but that is a *generic utility* callback — there is no concrete in-tree
> edge the map should have linked, so it is **extracted** (Tier 1), not fallback. The fallback tier is
> reserved for *stored* pointers wired to *known in-tree* handlers (route table, registry, codec table).

---

## 3. Per-file inventory (tier + pattern)

### Headers (`*.h`) — all extracted (Tier 1)

| File | Module | Pattern exercised |
|------|--------|-------------------|
| `include/brand.h` | (shared) | enum + the `brand_handler_t` **function-pointer vtable** type def (source of the Tier-2 hazard, but the header itself is clean) |
| `include/txn.h` | (shared) | core struct, enum, `#define` flags, prototypes |
| `include/errors.h` | (shared) | enum, `typedef` fn-ptr `pdlc_op_fn`, prototypes |
| `include/message.h` | (shared) | ISO 8583 struct, prototypes |
| `include/common.h` | (shared) | simple **expression** macros (`PDLC_ARRAY_LEN`, `FIELD_OR`) — resolvable, NOT a hazard |
| `src/routing/routing.h` | routing | module interface prototypes |
| `src/routing/route_table.h` | routing | `route_entry_t` struct (holds a vtable pointer) |
| `src/settlement/reconciler.h` | settlement | prototypes |
| `src/settlement/batch.h` | settlement | `settle_batch_t` struct + prototypes |
| `src/transaction/transaction.h` | transaction | concrete phase-handler prototypes |
| `src/messaging/codec.h` | messaging | `field_codec_t` (fn-ptr table type) — clean as a declaration |
| `src/config/brand_rules.h` | config | `brand_rule_t` struct + `get_brand_rule()` proto |
| `vendor/stratus/tpf_compat.h` | (vendor) | `#pragma stratus` idioms, `STRATUS_SVC` macro, extern decls — extractable as a header; the *hazard* is that includers reference it via an index-escaping path |

### Tier 1 — clean `.c` (extracted, `coverage: coarse`, deep-eligible) — 15 files

| File | Module | Tags | Clean cross-module calls (→ depends_on) |
|------|--------|------|------------------------------------------|
| `src/routing/brand_router.c` | routing | `routing`, `card_brand` | `config/brand_rules`, `routing/route_table`, `routing/brand_registry`, `settlement/reconciler` |
| `src/routing/capture_route.c` | routing | `routing` | `config/brand_rules`, `routing/route_table` |
| `src/settlement/reconciler.c` | settlement | `settlement` | `messaging/formatter`, `settlement/settlement_batch`, `settlement/ledger_post` |
| `src/settlement/settlement_batch.c` | settlement | `settlement` | `messaging/iso8583` |
| `src/settlement/ledger_post.c` | settlement | `settlement` | — |
| `src/messaging/formatter.c` | messaging | `message_format` | `messaging/iso8583` |
| `src/messaging/iso8583.c` | messaging | `message_format` | — |
| `src/transaction/txn_lifecycle.c` | transaction | `transaction_flow` | `transaction/auth_handler`, `transaction/capture_handler`, `transaction/settle_handler`, `transaction/txn_state`, `routing/brand_router`, `routing/capture_route` |
| `src/transaction/txn_state.c` | transaction | `transaction_flow` | — *(called by `txn_lifecycle` via `txn_advance()` — see `used_by` §5)* |
| `src/transaction/auth_handler.c` | transaction | `transaction_flow` | — |
| `src/transaction/capture_handler.c` | transaction | `transaction_flow` | — |
| `src/transaction/settle_handler.c` | transaction | `transaction_flow` | — |
| `src/errors/error_codes.c` | errors | `error_handling` | — |
| `src/errors/retry.c` | errors | `error_handling` | `errors/error_codes` (`is_retryable`) |
| `src/errors/fallback.c` | errors | `error_handling` | — |

### Tier 2 — partial / `coverage: coarse` (fallback) — 3 files

| File | Module | Tags | Hazard |
|------|--------|------|--------|
| `src/routing/route_table.c` | routing | `routing`, `card_brand` | **Dispatch table.** `route_via_table()` invokes `entry->handler->route(t)` through a function pointer installed at runtime via `route_table_install()`. The table array and `route_via_table()` are seen; the call target is not. |
| `src/routing/brand_registry.c` | routing | `routing`, `card_brand` | **Callback registration.** Static vtables (`g_visa_handler`, …) bind `.route` to the macro-generated `*_route` symbols; `register_brand(&g_visa_handler)` → eventual dispatch is not statically traceable. Clean interfaces: `register_brand`, `lookup_handler`, `brand_name`. |
| `src/messaging/field_codec.c` | messaging | `message_format` | **Function-pointer table keyed by field.** `encode_field()/decode_field()` call `g_codecs[field].encode(...)`; the concrete codec is dynamic. Intra-file gap (no missing cross-module edge), still coarse. |

### Tier 3 — hard / unresolved (`coverage: coarse`, under-reported interface) — 3 files

| File | Module | Tags | Hazard |
|------|--------|------|--------|
| `src/routing/dispatch.c` | routing | `routing`, `card_brand` | **Computed call target.** `dispatch_generic()` gets an opaque `const brand_handler_t *` from `lookup_handler()`, selects a member by computed index, and calls through it; `dispatch_via_ctx()` casts a raw `void*` from `brand_ctx`. Targets are unknowable. (One clean edge survives: `routing/brand_registry` via `lookup_handler`.) This is the canonical "function-pointer dispatch in dispatch.c". |
| `src/config/brand_rules.c` | config | `card_brand` | **Macro-generated functions.** `DECLARE_BRAND_HANDLER(brand)` token-pastes whole `<brand>_route` function definitions; the parser does not expand macros (the invocation surfaces as an `ERROR` node), so `visa_route`/`mastercard_route`/`amex_route`(/`discover_route`) are invisible. Only `get_brand_rule()` is resolvable, so the interface is under-reported. |
| `src/config/feature_flags.c` | config | `card_brand` | **`#ifdef` + Stratus include.** Registration blocks gated by `ENABLE_DISCOVER`/`ENABLE_STRATUS_SVC`; `STRATUS_SVC()` and `stratus_*` come from `../../vendor/stratus/tpf_compat.h` via an index-escaping path. Both the conditional branches and the vendor symbols are unresolvable. |

---

## 4. Cross-module dependency chains

### 4.1 Clean two-hop chain (the scope_ripple test — D6b)

All three nodes are **Tier 1**; every hop is a direct, statically-resolvable call, so the extractor
resolves the symbols and `merge_edges` (TASK-011) must stitch the closure:

```
routing/brand_router.c  --reconcile_txn()-->  settlement/reconciler.c  --format_settlement_msg()-->  messaging/formatter.c
        (HOP 1, clean)                                  (HOP 2, clean)
```

This realizes D6b's worked example: *"Brand routing is shared with settlement reconciliation — adding a
brand also changes settlement, not just routing."* The deep pass (TASK-041) traces this closure to raise
a `scope_ripple` flag. The test of `merge_edges` is whether it stitches the two-hop closure, **not**
whether the parser finds the symbols (it does).

`depends_on` / `used_by` for the chain:
- `brand_router` `depends_on` `settlement/reconciler`; `reconciler` `used_by` `routing/brand_router`
- `reconciler` `depends_on` `messaging/formatter`; `formatter` `used_by` `settlement/reconciler`

### 4.2 Unresolvable function-pointer path (the `merge_edges` gap — acceptance #5)

A real cross-module relationship that `merge_edges` **cannot** fully resolve, so it must surface in
`coverage_report.unresolved_patterns` rather than as a `depends_on` edge:

```
routing/route_table.c  --entry->handler->route(t)-->  transaction/{auth,capture,settle}_handler.c
        (Tier 2; target installed at runtime via route_table_install())            (concrete handlers)
```

The concrete handlers (`auth_handle`, …) ARE resolvable on their *direct* edge from
`transaction/txn_lifecycle.c`; only the **table-driven** path into them is unresolvable. So
`transaction/auth_handler` legitimately appears in `txn_lifecycle`'s closure but NOT in
`route_table`'s — the missing edge is the documented gap, confirmed deep by `code_impact`.

A second unresolvable path: `routing/brand_registry.c` vtables → `config/brand_rules.c`
macro-generated `*_route` (invisible symbols), and `routing/dispatch.c` computed targets.

---

## 5. Reverse edges (`used_by`) for the oracle

| File (module/stem) | `used_by` (clean) |
|--------------------|-------------------|
| `config/brand_rules` | `routing/brand_router`, `routing/capture_route` |
| `routing/route_table` | `routing/brand_router`, `routing/capture_route` |
| `routing/brand_registry` | `routing/brand_router`, `routing/dispatch` |
| `routing/brand_router` | `transaction/txn_lifecycle` |
| `routing/capture_route` | `transaction/txn_lifecycle` |
| `settlement/reconciler` | `routing/brand_router` |
| `settlement/settlement_batch` | `settlement/reconciler` |
| `settlement/ledger_post` | `settlement/reconciler` |
| `messaging/formatter` | `settlement/reconciler` |
| `messaging/iso8583` | `settlement/settlement_batch`, `messaging/formatter` |
| `transaction/auth_handler` | `transaction/txn_lifecycle` *(+ unresolved table path from `routing/route_table`)* |
| `transaction/capture_handler` | `transaction/txn_lifecycle` |
| `transaction/settle_handler` | `transaction/txn_lifecycle` |
| `transaction/txn_state` | `transaction/txn_lifecycle` |
| `errors/error_codes` | `errors/retry` |

Files with no `used_by` from another module in this fixture: `errors/fallback`,
`config/feature_flags` (entry points / not yet wired into a caller within the tree).

---

## 6. What the extractor must report per hazard (spec for TASK-009 + oracle for TASK-005)

| Hazard (file) | Why static analysis can't resolve it | What the extractor MUST report |
|---------------|---------------------------------------|--------------------------------|
| Function-pointer vtable dispatch (`route_table.c`) | Target bound at runtime via `route_table_install`; the parser sees the array + the `field_expression` callee (`entry->handler->route`), not the runtime target | `coverage: coarse`; omit the routing→transaction edge from `depends_on`; add to `unresolved_patterns` |
| Callback registration (`brand_registry.c`) | `.route` members point to macro-generated symbols; registration→dispatch link not traceable | `coverage: coarse`; resolve `register_brand`/`lookup_handler`/`brand_name` interfaces; flag the vtable bindings unresolved |
| Codec fn-ptr table (`field_codec.c`) | Concrete codec chosen dynamically by field index | `coverage: coarse`; resolve `encode_field`/`decode_field`; flag the indirect call |
| Computed dispatch (`dispatch.c`) | Opaque vtable pointer + computed member + `void*` cast | `coverage: coarse`; keep the clean `lookup_handler` edge; flag both dispatch sites unresolved |
| Macro-generated functions (`brand_rules.c`) | the parser does not expand `DECLARE_BRAND_HANDLER` (invocation surfaces as an `ERROR` node); generated `*_route` invisible | `coverage: coarse`; resolve only `get_brand_rule`; report interface as under-reported (generated symbols missing) |
| `#ifdef` + non-standard include (`feature_flags.c`) | Inactive `#ifdef` branches not indexed; `vendor/` escapes index roots | `coverage: coarse`; flag conditional registration + the Stratus include as unresolved |

---

*Signed off by:* _____________  (TASK-005 author confirms the tier assignments, edge tables, and the
`coverage_report` summary above before hand-authoring `expected_code_map.json`.)

---

## Additive pass — declared purposes + the versioned duplicate (TASK-112, D-A20)

The V-flag-4 additions. The fixture already exercised the six *parser* blind spots; these
exercise the two **provenance** phenomena D-A20 measured over 6 165 real Stratus files, which
the original fixture could not reproduce at all.

### 1 · Declared purposes under varied labels — 21/35 files (60%)

D-A20's decisive numbers: 58.0% of real files declare a purpose, and **96.7% of those are
specific**. So where a declaration exists it discriminates, and tier 1 is viable as a *hybrid* —
declared purpose where present, include-graph fallback for the rest. Not "purpose alone".

The label distribution is seeded to match the measured one, because assuming a single keyword
would have been a **5.7× under-report**: `Intention:` is only 17% of real declarations, so
counting it alone reports ~10% coverage against a real 58%.

| Label in fixture | Files | Mirrors |
|---|---|---|
| `PURPOSE` / `Purpose` | 9 | 2 727 real files — the dominant form |
| `Intention` | 3 | 623 |
| `DESCRIPTION` / `Description` | 3 | 363 |
| `SYNOPSIS` | 1 | 126 |
| `Descr` / `Desc` | 2 | 23 |
| **`Putpose`** (typo, `capture_route.c`) | 1 | the real `Putpose` ×4 — **why matching must be fuzzy** |

The typo is the load-bearing one: it is why the extractor matches labels at edit-distance ≤ 1
rather than by exact set membership. One edit is measured, not chosen — it catches a transposed
key without starting to match unrelated words.

**14 files are deliberately headerless** (40%), exercising the fallback population: no declared
purpose, `purpose_source: inferred` downstream, and the include graph carrying tier 1 for them.

Also seeded: the `v001 210714` version/date stamp form, so `declared_version` / `declared_date`
have something to parse — and so **staleness** is visible. A purpose stamped 2021 on a file
changed since is high-provenance but possibly out of date, which is what makes the later
`purpose_verdict` pass necessary rather than decorative.

### 2 · The versioned duplicate — `iso8583.c` + `iso8583_v2.c`

D-A20 finding 3. Both files are wired, both define a build/parse pair, neither is marked dead.
An assertion about ISO 8583 message construction lands on "message parsing" and must then answer
a question the code cannot: v1, v2, or both? Getting it wrong means shipping to the dead path.

Real-world bound: **38** suffix files repo-wide (`_v2`, `_v6`, `_test`, `_old`) with no silent
duplicate stems — so the hazard is real but small and fully enumerable up front.

**Expected extractor behaviour: two ordinary files.** The extractor emits both with their own
interfaces and no special marking. Surfacing the pair as a finding that requires operator
disposition is the **map build's** job (D-A16), never a silent pick by the agent — which is
exactly why the extractor must not try to be clever here.
