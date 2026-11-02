# PIV Text-to-SQL Assistant — Business Requirements & Technical Specification

**Owner:** Varun Munjal (VP, Sr. Product Manager, AI Automation — PBI) **Team:** Post-Install Validations (PIV) / Transaction Processing AI & Automation **Status:** Draft v0.1 — for build handoff

## 1. Purpose

Build a localized, internal text-to-SQL assistant for the PIV team, used from VS Code in agent mode. When a new data request or research question arrives, the assistant should identify the right query and produce validated-quality SQL as fast as possible by learning from the team's history of solved requests, falling back to a data dictionary when no precedent exists.

## 2. Problem Statement

The PIV team receives a steady stream of data requests via Jira. Each request is answered by an analyst who writes or adapts SQL by hand. The same tables, joins and filters recur constantly, but that knowledge lives in individual heads and in SQL attachments scattered across \~300 closed tickets. New requests take longer than they should, and less-experienced team members cannot easily reuse prior work.

## 3. Goals and Non-Goals

**Goals**

- Cut time from "request received" to "correct SQL ready to run" for recurring request types.
- Make \~300 historical, validated problem-statement → SQL pairs reusable as precedent.
- Give the agent enough schema context (tables, columns, definitions, join keys) to extend a precedent or write new SQL.
- Run entirely locally as a VS Code workspace; no new hosted infrastructure for phase one.

**Non-Goals (phase one)**

- Executing SQL against production automatically without human review.
- Serving users outside the PIV team.
- Trend analysis / anomaly detection — reserved for phase two.

## 4. Users and Scope

- **Primary users:** PIV analysts handling data requests.
- **Access model:** local, internal team tool; each user runs it inside their own VS Code.
- **Interface:** VS Code agent mode (Copilot / agent chat window). No separate UI.

## 5. Business Requirements

| ID | Requirement | Priority |
| --- | --- | --- |
| BR-1 | Accept a natural-language problem statement and return candidate SQL. | Must |
| BR-2 | Search the historical Jira inventory first and surface the closest validated precedents with a similarity/confidence score. | Must |
| BR-3 | When a strong precedent exists, adapt its SQL (filters, date ranges, added columns) rather than rewrite from scratch. | Must |
| BR-4 | When fields are needed that the precedent lacks, resolve them via the data dictionary. | Must |
| BR-5 | When no precedent scores above threshold, generate SQL from the data dictionary alone and clearly flag it as unvalidated. | Must |
| BR-6 | Every response cites which Jira(s) and which dictionary entries were used. | Must |
| BR-7 | Analyst can accept, edit, and save the final SQL back into the inventory as a new validated pair. | Should |
| BR-8 | Inventory and dictionary can be refreshed on demand as new Jiras close or schema changes. | Should |
| BR-9 | Phase two: trend analysis and anomaly detection skill over result sets. | Later |

## 6. Solution Overview

The assistant is a VS Code workspace containing two knowledge assets and an agent instruction set:

1. **Historical inventory** — \~300 records, each pairing a Jira problem statement with its validated SQL and extracted metadata (tables, joins, filters, output columns).
2. **Data dictionary** — a metadata file covering every in-scope table at the column level: name, type, business definition, join keys, common filters, known gotchas.
3. **Agent instructions** — a custom agent / instructions file that tells the agent how to use the two assets and in what order.

### Request flow

1. Analyst types a problem statement in agent mode.
2. Agent searches the inventory for similar problem statements and returns top-k matches with scores.
3. **High match:** agent takes the best precedent's SQL as the base, explains what it changes, and adapts it. Any new columns are looked up in the dictionary.
4. **Medium match:** agent combines the join/table skeleton from one or more precedents with dictionary lookups to fill gaps.
5. **Low / no match:** agent builds SQL from the dictionary alone, states its assumptions, and labels the output as unvalidated.
6. Agent returns: SQL, a plain-English explanation, the sources used, and a confidence label.
7. Analyst reviews, runs, and optionally saves the result as a new inventory record.

## 7. Technical Specification

### 7.1 Repository layout

```
piv-sql-assistant/
  .github/
    copilot-instructions.md        # or agents/*.md — agent behaviour and routing rules
  inventory/
    inventory.jsonl                # one record per Jira
    sql/                           # raw SQL files, one per Jira
  dictionary/
    tables.yaml                    # table and column metadata
    joins.yaml                     # canonical join paths
  scripts/
    extract_jiras.py               # pull Jiras + SQL attachments
    build_inventory.py             # normalize, enrich, write inventory.jsonl
    build_dictionary.py            # merge docs + DB introspection into tables.yaml
    search.py                      # optional local similarity search helper
  README.md
```

### 7.2 Historical inventory

**Source:** \~300 closed Jira data-request tickets. SQL is stored as attachments.

**Extraction (`extract_jiras.py`)**

- Query Jira via REST for the target project/filter.
- For each ticket capture: key, summary, description, reporter, created/resolved dates, labels.
- Download attachments; keep `.sql`, `.txt`, or inline code blocks containing SQL.
- Store raw SQL under `inventory/sql/<JIRA-KEY>.sql`.

**Normalization (`build_inventory.py`)**

- Clean the problem statement (summary + description) into a concise, searchable text field.
- Parse SQL to extract: tables referenced, join conditions, filter columns, output columns, date-range pattern.
- Optionally use an LLM pass to write a one-line "intent" summary and tag the request type (e.g., reclass research, fee validation, volume pull).
- Write one JSON line per ticket.

**Record schema (inventory.jsonl)**

```json
{
  "jira_key": "PIV-1234",
  "problem_statement": "...",
  "intent_summary": "...",
  "request_type": "...",
  "tables": ["..."],
  "joins": ["a.id = b.a_id"],
  "filters": ["..."],
  "output_columns": ["..."],
  "sql_path": "inventory/sql/PIV-1234.sql",
  "validated": true,
  "resolved_date": "YYYY-MM-DD"
}
```

### 7.3 Data dictionary

**Sources:** existing documentation plus direct database introspection (information\_schema or equivalent).

**Build (`build_dictionary.py`)**

- Introspect in-scope schemas for table and column names, data types, nullability, keys.
- Merge human-written definitions from existing docs.
- Derive candidate join paths from foreign keys and from joins observed in the inventory.
- Flag columns that appear frequently as filters in historical SQL.

**Schema (tables.yaml)**

```yaml
tables:
  - name: schema.table_name
    description: "Business meaning of this table"
    grain: "one row per ..."
    columns:
      - name: column_name
        type: varchar
        description: "Business definition"
        common_filter: true
        example_values: ["..."]
    join_keys:
      - to: schema.other_table
        on: "table_name.id = other_table.table_id"
    notes: "Gotchas, partitioning, refresh cadence"
```

### 7.4 Agent instructions and routing

Implemented as a repository-level instructions file (and/or custom agent file) so VS Code agent mode loads it automatically. The instructions should:

- Describe the two assets and their file locations.
- Mandate the search-first order: inventory → dictionary → generate.
- Define confidence tiers and the behaviour for each:
  - **High** (strong semantic match on problem statement and overlapping tables): adapt precedent SQL; minimal changes.
  - **Medium** (partial match): reuse join skeleton, fill from dictionary.
  - **Low** (no useful precedent): generate from dictionary; label as unvalidated; list assumptions.
- Require output format: SQL block, explanation, sources (Jira keys + dictionary entries), confidence label.
- Forbid inventing table or column names not present in the dictionary.
- Never execute against production; return SQL for human review.

### 7.5 Retrieval approach

Phase one can rely on the agent reading `inventory.jsonl` directly (300 records is small enough for in-context or grep-based search). If quality or latency becomes an issue, add `search.py` with a local embedding index (e.g., sentence-transformers + FAISS or SQLite-vec) exposing a simple CLI the agent can call. Keep this optional so the tool stays zero-infrastructure.

### 7.6 Feedback loop

- When an analyst accepts a result, a lightweight script (or agent instruction) appends the new problem statement + SQL to the inventory with `validated: false` until a reviewer flips it.
- Re-run `build_inventory.py` and `build_dictionary.py` on a schedule or on demand.

### 7.7 Security and data handling

- Repository lives on internal infrastructure only; no external endpoints.
- Inventory contains SQL and problem statements only — no result data or PII.
- Database credentials for introspection are never stored in the repo.
- Any LLM calls follow the team's approved tooling (GitHub Copilot Enterprise / approved internal models).

## 8. Open Questions

- Which Jira project/filter defines the \~300 in-scope tickets, and how consistent are the SQL attachments?
- Which database(s) and schemas are in scope for the dictionary?
- Who owns validation of newly saved inventory records?
- Is a local embedding index acceptable, or should retrieval stay purely file-based?
- Threshold values for high/medium/low confidence — set after an initial evaluation set is built.

## 9. Success Metrics

- Median time from request to approved SQL (baseline vs. after rollout).
- Percentage of requests answered by adapting a precedent vs. generated from scratch.
- Analyst acceptance rate of first-pass SQL without edits.
- Inventory growth over time.

## 10. Phased Delivery

- **Phase 0 — Data assembly:** Jira extraction script, raw SQL collection, first-pass dictionary.
- **Phase 1 — Assistant MVP:** inventory build, agent instructions, manual testing against 20 held-out tickets.
- **Phase 1.5 — Hardening:** optional embedding search, feedback loop, refresh scripts.
- **Phase 2 — Analysis skill:** trend analysis and anomaly detection over returned datasets.
