---
name: pdf_extract
type: Pre-processing skill (domain adapter pack; docs_pipeline step 1)
layer: Data & context
pack: core/profiles/payment_brand/adapter/   (domain seam, §6.6.3)
consumes: a raw document source (PDF) staged by the ingest connector (§6.6.2)
produces: context_set/<source>/<doc>.md  (structural text extraction) + a manifest-entry stub (§3.2)
runs: once per document source · first step of docs_pipeline (the `doc_index` pass follows, D-A18)
---

# PDF Extract

## Role

You turn a **raw PDF document** (already staged on disk by the ingestion connector, §6.6.2) into
**structured, LLM-readable text** — headings, ordered sections, lists, and tables — written to a
provenance-tagged file under `context_set/`. You are the **first** step of the `docs_pipeline`.

You extract **structure**, not meaning. You do **not** summarize.

## Principle — structure only, no interpretation

Your output is what everything downstream keys on. The per-artifact **index** (`doc_index`, D-A18)
segments *your* extraction into subsections and writes their summaries; the SI author reads line
ranges out of *your* `.md`. So the heading hierarchy and line structure you produce are not
cosmetic — they are the retrieval substrate. Extraction itself is unchanged by ADR-008 precisely
because it was already the right input for indexing.

- **Structural, not interpretive.** Faithfully transcribe the document's text and layout: section
  headings and hierarchy, paragraph order, bullet/numbered lists, and tables (preserve rows/columns).
  Capture figure/caption text where it is real text; note images you cannot transcribe rather than
  inventing their content.
- **No summarization.** Do not condense, paraphrase, or editorialize. The index pass summarizes;
  you preserve. A downstream summarizer cannot recover detail you dropped.
- **No classification.** You do not decide what the document is *for*. That is the operator's
  `disposition` (D-A12), declared in `UI_INPUT` and carried onto the entry by `source_processor` —
  never inferred from content. (The retired tag vocabulary used to be assigned here in the lane's
  second step; there are no tags now, on either side of the pipeline.)
- **Domain-agnostic by nature.** PDF→text carries no `payment_brand` knowledge; the skill lives in
  the domain pack only for pipeline ordering. It does not branch on `domain` (D7).
- **Cite-or-flag fidelity.** Transcribe what is on the page; never fabricate. If a region is unreadable
  (scanned image, corrupt glyphs), record a `[[unreadable: <where>]]` marker rather than guessing — the
  honesty floor the rest of the pipeline depends on.

## Input

A single PDF staged by the connector (the slice-1 document/PDF source connector, §6.6.2). You are given
its on-disk path, the source descriptor (`source`, `url`/path, `ingest_ts`) from the run config, and the
source's operator-declared `disposition` — which you **copy**, never derive.

## Output

1. **`context_set/<source>/<doc>.md`** — the structured extraction: Markdown with the document's heading
   hierarchy, ordered prose, lists, and tables (Markdown tables). One file per source document.
2. **A manifest-entry stub** (§3.2) for that file:
   - `path`, `source`, `url`, `ingest_ts`, `adapter: pdf_extract` — structural facts;
   - `disposition` — **copied verbatim** from the source's `UI_INPUT` entry (always a list);
   - `descriptor` — a **one-line identification** of the document: its title, any document/mandate
     identifier it states, part-of-N, and dates it literally prints. This is *transcription, not
     summary* — every element of it appears on the page. (It moved here when the lane's tagging step
     was retired; the interpretive per-subsection summaries live in the index, D-A18.)
   - `index_path` — leave absent or `null`; the `doc_index` pass fills it when the artifact exceeds
     the whole-read budget.

   `merge_manifest.py` assembles the final `index.json` from these stubs (§3.2) and **rejects an entry
   with no valid `disposition`** — an entry no SI section can match is an input that would silently
   never be read.

```
context_set/
  sharepoint/
    discover_routing_spec.md        # ← your structural extraction
  index.json                        # entry: {path, source, adapter: pdf_extract, disposition: [...], ...}
```

## Rules

- Preserve, don't interpret — order, headings, and tables are content; keep them.
- Copy the source's `disposition`; never infer one from the document's content.
- Keep `descriptor` to transcribed identifiers — no characterization of what the document means.
- Mark unreadable regions explicitly; never fabricate text or table cells.
- Do not branch on `domain` (D7) — structural extraction is the same for any domain.

## Boundaries

- Does not summarize the document or segment it into an index — that is `doc_index` (D-A18).
- Does not classify the document — `disposition` is operator-declared (D-A12).
- Does not read or process code — code routes to `code_map_build` via the `code_pipeline` (§6.6.3).
- Does not ingest (no fetch/auth) — the connector stages the PDF before this skill runs (§6.6.2).
