# Knowledge Provenance: Technical Spec

PDLC Neuro · Evergreen Knowledge Base loop · build spec

| | |
|---|---|
| **Status** | Draft v0.2 for review (2026-11-10) |
| **Owner** | Varun Munjal, AI Automation Team, Merchant Services |
| **Read with** | `knowledge_provenance_vm_1.2.html` (the pitch deck) and `Knowledge_Provenance_Walkthrough_v1.1.md` (the agreed design, with the full metric definitions). Where this spec says "agreed", it means decided in the walkthrough. **If this spec and the walkthrough disagree on *what* the process does, the walkthrough wins.** This spec covers *how* to build it. |
| **Audience** | Tech lead and engineers building it, plus the Knowledge Hub team (Phases 3 and 4 need their help) |

---

## 0. What we are building and why

### 0.1 The problem
Every PDLC Neuro run builds a Solution Intent from three places: the **Knowledge Base** (Knowledge Hub), **documents in `sources/`**, and **what the analyst knows and types**. Nothing records which fact came from where. That causes three problems:

1. **We can't trust the Solution Intent.** A sentence the agent made up from its own training reads exactly like a sourced one, and nothing checks it before publish.
2. **The KB decays without anyone noticing.** When the analyst corrects a KB value in the chat, the Solution Intent gets the right number, but the KB keeps the old one. The next run hits the same gap.
3. **We can't measure anything.** Nobody can say how much of the work the KB does, how often it's wrong or missing, whether fixes ever reach it, or whether the agent even asks it.

### 0.2 Goals
| # | Goal | In one line | Pitch label |
|---|---|---|---|
| G1 | **Prove** | Every factual claim in a Solution Intent is traced to a real source, and unsourced claims are caught **before publish** | 01 · PROVE |
| G2 | **Improve** | What the KB got wrong or didn't have flows back into it, and **a person approves every change** | 02 · IMPROVE |
| G3 | **Measure** | Four questions answered every week: Can we trust the Solution Intent? Does the KB deliver when asked? Is the loop closing? Is it being used? | 03 · MEASURE |

### 0.3 Non-goals
- **Not proving facts true.** "Verified" means traced to a source. A KB claim can be verified and still be wrong.
- **Not updating the KB automatically.** Every KB change goes through an approver.
- **Not measuring people.** The metrics measure the KB and the process, not analysts.
- **Not replacing** the plugin's existing `[Confident]/[Plausible]/[Verify]` tags.
- **Not covering yet:** the Epic, edits made after publish in Confluence or Jira, or the items in §13.4.

### 0.4 Who it serves
| Role | What they get | What they do |
|---|---|---|
| **Analyst** | A Solution Intent they can stand behind | Keep or remove the claims that have no source, once per run |
| **Domain approver** | A short weekly queue of evidence-backed KB fixes | Approve, edit, reject, retire or re-route each one. This is the KB gate. |
| **Process owner** | Weekly metrics, plus the claims where the checker's two runs disagreed | Tunes prompts and the test set |
| **Tech team** | Reports on where the agent skipped the KB, and on failed searches | Fixes prompts and retrieval |
| **Leadership** | Four headline numbers, as weekly trends | Funding and adoption decisions |

### 0.5 Requirements

**Functional: what the system must do**

| # | Requirement | Step | Goal |
|---|---|---|---|
| FR-1 | Log every KB query and every `sources/` read during the run, including the text returned and failed lookups. Retry a KB no-hit once. | 1 | G1, G2 |
| FR-2 | The drafting agent cites a source after every factual sentence: KB, `sources/`, analyst, derived, or an honest `none`. | Drafting | G1 |
| FR-3 | At the end of the run, gather the log, transcript, cited Solution Intent and `sources/` manifest into one run folder. | 2 | all |
| FR-4 | Split the Solution Intent into one-fact claims, judged from the sentence itself, not from whether it has a citation. | 3 | G1 |
| FR-5 | Tag each claim with its source (KB / Local / User / Derived / Unsupported), using a quote that code has confirmed exists in the stored text. | 4 | G1 |
| FR-6 | For each claim, record what the KB did on that topic (Fully answered / Wrong Hit / No Hit / Never Asked) and the KB action it implies. | 4 | G2, G3 |
| FR-7 | Before publish, show the analyst every Unsupported claim for keep or remove. Block publish until every one is answered. | 4 | G1 |
| FR-8 | Publish a clean Solution Intent with citations stripped. Keep the cited copy and the full trace as the audit trail. | 2, 5 | G1 |
| FR-9 | Produce a readable provenance report per run, built by code from the trace. | 5 | G1 |
| FR-10 | Weekly, turn KB gaps into deduplicated candidates that are reusable, placed in the right domain and merged across runs, then route them to the domain approver. | 6 | G2 |
| FR-11 | Write approved changes to the KB as new versions, with who approved, when, and which runs raised them. | 6 | G2 |
| FR-12 | Compute the four weekly metric groups from the traces and Step 6 outcomes, and send Never Asked and retrieval-miss reports to tech. | Result | G3 |

**Non-functional: how well it must do it**

| # | Requirement |
|---|---|
| NFR-1 | **It never breaks the analyst's session.** If provenance fails, the work continues and the failure is logged. |
| NFR-2 | **Evidence is real by construction.** No LLM-picked quote or KB citation is accepted without a word-for-word code check. |
| NFR-3 | **Separate checking.** The agents that split, check and judge run in a fresh context, separate from the drafter. |
| NFR-4 | **Short wait.** The end-of-chat wait is short enough that analysts don't skip it (target ≤ 10 minutes for 200 claims, to confirm in the prototype). |
| NFR-5 | **Auditable and append-only.** Any KB change traces back to the original file location or chat message. Nothing is overwritten. |
| NFR-6 | **Fits the environment.** Copilot Chat in VS Code only, on the Windows/PowerShell VDI. No new model APIs, and no changes to other teams' plugins. |
| NFR-7 | **Re-runnable.** Old runs can be re-traced when prompts improve. Prompt and model versions are recorded with every result. |
| NFR-8 | **Data handling.** Run data is treated as confidential as the Solution Intent. The shared store holds the minimum needed. |
| NFR-9 | **Bounded cost.** About 20–25 model calls per run, measured against Copilot request limits. |

### 0.6 How we do it, on one page
**Capture during the run, judge after it, and let people decide only at the two gates.**

| Step | What | How (mechanism) | Who |
|---|---|---|---|
| 1 · Log | Record every knowledge read | A thin `prov` wrapper around `kh-cli` and `sources/` writes `log.jsonl` | Code |
| 2 · Collect | One folder per run | `prov finalize`: transcript export, manifest, cited snapshot, turn numbers | Code |
| 3 · Split | Solution Intent → claims | A fresh-context splitter agent; code assigns IDs and checks | LLM + code |
| 4 · Trace | Source, gap type, KB action per claim | Checker agents per section, in parallel; code checks every quote; second run for Wrong Hits and low-confidence answers; analyst keeps or removes Unsupported claims | LLM + code + **analyst** |
| 5 · Report | Readable audit trail | Generated from `trace.jsonl` by code | Code |
| 6 · Act | KB gaps → approved KB changes | Weekly: judge filters, dedups, places and merges; queue in Jira; versioned ingest | LLM + code + **approver** |
| Result | Four questions, weekly | Metrics rollup from traces and Jira history | Code |

Delivery is phased (§12): **prototype → per-run provenance (G1) → shared store and metrics (G3) → the KB loop (G2) → ingest and scale.** Each phase is worth something even if the next one stalls.

### 0.7 What success looks like
- **Per run:** no made-up quote survives into the trace. Unsupported claims are typically 0–5 per Solution Intent, all answered before publish.
- **Weekly trends** (directions; targets are set after 3–4 baseline weeks): Unsupported rate ↓ toward ≤2% · KB used rate ↑ · time to fix ↓ · runs per week and repeat teams ↑ · Never Asked ↓ toward ≤5%.
- **The loop works when** a gap found in one run is approved, ingested, and stops showing up in later runs.

### 0.8 How to read the rest

The pitch says what the process does: six steps, two human decisions, and one weekly result. The rest of this document says how to build it. It is organised so you can stop at the depth you need:

- **§1–§3** cover the mental model: the principles, the constraints, and the shape of the system. Read these before writing any code.
- **§4–§5** are the contracts: every component and every file format. This is what engineers build against.
- **§6** goes step by step: algorithms, edge cases, and acceptance tests for each step.
- **§7–§10** cover the cross-cutting parts: LLM design, Copilot specifics, the shared back end, and security.
- **§11–§13** cover delivery: how to test it, phased rollout, risks, and open questions.

Vocabulary is the walkthrough's. **Tags:** KB, Local, User (fact or decision), Derived, Unsupported. **Outcomes:** Unverified, User (confirmed at check). **Gap types:** Fully answered, Wrong Hit, No Hit, Never Asked. **KB actions:** add, correct, check, retire.

---

## 1. How to think about it: the design principles

These rules settle most build questions before they become arguments.

### P1. Judgement goes to the LLM. Proof goes to code.
Every LLM output that carries evidence has to be checkable by code. The checking agent picks a `source_quote`, and code confirms that the quote appears word for word in the stored text. The judge cites a KB entry, and code confirms that the entry was in the search results. **No LLM output is trusted without a deterministic check behind it.** This principle carries the whole idea. Without it, we are using a model to mark its own homework.

### P2. Capture is cheap and dumb. Interpretation comes later.
Step 1 records and never decides. Every judgement happens after the run, on the stored evidence. This keeps the in-run wrapper small, fast and unlikely to break the analyst's session. It also means we can re-run Steps 3–7 on old runs whenever the prompts improve.

### P3. One file is the record. Everything else is a view.
`trace.jsonl` (plus the analyst's keep/remove answers written back into it) is the record for a run. The report, the KB candidates and the metrics are all **built from** it and never edited by hand. If a number in the report looks wrong, fix the trace or the code, never the report.

### P4. Append, version, never overwrite.
Log lines are append-only. Re-tracing a run writes a new trace version and doesn't edit the old one. KB changes are new versions of an entry. A retired entry is marked inactive and never deleted. The audit trail is a product feature, not a side effect.

### P5. Fail loudly at the gate. Degrade quietly elsewhere.
- **Fail closed (block):** publishing with Unsupported claims still unanswered. A KB change without an approver.
- **Fail open (degrade, but record it):** wrapper bypassed (B6 covers it), transcript export missing (use the fallback), a second run times out (mark the claim Unverified).
- The analyst's session must **never** break because provenance broke. If logging fails, the read still goes through and the failure is logged.

### P6. Separate agents, fresh context.
Drafter, splitter, checker and judge are different agents with no shared memory. An agent checking its own drafting finds what it expects to find. In Copilot this means a separate chat session or a sub-agent (see §8), not the same thread.

### P7. Build the per-run loop first. Build the cross-run loop when the data has earned it.
Steps 1–5 run on one analyst's machine with plain files. Steps 6–7 need shared state across analysts. Don't build the shared back end until real runs prove that Steps 1–5 produce clean traces (see §12).

### P8. The metrics measure the KB and the process, never people.
Never build an analyst leaderboard, even when someone asks for one. This rule is already agreed; the code must not make it easy to break.

---

## 2. Context and constraints

What we are building into, and what that rules out.

| Constraint | Source | Consequence for the build |
|---|---|---|
| **Copilot Chat in VS Code is the only LLM runtime** | Environment decision (Step 2, decision 3) | No direct model API. Every LLM step is a Copilot agent prompt, with its own prompt file, sub-agent or chat session. Throughput and cost are bounded by Copilot request limits (§7.6). |
| **VDI, Windows, PowerShell as the default terminal** | Plugin setup docs | Scripts must run on Windows. Python is preferred **if it is on the VDI** (open question Q1). Otherwise, PowerShell 7. Paths must handle `\`. |
| **The KB is the Knowledge Hub, reached through the `mct_knowledge-hub` CLI (the `kh-cli` seam from neuro-plugin)** | Plugin docs | B1 wraps this CLI. We need it to return chunk IDs and locations (Q2). We do **not** own the KB's write path (Q6). |
| **`sources/` plus `sources/SOURCES.md` already exist, with SRC-IDs that must be cited inline** | Plugin Sources Discipline, Rules A–C | Reuse the SRC-ID convention in citations instead of adding a competing one (decision D-4). |
| **The plugin already has confidence tags for KH findings: `[Confident]` / `[Plausible]` / `[Verify]`** | Plugin ACD | These are a **different axis** from provenance tags. Don't merge them. A claim can be `KB` + `[Plausible]`. Keep both, and never let one overwrite the other. |
| **Runs live locally under `LOCAL_PROJECT_ROOT` on each analyst's VDI** | Plugin setup | Per-run work is local. Cross-run work (Steps 6–7) needs runs shipped to a shared place (§9). |
| **Delivered as part of the product-owner-plugin (a Copilot chat plugin: instructions, prompt files, skills, scripts)** | Plugin structure | Provenance ships as plugin assets: instructions, `/provenance` prompts and `scripts/prov/`. Adding it must not require changes to other teams' plugins. |
| **Solution Intents are 150–300 claims** | Walkthrough, Step 4 | The end-of-chat wait matters. Tracing must be parallel (per section) and bounded (§7.6). |

---

## 3. System shape

### 3.1 Three planes

```
 ┌─────────────────────── PLANE A · IN-RUN (analyst's VS Code, live) ───────────────────────┐
 │                                                                                          │
 │   Drafting agent (PDLC) ──cites as it writes──► final.md (hidden <!-- cite --> comments)   │
 │        │                                                                                 │
 │        ├── prov kb  "<query>" --section S ──► kh-cli ──► log.jsonl  (kb_query)           │
 │        └── prov read <file> <loc> --section S ──► sources/ ──► log.jsonl (source_read)   │
 │                                                                                          │
 └──────────────────────────────────────────────────────────────────────────────────────────┘
                                    │  analyst runs /provenance
 ┌─────────────────── PLANE B · END OF RUN (same machine, before publish) ──────────────────┐
 │  prov finalize   → transcript.jsonl, manifest.json, final.md snapshot, turn join   [code] │
 │  Split agent     → claims.jsonl                                                    [LLM]  │
 │  Check agents ×N → raw verdicts (one per section, in parallel)                    [LLM]  │
 │  prov verify     → quote checks, citation resolution, second-run selection       [code]  │
 │  Check agents    → second runs (Wrong Hit + low confidence only)                  [LLM]  │
 │  prov trace      → trace.jsonl (merged, versioned)                                [code]  │
 │  Analyst         → keep/remove on Unsupported                                    [HUMAN] │
 │  prov report     → knowledge_provenance_report.md, metrics.json                   [code]  │
 │  prov publish    → solution_intent.md (citations stripped). Blocked until answered. [code]│
 │  prov ship       → copies the run bundle to the shared store                      [code]  │
 └──────────────────────────────────────────────────────────────────────────────────────────┘
                                    │  weekly
 ┌──────────────────── PLANE C · CROSS-RUN (shared store, process owner's job) ─────────────┐
 │  6a reusable? · 6b in KB? · 6c where? · 6d merge          [LLM judge + code checks]       │
 │  6e approver queue per domain                               [HUMAN, the KB gate]          │
 │  6f ingest (versioned) → Knowledge Hub                      [code / KH team]              │
 │  Step 7 metrics rollup → weekly report / dashboard          [code]                        │
 │  Tech reports: Never Asked by section, retrieval misses     [code]                        │
 └──────────────────────────────────────────────────────────────────────────────────────────┘
```

### 3.2 Who does what

| Work | Code | LLM | Human |
|---|---|---|---|
| Log reads, rerun on no_hit | ✓ | | |
| Collect run folder, transcript, manifest, turn join | ✓ | | |
| Split into claims | | ✓ splitter | |
| Find the cited item, check the quote is real, resolve the citation | ✓ | | |
| Is the claim supported? Which quote? Gap type? Confidence? | | ✓ checker | |
| Pick claims for a second run, compare runs | ✓ | ✓ checker (2nd) | |
| Keep or remove Unsupported claims | | | ✓ analyst |
| Report, metrics, strip, publish gate | ✓ | | |
| Reusable? Duplicate? Placement? Merge? Proposed text? | ✓ search | ✓ judge | |
| Approve, edit, reject, retire, re-route | | | ✓ approver |
| Versioned ingest, audit | ✓ | | |

### 3.3 One CLI, many subcommands

Ship **one script entry point, `prov`**, with subcommands, rather than eight loose scripts. One entry point gives one place for config, logging, path handling and version stamping, and the agent instructions only have to name one tool.

| Subcommand | Plane | Build item | Called by |
|---|---|---|---|
| `prov init` | A | (new) | PDLC agent at run start: writes the run header |
| `prov kb` | A | B1 | Drafting agent: every KB query |
| `prov read` | A | B2 | Drafting agent: every `sources/` read |
| `prov finalize` | B | B5 (part), B6, B7 | `/provenance` prompt |
| `prov context <section>` | B | (new) | `/provenance`: builds the input packet for each section's checker |
| `prov verify` | B | (new) | `/provenance`: code checks over the checker output |
| `prov trace` | B | (new) | `/provenance`: writes `trace.jsonl` |
| `prov decide` | B | (new) | Chat agent: records the analyst's keep/remove |
| `prov report` | B | (new) | `/provenance`: report and `metrics.json` |
| `prov publish` | B | B5 | Analyst or agent: strip and publish, with the gate |
| `prov ship` | B | (new) | After publish: sends the bundle to the shared store |
| `prov candidates` | C | (new) | `/provenance-weekly`: 6a–6d code side |
| `prov queue` / `prov ingest` | C | (new) | 6e/6f |
| `prov metrics --week` | C | (new) | Weekly rollup |
| `prov eval` | dev | (new) | Test-set regression (§11) |

---

## 4. Component inventory

The walkthrough's B1–B8, plus what it takes to run the steps after them.

| # | Component | Kind | Plane | Phase | Notes |
|---|---|---|---|---|---|
| B1 | KB wrapper (`prov kb`) | script | A | 0 | Wraps `kh-cli`. Logs, reruns once on no_hit, returns copy-ready IDs. |
| B2 | `sources/` wrapper (`prov read`) | script | A | 1 | Reads through one canonical text extractor (§6.1.3). Copilot may bypass it. |
| B3 | Citation instructions | instructions | A | 0 | In the PDLC agent instructions. Draft and cite section by section. |
| B4 | Citation format | grammar | A | 0 | Formal grammar in §5.3, with a parser in code. |
| B5 | Strip and publish (`prov publish`) | script | B | 1 | Gated on the Unsupported answers. |
| B6 | `sources/` manifest | script | B | 1 | Part of `prov finalize`. |
| B7 | Transcript capture | script + instructions | B | 0 (manual) → 1 | Export first. Self-logging as the fallback. |
| B8 | Section citation check | script | A | only if needed | Add only if the prototype shows citations slipping. |
| B9 | Splitter prompt | prompt file | B | 1 | Fresh context. |
| B10 | Checker prompt | prompt file | B | 1 | One instance per section, parallel. Structured JSON output. |
| B11 | Verifier (`prov verify`) | script | B | 1 | Quote checks, citation resolution, second-run selection, merge. |
| B12 | Report and metrics generator | script | B | 1 | Pure functions of `trace.jsonl`. |
| B13 | `/provenance` orchestrator prompt | prompt file | B | 1 | Runs B6/B7 → B9 → B10 → B11 → analyst check → B12 → B5. |
| B14 | Shared store and `prov ship` | infra + script | C | 2 | §9. |
| B15 | Candidate pipeline (6a–6d) | script + judge prompt | C | 3 | Needs KB similarity search (Q5). |
| B16 | Approver queue (6e) | Jira or files | C | 3 | Recommend Jira (§6.6.5). |
| B17 | Ingest (6f) | script / KH API | C | 4 | Depends on the KH write path (Q6). |
| B18 | `kb_domains` registry | config | C | 3 | Domain, description, approver, backup approver. |
| B19 | Test set and `prov eval` | data + script | dev | 1 | 20–30 hand-labelled claims to start. Grows over time. |
| B20 | Weekly metrics rollup and tech reports | script | C | 2 | Markdown first. Dashboard later. |

---

## 5. Data contracts

All machine files are **UTF-8 JSON Lines** (one JSON object per line) or JSON. Every record has a `schema` field (for example `"log/1"`) so formats can change without breaking old runs. Timestamps are ISO-8601 UTC. IDs are strings.

### 5.1 Run folder

```
<LOCAL_PROJECT_ROOT>/<initiative>/runs/<run_id>/
  run.json                       header + state machine           (prov init, updated by each stage)
  log.jsonl                      Step 1 events                     (prov kb / prov read, live)
  transcript.jsonl               every message, numbered           (prov finalize)
  manifest.json                  sources/ files present at end     (prov finalize)
  final.md                       cited Solution Intent snapshot    (prov finalize)
  sources.md                     agent's human citation list       (agent; for people only)
  claims.jsonl                   Step 3 output                     (splitter → prov)
  checks/<section>.r1.json       raw checker output, run 1         (checker)
  checks/<section>.r2.json       raw checker output, second runs   (checker)
  trace.v<N>.jsonl               Step 4 output, versioned          (prov trace)
  trace.jsonl                    copy of the current version (or a link to it)
  decisions.jsonl                analyst keep/remove answers       (prov decide)
  knowledge_provenance_report.md Step 5                            (prov report)
  metrics.json                   per-run counts                    (prov report)
  solution_intent.md             published, citations stripped     (prov publish)
```

`run_id` format: `r-YYYY-MM-DD-NNNN`. There is **one run per epic** (agreed). Sessions are recorded inside `run.json`.

### 5.2 `run.json`: header and state

```json
{
  "schema": "run/1",
  "run_id": "r-2026-10-27-0412",
  "epic": "EP-2210",
  "initiative": "cnp-3ds-mandate",
  "domain": "Payments",
  "team": "MS-PBI",
  "analyst": "<sid>",
  "assistant": {"plugin": "product-owner-plugin", "plugin_version": "x.y.z", "model": "<copilot model id>"},
  "kb_snapshot": "kb-2026-10-20",
  "sections": ["Scope", "Solution", "Timeline", "Risks"],
  "sessions": [{"n": 1, "start": "2026-10-27T09:41:00Z", "end": "2026-10-27T11:02:00Z"}],
  "prov_version": "0.1.0",
  "prompt_versions": {"splitter": "s-3", "checker": "c-5"},
  "state": "drafting",
  "state_history": [{"state": "drafting", "at": "2026-10-27T09:41:00Z"}]
}
```

**State machine.** Each `prov` subcommand checks that the run is in the state it expects, and refuses otherwise. This makes re-runs safe and stops steps running out of order.

```
drafting → finalized → split → checked → traced → awaiting_analyst → answered → reported → published → shipped
                         ▲                                    │
                         └──────── re-trace (new trace.vN) ◄──┘   (allowed until 'published')
```

### 5.3 Citation grammar (B4)

The format is a hidden HTML comment at the end of each factual sentence. The grammar is formal so that one parser serves both B8 and B11.

```
citation    := "<!--" ws "cite:" ws refs ws "-->"
refs        := ref ( ws ";" ws ref )*
ref         := kb_ref | src_ref | analyst_ref | derived_ref | none_ref
kb_ref      := "KB" ws chunk_id                                   e.g. KB ic-0412
src_ref     := ( "sources/" path | src_id ) [ ws "·" ws location ]   e.g. sources/interchange_2026.xlsx · CNP!A4:D4
                                                                 or SRC-003 · CNP!A4:D4
analyst_ref := "analyst" ws quoted                                 e.g. analyst "Phase 1: 2027-03-01"
derived_ref := "derived from" ws input ( ws "," ws input )* [ ws ";" ws "calc" ]
none_ref    := "none" [ ws "(general knowledge)" ]
location    := sheet "!" range | "§" section | "L" n [ "-" m ] | "p" n
```

- The parser accepts `·` or `|` as the location separator, and is lenient with whitespace. Copilot won't be perfectly consistent.
- **A citation that doesn't parse** is treated as `none` and flagged `citation_malformed` in the trace. The claim still gets searched in Step 4C, so a bad citation can't hide a claim.

### 5.4 `log.jsonl` (Step 1)

```json
{"schema":"log/1","seq":12,"ts":"2026-10-27T10:02:41.120Z","session":1,"section":"Scope",
 "turn":null,"event":"kb_query","query":"CNP interchange tiers","rerun_of":null,
 "result":"hit","chunks":[{"id":"ic-0412","location":"Payments/Pricing","score":0.81,
 "text":"Standard 1.80% + $0.10 per transaction ..."}],"kb_snapshot":"kb-2026-10-20",
 "duration_ms":640,"error":null}

{"schema":"log/1","seq":13,"ts":"2026-10-27T10:02:44.002Z","session":1,"section":"Scope",
 "turn":null,"event":"source_read","path":"sources/interchange_2026.xlsx","src_id":"SRC-003",
 "location":"CNP!A4:D4","search":null,"result":"found",
 "excerpt":"Card-not-present | Standard | 1.95% | $0.10","modified":"2026-10-24T16:10:00Z",
 "extractor":"xlsx/1","error":null}
```

- `seq` is a counter that only goes up, per run. It is the order of events.
- `turn` is **null when written** and is filled in by `prov finalize` (see §6.1.4). This fixes a gap in the walkthrough: the wrapper runs inside a tool call and **cannot know the turn number**. The walkthrough already accepts that the assistant doesn't know turn numbers (B4).
- `chunks[].text` stores the **full** chunk text and never truncates it. Step 4's quote check runs against it.
- `error` is filled in when the wrapper failed but passed the read through anyway (P5).

### 5.5 `transcript.jsonl` (B7)

```json
{"schema":"transcript/1","turn":27,"session":1,"ts":"2026-10-27T10:19:05Z","role":"assistant",
 "text":"I couldn't find the mandate effective dates in the KB or in sources/. Can you provide them?",
 "tool_calls":[{"name":"run_in_terminal","summary":"prov kb \"mandate effective date\" --section Timeline"}]}
{"schema":"transcript/1","turn":28,"session":1,"ts":"2026-10-27T10:21:40Z","role":"analyst",
 "text":"Phase 1: 2027-03-01, Phase 2: 2027-09-01","attachments":[]}
```

- `role` is `analyst` or `assistant`. **Only `analyst` text can back a claim.**
- `tool_calls` is optional but valuable if the export provides it (see §6.1.4).
- Attachments the analyst pastes as files should be saved to `sources/` and read through `prov read`, so they are tagged Local. Pasted text stays in `text` and is tagged User.

### 5.6 `manifest.json` (B6)

```json
{"schema":"manifest/1","taken_at":"2026-10-27T11:02:30Z",
 "files":[{"path":"sources/interchange_2026.xlsx","src_id":"SRC-003","modified":"2026-10-24T16:10:00Z","bytes":48213,"extractable":true}]}
```

The walkthrough's no-hashes assumption holds for Step 4, because it runs minutes after the reads. Adding `bytes` and `modified` costs nothing and lets Step 4 warn if a file changed between the read and the check. Optional sha256 is off by default.

### 5.7 `claims.jsonl` (Step 3)

```json
{"schema":"claim/1","id":"C-01","section":"Scope","para":1,"sentence":1,
 "text":"CNP Standard rate is 1.95%",
 "sentence_text":"CNP Standard tier: 1.95% + $0.10 per transaction.",
 "citations":[{"kind":"src","path":"sources/interchange_2026.xlsx","src_id":"SRC-003","location":"CNP!A4:D4"}],
 "citation_raw":"sources/interchange_2026.xlsx · CNP!A4:D4","derived_from":null}
```

- IDs are assigned **by code** after splitting, in document order (`C-01…`). The LLM's IDs are ignored. This keeps IDs stable and gap-free.
- `sentence_text` is kept so Step 4 and the report can show the context, and so B5 can find the sentence again when the analyst removes a claim.

### 5.8 `trace.jsonl` (Step 4: the record)

```json
{"schema":"trace/1","trace_version":1,"claim_id":"C-01","section":"Scope",
 "tag":"Local","user_kind":null,"unsupported_kind":null,
 "source_quote":"Card-not-present | Standard | 1.95% | $0.10",
 "source_ref":{"kind":"log","seq":13,"path":"sources/interchange_2026.xlsx","location":"CNP!A4:D4","turn":14},
 "citation_status":"held",
 "kb_quote":"Standard 1.80% + $0.10","kb_ref":{"seq":12,"chunk_id":"ic-0412","location":"Payments/Pricing"},
 "gap_type":"wrong_hit","gap_detail":null,"retrieval_miss":false,
 "kb_action":"correct",
 "confidence":"high","runs":2,"runs_agree":true,"borderline":false,
 "reason":"Same tier and fee; sheet dated 2026, KB is the 2025 schedule.",
 "checks":{"cited_item_exists":true,"source_quote_verbatim":true,"kb_quote_verbatim":true},
 "derived":null,
 "analyst_decision":null,
 "outcome":"traced"}
```

| Field | Values |
|---|---|
| `tag` | `KB` · `Local` · `User` · `Derived` · `Unsupported` |
| `user_kind` | `fact` · `decision` · `confirmed_at_check` (when tag is User) |
| `unsupported_kind` | `plain` · `general_knowledge` · `input_not_found` · `calc_fails` |
| `citation_status` | `held` (citation supported the claim) · `corrected` (search found a different source) · `failed` · `absent` · `malformed` |
| `gap_type` | `fully_answered` · `corroborated` · `wrong_hit` · `no_hit` · `missing_piece` · `never_asked` · `null` (Unsupported or Derived) |
| `retrieval_miss` | true if the first query missed and the rerun hit, and the claim used the rerun result |
| `kb_action` | `none` · `add` · `correct` · `check` |
| `outcome` | `traced` · `unverified` · `removed` (analyst) |
| `analyst_decision` | `null` · `keep` · `remove` (copied from `decisions.jsonl` by `prov decide`) |

`missing_piece` is kept separate from `no_hit` in the data, even though both show as "missing" in the Q2 charts and both lead to `add`. The walkthrough treats them alike for counting. Keeping them apart is cheap and helps 6c placement, because a missing piece already points at an entry.

### 5.9 `decisions.jsonl`

```json
{"schema":"decision/1","claim_id":"C-16","decision":"keep","by":"<sid>","at":"2026-10-27T11:09:12Z","via":"chat"}
```

### 5.10 `metrics.json` (per run)

The walkthrough's fields, by section and domain: `kb_asked`, `kb_used`, `kb_overruled`, `kb_missing`, `kb_returned`, `kb_never_asked`, `mix{KB, Local, User_fact, User_decision, Derived, Unsupported}`, `unsupported{found, kept, removed, general_knowledge}`, `unverified`, `borderline`, `retrieval_misses`, plus header fields (`team`, `analyst`, `run_date`, `epic`) for Q4. **Computed only by `prov report` from `trace.jsonl`**, never by an LLM (P3).

### 5.11 KB candidate (Step 6)

```json
{"schema":"candidate/1","candidate_id":"KC-0031","status":"open",
 "action":"correct","target":{"entry_id":"ic-0412","domain":"Payments/Pricing","tier":1},
 "kb_says":"Standard 1.80% + $0.10","source_says":"Card-not-present | Standard | 1.95% | $0.10",
 "proposed_text":"Standard 1.95% + $0.10 (effective 2026-01-01)",
 "evidence":[{"run_id":"r-2026-10-27-0412","claim_id":"C-01","source_quote":"...","source_ref":{...}}],
 "runs_seen":3,"first_seen":"2026-10-27","flags":[],
 "judge":{"recommendation":"approve","reason":"...","runs":2,"agree":true,"prompt_version":"j-2"},
 "routed_at":null,"approver":null,"decided_at":null,"decision":null,"decision_reason":null,
 "ingested_at":null,"kb_version_after":null,"jira_key":null,
 "history":[{"at":"...","event":"created"},{"at":"...","event":"merged","run_id":"..."}]}
```

`flags` takes values from: `analyst_supplied_no_document`, `judge_unsure`, `sources_disagree`, `placement_unsure`, `new_topic`, `borderline`.

---

## 6. Step-by-step build detail

For each step: what it consumes and produces, how it works, where it breaks, and what "done" means.

### 6.1 Step 1: Log every knowledge read (B1, B2, `prov init`)

#### 6.1.1 `prov init`
Called by the PDLC agent at the start of the epic's first session. It is also called at the start of every later session, where it appends to `sessions`. It writes `run.json`. On a later session, `prov init --resume` reopens the existing run. **The agent instructions must make this the first action of every session.** If it's missed, `prov kb` creates the run lazily and flags `init_missing`.

#### 6.1.2 `prov kb "<query>" --section <S> [--k 5]`
1. Call `kh-cli` with the query. Capture the raw output.
2. Parse chunk IDs, locations, scores and **full text**. *Depends on Q2. If `kh-cli` doesn't expose IDs, Step 4 can't match KB citations, and this is a blocker to raise with the Knowledge Hub team first.*
3. Write a `kb_query` line.
4. On `no_hit`, rewrite the query **once** and call again. The second line has `rerun_of` = the first line's `seq`.
   - Who rewrites it? **Option A (recommended):** the wrapper returns `no_hit` with the instruction "rerun once with a reworded query using `--rerun-of <seq>`", and the agent rewords it. The agent understands the context. **Option B:** fixed rules in code (drop stop words, expand acronyms from a glossary). Option B is deterministic but weaker. Start with A and log which one was used.
   - Enforce "once" in code: a second `--rerun-of` against the same `seq` is refused.
5. Return to the agent a compact, copy-ready block:
   ```
   KB ic-0412 · Payments/Pricing · score 0.81
   "Standard 1.80% + $0.10 per transaction ..."
   cite as: <!-- cite: KB ic-0412 -->
   ```
   Handing the agent the exact citation string is the cheapest way to get good citations.
6. **On error** (CLI down, parse failure): pass through whatever the CLI returned, write the line with `error`, and exit 0. Never block the session (P5).

#### 6.1.3 `prov read <path> [<location>] --section <S>` and `prov read --search "<term>" --section <S>`
- **Canonical text extraction is the critical design choice here.** Step 4 checks quotes against "the stored text". For `.md` and `.txt` that's simple. For `.xlsx`, `.docx` and `.pdf`, the wrapper and the verifier **must use the same extractor**, or a real quote will fail verification. Define one extractor per type, version it (`extractor: "xlsx/1"`), and record the version on each log line:
  - **xlsx:** each row rendered as cells joined with ` | `, with an optional range like `CNP!A4:D4`. The walkthrough examples already assume this shape.
  - **docx / md:** paragraphs as text. Locations are `§` heading paths or `L`-line ranges.
  - **pdf:** reuse the existing `pdf-scrape-standard` skill's extraction if it is deterministic. Locations are `p<n>`.
- Simplest robust option: **at session start, convert every `sources/` file to a text sidecar** (`sources/.text/<file>.txt`) using the canonical extractors, and have both `prov read` and the verifier read the sidecars. This also makes `--search` easy, as a grep over the sidecars.
- `--search` writes a `source_read` with `search` set, and `found` or `not_found`. Failed searches matter for gap typing.
- Confluence pages found on the fly: the agent saves them into `sources/` first, using the existing `confluence-scrape` skill, then reads them with `prov read`. This rule is already agreed and must be in the instructions.

#### 6.1.4 Turn numbers: the fix
The wrapper can't know the turn. Assign it **after the run** in `prov finalize`:

1. **Preferred:** if the chat export includes tool calls within each assistant response, match each `prov kb` or `prov read` invocation to its log line by order and argument text. The turn is exact.
2. **Fallback:** join on timestamps. A log line belongs to the assistant turn whose time window (from the previous analyst message to the end of the response) contains the log `ts`.
3. **Last resort:** turn stays `null`. Step 4D then uses **section + order (`seq`)** instead of turns. That is enough for gap typing, since the rules are "this section first, then the whole run".

Write down which method was used (`turn_join: "tool_calls" | "timestamps" | "none"`) in `run.json`.

#### 6.1.5 Enforcing the wrapper
Copilot can use its built-in file read tool and skip `prov read`. Layered defence:
1. **Instructions:** "Read `sources/` only through `prov read`. Query the KB only through `prov kb`."
2. **Tool restriction:** if the PDLC agent is a custom chat mode or agent with a tools allowlist, leave out the built-in read for `sources/`. *To verify: whether VS Code lets you restrict tools per path. It probably doesn't, so this may be all or nothing.*
3. **B6 safety net:** Step 4 verifies Local quotes against the file itself, so a bypass costs a log line but not correctness.
4. **Measure it:** `prov finalize` counts `sources/` files cited in `final.md` with no `source_read` line → `bypass_rate` in `metrics.json`. The prototype decides whether that's acceptable.

KB bypass matters more. If the agent ever reaches the Knowledge Hub without `prov kb`, for example through the Knowledge Hub chat agent, **the KB evidence is lost, and B6 can't recover it.** The instructions must forbid other KB paths during a PDLC run. The prototype must check this.

#### 6.1.6 Acceptance
- [ ] 100% of KB reads in a test session produce a log line with full chunk text and IDs.
- [ ] `no_hit` triggers exactly one rerun, and the line has `rerun_of` set.
- [ ] Killing `kh-cli` mid-session does not break the chat. The line records `error`.
- [ ] The extractor round-trip test passes: for every fixture file, a quote taken from `prov read` output verifies against the same file.
- [ ] Overhead is under 150 ms per call on top of `kh-cli` latency.

### 6.2 Step 2: Collect the run (`prov finalize`, B5 part, B6, B7)

1. **Snapshot `final.md`.** Copy the Solution Intent with its citations into the run folder. Source: wherever the PDLC writes the Solution Intent (to confirm per stage).
2. **Transcript (B7).**
   - **Primary:** VS Code chat export. *To verify (Q3): the "Export Chat" command's JSON format. Does it include roles, timestamps, tool calls, and every session if a run spans sessions?* Write a converter, `prov finalize --transcript <export.json>`, that maps it to `transcript.jsonl` and numbers turns with one counter across sessions.
   - **Fallback:** the instructions tell the assistant to append each analyst message, verbatim, and its own reply to `transcript.jsonl` via `prov say` as it goes. This is weaker: the assistant could paraphrase. So **mark the transcript `capture: "self_logged"`**, and have Step 4 treat User quotes from a self-logged transcript as `confidence: low`. The analyst's own words are the evidence. If the assistant transcribes them, the evidence goes through the thing we're checking.
   - It's worth a spike: VS Code keeps chat sessions in workspace storage as JSON. Reading that directly may beat a manual export. It is fragile across VS Code versions, so put it behind the converter.
3. **Manifest (B6).** List `sources/` with `modified`, `bytes`, `src_id` (from `SOURCES.md`) and `extractable`.
4. **Turn join** (§6.1.4).
5. **Sanity checks**, reported but not blocking: every `KB <id>` cited in `final.md` exists in the log; every `sources/` path cited exists in the manifest; the counts of factual sentences with and without a citation (cheap regex; this is B8's metric).
6. Set state to `finalized`.

**Acceptance:** finalize is idempotent, so running it twice gives the same files. A missing export doesn't fail it: it falls back and records which path it took.

### 6.3 Step 3: Split into claims (B9)

**Agent:** a fresh-context splitter. It gets **only `final.md`**: no log, no transcript, no `SOURCES.md`. It must judge "is this a claim?" from the sentence alone. Giving it the sources would bias it towards treating only sourced facts as claims, which is exactly the failure the walkthrough designed against.

**Prompt contents** (versioned as `s-<n>`):
- The claim definition, the "not a claim" list, the test ("if this sentence were false, would the Solution Intent be wrong?") and "when unsure, make it a claim", all word for word from the walkthrough.
- One fact per claim, with the "1.95% + $0.10 = two claims" example.
- Citation inheritance: each claim gets its sentence's citation. With two citations, assign each to the right claim, or carry both.
- 6–10 worked examples drawn from the test set. Include the hard ones: mixed intent and fact, a dependency claim, a decision.
- **Output: a JSON array only**, matching `claim/1` minus `id`. The orchestrator writes it to `claims.jsonl` with code-assigned IDs.

**Processing:**
- Split section by section, one call per section, for size and parallelism. Sections are independent for splitting.
- **Code post-checks:** every claim's `sentence_text` exists in `final.md`, which catches invented claims; every citation that was present was carried, so none was dropped; every factual-looking sentence (contains a number, date, %, $, "must" or "required") produced at least one claim, otherwise `possible_skip` is listed for the eval set. The last check is a heuristic for tuning, not a gate.

**Acceptance:** on the test set, fact/intent precision ≥ 0.9 and recall ≥ 0.95. Recall matters more: a missed claim is never checked.

### 6.4 Step 4: Trace each claim (B10, B11)

The heaviest step. It is split into code and LLM stages so that the LLM only does what needs judgement.

#### 6.4.1 Stage 4.0: Resolve citations (code)
For each claim citation, before any LLM runs:
- `KB <id>` → find log lines whose `chunks[].id` matches. Take the full chunk text.
- `sources/…` or `SRC-…` → the log `source_read` for that path and location, if present, **or** the sidecar text from the manifest file (the B6 path). A path that is not in the manifest → `failed: file_not_present`, which catches made-up file names.
- `analyst "<quote>"` → fuzzy-find the quote in **analyst** messages only (normalised containment; if none, best partial match ≥ 0.9). Record the turn. Found only in an assistant message → `failed: cites_assistant`.
- `derived from …` → resolve each input the same way.
- `none` / malformed → nothing to resolve. Search required.

This turns the walkthrough's step A into data, so the LLM gets the cited text already attached.

#### 6.4.2 Stage 4.1: Build section packets (code, `prov context <section>`)
Each checker instance gets:
- that section's claims with their resolved cited text;
- **the section's log lines** (full chunk text and excerpts);
- **a compact index of the whole-run log**: query plus chunk IDs, plus the full text only for chunks that share a keyword with the section's claims. This keeps packets inside the context limit;
- **analyst messages only**, in full, with turn numbers. Assistant messages are included only as context for analyst replies (the t40/t41 "Go with B." case): pass each analyst message together with the assistant message it answers, clearly labelled `context_only`;
- the list of `sources/` sidecar paths, plus a grep tool (or pre-run keyword hits) for the "search sources/" part of step C.

Packet budget: about 30–40k tokens. If a section is bigger, split it into claim batches of about 25.

#### 6.4.3 Stage 4.2: Check (LLM, one instance per section, in parallel)
**Agent:** a fresh-context checker, prompt version `c-<n>`. For each claim it returns:

```json
{"claim_id":"C-01","supported":true,"tag":"Local","user_kind":null,
 "source_quote":"Card-not-present | Standard | 1.95% | $0.10","source_ref":{"kind":"log","seq":13},
 "search_path":"citation",
 "kb_topic_lines":[12],"kb_quote":"Standard 1.80% + $0.10","gap_type":"wrong_hit","retrieval_miss":false,
 "kb_action":"correct","confidence":"high","reason":"..."}
```

Prompt rules (from the walkthrough):
- Support is judged on **meaning**, but the `source_quote` must be **copied exactly** from the stored text. Say plainly that code will check it.
- Search order when the citation fails or is absent: section log → whole-run log → `sources/` → analyst messages.
- Only analyst messages are sources. Silence isn't agreement. "Go with B." supports a decision only when read with the proposal it answers.
- Derived: recompute it, and show the working in `reason`.
- Gap-type table, `kb_quote` rule, and confidence criteria: copied from the walkthrough as a decision table.
- **Never query the KB.** The checker gets no `prov kb` tool. Enforce this by tool allowlist, not only by instruction.

#### 6.4.4 Stage 4.3: Verify (code, `prov verify`)
For every checker answer:
1. `source_quote` and `kb_quote` are **verbatim substrings** of the referenced stored text, after normalisation: Unicode NFKC, lower-case, collapse whitespace and line breaks, unify quote and dash characters, strip markdown emphasis. Fail → the claim becomes `supported: false`, and the claim goes into a **re-check** pass with the failure reason attached. This happens once only; if it fails again, the claim is Unsupported with `reason: quote_not_found`.
2. `source_ref` points at something real (a log `seq`, a manifest file, an analyst turn).
3. A tag of `User` requires `source_ref.kind == transcript` and `role == analyst`.
4. Derived: every input claim is itself supported. Otherwise the claim is `Unsupported (input_not_found)`.
5. Consistency rules: tag KB ⇒ gap `fully_answered`; Unsupported ⇒ gap `null`; Derived ⇒ gap `null`; User (decision) ⇒ `kb_action: none`. **Code fixes these automatically**, logs `autocorrected`, and counts how often it happened. A high count is a prompt bug.
6. **Select second runs:** every `wrong_hit` plus every `confidence: low`.

#### 6.4.5 Stage 4.4: Second runs (LLM)
A fresh checker gets the **same packet, without the first answer**, for the selected claims only. Code compares the two on **tag and gap type** (the fields that drive actions):
- Agree → keep the first answer. `runs: 2, runs_agree: true`. Low confidence stays `borderline: true`.
- Disagree → `outcome: unverified`, both answers kept in `checks/`, no KB action, not sent to the analyst.
- One extra run only, never a loop. Enforce this in code.

#### 6.4.6 Stage 4.5: Write the trace (code, `prov trace`)
Merge into `trace.v<N>.jsonl` and point `trace.jsonl` at it. Set state to `traced`. If any `Unsupported` claims exist, set state to `awaiting_analyst`.

#### 6.4.7 Analyst check (in chat)
The orchestrator prints the walkthrough's message: the N claims, each with section, text and `unsupported_kind`; Keep or Remove per claim; Keep all; Remove all. Copilot has no buttons, so the analyst replies in text ("keep 1, remove 2 3" or "remove all"). The agent parses the reply and calls `prov decide`, then **reads the parsed decisions back** for confirmation before writing. Each decision writes `decisions.jsonl` and updates the trace (`keep` → `tag: User, user_kind: confirmed_at_check`; `remove` → `outcome: removed`).

- **Remove** must actually take the text out of the Solution Intent. `prov publish` removes the claim's `sentence_text` when **all** claims from that sentence are removed. When only some are, it **asks the agent to rewrite the sentence** without the removed fact and shows the analyst the diff. A partly removed sentence can't be fixed reliably by code.
- **Open (from the walkthrough):** a third option, **fix**, for `calc_fails`. Recommendation: add it in Phase 1. It is cheap: the agent applies the recomputed value, the claim becomes Derived, and it gets one re-verify.
- **Threshold alarm:** more than 20 Unsupported claims → tell the analyst that citing probably broke, and flag the run for the process owner. Don't make the analyst triage 40 claims.

#### 6.4.8 Acceptance
- [ ] On the test set, tag accuracy ≥ 90% and gap-type accuracy ≥ 85% (to be set from the baseline).
- [ ] 0 fabricated quotes survive into `trace.jsonl`. This is checked by code on every run, so it holds by construction.
- [ ] End-of-chat wait for a 200-claim Solution Intent is ≤ 10 minutes (target to confirm in the prototype; see §7.6).
- [ ] Re-tracing a run gives a new version, and the old one is kept.

### 6.5 Step 5: Report (B12)

Pure code: `trace.jsonl` + `run.json` + `decisions.jsonl` → `knowledge_provenance_report.md` and `metrics.json`.

- The layout follows the walkthrough example exactly: Summary · By section · KB actions · Needs attention · Analyst check · For tech.
- **Golden-file tests:** fixed trace in, byte-identical report out.
- The summary block is also printed in chat for the analyst. That is all the analyst sees (agreed).
- Link every claim to its evidence with relative links into `log.jsonl` line numbers, so "where did this number come from?" is one click in VS Code.

### 6.6 Step 6: Act on the gaps (B15–B18)

Runs weekly, run by the process owner (`/provenance-weekly`), over every shipped run since the last pass.

#### 6.6.1 Intake (code)
Take all trace lines with `kb_action ∈ {add, correct, check}`. Drop Unverified, Derived, User (decision) and removed claims. Kept Unsupported claims (User, confirmed at check) **are included** and flagged `analyst_supplied_no_document`. Separately, write the **tech report**: Never Asked by section, prompt and team, plus retrieval misses. That report is done whatever happens to the candidates.

#### 6.6.2 6a Reusable? (judge)
- Batch about 20 items per call: claim, section, epic summary, and `source_quote`. Output `reusable | run_specific | unsure`, with a reason.
- `unsure` → keep (agreed). Dropped items go to `dropped.jsonl` with the reason, and a 10% sample goes to the process owner each week.

#### 6.6.3 6b Already in the KB? and 6c Where? (search + judge)
- **Needs KB similarity search over the live KB (Q5).** Best: `kh-cli` exposes semantic search with top-k results and scores. Then we reuse the KB's own index and build nothing. If it doesn't, the fallback is an export of the KB and a local embedding index. That is a much bigger build and needs data-handling approval. **Raise this with the Knowledge Hub team before starting Phase 3.**
- Placement tiers 1–3 as agreed: log location → similarity above a threshold (start at 0.75 and tune) → `kb_domains` + judge, marked `new_topic`.
- Code check: every KB entry the judge cites must be in the search results, with its quoted text verbatim.
- Second judgement for **retire** and **correct**. If they disagree → flag `judge_unsure`.

#### 6.6.4 6d Merge across runs (code + judge)
- Code finds open candidates with the same `target.entry_id`, or the same domain for new topics.
- The judge classifies each pair: merge · merge with `sources_disagree` · separate · new.
- Previously rejected and identical → link to the rejection and don't queue it again, **unless** there is new evidence (different source or value) or it recurs more than N times (start at N=3).
- Write the merge history to `candidate.history`.

#### 6.6.5 6e Approver queue: use Jira, not files
The walkthrough leaves the queue's form open. **Recommendation: one Jira issue per candidate**, in a dedicated project or component, assigned to the domain approver from `kb_domains`. Reasons:
- Assignment, notifications, comments, status history and timestamps come built in. Q3 metrics (`routed_at`, `decided_at`) come straight from the Jira history.
- The plugin already wraps Jira through `common-plugin` CLIs, so there's nothing new to integrate.
- Approvers already live in Jira. A new tool for a weekly queue would hurt adoption.
- Map actions to Jira transitions: Approve · Edit (approve with the edited text in a field) · Reject (+ reason, required) · Retire · Re-route (reassign, plus a domain field). The card body is the walkthrough's card layout.

Fallback with no Jira project: one markdown file per domain per week in the shared store, with a checkbox per action. This works for a pilot but makes time-to-fix measurement manual.

#### 6.6.6 6f Ingest
- **We do not own the KB write path (Q6).** Three ways it could work, best first:
  1. KH exposes a versioned write API → `prov ingest` calls it and records `kb_version_after`.
  2. KH is fed from source documents or a repo (for example Confluence or Bitbucket) → ingest is a PR or page edit to the source, and `ingested_at` is when it was merged or re-indexed.
  3. Manual: the approved change goes to the KH content owners as a ticket → `ingested_at` is when they close it.
- Whichever it is, **time to fix ends at `ingested_at`, not at approval.** The pitch's 21 → 9 days measures the whole loop. If ingest is manual, the number will mostly measure the KH team's queue. Say that openly in the metrics notes.
- **Retire** needs KH support for marking an entry inactive, so retrieval stops returning it. If KH can't do that, "retire" becomes "correct the stale entry with a pointer to the current one", and we should say that's weaker.

#### 6.6.7 Acceptance
- [ ] Dedup judge accuracy is measured on test pairs (known duplicates and non-duplicates) before go-live.
- [ ] No candidate reaches Jira without verified evidence quotes.
- [ ] Nothing is written to the KB without an approver action recorded on the candidate.

### 6.7 Result: metrics (B20)

Pure code over every `metrics.json` plus the candidate store.

- Definitions and formulas exactly as in the walkthrough's Step 7 tables. **Put each formula in one metrics module in the `prov` CLI, with unit tests**, and point the dashboard and the reports at it. Two implementations of "KB used rate" will drift.
- Weekly rollup = **the average of each Solution Intent's shares** (agreed), not pooled. Store both, because the pooled number is useful for checking.
- Q3 reads candidates (Jira history). Q4 reads run headers.
- Behind-the-scenes metrics: judge override rate, Unverified rate, autocorrect rate (§6.4.4), wrapper bypass rate, and how the transcript was captured.
- **Output:** `weekly/<yyyy-ww>.md` in the shared store, with the four headline numbers on top. A dashboard comes later, once someone actually asks for it.
- **Baseline first:** the first 3–4 weeks have no targets (agreed). Put that note at the top of the report so nobody reads week-1 numbers as failure.

---

## 7. LLM design

### 7.1 Agents

| Agent | Step | Sees | Doesn't see | Tools | Output |
|---|---|---|---|---|---|
| Drafter (existing PDLC) | run | Everything in the run | — | `prov kb`, `prov read`, existing skills | `final.md` with citations |
| Splitter | 3 | `final.md` section | Log, transcript, sources | none | claims JSON |
| Checker | 4 | Section packet | Drafting conversation, first-run answer (on second runs) | read-only grep over sidecars | verdict JSON |
| Judge | 6 | Candidate, evidence, KB search results, `kb_domains` | The run's chat | `prov kb-search` (read-only) | decision JSON + proposed text |

### 7.2 Structured output
Every agent returns **JSON only**, validated against a schema in code. If validation fails, retry once with the validation error appended. If it fails again, mark the batch `failed` and continue: claims in a failed check batch become Unverified, never silently Supported.

### 7.3 Prompts are code
Prompts live in the plugin repo under `prompts/prov/`, with version IDs (`s-3`, `c-5`, `j-2`) recorded in `run.json` and on candidates. A prompt change needs a `prov eval` run, with its result in the PR (§11). Without this, metric trends can't be told apart from prompt changes.

### 7.4 Quote check details
Normalisation is defined in §6.4.4. Two more rules:
- Minimum quote length of 3 tokens. An empty or tiny quote ("1.95%") matches too easily. For bare values, the quote must include the value **and** its label from the same row or sentence.
- The quote must come from the **referenced** item, not from anywhere in the run. Checking against the wrong item lets evidence be "borrowed".

### 7.5 Model choice
Use the strongest model Copilot offers for Checker and Judge, because their accuracy is the product. The splitter can use a cheaper one if `prov eval` shows no loss. Record the model ID per run, since a model change resets the baseline.

### 7.6 Volume, latency and cost: do the arithmetic early
For a 200-claim Solution Intent across 8 sections:
- Splitter: 8 calls.
- Checker: about 8–12 calls (per section, batches of about 25).
- Re-checks after failed quote checks: estimate 5% of claims → 1–2 calls.
- Second runs: Wrong Hits (~5%) + low confidence (~10–15%) → about 30–40 claims → 2–3 calls.
- **About 20–25 model calls per run**, mostly parallel if sub-agents run in parallel (see §8.3); otherwise sequential.

Measure this in the prototype against the Copilot premium-request limits the firm has set, and agree a budget per run. If sub-agents can't run in parallel, a sequential 10-minute+ wait at the end of the chat is the most likely reason analysts will skip `/provenance`. **This is the main adoption risk in the build, so test it in Phase 0.**

---

## 8. Copilot / VS Code implementation

### 8.1 What ships in the plugin

```
product-owner-plugin/
  instructions/
    provenance-drafting.instructions.md     B3 + B4: cite rules, prov kb / prov read only, prov init first
  prompts/
    provenance.prompt.md                    /provenance: Steps 2–5 orchestrator (B13)
    provenance-weekly.prompt.md             /provenance-weekly: Step 6 + metrics (process owner)
  prompts/prov/                             internal prompt bodies, versioned
    splitter.md   checker.md   judge-reusable.md   judge-dedup.md   judge-merge.md
  scripts/prov/                             the `prov` CLI (Python or PowerShell; see Q1)
    prov(.py|.ps1)  extractors/  metrics.py  schemas/
  config/
    kb_domains.yaml                         B18 (or pulled from a shared source)
  tests/prov/                               fixtures, golden reports, eval set
```

Use the plugin's existing conventions for where instructions, prompts and scripts go. The tree above shows the logical parts, not exact paths.

### 8.2 Drafting instructions (B3): the essentials
- First action each session: `prov init` (or `--resume`).
- Query the KB **only** with `prov kb "<q>" --section <current section>`. Read `sources/` **only** with `prov read`. Before reading a Confluence page, save it into `sources/`.
- Draft **section by section**. After every factual sentence, add exactly one `<!-- cite: … -->`, using the `cite as:` string the wrapper returned.
- Analyst facts: quote the analyst's own words briefly. Never cite your own earlier message.
- Derived: cite the inputs and add `; calc`.
- Your own knowledge: `none (general knowledge)`. Nothing at all: `none`. **Never invent a citation.** An honest `none` is the correct answer, not a failure.
- Keep the plugin's existing `[Confident]/[Plausible]/[Verify]` tags as they are. Citations are separate.

### 8.3 Fresh context and parallelism
- **Splitter, checker and judge must not run in the drafting thread** (P6). Options, best first:
  1. **Sub-agents** started from the `/provenance` prompt. Each gets a fresh context, and they may run in parallel. *To verify (Q4): VS Code Copilot's current sub-agent support, whether sub-agents can run in parallel, whether each sub-agent's tools can be limited, and whether the results come back as text the orchestrator can pass to `prov verify`.*
  2. **A new chat session** for `/provenance`. This gives a fresh context but runs sequentially. The analyst opens it at the end of the chat and stays until it finishes.
  3. **Batch mode outside chat:** only possible if a firm-approved model API exists. Not assumed: Copilot is the only LLM runtime (§2).
- In every option, **the scripts carry the state, not the chat**. The orchestrator prompt is a thin loop: call `prov context`, hand off to the sub-agent, save its JSON to `checks/`, call `prov verify`. If the chat dies halfway, `/provenance` resumes from `run.json` state.

### 8.4 Terminal auto-approve
`prov kb` and `prov read` run on almost every turn. They must be on the terminal **auto-approve** allowlist, or the analyst will be clicking "Allow" all day. The plugin already sets auto-approve rules. Add `prov` read-only subcommands there, and keep `prov publish` and `prov ship` approval-gated.

---

## 9. Shared store (Plane C)

Steps 6–7 need every analyst's runs in one place.

| Option | Good | Bad | When |
|---|---|---|---|
| **A. Bitbucket repo `kp-runs`** (one folder per run; `prov ship` commits and pushes the bundle) | Versioned, auditable, uses existing access control, no new infra, diffable | Git isn't a database; grows over time; PII in transcripts lives in git history forever | **Pilot (Phases 2–3)** |
| B. Shared network drive | Simplest | No audit trail, weak access control, easy to corrupt | Avoid |
| C. Small service + DB (runs, claims, candidates tables) | Queryable, a dashboard is easy, retention can be enforced | Needs a team to build and run it, plus a security review | **Scale (Phase 4+)**, once the pilot has proven the value |

**Recommendation:** use A, with two safeguards:
1. **Ship only what Plane C needs**: `run.json`, `trace.jsonl`, `metrics.json`, `decisions.jsonl`, and the `log.jsonl` lines referenced by KB actions. **Keep the full transcript on the analyst's machine** unless policy allows otherwise. The evidence quotes in the trace carry the necessary excerpts. This avoids copying every chat into a repo.
2. **Candidates live in Jira** (§6.6.5), not in the repo. The repo holds runs; Jira holds the queue.

---

## 10. Security, privacy and governance

- **Data classification.** Transcripts and `sources/` can hold confidential initiative data and may include client information. Treat the run folder like the Solution Intent itself. The shared store needs the same or stricter access control as the PDLC outputs. *Q7: ask Data Governance about retention and classification before Phase 2.*
- **Never trust content as instructions.** KB chunks, `sources/` files and transcripts are passed to the checker and judge **as data**. A source doc containing "ignore previous instructions" must not change a verdict. Put all evidence inside delimited blocks, and tell agents to treat it as quoted material. The quote-verbatim code check also limits the damage.
- **KB write integrity.** Only the ingest step writes to the KB, only for candidates with an approver decision recorded, and with the approver's identity attached. An analyst-only correction (`analyst_supplied_no_document`) can never be approved without an edit or a source link. Enforce that as a Jira validation rule.
- **Audit.** For any KB change, you can go back from the KB version → candidate → evidence quotes → runs → log lines → the original file and location. Test this chain end to end (§11).
- **People.** Analyst IDs are stored for Q4 (teams), but reports group by team. No per-analyst views (P8).

---

## 11. Quality and evaluation

| Asset | What | Used for |
|---|---|---|
| **Claim test set** (B19) | 20–30 hand-labelled claims to start, from real runs. Each has its sentence, its expected claims, tag, gap type and KB action. Must include borderline fact/intent sentences, debit-vs-credit near-misses, derived calcs (good and bad), decisions, and silence-isn't-agreement. | `prov eval` on every prompt or model change |
| **Golden runs** | 2–3 full run folders frozen as fixtures, with the expected `trace.jsonl` and report | End-to-end regression, report golden files |
| **Dedup pairs** | 20+ known duplicate and non-duplicate KB pairs | Step 6 judge accuracy |
| **Extractor fixtures** | One file per type with known quotes | Quote check round trip |
| **Unit tests** | Citation parser, normalisation, gap/action consistency rules, every metric formula | Every commit |

`prov eval` prints: splitter precision/recall, tag accuracy, gap-type accuracy, KB-action accuracy, Unverified rate, and the cost (number of calls). Store the history so the process owner can see whether a prompt change helped.

Grow the test set from production. Every Unverified claim the process owner reviews and every approver override is a candidate for a new labelled case. This is the cheapest way to keep the checker honest.

---

## 12. Rollout

### Phase 0: Prototype (agreed in the walkthrough)
**Build:** B1, B3, B4, a manual chat export, and a hand-run Steps 3–4 (one prompt plus a minimal `prov verify`).
**Run:** one real PDLC run.
**Measure:** citation coverage; citation pass rate; wrapper bypass rate; where citing slipped; **plus** whether the KB CLI returns IDs (Q2), what the chat export contains (Q3), sub-agent parallelism (Q4), and how long the end of the chat takes (§7.6).
**Exit:** decide on B8, on whether B2 is enough, and on Python vs PowerShell. Go or no-go for Phase 1.

### Phase 1: Per-run provenance (Steps 1–5)
**Build:** the full `prov` CLI for Planes A and B, `/provenance`, the splitter and checker, the analyst check, the report, the publish gate, and the test set with `prov eval`.
**Pilot:** 1–2 teams, about 10 runs.
**Exit:** fact/intent recall ≥ 0.95, tag accuracy ≥ 90%, zero fabricated quotes, end-of-chat wait acceptable to analysts (ask them), and Unsupported per Solution Intent in the 0–5 range.

### Phase 2: Shared store and metrics v1
**Build:** `prov ship`, the `kp-runs` repo, the weekly rollup (Q1, Q2 and Q4; Q3 needs Phase 3), and the tech report.
**Exit:** 3–4 baseline weeks recorded. Tech has acted on at least one Never Asked finding.

### Phase 3: The KB loop (Step 6 up to the approver)
**Needs:** KB similarity search (Q5), `kb_domains`, named approvers, and a Jira project.
**Build:** 6a–6e, judge prompts, dedup test pairs.
**Exit:** approvers clear the weekly queue. Judge override rate measured. Q3 time-to-fix measured, even if ingest is still manual.

### Phase 4: Ingest and scale
**Needs:** the KH write path (Q6).
**Build:** `prov ingest`, retire support, and possibly Option C storage and a dashboard.

**Why this order:** each phase is worth something even if the next one stalls. Phase 1 alone catches made-up content before publish (Q1 in the pitch). Phase 2 alone shows where the KB is failing (Q2, Q4). Phase 3 needs the Knowledge Hub team, so don't let it block anything earlier.

---

## 13. Risks and open questions

### 13.1 Risks, most serious first

| # | Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|---|
| R1 | **The end-of-chat wait is too long**, so analysts skip `/provenance` | Med-High | Kills adoption, and with it every metric | Parallel sub-agents; per-section batches; measure in Phase 0; trace sections in the background as each one is finalised (later) |
| R2 | **The drafter's citations degrade over long runs** | High | More Unsupported claims, and a noisy analyst check | Cite section by section; `cite as:` strings from the wrapper; B8 section check; search fallback in 4C |
| R3 | **KB evidence is lost** because the agent reaches the KB without `prov kb` | Med | Gap types are wrong, with no recovery | Instruction plus tool allowlist; flag KB citations with no log line; measure in Phase 0 |
| R4 | **The chat export lacks roles, timestamps or multi-session support** | Med | Weak User evidence, no turn join | Self-logged fallback marked low confidence; storage-file spike; ordering by `seq` |
| R5 | **No KB similarity search or write API** from the Knowledge Hub team | Med | Phases 3 and 4 stall | Raise in week 1; Phases 1–2 still deliver value; local index only with data approval |
| R6 | **The checker is confidently wrong in a consistent way** (two runs agree on a wrong answer) | Med | Wrong KB corrections reach approvers | Approver gate; test set; judge second opinion on corrections; KB upheld share metric |
| R7 | **Approver fatigue or rubber-stamping** | Med | Bad KB changes, or a backlog | ~2 candidates per run (agreed estimate); merge across runs; backlog metric; watch upheld share near 0% |
| R8 | **Quotes from binary sources fail verification** because extractors differ | Med | False Unsupported claims | One canonical extractor shared by wrapper and verifier (§6.1.3); fixture tests |
| R9 | **The splitter's claim count varies between runs** | High (small) | Noisy metrics | Weekly trends, not exact numbers (agreed); prompt versioning |
| R10 | **Confidential data ends up in the shared store** | Low-Med | Compliance | Ship the trace, not transcripts; Data Governance review before Phase 2 |

### 13.2 Open questions for tech and partner teams

| # | Question | Owner | Blocks |
|---|---|---|---|
| Q1 | Is Python 3 available on the VDI, with openpyxl (xlsx) and a PDF library? If not, is PowerShell 7 fine as the runtime? | VDI / platform | Phase 0 |
| Q2 | Does `mct_knowledge-hub` CLI return chunk IDs, locations, scores and full chunk text? Does it have a machine-readable (JSON) output mode? | Knowledge Hub team | Phase 0 (**blocker**) |
| Q3 | What does VS Code's chat export contain: roles, timestamps, tool calls, multiple sessions? Can it be scripted? | Us (spike) | Phase 0 |
| Q4 | Copilot sub-agents: fresh context? parallel? per-agent tool limits? | Us (spike) | Phase 1 design |
| Q5 | Can `kh-cli` do top-k semantic search over the live KB, for dedup? | Knowledge Hub team | Phase 3 |
| Q6 | How does content get into the KB today: API, source-document re-index, or manual? Is there versioning? Can an entry be marked inactive? | Knowledge Hub team | Phase 4 |
| Q7 | Retention and classification rules for run folders, transcripts and the shared store | Data Governance | Phase 2 |
| Q8 | Is there a Jira project we can use for the approver queue, and who are the domain approvers? | Process owner | Phase 3 |
| Q9 | What are the Copilot premium-request limits per user? Is there an org budget? | Platform | Phase 0 (measure) |
| Q10 | Which PDLC stages produce the Solution Intent, and where is `final.md` written? | Plugin owner | Phase 1 |

### 13.3 Decisions this spec proposes (to agree)

| # | Decision | Recommendation |
|---|---|---|
| D-1 | One `prov` CLI with subcommands | Yes (§3.3) |
| D-2 | Turn numbers filled in after the run, not by the wrapper | Yes (§6.1.4) |
| D-3 | Canonical text sidecars for `sources/`, used by both wrapper and verifier | Yes (§6.1.3) |
| D-4 | Citations accept SRC-IDs from `SOURCES.md` as well as paths | Yes, to match the plugin's existing Sources Discipline (§2) |
| D-5 | Self-logged transcript ⇒ User evidence at low confidence | Yes (§6.2) |
| D-6 | Approver queue in Jira | Yes (§6.6.5) |
| D-7 | Pilot shared store = Bitbucket repo; transcripts stay local | Yes (§9) |
| D-8 | Add the "fix" option for failed calculations in Phase 1 | Yes (§6.4.7) |
| D-9 | Keep `missing_piece` separate from `no_hit` in the data | Yes (§5.8) |
| D-10 | Run state machine in `run.json`; all scripts check state | Yes (§5.2) |

### 13.4 Deliberately out of scope (as agreed in the walkthrough)
- Topic-matching fix for gap typing
- Spot-check sample of Used claims
- Volatile-topics cross-check rule
- Tracing the Epic (Solution Intent only for now)
- Tracing edits made after publish in Confluence or Jira (known limit)

The data model keeps room for each of these: claims carry `section` and `para`, and the trace is versioned. Nothing here needs to change to add them later.
