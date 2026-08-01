# ACCEPTANCE_SI.md — Solution Intent spine, end-to-end acceptance (TASK-127)

**Run:** `r-2026-08-01-si1` · **domain:** `payment_brand` · **runtime_tool:** `claude`
**Slice:** the full ADR-008 spine — Data & context → SI v1 → enrichment → v2 → 4-level Jira plan
→ (stub) push. **Result: PASS**, with nine integration breaks found and fixed en route.

Successor to `ACCEPTANCE.md`, which logged the pre-ADR-008 BRD→FRD spine and is kept unchanged as
a historical record.

> **What this run proves, and what it does not.** It proves the *pipeline* works end to end on a
> real operator path. It does **not** claim the resulting Solution Intent is business-correct: the
> corpus is fixture data, and the operator ruled at GF that the frame/source brand mismatch is an
> artifact of that. The VDI run will use real sources.

---

## The path

| Stage | Gate | Outcome |
|---|---|---|
| Configure + Generate (React UI → FastAPI) | **G0** | scaffold at `registry_sha`, 83 core files, 8 agents, 4 prompts |
| `start-ingest` — 6 sources | — | 5 extracts, 5 indexes, code map, `context_set/index.json` |
| `start-si` — v1 authored **code-blind** | **GF** ×2, **G1** | score **98/85**, 7/7 preconditions; accept **froze** v1 |
| `start-enrich` — Arms 1+2, walkthrough, apply | **G2** | score **100/85**, 3/3 preconditions; v2 written |
| `start-jira` — 4-level plan | **G3** | score **100/85**; acceptance authorised the push |
| Push (stub target) | — | 37 issues, parent-before-child, no secret on disk |

**Every gate was an operator act.** No validator advanced the run.

## Artifacts

`runs/r-2026-08-01-si1/` — `UI_INPUT.yaml` · `context_set/` (5 extracts + 5 `*.index.json` +
`code_map/{components,files}.json` + `index.json`) · `repo/` · `solution_intent/{v1.md,
v1.frozen.json, enrichment.json, v2.md}` · `jira_plan.json` · `jira_trace.json` ·
`ledger/{telemetry.jsonl, decisions.jsonl, run_state.json}`.

## Acceptance conditions

| Condition | Evidence |
|---|---|
| Operator completes the run through UI + tool | G0 via `POST /generate`; every stage driven from the scaffold |
| Every gate is an operator act | G0/GF×2/G1/walkthrough×6/G2/G3 — all recorded in `decisions.jsonl` |
| v1 + `enrichment.json` reconstruct v2 | re-applied deterministically; byte-identical |
| v1 frozen and unedited | `sha256 ee448028…`, mode `r--r--r--`, write raises `PermissionError` |
| Trace chain `D→R→§16→story→key` intact | 5 D · 9 R · 22 §16 entries · 22 stories · 37 keys; **0 orphan epics** |
| Checks green | §10 4/4 · guardrail 7 on all 5 indexes · map totality 35 files/16 modules · ledger valid |
| Metrics derive | full amended set, below |
| Registry re-published + re-hydrated | `feature/pdlc_app` @ `0db09dd9`, 121 files; re-Generate serves the new pipeline |

## Metrics (`metrics_scan.py` over this run's ledger)

M01 $/SI-v1 **1.24** · M02 $/enrichment **2.21** · M03 avg score at acceptance **99.3** ·
M04 first-pass **1.0** · M06 v1→v2 **3000s** · M07 p95 **2.7e6 ms** · M09 coverage at push
**100.0** · M10 stories/epic **2.44** · M11 push success **1.0** ·
**M12 enrichment yield 21** (1 correction · 19 derived impacts · 1 auto-fill).

M12 is the stage's value in one number: 21 things v2 knows that v1 did not.

## What enrichment actually found

All three D-A16 authority rows fired, which is the design working rather than a coincidence:

- **auto-correct** — v1 §2 said brand identification is a PAN/BIN-range lookup, sourced from the
  routing KB. The code has no such lookup: `txn_t` carries `pan_token[24]` ("tokenized PAN, never
  the real number") and `route_transaction()` receives `t->brand` already resolved. Source-derived,
  so corrected in place with code provenance.
- **escalate** — the operator had dispositioned `iso8583.c` as the live path at the onboarding
  gate. `build_iso8583()` defines `set_bit()` and **never calls it**, so it emits no bitmap;
  `build_iso8583_v2()` does. DE 48 subelements need one. Because this contradicted a *human*, it
  escalated rather than auto-applying — and the operator accepted the correction.
- **auto-fill** — §13 A4 asked which DE 48 subelements the parser builds today. Answer: none, and
  it has no concept of them (`iso_msg_t` is a flat `char *fields[128]`). Neither the mandate nor
  the KB says this; only the code does.

## Nine integration breaks, found and fixed

Every one was invisible to the per-subsystem fixtures. Each now has a regression test.

| # | Break | Why no fixture caught it |
|---|---|---|
| 1 | `hydrate.py` retried `--unshallow` on a bad SHA | git ignores `--depth` on local clones, so the error blamed shallowness for a bad `registry_sha` |
| 2 | Retired `code_map.json` in both overlays + `source_processor` | the doc sweep covered `docs/` only |
| 3 | **16 overlay files still described BRD/FRD** — `start-si` told the operator to author a BRD; `start-enrich` pointed at a skill file that does not exist | §10.2 parity asks whether a file *exists* per role, never whether its contents describe the pipeline that exists |
| 4 | `ingest_sharepoint` refused >1 PDF | its two sibling connectors had been generalised; it had not |
| 5 | `clone.py` failed into **every** fresh scaffold | the fixture cloned into a temp path that does not exist — the one arrangement a real run never has |
| 6 | `validate_onboarding` had no argparse and was hardcoded to the fixture | an operator could not point the gate at their own repo |
| 7 | …and ignored the repo's **frozen** signal profile | it re-asked a question the operator had already frozen, and would have keyed the map cache against a profile governing nothing |
| 8 | `confluence_extract` named in §6.6.3, **never built** | a connector check ends at `staged_path` and cannot see that its output has nowhere to go |
| 9 | `jira_plan` required an **undocumented** §7 table | an SI authored exactly to spec yielded zero deliverables, orphaning all 9 epics — and v1 is frozen by then |

## Open questions settled here

- **`docs/` hydration** (raised 2026-07-31) — **no fix needed.** `docs/` is published but not
  hydrated, as the question anticipated. But nothing in a run workspace cites a `docs/` path: the
  skills carry their contracts inline. Adding `docs/` to `hydrate.py` would ship 5 design documents
  into every run and invite an agent to treat a stale copy as authoritative. `hydrate.py` unchanged.

## Post-acceptance defects (found by auditing this run, fixed 2026-08-02)

| Defect | Fix | Regression test |
|---|---|---|
| `registry_repo/` — the tracked, push-ready registry tree meant to travel to the VDI — was a **pre-ADR-008 snapshot** still holding `brd_author.skill.md` and `brd_validator.skill.md`, with no `confluence_extract`. The re-publish went to Bitbucket, not to this directory, and nothing compared them. | regenerated from the §10-gated subset (122 files) | `verify_registry` now asserts the snapshot holds exactly the published set and is **byte-identical** to source — it caught a drift within minutes of being written |
| Both family-2 checks **silently swallowed unknown flags**: argv is a bare path list, so a typo'd or renamed `--flag` matched nothing, was dropped, and the run still exited 0 — a passing check that had quietly narrowed what it scanned. `check_map_totality --help` additionally crashed with a traceback about a missing `components.json`. | unknown options now exit 2 with usage; the map check also validates that its argument *is* a map directory | exercised directly |
| 206 files of run workspace tracked in git — 137 of them verbatim copies of the registry (`core/`, the overlay wrappers, `prompts/`) plus a cloned `repo/` and an entire transient second run. | tracked down to the 35 files a run **cannot regenerate**: ledger, SI artifacts + freeze record, plan + trace, manifest, per-artifact indexes, code map | `.gitignore` |

*A fourth was reported and withdrawn: I claimed the checks passed vacuously on a nonexistent path. They do not — they exit 2 and 1 respectively. The original test piped through `tail`, so `$?` captured tail's exit code rather than the script's.*

## Follow-up work (2026-08-02)

Three items taken after acceptance, in the order of risk to the port.

**1. PDF→text is now a declared dependency** (`core/scripts/pdf_text.py`). It was the only known
thing that could stop the VDI run cold, and it was unverifiable beforehand because it rested on an
ambient agent capability. Now: `pypdf` when importable, else a pure-stdlib reader, with the branch
recorded in `ENV_PRECHECK.md` alongside the C-extractor entry it mirrors. `--which` answers it at
port time. The limitation below is closed.

**2. The index's structure is derived, not authored** (`core/scripts/doc_index.py`, amending
D-A18). An entry is `{id, heading, lines, summary}`; the first three are facts about the extract.
The split follows from asymmetry of error — **a wrong line range is invisible**, a wrong summary is
caught on first read — so the unfalsifiable field was the one being guessed. Guardrail 7 now holds
by construction. Two bugs surfaced while building it, both from real extracts: the document title
took ordinal id `1` and collided with a `## 1.` heading claiming its own number, and subdivision
preferred the nearest blank line, which split a dense table into a 1-line part and a still-oversized
remainder. *(Raised by V on the Jira lane; it generalises to every extract.)*

**3. The refusal paths are now driven through the spine**
(`fixtures/spine_refusals/verify_refusals.py`). The acceptance run took the happy path at every
gate, and nine breaks surfaced on that path alone. This drives G1's refusal (and proves v1 stays
**unfrozen** — a refused gate that froze anyway would leave a document nobody accepted), the
reopen→fix→accept cycle, G2 refusing while the walkthrough is unfinished, a rejected finding
staying in the record without reaching v2, G3's authorization being unmintable for a broken plan,
and a partial push resuming rather than duplicating.

It found two more gaps:

| Gap | Fix |
|---|---|
| `enrichment.disposition` **silently discarded** a `target` passed with `reject`, while `decisions.disposition` raises on the same input. Two writers disagreeing about one operator act — and the quiet one is what the apply pass reads, so a caller could believe it had placed a finding that was actually dropped. | now raises, matching the audit twin |
| `push_plan` recorded each success as it returned, but on a mid-batch failure the partial trace **died with the stack frame** — so its own docstring's promise ("a retry resumes rather than re-creating") was true of a local variable and of nothing a caller could reach. Every caller had to track successes independently. | the exception now carries `partial_trace` and `pushed_before_failure`; additive, so existing handlers are unaffected |

## Post-review correction of the accepted artifacts (2026-08-02)

The full-repo review (`code_review.md`) found its top defect **in this run's accepted artifacts**:
`apply_to_v2` selected §16 entries by *kind* regardless of `section_target`, and reroute placement
was unimplemented — so the operator's reroute of **F-331/F-361 to §14** was silently overridden.
Both sat in the accepted v2's §16, both generated build stories (S20/S21) in the pushed plan, and
§14 never received them: the plan carried two stories the operator had explicitly ruled out.

**Corrected on V's instruction ("fix all"), with an honest gate cycle rather than a quiet swap:**

- `v2.md` regenerated deterministically from the same frozen v1 + `enrichment.json` — §16 now has
  **20** entries, F-331/F-361 appear in **§14** under *"Added during enrichment
  (operator-rerouted)"*, and §18's counts are drawn from what was actually applied (3 corrections,
  not the route-based 1).
- **G2 reopen → accept (version 3)** and **G3 reopen → accept (version 2)** recorded in the ledger
  — the artifact changed, so the acceptances were re-earned, not carried over. The new
  `record_g2` freeze-verification ran as part of the accept.
- The plan rebuilt: **20 stories** (S20/S21 gone); `evaluate_g3`'s `dispositioned_without_story`
  allowance now does real work, since the rerouted entries genuinely yield no story.
- `jira_trace.json` regenerated from a fresh stub push (35 issues). The prior push hit a stub
  target, so no external system ever held the old keys — regenerating is honest here; on a real
  Jira it would instead have meant closing two pushed issues, which is exactly why the defect
  class matters.
- The push ran under the new **plan-bound authorization** (`plan_sha256` + `run_id` verified).

## Known limitations

- ~~No deterministic PDF→text step.~~ **Closed** — see follow-up 1.
- **`ingest_jira._flatten` renders list fields as blank-line-separated paragraphs** rather than
  bullets. Totality holds and nothing is lost, but it inflates the line count the index selects in.
- **Gate acts were performed by the operator in-conversation**, not through a UI affordance; the
  "unaided operator" claim is therefore not independently attested by this run.
