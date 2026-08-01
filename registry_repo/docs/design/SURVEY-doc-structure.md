# SURVEY — document structure + index viability (doc arm)

**Status:** 🟡 **PARTIALLY ANSWERED by screenshots 2026-07-31** (Visa VisaNet Global Technical Letter,
Article 11.2.6) — verdict **WELL-STRUCTURED**. Full run still wanted for corpus-wide numbers and
extraction fidelity. · **Run on:** the VDI, with Copilot, against the **real** document corpus
**Feeds:** `ADR-008-solution-intent-pivot.md` → **D-A18** (item 4, retrieval within a class)
**Companion to:** `SURVEY-stratus-repo.md` (code arm — ✅ run 2026-07-29)

---

## Why this survey exists

ADR-008 removes tags. On the doc side, the replacement is a **per-artifact index** (D-A18): at ingest,
each document gets an index file with **one entry per subsection**, carrying that subsection's heading,
line range, and a condensed summary. At authoring time a Solution Intent section consults the index and
pulls only the identified passages.

That design rests on **one unverified assumption**: that the source documents carry **navigable
substructure** — numbered clauses, headings, a table of contents — for entries to key on.

D-A18 already names the degraded case: *"a document with no substructure — 40 pages, five headings, flat
prose beneath. Boundaries must then be synthesised by paragraph grouping to a target size. It works, but
it is the weakest case, and it is what the real fixtures must be checked against."*

**This is the last unmeasured assumption in the design.** The code arm was measured on 2026-07-29 and the
result inverted a signal ranking and caught a 5.7× coverage under-report — so measuring rather than
assuming has already paid for itself once here.

## Screenshot findings — 2026-07-31 (partial, one article)

| Question | Finding |
|---|---|
| **Structure coverage** | **WELL-STRUCTURED.** Numbered articles (`11.2.6`), numbered tables (`Table 11.2.6.A–F`) each with descriptive titles, two clear heading levels, running headers, per-chapter pagination. **No TOC needed — the numbering *is* the index.** |
| **Entry size** | **Skews SMALL, not large** — the opposite of what was planned for. ~7 pages (11-51→11-57) across ~15 sections. Some sections are a single sentence (*"ACTIVATION DETAILS — There are no activation requirements…"*). **A merge policy for tiny entries matters more than a subdivide policy for oversized ones.** |
| **Heading informativeness** | **Mixed** — roughly half are template boilerplate (`BUSINESS OVERVIEW`, `Business Reason`, `REFERENCE`, `IMPACT CONSIDERATIONS`), half are specific (`Key V.I.P. and BASE II Fields and Positions`). **Confirms summaries are required**; heading-only indexing would have failed. |
| **Cross-references** | **Real and frequent** — `Article 1.1`, `Article 11.2.5`, `Appendix E`, plus external specs. Pulling one article may be insufficient. |
| **Mixed content** | The letter carries **business rationale AND technical detail** in one artifact → a case for **multi-disposition** (D-A12), not a new mechanism. |

Still open: corpus-wide numbers (this is one article), **extraction fidelity** (does `pdf_extract`
preserve this?), and whether other Visa article types or Mastercard documents differ.

## The two numbers that decide it

| Number | If good | If poor |
|---|---|---|
| **Structure coverage** — % of documents with detectable heading/clause hierarchy | the index keys on the document's own structure; D-A18 works as designed | boundaries must be **synthesised** by paragraph grouping — the weak path, and the embeddings conversation reopens |
| **Entry size distribution** — lines/words per structural subsection | per-subsection granularity is genuinely fine-grained; retrieval is precise | subsections are too coarse (a "section" is 40 pages), so subdivision does the real work and the document's structure buys little |

A third, cheaper but essential: **extraction fidelity.** The index keys on `pdf_extract`'s *output*, not
on the PDF. `pdf_extract.skill.md` claims to emit "the document's heading hierarchy … section headings
and hierarchy, paragraph order, bullet/numbered lists, and tables" — if that flattens in practice, the
index has nothing to work with regardless of what the source PDF contains.

---

## The prompt — paste into Copilot on the VDI

```
TASK — read-only survey. Do NOT modify any document or skill file.

I need to know whether our source documents carry enough internal structure to
build a per-subsection navigation index from them. Use the REAL corpus, not
only the bundled fixtures: the SharePoint mandate PDFs, the Confluence pages,
and fixtures/pdf/ if that is all that is reachable. Say clearly which corpus
you actually had access to and how many documents were in it.

1. CORPUS INVENTORY
   List every document you can reach: filename, type (pdf/html/other), page
   count, and approximate word count. Report totals and the size distribution
   (how many are under 5 pages, 5-20, 20-50, 50+).

2. STRUCTURE DETECTION — per document
   Determine whether the document has a usable heading/clause hierarchy:
     - is there a table of contents?
     - are there numbered sections/clauses (1, 1.1, 1.1.1 / Article 4 / §7)?
     - are there unnumbered but visually consistent headings?
     - how many hierarchy LEVELS deep does it go?
     - how many total structural subsections at the deepest usable level?
   Classify each document as: WELL-STRUCTURED (numbered, consistent, 2+ levels)
   / LOOSELY-STRUCTURED (headings but inconsistent or 1 level) / FLAT (prose,
   no reliable internal divisions). Report counts per class.

3. ENTRY SIZE DISTRIBUTION
   For the documents that are structured, treat each deepest-level subsection
   as one prospective index entry. Report the distribution of entry sizes in
   lines and words: min, median, max, and how many entries exceed ~150 lines
   (those would need subdividing). Flag any single subsection larger than 5
   pages, and say what it contains (usually a long table).

4. EXTRACTION FIDELITY — this is the critical check
   Take 3 representative documents (one well-structured, one loosely, one flat
   if available). Run them through core/profiles/payment_brand/adapter/
   pdf_extract.skill.md as written. Then compare the markdown OUTPUT against
   the source:
     - did heading hierarchy survive as markdown headings?
     - did numbered clause identifiers survive?
     - did tables survive as tables?
     - did reading order survive?
   Show the first ~40 lines of each extraction verbatim next to a description
   of the corresponding source pages. Be explicit about anything LOST.

5. ALSO REPORT
   a) Table density - roughly what fraction of content is tables vs prose?
      Which documents are table-dominated?
   b) Cross-references - do sections reference other sections ("see 4.2")?
      Roughly how often? (affects whether pulling one entry is sufficient)
   c) Confluence/HTML pages - do they use real heading tags (h1/h2/h3), or is
      everything styled divs? Report per page.
   d) Boilerplate - how much of a typical document is front matter, legal
      notices, revision history, glossary? Roughly what % is substantive?

OUTPUT: write the findings to DOC_STRUCTURE_SURVEY.md as a markdown report
with one section per numbered item. Use real counts, real filenames and real
verbatim excerpts throughout - no illustrative or invented examples. If you
could not reach the real corpus and only had fixtures, say so prominently at
the top, because it changes how much the result can be trusted.
```

### Why the prompt is shaped this way

- **Demands the real corpus, and demands you say if you didn't get it.** The bundled fixtures are two
  Mastercard PDFs chosen to be tractable — measuring them would confirm the design against its own happy
  path. The code survey's value came entirely from hitting the *real* repo.
- **Three-way classification, not a yes/no.** WELL / LOOSE / FLAT matters because the mitigation differs:
  well-structured needs nothing, loose needs normalisation, flat needs synthesised boundaries.
- **Item 3 is the sleeper.** Structure can exist yet be useless — a document with five top-level sections
  over 40 pages is technically "structured" and gives 8-page index entries, which retrieve nothing
  useful. Entry *size* decides whether the structure is worth keying on.
- **Item 4 tests our own code, not the documents.** The index depends on `pdf_extract`'s output. If
  extraction flattens hierarchy, source structure is irrelevant — and this is the one failure mode we
  could fix ourselves rather than design around.
- **5a and 5d affect summary quality.** A table-dominated or boilerplate-heavy document summarises badly;
  the condensed summaries are what the agent reads to choose entries.

---

## What to do with the result

1. Read `DOC_STRUCTURE_SURVEY.md`.
2. Update **D-A18** with real numbers, replacing the assumption with a measurement.
3. **If structure coverage is high and entry sizes are reasonable** → D-A18 stands; item 4 is closed on
   evidence and Phase D can build it as specified.
4. **If FLAT dominates** → the synthesised-boundary path becomes primary rather than the exception.
   Re-open the item-4 option space, including the embeddings question — which on a VDI is a procurement
   conversation, not an engineering one, and therefore much better discovered now than mid-build.
5. **If extraction fidelity is poor** → fix `pdf_extract` first. That is our code, and no amount of
   document structure survives a lossy extractor.

---

## Also outstanding — three follow-ups on the code arm

Cheap additions to `SURVEY-stratus-repo.md`'s scan, none of which block Phase B:

```
6. GRAPH ISOLATION - for each file, count local includes OUT (files it
   includes) and IN (files that include it). Report how many have BOTH counts
   at zero, and list them. NOTE: "56.5% use local includes" is NOT this
   number - a header that includes nothing is still connected by everything
   including it, since edges run both ways.

7. SYMBOL PRESENCE - how many files export no functions/symbols at all
   (nothing tree-sitter would emit as an interface)? List them.

8. THE INTERSECTION - how many files are simultaneously: (a) no
   purpose-labelled field, (b) no usable prose in any leading comment,
   (c) degree zero in both directions, (d) no exported symbols. This is the
   unanalyzable count. List with a one-line reason each.
```

**Item 6 is the one that could still change the design** — degree-zero files become singleton modules,
and if that population is large, tier-1 economy fails (997 entries against a ~200 target in the D-A21
worked example). Items 7–8 size the declared coverage gap and are expected to be small.
