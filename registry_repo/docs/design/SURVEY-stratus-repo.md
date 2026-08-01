# SURVEY — Stratus repo header convention + module-grouping signals

**Status:** ✅ **RUN 2026-07-29** — 6 165 files · report at `Stratus_Repo/HEADER_SURVEY.md` · results folded into ADR-008 D-A20
**Feeds:** `ADR-008-solution-intent-pivot.md` → **D-A19 / D-A20** (item 6, code-impact without tags)

---

## Why this survey exists

ADR-008 removes tags. On the code side, the replacement is a **two-tier semantic walk**: match an
assertion against ~N **module** purposes first, then descend to **file** purposes only inside matched
modules (D-A19). That walk only works if two things hold:

1. **Modules can be derived deterministically** — the model may not choose them (binding rule: the
   structural extractor is deterministic and frozen, the model owns only `purpose`; also `commit_sha`
   is the whole-map cache key, so the same commit must yield the same modules every run).
2. **Purposes are specific enough to discriminate.** Rich purpose ≠ tags. **Terse purpose ≈ tags** — if
   purposes read "handles routing", tier 1 filters nothing and we have reinvented the problem we are
   removing.

Two screenshots (2026-07-29) already invalidated the first draft's assumptions:

- **`Stratus_Repo/source/` is essentially flat** — directory partition yields one module, so the
  directory signal contributes **nothing** here.
- **Files carry a structured header with an explicit `Intention:` field** — e.g.
  `amex_se_map_io.c` → *"routines to lookup the amex se number"*. This is **better** than a
  model-written purpose: deterministic to extract, human-authored, and **citable to a line**.
- **But filename quality varies enormously.** `amex_se_map_io.c` is informative; `722.c`, `60_dep.c`,
  `96b_extract.c`, `a2_give_ops_hell.c` are not. So prefix families are a **weaker** signal than first
  credited, and for a file like `722.c` the header may be the *only* semantic signal that exists.
- **`include/` and `source/` are a file-type split, not a functional one**, and `.h` files appear in
  both — so `.c`/`.h` pairing is inconsistent.

This survey measures what is actually there, rather than designing against an assumption.

## The two numbers that decide the design

| Number | Result | Verdict |
|---|---|---|
| **Purpose-field coverage** | **58.0%** (3 576 / 6 165) | Moderate — declared purpose carries the majority; the **include graph must carry the other 42%**. Tier 1 is a **hybrid**, not "purpose alone." |
| **Specific vs generic** | **96.7% specific** (3 457 / 119) | **Strong** — the terse-purpose failure mode D-A19 warns about is essentially **absent** (3.3%). |
| **Leading-comment coverage** | **96.1%** | Nearly every file has *some* header block — see the recoverable-population note below. |

**The discovery instruction was decisive.** Purpose appears under `PURPOSE` (2 403), `Intention` (623),
`DESCRIPTION`/`Description` (363), `Purpose` (324), `SYNOPSIS` (126), `Descr`/`Desc` (23), plus typos
(`Putpose` ×4). **`Intention:` is only 17% of the total** — counting it alone would have reported ~10%
coverage instead of 58%, a **5.7× under-report**, and the design would have been rewritten on false
evidence.

**Signal priority came out close to inverted** from the draft: the **include graph is primary**
(95.1% of includes resolve to a repo file, avg 9.1 per file), declared purpose is the semantic second,
and **prefix families are weak** (903 tokens, 24% singletons, cryptic — `s`, `md`, `or`). `.c`/`.h`
pairing is unreliable (1 157 `.c` files have their `.h` in the other directory).

## Follow-ups this raised

1. **Is the missing 42% uniform or clustered?** Module purposes are synthesised from member file
   purposes, so a concentrated gap makes tier 1 fail in one subsystem while the aggregate looks healthy.
2. **~2 300 files have a header but no purpose-labelled field** (the 96.1% / 58.0% gap) — likely usable
   prose under no label, which would push effective coverage well above 58%.

Everything else in the survey is a secondary grouping signal, collected because it is nearly free
during a scan that is happening anyway.

---

## The prompt — paste into Copilot on the VDI

```
TASK — read-only survey. Do NOT modify, reformat, or create any source file.

Scan every .c and .h file under Stratus_Repo/include/ and Stratus_Repo/source/
(recursively). I need to know whether these files carry a machine-parseable
header comment describing what each file does, and exactly how it varies.

1. DISCOVER THE CONVENTION — do not assume a keyword.
   For each file, look at the leading comment block (before the first #include
   or code statement). Identify every "Label:" style field you find in those
   blocks — e.g. Name:, Intention:, Purpose:, Description:, Function:, Module:,
   Author:, MODIFICATION HISTORY:, or anything else.
   Report the DISTINCT field labels found, with a count of how many files use
   each, sorted by frequency. Include the exact spelling and capitalization.

2. COVERAGE — report actual counts, not estimates:
   - total .c files, total .h files (per directory)
   - how many have a leading comment block at all
   - how many have a field that states the file's PURPOSE/INTENT (whatever it
     is labelled)
   - how many have NO such field — and list those filenames in full

3. SAMPLES — for each distinct label variant, show 3 real examples verbatim
   (filename + the header block). Also show 5 examples of files with no
   usable header.

4. QUALITY — for files that do state a purpose, assess whether the text is
   specific enough to tell one file from another. Flag any that are generic or
   empty (e.g. "misc routines", "see header", "TBD", a restatement of the
   filename). Give a rough count of specific vs generic.

5. WHILE YOU ARE SCANNING, also report:
   a) Filename prefix families — group filenames by leading token (split on _
      and camelCase). Report each family with its file count. Flag files whose
      names carry no semantic signal (e.g. purely numeric like 722.c).
   b) #include usage — do files consistently use #include "local.h" for
      intra-repo dependencies? Report roughly how many local includes per file
      and whether an internal dependency graph is derivable.
   c) Versioned or duplicated files — any *_v2, *_v3, *_old, *_new, *_bak,
      *_test pairs, or two files that look like alternate implementations of
      the same thing. List them.
   d) Where .h files actually live — how many headers are in include/ vs
      source/, and how many .c files have a matching .h in the OTHER directory.

OUTPUT: write the findings to Stratus_Repo/HEADER_SURVEY.md as a markdown
report with one section per numbered item above. Use real counts and real
filenames throughout — no illustrative or invented examples. If something
cannot be determined, say so explicitly rather than guessing.
```

### Why the prompt is shaped this way

- **Discovers rather than counts.** Asking "how many files have `Intention:`" would miss a `Purpose:`
  variant entirely and report false low coverage.
- **Demands the no-header list in full.** That population *is* the model-inferred fallback set; its size
  decides whether the fallback is a minor path or the primary one.
- **Asks about generic purposes.** A header reading "misc routines" is present but useless for tier-1
  matching — the terse-purpose failure mode, measured rather than assumed.
- **Bundles 5a–5d.** These are the module-grouping signals from D-A20, nearly free to collect during a
  scan already running. 5a in particular reveals whether prefix families work repo-wide or only in the
  well-named corner.

---

## What to do with the result

1. Read `Stratus_Repo/HEADER_SURVEY.md`.
2. Update **D-A20** in `ADR-008-solution-intent-pivot.md` with the real numbers, replacing the
   two-screenshot evidence with a full-repo measurement.
3. If **purpose-field coverage is low** or **generic dominates**, D-A19's tier-1 mechanism needs
   revisiting before Phase B — the include graph would have to carry the filtering, which is a
   materially different build.
4. Re-confirm the module-grouping signal priority in D-A20 against 5a–5d.

## Companion survey — written, not yet run

→ **`SURVEY-doc-structure.md`** covers the doc arm: whether source documents carry the navigable
substructure D-A18's per-artifact index keys on. Both arms share the same failure mode — **flat prose
PDF** (doc side) and **flat directory tree** (code side) — and the code side already proved to *be* the
degraded case, so the doc side is worth measuring rather than assuming.

That file also carries **three follow-up items for this survey** (graph isolation, symbol presence, and
the unanalyzable intersection). Item 6 — graph isolation — is the one that could still change the
design, since degree-zero files become singleton modules and a large population breaks tier-1 economy.
