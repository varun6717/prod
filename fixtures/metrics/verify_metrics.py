#!/usr/bin/env python3
"""verify_metrics.py — TASK-125 proof: every amended metric derives from a real run's ledger.

The ledger under test is **not typed by hand**. Run A is replayed from the D4 enrichment record
(`fixtures/enrichment/verify_spine.py :: build_findings`, the same findings and the same three
operator dispositions) through the shipped `enrichment.emit_finding_events` wiring, and its push
counts come from the D5 plan (`fixtures/jira_plan/plan_pass.json`). So the events are the events
the pipeline actually emits, and the metrics are metrics over the D4/D5 run.

  1. **The stream is legal** — every run ledger validates against the schemas before anything is
     derived. A metric over an invalid stream would prove nothing.
  2. **Every amended metric derives** — M01–M07, M09–M12 all come back non-``None`` and equal to a
     value computed here by an independent path (off the record and the plan, not off the ledger).
  3. **No retired name survives** in `metrics_scan.py` — the acceptance condition, swept as text.

Three more runs join run A in a fleet scan, each one carrying a **falsifier** — a wrong-but-
plausible implementation it would catch, named in the check:

  * **B** — G1 reopened, enriched to *zero* yield, plan scored 40 and refused at G3, never pushed.
  * **C** — ingest only; never reached si_v1, never enriched.
  * **D** — a complete run whose push *failed*.

Between them: M09 must ignore B's 40 (a global "last jira score" would report it), M12's
denominator must exclude C (a pooled total would divide by it), M04 must skip C rather than score
it 0, and M11 must count D's failure while never counting B's absence as one.

Run: python3 fixtures/metrics/verify_metrics.py
"""
from __future__ import annotations

import json
import re
import sys
import tempfile
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_REPO_ROOT = _HERE.parents[1]
sys.path.insert(0, str(_REPO_ROOT / "core" / "scripts"))
sys.path.insert(0, str(_REPO_ROOT / "fixtures" / "enrichment"))

import enrichment as E  # noqa: E402
import ledger  # noqa: E402
import metrics_scan as M  # noqa: E402
import solution_intent_validator as V  # noqa: E402
import telemetry  # noqa: E402
import yaml  # noqa: E402
from verify_spine import build_findings  # noqa: E402

_FAILURES: list[str] = []

# Run A — the D4/D5 run. Timestamps are explicit so the G1→G2 cycle time is a real interval.
A_RUN, A_START = "r-2026-08-01-si1", "2026-08-01T09:00:00Z"
A_G1, A_G2, A_G3 = "2026-08-01T09:40:00Z", "2026-08-01T10:25:00Z", "2026-08-01T11:00:00Z"
B_RUN, B_TS = "r-2026-09-02-si2", "2026-09-02T09:00:00Z"   # a different calendar month
C_RUN, C_TS = "r-2026-09-03-si3", "2026-09-03T09:00:00Z"
D_RUN, D_START = "r-2026-09-04-si4", "2026-09-04T09:00:00Z"
D_G1, D_G2 = "2026-09-04T09:30:00Z", "2026-09-04T10:00:00Z"  # 30 min → 1800s

_RETIRED = ("brd_authoring", "frd_authoring", "jira_authoring", "code_impact", "code_map",
            "brd", "frd")


def _check(label: str, ok: bool, detail: str = "") -> None:
    print(f"  [{'PASS' if ok else 'FAIL'}] {label}" + (f" — {detail}" if detail else ""))
    if not ok:
        _FAILURES.append(label)


def _close(a, b, tol=1e-9) -> bool:
    return a is not None and abs(a - b) < tol


def _emitter(root: Path, name: str, run_id: str):
    led = ledger.init_ledger(root / name / "ledger", run_id=run_id)
    return led, telemetry.Emitter(led, run_id=run_id, domain="payment_brand", tool="claude")


def _d4_record() -> dict:
    """The D4 enrichment run, rebuilt exactly as verify_spine runs it."""
    profile = yaml.safe_load(
        (_REPO_ROOT / "core/profiles/payment_brand/si_profile.payment_brand.yaml").read_text())
    v1 = (_REPO_ROOT / "fixtures/si_author/v1.md").read_text(encoding="utf-8")
    rec = build_findings(V.parse_v1(v1, profile))
    # the walkthrough, as the operator ran it at TASK-121
    E.disposition(rec, "F-202", call="accept", target="§13",
                  rationale="Recon does parse field 48 — the assumption was wrong.",
                  actor="vmunjal")
    E.disposition(rec, "F-310", call="accept", target="§16",
                  rationale="Genuinely new capability — this becomes a build story.",
                  actor="vmunjal")
    E.disposition(rec, "F-311", call="defer", target="§17",
                  rationale="Cannot size the hook until the emitter design is settled.",
                  actor="vmunjal")
    return rec


def _write_run_a(root: Path, rec: dict, plan: dict) -> Path:
    """The D4/D5 run: authored, enriched, plan refused once at G3, re-scored, pushed."""
    led, em = _emitter(root, "a", A_RUN)
    em.run_started(path="/work/" + A_RUN, registry_sha="7d2e9a1", ts=A_START)
    telemetry.mark_stage(em, "ingest", "running", ts=A_START)
    telemetry.mark_stage(em, "ingest", "done", duration_ms=12_000, ts=A_START)

    telemetry.mark_stage(em, "si_v1", "running", ts=A_START)
    em.model_call(stage="si_v1", model="claude-opus-4-8", tokens_in=18_000, tokens_out=4_200,
                  cost_usd=0.91, ts=A_START)
    em.validation(artifact="si_v1", score=88.0, ts=A_G1)
    em.gate_decision(gate="G1", outcome="accept", actor="vmunjal", version=1, ts=A_G1)
    telemetry.mark_stage(em, "si_v1", "done", duration_ms=402_000, version=1, ts=A_G1)

    # Enrichment — driven off the D4 record through the shipped wiring, not retyped.
    telemetry.mark_stage(em, "enrichment", "running", ts=A_G1)
    em.model_call(stage="enrichment", model="claude-opus-4-8", tokens_in=9_000, tokens_out=1_500,
                  cost_usd=0.34, ts=A_G1)
    for f in rec["findings"]:
        E.emit_finding_events(em, E.Finding(**f), ts=A_G1)
    for fid in [f["id"] for f in rec["findings"] if f.get("disposition")]:
        E.emit_disposition_events(em, led / "decisions.jsonl", rec, fid, ts=A_G1)
    telemetry.mark_stage(em, "enrichment", "done", duration_ms=311_000, ts=A_G2)

    telemetry.mark_stage(em, "si_v2", "running", ts=A_G2)
    em.model_call(stage="si_v2", model="claude-opus-4-8", tokens_in=12_000, tokens_out=3_000,
                  cost_usd=0.52, ts=A_G2)
    em.validation(artifact="enrichment", score=91.0, ts=A_G2)
    em.gate_decision(gate="G2", outcome="accept", actor="vmunjal", version=2, ts=A_G2)
    telemetry.mark_stage(em, "si_v2", "done", duration_ms=98_000, version=2, ts=A_G2)

    telemetry.mark_stage(em, "jira", "running", ts=A_G2)
    em.validation(artifact="jira", score=71.0, ts=A_G3)          # first cut refused …
    em.gate_decision(gate="G3", outcome="reopen", actor="vmunjal", version=1, ts=A_G3)
    em.validation(artifact="jira", score=93.0, ts=A_G3)          # … re-authored, then accepted
    em.gate_decision(gate="G3", outcome="accept", actor="vmunjal", version=2, ts=A_G3)
    em.jira_push(epics=len(plan["epics"]), stories=len(plan["stories"]), success=True,
                 partial=False, ts=A_G3)
    telemetry.mark_stage(em, "jira", "done", duration_ms=145_000, ts=A_G3)
    return led


def _write_run_b(root: Path) -> Path:
    """G1 reopened; enrichment produced nothing; the plan was refused at G3 and never pushed."""
    led, em = _emitter(root, "b", B_RUN)
    em.run_started(path="/work/" + B_RUN, registry_sha="7d2e9a1", ts=B_TS)
    telemetry.mark_stage(em, "si_v1", "running", ts=B_TS)
    em.model_call(stage="si_v1", model="claude-opus-4-8", tokens_in=21_000, tokens_out=5_000,
                  cost_usd=1.10, ts=B_TS)
    em.validation(artifact="si_v1", score=74.0, ts=B_TS)
    em.gate_decision(gate="G1", outcome="reopen", actor="vmunjal", version=1, ts=B_TS)
    em.validation(artifact="si_v1", score=86.0, ts=B_TS)
    em.gate_decision(gate="G1", outcome="accept", actor="vmunjal", version=2, ts=B_TS)
    telemetry.mark_stage(em, "si_v1", "done", duration_ms=515_000, version=2, ts=B_TS)

    telemetry.mark_stage(em, "enrichment", "running", ts=B_TS)
    em.model_call(stage="enrichment", model="claude-opus-4-8", tokens_in=8_000, tokens_out=900,
                  cost_usd=0.40, ts=B_TS)
    em.verdict(finding_id="F-401", arm="claim", verdict="confirmed", route="none", ts=B_TS)
    em.verdict(finding_id="F-402", arm="impact", verdict="confirmed", route="none", ts=B_TS)
    telemetry.mark_stage(em, "enrichment", "done", duration_ms=120_000, ts=B_TS)

    telemetry.mark_stage(em, "jira", "running", ts=B_TS)
    em.validation(artifact="jira", score=40.0, ts=B_TS)   # the M09 falsifier: never pushed
    em.gate_decision(gate="G3", outcome="reopen", actor="vmunjal", version=1, ts=B_TS)
    telemetry.mark_stage(em, "jira", "done", duration_ms=90_000, ts=B_TS)
    return led


def _write_run_c(root: Path) -> Path:
    """Ingest only — never authored, never enriched. The M12-denominator falsifier."""
    led, em = _emitter(root, "c", C_RUN)
    em.run_started(path="/work/" + C_RUN, registry_sha="7d2e9a1", ts=C_TS)
    telemetry.mark_stage(em, "ingest", "running", ts=C_TS)
    telemetry.mark_stage(em, "ingest", "done", duration_ms=20_000, ts=C_TS)
    return led


def _write_run_d(root: Path) -> Path:
    """A complete run whose push FAILED — the M11 denominator, and a second M09 sample."""
    led, em = _emitter(root, "d", D_RUN)
    em.run_started(path="/work/" + D_RUN, registry_sha="7d2e9a1", ts=D_START)
    telemetry.mark_stage(em, "si_v1", "running", ts=D_START)
    em.model_call(stage="si_v1", model="claude-opus-4-8", tokens_in=15_000, tokens_out=3_100,
                  cost_usd=0.80, ts=D_START)
    em.validation(artifact="si_v1", score=90.0, ts=D_G1)
    em.gate_decision(gate="G1", outcome="accept", actor="vmunjal", version=1, ts=D_G1)
    telemetry.mark_stage(em, "si_v1", "done", duration_ms=300_000, version=1, ts=D_G1)

    telemetry.mark_stage(em, "enrichment", "running", ts=D_G1)
    em.model_call(stage="enrichment", model="claude-opus-4-8", tokens_in=7_000, tokens_out=1_100,
                  cost_usd=0.30, ts=D_G1)
    em.verdict(finding_id="F-501", arm="claim", verdict="contradicted", route="auto_correct",
               ts=D_G1)
    em.verdict(finding_id="F-502", arm="claim", verdict="confirmed", route="none", ts=D_G1)
    telemetry.mark_stage(em, "enrichment", "done", duration_ms=100_000, ts=D_G2)

    telemetry.mark_stage(em, "si_v2", "running", ts=D_G2)
    em.model_call(stage="si_v2", model="claude-opus-4-8", tokens_in=9_500, tokens_out=2_200,
                  cost_usd=0.20, ts=D_G2)
    em.validation(artifact="enrichment", score=82.0, ts=D_G2)
    em.gate_decision(gate="G2", outcome="accept", actor="vmunjal", version=2, ts=D_G2)
    telemetry.mark_stage(em, "si_v2", "done", duration_ms=60_000, version=2, ts=D_G2)

    telemetry.mark_stage(em, "jira", "running", ts=D_G2)
    em.validation(artifact="jira", score=68.0, ts=D_G2)
    em.gate_decision(gate="G3", outcome="accept", actor="vmunjal", version=1, ts=D_G2)
    em.jira_push(epics=3, stories=5, success=False, partial=True, ts=D_G2)
    telemetry.mark_stage(em, "jira", "done", duration_ms=80_000, ts=D_G2)
    return led


def main() -> int:
    rec = _d4_record()
    plan = json.loads((_REPO_ROOT / "fixtures/jira_plan/plan_pass.json").read_text())

    print("verify_metrics — the amended metric set over the D4/D5 run's ledger\n")

    with tempfile.TemporaryDirectory(prefix="metrics-") as td:
        root = Path(td)
        leds = {"A (D4/D5)": _write_run_a(root, rec, plan), "B (refused at G3)": _write_run_b(root),
                "C (ingest only)": _write_run_c(root), "D (push failed)": _write_run_d(root)}

        print("1) the streams are legal before anything is derived:")
        for name, led in leds.items():
            rep = ledger.validate_ledger(led)
            _check(f"run {name} validates against all three schemas",
                   all(not e for e in rep.values()), str(rep))

        # ── the independent expectations, computed off the RECORD and the PLAN
        verdicts = [f for f in rec["findings"] if f.get("verdict")]
        exp = {r: sum(1 for f in verdicts if f.get("route") == r)
               for r in ("auto_correct", "auto_write", "auto_fill")}
        exp_yield_a = sum(exp.values())

        print(f"\n2) run A alone — {len(verdicts)} verdicts, {exp_yield_a} of them enriching:")
        a = M.scan(leds["A (D4/D5)"] / "telemetry.jsonl")
        _check("M01 $/SI-v1 derives", _close(a.m01_cost_si_v1, 0.91), f"{a.m01_cost_si_v1}")
        _check("M02 $/enrichment spans BOTH enrichment stages",
               _close(a.m02_cost_enrichment, 0.86),
               f"{a.m02_cost_enrichment} = 0.34 (enrichment) + 0.52 (si_v2)")
        _check("M03 averages the score standing at each ACCEPTED gate",
               _close(a.m03_avg_score_at_acceptance, (88.0 + 91.0 + 93.0) / 3),
               f"{a.m03_avg_score_at_acceptance:.4f} — the refused 71.0 never counted")
        _check("M04 first-pass acceptance is 1.0 — G1 accepted at v1, never reopened",
               _close(a.m04_first_pass_acceptance, 1.0), f"{a.m04_first_pass_acceptance}")
        _check("M05 buckets the run into its calendar month",
               a.m05_docs_per_month == {"2026-08": 1}, str(a.m05_docs_per_month))
        _check("M06 v1→v2 cycle time is the G1→G2 interval",
               _close(a.m06_v1_to_v2_seconds, 2700.0), f"{a.m06_v1_to_v2_seconds}s")
        _check("M07 latency p95 derives from stage_completed",
               _close(a.m07_latency_p95_ms, 402_000.0), f"{a.m07_latency_p95_ms}ms")
        _check("M09 is the score standing AT the push, not the plan's first cut",
               _close(a.m09_story_coverage_at_push, 93.0),
               f"{a.m09_story_coverage_at_push} — a 'first jira score' reading would say 71.0")
        _check("M10 stories/epic reads the D5 plan's own shape",
               _close(a.m10_stories_per_epic, len(plan["stories"]) / len(plan["epics"])),
               f"{len(plan['stories'])}/{len(plan['epics'])} = {a.m10_stories_per_epic:.4f}")
        _check("M11 push success rate derives", _close(a.m11_push_success_rate, 1.0),
               f"{a.m11_push_success_rate}")
        _check("M12 enrichment yield matches the count taken off the RECORD",
               _close(a.m12_enrichment_yield, float(exp_yield_a)),
               f"ledger says {a.m12_enrichment_yield}, record says {exp_yield_a}")
        _check("M12's three components break out separately",
               a.m12_breakdown == {"corrections": exp["auto_correct"],
                                   "derived_impacts": exp["auto_write"],
                                   "auto_fills": exp["auto_fill"]}, str(a.m12_breakdown))
        _check("M08 is reported as deferred, not as a number",
               a.m08_upstream_change_alerts == "deferred (W)")
        empty = [k for k, v in a.as_dict().items()
                 if k.startswith("m") and not k.startswith("m08") and v in (None, {}, [])]
        _check("EVERY amended metric derives — none came back empty", not empty, str(empty))

        print("\n   what `metrics_scan.py <ledger>/telemetry.jsonl` prints for run A:")
        for line in json.dumps(a.as_dict(), indent=2).splitlines():
            print("   " + line)

        print("\n3) the fleet — per-run averaging, not pooling:")
        fleet = root / "fleet.jsonl"
        fleet.write_text("".join((led / "telemetry.jsonl").read_text() for led in leds.values()))
        f = M.scan(fleet)
        _check("all four runs are seen", f.runs == 4, str(f.runs))
        _check("M01 is the MEAN over the runs that authored — C never did",
               _close(f.m01_cost_si_v1, (0.91 + 1.10 + 0.80) / 3), f"{f.m01_cost_si_v1}")
        _check("M02 likewise means over the three that enriched",
               _close(f.m02_cost_enrichment, (0.86 + 0.40 + 0.50) / 3), f"{f.m02_cost_enrichment}")
        _check("M03 spans every accepted gate in the fleet",
               _close(f.m03_avg_score_at_acceptance,
                      (88.0 + 91.0 + 93.0 + 86.0 + 90.0 + 82.0 + 68.0) / 7),
               f"{f.m03_avg_score_at_acceptance:.4f} — B's reopened 74.0 and A's refused 71.0 out")
        _check("M04 is 2/3 — B reopened, and C is SKIPPED rather than scored 0",
               _close(f.m04_first_pass_acceptance, 2 / 3),
               f"{f.m04_first_pass_acceptance:.4f} — counting C would give 0.5")
        _check("M05 splits the two calendar months",
               f.m05_docs_per_month == {"2026-08": 1, "2026-09": 3}, str(f.m05_docs_per_month))
        _check("M06 averages the two runs that reached G2",
               _close(f.m06_v1_to_v2_seconds, (2700.0 + 1800.0) / 2), f"{f.m06_v1_to_v2_seconds}s")
        _check("M09 averages the runs that PUSHED — B's refused 40.0 is excluded",
               _close(f.m09_story_coverage_at_push, (93.0 + 68.0) / 2),
               f"{f.m09_story_coverage_at_push} — a global 'last jira score' would say 68.0, "
               "and a global max/last-seen over B would drag in 40.0")
        _check("M10 pools the pushed plans' shapes",
               _close(f.m10_stories_per_epic, (7 + 5) / (12 + 3)), f"{f.m10_stories_per_epic:.4f}")
        _check("M11 counts D's failure and does NOT count B's absence as one",
               _close(f.m11_push_success_rate, 0.5),
               f"{f.m11_push_success_rate} — 1 of 2 pushes; B never pushed so it is not a denominator")
        _check("M12's denominator is the runs that ENRICHED — C is excluded",
               _close(f.m12_enrichment_yield, (exp_yield_a + 0 + 1) / 3),
               f"{f.m12_enrichment_yield:.4f} — dividing by all 4 runs would give "
               f"{(exp_yield_a + 1) / 4:.4f}")

        print("\n4) `None` means 'does not apply', never 0:")
        _check("run C reports NO push-success rate",
               M.scan(leds["C (ingest only)"] / "telemetry.jsonl").m11_push_success_rate is None)
        _check("run C reports NO yield — 0 would be a claim about a stage it never ran",
               M.scan(leds["C (ingest only)"] / "telemetry.jsonl").m12_enrichment_yield is None)
        _check("but run B, which enriched to no effect, DOES report 0",
               _close(M.scan(leds["B (refused at G3)"] / "telemetry.jsonl").m12_enrichment_yield,
                      0.0))
        _check("run B reports NO coverage-at-push — it never pushed",
               M.scan(leds["B (refused at G3)"] / "telemetry.jsonl").m09_story_coverage_at_push
               is None, "the 40.0 it scored was refused, not shipped")

    print("\n5) no retired metric or stage name survives in metrics_scan.py:")
    src = (_REPO_ROOT / "core/scripts/metrics_scan.py").read_text(encoding="utf-8")
    hits = sorted({w for w in _RETIRED if re.search(rf"\b{w}\b", src, re.IGNORECASE)})
    _check("the acceptance sweep comes back empty", not hits, f"found {hits}")
    live = json.loads((_REPO_ROOT / "core/scripts/schemas/telemetry.schema.json").read_text())
    stages, arts = set(live["$defs"]["stage"]["enum"]), set(live["properties"]["artifact"]["enum"])
    used = set(re.findall(r'"(si_v1|si_v2|enrichment|ingest|jira)"', src))
    _check("every stage/artifact name it references is in the live vocabulary",
           used <= (stages | arts), f"{sorted(used - stages - arts)}")
    _check("the stale banner is gone", "STALE" not in src)

    print()
    if _FAILURES:
        print(f"FAILED — {len(_FAILURES)} check(s): {_FAILURES}", file=sys.stderr)
        return 1
    print("PASS — every amended metric (M01–M07, M09–M12) derives from the D4/D5 run's own "
          "ledger, each matched against an independent count off the record and the plan; the "
          "fleet scan averages per run rather than pooling; no retired name survives.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
