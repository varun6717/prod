# Knowledge Provenance — Walkthrough (decisions by step)

PDLC Neuro · Evergreen Knowledge Base Loop. Each step below records what we agreed in the step-by-step walkthrough. Steps are added as we go. Where this differs from `knowledge_provenance_process_v0.2.md`, this file wins. Structure follows `Knowledge_Provenance/neuro_knowledge_provenance_process.md` (7 steps, claim-level tracing) with the amendments agreed here.

Running example: run `r-2026-10-27-0412` · epic EP-2210 · KB snapshot `kb-2026-10-20` · sections Scope, Solution, Timeline, Risks.

Legend: **KB** = green · **Local** (`sources/`) = amber · **User** = blue. **Unsupported** = red, hatched (distinct from the red No Hit badge). **Derived** is kept as data but not shown in presentation/management charts.

| Step | What happens | Status |
|---|---|---|
| 1 | Log every knowledge read during the run | Agreed |
| 2 | Collect the run into one folder | Agreed |
| 3 | Break the Solution Intent into claims | Agreed |
| 4 | Trace each claim to its source | Agreed |
| 5 | Write the provenance report | Agreed |
| 6 | Act on the tags (fix, route, add to KB) | Agreed |
| 7 | Compute metrics | Agreed |

---

## Step 1 — Log every knowledge read during the run

### What it is
One wrapper sits in front of the only two places the assistant reads knowledge from:
- the **KB command-line tool**
- the **`sources/` folder**

Every source goes through `sources/`, including ones found on the fly (e.g. a Confluence page is saved into `sources/` before use), so nothing is read without being logged. `sources.md` is the assistant's citation list. It is **not** part of the log.

### Run header (written once)

| Field | Example |
|---|---|
| Run ID | r-2026-10-27-0412 |
| Epic · domain | EP-2210 · (domain) |
| Analyst | (analyst ID) |
| Assistant version | (version) |
| Start / end | timestamps |
| KB snapshot | kb-2026-10-20 |
| Sections | Scope, Solution, Timeline, Risks |

### Event lines (two types only)
Each line records what the assistant sent to the KB or `sources/` and what came back.

| Event | Fields | Result |
|---|---|---|
| `kb_query` | section, turn, query text, chunk IDs, location (KB domain/section), chunk text | `hit` / `no_hit` |
| `source_read` | section, turn, file path + location (sheet/row, §, lines), excerpt text, version or modified date | `found` / `not_found` |

- Failed reads are logged too. The query or search term is what matters there.
- The text that came back is stored because later steps compare it with what the Solution Intent used.

### Automatic rerun
When a `kb_query` returns `no_hit`, the wrapper retries once with a reworded query. Both lines are logged; the second is marked `rerun_of`. If the rerun hits, it's a **retrieval miss**, not a KB gap.

### Turn numbers
- Turn numbers are one counter across the whole chat. Every message (assistant or analyst) takes the next number. That numbering lives in the **transcript** (Step 2).
- Log lines carry the turn number of the **assistant message that made the read**. Analyst messages never appear in the log.
- The log therefore skips turns: those are analyst messages, or assistant messages that read nothing.

```
Transcript                              Log
t13  analyst    "Start on Scope…"       —
t14  assistant  "KB has 1.80%…"     ◄── t14 kb_query … / t14 source_read …
t15  analyst    "Go with the sheet"     —
```

### Example log

```
run r-2026-10-27-0412 · EP-2210 · (domain) · KB kb-2026-10-20 · sections: Scope, Solution, Timeline, Risks

Scope     t14  kb_query     "CNP interchange tiers" → ic-0412 · KB Payments/Pricing          hit        "Standard 1.80% + $0.10 …"
Scope     t14  source_read  sources/interchange_2026.xlsx · CNP!A4:D4 · mod 2026-10-24       found      "Card-not-present | Standard | 1.95% | $0.10"
Solution  t21  kb_query     "3DS step-up rule CNP" → auth-0071 · KB Payments/Auth            hit        "Step-up required for CNP > $250 …"
Timeline  t27  kb_query     "mandate effective date" → —                                     no_hit
Timeline  t27  kb_query     "scheme mandate go-live dates" (rerun_of t27) → —                no_hit
Timeline  t27  source_read  search sources/ "mandate effective date" → —                     not_found
Risks     t33  source_read  sources/chargeback_monitoring.md (Confluence v12) · §4           found      "Scheme threshold: 0.9% dispute ratio …"
```

Turn 28 (analyst types the mandate dates) and turn 34 (analyst adds dispute volume) appear only in the transcript.

### What Step 1 does NOT do
- No analyst input (that's the transcript).
- No judgements: no tags, no gap types, no Never Asked, no conflict detection.
- No `sources.md` check (later step).

### To confirm with tech
- Does the KB command-line tool return chunk IDs and locations?
- Can the wrapper intercept reads from `sources/`?

---

## Step 2 — Collect the run into one folder

### What it is
At the end of the run, everything later steps need is gathered under the run ID. Automatic; no analyst action.

```
runs/r-2026-10-27-0412/
  log.jsonl          ← Step 1, already written live during the run
  transcript.jsonl   ← every message: turn, timestamp, role, verbatim text
  final.md           ← Solution Intent + Epic by section, with the assistant's inline citations
  sources.md         ← the assistant's citation list
```

### One job per file

| File | Holds | Used later for |
|---|---|---|
| `log` | What the assistant sent to the KB / `sources/` and what came back | `source_quote` and `kb_quote` for KB and Local claims; gap type |
| `transcript` | Every message, numbered (system of record for turn numbers) | `source_quote` for User claims |
| `final` | The finished output and its inline citations (not yet split into claims — that's Step 3) | What gets checked |
| `sources.md` | The assistant's human-readable citation list | Kept for people; **not** used in the checks (inline citations cover that). Optionally generated from the inline citations so the two can't disagree. |

- The log and the transcript don't duplicate each other. The log holds reads only; the transcript holds messages only. They join on turn number.
- In the transcript, **only analyst messages** count as a source (tag **User**). Assistant messages are context only; a claim that traces back only to something the assistant said is **Unsupported**.
- **Analyst uploads** are saved into `sources/` and read through the wrapper, so they're logged and tagged **Local**. Typed or pasted text stays in the transcript and is tagged **User**.

### When each file is created

| File | Created |
|---|---|
| `log` | During the run (Step 1 wrapper) |
| `transcript` | At run end, by exporting the chat. **Fallback:** the assistant writes each message to `transcript.jsonl` as the run goes. |
| `final` | At export/publish from the chat |
| `sources.md` | By the assistant during the run |

### Example `final.md` (excerpt)

```
## Scope
CNP Standard tier: 1.95% + $0.10 per transaction  <!-- cite: sources/interchange_2026.xlsx · CNP!A4:D4 -->

## Timeline
Phase 1 go-live: 1 March 2027                     <!-- cite: analyst "Phase 1: 2027-03-01" -->
Phase 2 go-live: 1 September 2027                 <!-- cite: analyst "Phase 2: 2027-09-01" -->
```

Citations are kept in `final.md` and stripped from the published `solution_intent.md` (B5). Analyst citations are short quotes; Step 4 maps them to turn numbers.

### Decisions
1. **"Final"** is snapshotted when the analyst exports/publishes from the chat, after any Unsupported check. Later edits in Confluence/Jira aren't traced (known limit).
2. **One run ID per epic.** Turn numbers continue across chat sessions; each session start is recorded in the header.
3. **Environment: VS Code (Copilot Chat).** To verify: chat export includes message order, roles and timestamps; the KB CLI can be wrapped by a script; reads from `sources/` can be routed through the wrapper (e.g. instructions require reading sources only via a wrapper script). Use the fallback wherever VS Code can't do it.

## Step 3 — Break the Solution Intent into claims

### What it is
A **splitting agent** goes through `final.md` section by section, sentence by sentence. For each sentence it asks "is this stated as fact?" If yes, it splits it into one-fact claims; each claim keeps the sentence's citation (or `none`). It does **not** check whether a claim is supported — that's Step 4.

- **Scope: Solution Intent only.** The Epic is largely a translation of the Solution Intent; extend to the Epic later if needed.
- **Input:** `final.md` (Solution Intent with hidden per-sentence citations).
- **Output:** `claims.jsonl` — one line per claim: ID, section, claim text, citation (or `none`).

### Citations arriving from drafting
The drafter cites all three source types as it writes (B3/B4):

| Fact came from | Citation | Cited text later comes from |
|---|---|---|
| KB | `<!-- cite: KB ic-0412 -->` | Log |
| `sources/` file | `<!-- cite: sources/<file> · <location> -->` | Log excerpt, or the file in `sources/` if the read bypassed the wrapper |
| Analyst | `<!-- cite: analyst "Phase 1: 2027-03-01" -->` | Transcript (Step 4 maps the quote to its turn) |
| Derived (worked out from sourced inputs) | `<!-- cite: derived from <inputs> ; calc -->` | The inputs' sources |
| Assistant's general knowledge | `<!-- cite: none (general knowledge) -->` | Nothing — not a source |
| No source at all | `<!-- cite: none -->` | Nothing |

**Only four things count as sources:** KB retrieval, `sources/` files, the analyst, and derivation from those. The assistant's own messages and general knowledge are **not** sources — the assistant's words in the transcript can't be checked. Marking general knowledge honestly (`none (general knowledge)`) tells the analyst "the assistant knowingly used its own knowledge" rather than "a citation went missing", and shows over time how much the assistant relies on it.

The Solution Intent arrives **mostly** cited, but not fully: the drafter may write an honest `none`, forget, cover only part of a sentence, or make something up. That's why Step 3 decides what's a claim **from the sentence itself, not from whether it has a citation**.

### What counts as a claim
**Definition:** a claim is a sentence (or part of one) that **should** have a source — something stated as true where someone could fairly ask "says who?". Whether it actually **has** a source is Step 4's question. (If a claim were defined as "something we can assign a source to", made-up content would never become a claim and would never be checked.)

Rule given to the splitter (in its prompt):

> **A claim** states something as true about the world: a number, date, rule, current state, cause, comparison, dependency, or a decision taken.
> **Not a claim:** goals and intent ("will help", "aims to", "is designed to"), headings, transitions, and sentences that only repeat an earlier claim.
> **Test:** if this sentence were false, would the Solution Intent be wrong? If yes, it's a claim.
> **When unsure, make it a claim.** (Worst case: one extra "keep or remove?" for the analyst.)

Why this broad rule (not "values only"): anything that isn't a claim is never checked. A values-only rule would skip general assertions like "Competitors already offer frictionless 3DS" — if made up, they'd go into the published Solution Intent unexamined.

| Sentence | Result | Why |
|---|---|---|
| "Competitors already offer frictionless 3DS." | Claim | Current state; if false, the Solution Intent misleads |
| "We will apply step-up for CNP over $250." | Claim | Decision taken |
| "This initiative will help merchants stay compliant." | Not a claim | Intent |
| "…which is critical to retaining our largest clients." | Claim | Asserts a dependency |

A sentence that mixes intent and fact keeps only the fact part.

### Splitting rules
- **One fact per claim** (one name, number, date, rule or decision). "1.95% + $0.10" is two claims — rate and fee — because each can be right or wrong on its own (the KB was wrong on the rate, right on the fee).
- Each claim inherits its sentence's citation. A sentence with two citations: the splitter assigns the right one to each claim, or carries both for Step 4 to resolve. No citation: `none`.

### Who and when
- A **separate agent**, not the drafter, in a fresh context with no memory of the drafting conversation.
- Runs **once at the end** over the whole Solution Intent (sections get revised during the chat, so splitting early wastes work).
- In VS Code: a separate prompt/command (e.g. a `/provenance` prompt file) run when the Solution Intent is done. The same command continues into Step 4.
- Steps 3 and 4 run **at the end of the chat, before publish**, so Unsupported claims can go to the analyst while they're still in the session.

### Example (Business Overview)

```
## Business Overview
Merchant Services processes card-not-present (CNP) payments for ~38,000 e-commerce
merchants, with CNP representing 62% of transaction volume in 2025.
  <!-- cite: sources/merchant_portfolio_2025.xlsx · Summary!B2:B3 -->
The upcoming card scheme mandate requires stronger authentication on CNP transactions,
with Phase 1 taking effect on 1 March 2027.
  <!-- cite: analyst "Phase 1: 2027-03-01" -->
Merchants exceeding a 0.9% dispute ratio enter the scheme's monitoring program and face
monthly fines.
  <!-- cite: sources/chargeback_monitoring.md §4 -->
This initiative will help merchants stay compliant while protecting approval rates,
which is critical to retaining our largest e-commerce clients.
```

| ID | Claim | Citation |
|---|---|---|
| C-10 | ~38,000 e-commerce merchants on CNP | merchant_portfolio_2025.xlsx Summary!B2 |
| C-11 | CNP was 62% of transaction volume in 2025 | merchant_portfolio_2025.xlsx Summary!B3 |
| C-12 | The scheme mandate requires stronger authentication on CNP | analyst "Phase 1: 2027-03-01" |
| C-13 | Mandate Phase 1 takes effect 2027-03-01 | analyst "Phase 1: 2027-03-01" |
| C-14 | Merchants over a 0.9% dispute ratio enter the monitoring program | chargeback_monitoring.md §4 |
| C-15 | Merchants in the monitoring program face monthly fines | chargeback_monitoring.md §4 |
| C-16 | Large e-commerce clients' retention depends on approval rates | `none` |

"This initiative will help merchants stay compliant" is intent → skipped.

### What Step 3 does NOT do
No support check, no tags, no gap types. All of that is Step 4.

## Step 4 — Trace each claim to its source

### What it is
Takes every claim from Step 3 (cited or not) and gives it a **tag** (where it came from), a **gap type** (what the KB did on that topic) and a **KB action**, with the quotes as evidence.

- **Input:** `claims.jsonl` (Step 3) plus the full source text saved during the run: `log.jsonl` (KB chunks, `sources/` excerpts), `transcript.jsonl` (analyst messages), the `sources/` files and manifest.
- **Who:** a **checking agent** — separate from the drafter, fresh context — one claim at a time, plus two simple code checks.
- **Output:** `trace.jsonl`, one line per claim.
- Step 4 **never re-queries the KB**. It judges what the assistant saw during the run, from the log.

### For each claim

**A. Find the cited text (code)**
- KB citation → that chunk in the log.
- `sources/` citation → that excerpt in the log, or the file in `sources/` if the read wasn't logged (the manifest confirms the file existed).
- Analyst citation (short quote) → found in the transcript's **analyst** messages; record the turn number (e.g. t28).
- Not found, cites an assistant message, or no citation → go to C.

**B. Check the claim against the cited text (agent, then code)**
- The agent reads the claim and the **full** cited text and picks out the part that supports the claim: the **`source_quote`**. Support is judged on **meaning** — the Solution Intent may reword or summarize.
- Code confirms the `source_quote` is an exact piece of the full text (ignoring spacing, line breaks, capitals), so the evidence is real, not invented.
- **Supported** = both pass. Tag the claim from where its `source_quote` was found. Go to D.
- Either fails → go to C.

| `source_quote` found in | Claim tagged |
|---|---|
| A KB chunk (log) | **KB** |
| A `sources/` file (log excerpt or the file) | **Local** |
| An analyst message (transcript) | **User** — marked **fact** (something true the analyst supplied) or **decision** (a choice the analyst made or agreed to) |
| Worked out from other supported claims (see Derived below) | **Derived** |
| Nowhere | **Unsupported** |

One tag per claim. The citation sets the tag if it holds up; if it's missing or fails, the search in C finds the source and that sets the tag. Other sources that agree don't add tags — the KB's agreement shows up in the gap type and `kb_quote`. Two outcomes that aren't sources: **Unverified** (second run disagreed, see E) and **User (confirmed at check)** (an Unsupported claim the analyst chose to keep).

**Unsupported sub-labels.** A claim cited `none (general knowledge)` still goes through the search in C (it may turn out to be in the log or transcript, and then it's tagged normally). If nothing is found it is **Unsupported (general knowledge)**; otherwise plain **Unsupported**. Same handling — the label just helps the analyst decide and feeds the metrics.

Unsupported means **unsourced**, which covers two kinds: **made up** (hallucination) and **true but not in this run's record** (something the analyst knows but never typed, or general knowledge the assistant brought in that happens to be right). The analyst's answer separates them: **removed** is the best measure of hallucinations caught before publish; **kept** is mostly true-but-unsourced.

**C. Search — no citation, or the citation failed (agent)**
- Search in order: the section's log → the whole-run log → the `sources/` files → analyst messages.
- Found → pick `source_quote`, run the code check, tag it, go to D.
- Nothing found → **Unsupported**.

**D. Gap type and KB action (agent)**
Every claim, whatever its tag, is compared with the KB activity **in the log** on the same topic — that section first, then the whole run. KB activity on the topic anywhere in the run counts as "asked". A "hit" means the KB returned a chunk on that topic; that chunk can still agree, lack this piece, or contradict.

| KB activity on this topic | Gap type | `kb_action` | `kb_quote` |
|---|---|---|---|
| Hit, and the claim came from it (tag KB) | Fully answered | none | — (KB text is already the `source_quote`) |
| Hit with the **same** info (claim tagged Local/User) | Fully answered (KB corroborated) | none | Yes |
| Hit, but **missing this piece** | No Hit | **add** (to that entry) | Yes — shows where to add |
| Hit with **different** info (claim tagged Local/User) | **Wrong Hit** | **correct** | Yes — shows what to correct |
| No hit, but the automatic **rerun** hit and the claim used it | Fully answered, flagged **retrieval miss** | none | — |
| Queried, **nothing returned** | No Hit | **add** | — |
| **Never queried** | Never Asked | **check** (does the KB have it?) + report to tech | — |
| Claim is **Unsupported** | — | none | — |

**`kb_quote` rule:** filled whenever the KB returned something on the topic and the claim was **not** taken from the KB.

Examples of "hit" cases:
- Same: claim "fee $0.10"; KB "Standard 1.80% + **$0.10**".
- Missing piece: claim "Commercial tier 2.40%"; KB "Standard 1.80% + $0.10; Premium 2.10% + $0.10" (no Commercial).
- Different: claim "Standard rate 1.95%"; KB "Standard **1.80%** + $0.10".

`kb_action` = add / correct / check marks a **potential** candidate only. Step 6 applies the reusability filter and the dedup check before anything reaches an approver. Nothing goes into the KB automatically.

**E. Confidence**
- The agent rates its **whole answer** for the claim (tag, `source_quote`, `kb_quote`, gap type, KB action) **high** or **low**. The judgement-heavy parts are the tag (does this quote really support the claim?) and the gap type (same topic? does it agree?).
- It says low when: the topic match was borderline; the claim is a loose summary the quote only partly covers; a derived calculation involved rounding or assumptions.
- For a **Wrong Hit**, the rating asks: is the KB chunk about exactly the same thing (e.g. not debit vs credit)? Is it a real contradiction, or could context explain it (net vs gross, region, effective period)? Does the `source_quote` plainly support the claim? Example — high: KB "Standard 1.80% (2025 schedule)" vs sheet "1.95%, effective 2026-01-01". Low: KB "1.80% for **debit** CNP" vs sheet "1.95% for **credit** CNP" — may really be a missing piece, not a contradiction.
- **Second run** — a fresh agent that hasn't seen the first answer — for every **Wrong Hit** (it leads to a KB correction) and every **low-confidence** answer. Run once more only, never in a loop.
  - Agree → keep the answer (Wrong Hits/low answers marked "2 runs agree"; low ones stay flagged **borderline**).
  - Disagree → **Unverified**. Nobody is asked.
- **Test set:** 20–30 hand-labelled claims from real runs (including borderline fact/intent sentences for Step 3). Rerun the splitter and checking agent on them whenever a prompt changes and track accuracy. One-time human effort, not per run.

**F. Write to `trace.jsonl`:** claim ID, tag, `source_quote` + where it came from (log line / file / turn), `kb_quote`, gap type, `kb_action`, confidence, reason.

### Derived claims
Some true statements aren't written anywhere: the assistant **worked them out** from sourced facts. Without special handling they'd be false Unsupported alarms.

| Kind | Example | Built from |
|---|---|---|
| Calculated | "At 1.95% + $0.10, a $20 CNP transaction costs $0.49 in interchange." | Arithmetic on C-01, C-02 |
| Inferred | "With Phase 1 on 2027-03-01 and a 4-month build, development must start by Nov 2026." | Logic combining sourced facts |
| Summarized | "Pricing and authentication both change for CNP." | Several sourced claims restated as one |

- **Drafting:** the assistant cites the **inputs** and marks it derived: `<!-- cite: derived from sources/interchange_2026.xlsx CNP!A4:D4 ; calc -->`.
- **Step 3:** carries the citation onto the claim, as usual.
- **Step 4** checks two things:
  1. **Inputs are real** — each input is traced like a normal claim (often it already is its own claim).
  2. **Derivation can be recreated** — the agent redoes the calculation or follows the logic and gets the same result (20 × 1.95% + $0.10 = $0.49 ✓).

| Result | Tag | To analyst? |
|---|---|---|
| Inputs supported and derivation holds | **Derived** (inputs listed) | No |
| An input is Unsupported | **Unsupported** ("input not found") | Yes |
| Derivation fails (e.g. says $0.59) | **Unsupported** ("calculation doesn't hold") | Yes |

- **Gap type:** a derived claim is never a KB candidate (it's run-specific). Its **inputs** carry the gap types — C-01 stays the Wrong Hit; the $0.49 calculation doesn't.

### Decisions agreed in chat → User (decision)
The assistant proposes options, the analyst picks one. The assistant's words aren't a source; the analyst made the decision and stands behind it, so the tag is **User**, marked **decision**.

```
t40  assistant  For rollout, two options: (A) all regions at once on 2027-03-01, or
                (B) phase by region — EU first on 2027-03-01, then US and APAC on 2027-09-01.
t41  analyst    Go with B.
```
Solution Intent: "Rollout will be phased by region: EU first on 1 March 2027, then US and APAC on 1 September 2027." `<!-- cite: analyst "Go with B." ; analyst "Phase 1: 2027-03-01" -->`

- Step 4 finds "Go with B." at t41 and reads it **together with the proposal it answers** (t40). `source_quote` = "Go with B.", context noted ("answering t40, option B").
- C-30 "Rollout is phased by region" → **User (decision)**.
- The dates (C-31, C-32): the agreement supports *choosing* them, but they came from earlier (analyst at t28), and that source drives their gap type. The drafter should cite both; if it cites only the agreement, Step 4's search finds t28.
- **Silence isn't agreement.** If the analyst never chose ("Let's move on to Risks."), the claim is **Unsupported**.

| | User (fact) | User (decision) |
|---|---|---|
| Example | "We're at ~4,200 disputes/month" | "Go with B: phase by region" |
| Knowledge? | Yes — true about the world | No — a choice for this project |
| KB candidate? | Possibly, after the reusability filter | **Never** |
| Counts toward "human fill" (KB gap)? | Yes | **No** |

### Design: how Step 4 runs
- **One subagent per section, run in parallel.** Each gets that section's claims plus the relevant log lines, transcript messages and `sources/` files, and returns a result per claim in a single call. Keeps the end-of-chat wait short for a 150–300 claim Solution Intent.
- **Code checks stay in code:** cited item exists (log / manifest / transcript), and `source_quote` / `kb_quote` appear word for word in their stored text.
- **Second runs** only for Wrong Hits and low-confidence answers, per claim, not per section.

### After all claims are traced
- **Only Unsupported** claims go to the analyst, in one message while they're still in the chat: "These N claims have no source — keep or remove?" Each claim gets its own keep/remove, with keep-all / remove-all shortcuts. It must be answered before publish. Typically 0–5 per Solution Intent; regularly 20+ means drafting or citing is broken. (Unverified and Wrong Hit claims are not sent to the analyst.)
  - **Remove** → taken out of the Solution Intent (before publish).
  - **Keep** → stays in the Solution Intent; tagged **User (confirmed at check)** — the analyst vouches for it. Still counted as originally Unsupported in the metrics. Whether it ever reaches the KB is a separate decision in Step 6.
- Not sent to the analyst: **Wrong Hits** (the Solution Intent already uses the right value — the KB is what's wrong, so they go to the approver in Step 6), **Unverified** claims, **No Hit / Never Asked** (KB issues, not Solution Intent problems).
- Example message:
  ```
  3 claims in the Solution Intent have no source:
    1. Business Overview — "Large e-commerce clients' retention depends on approval rates"
    2. Solution — "Competitors already offer frictionless 3DS"  (general knowledge)
    3. Solution — "At 1.95% a $20 transaction costs $0.59"  (calculation doesn't hold: inputs give $0.49)
  [Keep] / [Remove] per claim · [Keep all] · [Remove all]
  ```
- _Open:_ offer a third option, **fix**, for failed calculations (assistant applies the corrected value; claim becomes Derived)?
- Then the Solution Intent is published (citations stripped, B5) and `trace.jsonl` feeds Step 5.

### Confidence groups at the end of Step 4

| Group | Meaning | Analyst (end of chat) | Report (Step 5) | Approver (Step 6) | Metrics (Step 7) |
|---|---|---|---|---|---|
| **High** | Sure first time, or two runs agreed | Only if Unsupported | Listed normally | KB actions route normally | Counted normally |
| **Low, 2 runs agree** | Borderline but consistent | Only if Unsupported | Listed with a **borderline** flag and the reason | KB actions route **flagged borderline** | Counted, plus a low-confidence count |
| **Unverified** | The two runs disagreed | No | **"Needs attention"** section, showing both runs' answers | **Not routed** — no KB action | **Unverified rate** |

Unverified claims aren't reviewed per run. The **process owner** reviews them in aggregate (e.g. a weekly sample) to find why runs disagree, and fixes the prompts or test set.

### Unsupported vs Unverified

| | **Unsupported** | **Unverified** |
|---|---|---|
| Means | **No source found anywhere** — not just no citation. Uncited claims are searched first (C-07 had no citation but was found at t34 → User). | The agent ran twice and **the runs disagreed** (tag, gap type or both). A source usually exists; we can't trust our verdict on it. |
| What's wrong | The **Solution Intent** may contain something made up | **Our check** couldn't reach a consistent answer |
| Example | C-16 "Large clients' retention depends on approval rates" — nothing anywhere | C-01 — both runs say it came from the xlsx; run 1 says Wrong Hit, run 2 says No Hit (debit vs credit) |
| Who deals with it | **Analyst**, end of chat: keep or remove | **Process owner**, in aggregate: fix the prompts |
| Risk if ignored | Made-up content gets published | A missed KB correction, noisier metrics |

### `source_quote` vs stored source text
- **Stored source text** = the full text captured during the run (Steps 1–2): the whole KB chunk or `sources/` excerpt in the log, the `sources/` file, or the whole analyst message in the transcript.
- **`source_quote`** = the small piece of it the agent picks in Step 4 as evidence. It doesn't exist before Step 4; it's written to `trace.jsonl` and copied forward to the report (Step 5) and KB candidates (Step 6). Same for `kb_quote`.

```
stored source text (log / file / transcript)  ⊃  source_quote  ──supports?──►  claim
          └──── code: exact piece? ────┘                └──── agent: judgement ────┘
```

### Worked example

C-01 "CNP Standard rate is 1.95%", cited `sources/interchange_2026.xlsx · CNP!A4:D4`:

| Step | What happens | Result |
|---|---|---|
| A | Log has a `source_read` of that file/range at t14 | Exists |
| B | Agent picks "Card-not-present \| Standard \| 1.95% \| $0.10" from the excerpt; code confirms it's in the stored text | Supported → **Local** |
| D | Scope log: t14 `kb_query` "CNP interchange tiers" → ic-0412 "Standard 1.80% + $0.10" — same topic, different value | **Wrong Hit**, `kb_action` correct, `kb_quote` "Standard 1.80% + $0.10" |
| E | Wrong Hit → second run agrees | High |

| ID | Claim | Citation | What happened | Tag | Gap type · action |
|---|---|---|---|---|---|
| C-01 | CNP rate 1.95% | xlsx CNP!A4:D4 | Verified; KB said 1.80% | Local | Wrong Hit · correct |
| C-02 | CNP fee $0.10 | xlsx CNP!A4:D4 | Verified; KB also said $0.10 | Local | Fully answered (corroborated) · none |
| C-03 | Step-up for CNP over $250 | KB auth-0071 | Verified in log | KB | Fully answered · none |
| C-13 | Phase 1 go-live 2027-03-01 | analyst "Phase 1: 2027-03-01" | Quote found at t28; log has t27 no_hit + rerun no_hit | User | No Hit · add |
| C-12 | Mandate requires stronger authentication on CNP | analyst "Phase 1: 2027-03-01" | Quote found but doesn't support the claim → search; whole-run log finds auth-0071 "…required under the scheme SCA mandate for CNP" | KB | Fully answered · none (citation corrected) |
| C-11 | CNP was 62% of volume in 2025 | xlsx Summary!B3 | No `source_read` in log (bypassed wrapper); file in manifest → read from `sources/`, supports it | Local | Never Asked · check |
| C-07 | ~4,200 disputes/month | `none` | Search: nothing in log or `sources/`; transcript t34 analyst "we're at ~4,200 disputes/month" | User | Never Asked · check |
| C-16 | Large clients' retention depends on approval rates | `none` | Search: nothing anywhere | — | Unsupported → analyst keep/remove |

## Step 5 — Provenance report

### What it is
A **human-readable view of `trace.jsonl`**, one per run: `runs/<id>/knowledge_provenance_report.md`. Same information, laid out for people: a header from the run, summary counts, claims grouped by section with their evidence quotes, and pulled-out lists (KB actions, Needs attention, analyst check, for tech).

- **Built by code, not an agent.** Every judgement was made in Step 4; Step 5 only formats. Fast, free, always consistent.
- **The analyst's keep/remove answers are written back into `trace.jsonl`** (e.g. C-16 → User (confirmed at check), C-21 → removed), so the `.jsonl` stays the single complete record and the report never contains anything the file doesn't.
- **The report does not feed the metrics.** Steps 5, 6 and 7 all read `trace.jsonl` directly:

```
                 ┌──► Step 5  report       (for people, per run)
trace.jsonl ─────┼──► Step 6  KB actions   (candidates → approvers)
                 └──► Step 7  metrics      (numbers, across runs)
```

The report's summary block and the metrics use the same counts from the same file, so they always agree; the report shows one run, the metrics combine many.

### Who reads it

| Reader | Use |
|---|---|
| Analyst | Summary block only, at the end of the chat (after keep/remove) |
| Process owner | "Needs attention"; audit trail when something is questioned |
| Approvers | Not directly — Step 6 sends candidates; the report is the backing evidence |
| Leadership | Not directly — they see Step 7 metrics across runs |

Its main value is as the **audit trail**: "where did this number come from?" is answered in one click.

### Example (excerpt)

```markdown
# Knowledge Provenance — r-2026-10-27-0412 · EP-2210
KB snapshot kb-2026-10-20 · Analyst (id) · 2026-10-27

## Summary
42 claims
  KB 17 (40%) · Local 11 (26%) · User 8 (19%: 6 fact, 2 decision) · Derived 4 (10%) · Unsupported 2 (5%)
Gap types:   Fully answered 21 · Wrong Hit 2 · No Hit 5 · Never Asked 6
KB actions:  correct 2 · add 5 · check 6
Unsupported: 3 found → analyst kept 1, removed 2
Unverified:  1 · Borderline: 2

## By section
### Scope
| ID   | Claim                      | Tag   | Evidence                                      | KB said                            | Gap                           |
| C-01 | CNP Standard rate is 1.95% | Local | xlsx CNP!A4:D4 — "…Standard | 1.95% | $0.10"  | ic-0412 — "Standard 1.80% + $0.10" | Wrong Hit · correct           |
| C-02 | CNP fee $0.10              | Local | xlsx CNP!A4:D4 — "…$0.10"                     | ic-0412 — "…+ $0.10"               | Fully answered (corroborated) |

## KB actions (→ Step 6)
| ID   | Action  | KB says                          | Source says                       | Flag |
| C-01 | correct | ic-0412 "Standard 1.80% + $0.10" | xlsx "Standard | 1.95%"           |      |
| C-13 | add     | —                                | analyst t28 "Phase 1: 2027-03-01" |      |
| C-11 | check   | — (never asked)                  | portfolio xlsx "62%"              |      |

## Needs attention
C-44  Unverified — run 1: Wrong Hit, run 2: No Hit (debit vs credit). No KB action.

## Analyst check (Unsupported)
C-16  "Large clients' retention depends on approval rates" → kept (User, confirmed at check)
C-21  "Competitors already offer frictionless 3DS"         → removed

## For tech
Never Asked: Risks (no KB queries), Business Overview: portfolio stats
Retrieval misses: none this run
```

### Decisions
1. Generated by code from `trace.jsonl`; no agent.
2. The analyst sees only the summary block at the end of the chat; the full report stays in the run folder.
3. Markdown in the run folder for now; an HTML view or dashboard can come later from Step 7.
4. Kept with the run folder as the audit trail; not published with the Solution Intent.

## Step 6 — Act on the tags (from claim to KB change)

### What it is
Turns claims marked `add`, `correct` or `check` into **KB changes an approver signs off on**. The only step that changes the KB; nothing changes without a person approving it. An **LLM judge** makes the judgement calls at each stage; code does the plumbing; the approver decides.

- **Input:** `trace.jsonl` lines with `kb_action` add / correct / check, from every run.
- **Excluded from the start:** Unverified, Derived (run-specific; inputs carry the gaps), User (decision) (choices, not knowledge), Unsupported claims the analyst **removed**. (Kept ones are User (confirmed at check) and can continue — see 6c.)
- **Separate from the KB flow:** Never Asked and retrieval misses are reported to **tech** regardless of what happens below.

### The six stages

| Stage | LLM judge decides | Code does | Human |
|---|---|---|---|
| **6a Reusable?** | Would a future run need this, or is it only true for this project? | — | — |
| **6b Already in the KB?** | From the closest KB entries: same fact & same value (duplicate) / same fact & different value (stale) / different fact | Searches the **live KB** (the only place in the process that does); checks quotes word for word | — |
| **6c Where does it go?** | Which entry to update, or a new entry; which domain | Looks up the domain's approver | — |
| **6d Merge across runs** | Is this the same change as an open candidate? | Finds open candidates for the same entry; counts runs; links evidence | — |
| **6e Approver review** | Drafts the **proposed KB text** and a **recommendation** (approve / edit / reject + reason) | Builds the weekly queue per domain | **Approve, edit, reject or retire — the KB gate** |
| **6f Ingest** | — | Versioned update (never overwrite in place); audit trail: who approved, when, which runs | — |

**6a — Reusable?**

| Reusable → continue | Run-specific → drop |
|---|---|
| Interchange rates, scheme rules, thresholds, mandate dates, definitions | This epic's go-live dates, "we're currently at ~4,200 disputes/month", team names |

- Only reusable items go on to 6b. Dropped items are logged with a reason; no candidate.
- **When unsure, keep it** — the approver can reject; a wrong drop disappears silently.
- The process owner **samples dropped items** periodically (same aggregate review as Unverified).

**6b — Already in the KB?** Step 4 only saw what the KB returned during the run; now the judge checks the KB itself for the correct value.

| Step 4 action | Correct value already in KB? | Becomes |
|---|---|---|
| correct | No | **Correct** the entry (e.g. ic-0412 → 1.95%) |
| correct | Yes, as another entry | **Retire** the stale entry + tell tech (retrieval issue) |
| add | No | **Add** (new, or extend an existing entry) |
| add | Yes | No candidate — **retrieval miss** → tech |
| check (Never Asked) | No | Becomes an **add** |
| check | Yes | No candidate — KB had it but wasn't asked → tech |

**6b/6c — How duplicates and placement are judged.** Three signals, strongest first:

| Signal | When available | Gives |
|---|---|---|
| 1. **KB location from the log** | The KB returned a chunk on the topic during the run (Wrong Hit, missing piece) | The exact entry and domain, e.g. ic-0412 in `Payments/Pricing` |
| 2. **Similarity search** (embed the proposed text; reuse the KB's own index) | Always | Nearest KB entries — possible duplicates and where similar knowledge lives |
| 3. **Domain list** (`kb_domains`: each domain, a short description, its approver) | Always | Where a brand-new topic belongs |

The **LLM judge** reads the candidate, its evidence and the top similar entries, and decides: duplicate (same fact & value / stale / different fact), and where (update entry X, extend entry X, or new entry in domain Y). A near-exact similarity match for a No Hit is a strong sign of a **retrieval miss**.

**6c — Where does it go?** Placement has three tiers:

| Tier | Used when | Location comes from |
|---|---|---|
| 1 | The KB returned a chunk on the topic during the run | Log location (exact) |
| 2 | Similar entries exist (score above a threshold) | Similarity search + judge |
| 3 | Nothing similar exists | Domain list + judge, marked **"new topic"** |

- Borderline domain → best guess, flagged **"placement unsure"**.
- In every tier the **approver can re-route** to another domain — a misplaced item costs one click, it's never lost.
- Example — C-16 "Large e-commerce clients' retention depends on approval rates" (kept by the analyst): similarity finds "Retention drivers for Tier-1 merchants" (Clients/Retention, 0.82), "Authorization approval rate benchmarks" (Payments/Auth, 0.74). Judge: not a duplicate; extend the Clients/Retention entry — "the claim is about retention; approval rate is the driver, not the subject." Routed to the Clients/Retention approver, flagged "analyst-supplied, no document".

**Kept Unsupported claims (User, confirmed at check)** may become KB candidates — expert knowledge that isn't written down is exactly what the KB should capture — but they go through 6a/6b like any other, are **always** flagged "analyst-supplied, no document", and the judge's recommendation defaults to **"verify before approving"**. Claims the analyst removed never reach Step 6.

**6d — Merge across runs.** Candidates wait in an **open pool** per domain until reviewed. When a new candidate arrives (it already has its target entry, action and proposed value from 6b/6c):
1. **Code** finds open candidates for the **same target entry** (e.g. ic-0412). For a brand-new topic with no entry yet, it looks within the same domain.
2. **The judge** compares the new candidate with each match:

| Judge finds | Result |
|---|---|
| Same fact, same proposed value | **Merge** — one candidate, run count +1, this run's `source_quote` added as evidence |
| Same fact, **different** proposed value (run A 1.95%, run B 2.05%) | **Merge, flagged "sources disagree"** — the approver sees both |
| Different fact on the same entry (rate vs fee) | **Separate** candidate |
| No match | **New** candidate |

3. **After review:** approved → closed (the KB is fixed, so later runs shouldn't raise it again). **Rejected** → a later identical candidate links to the rejection and is **not re-queued**, unless it brings **new evidence** (a different source or value) or keeps recurring past a threshold.

The run count tells the approver how much the gap is affecting work: "seen in 3 runs" outranks "seen once".

**6e — Approver review.** Weekly queue per domain. Each candidate shows:

```
CORRECT  ic-0412 · Payments/Pricing                      seen in 3 runs (EP-2210, EP-2231, EP-2240)
  KB says:      "Standard 1.80% + $0.10"
  Source says:  "Card-not-present | Standard | 1.95% | $0.10"   sources/interchange_2026.xlsx · CNP!A4:D4
  Proposed:     "Standard 1.95% + $0.10 (effective 2026-01-01)"
  Judge:        Approve — same tier and fee; KB is the 2025 schedule; 2026 sheet is current.
  Flags:        —
  [Approve]  [Edit]  [Reject + reason]  [Retire]  [Re-route]
```

Actions: **approve, edit, reject, retire** (a stale duplicate), **re-route** (to another domain's approver).

### Guardrails (same pattern as Step 4)
- **Evidence must be real:** any KB text the judge cites must appear word for word in the search results (code check).
- **Confidence + a second judgement** for **retire** and **correct**. If the two disagree, the candidate goes to the approver flagged **"judge unsure"**.
- **The judge recommends; the human decides.** The approver sees the reasoning but isn't bound by it.
- **Analyst-only corrections:** a correction backed only by something the analyst typed (no document) is flagged **"analyst-supplied, no document"** so the approver confirms it against an authoritative source. A chat message alone shouldn't overwrite a KB fact.
- **Test set:** include known duplicates and non-duplicates to watch the dedup judge's accuracy.

### Example

| Claim | Step 4 action | 6a Reusable? | 6b In KB? | Outcome |
|---|---|---|---|---|
| C-01 CNP rate 1.95% | correct | Yes | No | **Correct ic-0412** → Pricing approver |
| C-13 Mandate Phase 1 2027-03-01 | add | Yes (scheme-wide date) | **Yes** — pb-mand-0207 | No candidate — **retrieval miss** → tech |
| C-11 CNP 62% of volume (2025) | check | Yes | No | **Add** → Portfolio approver |
| C-07 ~4,200 disputes/month | check | **No** — current, run-specific | — | Dropped; Never Asked on Risks still → tech |
| C-30 Phase by region | — | — | — | Never a candidate (User decision) |

Out of 42 claims, about two reach an approver. Expected: most claims are fine; only real KB problems escalate.

**Feeds Step 7:** Step 6 outcomes (routed, approved, rejected, retired, time from gap found to KB update, dropped at 6a, retrieval misses found at 6b) are recorded per candidate so Step 7 can measure whether the loop is closing.

## Step 7 — Metrics

### What it is
Counts up results across runs to answer **four questions**. Built by **code**, no agent. Reads `trace.jsonl` from every run plus Step 6 outcomes (what approvers did, and when). Kept deliberately small: a headline and one or two supporting metrics per question.

### The four questions

| Question | Metric | Definition | Want |
|---|---|---|---|
| **1. Can we trust the Solution Intent?** | ★ **Unsupported rate** | % of claims with no source of any kind (split: kept in / removed from the Solution Intent) | ↓ toward ≤2% |
| | **Verified share** | % of claims traced to a source and confirmed (everything except Unsupported and Unverified) | ↑ |
| **2. When we ask the KB, does it deliver?** (used · overruled · missing) | ★ **KB used rate** | Where the KB was asked, % of claims where the KB's answer was **used** in the Solution Intent; the rest is **overruled** or **missing** (all three ÷ asked, adding to 100%) | ↑ |
| | **Provenance mix** (trend chart) | Weekly share of **knowledge claims** from KB / Local / User (fact) / Unsupported — the KB's share of the work | KB share ↑ |
| **3. Is the loop closing?** | ★ **Time to fix** | Median days from a gap first seen in a run to the KB updated | ↓ |
| | **KB updates approved** | Approved changes (add / correct / retire) per week, by domain | Rise early, then fall to a low, steady level |
| | **Open backlog** | Candidates waiting for an approver, and the age of the oldest, by domain | Small and young |
| **4. Is it being used?** | ★ **Adoption** | Runs per week; active teams; repeat teams | ↑ |
| | **Never Asked rate** | Of knowledge claims, % on topics where the KB was never queried — by section | ↓ toward ≤5% |

★ = headline metric for leadership (one per question).

**Headline example (illustrative):**

```
Weeks 1–8 · 64 runs · 5 teams
1. Unsupported rate   6%  → 2%    ↓   Can we trust the Solution Intent?
2. KB used rate       62% → 78%   ↑   When we ask the KB, does it deliver?
3. Time to fix        21d → 9d    ↓   Is the loop closing?
4. Runs per week      4   → 11    ↑   Is it being used?
```

### Question by question

#### Question 1 — Can we trust the Solution Intent?

**★ Unsupported rate**
- **Definition:** % of all claims with **no source of any kind** — not the KB, not `sources/`, not the analyst, and not derivable from those. (User is a source; Unsupported claims don't even have that.)
- **Split by the analyst's answer at the end of the chat** — this is about the **Solution Intent**, not the KB:

| | Meaning |
|---|---|
| **Removed from the Solution Intent** | Something likely wrong was caught **before it was published** — the system working. **Removed rate = hallucinations caught before publish.** |
| **Kept in the Solution Intent** | True, but not in this run's record — the analyst vouches for it (User, confirmed at check). Whether it reaches the KB is a separate Step 6 decision. |

- **Also shown:** the share marked **general knowledge** (`none (general knowledge)`) — how much the assistant leans on its own training knowledge rather than run sources.
- Unsupported means **unsourced**: either made up (hallucination) or true but not recorded in the run. The analyst's keep/remove is what separates the two.

**Verified share**
- **Definition:** % of claims traced to a source and confirmed = all claims − Unsupported − Unverified.
- Answers "how much of this Solution Intent can we stand behind?" It mirrors the Unsupported rate but also counts claims where our own check was unsure (Unverified).
- **Why not the provenance mix here:** a claim from a `sources/` file (Local), the analyst (User) or a checked derivation (Derived) is traced and verified just as much as a KB claim. A shift from Local to KB doesn't make the Solution Intent more trustworthy — it means the KB is doing more of the work. So the mix belongs in Question 2 (shown over knowledge claims only).

**Stated limit:** *verified means traced to a source, not proven true.* A KB claim can be verified and still be wrong if the KB itself is wrong and nobody overruled it — the run had nothing to contradict it.

**What success looks like** (directions + indicative levels; firm targets set after the baseline weeks)

| Metric | Success |
|---|---|
| **Unsupported rate** | Falls toward **≤2%** of claims. Within it, **removed** falls over time (the assistant makes less up as its sources improve). |
| **General-knowledge share** | Falls, as more of what the assistant "just knows" is backed by KB or sources |
| **Verified share** | Rises toward **~98%** |

#### Question 2 — When we ask the KB, does it deliver? (used · overruled · missing)

*Deliver* = its answer is **used** in the Solution Intent. Not delivering = **overruled** (it answered, but was replaced — an accuracy problem) or **missing** (it had nothing, or not this piece — a gap problem). The question deliberately doesn't claim "correct": used means not contradicted, not proven right.

**Ground rules**
- **Only claims where the KB was asked.** Never Asked is a workflow problem (Question 4); Unsupported has nothing to compare against; Unverified can't be counted either way. All three are left out of used / overruled / missing.
- **Use the gap type, not the tag.** C-02 (fee $0.10) is tagged Local because the drafter cited the xlsx, but the KB returned the same $0.10 — for KB health it counts as used.
- **"Fully answered" (the gap badge) = KB used in the Solution Intent.**

| Bar label | Gap types | Plain meaning |
|---|---|---|
| **Used** | Fully answered — tag KB, corroborated, or found on rerun | The KB's answer went into the Solution Intent, unchallenged |
| **Overruled** | Wrong Hit | The KB answered, but a source or the analyst replaced it |
| **Missing** | No Hit + missing piece | The KB had nothing, or not this piece |

All three are **÷ asked**, so they always add to 100%. (Not "share of not-used" — that can move the wrong way while both improve: if overruled falls 5 → 2 and missing 15 → 5, overruled's share of not-used *rises* 25% → 29%.)

**Dashboard (illustrative, Weeks 1–8)**

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│  Q2 · WHEN WE ASK THE KB, DOES IT DELIVER?            Weeks 1–8 · 64 runs        │
├─────────────────────────────────────────────────────────────────────────────────┤
│  ★ KB USED RATE            66%  ──────────────►  85%   ▲ +19 pts                │
│                                                                                 │
│  Wk1  ████████████████▌ 66 used │ █ 4 overruled │ ███████▌ 30 missing           │
│  Wk8  █████████████████████▎ 85 used │ █▎ 5 overruled │ ██▌ 10 missing          │
├──────────────────────────────────────┬──────────────────────────────────────────┤
│  BY DOMAIN (Wk8)                     │  PROVENANCE MIX (knowledge claims)       │
│               Used  Overr.  Missing  │  Wk1  KB 42% · Local 30% · User 22% · U 6% │
│  Pricing       92%    3%      5%     │  Wk8  KB 56% · Local 24% · User 18% · U 2% │
│  Auth          88%    4%      8%     │                                          │
│  Risk          64%    9%     27%  ◄  │                                          │
├──────────────────────────────────────┴──────────────────────────────────────────┤
│  DETAILS (process owner)                                                        │
│  KB accuracy        94.3% → 94.4%   steady    KB upheld share   15%   healthy   │
└─────────────────────────────────────────────────────────────────────────────────┘
```

**How to read it:** the KB now delivers 85% of the time, up from 66% — mainly because gaps were filled (missing 30% → 10%) — its accuracy held steady at ~94%, and Risk is where to build next. Overruled ticked up 4% → 5% only because the KB is answering more questions; KB accuracy shows quality didn't drop.

**The metrics**

| # | Metric | Definition | Example | Good looks like | Who sees it |
|---|---|---|---|---|---|
| 1 | ★ **KB used rate** | Of claims where the KB was asked, % where its answer was **used** in the Solution Intent | 66% → 85% | **Rises** | Leadership |
| 2 | **Overruled** | Of claims asked, % where the KB answered but a source or the analyst **replaced** it (Wrong Hit) — accuracy problem | 4% → 5% | **Low**; a slight rise is fine when the KB is answering more (see #6) | Leadership |
| 3 | **Missing** | Of claims asked, % where the KB had **nothing, or not this piece** (No Hit + missing piece) — gap problem | 30% → 10% | **Falls** | Leadership |
| 4 | **By domain** | Used / overruled / missing per KB domain | Risk: 27% missing | Shows **where to build next**; weakest domains rise fastest | Leadership |
| 5 | **Provenance mix** | Weekly share of **knowledge claims** from KB / Local / User (fact) / Unsupported (average across Solution Intents) | KB 42% → 56% | **KB band grows**; Local and User (fact) shrink; Unsupported shrinks | Leadership — hero chart |
| 6 | **KB accuracy** (details) | When the KB **gave an answer**, % that was used: used ÷ (used + overruled). Not affected by gaps being filled. | 66/70 = 94.3% → 85/90 = 94.4% | **Steady or rising**; a drop means the KB is going stale | Process owner |
| 7 | **KB upheld share** (details) | Of Wrong Hits an approver reviewed (Step 6e), % **rejected** because the KB was right after all | 15% | **Low and falling** (≤20%). Rising → check `sources/` for drafts / out-of-scope files, or an over-eager Step 4. Don't expect zero: a steady 5–15% shows approvers really review; near 0% for long is worth a look for rubber-stamping. | Process owner |

**What gets logged**

Per run (`metrics.json`), by section and domain:

| Field | Definition |
|---|---|
| `kb_asked` | Knowledge claims where the KB was asked (excludes Never Asked, Unsupported, Unverified) |
| `kb_used` | Fully answered — tag KB + corroborated + found on rerun |
| `kb_overruled` | Wrong Hits |
| `kb_missing` | No Hit + missing piece |
| `kb_returned` | `kb_used` + `kb_overruled` (the KB gave an answer) |
| `mix` | Claim counts by tag: KB, Local, User (fact), User (decision), Derived, Unsupported |

Weekly rollup:

| Metric | Formula |
|---|---|
| ★ KB used rate | `kb_used` ÷ `kb_asked` |
| Overruled | `kb_overruled` ÷ `kb_asked` |
| Missing | `kb_missing` ÷ `kb_asked` |
| KB accuracy | `kb_used` ÷ `kb_returned` |
| KB upheld share | Step 6: Wrong Hit candidates rejected ÷ reviewed (weekly, not per run) |
| Provenance mix | Average of each Solution Intent's shares over **knowledge claims** (KB, Local, User (fact), Unsupported) |

**Provenance mix — the full view**

One 100% stacked bar per week, **knowledge claims only**:

```
PROVENANCE MIX — knowledge claims, weekly (avg per Solution Intent)

Wk1  │████████████████████▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓░░░░░░░░░░░░×××│
Wk4  │████████████████████████▓▓▓▓▓▓▓▓▓▓▓▓▓░░░░░░░░░░××│
Wk8  │███████████████████████████▓▓▓▓▓▓▓▓▓▓▓▓░░░░░░░░░×│

█ KB (green) 42→56%   ▓ Local (amber) 30→24%   ░ User (fact) (blue) 22→18%   × Unsupported (red, hatched) 6→2%
```

- **Weekly**, averaging each Solution Intent's shares so each counts equally (daily is too noisy; pooling lets one 300-claim Solution Intent outweigh five 40-claim ones).
- **Filters:** team, domain, section (e.g. Risk sections only).
- **Likely the hero chart for the pitch:** the green band growing week after week shows the loop working at a glance.
- **Excludes Derived and User (decision)** — they aren't knowledge the KB could have supplied:
  - **User (fact)** = something true about the world the analyst supplied ("Mandate Phase 1 takes effect 2027-03-01") — KB could hold it; may become a candidate. **In** the chart.
  - **User (decision)** = a choice for this project ("phase the rollout by region") — didn't exist until decided; never a KB candidate. **Out** of the chart.
  - **Derived** is out for three reasons: its inputs are already claims in their own bands (counting it again double-counts the same source); mixed inputs (User + KB) have no single band; and the source never actually says the derived value.
- **Derived is still kept as a data point** — checked in Step 4, shown per claim in the Step 5 report, counted in Question 1's Verified share, and logged in `mix` so it can be reported if ever needed. Just not shown in the presentation or management view.

**The story:** when we ask the KB, it delivers more often; when it doesn't, it's missing less (gaps filled — the domain view shows where next) and its accuracy holds; and it does more of the work in every Solution Intent.

#### Question 3 — Is the loop closing?

When a run finds a KB gap, does it actually get **fixed**, and how fast? This is what makes the KB evergreen — finding gaps is worthless if they sit in a queue.

**Data source:** Step 6, not `trace.jsonl`. Logged per candidate: `candidate_id`, `domain`, `action` (add / correct / retire), `first_seen` (first run that raised it, from the 6d merge), `runs_seen`, `routed_at`, `decided_at`, `decision` (approved / edited / rejected / retired / re-routed), `ingested_at`.

**What counts as a "gap" here:** a KB problem a run found that needs a KB change — any candidate that comes through Step 6 and is approved.

| Gap type (Step 4) | After Step 6 checks | KB change | Counts? |
|---|---|---|---|
| Wrong Hit (KB overruled) | Correct value not in the KB | **Correct** the entry | Yes |
| Wrong Hit | Correct value already in the KB (stale duplicate) | **Retire** the old entry | Yes |
| Missing piece (KB incomplete) | Not in the KB | **Add** to the entry | Yes |
| No Hit (KB had nothing) | Not in the KB | **Add** a new entry | Yes |
| Never Asked | Confirmed the KB doesn't have it | **Add** | Yes |

Not counted: retrieval misses (KB already had it — tech fixes the search); Never Asked where the KB already had it (workflow — tech); dropped at 6a (run-specific); Unverified (never routed); rejected by the approver (not a gap — the KB was right).

**Retire** = mark an outdated or duplicate entry **inactive**, so retrieval stops returning it. It is not deleted: it stays in the KB's version history for audit. Example: the 2025 pricing entry (1.80%) is retired because the 2026 entry (1.95%) already exists.

**★ Time to fix**
- **Definition:** median days from a gap **first seen in a run** to the **KB updated** (ingested). Measures the whole loop, not just the approver's queue.
- **Only approved fixes count** (correct, add, retire).
- **Example:** C-01 (1.80% → 1.95%) first seen Oct 27, approved and ingested Nov 3 → **7 days**.
- The clearest proof the loop works: not "we found gaps" but "we fixed them in 9 days".

**KB updates approved**
- **Definition:** approved changes (add, correct, retire) per week, by domain.
- **Expected shape:** **rises early, then falls to a low, steady level.** Early runs uncover the backlog of stale and missing content; as the KB fills in, there's less to fix. The decline is the good news. It won't reach zero — the world keeps changing (new pricing, new rules), so a low steady flow of updates is healthy.
- **Read it with the other metrics:** updates falling to near zero while adoption is rising and Question 2's "missing" is still high means the loop is stuck, not finished.

**Open backlog**
- **Definition:** candidates waiting for an approver, and the age of the oldest, by domain.
- **Why:** time to fix only counts gaps that **got** fixed. If approvers stop reviewing, time to fix looks fine while the queue silently grows. The backlog catches that.

**Dashboard (illustrative)**

```
┌──────────────────────────────────────────────────────────────────────────┐
│  Q3 · IS THE LOOP CLOSING?                         Weeks 1–8 · 64 runs    │
├──────────────────────────────────────────────────────────────────────────┤
│  ★ TIME TO FIX (median)      21 days  ─────────►  9 days   ▼             │
├─────────────────────────────────────┬────────────────────────────────────┤
│  KB UPDATES APPROVED / WEEK         │  OPEN BACKLOG (now)                │
│  Wk1  ███ 3                         │  12 open                           │
│  Wk2  ███████ 7                     │  Pricing   2   oldest  4d          │
│  Wk3  ███████████ 11                │  Auth      3   oldest  6d          │
│  Wk4  ██████████████ 14  ← peak     │  Risk      7   oldest 18d   ◄      │
│  Wk6  ██████████ 10                 │                                    │
│  Wk8  ██████ 6           settling   │                                    │
└─────────────────────────────────────┴────────────────────────────────────┘
```

**How to read it:** gaps now get fixed in ~9 days, down from 21; updates peaked in week 4 as the early backlog cleared and are settling to a lower level; Risk's approver is falling behind.

| Metric | Success |
|---|---|
| ★ **Time to fix** | **Falls** (e.g. 21 → 9 days), then holds steady |
| **KB updates approved** | **Rises early, then falls to a low, steady level** as the KB fills in |
| **Open backlog** | **Small and young** — no domain with items older than ~two review cycles (e.g. 14 days) |

**Behind the scenes (unchanged):** judge override rate — how often approvers disagree with the Step 6 judge.

#### Question 4 — Is it being used?

"Used" means two things: **are teams adopting the process?** (the business case) and **is the assistant actually using the KB?** (the workflow health Questions 1–3 depend on).

**★ Adoption**
- **Definition:** **runs per week**; **active teams** (≥1 run in the last 4 weeks); **repeat teams** (≥2 runs in the last 4 weeks).
- **Example:** Week 1: 4 runs, 2 teams, 1 repeat. Week 8: 11 runs, 5 teams, 4 repeat.
- **Why repeat matters:** a team trying it once is curiosity; a team coming back is adoption.

**Never Asked rate**
- **Definition:** Never Asked ÷ (asked + Never Asked) — of knowledge claims, the % on topics where the **KB was never queried**. Together with Question 2 (which covers what happened *when* the KB was asked), Questions 2 and 4 cover every knowledge claim.
- **Example:** 100 knowledge claims; 80 had a KB query on the topic, 20 didn't → **20% Never Asked**.
- **By section** shows exactly **where** the assistant skips the KB (e.g. Risks 60% → the PDLC prompt for Risks doesn't query the KB) — a fix for tech.
- **Why it matters:** if the assistant skips the KB, the KB can't deliver or improve; a high Never Asked rate weakens every other metric.

**No Hit vs Never Asked**

| | What happened | Whose problem | Fix | Measured in |
|---|---|---|---|---|
| **No Hit** | We **asked** the KB and got **nothing back** | The **KB's** — content missing | **Add** content (Step 6) | Question 2 ("missing") |
| **Never Asked** | We **didn't ask** the KB at all | The **workflow's** — the assistant skipped it | **Fix the prompt / workflow** (tech) | Question 4 |

Example: Timeline t27 queried "mandate effective date" and got nothing → No Hit. Risks t33 went straight to the Confluence page without querying the KB → Never Asked.

**Dashboard (illustrative)**

```
┌──────────────────────────────────────────────────────────────────────────┐
│  Q4 · IS IT BEING USED?                            Weeks 1–8              │
├──────────────────────────────────────────────────────────────────────────┤
│  ★ RUNS PER WEEK         4  ──────────────►  11   ▲                      │
│     Active teams         2  ──────────────►   5                          │
│     Repeat teams         1  ──────────────►   4                          │
├──────────────────────────────────────────────────────────────────────────┤
│  NEVER ASKED RATE        25%  ────────────►   8%  ▼                      │
│  By section (Wk8)   Scope 3% · Solution 5% · Timeline 6% · Risks 22% ◄  │
└──────────────────────────────────────────────────────────────────────────┘
```

**How to read it:** usage nearly tripled and most teams come back; the assistant now skips the KB only 8% of the time, but the Risks section still needs a prompt fix.

| Metric | Success |
|---|---|
| ★ **Adoption — runs per week** | **Rises**, then holds at the level of real PDLC demand |
| **Active / repeat teams** | **Rise**; most active teams become repeat teams |
| **Never Asked rate** | **Falls** toward ≤5%, with no section stuck high |

**What gets logged:** per run, from the run header — `team`, `analyst`, `run_date`, `epic`; from `trace.jsonl` — `kb_never_asked` count by section (Question 2's `kb_asked` gives the other half).

### Behind the scenes (process owner only)

| Metric | Why |
|---|---|
| **Judge override rate** | % of Step 6 recommendations the approver overrode — how far to trust the LLM judge |
| **Unverified rate** | % of claims where the checker's two runs disagreed — whether Step 4 can be trusted |

### Rules
- **Denominator — knowledge claims:** all claims minus User (decision) and Derived, so the KB isn't blamed for choices or calculations it could never hold. Exceptions: Unsupported rate and Verified share use all claims; KB used rate uses only knowledge claims where the KB was asked (excluding Unsupported and Unverified).
- **Vocabulary:** **Unsupported** = no source anywhere (the Solution Intent may contain something made up). **Unverified** = the checker's two runs disagreed (our check is unsure). Other frameworks' "unverified" usually means our Unsupported.
- **Trends, not exact numbers.** Claim splitting varies a little between runs; use weekly rollups and look for direction.
- **Not targets for people.** The metrics measure the KB and the process. Judging analysts on KB share would push the assistant to cite the KB even when another source is better.
- **Baseline first:** use the first few weeks of runs to set a baseline before setting any targets.
- **Storage:** `metrics.json` per run in the run folder, plus a weekly rollup. A dashboard can come later.

### Left out on purpose (data is still there if needed)
Retrieval miss rate, human fill rate (mirror of KB share), citation coverage and pass rate (used in the prototype test), Step 6 input split and queue outcomes, repeat gaps, test set accuracy, 6a drop sampling.

---

## Where people are involved

| # | Who | When | What they do | Per run? |
|---|---|---|---|---|
| 1 | **Analyst** | End of chat, before publish (Step 4) | "Keep or remove?" on **Unsupported** claims only | Yes — one message |
| 2 | **Domain approver** | Step 6, e.g. weekly queue per domain | **The KB gate:** approve, edit or reject each candidate (correct, add, retire). Nothing enters the KB without this. | Batched |
| 3 | **Process owner** | Weekly/monthly | Reviews Unverified claims and metrics in aggregate; tunes prompts and test set | No |
| 4 | **Tech team** | As reports arrive | Acts on Never Asked and retrieval-miss reports | No |

One-time setup: hand-label the test set (20–30 claims); build the **domain list** (`kb_domains`: each KB domain, a short description, its approver) — used for routing and for placing new topics.

Everything else is automatic: logging, run folder, splitting, tracing, tags, gap types, second runs, report, reusability filter, dedup, metrics.

> **Pitch line:** People decide only twice — the analyst confirms anything with no source, and an approver signs off on every KB change. Everything in between is automatic and evidence-backed.

---

## Build items

What has to be built for the process to work. Environment: VS Code (Copilot Chat).

| # | Build item | What it does | Step |
|---|---|---|---|
| B1 | **KB wrapper** | Script around the KB command-line tool. Logs every `kb_query` (query, chunk IDs, location, text, hit/no_hit), reruns once on no_hit, returns results with ready-to-copy IDs (e.g. `KB ic-0412`). | 1 |
| B2 | **`sources/` wrapper** | Script the assistant uses to read `sources/` files. Logs every `source_read` and returns ready-to-copy IDs (e.g. `sources/interchange_2026.xlsx · CNP!A4:D4`). Copilot may bypass it with its built-in file tool, so B6 is the safety net. | 1 |
| B3 | **Citation instructions** | Rule in the PDLC prompt / `copilot-instructions.md`: after every sentence that states a fact, add a citation; cite only things read this run or what the analyst said; if the fact comes from the assistant's own general knowledge, write `none (general knowledge)`; if there's no source at all, write `none`; never invent one. Draft and cite **section by section**. | Drafting |
| B4 | **Citation format** | Hidden markdown comments. KB: `<!-- cite: KB ic-0412 -->`. Local: `<!-- cite: sources/<file> · <location> -->`. Analyst: `<!-- cite: analyst "Phase 1: 2027-03-01" -->` — a short quote, not a turn number, because the assistant doesn't know turn numbers while drafting. Step 4 finds the quote in the transcript and fills in the turn. Derived: `<!-- cite: derived from <inputs> ; calc -->`. General knowledge (assistant's own training, no source in the run): `<!-- cite: none (general knowledge) -->`. Several sources on one sentence: separate with `;` (e.g. an agreement plus the dates' source). | Drafting |
| B5 | **Strip step** | Saves the cited version to `runs/<id>/final.md`, then produces the clean, published `solution_intent.md` with all citation comments removed (they can otherwise survive a paste into Confluence/Jira). | 2 |
| B6 | **`sources/` manifest** | At run end, records the list of `sources/` files present (path + modified date) in the run folder. Step 4 verifies Local citations directly against the files in `sources/`, so a read that bypassed B2 is still checkable. No copies or hashes (see assumption below). | 2 |
| B7 | **Chat export** | Exports the VS Code chat to `transcript.jsonl` with message order, role and timestamp; turn numbers assigned on export. Fallback: assistant appends each message as it goes. | 2 |
| B8 | **Optional section check** | Small code check at the end of each drafted section: counts factual sentences with no citation and asks the assistant to fill them in (or mark `none`). Add only if the prototype shows citations slipping. | Drafting |

### `sources/` verification — how B6 works
- **Assumption:** before every run, the analyst puts current, accurate files in `sources/`. The quotes are copied into the report, so evidence survives later file changes. No snapshots or hashes.
- **Problem it solves:** Copilot can read `sources/` files with its built-in file tool, bypassing B2, so some reads go unlogged.
- **Fix:** Step 4 checks a Local `source_quote` directly against the cited file in `sources/`. A missing `source_read` line is no longer fatal.
- The manifest just records which files were present, so Step 4 can tell a citation to a real file from a made-up file name.
- The log stays essential for the **KB** (results can't be reproduced exactly later) and for the order of events gap types depend on. For Local claims, `source_read` lines become helpful rather than required.

## Prototype test (before building everything)

Run one real PDLC run in VS Code with only B1, B3 and B4 in place (plus a manual chat export). Measure:

| Measure | What it tells us | Good enough |
|---|---|---|
| % of factual sentences that carry a citation | Whether cite-as-you-write holds up over a long run | _Target to set_ |
| % of citations that pass Step 4 (exists + quote found + supports claim) | Whether citations are trustworthy | _Target to set_ |
| % of `sources/` reads that went through the wrapper | Whether B2 is enough or B6 is required | _Target to set_ |
| Where it slipped (section, how late in the run) | Whether B8 (section check) is needed | — |

Outcome decides: whether B8 is needed, whether B2 can be relied on, and whether to proceed with the full build.
