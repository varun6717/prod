# ADR-003 — Agent-assisted domain vocabulary: onboarding proposal + every-run adequacy check (propose, never bless)

> ⛔ **Superseded by ADR-008 (2026-07-31).** The vocabulary — and with it tagging, containment
> (§10.1), the adequacy detector (§5.4.1), and `vocab_sha` — is **deleted** (D-A19/D-A22). The
> propose-never-bless governance pattern this ADR established lives on in the D-A21 onboarding
> gate actions. Kept for history; do not build against it.

**Status:** **Accepted** — ruled by operator **V**, 2026-06-20 (option **A**: forward-compat hook now + L1 deterministic detector in-slice + L2 deferred to port + L3 Phase 5).
**Amends:** `REQUIREMENTS.md` (new `FR-DC-20` W / `FR-DC-21` S; a forward-compat **note** on D5); `TECH_SPEC.md` §3.6 (`vocab_gap_flag` record), §5.2 (`onboarding_manifest` gains `built_with_vocab_sha` + `adequacy_threshold`), §5.3 (`vocab_sha` added to the cache key), §5.4.1 (the L1 adequacy detector — `uncovered_concepts` aggregation + `untagged_ratio` floor, normative), §5.5 (`model_enrich` returns `uncovered_concepts`; purpose/tags separability), §10 (adequacy is a **runtime flag**, not a build gate); `TASK_LIST.md` (TASK-011 emission, TASK-012/013 hook + L1; Phase 5 gains L2/L3); `code_map_build.skill.md`.
**Does not reopen:** D1–D10. D5's **12 tags stay frozen**; a vocabulary *amendment* is a human-gated **addition**, never a silent redefinition. Architectural invariants intact: deterministic/frozen extractor, model-free 3-branch gate, model owns `purpose`+`tags` only, deterministic `merge_edges`, and the §10.1/§10.5 **containment** check is unchanged. This ADR adds a complementary *adequacy* check; it does not weaken containment.
**Sibling of:** `FR-DC-19` (`extractor_onboard`). Same governance shape — an agent **proposes** a frozen artifact, a human **freezes/commits**; the skill must never self-bless. This ADR is that pattern applied to the **vocabulary** instead of the extractor.

---

## Context

The domain tag vocabulary (D5) is the contract three things route on: adapter `emits`, `code_map` `tags`, and BRD/FRD profile `topics`. It is **per-domain and frozen**, authored once and SHA-pinned.

Today exactly **one direction** of vocabulary checking exists:

- **Containment (§10.1/§10.5, TASK-046)** — *usage ⊆ dictionary.* Every topic/emit/tag must already be in the vocabulary. This catches **invention/drift** (a tag escaping the dictionary) and is a **build-time hard gate**.

The **other direction does not exist**:

- **Adequacy** — *does the dictionary cover the concepts actually present in the artifacts?* This catches the vocabulary being **too small** for the real corpus.

Two forces make the dictionary outgrow itself, and **neither shows up in this external build** because the synthetic fixtures were authored to fit the 12 tags:

1. **A much larger real codebase** (the VDI Stratus repo) contains modules whose concepts the 12 tags do not name.
2. **A new PDF/article** introduces a concept no existing tag covers.

In both cases the model **cannot invent a tag** (`assert tags ⊆ vocabulary` forbids it), so the affected file/doc comes out `tags: []`. That is *honest* but **silent**: an untagged file is found by no section's selective read, and nothing fails. The gap is invisible until someone notices a requirement that should have had code behind it didn't. We want that silent gap turned into a **visible, trending, human-actionable signal** — and we want it designed **before the port**, since the port is where the gap first becomes real.

A second, related need: a **new (second) domain** has no D5 decision at all — its vocabulary must be authored from scratch. An agent that has read the domain's sample artifacts can **propose** that first vocabulary far faster than a blank-file start.

## Decision

Add **two human-gated, agent-assisted capabilities**, sharing one principle — **propose, never bless.**

### 1. `domain_onboard` — propose a vocabulary for a *new* domain (FR-DC-20, W)

At new-domain onboarding, before any run, a deferred skill proposes `vocabulary.<domain>.yaml` from:

- the **untagged code_map** of a sample repo — structure (`path/module/interfaces/depends_on`) **plus `purpose`**, but **not** `tags` (circular);
- **sample documents** for the domain;
- the operator's **domain framing**.

Output is a **reviewable proposal** — for each candidate tag `{name, definition, emitted_by, code_tag?, evidence:[files/docs]}` — that a **human edits, approves, and freezes**. It never commits the file.

This requires one mechanical refinement to enrichment: **split `model_enrich` into a purpose-first pass and a tags-last pass.** `purpose` is vocabulary-independent and may be computed before the vocabulary exists (it feeds the proposal); `tags` stays last, consuming the frozen result. In a normal run the two run back-to-back exactly as today — the split only matters during onboarding.

### 2. Every-run vocabulary **adequacy** check + amendment loop (FR-DC-21, W)

This is the vocabulary twin of the coverage floor: it raises a **human-gated** flag, never auto-grows the dictionary. The detection rests on **leftover meaning**, not an empty-tag count — see "the partial-coverage problem" below for why.

```
on each run (reusing the gate's existing new/changed signal — §5.3 commit_sha/git_diff; doc source-idempotency):

  # ---- PRIMARY signal — leftover meaning, emitted by the tagging pass itself (§5.5) ----
  # model_enrich(file) → purpose, tags, uncovered_concepts[]   # concepts present but with NO vocab tag;
  #   emitted in the SAME pass that assigns tags (the model already read the file), and INDEPENDENT of how
  #   many tags the file got. Routes to the ledger, NOT the code_map (it has no tag → routes nothing).
  recurring = uncovered_concepts that recur across the NET-NEW delta files   # deterministic aggregate
  for c in recurring:
      raise VOCAB_GAP_FLAG(concept=c, evidence=files_naming(c))   # names the missing concept + evidence

  # ---- FLOOR — deterministic, model-free safety net ----
  untagged_ratio(code) = files with tags:[]       / total files       # CODE arm
  untagged_ratio(docs) = manifest entries no-topic / total entries    # DOC  arm
  emit both to telemetry every run                                    # continuous trend, never blind
  if untagged_ratio(code) > T or untagged_ratio(docs) > T:            # T = adequacy_threshold (default 0.20)
      raise VOCAB_GAP_FLAG(arm=…, ratio=…)   # systematic gap, even if the model's emission was absent

  # ---- human-gated amendment (deferred L2 — see timing split) ----
  human reviews the proposal → if accepted:
      add tag(s) to vocabulary.<domain>.yaml      # an ADDITION; D5 set never silently redefined
      bump vocab_sha (versioned)
      re-tag pass: only the TAG pass re-runs (structure/purpose untouched); a vocab_sha change
                   invalidates affected code_maps via the gate cache key, exactly as a re-blessed
                   extractor_sha does (§5.3 Branch B guard).
```

**The partial-coverage problem — why leftover meaning, not an empty count.** A vocabulary gap takes two shapes: a file whose *only* concept has no tag (`tags: []` — "fully uncovered"), and a file that got its *primary* tag but a *secondary* concept has no tag (`tags: [routing]` while `tokenization` goes un-nameable — "partially uncovered"). A plain `untagged_ratio` over empty-tag files catches the first and **silently misses the second** — the partially-uncovered file is non-empty, so it counts as "tagged." The fix is to detect the *cause* (a concept with no tag) rather than the *symptom* (zero tags): `model_enrich` reports `uncovered_concepts[]` as a byproduct of the pass it already runs, which is independent of the tag count and so catches **both** shapes. The deterministic `untagged_ratio` is kept underneath as a model-free floor (it still fires on a systematic fully-uncovered gap even if the model emission is missing) and as the cheap always-on trend line. This supersedes the earlier "two-thresholds" framing: one cause-level signal + one deterministic floor, not two ratio thresholds.

## The invariant — why the human gate is structural, not ceremony

The same model that **assigns** tags at runtime (and routes sections on them) is the one that would **propose** new tags. If it could also silently **add** the tags it wished it had, the vocabulary stops being an external contract and `assert tags ⊆ vocabulary` becomes the model grading its own homework — it could never be "wrong." The human-freeze gate is the **only** thing that keeps the dictionary an independent contract. Hence: agent **proposes**, human **disposes**, build checks **enforce** — identical to FR-DC-19's freeze discipline.

And the two checks stay distinct in *kind*:

| Check | Direction | Enforcement | Failure mode it catches |
|---|---|---|---|
| **Containment** (exists, §10.1/§10.5) | usage ⊆ dictionary | **build-time hard gate** | a tag *escaping* the dictionary (drift/invention) |
| **Adequacy** (this ADR) | corpus → dictionary | **runtime flag** (never hard-fails a run) | the dictionary being *too small* — a concept with no tag, whether the file is fully (`tags:[]`) or partially (`tags:[routing]` + leftover) uncovered |

Adequacy must **not** become a hard gate — a run with some untagged files is valid and proceeds; the flag is advisory input to a human, recorded in `decisions.jsonl`.

## Rationale

1. **The gap is otherwise silent.** Without adequacy, an undersized vocabulary degrades to `tags:[]` that no section finds and no check fails. This converts that into a trending, actionable signal.
2. **Reuses existing machinery — no new change detection.** Code uses the gate's `commit_sha`/`git_diff_names`; docs use per-source idempotency (D8b). The only additions are a **count** (`untagged_ratio`) and a **gated, delta-scoped model pass**.
3. **It parallels `REONBOARD_FLAG` exactly.** Deterministic trigger (coverage floor / untagged ratio) → human-gated frozen-artifact change (onboard an extractor / amend the vocabulary). The system already accepts this shape for the extractor; this applies it to the dictionary.
4. **Determinism + freeze intact.** The ratio is model-free; the model only *proposes*; the human *freezes*; the extractor and the gate are untouched.
5. **Forward-compat hook reserved now, like FR-DC-13 reserved `external_calls`/`exposes`.** Adding `vocab_sha` to the onboarding manifest + gate cache key **now** (cheap) means a future amendment invalidates affected maps without a key reshape later. Naming the loop now keeps it additive.
6. **Sibling governance to FR-DC-19.** One coherent "propose-not-bless onboarding" story for both frozen artifacts (extractor, vocabulary).

## Consequences

### Already-built work (TASK-008/009/010/011): **no Python change to the committed code.**
- `apply_enrichment` is **unchanged** — it still writes **only** `purpose`+`tags` onto the map entry (the guard stays intact). `uncovered_concepts` is a model output that does **not** land on the entry, so the setter does not touch it.
- The **enrichment *contract*** (documented in `code_map_build.skill.md`, a TASK-011 artifact) gains one output: `model_enrich` now returns `purpose, tags, uncovered_concepts`. This is a prose/contract refinement to the model step (the model already reads the file; naming leftover meaning is a byproduct), not a change to the deterministic Python guard.
- `load_domain_vocabulary` already **abstracts the source** of the set; producer (proposal) and consumer (`apply_enrichment`/`assert_tags_in_vocabulary`) are cleanly separated, so the proposal capability is purely additive.
- The `merge_edges` closure and the C extractor are untouched.
- **Only future, optional touch:** `load_domain_vocabulary` may later also return a `vocab_sha` (a one-line addition) once versioning lands. Not needed until the amendment loop is built.

### The timing split ruled by V (option A)

**Hook — now (TASK-012/013, forward-compat plumbing, behavior-free).** Reserve `built_with_vocab_sha` in `onboarding_manifest.yaml` (TASK-012) and add it to the gate's Branch-B cache key (TASK-013), constant for the single frozen domain — exactly the `external_calls`/`exposes` reservation pattern (FR-DC-13). A future vocabulary amendment then invalidates affected maps (→ re-tag) without a later key reshape.

**L1 detector — in this slice (TASK-011 emission + TASK-013 aggregation/flag).** The adequacy detector is the twin of the coverage floor (`REONBOARD_FLAG`), which is already MVP — so it belongs with the gate. Two pieces:
- **Emission (TASK-011 contract):** `model_enrich` reports `uncovered_concepts[]` per file in the same tagging pass. This is what lets L1 catch the **partial-coverage** case (a non-empty file with leftover meaning) that a plain empty-count misses.
- **Aggregation + flag (TASK-013):** a small **deterministic** helper (e.g. `core/scripts/checks/vocab_adequacy.py`), invoked from the gate's post-build path beside `check_coverage`, aggregates `uncovered_concepts` across the net-new delta (recurring concept → `VOCAB_GAP_FLAG(concept, evidence)`) and computes the model-free `untagged_ratio` floor against `adequacy_threshold`. It does **not** block the run.

Testable now: on `fixtures/c_repo` the floor reads ≈0.06 and `uncovered_concepts` ≈ ∅ → **no flag** (no false positives); a **crafted fixture** carrying an out-of-vocabulary concept (a `tokenization` file, and a partial-coverage variant where the file *also* carries `routing`) → `uncovered_concepts` populates and the flag fires → the same proof shape as `assert_tags_in_vocabulary`. The model-judgment *quality* (catching every real gap, phrasing good proposals) is only provable on a real corpus → that's the L2/port half.

**L2 model proposal + amendment loop — deferred to the port (Phase 5 / port-time).** `vocab_gap_assess` (a bounded model step that turns the recurring `uncovered_concepts` into a well-formed candidate tag — name/definition/`emitted_by`/`code_tag?`/evidence), the human-gated `vocab_sha` amendment, and the re-tag pass that re-applies the refined vocabulary to affected files. The model-judgment half cannot be meaningfully validated against synthetic fixtures authored to fit the 12 tags; its first real exercise is the VDI corpus. Named now, built at the port. (Note the L1/L2 line: L1 *detects and names* the leftover concept deterministically from `uncovered_concepts`; L2 is the model *phrasing it as a tag proposal* + the human amendment — so a single new concept is never silently lost in-slice, even though the proposal/amendment is deferred.)

**L3 `domain_onboard` — Phase 5 (named not built).** `core/skills/domain_onboard.skill.md` — propose a *new* domain's vocabulary from the untagged map + sample docs. Cannot be exercised until domain #2 exists (`payment_brand`'s vocabulary is frozen by D5). Mirrors how FR-DC-19's `extractor_onboard` is named-not-built.

### Spec/ledger touch-points (on Accept)
- **§3.4 / §8.1:** an adequacy telemetry event (`untagged_ratio` for code + docs), so the trend is observable; no metric hand-entered.
- **§3.6:** a `vocab_gap_flag` decision record (two shapes — a named recurring `concept`+`evidence` from `uncovered_concepts`, or the `untagged_ratio`/`threshold` floor — plus who/when/decision), alongside `reonboard_flag`.
- **§5.4.1:** the L1 detector (the `uncovered_concepts` aggregation + the `untagged_ratio` floor) named beside the coverage floor; `adequacy_threshold` lives in §5.2.
- **§5.5:** `model_enrich` returns a third value `uncovered_concepts[]` (the adequacy byproduct, routed to the ledger not the map); plus the purpose-first/tags-last separability note.
- **§10:** state that adequacy is a **runtime flag**, not a build gate; containment stays the build gate.
- **`vocabulary.<domain>.yaml`:** gains an additive `vocab_sha`/version header.
- **REQUIREMENTS.md:** `FR-DC-20`/`FR-DC-21` (Watcher) in the deferred area near FR-DC-19; a forward-compat **note** on D5 that the frozen set may be **extended** via this human-gated loop (the existing 12 are not changed).

### Scope discipline
- `payment_brand` is unaffected operationally: its vocabulary was frozen by D5, so a real run exercises only the *application* path; on `fixtures/c_repo` the adequacy detector reads low (≈0.06) and raises nothing. The **L1 detector ships in-slice** (it is the coverage-floor twin and is testable here); the **L2 diagnosis/amendment loop** earns its cost at the **first real (VDI) corpus**; **L3 `domain_onboard`** earns its cost at the **second domain**. Pulling L1 in is a small, deliberate, operator-ruled expansion of the MVP "single domain" note — justified because the detector is the exact model-free analog of a signal the MVP already builds (the coverage floor), and because the gap it catches first appears at the port.
