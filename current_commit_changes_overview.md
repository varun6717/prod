# current_commit_changes_overview.md — what changed, for the VDI merge

**Who this is for.** The agent (Copilot or Claude) merging this push into the VDI-side working
copy. It states what moved, what is newly strict, what will conflict, and what to regenerate
rather than merge.

**How this file works.** It is **truncated and rewritten on every commit**, never appended, and it
ships **in the same commit as the code it describes** (`TASK_LIST.md` protocol step 6). So it
always describes exactly one change set: the one you are about to merge.

**Scope of this edition.** Baseline `4f38156` → this commit (three commits: `708e29f`, `f293173`, and this one). **Trust the baseline SHA, not the
filename.** If your merge-base is older than `4f38156`, run `git log --oneline <your-base>..HEAD`.

---

## This change set

Wording in one skill, plus the integration guide below. **No code, no fixtures, no spec, no overlays.**

| File | Change |
|---|---|
| `core/profiles/payment_brand/fpi_mnemonic_enrich.skill.md` | Two wording changes: the lookup is **connector-agnostic**, and the table is read **in full, never through its index**. |

**Why it mattered enough to change.** The skill's example evidence path read
`context_set/confluence/interchange_levels.md`. This is a **model-executed instruction file**, so
an illustrative path can be read as a constraint — a model could go looking only under
`context_set/confluence/` and miss a table staged by SharePoint. The step now says: find it by
**disposition and content, never by directory**, and names descriptor parity as the reason
connector choice is irrelevant. The example path is a placeholder rather than a real directory.

**And the table is now read whole, never through its index.** The index exists to *choose* what to
read, and choosing is wrong for a lookup: a row never looked at is indistinguishable from a row that
does not exist, so an index-guided read would report "FPI not found" for a level sitting in a
section it happened not to pick — a silent miss that becomes a mnemonic nobody configures. If the
table is too large to hold, the skill must say so and stop rather than report a partial read as
complete.

**Practical effect for the VDI:** a reference table staged through the **SharePoint** `.md` path
works with no change to the skill, the prompts, or the pipeline. Configure it as a SharePoint
source with disposition **`technical_specification`** and the enrichment pass will find it.

---

## Behaviour that is newly STRICTER

None.

---

## Signature / contract changes

None.

---

## Conflict hot spots

None — the changed file is new as of the previous commit, so the VDI cannot have local edits in it
unless they were made after that merge.

**Still untouched:** the five `[TBD — VDI]` placeholders, every connector, `adapter.yaml`, the
overlays, the SI profile.

---

## HOW TO USE THIS ON THE VDI — the interchange reference table

**Keep your existing SharePoint `.md` mechanism exactly as it is. Change nothing about it.** The
new skill was written to be connector-agnostic precisely so it works with whatever staged the file.
There is no new input, no new source type, and no new UI field.

**Wiring it up, end to end:**

1. **Author the table as Markdown.** Headings every **~15–20 rows** (`max_entry_lines: 25`), grouped
   by a real column — product, card type, fee category. One table row = **one line**; never wrap a
   row. Put a line at the top saying a **blank FPI means "no observed volume", not "not
   applicable"** — the skill and the SI author both read that and will otherwise misread the gaps.
2. **Stage it via your SharePoint `.md` path** and add it in the UI under **Artifact Inventory** as
   a SharePoint source.
3. **Set the disposition to `technical_specification`.** ← *the one step that is easy to miss.*
   It is not the row's default. This disposition routes it to **§8 as primary**, so the SI author
   sees it too; left as `product_domain_knowledge` it routes elsewhere, and as `other` it routes
   nowhere and can never be cited.
4. **Generate.** `UI_INPUT.yaml` is **immutable** — a source not configured now cannot be added
   later; that would be a new `run_id`. If the table is missing at Generate, the enrichment pass
   will correctly report "no reference table in the corpus" and stop.
5. **`/start-ingest`** — nothing special; it stages, indexes, and lands a manifest entry like any
   other source.
6. **`/start-si`** — v1 may already cite the table (it is primary for §8).
7. **`/start-enrich`** — the pass runs automatically as **step 3**, before the walkthrough. It
   finds the table **by disposition and content, not by directory**, reads it **in full** (not via
   its index — this is a lookup, and a row never looked at is indistinguishable from one that does
   not exist), and stages findings.

**What you should see afterwards:**

- **§16 of v2** carries the resolved mnemonics, grouped under their requirement, each citing the
  table by **path and line range** (`[ref: …/interchange_levels.md L45–52]`).
- **The Jira plan** contains a story per mnemonic-driven change, flagged **`non_code`** — because
  PeopleSoft configuration has no `code_location` to name, and inventing a path is exactly what
  that flag exists to make unnecessary.
- **Findings for the misses too** — an FPI in the SI that is absent from the table, and levels in
  the affected family the letter never mentioned. Silence on those is the one outcome you cannot
  act on.

**Two contracts to confirm about your `.md` path**, because neither fails loudly:

1. **Descriptor parity.** It must emit the same descriptor shape as every other connector, or
   downstream breaks in places that will not point back at the connector.
2. **The staged file is byte-identical to the source.** Bypassing extraction is the *point*. If
   anything re-wraps a table row, one row stops being one line and the `L45–52` citation quietly
   stops meaning "these 8 levels."

**And that mechanism is not in this repo**, so the next hydrate overwrites it. Send the diff and it
gets landed generically, with a fixture asserting a staged `.md` reaches `doc_index` unmodified —
exactly the kind of invariant that stops being true without anyone noticing.

---

## Derived artifacts — regenerate, never merge

| Path | Do this |
|---|---|
| `registry_repo/**` | `python3 core/scripts/publish_registry.py --stage registry_repo --force` |
| `app/frontend/dist/**` | **Gitignored — never travels.** `cd app/frontend && npm run build` |
| `fixtures/jira_plan/plan_pass.json` | Regenerated by `verify_jira_plan.py` |

---

## After merging, run the green bar

```bash
for f in $(find fixtures -name "verify_*.py"); do python3 "$f" || echo "RED: $f"; done
python3 core/scripts/build_checks.py
```

Expected: **31 verifies green, §10 4/4.** A `core/` file changed, so a re-publish is owed (registry
stays at 127 files).

---

## Standing reminders

- **`origin` must be `github.com/varun6717/prod.git`.** `code_640011` is the **registry**.
- **Kickoff after Generate is `/start-ingest`** → `/start-si` → `/start-enrich` → `/start-jira`.
  The retired `start-brd` / `start-frd` names still appear in `docs/TECH_SPEC.md`,
  `docs/REQUIREMENTS.md` and `docs/COPILOT_VDI_VALIDATION.md`; those docs are stale, the overlays
  on disk are correct.
- **A gap in the generic code is fixed in the build repo and re-published** — not patched on the VDI.
