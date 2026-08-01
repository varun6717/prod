#!/usr/bin/env python3
"""verify_walkthrough.py — TASK-120 proof: a full disposition walkthrough session.

This is the **one human checkpoint of the entire enrichment stage**, so what is proven is that
each of D-A17's four binding constraints actually holds against a real session — not that the
skill file mentions them.

  1. **Triage, not enumerate** — material individually, advisory batched.
  2. **Dependency ordering** — upstream findings are presented before the findings derived from them.
  3. **Downstream revisit** — a `reject` on an upstream gap SUPERSEDES what rested on it.
  4. **Resumable** — an interrupted session re-enters at the right finding, losing nothing.
  5. **The defer path** lands in §17.
  6. **Propose, never decide** — an auto-applied finding cannot be dispositioned; a rationale is
     mandatory; nothing is decided without a call.
  7. **Both ledgers** carry the trail, with the rationale in the one that explains.

Run: python3 fixtures/enrichment/verify_walkthrough.py
"""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_REPO_ROOT = _HERE.parents[1]
sys.path.insert(0, str(_REPO_ROOT / "core" / "scripts"))

import enrichment as E  # noqa: E402
import ledger  # noqa: E402
import telemetry  # noqa: E402

_FAILURES: list[str] = []
T = "2026-08-01T00:00:00Z"


def _check(label: str, ok: bool, detail: str = "") -> None:
    print(f"  [{'PASS' if ok else 'FAIL'}] {label}" + (f" — {detail}" if detail else ""))
    if not ok:
        _FAILURES.append(label)


def build_session() -> dict:
    """A realistic escalated queue: one scope move, one no-code gap with two derived findings,
    one operator contradiction, and a batch of routine advisory consequences."""
    rec = E.new_record("r-2026-08-01-si1", "35ffb65ccf77")

    # material — a scope move
    E.add(rec, E.make_finding("F-301", arm="impact", kind="derived_impact", scope_moving=True,
                              requirement_ref="R6", assertion_ref="R6.1",
                              evidence=[{"path": "src/routing/dispatch.c"}],
                              reasoning="token BIN routing forces a change to the fallback path, "
                                        "which v1 placed out of scope"))
    # material — a no-code gap, with two findings DERIVED from it
    E.add(rec, E.make_finding("F-310", arm="impact", kind="no_code_found",
                              requirement_ref="R11", assertion_ref="R11.5",
                              reasoning="no MDES coverage report emitter found"))
    E.add(rec, E.make_finding("F-311", arm="impact", kind="derived_impact", business_visible=True,
                              requirement_ref="R11", depends_on_finding=["F-310"],
                              evidence=[{"path": "src/settlement/ledger_post.c"}],
                              reasoning="if the emitter must be built, settlement posting gains a "
                                        "reporting hook"))
    E.add(rec, E.make_finding("F-312", arm="impact", kind="derived_impact", business_visible=True,
                              requirement_ref="R11", depends_on_finding=["F-311"],
                              evidence=[{"path": "src/settlement/settlement_batch.c"}],
                              reasoning="…and the batch closer would need to trigger it"))
    # material — an operator contradiction
    E.add(rec, E.make_finding("F-320", arm="claim", kind="contradiction",
                              claim_provenance="operator", section_ref="§13",
                              evidence=[{"path": "src/settlement/reconciler.c"}],
                              reasoning="recon parses field 48; the §13 assumption is wrong"))
    # advisory batch — routine technical consequences
    for n in range(1, 6):
        f = E.make_finding(f"F-4{n:02d}", arm="impact", kind="derived_impact",
                           business_visible=True, requirement_ref="R2",
                           evidence=[{"path": f"src/messaging/field_codec.c"}],
                           reasoning=f"codec entry {n} widens with the new subelement")
        f.severity = "advisory"          # D6c: routine consequence, no business visibility
        E.add(rec, f)
    return rec


def main() -> int:
    rec = build_session()
    print("verify_walkthrough — a full disposition session\n")
    print(f"  {len(rec['findings'])} findings, "
          f"{len(E.pending(rec))} escalated and awaiting a human\n")

    # 1) triage
    print("1) triage, do not enumerate (D-A17 constraint 2):")
    tri = E.triage(rec)
    _check("material findings are presented individually",
           {f["id"] for f in tri["individual"]} == {"F-301", "F-310", "F-311", "F-312", "F-320"},
           str(sorted(f["id"] for f in tri["individual"])))
    _check("advisory findings are batched, not marched through one by one",
           tri["batched"] == 5 and len(tri["batches"]) == 1,
           f"{tri['batched']} in {len(tri['batches'])} batch(es)")
    _check("batching does not hide them — the batch names its reason and members",
           all(v and k for k, v in tri["batches"].items()), str(list(tri["batches"])))
    _check("a scope-moving finding is NEVER batched",
           all(f["id"] != "F-301" for v in tri["batches"].values() for f in v))

    # 2) dependency ordering
    print("\n2) dependency ordering (constraint 3):")
    order = [f["id"] for f in E.walkthrough_order(rec)]
    _check("the upstream gap precedes what was derived from it",
           order.index("F-310") < order.index("F-311") < order.index("F-312"),
           " → ".join(order[:6]))
    _check("the order is deterministic — an interrupted session resumes to the same queue",
           order == [f["id"] for f in E.walkthrough_order(rec)])

    # 3) the operator works the queue; an upstream reversal supersedes downstream
    print("\n3) downstream revisit after an upstream reversal:")
    E.disposition(rec, "F-301", call="reroute", target="§12",
                  rationale="The fallback path is genuinely out of scope this release; record "
                            "the coupling as an exclusion rather than absorbing the work.",
                  actor="vmunjal")
    E.disposition(rec, "F-310", call="reject",
                  rationale="Arm 1 missed it — the emitter lives in the reporting repo, not here.",
                  actor="vmunjal")
    superseded = E.supersede_dependents(rec, "F-310")
    _check("rejecting the upstream gap supersedes BOTH derived findings",
           set(superseded) == {"F-311", "F-312"}, str(sorted(superseded)))
    _check("supersession is transitive — F-312 depended on F-311, not on F-310 directly",
           "F-312" in superseded)
    sup = next(f for f in rec["findings"] if f["id"] == "F-311")
    _check("a superseded finding is KEPT, with what withdrew it recorded",
           sup["status"] == "superseded" and sup["superseded_by"] == "F-310",
           "the trail must still show what was believed and why it stopped being believed")
    _check("superseded findings leave the pending queue",
           not any(f["id"] in superseded for f in E.pending(rec)))

    # 4) resumability
    print("\n4) resumable across sessions (constraint 4):")
    mid = E.resume_point(rec)
    _check("the resume point names what is decided and what is next",
           mid["decided"] == 4 and mid["next"] == "F-320",
           f"{mid['decided']} decided, {mid['remaining']} left, next {mid['next']}")
    with tempfile.TemporaryDirectory(prefix="walk-") as td:
        si = Path(td) / "solution_intent"
        E.write(rec, si)
        reloaded = json.loads((si / "enrichment.json").read_text())
    _check("the record round-trips through disk with no loss",
           E.resume_point(reloaded) == mid)
    _check("nothing already decided is re-asked",
           all(f["id"] not in mid["decided_ids"] for f in E.pending(reloaded)))

    # 5) the defer path
    print("\n5) the defer path is required, and lands in §17:")
    E.disposition(rec, "F-320", call="defer", target="§17",
                  rationale="Cannot confirm whether recon's field-48 parse is load-bearing "
                            "without the settlement team; raising it as an open question.",
                  actor="vmunjal")
    f320 = next(f for f in rec["findings"] if f["id"] == "F-320")
    _check("a deferral is a real disposition, not a skip", f320["status"] == "dispositioned")
    _check("it lands in §17 Open questions", f320["section_target"] == "§17",
           "deferral converts the finding into an open question rather than forcing a guess")
    _check("§17 is the declared destination for 'cannot determine'",
           E.NO_CODE_GAP_ROUTING["cannot_determine"] == "§17")

    # 6) propose, never decide
    print("\n6) propose, never decide (constraint 1):")
    auto = E.make_finding("F-500", arm="impact", kind="derived_impact", business_visible=False,
                          evidence=[{"path": "x.c"}])
    E.add(rec, auto)
    _check("an auto-applied finding cannot be dispositioned — nothing is left to decide",
           _raises(lambda: E.disposition(rec, "F-500", call="accept", rationale="x", actor="v")))
    _check("a rationale is structurally mandatory (schema)",
           bool(E.validate({**rec, "findings": [{"id": "F-901", "arm": "claim",
                                                 "kind": "contradiction", "action": "escalated",
                                                 "status": "dispositioned",
                                                 "disposition": "accept", "actor": "v",
                                                 "escalation_reason": "operator_contradiction",
                                                 "severity": "material"}]})),
           "a decision nobody can review is not a decision")
    # finish the batch
    for n in range(1, 6):
        E.disposition(rec, f"F-4{n:02d}", call="accept", target="§16",
                      rationale="Accepted as a batch: routine codec consequences, no business "
                                "visibility.", actor="vmunjal")
    _check("the queue empties only when every escalation has a call",
           not E.pending(rec), f"{len(E.pending(rec))} left")

    # 7) both ledgers
    print("\n7) the trail — both ledgers, rationale in the one that explains:")
    with tempfile.TemporaryDirectory(prefix="walk-led-") as td:
        led = ledger.init_ledger(Path(td) / "ledger", run_id="r-2026-08-01-si1")
        em = telemetry.Emitter(led, run_id="r-2026-08-01-si1", domain="payment_brand", tool="claude")
        for f in rec["findings"]:
            if f["status"] == "dispositioned":
                E.emit_disposition_events(em, led / "decisions.jsonl", rec, f["id"], ts=T)
        report = ledger.validate_ledger(led)
        _check("both ledgers validate", all(not e for e in report.values()), str(report))
        dec = [json.loads(l) for l in (led / "decisions.jsonl").read_text().splitlines() if l.strip()]
        tel = [json.loads(l) for l in (led / "telemetry.jsonl").read_text().splitlines() if l.strip()]
        _check("every dispositioned finding produced an audit record",
               len(dec) == sum(1 for f in rec["findings"] if f["status"] == "dispositioned"),
               f"{len(dec)} records")
        _check("every audit record carries a rationale",
               all(d["rationale"].strip() for d in dec))
        _check("telemetry carries the counts and NOT the prose",
               len([e for e in tel if e["event"] == "disposition"]) == len(dec)
               and not any("rationale" in e for e in tel))
        calls = {d["call"] for d in dec}
        _check("all four call types are exercised in one session",
               calls == {"accept", "reject", "reroute", "defer"}, str(sorted(calls)))
    _check("the whole record still validates after the session", not E.validate(rec),
           str(E.validate(rec)[:2]))

    print()
    if _FAILURES:
        print(f"FAILED — {len(_FAILURES)} check(s): {_FAILURES}", file=sys.stderr)
        return 1
    print("PASS — material findings individually and advisory batched; upstream before "
          "downstream; a reversal supersedes what rested on it without deleting it; the session "
          "resumes losslessly; deferral lands in §17; nothing is decided without a call and a "
          "rationale.")
    return 0


def _raises(fn) -> bool:
    try:
        fn()
    except Exception:
        return True
    return False


if __name__ == "__main__":
    raise SystemExit(main())
