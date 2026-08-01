# `core/code_profiles/` — the per-repo signal profile (D-A22, D-A21)

One file per repository: `<repo>.profile.yaml`. It records **how to read this repo** — which
signals derive its modules, which labels carry its purposes, where its thresholds sit — frozen at
a human onboarding gate.

## Why this is a separate seam from the extractor

`core/extractor_manifest.yaml` freezes **per-language** parsing: one C extractor serves every C
repo. But two C repos can need completely different *reading rules* — a flat 6 000-file tree where
the include graph is the only usable signal, versus a cleanly-foldered one where directories carry
modules. That variation is per **repo**, not per language, so it cannot live in the extractor
manifest without forking the extractor.

Hence the split (D-A22): language freeze in the manifest, repo reading-rules here, mutable build
state in `cache/code_maps/index.yaml`. Three lifetimes, three homes.

## What is in it, and why each field exists

| Block | Field | Why it varies per repo |
|---|---|---|
| `derivation` | `priority` | D-A20's survey **inverted the draft ordering**: the include graph is primary (56.5% of files use local includes, 95.1% resolving), prefixes are tie-break only, directory is worthless in a flat tree. A different repo can invert it back. |
| | `hub_threshold_fan_in` | The scan proposes a number; the gate exists because some high-fan-in files are genuinely modular rather than shared surfaces. |
| | `cluster_min_size` / `cluster_max_size` | Guards the two failure shapes: a tail of 2-file clusters, or one 800-file giant. |
| `purpose` | `label_aliases` | The measured reason this is data: `Intention:` alone under-reports coverage **5.7×**. A team-specific label (`Function:`) is a data edit here, never a code change. |
| | `fuzzy_edit_distance` | `Putpose` ×4 is real. |
| | `warn_if_human_authored_below` | The **quality ceiling** the gate exists to make visible: a map that is 85% human-authored purposes is a fundamentally better substrate than one that is 60% model-inferred. |
| | `low_confidence_threshold` | What counts as low enough that tier 1 **widens** rather than excludes. |
| `stages` | `skip_stage_c` | The gate's cost lever. Skipping is a **deferral, not an exclusion** — purposes cache per file hash, so stage C can be run later to fill the gaps. |
| `overrides` | `singleton_groups` | Model-**proposed**, human-approved groupings, frozen as **data**. This is propose-never-bless: nothing model-driven survives the freeze except as data a human signed. |
| `gate` | `status`, `reviewed_by`, `actions_taken` | The audit record of the only human checkpoint on map quality. |

## The freeze, and what `profile_sha` buys

Freezing computes `profile_sha` over the profile's semantic content. It is half of the map cache
key `(commit_sha, profile_sha)` — and it is what makes **gate branch 4** possible: if
re-onboarding moves the hub threshold from 500 to 200, *every* module boundary can shift, so
nothing in the old map is trustworthy. **A profile change invalidates wholesale; a commit change
invalidates selectively.**

The three gate actions are **pre-freeze only**. After approval the profile is frozen data and none
of them exist at runtime — that is the determinism guarantee, and it is why the actions can be as
model-assisted as they like without weakening the binding rule.
