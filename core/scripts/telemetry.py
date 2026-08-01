#!/usr/bin/env python3
"""telemetry.py — the run-ledger writers: `emit()` + run_state updater (§3.4, §8.1, §3.5).

The single surface every run stage writes its ledger through. Three concerns:

  1. ``emit()`` / ``Emitter`` — the **telemetry.jsonl** event writer (§3.4 / §8.1). Every
     event carries the common envelope (``ts, run_id, domain, tool, event``) + the §8.1
     per-event payload; the record is validated against the telemetry schema before it is
     appended, so a malformed emission fails loud rather than poisoning the stream. These
     rows are the *only* source ``metrics_scan.py`` (§8.2, TASK-048) reads — **no metric is
     hand-entered** (NFR-06, FR-MX-01). All twelve events have a typed helper — the nine
     original §8.1 events plus the three ADR-008 enrichment events (``verdict``,
     ``escalation``, ``disposition``; TECH_SPEC banner §3.4–3.6).

  2. ``update_run_state()`` — the **run_state.json** updater (§3.5): last-write-wins current
     state, per-stage status with ``started`` / ``completed`` stamps + artifact ``version``,
     driving §9 resume (NFR-08). Validated against the run_state schema on every write.

  3. The **decisions.jsonl** gate/flag/walkthrough audit (§3.6, NFR-03) — re-exported from
     ``decisions.py`` (``gate``, ``flag``, ``disposition``, ``reonboard_flag``)
     so a run stage has one import for any ledger record. Those record
     *who/when/outcome/**rationale***; their telemetry twins record the same decision
     without the prose, so metrics never have to read a rationale.

It is plumbing (NFR-07): it stamps, validates, and appends/replaces files. It makes no
authoring judgment and holds no global state — every writer takes an explicit ledger dir
and accepts an explicit ``ts`` so a caller (or a test) can make a record deterministic.

Ledger layout (a run's ``ledger/``, §2.2): ``telemetry.jsonl`` (append), ``run_state.json``
(replace), ``decisions.jsonl`` (append).
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import ledger
# Re-export the decisions.jsonl writers so telemetry.py is the one ledger-writing surface.
from decisions import gate, flag, disposition, reonboard_flag  # noqa: F401

__all__ = [
    "emit", "Emitter", "update_run_state", "mark_stage", "STAGES",
    "gate", "flag", "disposition", "reonboard_flag",
]

# The ADR-008 pipeline stage vocabulary (also pinned in the telemetry/run_state schemas).
# `ingest` covers the whole Data & context layer — the code-lane map build included, since it
# is a lane of the source_processor fan-out rather than an operator stage of its own.
# `enrichment` is the two arms + the disposition walkthrough; `si_v2` is the apply pass that
# writes v2; `jira` covers plan authoring through the (G3-gated) push.
STAGES = ("ingest", "si_v1", "enrichment", "si_v2", "jira")

_RUN_STATE_STATUS = ("pending", "running", "done", "failed")

_telemetry_schema = None  # lazily loaded + cached (schema read is pure)
_run_state_schema = None


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _tel_schema() -> dict:
    global _telemetry_schema
    if _telemetry_schema is None:
        _telemetry_schema = ledger.load_schema("telemetry")
    return _telemetry_schema


def _rs_schema() -> dict:
    global _run_state_schema
    if _run_state_schema is None:
        _run_state_schema = ledger.load_schema("run_state")
    return _run_state_schema


# ── telemetry.jsonl ────────────────────────────────────────────────────────────
def emit(
    ledger_dir: str | Path,
    event: str,
    *,
    run_id: str,
    domain: str,
    tool: str,
    ts: str | None = None,
    validate: bool = True,
    **payload,
) -> dict:
    """Append one §8.1 event to ``ledger_dir/telemetry.jsonl`` and return the record.

    Builds the envelope (``ts, run_id, domain, tool, event``) + the given ``payload`` and,
    unless ``validate=False``, asserts the result against the telemetry schema — so an event
    that would not satisfy §8.1 (wrong payload for its ``event``, a ``stage`` outside the
    vocabulary, an unknown field) is rejected here, not discovered later by ``metrics_scan``.
    """
    record = {"ts": ts or _now_iso(), "run_id": run_id, "domain": domain, "tool": tool,
              "event": event, **payload}
    if validate:
        errs = ledger.validate_record(record, _tel_schema())
        if errs:
            raise ValueError(f"telemetry event fails §8.1 schema: {errs} | record={record}")
    path = Path(ledger_dir) / "telemetry.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, ensure_ascii=False) + "\n")
    return record


@dataclass
class Emitter:
    """Envelope-bound telemetry writer — binds ``ledger_dir`` + ``run_id/domain/tool`` once
    so a run stage emits events without repeating the envelope. One typed method per §8.1
    event; each validates + appends via ``emit()``."""

    ledger_dir: str | Path
    run_id: str
    domain: str
    tool: str

    def emit(self, event: str, *, ts: str | None = None, validate: bool = True, **payload) -> dict:
        return emit(self.ledger_dir, event, run_id=self.run_id, domain=self.domain,
                    tool=self.tool, ts=ts, validate=validate, **payload)

    # Typed per-event helpers — payload fields exactly as §8.1 pins them.
    def run_started(self, *, path: str, registry_sha: str, ts: str | None = None) -> dict:
        return self.emit("run_started", path=path, registry_sha=registry_sha, ts=ts)

    def stage_started(self, stage: str, *, ts: str | None = None) -> dict:
        return self.emit("stage_started", stage=stage, ts=ts)

    def stage_completed(self, stage: str, *, duration_ms: int, ts: str | None = None) -> dict:
        return self.emit("stage_completed", stage=stage, duration_ms=duration_ms, ts=ts)

    def model_call(self, *, stage: str, model: str, tokens_in: int, tokens_out: int,
                   cost_usd: float, ts: str | None = None) -> dict:
        return self.emit("model_call", stage=stage, model=model, tokens_in=tokens_in,
                          tokens_out=tokens_out, cost_usd=cost_usd, ts=ts)

    def validation(self, *, artifact: str, score: float, ts: str | None = None) -> dict:
        return self.emit("validation", artifact=artifact, score=score, ts=ts)

    def gate_decision(self, *, gate: str, outcome: str, actor: str, version: int,
                      ts: str | None = None) -> dict:
        return self.emit("gate_decision", gate=gate, outcome=outcome, actor=actor,
                          version=version, ts=ts)

    def flag_decision(self, *, flag_type: str, option: str, severity: str,
                      ts: str | None = None) -> dict:
        return self.emit("flag_decision", flag_type=flag_type, option=option,
                          severity=severity, ts=ts)

    def jira_push(self, *, epics: int, success: bool, partial: bool, ts: str | None = None) -> dict:
        return self.emit("jira_push", epics=epics, success=success, partial=partial, ts=ts)

    def error(self, *, stage: str, kind: str, message: str, ts: str | None = None) -> dict:
        return self.emit("error", stage=stage, kind=kind, message=message, ts=ts)

    # ── enrichment events (ADR-008; banner §3.4–3.6) ──────────────────────────
    # These three are the enrichment stage's whole ledger footprint. `finding_id` is a
    # pointer into `enrichment.json` — the stream records THAT a finding resolved and HOW
    # it routed, never what it said (FR-XS-05).

    def verdict(self, *, finding_id: str, arm: str, verdict: str, route: str,
                ts: str | None = None) -> dict:
        """One assertion/claim resolved against code (D-A5/D-A8).

        ``arm`` is ``impact`` (Arm 1, requirement → code) or ``claim`` (Arm 2, claim → code);
        ``verdict`` is the outcome; ``route`` is where it went without a human (D-A16). The
        ``route`` field is what makes **M12 enrichment yield** derivable with no hand entry:
        corrections are ``auto_correct``, derived impacts ``auto_write``, auto-fills
        ``auto_fill``. ``route="escalate"`` is followed by an ``escalation`` event.
        """
        return self.emit("verdict", finding_id=finding_id, arm=arm, verdict=verdict,
                          route=route, ts=ts)

    def escalation(self, *, finding_id: str, reason: str, severity: str,
                   ts: str | None = None) -> dict:
        """A finding needs a human (D-A9/D-A16) — it enters the walkthrough queue.

        ``reason`` is one of the four escalation triggers; ``severity`` (``material`` |
        ``advisory``, D6c) is what lets the walkthrough **triage rather than enumerate**
        (D-A17): material findings get individual attention, advisory ones batch. Every
        escalation must be answered by a ``disposition`` before G2 (hard precondition, §9.3).
        """
        return self.emit("escalation", finding_id=finding_id, reason=reason,
                          severity=severity, ts=ts)

    def disposition(self, *, finding_id: str, call: str, actor: str,
                    target: str | None = None, ts: str | None = None) -> dict:
        """The operator's call on an escalated finding (D-A16/D-A17).

        The telemetry twin of the ``decisions.jsonl`` ``disposition`` record, which carries
        the same call **plus the rationale**. ``target`` is the SI section the finding landed
        in; it is absent on ``call="reject"`` (the finding was wrong and is dropped).
        """
        payload = {"finding_id": finding_id, "call": call, "actor": actor}
        if target is not None:
            payload["target"] = target
        return self.emit("disposition", ts=ts, **payload)


# ── run_state.json ───────────────────────────────────────────────────────────--
def update_run_state(
    ledger_dir: str | Path,
    *,
    stage: str | None = None,
    status: str | None = None,
    current_stage: str | None = None,
    version: int | None = None,
    repo_commit_sha: str | None = None,
    ts: str | None = None,
    validate: bool = True,
) -> dict:
    """Update ``ledger_dir/run_state.json`` (§3.5) last-write-wins; return the new state.

    Reads the existing state (seeded by ``ledger.init_ledger``), applies the change, and
    rewrites it. When ``stage``+``status`` are given, the stage's status is set and stamped
    per §3.5 — ``running`` records ``started`` (once), ``done``/``failed`` records
    ``completed`` (``started`` preserved). ``current_stage`` advances to ``stage`` unless
    set explicitly. ``version`` pins the accepted artifact version on the stage;
    ``repo_commit_sha`` sets the top-level repo pin. Validated against the run_state schema.
    """
    d = Path(ledger_dir)
    rs_path = d / "run_state.json"
    state = json.loads(rs_path.read_text(encoding="utf-8"))
    when = ts or _now_iso()

    if stage is not None:
        if stage not in STAGES:
            raise ValueError(f"stage {stage!r} not in §8.1 vocabulary {STAGES}")
        entry = state.setdefault("stages", {}).setdefault(stage, {"status": "pending"})
        if status is not None:
            if status not in _RUN_STATE_STATUS:
                raise ValueError(f"status {status!r} not in {_RUN_STATE_STATUS}")
            entry["status"] = status
            if status == "running":
                entry.setdefault("started", when)
            elif status in ("done", "failed"):
                entry["completed"] = when
        if version is not None:
            entry["version"] = version

    if current_stage is not None:
        if current_stage not in STAGES:
            raise ValueError(f"current_stage {current_stage!r} not in §8.1 vocabulary {STAGES}")
        state["current_stage"] = current_stage
    elif stage is not None:
        state["current_stage"] = stage

    if repo_commit_sha is not None:
        state["repo_commit_sha"] = repo_commit_sha

    if validate:
        errs = ledger.validate_record(state, _rs_schema())
        if errs:
            raise ValueError(f"run_state fails §3.5 schema: {errs} | state={state}")

    rs_path.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")
    return state


def mark_stage(
    emitter: Emitter,
    stage: str,
    status: str,
    *,
    duration_ms: int | None = None,
    version: int | None = None,
    ts: str | None = None,
) -> dict:
    """Convenience: advance both ledgers for a stage transition in lock-step.

    Updates ``run_state.json`` (stage status + stamps + ``current_stage``) **and** emits the
    matching telemetry event — ``stage_started`` on ``running``, ``stage_completed``
    (requires ``duration_ms``) on ``done`` — so the two ledgers never drift. ``failed`` /
    ``pending`` update run_state only (the ``error`` event is emitted separately with its
    payload). Returns the new run_state.
    """
    when = ts or _now_iso()
    state = update_run_state(emitter.ledger_dir, stage=stage, status=status,
                             version=version, ts=when)
    if status == "running":
        emitter.stage_started(stage, ts=when)
    elif status == "done":
        if duration_ms is None:
            raise ValueError("mark_stage(status='done') requires duration_ms (§8.1 stage_completed)")
        emitter.stage_completed(stage, duration_ms=duration_ms, ts=when)
    return state


# ──────────────────────────────────────────────────────────────────────────────
# Proof (TASK-032, re-cut at TASK-104). Run: python3 core/scripts/telemetry.py
#   Build a synthetic full-run event stream over the ADR-008 pipeline (ingest → si_v1 →
#   enrichment → si_v2 → jira) + run_state lifecycle + all five decision kinds, then assert:
#   every telemetry row is schema-valid; the stream carries the events each MVP metric
#   (§8.2 as amended by FR-MX-02) is derived from with NO hand entry — including **M12
#   enrichment yield**, which the `verdict.route` field makes countable; run_state validates
#   and resumes coherently; decisions.jsonl validates; the retired BRD/FRD-era stage names
#   are refused. (metrics_scan.py is re-cut at TASK-125; here we prove the stream is
#   sufficient + valid — the input contract metrics_scan consumes.)
# ──────────────────────────────────────────────────────────────────────────────
def _demo() -> None:
    import tempfile

    import decisions

    T = "2026-06-22T00:00:00Z"  # fixed ts → deterministic proof
    with tempfile.TemporaryDirectory(prefix="telemetry-proof-") as tmp:
        led = ledger.init_ledger(Path(tmp) / "ledger", run_id="r-proof-001")
        em = Emitter(led, run_id="r-proof-001", domain="payment_brand", tool="claude")

        # A full v1 → enrichment → v2 → jira run's worth of events — one of every event.
        em.run_started(path="/work/r-proof-001", registry_sha="7d2e9a1", ts=T)
        mark_stage(em, "ingest", "running", ts=T)
        mark_stage(em, "ingest", "done", duration_ms=12000, ts=T)
        mark_stage(em, "si_v1", "running", ts=T)
        em.model_call(stage="si_v1", model="claude-opus-4-8", tokens_in=18000,
                      tokens_out=4200, cost_usd=0.91, ts=T)
        em.flag_decision(flag_type="scope_ripple", option="include in scope",
                         severity="material", ts=T)
        em.validation(artifact="si_v1", score=88.0, ts=T)
        em.gate_decision(gate="G1", outcome="accept", actor="vmunjal", version=1, ts=T)
        mark_stage(em, "si_v1", "done", duration_ms=402000, version=1, ts=T)

        # Enrichment: both arms emit verdicts; the escalations reach the walkthrough.
        mark_stage(em, "enrichment", "running", ts=T)
        em.model_call(stage="enrichment", model="claude-opus-4-8", tokens_in=9000,
                      tokens_out=1500, cost_usd=0.34, ts=T)
        # Arm 2 (claim → code): a source-derived claim corrected, a [TBD] closed, one match.
        em.verdict(finding_id="F-001", arm="claim", verdict="contradicted",
                   route="auto_correct", ts=T)
        em.verdict(finding_id="F-002", arm="claim", verdict="answered", route="auto_fill", ts=T)
        em.verdict(finding_id="F-003", arm="claim", verdict="confirmed", route="none", ts=T)
        # Arm 1 (requirement → code): a technical consequence auto-writes; a gap escalates.
        em.verdict(finding_id="F-010", arm="impact", verdict="impacted",
                   route="auto_write", ts=T)
        em.verdict(finding_id="F-014", arm="impact", verdict="no_code_found",
                   route="escalate", ts=T)
        em.escalation(finding_id="F-014", reason="no_code_found", severity="material", ts=T)
        em.disposition(finding_id="F-014", call="reroute", target="§14",
                       actor="vmunjal", ts=T)
        mark_stage(em, "enrichment", "done", duration_ms=311000, ts=T)

        # The apply pass writes v2, then G2.
        mark_stage(em, "si_v2", "running", ts=T)
        em.model_call(stage="si_v2", model="claude-opus-4-8", tokens_in=12000,
                      tokens_out=3000, cost_usd=0.52, ts=T)
        em.validation(artifact="enrichment", score=91.0, ts=T)
        em.gate_decision(gate="G2", outcome="accept", actor="vmunjal", version=2, ts=T)
        mark_stage(em, "si_v2", "done", duration_ms=98000, version=2, ts=T)

        mark_stage(em, "jira", "running", ts=T)
        em.jira_push(epics=5, success=True, partial=False, ts=T)
        em.error(stage="ingest", kind="source_timeout", message="confluence read timed out", ts=T)

        # All four decisions.jsonl kinds (the NFR-03 audit twins).
        decisions.gate(led / "decisions.jsonl", gate="G1", outcome="accept", version=1, ts=T)
        decisions.flag(led / "decisions.jsonl", flag_type="scope_ripple",
                       area="settlement/reconciler", option="include in scope",
                       severity="material", rationale="Shares the brand table; in-scope per ops.", ts=T)
        decisions.disposition(led / "decisions.jsonl", finding_id="F-014", call="reroute",
                              target="§14",
                              rationale="Settlement recon lives in another repo — §14 dependency.",
                              ts=T)
        decisions.reonboard_flag(led / "decisions.jsonl", language="c", coverage=0.71,
                                 floor=0.80, patterns=["macro"], decision="re-onboard", ts=T)

        # 1) Whole ledger validates against all three schemas.
        report = ledger.validate_ledger(led)
        print("ledger validation:")
        for fname, errs in report.items():
            print(f"  {fname:18} {'OK' if not errs else errs}")
        assert all(not e for e in report.values()), f"ledger must validate clean: {report}"

        # 2) The stream carries every event the MVP metrics (§8.2) derive from.
        events = [json.loads(l) for l in (led / "telemetry.jsonl").read_text().splitlines() if l.strip()]
        kinds = {e["event"] for e in events}
        required = {"run_started", "stage_started", "stage_completed", "model_call",
                    "validation", "gate_decision", "flag_decision", "jira_push", "error",
                    "verdict", "escalation", "disposition"}
        missing = required - kinds
        print(f"\nevents present: {sorted(kinds)}")
        assert not missing, f"stream missing events: {missing}"

        # 3) Spot-check the derivations are computable with NO hand entry (NFR-06/FR-MX-01).
        #    M01 $/SI-v1 and M02 $/enrichment now read the pipeline's own stage names; M12
        #    enrichment yield falls straight out of `verdict.route` (corrections + derived
        #    impacts + auto-fills), which is the whole reason that field is on the event.
        si_cost = sum(e["cost_usd"] for e in events
                      if e["event"] == "model_call" and e["stage"] == "si_v1")
        enrich_cost = sum(e["cost_usd"] for e in events
                          if e["event"] == "model_call" and e["stage"] in ("enrichment", "si_v2"))
        p95_inputs = [e["duration_ms"] for e in events if e["event"] == "stage_completed"]
        routes = [e["route"] for e in events if e["event"] == "verdict"]
        yield_m12 = sum(1 for r in routes if r in ("auto_correct", "auto_write", "auto_fill"))
        escalated = sum(1 for e in events if e["event"] == "escalation")
        dispositioned = sum(1 for e in events if e["event"] == "disposition")
        assert abs(si_cost - 0.91) < 1e-9, si_cost                  # M01 $/SI-v1
        assert abs(enrich_cost - 0.86) < 1e-9, enrich_cost          # M02 $/enrichment
        assert p95_inputs, "M07 needs stage_completed durations"
        assert yield_m12 == 3, yield_m12                            # M12 enrichment yield
        print(f"derivable: M01 $/SI-v1={si_cost:.2f}  M02 $/enrichment={enrich_cost:.2f}  "
              f"M07 inputs={p95_inputs}  M12 yield={yield_m12}  (no hand entry)")

        # 4) G2's hard precondition is checkable from the stream: every escalation answered.
        assert escalated == dispositioned, (escalated, dispositioned)
        print(f"G2 precondition: {escalated} escalation(s), {dispositioned} disposition(s) — "
              f"every escalation answered")

        # 5) run_state resumed coherently to the last stage touched.
        rs = json.loads((led / "run_state.json").read_text())
        assert rs["stages"]["ingest"]["status"] == "done", rs
        assert rs["stages"]["ingest"]["started"] == T and rs["stages"]["ingest"]["completed"] == T
        assert rs["stages"]["si_v2"]["version"] == 2, rs
        assert rs["current_stage"] == "jira", rs["current_stage"]

        # 6) Bad emissions are rejected at the door (validation bites).
        negatives = [
            ("stage_completed without duration_ms",
             lambda: em.emit("stage_completed", stage="ingest", ts=T)),
            ("run_state stage 'deploy' (outside vocabulary)",
             lambda: update_run_state(led, stage="deploy", status="running", ts=T)),
            ("retired stage name 'brd_authoring'",
             lambda: update_run_state(led, stage="brd_authoring", status="running", ts=T)),
            ("verdict with an unknown route",
             lambda: em.verdict(finding_id="F-099", arm="claim", verdict="confirmed",
                                route="auto_delete", ts=T)),
            ("disposition 'reject' carrying a target section",
             lambda: decisions.disposition(led / "decisions.jsonl", finding_id="F-099",
                                           call="reject", target="§16",
                                           rationale="search miss", ts=T)),
        ]
        print("\nnegatives (each must be refused):")
        for label, thunk in negatives:
            try:
                thunk()
            except ValueError as e:
                print(f"  {label:48} -> REJECTED ({str(e)[:48]}…)")
            else:
                raise AssertionError(f"{label!r} should have been rejected")

    print("\nPASS — emit() validates + writes all twelve events over the ADR-008 stage "
          "vocabulary; run_state updater stamps + resumes; decisions.jsonl audit valid "
          "incl. the walkthrough record; stream sufficient for the amended MVP metrics "
          "(NFR-06, FR-MX-01/02, NFR-03).")


if __name__ == "__main__":
    _demo()
