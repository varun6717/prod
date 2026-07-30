# ADR-007 — Multi-system / cross-repo code impact: the deferred "fractal" extension (single-repo MVP + reserved seams)

**Status:** **Accepted** — decision original to `REQUIREMENTS.md` Draft v1 (`FR-DC-13` M + the C5 handed-forward note, V-approved there); extracted to ADR form 2026-07-02 as an editorial split (no semantic change). Deferred (design recorded, not built). MVP is single-repo (FR-DC-13); staged adoption named; only stage 1 (single-repo) is in scope.
**Amends:** `REQUIREMENTS.md` (C5 handed-forward note; `FR-DC-13`); `TECH_SPEC.md` §3.3 (the reserved `external_calls`/`exposes` fields, unpopulated in MVP), §5.7, §11 deferred-work note. No normative reshape — the reserved fields make the extension additive, not a schema change.
**Does not reopen:** D1–D10, nor the code-impact subsystem's invariants — the deterministic/frozen extractor, model-free gate, and within-repo dependency closure (`depends_on` + `used_by`) are unchanged. This ADR only records how the single-repo design extends *one tier up* when multi-repo lands.

---

## Context

MVP code impact is **single-repo** (FR-DC-13): one repo cloned by SEAL ID, one `code_map.json`, within-repo dependency closure only. Real JPMC changes routinely ripple across repos (a routing change touching settlement in another service), so a cross-repo tier is genuinely needed — but building it now would multiply cost and risk before the single-repo spine is proven on the real corpus. The question this ADR settles is not *whether* to build it (deferred) but *what shape* it takes, so the MVP `code_map.json` reserves the right hooks and the later extension is additive rather than a reshape.

## Decision

Defer multi-system / cross-repo impact, and record its shape as a **"fractal" reuse** of the existing patterns one tier up:

- **System tier (discovery).** Discover impacted repos by matching the requirement against a cached corpus of **coarse `code_map`s** (coarse-map-as-discovery), backed by a *thin* repo inventory (enumeration + ownership + LOB filter) and an architecture-metadata cross-check for config-driven edges. Then the existing **code tier** runs within each impacted repo, unchanged.
- **Cross-repo analysis only at integration seams.** Match a producer's outbound call site to the consumer's inbound handler, check whether the **contract** changes, raise contract-break flags, and descend into the consumer **only if the contract breaks** — never an N×N all-function trace.
- **Staged adoption.** (1) single-repo [MVP] → (2) explicit multi-repo (operator names the repos; stitch at contracts) → (3) registry-filtered coarse-map discovery.

**Forward-compat hook (in-slice):** `code_map.json` reserves `external_calls` / `exposes` now (unpopulated in MVP, §3.3) so the cross-repo extension adds data to an existing shape rather than reshaping it.

## Rationale

- **Reuse over reinvention.** The system tier is the code tier's own coarse-map + closure pattern applied to repos instead of files — one mental model, not two.
- **Bounded cost.** Contract-seam stitching (descend only on break) avoids the combinatorial N×N trace a naïve cross-repo impact would incur.
- **Additive by construction.** Reserving `external_calls`/`exposes` now means stage 2/3 populate fields that already exist; no migration of committed maps.
- **Proven-spine-first.** Deferring keeps the slice focused on making single-repo impact correct on the real corpus before scaling the axis.

## Consequences

- **In-slice:** only the reserved (unpopulated) fields — no cross-repo code, no repo inventory, no discovery corpus.
- **First exercise:** stage 2 (explicit operator-named multi-repo) at the port — TASK-068 (multi-repo cross-repo closure).
- **Scope discipline:** records the deferred design and its forward-compat hook; does not reopen FR-DC-13 or pull the system tier into the slice.
