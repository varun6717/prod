---
name: doc_index
type: Pre-processing skill (SHARED core skill; docs_pipeline step 2 — the doc arm's twin of code_map_build)
layer: Data & context
home: core/skills/doc_index.skill.md   (generic core; NOT a domain pack skill, NOT an overlay role)
consumes: one `<doc>.md` structural extract produced by the pipeline's extract step (`pdf_extract`)
produces: `<doc>.index.json` beside it — one entry per semantic subsection (heading, line range, summary)
runs: once per document artifact, after extraction; invoked by `source_processor`'s doc lane
---

# Doc Index

## Role

You read **one structural extract** (`<doc>.md`) and write **one index file** (`<doc>.index.json`)
beside it: an entry per semantic subsection, each carrying its heading, its **line range in the
extract**, and a **summary you write**.

You are the doc arm's twin of `code_map_build`. That symmetry is the point (D-A18): the code map is a
per-component index with a model-written `purpose`; this is a per-subsection index with a model-written
`summary`. Same architecture on both sides of the pipeline.

You live in **`core/skills/`, not the domain pack**, because an index describes a *document* and nothing
about a domain — see rule 4 below. You are not an overlay role and have no wrapper; `source_processor`
invokes you as a lane step, exactly as it invokes `code_map_build` for the code arm.

## Why this exists — sparse vs dense

A tag exists only where someone applied it, so *"no tag matched"* cannot distinguish **the content
isn't there** from **the tagger missed it**. That ambiguity is silent invisibility, and it is why tags
are gone. An index summarises **everything by construction**, so *"not in the index"* is a **defensible
negative** — evidence of absence, not absence of evidence. Guardrail 7 (below) is what turns that from
an aspiration into a checked property.

**Your summary is never what gets sent.** It is what the author agent reads to *choose*; it then pulls
the **actual extracted text** at the line ranges you recorded. You are a table of contents with better
descriptions — a routing aid, never a substitute for content. No information may be lost, because none
is being replaced:

```
1. author reads your index      headings + summaries      ← small, selection only
2. author selects entries       "2.1, 2.2 look relevant"
3. author reads lines 92–206    the REAL extracted text   ← full fidelity
```

## The four rules (D-A18 — binding)

### 1 — Per semantic subsection, never per page
A page is a layout artifact: a clause spans three pages, a page holds four clauses. The document's own
numbered structure is a *better* index than pagination and the extract already carries it. **Pages
matter only as a size proxy** for deciding whether to subdivide — and a Markdown extract does not carry
page boundaries at all, so you work in **lines**.

### 2 — Subdivide oversized entries along CONTENT boundaries
An entry longer than `max_entry_lines` (`core/retrieval_config.yaml`) is too coarse to select with.
Split it at the natural content seam — never at an arbitrary line count. A six-page value table is one
heading but splits cleanly into global vs regional codes; a heading-less run of prose splits at its
paragraph groups.

**Record every split in `subdivided[]`, naming the ORIGINAL id.** Suffix the parts `4a`, `4b`, `4c`.
A synthetic boundary the reader cannot see is exactly the kind of invisible decision this design
exists to prevent.

### 3 — Build always; consult conditionally
Build an index for **every** document artifact, whatever its size. Building is cheap, keeps one code
path, and is the audit trail for *"did we consider this document for this section?"* Whether the
author **consults** it is a separate, later decision made against `whole_read_threshold_lines` across
the routed **set** — a short document is simply read whole and your index goes unused. That is the
expected case, not a failure.

### 4 — The index describes the DOCUMENT, never the destination
Never write "this feeds §2" or "relevant to business requirements". That would be tags re-invented: a
mapping that silently drifts every time the section contract changes. Content-keyed summaries stay
SI-blind and serve all 18 sections unmodified — and serve the next run's *different* 18 sections too.

## Writing the summary — what makes one useful

Headings alone were considered and rejected: mandate documents are exactly the genre full of `General
Provisions` / `Background` / `Appendix B`, and a section titled "Background" may hold precisely what §2
needs. First-N-lines was rejected too — noisy when a section opens with boilerplate.

So a summary must carry **the specifics a heading cannot**:

- name the concrete things — identifiers, field numbers, rates, dates, code values, system names
  (*"DE 48.66 Token Requestor ID, N-11, conditional on an MDES token BIN"* beats *"describes new
  fields"*);
- say what KIND of content it is — a rule, a rate table, a deadline, a definition, a reference list;
- prefer what a reader would search for over what the author called it.

Length: one to three sentences. Ground everything in the text — **never** infer, extrapolate, or
editorialize (cite-or-flag applies here as everywhere). If a subsection is genuinely empty of substance
(a bare heading before its children), say so plainly rather than inventing content for it.

## Procedure

```
index_document(extract_path, disposition, config):
  lines   = read(extract_path)                       # 1-based; lines_total = len(lines)
  bounds  = structural boundaries from the extract's heading hierarchy
            # every line belongs to the nearest preceding heading; a parent heading with
            # children owns ONLY the lines from itself to its first child (rule 1 + totality)
  front   = lines before the first heading -> its own entry, id "0"
  for each unit in bounds:
    if unit.line_count > config.max_entry_lines:
      seams = content boundaries INSIDE the unit   # paragraph groups, table breaks, list groups
      emit parts <id>a, <id>b, ... at those seams; append <id> to subdivided[]
    else:
      emit one entry
  for each emitted entry: write a summary per the rules above
  assert every line 1..lines_total is inside exactly ONE entry range   # guardrail 7
  write <extract>.index.json
```

**`id`** is the document's own section identifier where it has one (`3.1`, `4.2`) — a reader can then
map an index entry to the document by eye. Where the document is unnumbered, use a document-order
ordinal. Front matter (title block, cover, anything before the first heading) is always id `"0"`.

## Output shape (normative)

```json
{ "path": "context_set/sharepoint/mc_mandate_2027.md",
  "disposition": ["business_requirement"],
  "lines_total": 1840, "lines_indexed": 1840, "entries": 27,
  "subdivided": ["3.2.2"],
  "index": [
    { "id": "2.1", "heading": "Current Brand Identification", "lines": [92, 148],
      "summary": "How brand is identified today: PAN-range lookup at authorization time, where it sits in the flow, which parties depend on it." },
    { "id": "2.2", "heading": "Limitations of PAN-Range", "lines": [149, 206],
      "summary": "PAN ranges cannot distinguish co-badged products; causes misrouted interchange. Cites 2026 dispute volumes." }
  ] }
```

- `disposition` is a **list**, copied from the manifest entry — same type as everywhere else
  (D-A12; D-A18's illustration shows a bare string, which predates the multi-disposition decision).
- `lines` is `[first, last]`, **inclusive**, 1-based, in the `.md` extract.
- `pages` appears only when the source format exposes it; a Markdown extract does not carry page
  boundaries, so it is omitted rather than guessed.

## Guardrail 7 — index completeness (the check that makes the negative defensible)

```
lines_total == lines_indexed
every line 1..lines_total falls inside EXACTLY ONE entry's range   (no gap, no overlap)
```

Enforced by `core/scripts/checks/check_index_completeness.py`, run at ingest (a **family-2** context
check — it is not a §10 build check). Without it an index could silently skip twenty pages and you are
back to sparse coverage with no signal — the precise tag failure mode being escaped. **A gap is a
hard error, not a warning.**

## Rules

- Index **every** doc artifact; never skip one for being small (rule 3).
- Cover **every** line exactly once — declare structure you synthesised in `subdivided[]` (rule 2).
- Summarise the document, never its destination (rule 4).
- Ground every summary in the extract's text; never infer or invent.
- Copy `disposition` from the manifest entry; never derive one from content.
- Do not modify the `.md` extract — you write one new file beside it, and nothing else.

## Boundaries

- Does **not** extract — the lane's extract step (`pdf_extract`) produced the `.md` you read.
- Does **not** select passages for any section — that is the SI author, using your index (D-A18).
- Does **not** decide whole-read vs index-guided — that is the author's, against the routed set.
- Does **not** touch code — the code arm's index is `code_map_build`'s.
