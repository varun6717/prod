#!/usr/bin/env python3
"""`decisions.jsonl` writers — the gate + flag + walkthrough audit ledger (§3.6, NFR-03).

Append-only, one JSON object per line. Five record `kind`s, all here so §3.6 lives
in one place (the unified ledger-writing surface re-exports them via ``telemetry.py``):

  - ``gate`` — a human acceptance gate decision (G1/G2/G3): who/when/outcome/version.
    The audit twin of the ``gate_decision`` telemetry event (which feeds M04); the
    rationale-bearing record of the decision (NFR-03).
  - ``flag`` — an operator disposition of an SI-authoring flag (scope ripple, etc.):
    who/when/option/severity/**rationale** (D6c material-vs-advisory). Twin of the
    ``flag_decision`` telemetry event.
  - ``disposition`` — the operator's call on an **escalated enrichment finding** at the
    disposition walkthrough (D-A16/D-A17). Twin of the ``disposition`` telemetry event,
    and the only place the **rationale** is written: `enrichment.json` records what each
    finding was, this records *why the human decided what they decided*. Together with the
    frozen `v1.md` they are what makes v2 reconstructable and auditable at G2.
  - ``reonboard_flag`` — the *extractor* coverage floor was tripped (§5.4, FR-DC-16):
    "a structural idiom the frozen tool can't parse — re-bless it?"
  - ``vocab_gap_flag`` — the *vocabulary* adequacy detector raised its hand
    (§5.4.1, ADR-003 / FR-DC-21): "a concept the frozen dictionary can't tag."
    ⚠ Its producer (`checks/vocab_adequacy.py`) was deleted with the vocabulary in the
    ADR-008 retirement sweep (TASK-100) and §5.4.1 is retired; the writer + schema branch
    are kept only until §3.6 is consolidated, so nothing reading old ledgers breaks.

``reonboard_flag`` / ``vocab_gap_flag`` are the same shape of event: a **frozen artifact
noticing it has been outgrown and asking a human**. Neither writer mutates the artifact —
it records a hand-raise for a human to dispose of (`decision` defaults to ``"pending"``
until a human picks ``amend-vocab`` / ``accept-as-is`` / ``re-onboard``). The run is NOT
blocked by either (advisory runtime flags; §10 containment stays the hard gate).

Records are appended to a run's ``ledger/decisions.jsonl`` (created with the run
workspace in TASK-022). The writers take an explicit ``ledger_path`` so they are
pure I/O with no global state, and an explicit ``ts`` so a caller can make the
record deterministic (tests pass a fixed timestamp; a real run stamps now).
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Sequence

DEFAULT_ACTOR = "vmunjal"

# The operator's four possible calls at the disposition walkthrough (D-A16/D-A17). Kept in
# lock-step with telemetry.schema.json's `call` enum. `defer` is not optional politeness —
# an operator who genuinely cannot answer "have we ever done this?" must be able to say so,
# or the walkthrough manufactures false certainty exactly where the design demands honesty.
WALKTHROUGH_CALLS: tuple[str, ...] = ("accept", "reject", "reroute", "defer")

# Calls that place the finding in an SI section (so `target` is required). `reject` is the
# odd one out: the finding was wrong (an Arm 1 search miss) and is dropped, not placed.
_PLACING_CALLS = frozenset({"accept", "reroute", "defer"})


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def append_decision(ledger_path: str | Path, record: dict) -> dict:
    """Append one §3.6 record as a JSON line to ``ledger_path``. Returns the record.

    Append-only and self-contained (creates the file/parents if absent). The record
    is written exactly as given — the typed builders below construct the §3.6 shapes.
    """
    path = Path(ledger_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, ensure_ascii=False) + "\n")
    return record


def gate(
    ledger_path: str | Path,
    *,
    gate: str,
    outcome: str,
    version: int,
    actor: str = DEFAULT_ACTOR,
    ts: str | None = None,
) -> dict:
    """Write a ``gate`` record (§3.6) — a human acceptance gate decision (G1/G2/G3).

    The decisions.jsonl audit twin of the ``gate_decision`` telemetry event: it captures
    *who* accepted/reopened *which* gate at *what* artifact ``version`` and *when*
    (NFR-03). ``outcome ∈ {accept, reopen}``; ``gate ∈ {G1, G2, G3}`` (the schema bites).
    """
    record = {
        "ts": ts or _now_iso(),
        "kind": "gate",
        "gate": gate,
        "outcome": outcome,
        "actor": actor,
        "version": version,
    }
    return append_decision(ledger_path, record)


def flag(
    ledger_path: str | Path,
    *,
    flag_type: str,
    option: str,
    severity: str,
    rationale: str,
    area: str | None = None,
    actor: str = DEFAULT_ACTOR,
    ts: str | None = None,
) -> dict:
    """Write a ``flag`` record (§3.6) — an operator's disposition of a BRD-authoring flag.

    The rationale-bearing audit twin of the ``flag_decision`` telemetry event. Records the
    operator-chosen ``option`` for a flag (e.g. a ``scope_ripple`` in ``area``), its
    ``severity`` (``material`` | ``advisory``, D6c), the ``rationale``, and the actor —
    the human-mediated scope decision (scope is never auto-changed). ``area`` is optional.
    """
    if severity not in ("material", "advisory"):
        raise ValueError(f"flag severity must be 'material' | 'advisory' (D6c); got {severity!r}")
    record: dict = {
        "ts": ts or _now_iso(),
        "kind": "flag",
        "flag_type": flag_type,
    }
    if area is not None:
        record["area"] = area
    record["option"] = option
    record["severity"] = severity
    record["rationale"] = rationale
    record["actor"] = actor
    return append_decision(ledger_path, record)


def disposition(
    ledger_path: str | Path,
    *,
    finding_id: str,
    call: str,
    rationale: str,
    target: str | None = None,
    actor: str = DEFAULT_ACTOR,
    ts: str | None = None,
) -> dict:
    """Write a ``disposition`` record (§3.6 / D-A16 / D-A17) — the walkthrough's audit line.

    One record per **escalated** enrichment finding the operator dispositions. Most findings
    never get one: grounded, unambiguous findings auto-apply and are recorded as ``verdict``
    telemetry only. This kind exists for the ones needing judgment — ambiguous, scope-moving,
    or would overrule a human.

    ``finding_id`` points into ``enrichment.json`` (the ledger never inlines the finding —
    FR-XS-05). ``call`` is one of ``WALKTHROUGH_CALLS``; ``target`` is the SI section it
    landed in (``"§16"``, ``"§14"``, ``"§7"``, ``"§8"``, ``"§12"``, ``"§17"``) and is required
    for every call except ``reject``, which drops the finding rather than placing it.

    ``rationale`` is mandatory and is the whole point of the record: this is the *only* file
    in the run that says **why**. The telemetry twin (``disposition`` event) carries the same
    decision without the prose, so metrics can count dispositions without reading rationales.
    """
    if call not in WALKTHROUGH_CALLS:
        raise ValueError(f"disposition call must be one of {WALKTHROUGH_CALLS} (D-A16); got {call!r}")
    if call in _PLACING_CALLS and not target:
        raise ValueError(f"disposition call {call!r} places the finding — `target` (the SI section) is required")
    if call == "reject" and target:
        raise ValueError("disposition call 'reject' drops the finding — it has no `target` section")
    record: dict = {
        "ts": ts or _now_iso(),
        "kind": "disposition",
        "finding_id": finding_id,
        "call": call,
    }
    if target:
        record["target"] = target
    record["rationale"] = rationale
    record["actor"] = actor
    return append_decision(ledger_path, record)


def reonboard_flag(
    ledger_path: str | Path,
    *,
    language: str,
    coverage: float,
    floor: float,
    patterns: Sequence[str] = (),
    decision: str = "pending",
    actor: str = DEFAULT_ACTOR,
    ts: str | None = None,
) -> dict:
    """Write a ``reonboard_flag`` record (§3.6 / §5.4) — extractor coverage below floor.

    Raised by the gate's ``check_coverage`` when ``coverage < floor`` (FR-DC-16). It
    asks a human whether to re-bless the extractor for new idioms; the frozen
    extractor is NEVER auto-modified. ``patterns`` carries the ``unresolved_patterns``
    that drove the gap so the human sees *what* the tool could not parse.
    """
    record = {
        "ts": ts or _now_iso(),
        "kind": "reonboard_flag",
        "language": language,
        "coverage": coverage,
        "floor": floor,
        "unresolved_patterns": list(patterns),
        "decision": decision,
        "actor": actor,
    }
    return append_decision(ledger_path, record)


def vocab_gap_flag(
    ledger_path: str | Path,
    *,
    arm: str,
    concept: str | None = None,
    evidence: Sequence[str] | None = None,
    untagged_ratio: float | None = None,
    threshold: float | None = None,
    decision: str = "pending",
    actor: str = DEFAULT_ACTOR,
    ts: str | None = None,
) -> dict:
    """Write a ``vocab_gap_flag`` record (§3.6 / §5.4.1, ADR-003). Two shapes, one kind.

    - **Primary** (concept): pass ``concept`` + ``evidence`` — a recurring concept the
      vocabulary lacks, caught from the model's ``uncovered_concepts`` (so it covers a
      *partially*-tagged file too, not just a fully-untagged one).
    - **Floor** (ratio): pass ``untagged_ratio`` + ``threshold`` — the deterministic,
      model-free safety net crossed ``adequacy_threshold``.

    Exactly one shape per call. The vocabulary is NEVER auto-grown — this is a
    hand-raise, the dictionary's twin of ``reonboard_flag``.
    """
    if (concept is None) == (untagged_ratio is None):
        raise ValueError("vocab_gap_flag: pass exactly one of (concept+evidence) | (untagged_ratio+threshold)")
    record: dict = {
        "ts": ts or _now_iso(),
        "kind": "vocab_gap_flag",
        "arm": arm,
    }
    if concept is not None:
        record["concept"] = concept
        record["evidence"] = list(evidence or [])
    else:
        record["untagged_ratio"] = untagged_ratio
        record["threshold"] = threshold
    record["decision"] = decision
    record["actor"] = actor
    return append_decision(ledger_path, record)
