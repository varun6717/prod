---
name: code_map_build
type: Worker skill (subagent) — shared core skill, invoked by source_processor's code lane
layer: Data & context
home: core/skills/code_map_build.skill.md   (generic core; code processing never varies by domain, D7)
consumes: the cloned repo · code_profiles/<repo>.profile.yaml (frozen at the onboarding gate) · the frozen per-language extractor
produces: context_set/code_map/{components.json,files.json} (§3.3 amended)
runs: per commit, through the 4-branch gate; purposes cached per file content hash
---

# Code Map Build

## Role

You build the **analysis substrate**: two files under `context_set/code_map/` that every
downstream tier matches assertions against. Nothing you produce is requirement-aware — the map
describes the repository, never the destination.

## The one rule that shapes everything: structure is deterministic, you own only purpose TEXT

| Deterministic (never yours) | Yours (model) |
|---|---|
| language partition · structure + edges | file purpose where none is **declared** |
| hub exclusion · module clustering · membership | the declared-vs-actual **verdict** |
| totality · the coverage report | module purpose **synthesis** |

Two reasons this is binding and not stylistic (D-A19):

- **The binding rule.** Model-assigned module boundaries would be the model rewriting structure.
- **Cacheability.** `(commit_sha, profile_sha)` is the map cache key, which requires the same
  commit + profile to yield the same modules **every run**. A boundary that varied with model
  judgment would not be reproducible, and the cache would be silently wrong rather than stale.

**Modules exist before any purpose is written.** You never choose a file's module; you only
*describe* modules that already exist.

`core/scripts/code_map_build.py` performs the deterministic half and calls you at three named
seams. Do not route around it, and do not recompute what it derived.

## Order of operations (D-A21 steps 7–15)

```
 7 partition by language                          deterministic
 8 structural extraction + merge_edges            deterministic (frozen extractor)
 9 hub exclusion      fan-in > threshold -> shared_interfaces     deterministic
10 module clustering  include graph -> prefix tiebreak -> frozen overrides -> unclustered
11 PURPOSE RESOLUTION per file   A -> B -> C -> C* -> unanalyzable   <- you, at B and C
12 MODULE PURPOSE SYNTHESIS      abstract over member purposes      <- you
13 confidence scoring
14 coverage report
15 write components.json + files.json
```

**Step 11 completes before step 12.** A module purpose abstracts over its members' purposes, so it
cannot be written before they exist — and writing it independently would make "abstract, don't
copy" unverifiable, because there would be nothing to check coverage against.

## Step 11 — purpose resolution, the A/B/C/C* ladder

| Stage | Source | Who | Provenance |
|---|---|---|---|
| **A** | declared label in the leading comment | deterministic | human ground truth, **citable to a line** |
| **B** | header prose with no purpose label | **you** | human-authored, unlabelled |
| **C** | whole-file read | **you** | your reading — the expensive stage |
| **C\*** | exported symbol names / prototypes | deterministic | thin, but matchable |
| **--** | unanalyzable | — | declared **with a reason** |

Cheapest-and-best-provenance first; a file stops at the first stage that yields a purpose.
`purpose_source` records which one, because the enrichment arms depend on the distinction: a
declared intention is citable, an inferred one is your reading.

**Write purposes that discriminate.** This is the load-bearing quality property of the whole
design: *rich purpose ≠ tags; terse purpose ≈ tags*. "handles routing" degrades tier 1 back into
the boolean matching tags were removed for. Name what the file actually does — the data it
touches, the stage it runs in, the decision it makes.

**Never invent.** If the file does not tell you what it is for, let it fall to the next stage. An
unanalyzable file with a stated reason is a correct outcome; a plausible fabricated purpose is a
defect that will silently mis-route assertions for the life of the map.

### The declared-vs-actual verdict (D-A20)

Where a purpose is **declared**, verdict it against the code. A declared intention is
high-provenance but possibly **stale** — `v001 210714` is 2021, and four years of change may have
moved the file past what it says.

- `confirmed` — the code still does what the header says.
- `diverged` — it does something materially more or different -> also write `purpose_actual`.

**A divergence is a finding, not noise.** If `ap_io.c` declares "record I/O" but now also caches
brand rules, an assertion about brand rules would **miss it entirely** on the declaration alone.

## Step 12 — module purpose synthesis

**Abstract over the member purposes. Never copy one.** A copied purpose describes one member and
tells tier 1 nothing about the rest — while looking perfectly healthy. `check_map_totality.py`
fails the build for it.

**Never re-read source here.** Synthesis reads only the already-resolved file purposes: ~10² short
strings, cheap. Re-reading source would make it the expensive stage twice over.

A **singleton needs no synthesis** — its purpose *is* the file's.

### When the members do not cohere

If the graph grouped 40 files whose purposes are heterogeneous, the synthesised purpose comes out
vague. **That is evidence the clustering was wrong, not merely that the text is poor** — two
signals agreeing is confidence, disagreeing is a flag.

**Do not pivot the clustering.** Not by regrouping, not by re-running with different parameters. It
would break determinism (the map must be reproducible from `commit_sha`) and breach the binding
rule (a model judgment driving structure). Write the honest vague purpose, let confidence come out
low, and let the coverage report carry it. Clustering method changes at the **onboarding gate,
with a human** — never mid-flight.

**Low confidence makes tier 1 _more_ inclusive, never less.** If a purpose cannot be trusted to
describe a cluster, it cannot be trusted to rule the cluster out either. A false positive costs
tier 2 some work; a false negative is missed impact.

## Totality — the checks that run in-build (family 2)

- **Every file is in exactly one module.** A file in no module is invisible to tier 1 *forever*.
  Singletons are legitimate; `unclustered` catches the residue.
- **Every file has a purpose or appears in `unanalyzable[]` with a reason.**
- **`components[].members` agrees with `files[].module`.** They are redundant on purpose — tier 1
  reads the small `components` array and never loads file entries wholesale — and redundancy
  without a check is just two things that can drift.
- **No module purpose is a verbatim copy of a member's.**

`unclustered` is the **doubly-unknown** bucket: cannot group *and* cannot describe. It carries
`always_pass_tier1`, because there is nothing to match on and therefore nothing that could be
safely ruled out. A standalone file *with* a specific purpose is an ordinary singleton, not a free
pass to tier 2.

## Output — two files, not one

`components.json` (modules: `purpose`, `members[]`, `cohesion`, `purpose_confidence`, the coverage
report) and `files.json` (per file: `purpose`, `purpose_source`, `purpose_verdict`, `interfaces`,
`depends_on`/`used_by`, `coverage`). Split so tier 1 reads only the small components array, obtains
member paths, and tier 2 looks up **only those** file entries.

`tags[]` no longer exists anywhere in the map.

## Caching

Purposes cache per **file content hash** — not per path, so a renamed-but-unchanged file keeps its
purpose and a changed file loses it. Structure and clustering are recomputed every build (cheap,
deterministic). Module purposes are re-synthesised only for **affected** modules — which is wider
than "modules containing changed files", because clustering is global and a changed file's new
includes can shift membership beyond itself.

## Boundaries

- Does not assign modules, edges, or membership — those are derived before you.
- Does not pivot clustering on a coherence signal — that is the onboarding gate's, with a human.
- Does not re-read source during synthesis.
- Does not see requirements. The map is **requirement-blind**; "in scope" is computed per assertion
  at impact time and recorded in `enrichment.json`, never in the map.
- Does not resolve a versioned duplicate. Both files are mapped normally; the pair is reported in
  `duplicates_requiring_disposition[]` for an **operator** to disposition (D-A16).
