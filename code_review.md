# code_review.md — full-repo review, 2026-08-02

**Scope:** `core/scripts/` (all 26 modules), `core/adapters/jpmc_adapters/`, `core/extractors/`,
`app/backend/`, with the acceptance run's artifacts (`runs/r-2026-08-01-si1/`) used as ground truth
to verify findings rather than argue them. Every finding below was **reproduced against the code or
the run artifacts before being recorded**; nothing here is speculative. Checked-and-clean areas are
listed at the end so their absence from the findings reads as verified, not skipped.

Findings are ranked. **#1 is real, present in the accepted artifacts of the acceptance run, and
should be fixed before the VDI port.**

---

## HIGH

### 1. A `reroute` disposition is silently overridden — the operator's ruling did not hold

`apply_enrichment.apply_to_v2` step 2 selects §16 entries with:

```python
if f.get("section_target") == "§16" or f["kind"] in ("derived_impact", "no_code_found"):
```

The second clause ignores `section_target` entirely. A `no_code_found` finding the operator
**rerouted to §14** still matches on kind and lands in §16 — and reroute-to-§14 is otherwise
**unimplemented**: step 1 only appends correction notes to `CORRECTABLE` sections for
`auto_correct`/`auto_fill`/accepted-contradiction findings, so nothing ever writes a rerouted
finding into its target section.

**Verified consequence in the accepted run:** F-331 and F-361 were rerouted to §14 at the
walkthrough with the rationale *"certification tooling … belongs in Dependencies, **not the build
plan**"*. Both appear in v2's **§16** (lines 500, 503), both generated **build stories** (S20, S21)
in the pushed `jira_plan.json` — the precise outcome the ruling forbade — and §14 never received
them (its MTS/Testing-API lines are v1's original text). The document even prints the reroute
rationale *inside §16*, directly above the entry it failed to govern, so the accepted v2 visibly
contradicts itself. G3 still scored 100 because every §16 entry yielded a story, which made the
`dispositioned_without_story` allowance passed to `evaluate_g3` vacuous.

This defeats the walkthrough's core guarantee (the operator decides where a finding lands) on the
only disposition that moves one. **Fix:** in step 2, exclude findings whose `section_target` is set
and is not `"§16"`; implement placement into the reroute target (an *"Added during enrichment"*
append, as §17 already does for `defer`); regenerate the run's v2/plan or annotate
`ACCEPTANCE_SI.md`. Add a refusal-fixture case: reroute → target section receives it, §16 does not,
no story is created.

### 2. `G3Authorization` is not bound to the plan it authorized

`authorize()` checks eligibility and mints `{run_id, actor, score, ts}` — nothing ties the token to
the **plan content** that was evaluated. `push_plan` never compares `authorization.run_id` to
`plan["run_id"]`, and there is no plan digest, so:

- evaluate G3 on plan A → mint token → push a **modified** plan B: accepted silently;
- a token minted for run X authorizes a push of run Y.

The same reasoning that froze v1 ("if the artifact can change after acceptance, the gate stops
meaning anything") applies to the plan at G3, where the action is the run's only external mutation.
Related: `push_plan` resolves `parent_key` via `out.get(parent_local, {}).get("key")` — a parent
absent from both trace and plan yields `parent_key=None` and a **silently orphaned** issue; today
that is prevented only by the (unbound) gate. **Fix:** carry `plan_sha256` (and enforce `run_id`)
in `G3Authorization`; `push_plan` recomputes and refuses on mismatch; raise instead of `None` for a
missing parent.

### 3. The freeze digest is never checked on the live path

`verify_frozen()` — "the real guard" per `freeze_v1`'s own docstring — has **no production caller**
(only the module demo uses it). The enrichment stage does not verify v1 against
`v1.frozen.json` before running the arms; neither does G2 nor the plan build. `apply_to_v2` checks
the *record's* `v1_sha256` against whatever v1 text the caller passes — a different guard: it
proves record↔text consistency, not text↔frozen-record. A caller holding a tampered v1 plus a
record recomputed against it passes every live check. **Fix:** call `verify_frozen(si_dir)` at the
start of enrichment and inside `record_g2`; one line each.

---

## MEDIUM

### 4. `reject` does not trigger `supersede_dependents`

`supersede_dependents`' docstring names its canonical case — "a `reject` on a no-code gap" — but
`enrichment.disposition(call="reject")` never calls it; the only caller is a fixture. If the
walkthrough skill forgets, findings resting on a withdrawn premise stay `applied`/`undispositioned`
and reach v2. The invariant lives in a function nothing invokes — the same shape as #3.

### 5. §18's counts under-report what enrichment changed

Accepted run: §18 says **"1 corrected · 1 auto-filled"** while the document carries **3**
`Corrected during enrichment` notes. The counts are route-based (`route == "auto_correct"`), so an
accepted escalated contradiction (F-320) and an auto-fill placed as an in-place note (F-301) are
invisible to §18. §16's count (22) also includes the two rerouted entries from #1. A stakeholder
reading the verification summary under-counts the v1→v2 delta — §18's entire purpose. **Fix:**
derive the counts from the applied report, not the routes.

### 6. `Not applicable` anywhere in a section body marks it N/A

`parse_v1` runs `_NA.search(body)` over the whole section. Ordinary prose containing
"Not applicable — …" (e.g. *"Prepaid is Not applicable — see Part 2"*) silently flags the section
`is_na`, which **excludes its coverage from `section_coverage`** (score inflation) and changes H2
semantics. Anchor the marker (line-start, or require it as the section's sole content).

### 7. `parse_v1` section spans break on quoted headings

Section bodies are located with `text.index(f"## {sid}. ")` and headings with an unfenced
`^## (\d+)\. ` multiline match. A fenced code block quoting a section heading (plausible in a
technical SI) produces duplicate section ids and mis-spanned bodies with no error. Low likelihood,
high confusion when it hits; fence-aware parsing or duplicate-id detection would make it loud.

### 8. `push_epics` inverts the module's own safe default

`push_plan` documents `dry_run=True` as "the safe direction: a caller who forgets the argument
previews". The §7.1-pinned compatibility surface `push_epics` defaults **`dry_run=False`** — a
forgetful caller on that surface attempts a real push. The `PermissionError` backstop prevents a
write, so this is an inconsistency rather than a hole, but the advertised property does not hold on
one of the two public surfaces. If §7.1 pins the default, note it there; if it pins only the
signature shape, flip it.

### 9. G2 `verdict_completeness` mixes deduplicated and raw counts

The numerator set dedupes verdicted findings by `assertion_ref`/`section_ref`, while unverdicted
findings are counted **per finding** in the denominator. Two verdicted findings on one section
count once; two unverdicted ones count twice. Direction of error is conservative (score can only be
dragged down), but the ratio is not the fraction it claims to be.

---

## LOW

- **`push_plan` `ts` defaults to `""`** — a forgotten `ts` records empty `pushed_ts` in the trace
  rather than failing or defaulting to now.
- **`pdf_text` page numbering equates one content stream with one page** — multi-stream pages (or
  streams spanning pages) mislabel `@@PAGE` markers. Text order is unaffected.
- **`doc_index.verify()` does not check part sizes** — a letter-suffixed subdivision part can
  exceed `max_entry_lines` in pathological seam layouts and no check objects (the fixture's
  over-limit assertion filters to non-letter ids). Probing the dense-table case showed correct
  behaviour; this is about the absent guard, not an observed failure.
- **`ledger.py` validator: `pattern` uses `re.search`** — correct per JSON-Schema, noted because
  authors often assume anchoring; schema patterns here are explicitly `^…$`-anchored, so fine.

---

## Verified clean (checked, no finding)

- **Auth seam** (`auth.py`): fail-loud on missing/unknown secrets, redaction on every
  stringification surface, lazy resolution (dry run needs no secret), backend swap point — all as
  documented; canary-leak fixtures corroborate.
- **Gate refusal wiring**: G1/G2 accept refused when ineligible, reopen always allowed, refused G1
  leaves v1 unfrozen and writable — proven by `verify_refusals` end to end.
- **Ledger schema validator**: type/enum/oneOf/if-then-else subset correct, including the
  bool-is-not-int guard.
- **`doc_index` partition**: guardrail 7 by construction held under adversarial probes (dense
  section with no usable seam falls back to even mid-paragraph cuts; no gaps/overlaps).
- **`clone.py` / `hydrate.py` / `ingest_sharepoint.py`** TASK-127 fixes: correct, and their
  regression fixtures genuinely exercise the failure shapes.
- **Backend validation** (`app/backend/validation.py`): field-path-naming 422s, per-type source
  requirements, disposition list rules — consistent with §3.1 and `dispositions.py`.

## Method note

Findings #1 and #5 were confirmed by reading the accepted run's `v2.md` and `jira_plan.json`;
#3 and #4 by caller search; #2 by API-shape analysis of `authorize`/`push_plan`; #6–#9 by reading
the parsing/scoring paths against the profile contract. The review deliberately re-used the
acceptance run as a test oracle: the highest-severity finding (#1) is invisible to every fixture
because the fixtures' operators never chose `reroute` — the same isolation blind spot that let the
nine TASK-127 integration breaks survive their unit fixtures.
