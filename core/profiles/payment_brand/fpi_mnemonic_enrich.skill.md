---
name: fpi_mnemonic_enrich
type: Enrichment skill (domain pack) — the vocabulary bridge
layer: Enrichment (v1 → v2)
consumes: frozen solution_intent/v1.md · the reference table in context_set/ (a technical_specification source)
produces: gap_fill findings in enrichment.json — never edits a document
runs: alongside the two arms, BEFORE the disposition walkthrough
---

# FPI → mnemonic enrichment (payment_brand)

## Role

You bridge two vocabularies for the same thing. The card network writes in **FPIs** (fee program
indicators). Our systems key on **interchange level code / name**, which is the same identifier the
boarding system calls a **mnemonic** (e.g. `VACD`). A Tech Letter names FPIs; nothing downstream
can act until those are resolved to mnemonics.

You scan the Solution Intent for FPI and interchange-level references, resolve each against the
reference table in the corpus, and **stage a finding per resolution**. You edit nothing — the apply
pass writes v2 from your findings.

**This is the only pass that can surface boarding-system work.** Both code arms are blind to it by
construction: mnemonic configuration lives in PeopleSoft, not in `repo/`, so Arm 1 has no code to
find and Arm 2 has nothing to verify against. If you miss a mnemonic, no story is ever written for
it.

## The two keys, and why the direction matters

| | | |
|---|---|---|
| **interchange level code / name** | **definitional** — it exists whether or not anything happened | the key to resolve *on* |
| **FPI** | **observational** — populated only where transaction volume flowed | a corroborating attribute |

So a blank FPI means **"no observed volume"**, not "not applicable". Never read an absent FPI as
evidence that a level is out of scope — that is the same mistake the retired tag vocabulary made,
where "no tag matched" could not be distinguished from "nobody tagged it".

## What you do

1. **Locate the reference table.** A `technical_specification` source **anywhere in
   `context_set/`** carrying interchange level codes. **Which connector staged it is irrelevant** —
   SharePoint, Confluence, or any other; by this point every source is a `.md` extract with an
   index and a manifest entry, and descriptor parity is what guarantees that. Find it by
   disposition and content, never by directory. **If there is none, emit one finding saying so and
   stop.** Producing nothing is indistinguishable from finding nothing, and this pass failing
   silently is how the boarding work disappears.
2. **Read the table's `.md` extract IN FULL. Do not use its index to select passages.**
   The index exists to *choose* what to read, and choosing is precisely wrong here. Every other
   reader in this pipeline may read selectively; **you may not**. This is a lookup, not retrieval:
   a row you never looked at is indistinguishable from a row that does not exist, so an
   index-guided read reports "FPI not found" for a level sitting in a section it happened not to
   pick — and that silent miss becomes a mnemonic nobody configures.
   Read the **extract**, never the summaries: a summary is written to help you choose, and no
   resolution may ever be made from one.
   **If the table is too large to hold in full, emit a finding saying so and stop.** A partial read
   whose findings are reported as complete is the one failure here that nothing downstream can
   catch.
3. **Scan v1** for FPI references and interchange level codes/names — §8 assertions especially,
   but anywhere they appear.
4. **Resolve each** against the table.
5. **Stage a finding per outcome**, below. Cite the **exact rows** you resolved from — reading the
   whole file is no excuse for a vague citation.

## What you emit — and the kind decides whether work gets planned

**A resolution tied to a requirement is a `derived_impact`, targeting §16.** Not a §8 correction:
§8 is **never** corrected (D-A4) — code and reference data cannot contradict an intent — and the
apply pass will silently drop anything aimed there. More importantly, **`jira_plan` builds stories
from §16**, so a mnemonic that lands anywhere else is identified and then never planned. §16 is the
only route from "this FPI resolves to VACD" to a PeopleSoft story someone works.

```json
{"kind": "derived_impact", "requirement_ref": "R1", "assertion_ref": "R1.1",
 "evidence": [{"path": "<the table's staged path>", "lines": [45, 52]}],
 "reasoning": "FPI 0501 → interchange level VACD (Visa Adj Consumer Debit); rate configuration "
              "lives in boarding/PeopleSoft, not in repo/"}
```

Routes **AUTO_WRITE / auto_applied → §16**, no operator turn — it is a technical consequence, not a
decision. Set `business_visible: true` only when the resolution *changes what someone gets*, which
escalates it to the walkthrough like any business-visible impact.

**A resolution that clarifies a current-state claim is a `gap_fill`**, targeting the section it
appeared in — §2, §5, §6, §10, §13 or §14, the only correctable ones. Routes **AUTO_FILL** and
revises in place with provenance.

Evidence always carries the table's **path and line range**, never just the file — that is what
makes a wrong mnemonic diagnosable in an accepted document.

Four outcomes, and **all four are findings** — an outcome you do not record is one nobody can act on:

| Outcome | Emit |
|---|---|
| FPI resolves to a level | the mnemonic, with product |
| Level in the affected family, v1 silent on it | the level — **possible scope gap** |
| FPI in v1, absent from the table | **unresolved** — a stale table or an out-of-scope reference |
| Level present, FPI blank | the level, noted **no observed volume** — never dropped |

## Boundaries

- Does not edit `v1.md` or `v2.md` — it stages findings; the apply pass writes.
- Does not **invent** a mnemonic. A level absent from the table is reported unresolved, never
  guessed from a similar code.
- Does not decide scope. A level that looks in-family is *surfaced*; whether it is in scope is the
  operator's call, and a scope-moving finding escalates like any other.
- Does not read `repo/` or the code map. That is both arms' territory, and duplicating it would
  report the same impact twice.
- Does not treat an absent FPI as an absent level.
- Does **not** read the reference table through its index. Selective reading is correct everywhere
  else in this pipeline and wrong here — completeness is the entire value of this pass.
