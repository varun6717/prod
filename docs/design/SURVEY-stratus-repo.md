# SURVEY — Stratus repo header convention + module-grouping signals

**Status:** ⬜ not yet run · **Run on:** the VDI, with Copilot, against the real `Stratus_Repo`
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

| Number | If high | If low |
|---|---|---|
| **Purpose-field coverage** (% of files declaring an intent) | `Intention:` carries tier 1; the model only *verdicts* declared vs actual | the include graph must carry tier 1, and model-inferred purpose becomes the main path, not the fallback |
| **Specific vs generic** (of those that declare one) | tier 1 filters well | tier 1 degrades toward tag-like behaviour — the failure mode D-A19 warns about |

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

## Companion survey — still outstanding

The doc arm has the same open question: **D-A18's per-artifact index assumes the source documents carry
numbered substructure** (clauses, headings) to key entries on. The degraded case is a flat-prose
document needing synthesised paragraph boundaries. That needs the same treatment — a survey of the real
Mastercard/Visa PDFs in `fixtures/pdf/` (and whatever the live SharePoint corpus looks like) to confirm
structure is navigable.

Both arms share this failure mode: **flat prose PDF** (doc side) and **flat directory tree** (code
side). The code side is now measured. The doc side is not.
