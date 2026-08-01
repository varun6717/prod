#!/usr/bin/env python3
"""Run-workspace ledger: initializer + JSON-Schema validators (TASK-022).

The ledger is the **run record** — events, state, decisions. It holds *that things
happened and what was decided*, never the artifacts' *content* (FR-XS-05): a BRD
paragraph, a code_map entry, a summary are content and live in their own files; the
ledger only points at the run's progress. That invariant is what these three schemas
enforce — none of them admits a free-form content blob.

Three files (TECH_SPEC §2.2), each with a schema in ``schemas/``:

  - ``telemetry.jsonl``  — append-only event stream (§3.4 envelope / §8.1 payloads +
                           the ADR-008 enrichment events); metrics_scan.py derives every
                           metric from these rows.
  - ``run_state.json``   — replaceable current state (§3.5); ``status ∈ {pending,
                           running, done, failed}``; drives §9 resume.
  - ``decisions.jsonl``  — append-only gate + flag + walkthrough audit (§3.6); shapes
                           match the writers in ``decisions.py``.

``init_ledger`` stamps a fresh, schema-valid ledger. It is what ``runs/_template/``
ships and what a real run's creation copies/regenerates from (the template is the
empty mould; a run overwrites ``run_state.json`` with its own ``run_id`` and appends
to the two ``.jsonl`` streams as it executes).

This module carries **no external dependency** (no ``jsonschema`` on this build) — a
minimal, deterministic validator (NFR-07) interprets the schema subset the three
contracts use. Run the proof: ``python3 core/scripts/ledger.py``.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

SCHEMA_DIR = Path(__file__).resolve().parent / "schemas"

# The stages this slice executes, in order (TECH_SPEC §3.5, ADR-008 vocabulary). Post-pivot
# the pipeline and the stage vocabulary are the same five names, so the template seeds all of
# them `pending` — there is no longer a deferred tail the schema admits but the template omits.
SLICE_STAGES = ("ingest", "si_v1", "enrichment", "si_v2", "jira")

# run_id placeholder in the template's run_state.json — a real run overwrites it.
TEMPLATE_RUN_ID = "__template__"


# ──────────────────────────────────────────────────────────────────────────────
# Minimal JSON-Schema validator (deterministic; the subset the 3 contracts use)
# Supported keywords: $ref ($defs), type, enum, const, required, properties,
# additionalProperties (bool|schema), propertyNames, items, oneOf, anyOf, allOf,
# pattern, minimum, maximum. Returns a list of human-readable error strings ([] = ok).
# ──────────────────────────────────────────────────────────────────────────────
import re

_TYPE_CHECKS = {
    "object": lambda v: isinstance(v, dict),
    "array": lambda v: isinstance(v, list),
    "string": lambda v: isinstance(v, str),
    # bool is a subclass of int in Python — exclude it from numeric/integer types.
    "integer": lambda v: isinstance(v, int) and not isinstance(v, bool),
    "number": lambda v: isinstance(v, (int, float)) and not isinstance(v, bool),
    "boolean": lambda v: isinstance(v, bool),
    "null": lambda v: v is None,
}


def _resolve(ref: str, root: dict) -> dict:
    if not ref.startswith("#/"):
        raise ValueError(f"unsupported $ref (only intra-document '#/...' supported): {ref}")
    node: Any = root
    for part in ref[2:].split("/"):
        node = node[part]
    return node


def _validate(value: Any, schema: dict, root: dict, where: str) -> list[str]:
    errs: list[str] = []

    if "$ref" in schema:
        errs += _validate(value, _resolve(schema["$ref"], root), root, where)

    if "type" in schema:
        types = schema["type"]
        types = [types] if isinstance(types, str) else types
        if not any(_TYPE_CHECKS[t](value) for t in types):
            errs.append(f"{where}: expected type {schema['type']}, got {type(value).__name__}")
            return errs  # type wrong → downstream keyword checks would be noise

    if "const" in schema and value != schema["const"]:
        errs.append(f"{where}: must equal {schema['const']!r}, got {value!r}")
    if "enum" in schema and value not in schema["enum"]:
        errs.append(f"{where}: {value!r} not in {schema['enum']}")

    if isinstance(value, str):
        pat = schema.get("pattern")
        if pat is not None and re.search(pat, value) is None:
            errs.append(f"{where}: {value!r} does not match pattern {pat!r}")

    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if "minimum" in schema and value < schema["minimum"]:
            errs.append(f"{where}: {value} < minimum {schema['minimum']}")
        if "maximum" in schema and value > schema["maximum"]:
            errs.append(f"{where}: {value} > maximum {schema['maximum']}")

    if isinstance(value, dict):
        for req in schema.get("required", []):
            if req not in value:
                errs.append(f"{where}: missing required property {req!r}")
        props = schema.get("properties", {})
        for key, sub in props.items():
            if key in value:
                errs += _validate(value[key], sub, root, f"{where}.{key}")
        names_schema = schema.get("propertyNames")
        if names_schema is not None:
            for key in value:
                errs += _validate(key, names_schema, root, f"{where}.<key {key!r}>")
        if "additionalProperties" in schema:
            ap = schema["additionalProperties"]
            extra = [k for k in value if k not in props]
            if ap is False:
                for k in extra:
                    errs.append(f"{where}: unexpected property {k!r}")
            elif isinstance(ap, dict):
                for k in extra:
                    errs += _validate(value[k], ap, root, f"{where}.{k}")

    if isinstance(value, list) and "items" in schema:
        for i, item in enumerate(value):
            errs += _validate(item, schema["items"], root, f"{where}[{i}]")

    for combiner in ("allOf",):
        for i, sub in enumerate(schema.get(combiner, [])):
            errs += _validate(value, sub, root, where)

    # if / then / else. Added at TASK-117, because the enrichment schema needs conditional
    # requirements ("escalated ⇒ must carry a reason and a severity") — and an UNSUPPORTED
    # keyword is worse than an absent one: the constraint sits in the file looking enforced
    # while validating nothing. The proof caught exactly that.
    if "if" in schema:
        branch = "then" if not _validate(value, schema["if"], root, where) else "else"
        if branch in schema:
            errs += _validate(value, schema[branch], root, where)

    if "oneOf" in schema:
        matches = sum(1 for sub in schema["oneOf"] if not _validate(value, sub, root, where))
        if matches != 1:
            errs.append(f"{where}: matched {matches} of oneOf branches (must match exactly 1)")
    if "anyOf" in schema:
        if not any(not _validate(value, sub, root, where) for sub in schema["anyOf"]):
            errs.append(f"{where}: matched none of anyOf branches")

    return errs


def validate_record(record: Any, schema: dict) -> list[str]:
    """Validate one parsed JSON value against a loaded schema. ``[]`` == valid."""
    return _validate(record, schema, schema, "$")


# ── schema loading + per-file validators ──────────────────────────────────────
def load_schema(name: str) -> dict:
    """Load a schema by stem (``telemetry`` | ``run_state`` | ``decisions``)."""
    return json.loads((SCHEMA_DIR / f"{name}.schema.json").read_text(encoding="utf-8"))


def validate_jsonl(path: str | Path, schema: dict) -> list[str]:
    """Validate every non-blank line of a ``.jsonl`` file. Empty file → ``[]`` (valid)."""
    errs: list[str] = []
    for n, line in enumerate(Path(path).read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError as e:
            errs.append(f"line {n}: invalid JSON ({e})")
            continue
        errs += [f"line {n}: {m}" for m in validate_record(record, schema)]
    return errs


def validate_json(path: str | Path, schema: dict) -> list[str]:
    """Validate a single-document ``.json`` file (run_state)."""
    return validate_record(json.loads(Path(path).read_text(encoding="utf-8")), schema)


def validate_ledger(ledger_dir: str | Path) -> dict[str, list[str]]:
    """Validate all three ledger files in a run's ``ledger/``. Returns {file: errors}."""
    d = Path(ledger_dir)
    return {
        "telemetry.jsonl": validate_jsonl(d / "telemetry.jsonl", load_schema("telemetry")),
        "run_state.json": validate_json(d / "run_state.json", load_schema("run_state")),
        "decisions.jsonl": validate_jsonl(d / "decisions.jsonl", load_schema("decisions")),
    }


# ── initializer ───────────────────────────────────────────────────────────────
def initial_run_state(run_id: str = TEMPLATE_RUN_ID) -> dict:
    """A valid §3.5 run_state at run start: every slice stage ``pending``, cursor at ingest."""
    return {
        "run_id": run_id,
        "current_stage": "ingest",
        "stages": {stage: {"status": "pending"} for stage in SLICE_STAGES},
    }


def init_ledger(ledger_dir: str | Path, run_id: str = TEMPLATE_RUN_ID) -> Path:
    """Stamp a fresh, schema-valid ledger into ``ledger_dir`` (creates it if absent).

    Writes empty ``telemetry.jsonl`` / ``decisions.jsonl`` (append-only streams begin
    empty) and an initial ``run_state.json``. This is the single source of the
    ``runs/_template`` ledger and what a real run's creation uses to seed its own.
    """
    d = Path(ledger_dir)
    d.mkdir(parents=True, exist_ok=True)
    (d / "telemetry.jsonl").write_text("", encoding="utf-8")
    (d / "decisions.jsonl").write_text("", encoding="utf-8")
    (d / "run_state.json").write_text(
        json.dumps(initial_run_state(run_id), indent=2) + "\n", encoding="utf-8")
    return d


# ──────────────────────────────────────────────────────────────────────────────
# Proof (TASK-022 fixture/proof). Run: python3 core/scripts/ledger.py
#   1. the shipped runs/_template ledger validates against all three schemas;
#   2. each schema REJECTS a deliberately-malformed record (the constraints bite) —
#      run_state's status enum (the named acceptance), telemetry's event payload,
#      decisions' kind/shape, the RETIRED BRD/FRD-era stage names (TASK-104) — and a
#      content-blob field is refused (FR-XS-05);
#   3. the writer shapes that must pass do pass, including the three ADR-008 enrichment
#      events and the walkthrough disposition record.
# ──────────────────────────────────────────────────────────────────────────────
def _demo() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    template_ledger = repo_root / "runs" / "_template" / "ledger"

    report = validate_ledger(template_ledger)
    print("runs/_template/ledger validation:")
    for fname, errs in report.items():
        print(f"  {fname:18} {'OK' if not errs else errs}")
    assert all(not e for e in report.values()), "the template ledger must validate clean"

    rs_schema = load_schema("run_state")
    tel_schema = load_schema("telemetry")
    dec_schema = load_schema("decisions")

    print("\nnegative cases (each must produce errors):")
    cases: list[tuple[str, dict, dict]] = [
        # run_state: status outside the §3.5 enum — the named acceptance condition.
        ("run_state bad status",
         rs_schema,
         {"run_id": "r1", "current_stage": "ingest",
          "stages": {"ingest": {"status": "paused"}}}),
        # run_state: a stage key outside the stage vocabulary.
        ("run_state bad stage key",
         rs_schema,
         {"run_id": "r1", "current_stage": "ingest",
          "stages": {"deploy": {"status": "pending"}}}),
        # ADR-008: the retired BRD/FRD-era stage names must be REJECTED, both ledgers.
        ("run_state retired stage name",
         rs_schema,
         {"run_id": "r1", "current_stage": "brd_authoring",
          "stages": {"brd_authoring": {"status": "running"}}}),
        ("telemetry retired stage name",
         tel_schema,
         {"ts": "2026-06-22T00:00:00Z", "run_id": "r1", "domain": "payment_brand",
          "tool": "claude", "event": "stage_started", "stage": "frd_authoring"}),
        # FR-XS-05: no artifact CONTENT in the ledger — a stray content blob is refused.
        ("run_state with content blob",
         rs_schema,
         {"run_id": "r1", "current_stage": "ingest",
          "stages": {"ingest": {"status": "done"}}, "brd_text": "## Executive Summary ..."}),
        # telemetry: stage_completed missing its required duration_ms payload.
        ("telemetry missing payload",
         tel_schema,
         {"ts": "2026-06-22T00:00:00Z", "run_id": "r1", "domain": "payment_brand",
          "tool": "claude", "event": "stage_completed", "stage": "ingest"}),
        # telemetry: unknown event.
        ("telemetry unknown event",
         tel_schema,
         {"ts": "2026-06-22T00:00:00Z", "run_id": "r1", "domain": "payment_brand",
          "tool": "claude", "event": "teleport"}),
        # decisions: vocab_gap_flag carrying BOTH shapes (must be exactly one).
        ("decisions vocab_gap both shapes",
         dec_schema,
         {"ts": "2026-06-22T00:00:00Z", "kind": "vocab_gap_flag", "arm": "code",
          "concept": "tokenization", "evidence": ["a.c"],
          "untagged_ratio": 0.3, "threshold": 0.2, "decision": "pending", "actor": "v"}),
        # decisions: a walkthrough disposition with no rationale — the record's whole point
        # is *why* the operator decided (D-A17); without it G2 cannot answer "why this now?".
        ("decisions disposition no rationale",
         dec_schema,
         {"ts": "2026-06-22T00:00:00Z", "kind": "disposition", "finding_id": "F-014",
          "call": "reroute", "target": "§14", "actor": "vmunjal"}),
        # telemetry: an enrichment event missing its route (verdict must say where it went).
        ("telemetry verdict missing route",
         tel_schema,
         {"ts": "2026-06-22T00:00:00Z", "run_id": "r1", "domain": "payment_brand",
          "tool": "claude", "event": "verdict", "finding_id": "F-002", "arm": "claim",
          "verdict": "contradicted"}),
    ]
    for label, schema, bad in cases:
        errs = validate_record(bad, schema)
        print(f"  {label:32} -> {'REJECTED' if errs else 'ACCEPTED (BUG)'}: {errs[:1]}")
        assert errs, f"{label!r} should have been rejected"

    # And the positive shapes the real writers emit must pass (parity with decisions.py).
    good_records: list[tuple[dict, dict]] = [
        (tel_schema, {"ts": "2026-06-22T00:00:00Z", "run_id": "r1", "domain": "payment_brand",
                      "tool": "claude", "event": "run_started", "path": "/work/r1", "registry_sha": "7d2e9a1"}),
        (tel_schema, {"ts": "2026-06-22T00:00:00Z", "run_id": "r1", "domain": "payment_brand",
                      "tool": "claude", "event": "gate_decision", "gate": "G1",
                      "outcome": "accept", "actor": "vmunjal", "version": 1}),
        (dec_schema, {"ts": "2026-06-22T00:00:00Z", "kind": "gate", "gate": "G1",
                      "outcome": "accept", "actor": "vmunjal", "version": 1}),
        (dec_schema, {"ts": "2026-06-22T00:00:00Z", "kind": "reonboard_flag", "language": "c",
                      "coverage": 0.71, "floor": 0.80, "unresolved_patterns": ["macro"],
                      "decision": "re-onboard", "actor": "vmunjal"}),
        (dec_schema, {"ts": "2026-06-22T00:00:00Z", "kind": "vocab_gap_flag", "arm": "code",
                      "concept": "tokenization", "evidence": ["payment/tokenize.c"],
                      "decision": "amend-vocab", "actor": "vmunjal"}),
        # The ADR-008 enrichment shapes — one telemetry event per new kind + its audit twin.
        (tel_schema, {"ts": "2026-06-22T00:00:00Z", "run_id": "r1", "domain": "payment_brand",
                      "tool": "claude", "event": "verdict", "finding_id": "F-002",
                      "arm": "claim", "verdict": "contradicted", "route": "auto_correct"}),
        (tel_schema, {"ts": "2026-06-22T00:00:00Z", "run_id": "r1", "domain": "payment_brand",
                      "tool": "claude", "event": "escalation", "finding_id": "F-014",
                      "reason": "no_code_found", "severity": "material"}),
        (tel_schema, {"ts": "2026-06-22T00:00:00Z", "run_id": "r1", "domain": "payment_brand",
                      "tool": "claude", "event": "disposition", "finding_id": "F-014",
                      "call": "reroute", "target": "§14", "actor": "vmunjal"}),
        (dec_schema, {"ts": "2026-06-22T00:00:00Z", "kind": "disposition",
                      "finding_id": "F-014", "call": "reroute", "target": "§14",
                      "rationale": "Settlement recon lives in another repo — §14 dependency.",
                      "actor": "vmunjal"}),
    ]
    print("\npositive cases (real writer shapes; each must validate):")
    for schema, good in good_records:
        errs = validate_record(good, schema)
        tag = good.get("event") or good.get("kind")
        print(f"  {tag:18} -> {'OK' if not errs else errs}")
        assert not errs, f"{tag!r} writer shape should validate: {errs}"

    print("\nPASS — template ledger valid; schemas reject malformed records and content blobs; writer shapes pass.")


if __name__ == "__main__":
    _demo()
