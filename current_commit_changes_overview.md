# current_commit_changes_overview.md — what changed, for the VDI merge

**Who this is for.** The agent taking this change into the VDI-side working copy. It states exactly
what to run, exactly which files land, and what to check afterwards.

**How this file works.** Truncated and rewritten every commit, never appended. It always describes
one change set — the one you are about to take.

**Scope of this edition.** **TASK-130 + TASK-131 together** — the FPI → mnemonic enrichment pass,
and the `reference_table` disposition it now depends on. Take them as **one** transfer; TASK-131
changes how the TASK-130 skill finds its input, so taking only one leaves the pass looking for a
disposition that does not exist.

---

## HOW TO TAKE IT — one cherry-pick, from a prepared branch

The VDI has diverged (local commits not upstream, e.g. the SharePoint `.md` staging path). **Do not
`git pull` or `git merge`** — that would drag in every unrelated commit since your merge-base.

A branch has been prepared containing **only** this change, squashed into one commit:

```bash
git fetch origin
git cherry-pick origin/task130-squashed

# regenerate the derived mirror from your own merged source
python3 core/scripts/publish_registry.py --stage registry_repo --force

# rebuild the SPA — dist/ is gitignored and never travels
cd app/frontend && npm run build && cd -
```

**On conflict** — most likely the two `start-enrich` prompts, where a step was inserted and the rest
renumbered. **This change is additive everywhere: keep both sides.** Take the incoming step 3,
re-apply your local edits around it, then `git cherry-pick --continue`.

---

## THE ONLY FILES THAT LAND

Use this to confirm the result — `git show --stat HEAD -- . ':(exclude)registry_repo'`

```
NEW ────────────────────────────────────────────────────────────────────────
  core/profiles/payment_brand/fpi_mnemonic_enrich.skill.md    the enrichment pass
  fixtures/enrichment/verify_fpi_enrich.py                    its proof (21 checks)

MODIFIED ───────────────────────────────────────────────────────────────────
  core/scripts/dispositions.py                     + reference_table, + NEVER_ROUTED
  core/scripts/apply_enrichment.py                 provenance_note prefix ONLY
  core/profiles/payment_brand/si_profile.payment_brand.yaml   comment only (routing note)
  overlays/claude/prompts/start-enrich.md          new step 3 + renumber
  overlays/copilot/.github/prompts/start-enrich.prompt.md     same, for §10.2 parity
  app/frontend/src/PDLCConfigurator.jsx            one dropdown entry
  docs/TECH_SPEC.md                                §3.1 enum + normative banner
  docs/REQUIREMENTS.md                             D-A12 list

REGENERATE — never merge ───────────────────────────────────────────────────
  registry_repo/**          publish_registry.py --stage registry_repo --force
  app/frontend/dist/**      npm run build   (gitignored — does not travel)
```

**Nothing else.** No connector, no `adapter.yaml`, no `overlay_manifest.yaml`, no backend, no
`jira_*`, and none of the five `[TBD — VDI]` placeholders. A larger diff means something went
wrong — stop and report it.

---

## WHAT YOU ARE GETTING

**1. A new enrichment pass: FPI → mnemonic.** The network writes in **FPIs**; our systems key on
**interchange level code/name**, which boarding calls a **mnemonic** (`VACD`). Nothing downstream
can act until those resolve — and **no existing pass could do it**, because mnemonic configuration
lives in PeopleSoft rather than `repo/`. Arm 1 has no code to find; Arm 2 has nothing to verify.
**This is the only pass that can surface boarding-system work.**

It runs at `/start-enrich` as **step 3** — after both arms, **before** the walkthrough. It reads the
reference table **in full** (never through its index: this is a lookup, and a row never looked at is
indistinguishable from one that does not exist), and **stages findings; it edits nothing.**

**2. A seventh disposition: `reference_table`.** A *lookup*, not evidence. It is **`NEVER_ROUTED`**,
so **v1 never reads it** — a mapping resolved from a lookup table is a *tool-resolved* fact, and
those belong in v2 via enrichment. It also keeps a 1000-row table out of §9.2's whole-read budget,
and it lets the pass find its input by set membership instead of guessing which
`technical_specification` source is the table and which is the Tech Letter that names codes in prose.

**3. Honest provenance.** `provenance_note` no longer labels everything `[code: …]`. Evidence under
`context_set/` now cites **`[ref: …]`**; repo paths are unchanged. It was hardcoded, so a fact
resolved from a document would have claimed code provenance it never had, inside an **accepted**
artifact.

---

## HOW TO USE IT ON A RUN

**Keep your SharePoint `.md` staging path exactly as it is** — the pass is connector-agnostic and
needs no change to it.

1. **Author the table as Markdown.** Headings every **~15–20 rows** (`max_entry_lines: 25`), grouped
   by a real column. **One table row = one line** — never wrap a row, or the `L45–52` citation stops
   meaning "these 8 levels". Put a line at the top: **a blank FPI means "no observed volume", not
   "not applicable"**.
2. **Add it in the UI** under Artifact Inventory, via your SharePoint `.md` path.
3. **Set disposition → `Reference Table`.** ← the new dropdown entry, and the step that matters.
   Not `Technical Specification` — that is the Tech Letter's class, and the pass would then find two
   candidates and refuse to guess.
4. **Generate.** `UI_INPUT.yaml` is immutable: a source not configured now cannot be added later.
5. `/start-ingest` → `/start-si` → `/start-enrich`. The pass fires automatically.

**What you should see:** §16 of v2 carrying resolved mnemonics grouped by requirement, each citing
the table by path **and line range**; Jira stories flagged **`non_code`** (PeopleSoft config has no
`code_location`, and inventing one is what that flag exists to make unnecessary); and findings for
the **misses** too — an FPI absent from the table, levels in the affected family the letter never
named. Silence on those is the one outcome you cannot act on.

---

## TWO ORDERING FACTS THAT ARE LOAD-BEARING

Do not reorder the enrichment steps:

**The pass runs BEFORE the walkthrough** — escalations must join the single operator turn (D-A17),
not require a second one.

**Its findings must reach §16 BEFORE G2** — `jira_plan` builds stories from §16, so a mnemonic
arriving after v2 is accepted is identified and then **never planned**. Moving this later silently
drops all boarding-system work from the Jira plan.

Related: the first implementation emitted §8 corrections and the apply pass dropped them —
`CORRECTABLE` excludes §8, because code cannot contradict an intent (D-A4).

---

## AFTER MERGING

```bash
for f in $(find fixtures -name "verify_*.py"); do python3 "$f" || echo "RED: $f"; done
python3 core/scripts/build_checks.py
```

Expect **§10 4/4**, and your verify count up by one (`verify_fpi_enrich.py`).

If `verify_fpi_enrich.py` fails on the prompt-ordering checks, the conflict resolution dropped or
misplaced step 3 — **fix the prompts, not the fixture.**

**A `core/` change means a re-publish is owed.** Do not patch generic code locally to make something
pass: if the gap is in the generic build rather than the VDI wiring, report it for an upstream fix.

---

## STANDING REMINDERS

- **`origin` must be `github.com/varun6717/prod.git`.** `code_640011` is the **registry**.
- **Kickoff after Generate is `/start-ingest`** → `/start-si` → `/start-enrich` → `/start-jira`.
  The retired `start-brd` / `start-frd` names still appear in `docs/TECH_SPEC.md`,
  `docs/REQUIREMENTS.md` and `docs/COPILOT_VDI_VALIDATION.md`; those docs are stale, the overlays on
  disk are correct.
- **Your SharePoint `.md` staging path is not in this repo** — the next hydrate overwrites it. Send
  the diff so it can be landed generically with a fixture.
