# ENV_PRECHECK.md — Tooling availability + fallback decisions

This file records the **port-time tooling checkpoint** (TECH_SPEC §5.7) for the C extractor.
It mirrors the `port_check(manifest, VDI)` logic: per tool in `onboarding_manifest.yaml`'s
`tools_required`, one of three branches applies: available → version / absent+provisionable → ops
step / absent+unprovisionable → `enable_model_fallback(c)`.

> **Toolchain change (ADR-001, 2026-06-19).** The C extractor uses **`tree-sitter` + `tree-sitter-c`**
> (Python deps, imported in a venv), **not** `ctags`/`cscope`. Reason: the target JPMC VDI is
> AppLocker-locked — the MSYS2 `cscope`/`ctags` installers are blocked and a formal IT package is
> slow, while pip into a venv runs in-policy. tree-sitter preserves every static-analysis blind spot
> (empirically verified against the TASK-005 oracle — see `SIGNOFF.md` re-validation addendum). So
> "availability" here means **`import` succeeds in the venv**, not "binary on PATH."

Checked: 2026-06-19 · macOS 25.2.0 (Darwin arm64) ext-build + JPMC VDI (Windows/AppLocker).

---

## C extractor tooling (`tools_required: [tree-sitter==0.25.2, tree-sitter-c==0.24.2]`)

### External build (macOS) — AVAILABLE

**Branch: AVAILABLE.** Installed into `./.venv` 2026-06-19:

```
tree-sitter    0.25.2
tree-sitter-c  0.24.2
```

Verified: parsed all 34 `fixtures/c_repo` files; structural output matches the signed oracle
`expected_code_map.json` (interfaces, edges, coverage 0.82). The macro / function-pointer / `#ifdef`
blind spots reproduce exactly (the `DECLARE_BRAND_HANDLER` macro surfaces as a detectable `ERROR`
node). Install: `python3 -m venv .venv && .venv/bin/pip install "tree-sitter==0.25.2" "tree-sitter-c==0.24.2"`.

### JPMC VDI (Windows/AppLocker) — AVAILABLE

**Branch: AVAILABLE.** Installed into the VDI `.venv` 2026-06-19 (`tree-sitter 0.25.2` +
`tree-sitter-c 0.24.2`); verified parsing a real Stratus C file (`Stratus_Repo/source/120b_extract.c`,
30,459 bytes, 23 top-level decls). The pip mirror is reachable and `python.exe` is AppLocker-allowed,
so no IT exception is required — this is the reason the toolchain moved off `ctags`/`cscope` (ADR-001).

**Ops step (any environment):** `pip install "tree-sitter==0.25.2" "tree-sitter-c==0.24.2"` into the
extractor's venv. In production the venv provisioning is a **VDI prerequisite** Generate names (same
shape as the FR-XS-26 allow-list), not something the scaffolder emits.

---

## Port-time summary

| Tool          | macOS ext-build       | JPMC VDI                  | Branch    |
|---------------|-----------------------|---------------------------|-----------|
| tree-sitter   | 0.25.2 (`.venv`)      | 0.25.2 (`.venv`)          | AVAILABLE |
| tree-sitter-c | 0.24.2 (`.venv`)      | 0.24.2 (`.venv`)          | AVAILABLE |

**Fallback posture:** if the deps are absent and unprovisionable (no pip mirror) on a target VDI, §5.5
`model_fallback(repo)` activates — all entries are marked `coverage: coarse`, the top-level coverage is
forced to `coarse`, and the deep pass (`code_impact`) confirms blind spots. Never a hard failure. The
decision is recorded in `decisions.jsonl` as `reonboard_flag`.

---

## FR-XS-26 allow-list prerequisite (Generate surface — not scaffolder-emitted)

This tooling availability is a **Generate/onboarding prerequisite** of the same shape as the
FR-XS-26 allow-list: Generate names it, the scaffolder does not emit it. The operator must
confirm tool availability before the extractor runs on any new environment.

## Copilot/VDI validation (D10 / FR-XS-24) — PASSED 2026-06-16

**Result: PASSED.** Run in the target JPMC VDI. Command execution confirmed (multi-command
sequence ran to completion without per-command approval stalls); parallel fan-out ran with
genuine concurrency (two `worker` subagents concurrently); custom subagents loaded. Org
Copilot policy does not lock approval — the one scenario that would have hard-blocked the
Copilot path did not occur. **Do not re-run.**

**Allow-list scope finding (FR-XS-26):** workspace `.vscode/settings.json` did **not** take
effect for `github.copilot.chat.agent.terminal.allowList`; **user-scope** settings did. The
allow-list home is therefore **user scope**, not the scaffold. In production it must be
provisioned centrally (MDM / managed VS Code profile / VDI bootstrap) and surfaced by
Generate/onboarding as a **VDI prerequisite** — the scaffolder does NOT emit it.

Satisfies: FR-XS-22 (manual-start MVP), FR-XS-23 (Claude Code + Copilot co-equal),
FR-XS-24 (Copilot/VDI PASSED), FR-XS-26 (allow-list home = user scope).
