#!/usr/bin/env python3
"""metrics_scan.py — derive the MVP metrics from `telemetry.jsonl` (§8.2, FR-MX-01/02, NFR-06).

Read-only scan of the run ledger. **Every metric is computed here from the events alone — no
metric is hand-entered.** The §8.1 events are the single source, which is what makes the numbers
an observation of the run rather than a report about it.

Re-cut at TASK-125 for the amended FR-MX-02 — the pre-pivot metrics died with the artifacts they
measured, and no retired name survives anywhere in this file (the fixture sweeps for them):

  M01 $/SI-v1        Σ model_call.cost_usd where stage = si_v1
  M02 $/enrichment   Σ model_call.cost_usd where stage ∈ {enrichment, si_v2}
                     # BOTH stages: the apply pass is enrichment's cost, not a separate one, and
                     # splitting them would understate what the stage costs to run
  M03 avg score at acceptance   mean validation.score preceding each gate_decision(accept)
  M04 first-pass acceptance     G1 accepted at version=1 with no prior reopen / runs reaching G1
  M05 docs/month                run_started per calendar month
  M06 v1→v2 cycle time          ts(G2 accept) − ts(G1 accept)
  M07 latency p95               p95 of stage_completed.duration_ms
  M09 §16→story coverage        validation(artifact=jira).score preceding the run's push
  M10 stories/epic              Σ jira_push.stories / Σ jira_push.epics
  M11 push success rate         jira_push.success / jira_push
  M12 ENRICHMENT YIELD          corrections + derived impacts + auto-fills per run
  M08 upstream alerts           W — depends on deferred change-detection; NOT computed

**M12 is the new one and the reason `verdict.route` exists.** It is the v1→v2 delta — the
stage's value story in one number — and it falls out of a single field rather than needing its
own instrumentation: `auto_correct` + `auto_write` + `auto_fill` counted off the verdict events.

A metric with no events yields ``None``, never 0. A run that never reached G3 has no push-success
*rate*; reporting 0% would be a claim, and the honest answer is that the question does not apply.
The one place 0 IS meaningful is M12: a run that produced verdicts and enriched nothing yielded
zero, and that is a finding about the run, not a missing measurement.

Everything is computed **per run and then averaged**, never pooled across runs. Pooling would let
one long run dominate a fleet metric — and M09 in particular is a per-run score, so a global "last
jira validation" would report one run's number as if it were everyone's.
"""
from __future__ import annotations

import json
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional, Sequence

# gate → the artifact whose validation precedes its accept (§8.2 M03). Post-ADR-008 artifacts.
_GATE_ARTIFACT = {"G1": "si_v1", "G2": "enrichment", "G3": "jira"}

# M02 counts BOTH enrichment stages — see the module note.
_ENRICHMENT_STAGES = {"enrichment", "si_v2"}

# M12's three routes: a correction, a derived impact, a gap closure. Anything else (escalate,
# none) is not yield — an escalation is work the operator did, not value enrichment produced.
_YIELD_ROUTES = {"auto_correct", "auto_write", "auto_fill"}


def load_events(path: str | Path) -> list[dict]:
    """Parse `telemetry.jsonl` → events in file (append) order. Blank lines skipped."""
    return [json.loads(line) for line in Path(path).read_text().splitlines() if line.strip()]


def _by_run(events: Sequence[dict]) -> dict[str, list[dict]]:
    runs: dict[str, list[dict]] = defaultdict(list)
    for e in events:
        runs[e.get("run_id", "?")].append(e)
    return runs


def _parse_ts(ts: str) -> datetime:
    return datetime.strptime(ts, "%Y-%m-%dT%H:%M:%SZ")


def p95(values: Sequence[float]) -> Optional[float]:
    if not values:
        return None
    ordered = sorted(values)
    idx = max(0, min(len(ordered) - 1, round(0.95 * (len(ordered) - 1))))
    return float(ordered[idx])


def _mean(values: Sequence[float]) -> Optional[float]:
    return (sum(values) / len(values)) if values else None


@dataclass
class Metrics:
    m01_cost_si_v1: Optional[float] = None
    m02_cost_enrichment: Optional[float] = None
    m03_avg_score_at_acceptance: Optional[float] = None
    m04_first_pass_acceptance: Optional[float] = None
    m05_docs_per_month: dict = field(default_factory=dict)
    m06_v1_to_v2_seconds: Optional[float] = None
    m07_latency_p95_ms: Optional[float] = None
    m09_story_coverage_at_push: Optional[float] = None
    m10_stories_per_epic: Optional[float] = None
    m11_push_success_rate: Optional[float] = None
    m12_enrichment_yield: Optional[float] = None
    m12_breakdown: dict = field(default_factory=dict)
    m08_upstream_change_alerts: str = "deferred (W)"
    runs: int = 0

    def as_dict(self) -> dict:
        d = {k: v for k, v in self.__dict__.items()}
        return d


def _accepted_scores(run_events: Sequence[dict]) -> list[float]:
    """The validation score immediately preceding each accepted gate (§8.2 M03)."""
    out, pending = [], {}
    for e in run_events:
        if e["event"] == "validation":
            pending[e["artifact"]] = e["score"]
        elif e["event"] == "gate_decision" and e.get("outcome") == "accept":
            art = _GATE_ARTIFACT.get(e.get("gate"))
            if art in pending:
                out.append(pending[art])
    return out


def _first_pass(run_events: Sequence[dict]) -> Optional[bool]:
    """True iff G1 was accepted at version 1 with no prior reopen. ``None`` if G1 never ran."""
    seen = False
    for e in run_events:
        if e["event"] != "gate_decision" or e.get("gate") != "G1":
            continue
        seen = True
        if e.get("outcome") == "reopen":
            return False
        if e.get("outcome") == "accept":
            return e.get("version") == 1
    return False if seen else None


def _gate_accept_ts(run_events: Sequence[dict], gate: str) -> Optional[datetime]:
    for e in run_events:
        if (e["event"] == "gate_decision" and e.get("gate") == gate
                and e.get("outcome") == "accept"):
            return _parse_ts(e["ts"])
    return None


def _coverage_at_push(run_events: Sequence[dict]) -> Optional[float]:
    """M09 — the jira validation score standing at the moment this run pushed.

    Scoped to *this run* and to the score in force **when the push happened**: a later re-score
    after the push says nothing about what was pushed. ``None`` if the run never pushed.
    """
    latest = None
    for e in run_events:
        if e["event"] == "validation" and e.get("artifact") == "jira":
            latest = e["score"]
        elif e["event"] == "jira_push":
            return latest
    return None


def scan(path: str | Path) -> Metrics:
    """Derive every amended MVP metric from one telemetry stream."""
    events = load_events(path)
    runs = _by_run(events)
    m = Metrics(runs=len(runs))

    si_costs, enr_costs, scores, first, cycles, coverage = [], [], [], [], [], []
    yield_counts: Counter = Counter()
    yields: list[int] = []          # one entry per run that ran enrichment at all
    pushes, push_ok, epics, stories = 0, 0, 0, 0
    months: Counter = Counter()

    for run_events in runs.values():
        si = sum(e["cost_usd"] for e in run_events
                 if e["event"] == "model_call" and e.get("stage") == "si_v1")
        enr = sum(e["cost_usd"] for e in run_events
                  if e["event"] == "model_call" and e.get("stage") in _ENRICHMENT_STAGES)
        if any(e["event"] == "model_call" and e.get("stage") == "si_v1" for e in run_events):
            si_costs.append(si)
        if any(e["event"] == "model_call" and e.get("stage") in _ENRICHMENT_STAGES
               for e in run_events):
            enr_costs.append(enr)

        scores += _accepted_scores(run_events)
        fp = _first_pass(run_events)
        if fp is not None:
            first.append(fp)

        g1, g2 = _gate_accept_ts(run_events, "G1"), _gate_accept_ts(run_events, "G2")
        if g1 and g2:
            cycles.append((g2 - g1).total_seconds())

        cov = _coverage_at_push(run_events)
        if cov is not None:
            coverage.append(cov)

        run_yield, saw_verdict = 0, False
        for e in run_events:
            if e["event"] == "run_started":
                months[e["ts"][:7]] += 1
            elif e["event"] == "verdict":
                saw_verdict = True
                if e.get("route") in _YIELD_ROUTES:
                    yield_counts[e["route"]] += 1
                    run_yield += 1
            elif e["event"] == "jira_push":
                pushes += 1
                push_ok += 1 if e.get("success") else 0
                epics += e["epics"]
                stories += e["stories"]
        if saw_verdict:
            yields.append(run_yield)

    m.m01_cost_si_v1 = _mean(si_costs)
    m.m02_cost_enrichment = _mean(enr_costs)
    m.m03_avg_score_at_acceptance = _mean(scores)
    m.m04_first_pass_acceptance = (sum(first) / len(first)) if first else None
    m.m05_docs_per_month = dict(sorted(months.items()))
    m.m06_v1_to_v2_seconds = _mean(cycles)
    m.m07_latency_p95_ms = p95([e["duration_ms"] for e in events
                                if e["event"] == "stage_completed"])
    m.m09_story_coverage_at_push = _mean(coverage)
    m.m10_stories_per_epic = (stories / epics) if epics else None
    m.m11_push_success_rate = (push_ok / pushes) if pushes else None
    m.m12_enrichment_yield = _mean(yields)
    m.m12_breakdown = {"corrections": yield_counts["auto_correct"],
                       "derived_impacts": yield_counts["auto_write"],
                       "auto_fills": yield_counts["auto_fill"]}
    return m


def main(argv: Sequence[str] | None = None) -> int:
    import argparse
    ap = argparse.ArgumentParser(description="Derive the MVP metrics from telemetry.jsonl (§8.2)")
    ap.add_argument("telemetry", help="path to a run's ledger/telemetry.jsonl")
    args = ap.parse_args(argv)
    print(json.dumps(scan(args.telemetry).as_dict(), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
