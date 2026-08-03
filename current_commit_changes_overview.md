# current_commit_changes_overview.md — what changed, for the VDI merge

**Who this is for.** The agent (Copilot or Claude) merging this push into the VDI-side working
copy. It states what moved, what is newly strict, what will conflict, and what to regenerate
rather than merge.

**Scope of this edition.** Baseline `33c7de0` → head `ae89929`. Six commits, 25 files
(excluding the `registry_repo/` mirror). **Regenerated each push — trust the baseline SHA above,
not the filename.** If your working copy's merge-base is not `33c7de0`, this file describes more
or less than your actual diff; run `git log --oneline <your-base>..HEAD` to see the truth.

---

## ⚠️ Read this before you pull — the remote topology changed

This is the single highest-risk item in the push, and it is not a code change.

| | before | now |
|---|---|---|
| **build repo** (this repo) | `github.com/varun6717/code_640011` | **`github.com/varun6717/prod`** |
| **registry** (hydration source) | Bitbucket / other | **`github.com/varun6717/code_640011`** |

`code_640011` now holds **only the published registry subset** — 126 files, `core/` + `overlays/`
+ `docs/` at the root. It has no `app/`, no `fixtures/`, no `TASK_LIST.md`, no `runs/`.

**So if your VDI clone still has `origin = code_640011` and you `git pull`, you will not get this
work — you will get the registry, and the merge will read as a mass deletion of the build repo.**

Fix before pulling:

```bash
git remote set-url origin https://github.com/varun6717/prod.git
git fetch origin && git log --oneline HEAD..origin/main
```

Do **not** add the registry as a remote of the build repo. It is written only by
`publish_registry.py`; a stray `git push` at it would overwrite the registry with the full repo.

---

## Commits, oldest first

| SHA | What and why |
|---|---|
| `246d42f` | **TASK-128** — doc review of `PROGRAM_OVERVIEW`/`BUILD_OVERVIEW` against disk. Six doc fixes + one stale skill frontmatter (`code_impact_assess`: "per epic" → "per requirement"). |
| `598c18d` | **Registry re-point** (the table above) + the live publish instructions in `CLAUDE.md`, `BOOTSTRAP.md`, protocol step 5. |
| `1bf3333` | **`generate.py` refuses an unknown domain**; UI help text drops the retired tag vocabulary. |
| `f17437a` | Two dead references in the locked `UI_INPUT.example.yaml` (comments only). |
| `8edcd4f` | **`publish_registry` now refreshes `registry_repo/` on a successful push** — staged and pushed can no longer diverge. |
| `ae89929` | **TASK-129** — `UI_INPUT.jira` implemented + `level`/`parent_link` ladder amendment (§3.1, §3.8). |

---

## What changed, by area

| Area | Files | Note |
|---|---|---|
| **Jira plan/push** | `jira_plan.py` `jira_validator.py` `jpmc_adapters/jira.py` | TASK-129. See "signature changes" below. |
| **Config + validation** | `app/backend/validation.py` `app/frontend/src/{emit.js,PDLCConfigurator.jsx}` | New `jira:` block + a new **Jira Creation** tab (now tab 4; Generator moved 4 → 5). |
| **Scaffold** | `generate.py` `hydrate.py` | Domain-pack fail-fast. |
| **Publish** | `publish_registry.py` | Snapshot coupling. |
| **Spec** | `docs/TECH_SPEC.md` | §3.1 + §3.8 amendments, both carrying port notes. |
| **Docs** | `docs/PROGRAM_OVERVIEW.md` `docs/BUILD_OVERVIEW.md` `CLAUDE.md` `BOOTSTRAP.md` `TASK_LIST.md` | Doc review + publish instructions. |
| **Skills** | `core/skills/code_impact_assess.skill.md` | One frontmatter word. |
| **Fixtures** | 6 `verify_*.py` + `sample_form.json` + `UI_INPUT.example.yaml` | +32 checks total. |

---

## Behaviour that is newly STRICTER — things that now fail and did not before

Expect these to surface as *new* failures on VDI configs that previously passed. Each is intended.

1. **`generate.py` refuses a domain with no pack.** Raises `ValueError` naming the domain, the
   missing artifact, and the domains the registry does publish. Previously it produced a
   complete-looking G0 scaffold that failed much later, at SI authoring.
2. **`validation.py` validates the `jira:` block.** The block stays **optional** (an L1-only run
   is still valid), but when present it must be complete: `project_key` + all three controls, and
   `parent_link` **required** when `level != initiative`, **forbidden** when it is. A partial
   `jira:` block that was previously ignored is now a **422 naming the field**.
3. **`publish_registry.py` writes `registry_repo/` on every successful push.** A publish now dirties
   the working tree if the snapshot was stale. Expected — commit it, or stage first.

---

## Signature / contract changes

```python
# core/scripts/jira_plan.py
build_plan(..., level: str = "initiative", parent_link: str | None = None)
    # defaults reproduce the previous whole-tree behaviour byte-for-byte
_project_to_level(plan, level, parent_link)   # NEW — runs last, owns plan["push_root"]

# core/scripts/jira_validator.py
evaluate_g3(...)   # now reads plan["push_root"].parent_link and plan["trace"].deliverables

# core/adapters/jpmc_adapters/jira.py
push_plan(...)     # seeds plan["push_root"].parent_link into the trace as action="external"

# core/scripts/hydrate.py
hydrate(...)       # descriptor gains "domains_available" (pre-pruning; reported, never enforced)

# app/backend/validation.py
_validate_jira(jira) -> list[str]   # NEW
```

`jira_plan.json` gains `push_root: {level, parent_link}` (§3.8). `UI_INPUT.yaml` gains
`jira.level` and `jira.parent_link` (§3.1). Both amendments carry port notes for the JPMC-side
spec — **apply those at port time; they are not applied for you.**

---

## Conflict hot spots for a VDI wiring session

- **`core/adapters/jpmc_adapters/jira.py` — same file you are wiring.** This push adds ~12 lines
  inside `push_plan`. Your VDI edits belong in `_create_issue` / `_update_issue`, which are
  **untouched here**, so a three-way merge should resolve cleanly. Verify both placeholder bodies
  survive the merge.
- **All connectors are UNCHANGED**, confirmed by diff: `ingest_jira.py`, `ingest_sharepoint.py`,
  `ingest_confluence.py`, `clone.py`, `auth.py`. If your merge shows changes in any of these, they
  are yours, not this push's — keep them.
- **`VDI_WIRING.md` is UNCHANGED.** Still 16 items. Any local ticks are yours; keep them.

---

## Derived artifacts — regenerate, never merge

Resolving these by hand produces a file that matches neither side.

| Path | Do this |
|---|---|
| `registry_repo/**` | Take either side, then `python3 core/scripts/publish_registry.py --stage registry_repo --force`. `verify_registry` fails if it drifts from source. |
| `app/frontend/dist/**` | **Gitignored — it does not travel.** The SPA changed, so run `cd app/frontend && npm run build` after merging, or the UI you load will lack the Jira Creation tab. |
| `fixtures/jira_plan/plan_pass.json` | Written by `verify_jira_plan.py` on each run. Take either side; it regenerates. |

---

## After merging, run the green bar

```bash
for f in $(find fixtures -name "verify_*.py"); do python3 "$f" || echo "RED: $f"; done
python3 core/scripts/build_checks.py
```

Expected: **30 verifies green, §10 4/4.** That was the state at `ae89929` before publish.

If anything is red, compare against the standing rule: a gap in the **generic** code is fixed in
the build repo and re-published — not patched on the VDI.

---

## What did NOT change

The five `[TBD — VDI]` placeholders and their contracts; the auth seam; every ingestion connector;
`adapter.yaml` and its lanes; the SI profile's routing matrix; the 18-section contract; the gate
ladder; `VDI_WIRING.md`.
