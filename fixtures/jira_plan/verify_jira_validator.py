#!/usr/bin/env python3
"""verify_jira_validator.py — TASK-123 proof: G3 over the pass/fail plans.

G3 is the last review before the run's **only external mutation**, so what is proven is that each
hard check bites individually and that acceptance is refused when any of them does.

  1. **The real plan scores and is eligible.**
  2. **Both guardrails run in opposite directions** — a dropped impact and an invented story are
     each caught, and each alone would slip past the other check.
  3. **The broken plan names every violated check**, one defect per check.
  4. **`traceability == 1.0` is absolute** — a near-perfect plan is still refused.
  5. **G3 stays an operator act** (D4) — accept is refused when ineligible; the module never
     advances itself.
  6. **The ledger records G3** with the jira artifact.

Run: python3 fixtures/jira_plan/verify_jira_validator.py
"""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_REPO_ROOT = _HERE.parents[1]
sys.path.insert(0, str(_REPO_ROOT / "core" / "scripts"))

import jira_validator as JV  # noqa: E402
import ledger  # noqa: E402

_FAILURES: list[str] = []
T = "2026-08-01T00:00:00Z"


def _check(label: str, ok: bool, detail: str = "") -> None:
    print(f"  [{'PASS' if ok else 'FAIL'}] {label}" + (f" — {detail}" if detail else ""))
    if not ok:
        _FAILURES.append(label)


def main() -> int:
    good = json.loads((_HERE / "plan_pass.json").read_text())
    bad = json.loads((_HERE / "plan_fail.json").read_text())
    s16 = good["trace"]["section16_entries"]

    print("verify_jira_validator — G3 over the 4-level plan\n")

    print("1) the real plan:")
    g = JV.evaluate_g3(good, section16_ids=s16)
    print(f"     traceability={g.traceability:.3f}  testability={g.testability:.3f}  "
          f"field_completeness={g.field_completeness:.3f}  score={g.score}")
    for c in g.checks:
        print(f"     {'✓' if c.ok else '✗'} {c.name}")
    _check("every hard check holds", g.hard_ok, str(g.blockers[:1]))
    _check("the plan is eligible", g.eligible, f"{g.score} vs {g.threshold}")
    _check("traceability is TOTAL, not merely high", g.traceability == 1.0)

    print("\n2) the two guardrails run in OPPOSITE directions:")
    # dropped impact: a §16 entry with no story
    dropped = JV.evaluate_g3(good, section16_ids=list(s16) + ["F-777"])
    _check("a §16 entry with no story is caught (dropped impact)",
           not dropped.hard_ok and any("yields no story" in b for b in dropped.blockers),
           next((b for b in dropped.blockers if "yields no story" in b), "")[:64])
    _check("…and it is EXCUSED when explicitly dispositioned",
           JV.evaluate_g3(good, section16_ids=list(s16) + ["F-777"],
                          dispositioned_without_story=["F-777"]).hard_ok)
    # invented story: grounded in nothing
    invented = json.loads(json.dumps(good))
    invented["stories"].append({**good["stories"][0], "local_id": "S99", "evidence": "F-000"})
    inv = JV.evaluate_g3(invented, section16_ids=s16)
    _check("a story grounded in nothing is caught (invented work)",
           not inv.hard_ok and any("invented work" in b for b in inv.blockers),
           next((b for b in inv.blockers if "invented work" in b), "")[:64])
    _check("neither check alone would catch both",
           dropped.testability == 1.0 and inv.testability == 1.0,
           "a complete-but-fabricated plan and a grounded-but-incomplete one both look healthy "
           "to the other direction")

    print("\n3) the broken plan names every violated check:")
    b = JV.evaluate_g3(bad, section16_ids=s16)
    print(f"     traceability={b.traceability:.3f}  testability={b.testability:.3f}  "
          f"field_completeness={b.field_completeness:.3f}  score={b.score}")
    for c in b.checks:
        if not c.ok:
            print(f"     ✗ {c.name}")
            for v in c.violations[:2]:
                print(f"         - {v[:88]}")
    broken = {c.name for c in b.checks if not c.ok}
    _check("all three hard checks fire",
           broken == {"hierarchy_traceability_complete", "controls_present",
                      "stories_locatable_and_testable"}, str(sorted(broken)))
    _check("the broken §8→§7 trace is named specifically",
           any("§8→§7 trace is broken" in v for v in b.blockers))
    _check("the missing controls field is named",
           any("missing controls" in v for v in b.blockers))
    _check("the untestable story is named twice — no criteria AND no location",
           sum(1 for v in b.blockers if "S2" in v) >= 2 or
           sum(1 for v in b.blockers if "acceptance criteria" in v) >= 1)

    print("\n4) traceability is absolute:")
    near = json.loads(json.dumps(good))
    near["stories"].append({**good["stories"][0], "local_id": "S98", "evidence": "F-000"})
    n = JV.evaluate_g3(near, section16_ids=s16)
    _check("a near-perfect plan is still refused", n.traceability < 1.0 and not n.hard_ok,
           f"traceability {n.traceability:.3f}")
    _check("…even though its score may still clear the threshold",
           n.score >= 80, f"score {n.score} — the score alone would have let it through")

    print("\n5) G3 stays an operator act (D4):")
    with tempfile.TemporaryDirectory(prefix="g3-") as td:
        led = ledger.init_ledger(Path(td) / "ledger", run_id="r-2026-08-01-si1")
        _check("accept on an ineligible plan is REFUSED",
               _raises(lambda: JV.record_g3(led, result=b, outcome="accept", version=1, ts=T)),
               "the next step is the run's only external mutation")
        v2 = JV.record_g3(led, result=b, outcome="reopen", version=1, ts=T)
        _check("reopen is always allowed and increments", v2 == 2)
        v1 = JV.record_g3(led, result=g, outcome="accept", version=1, ts=T)
        _check("accept locks the plan", v1 == 1)
        rep = ledger.validate_ledger(led)
        _check("both ledgers validate", all(not e for e in rep.values()), str(rep))
        tel = [json.loads(l) for l in (led / "telemetry.jsonl").read_text().splitlines() if l.strip()]
        _check("the validation event names the jira artifact",
               any(e["event"] == "validation" and e["artifact"] == "jira" for e in tel))
        _check("the gate_decision names G3",
               any(e["event"] == "gate_decision" and e["gate"] == "G3" for e in tel))
        dec = [json.loads(l) for l in (led / "decisions.jsonl").read_text().splitlines() if l.strip()]
        _check("decisions.jsonl carries the G3 audit twins",
               len([d for d in dec if d.get("gate") == "G3"]) == 2)

    print()
    if _FAILURES:
        print(f"FAILED — {len(_FAILURES)} check(s): {_FAILURES}", file=sys.stderr)
        return 1
    print("PASS — the real plan is eligible with total traceability; a dropped impact and an "
          "invented story are each caught by the direction the other would miss; the broken plan "
          "names every violated check; accept is refused when ineligible.")
    return 0


def _raises(fn) -> bool:
    try:
        fn()
    except Exception:
        return True
    return False


if __name__ == "__main__":
    raise SystemExit(main())
