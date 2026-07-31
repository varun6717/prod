# ADR-005 — Agent-assisted adapter onboarding: a guided helper to design a domain's pre-processing pack (propose-never-bless)

> ⛔ **Superseded by ADR-008 (2026-07-31).** `adapter.yaml` loses `emits` and the tag lanes — the
> doc pipeline is domain-agnostic extract + index (D-A18/D-A19), so the emit-derivation idea has
> no target. Open-Q #1 (the `ONBOARD_INPUT` shape) stays valid for the re-scoped domain
> onboarding; open-Q #2 is answered by the per-artifact index (D-A18). Kept for history.

**Status:** **Accepted** — ruled by operator **V**, 2026-06-20. Deferred (W); named now, built in Phase 5 (port / second domain). No in-slice build, no pinned-contract change.
**Amends:** `REQUIREMENTS.md` (new `FR-DC-23` W, in the FR-DC cluster beside FR-DC-19/20/22); `TECH_SPEC.md` §6.6.3 (forward-compat note — the agent-assisted adapter aid respects build-time registration); `TASK_LIST.md` (Phase 5 named follow-on). No normative schema change — `adapter.yaml` (§6.6.3) already admits additional `docs_pipeline` skills additively; no reserved hook, no Python.

---

## Context

Every domain-seam artifact that varies per domain has a propose-not-bless onboarding aid — **except the adapter pack.** This is the same asymmetry ADR-004 found for profiles, one seam over:

| domain-seam artifact | onboarding aid | status |
|---|---|---|
| per-language extractor | `extractor_onboard` (FR-DC-19) | named, deferred |
| vocabulary | `domain_onboard` (FR-DC-20) | named, deferred |
| BRD/FRD profiles | `profile_onboard` (FR-DC-22, ADR-004) | named, deferred |
| **adapter pack** (`adapter.yaml` + pre-processing skills) | **— none —** | **manual** ("write one more pack", §11) |

The adapter pack is the **domain's pre-processing seam** (§6.6.3): the front-half *meaning* layer that turns ingested raw content into vocab-tagged `context_set/` slices. Authoring it for a new domain today is fully manual — and TASK-017 showed why that is costly and error-prone: hand-authoring `adapter.yaml` independently of the frozen vocabulary produced **four** per-tag emit-map drifts (F1 + three undocumented) that had to be found and reconciled by hand against `vocabulary.payment_brand.yaml`'s `emitted_by` column. A helper that *derived* the emit-map **from** the frozen vocabulary would have made that entire drift class structurally impossible.

Two facts make the adapter pack genuinely *design* work, not a template fill (and so a good fit for a guided helper rather than a pure generator):

1. **The skill set is not fixed.** `payment_brand`'s pack is `{pdf_extract, article_summarize, confluence_tag}` for *its* source types (the `default` lane extracts then tags; the `confluence` lane tags KB pages). A different domain may need **different or net-new skills authored ad hoc** (a structured-data normalizer, a thread/email summarizer, a specialized classifier). The vocabulary fixes the *tag set*, but the **partition of tags across skills is a design choice** that depends on the pipeline shape the operator wants.
2. **It is a process-flow conversation.** The real work is identifying, with the human, *how this domain's documents should be processed* — which steps, in what order, each responsible for which tags — and which of those steps are reusable vs net-new.

## Decision

Name a deferred, human-gated skill — working name **`adapter_onboard`** — that designs a domain's pre-processing pack by **proposing**, never deciding. It runs a **guided conversation** anchored on a **canonical exemplar** (the `payment_brand` pack is the first such reference), and:

1. **Shows the fixed frame.** It presents what every domain gets for free and never authors — the generic engine (`source_processor`, `brd_author`/`frd_author`, validators) and the fixed code path (`code_pipeline → code_map_build`, the shared core skill; code processing never varies by domain, D7). The conversation is scoped to the **variable part only**: the `docs_pipeline`.
2. **Proposes the `docs_pipeline` shape.** From the **frozen** vocabulary + profiles + the domain's sample sources, it proposes the ordered pre-processing steps, **reusing shared/structural skills** where they fit and **scaffolding net-new domain-specific skills** where they do not.
3. **Derives the emit-map.** Each step's `emits` is proposed **from the vocabulary's `emitted_by` column**, so `adapter.yaml` and the vocabulary cannot drift by construction (the §10.5 no-drift check becomes a confirmation, not a manual reconciliation). It checks coverage: every `required: true` profile topic must have a producing step (§6.6.3 (b)).
4. **Scaffolds the skill bodies.** For each docs_pipeline skill — existing-pattern and ad-hoc — it drafts the `*.skill.md` body (the discretionary, model-proposed half; the human owns the final behavior, as in TASK-018/019).
5. **Emits a reviewable diff.** The proposed `adapter.yaml` + scaffolded skill files land as a reviewable diff for a human to edit, approve, and commit.

The mechanical half (emit-map derivation from `emitted_by`, required-topic coverage, `code_pipeline` wiring) is near-deterministic; the discretionary half (the pipeline *shape*, which skills exist, and each skill's *behavior*) is the model **proposal** and the operator **decision**.

### Two modes — bulk (onboarding) and incremental (drift)

Same propose-not-bless engine, two invocation contexts (mirroring `profile_onboard`):

- **Bulk — at onboarding.** Immediately after `profile_onboard` freezes the profiles, `adapter_onboard` proposes the **complete first pack** — the whole `docs_pipeline`, every skill (reused + net-new), and the full emit-map — from the frozen vocabulary + profiles + sample sources. Refined conversationally and frozen **in one session**.
- **Incremental — at drift.** Later, when the FR-DC-21 amendment loop adds a tag, `adapter_onboard` wires that one tag to a producing step (or proposes a new step) — the emit-map counterpart to `profile_onboard`'s single-tag routing.

**Vocabulary-and-profiles-first is mandatory.** The emit-map is nothing but vocabulary tags assigned to skills, and coverage is defined against the profiles' `required` topics — so the pack can only be designed *from* an already-frozen vocabulary **and** profiles. `adapter_onboard` is therefore **last** in the onboarding chain:

```
extractor_onboard (if new language)
  →  domain_onboard      (vocabulary, FR-DC-20)
  →  profile_onboard     (BRD/FRD profiles, FR-DC-22)
  →  adapter_onboard     (pre-processing pack — THIS ADR; emit-map derived from the frozen vocab)
  →  human refine + freeze
```

## The invariant — why the human gate is structural, not ceremony

`adapter.yaml` and its pack skills are **build-time, SHA-pinned, human-frozen seam artifacts** (§6.6.1; registration is build-time, human-authored, build-checked, never invented by the agent at runtime). So `adapter_onboard` MUST NOT:

- **decide** the pipeline shape (it proposes; a human confirms/edits),
- **author the final** skill behavior (it scaffolds; a human owns the wording/logic),
- **author or modify a core skill** — it may *reference* shared core skills (route `code_pipeline → code_map_build`) and *author* domain **pack** skills, but never writes `core/skills/`,
- **mutate** a live pack (it emits a diff; the change lands as a committed, re-pinned, build-time amendment — never a runtime write).

The build checks remain the gate, whatever shape is designed: `emits ⊆ vocabulary` and every required topic produced (§10.5), every named skill file present (§10.3). The agent proposes; §10 verifies; the human freezes.

## Rationale

- **Completes the chain.** The extractor, vocabulary, and profiles each have a helper; the adapter — the front-half meaning layer where the real domain judgment lives — is the last seam left manual. This closes it.
- **Eliminates a proven defect class.** Deriving the emit-map from the frozen vocabulary makes the TASK-017 F1+3 drift structurally impossible, rather than something a human must catch against §10.5 each time.
- **Right tool for the work.** Because the skill set is not fixed and the value is in the process-flow conversation, a *guided* helper (propose + converse + scaffold) fits better than a silent generator — while the near-deterministic emit-map comes along as a checked byproduct.
- **Pattern-consistent & additive.** Reuses the propose-never-bless governance of FR-DC-19/20/22 and the surface→wait→apply loop (FR-BR-08). `adapter.yaml` already admits additional `docs_pipeline` skills additively, so naming it costs nothing and building it later is purely additive.
- **Promotes reuse.** Encodes the "reuse shared structural skills, author only the domain-specific ones" rule — and motivates promoting domain-agnostic skills (e.g. `pdf_extract`, which is structural/domain-blind) into `core/skills/` so future packs reference rather than re-author them.

## Consequences

- **No in-slice change.** Nothing is built; no committed code, no schema edit, no reserved field. `payment_brand`'s pack stays hand-authored (TASK-017/018/019).
- **First exercise** is alongside `domain_onboard`/`profile_onboard` — a new domain at the port, or the FR-DC-21 amendment loop.
- **Named dependency — structural extraction must be core, available before the pack exists.** The onboarding order has a bootstrapping constraint: to read the sample documents for vocabulary analysis, `domain_onboard` needs **structural** extraction (`pdf_extract`) — but it cannot run the *tagging* skills (`article_summarize`/`confluence_tag`), which tag against a vocabulary that does not yet exist (circular). Therefore the structural step (`pdf_extract`, domain-agnostic) must live in `core/skills/` and be available **before** the domain's adapter pack is authored; the *tagging* skills are authored **last**, by `adapter_onboard`, once the vocabulary is frozen. This promotes "move `pdf_extract` to core" from a nice-to-have to a **prerequisite** of the onboarding sequence. (Mechanically separate change; this ADR records the dependency.)
- **Scope discipline.** Records a design decision (a `W`-level FR) and reserves a name; does not reopen D1–D10, change a pinned schema, or pull work into the slice. It is the adapter-side sibling of ADR-004 (profiles) and ADR-003 (vocabulary).

## Operating model — run vs. refine (so the lifecycle is unambiguous)

Once a domain is onboarded and its pack frozen:

- **Per change → RUN, do not refine.** Each change is a new run (`UI_INPUT` is immutable; re-configuring is a new run, §3.1) that *applies* the frozen adapter. Code is incremental — the map-build gate keys on the repo `commit_sha`: unchanged → reuse the cached `code_map`, changed → rebuild only the diffed files (FR-DC-15/§5.3). Documents are **re-ingested per run as configured** — MVP has **no** cross-run document delta/sync (Out-of-scope, REQUIREMENTS.md: "change detection & downstream flagging; sync/freshness; automated non-human-mediated re-runs").
- **Refine only on DRIFT, human-gated.** The adapter/vocab/profiles change only when a run surfaces a concept the vocabulary cannot tag (`VOCAB_GAP_FLAG`, advisory — never blocks the run). A human approves; the FR-DC-21 amend loop (L2, **deferred to port**) grows the vocab, re-runs the onboarding helpers incrementally, and re-freezes. The dictionary **never self-grows** (containment `tags ⊆ vocabulary` is a hard build gate, §10.1).

## Open questions (capture, do not invent)

1. **Onboarding sample-input mechanism (unspecified).** FR-DC-20 says `domain_onboard` "reads sample documents and a sample repo" but never specifies *how* those samples are configured/pulled. `UI_INPUT.yaml` (§3.1) is a **per-run** artifact carrying run-only fields (`run_id`, `gates`, `jira`, `frame`) that do not apply to learning a vocabulary, so onboarding likely reuses the **connector + source-pointer** machinery rather than the whole file — but the exact artifact is undefined. `adapter_onboard` depends on the same sample sources, so this gap must be resolved before either helper is built.
2. **Doc-side vocabulary-adequacy asymmetry.** The `uncovered_concepts[]` adequacy detector (FR-DC-21) is specified on `code_map_build`'s `model_enrich` (per code file) only. Containment (cannot invent a tag) applies to both pipelines, but the "vocabulary is too *small*" signal has **no documented doc/article-side equivalent** — a new concept appearing only in the source documents may not be surfaced the way a code-side one is. Worth deciding whether the doc adapter skills should emit a symmetric adequacy signal.
