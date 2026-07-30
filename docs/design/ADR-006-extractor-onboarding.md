# ADR-006 — Agent-assisted extractor onboarding: propose/refine a per-language extractor for a new language (Branch A, propose-never-freeze)

**Status:** **Accepted** — decision original to `REQUIREMENTS.md` Draft v1 (`FR-DC-19` W + the C5 handed-forward note, V-approved there); extracted to ADR form 2026-07-02 as an editorial split (no semantic change). Deferred (W); named now, built when a second language arrives. No in-slice build, no pinned-contract change.
**Amends:** `REQUIREMENTS.md` (`FR-DC-19` W, in the FR-DC cluster beside FR-DC-20/22/23; the C5 handed-forward note). No normative schema change — `onboarding_manifest.yaml` already admits an additional per-language extractor entry additively; no reserved hook, no Python this slice. Tech-spec follow-on (the `extractor_onboard` contract) is authored when the skill is built.
**Does not reopen:** D1–D10, nor any architectural invariant — the extractor stays **deterministic, frozen, never model-rewritten at runtime**; the 3-branch gate stays **model-free**; the model owns `purpose`+`tags` only. This ADR governs the *authoring* of a new extractor (a human-gated, build-time act), never its runtime behavior.
**Sibling of:** ADR-003 (`domain_onboard`, vocabulary), ADR-004 (`profile_onboard`, profiles), ADR-005 (`adapter_onboard`, adapter pack). Same propose-never-bless governance — an agent proposes a frozen artifact, a human freezes/commits — applied here to the **per-language extractor**, the structural anchor of the code map.

---

## Context

The code map's structural spine is a per-language **extractor** (ADR-001: tree-sitter + tree-sitter-c for C), which the 3-branch gate (FR-DC-15) treats as a frozen, version-controlled artifact keyed in `onboarding_manifest.yaml`. The gate branches deterministically: no frozen extractor for a language → **onboarding**; content hash unchanged → reuse the cached `code_map.json`; content changed → rebuild changed files only, extractor stays frozen.

Branch A — "no frozen extractor" — is the one branch with no defined authoring home. On slice-1 the only language is C, onboarded and frozen manually (TASK-009/012), so Branch A never fires; a language with no extractor is covered meanwhile by the **model-only fallback** (FR-DC-17), which yields a lower-coverage map rather than blocking map-build. But when a second language arrives, "build an extractor for it" must not be re-derived ad hoc — a runtime-mutable or model-rewritten extractor would break the reproducibility/audit anchor the whole code map rests on (the same repo could then yield different maps across runs).

## Decision

Name a deferred, human-gated skill — working name **`extractor_onboard`** — that performs Branch A by **proposing**, never freezing. When the gate detects no frozen extractor for a language, `extractor_onboard` MAY:

1. Read a **representative code sample** for the language.
2. **Propose or refine** a per-language extractor + its `onboarding_manifest` entry, normalized to the `code_map` structural contract (§5.5).
3. **Run it against the sample** and emit a **reviewable enhancement artifact**: the proposed extractor, a coverage estimate, and an unresolved-pattern report (the static-analysis blind spots it cannot yet resolve).

A human reviews, freezes, and commits per FR-DC-14. The skill MUST NOT freeze, self-bless, or modify a frozen extractor.

The **steady-state** extractor — once frozen — is invoked by the `code_map_build` gate skill (FR-DC-15), **not** by `extractor_onboard`. Onboarding authors the tool; the gate runs it. The two never mix.

## Rationale

- **Preserves the freeze invariant (FR-DC-14).** The agent proposes; a human freezes. Nothing self-refines at runtime, so map reproducibility holds.
- **A defined home, not ad-hoc derivation.** The "new language" case gets a named, human-gated skill rather than being improvised per repo — keeping FR-DC-14's guarantee intact when language #2 lands.
- **Earns no MVP cost.** Slice-1's single language is onboarded manually, and the model-only fallback keeps map-build live for any unonboarded language in the interim — so naming it now is free and building it later is purely additive.
- **Pattern-consistent.** Same propose-never-bless shape as the vocabulary (ADR-003), profile (ADR-004), and adapter (ADR-005) seam artifacts — one coherent onboarding story across all four frozen artifacts.

## Consequences

- **No in-slice change.** Nothing is built; no committed code, no schema edit, no reserved field. The C extractor stays hand-frozen (TASK-009/012).
- **First exercise** is a second language at the port — TASK-069 pairs `extractor_onboard` with a 2nd-language extractor.
- **Tech-spec follow-on (when built):** define the `extractor_onboard` contract — sample selection, the proposal-artifact shape, the coverage-estimate + unresolved-pattern report, and the freeze hand-off into `onboarding_manifest.yaml`.
- **Scope discipline.** Records a `W`-level FR and reserves a name; does not reopen D1–D10, change a pinned schema, or pull work into the slice.
