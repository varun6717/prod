#!/usr/bin/env python3
"""metrics_scan.py — derive the MVP metrics from ``telemetry.jsonl`` (§8.2, FR-MX-01, NFR-06).

⚠ **STALE post-ADR-008 — re-cut is TASK-125.** Every derivation below keys off the retired
BRD/FRD stage vocabulary (`brd_authoring` / `frd_authoring` / `code_impact`), which TASK-104
replaced with `ingest / si_v1 / enrichment / si_v2 / jira` — the schemas now REJECT the old
names, so a real run's stream matches nothing here and the metrics come out empty. The
self-contained `_demo` still passes only because it builds its own pre-pivot events. The
amended metric set is FR-MX-02 (M01 $/SI-v1, M02 $/enrichment, M06 v1→v2 cycle, **M12
enrichment yield** = the `verdict.route` counts auto_correct + auto_write + auto_fill).

Read-only scan of the run ledger's telemetry stream. Every MVP metric (§8.2) is computed
HERE from the events alone — **no metric is hand-entered** (NFR-06): the §8.1 events are
the single source. The scan never writes, never blocks, and assigns no meaning beyond the
§8.2 derivations; it is the metrics twin of the build checks (one reads telemetry, the
other reads the seam).

Metrics (§8.2). Per-run aggregates are grouped by the ``run_id`` envelope, then summarized:

  M01 $/BRD              Σ model_call.cost_usd where stage ∈ {brd_authoring, code_impact}
                        per run; mean across runs.
  M02 $/FRD              Σ model_call.cost_usd where stage = frd_authoring per run; mean.
  M03 avg completion     mean validation.score of the accepted version — the validation
                        event preceding each gate_decision(accept), over brd + frd.
  M04 first-pass accept  count(G1 accept at version=1, no prior reopen) / count(runs at G1).
  M05 docs/month         count(run_started) per calendar month (YYYY-MM).
  M06 BRD→FRD cycle      ts(G2 accept) − ts(G1 accept) per run (seconds); mean.
  M07 latency p95        p95 of stage_completed.duration_ms across all stages.
  M09 FRD→epic coverage  validation.score for artifact=jira preceding push (deferred slice).
  M10 epics/FRD          jira_push.epics per run (deferred slice).
  M11 push success rate  count(jira_push.success) / count(jira_push) (deferred slice).
  M08 upstream alerts    W — depends on deferred change-detection; NOT computed in MVP.

This slice is BRD→FRD only, so the jira metrics (M09–M11) are ``None`` when the stream
carries no ``jira_push``/jira ``validation`` events — derived, not stubbed.
"""
from __future__ import annotations

import json
import math
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional, Sequence

# gate → the artifact whose validation precedes its accept (§8.2 M03).
_GATE_ARTIFACT = {"G1": "brd", "G2": "frd", "G3": "jira"}
_BRD_STAGES = {"brd_authoring", "code_impact"}


def load_events(path: str | Path) -> list[dict]:
    """Parse ``telemetry.jsonl`` → events in file (append) order. Blank lines skipped."""
    return [json.loads(line) for line in Path(path).read_text().splitlines() if line.strip()]


def _by_run(events: Sequence[dict]) -> dict[str, list[dict]]:
    runs: dict[str, list[dict]] = defaultdict(list)
    for e in events:
        runs[e.get("run_id", "?")].append(e)
    return runs


def _parse_ts(ts: str) -> datetime:
    return datetime.strptime(ts, "%Y-%m-%dT%H:%M:%SZ")


def p95(values: Sequence[float]) -> Optional[float]:
    """Nearest-rank p95 (deterministic): the value at rank ceil(0.95·n) in ascending order."""
    if not values:
        return None
    s = sorted(values)
    idx = max(0, min(len(s) - 1, math.ceil(0.95 * len(s)) - 1))
    return s[idx]


def _mean(values: Sequence[float]) -> Optional[float]:
    return round(sum(values) / len(values), 4) if values else None


@dataclass
class Metrics:
    runs: int
    m01_cost_per_brd: Optional[float]
    m02_cost_per_frd: Optional[float]
    m03_avg_completion_score: Optional[float]
    m04_first_pass_acceptance: Optional[float]
    m05_docs_per_month: dict[str, int] = field(default_factory=dict)
    m06_brd_frd_cycle_secs: Optional[float] = None
    m07_latency_p95_ms: Optional[float] = None
    m09_frd_epic_coverage: Optional[float] = None
    m10_epics_per_frd: Optional[float] = None
    m11_push_success_rate: Optional[float] = None
    # M08 is W (deferred change-detection) — intentionally absent.

    def as_dict(self) -> dict:
        return {
            "runs": self.runs,
            "M01_$/BRD": self.m01_cost_per_brd,
            "M02_$/FRD": self.m02_cost_per_frd,
            "M03_avg_completion_score": self.m03_avg_completion_score,
            "M04_first_pass_acceptance": self.m04_first_pass_acceptance,
            "M05_docs_per_month": self.m05_docs_per_month,
            "M06_brd_frd_cycle_secs": self.m06_brd_frd_cycle_secs,
            "M07_latency_p95_ms": self.m07_latency_p95_ms,
            "M09_frd_epic_coverage": self.m09_frd_epic_coverage,
            "M10_epics_per_frd": self.m10_epics_per_frd,
            "M11_push_success_rate": self.m11_push_success_rate,
            "M08_upstream_change_alerts": "deferred (W)",
        }


def _accepted_scores(run_events: Sequence[dict]) -> list[float]:
    """M03: the validation.score preceding each gate_decision(accept), matched by artifact."""
    scores: list[float] = []
    for i, e in enumerate(run_events):
        if e.get("event") != "gate_decision" or e.get("outcome") != "accept":
            continue
        want = _GATE_ARTIFACT.get(e.get("gate"))
        for prev in reversed(run_events[:i]):              # nearest preceding validation
            if prev.get("event") == "validation" and prev.get("artifact") == want:
                scores.append(prev["score"])
                break
    return scores


def _first_pass(run_events: Sequence[dict]) -> Optional[bool]:
    """M04 per run: True iff G1 was accepted at version=1 with no prior G1 reopen.

    Returns None when the run never reached G1 (excluded from the denominator)."""
    reached = False
    seen_reopen = False
    for e in run_events:
        if e.get("event") != "gate_decision" or e.get("gate") != "G1":
            continue
        reached = True
        if e.get("outcome") == "reopen":
            seen_reopen = True
        elif e.get("outcome") == "accept":
            return e.get("version") == 1 and not seen_reopen
    return False if reached else None     # reached G1 but never accepted → in denominator, not numerator


def _gate_accept_ts(run_events: Sequence[dict], gate: str) -> Optional[datetime]:
    for e in run_events:
        if (e.get("event") == "gate_decision" and e.get("gate") == gate
                and e.get("outcome") == "accept"):
            return _parse_ts(e["ts"])
    return None


def scan(path: str | Path) -> Metrics:
    """Derive every MVP metric from the telemetry stream at ``path`` (§8.2). Pure."""
    events = load_events(path)
    runs = _by_run(events)

    brd_costs, frd_costs, completion_scores = [], [], []
    first_pass_flags: list[bool] = []
    cycle_times: list[float] = []
    durations: list[int] = []
    months: Counter[str] = Counter()
    jira_scores: list[float] = []
    epics: list[int] = []
    push_total = push_ok = 0

    for e in events:
        ev = e.get("event")
        if ev == "stage_completed":
            durations.append(e["duration_ms"])
        elif ev == "run_started":
            months[e["ts"][:7]] += 1
        elif ev == "jira_push":
            push_total += 1
            push_ok += 1 if e.get("success") else 0
            epics.append(e.get("epics", 0))

    for run_events in runs.values():
        brd = sum(e["cost_usd"] for e in run_events
                  if e.get("event") == "model_call" and e.get("stage") in _BRD_STAGES)
        frd = sum(e["cost_usd"] for e in run_events
                  if e.get("event") == "model_call" and e.get("stage") == "frd_authoring")
        if any(e.get("event") == "model_call" and e.get("stage") in _BRD_STAGES for e in run_events):
            brd_costs.append(brd)
        if any(e.get("event") == "model_call" and e.get("stage") == "frd_authoring" for e in run_events):
            frd_costs.append(frd)

        completion_scores += _accepted_scores(run_events)

        fp = _first_pass(run_events)
        if fp is not None:
            first_pass_flags.append(fp)

        g1, g2 = _gate_accept_ts(run_events, "G1"), _gate_accept_ts(run_events, "G2")
        if g1 and g2:
            cycle_times.append((g2 - g1).total_seconds())

        jira_scores += [e["score"] for e in run_events
                        if e.get("event") == "validation" and e.get("artifact") == "jira"]

    return Metrics(
        runs=len(runs),
        m01_cost_per_brd=_mean(brd_costs),
        m02_cost_per_frd=_mean(frd_costs),
        m03_avg_completion_score=_mean(completion_scores),
        m04_first_pass_acceptance=(round(sum(first_pass_flags) / len(first_pass_flags), 4)
                                   if first_pass_flags else None),
        m05_docs_per_month=dict(sorted(months.items())),
        m06_brd_frd_cycle_secs=_mean(cycle_times),
        m07_latency_p95_ms=p95(durations),
        m09_frd_epic_coverage=_mean(jira_scores),
        m10_epics_per_frd=_mean(epics),
        m11_push_success_rate=(round(push_ok / push_total, 4) if push_total else None),
    )


def main(argv: Sequence[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description="§8.2 metrics scan over telemetry.jsonl")
    parser.add_argument("telemetry", help="path to a run's ledger/telemetry.jsonl")
    ns = parser.parse_args(argv)

    metrics = scan(ns.telemetry)
    print(json.dumps(metrics.as_dict(), indent=2))
    return 0


# ──────────────────────────────────────────────────────────────────────────────
# Demonstration (TASK-048 fixture/proof — a synthetic telemetry stream). Run:
#   python3 core/scripts/metrics_scan.py --demo
# Two runs: A = clean first-pass BRD→FRD; B = G1 reopen→v2 then accept. No jira (slice).
# Proves every MVP metric derives from telemetry ALONE — no hand entry (NFR-06).
# ──────────────────────────────────────────────────────────────────────────────
def _demo() -> None:
    import tempfile

    def ev(run, ts, event, **p):
        return {"ts": ts, "run_id": run, "domain": "payment_brand", "tool": "claude",
                "event": event, **p}

    stream = [
        # ── Run A — first-pass accept on both gates ──
        ev("rA", "2026-06-10T09:00:00Z", "run_started", path="/w/rA", registry_sha="7d2e9a1"),
        ev("rA", "2026-06-10T09:01:00Z", "stage_completed", stage="ingest", duration_ms=12000),
        ev("rA", "2026-06-10T09:02:00Z", "stage_completed", stage="code_map", duration_ms=8000),
        ev("rA", "2026-06-10T09:05:00Z", "model_call", stage="brd_authoring",
           model="claude-opus-4-8", tokens_in=18000, tokens_out=4200, cost_usd=0.90),
        ev("rA", "2026-06-10T09:06:00Z", "model_call", stage="code_impact",
           model="claude-opus-4-8", tokens_in=9000, tokens_out=1500, cost_usd=0.10),
        ev("rA", "2026-06-10T09:07:00Z", "validation", artifact="brd", score=88.0),
        ev("rA", "2026-06-10T09:08:00Z", "gate_decision", gate="G1", outcome="accept",
           actor="vmunjal", version=1),
        ev("rA", "2026-06-10T09:20:00Z", "model_call", stage="frd_authoring",
           model="claude-opus-4-8", tokens_in=12000, tokens_out=3000, cost_usd=0.50),
        ev("rA", "2026-06-10T09:21:00Z", "validation", artifact="frd", score=92.0),
        ev("rA", "2026-06-10T09:23:00Z", "gate_decision", gate="G2", outcome="accept",
           actor="vmunjal", version=1),
        # ── Run B — G1 reopened once (v1) then accepted (v2): NOT first-pass ──
        ev("rB", "2026-07-02T10:00:00Z", "run_started", path="/w/rB", registry_sha="7d2e9a1"),
        ev("rB", "2026-07-02T10:01:00Z", "stage_completed", stage="ingest", duration_ms=30000),
        ev("rB", "2026-07-02T10:05:00Z", "model_call", stage="brd_authoring",
           model="claude-opus-4-8", tokens_in=20000, tokens_out=5000, cost_usd=1.10),
        ev("rB", "2026-07-02T10:07:00Z", "validation", artifact="brd", score=80.0),
        ev("rB", "2026-07-02T10:08:00Z", "gate_decision", gate="G1", outcome="reopen",
           actor="vmunjal", version=1),
        ev("rB", "2026-07-02T10:15:00Z", "validation", artifact="brd", score=90.0),
        ev("rB", "2026-07-02T10:16:00Z", "gate_decision", gate="G1", outcome="accept",
           actor="vmunjal", version=2),
        ev("rB", "2026-07-02T10:30:00Z", "model_call", stage="frd_authoring",
           model="claude-opus-4-8", tokens_in=11000, tokens_out=2800, cost_usd=0.46),
        ev("rB", "2026-07-02T10:31:00Z", "validation", artifact="frd", score=86.0),
        ev("rB", "2026-07-02T10:33:00Z", "gate_decision", gate="G2", outcome="accept",
           actor="vmunjal", version=1),
    ]

    with tempfile.TemporaryDirectory(prefix="metrics-scan-") as tmp:
        tpath = Path(tmp) / "telemetry.jsonl"
        tpath.write_text("\n".join(json.dumps(e) for e in stream) + "\n")
        m = scan(tpath)

    print(json.dumps(m.as_dict(), indent=2))

    # Hand-derived expectations (the proof that the scan derives, not invents):
    assert m.runs == 2, m.runs
    assert m.m01_cost_per_brd == round((1.00 + 1.10) / 2, 4), m.m01_cost_per_brd   # (0.90+0.10),(1.10)
    assert m.m02_cost_per_frd == round((0.50 + 0.46) / 2, 4), m.m02_cost_per_frd
    assert m.m03_avg_completion_score == round((88 + 92 + 90 + 86) / 4, 4), m.m03_avg_completion_score
    assert m.m04_first_pass_acceptance == 0.5, m.m04_first_pass_acceptance        # A first-pass, B not
    assert m.m05_docs_per_month == {"2026-06": 1, "2026-07": 1}, m.m05_docs_per_month
    assert m.m06_brd_frd_cycle_secs == _mean([15 * 60, 17 * 60]), m.m06_brd_frd_cycle_secs
    assert m.m07_latency_p95_ms == 30000, m.m07_latency_p95_ms
    assert m.m09_frd_epic_coverage is None, m.m09_frd_epic_coverage               # no jira (slice)
    assert m.m11_push_success_rate is None, m.m11_push_success_rate
    print("\nPASS — every MVP metric derived from the synthetic stream alone; "
          "jira metrics None (BRD→FRD slice); no hand entry (NFR-06).")


if __name__ == "__main__":
    import sys
    if "--demo" in sys.argv:
        _demo()
    else:
        raise SystemExit(main())
