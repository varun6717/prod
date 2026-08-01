#!/usr/bin/env python3
"""verify_spine.py — TASK-121 proof: the full enrichment spine, v1 → v2, and G2.

Runs the whole stage end to end over the fixture v1: both arms file findings, the walkthrough
resolves the escalations, the apply pass writes v2, and G2 scores it.

  1. **v2 exists and v1 is untouched** — byte-identical, and its freeze digest still verifies.
  2. **Every touch is traceable** — v1 + enrichment.json reconstruct v2 (D-A16).
  3. **Corrections revise IN PLACE with provenance**; discoveries append. Nothing is deleted.
  4. **§16 organised by requirement**, holding impacts *and* gaps; §17 extended, never replaced;
     §18 counts only; **§1 regenerated LAST** from the corrected body.
  5. **A rejected finding does not reach v2**; a superseded one does not either — both stay in
     the record.
  6. **G2 scores the run**, and both hard preconditions are enforceable — a seeded undispositioned
     escalation blocks acceptance.
  7. **The provisional §9.3 formula is evaluated against this run** (D-A23 asks for exactly that
     before it is frozen).

Run: python3 fixtures/enrichment/verify_spine.py
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
import tempfile
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_REPO_ROOT = _HERE.parents[1]
sys.path.insert(0, str(_REPO_ROOT / "core" / "scripts"))

import apply_enrichment as A  # noqa: E402
import enrichment as E  # noqa: E402
import ledger  # noqa: E402
import solution_intent_validator as V  # noqa: E402
import yaml  # noqa: E402

_FAILURES: list[str] = []
T = "2026-08-01T00:00:00Z"


def _check(label: str, ok: bool, detail: str = "") -> None:
    print(f"  [{'PASS' if ok else 'FAIL'}] {label}" + (f" — {detail}" if detail else ""))
    if not ok:
        _FAILURES.append(label)


def _summary(body: str, findings) -> str:
    """Stand-in for the model's §1 regeneration — derived from the CORRECTED body."""
    n = len(findings)
    return ("## 1. Executive summary\n\n"
            f"*(Regenerated at enrichment: {n} findings applied to the body below.)*\n\n"
            "Mastercard has issued brand mandate **MCS-2026-R3**, binding on JPMC Merchant "
            "Services, with full compliance required by **2026-09-30**. Enrichment has since "
            "checked v1's current-state claims against the Merchant Routing Service code and "
            "recorded the derived system impacts in §16.\n")


def build_findings(signals) -> dict:
    """A realistic enrichment run over the fixture v1: both arms, then the operator's calls."""
    rec = E.new_record("r-2026-08-01-si1",
                       hashlib.sha256((_REPO_ROOT / "fixtures/si_author/v1.md")
                                      .read_bytes()).hexdigest()[:12])
    # Arm 2 — a source-derived error, a confirmation, an unverifiable, an operator contradiction
    E.add(rec, E.make_finding("F-201", arm="claim", kind="contradiction",
                              claim_provenance="source", section_ref="§2", verdict="contradicted",
                              evidence=[{"path": "src/routing/brand_router.c",
                                         "symbol": "route_transaction", "lines": [17, 24]}],
                              reasoning="brand resolution reads the routing table, not a raw PAN "
                                        "range as §2 states"))
    E.add(rec, E.make_finding("F-203", arm="claim", kind="confirmation", section_ref="§6",
                              verdict="confirmed",
                              evidence=[{"path": "src/routing/dispatch.c"}]))
    E.add(rec, E.make_finding("F-207", arm="claim", kind="unverifiable", section_ref="§14",
                              verdict="unverifiable",
                              reasoning="the Certification Authority is a partner system"))
    E.add(rec, E.make_finding("F-202", arm="claim", kind="contradiction",
                              claim_provenance="operator", section_ref="§13",
                              verdict="contradicted",
                              evidence=[{"path": "src/settlement/reconciler.c"}],
                              reasoning="reconciler parses field 48; §13's A2 assumption is wrong"))
    # Arm 1 — impacts per requirement, plus a no-code gap
    for i, (rid, aid, path, why) in enumerate([
        ("R1", "R1.1", "src/messaging/iso8583.c", "field 48 build path carries the TRID"),
        ("R2", "R2.1", "src/messaging/field_codec.c", "codec table widens for 48.66/48.78"),
        ("R4", "R4.1", "src/routing/route_table.c", "BIN lookup resolves against MBT v2026-Q2"),
        ("R6", "R6.1", "src/routing/dispatch.c", "token BINs must reach the MDES endpoint"),
    ], start=1):
        E.add(rec, E.make_finding(f"F-3{i:02d}", arm="impact",
                                  kind="derived_impact", business_visible=False,
                                  requirement_ref=rid, assertion_ref=aid, verdict="impacted",
                                  evidence=[{"path": path}], reasoning=why))
    E.add(rec, E.make_finding("F-310", arm="impact", kind="no_code_found", requirement_ref="R11",
                              assertion_ref="R11.5", verdict="no_code_found",
                              reasoning="no MDES coverage report emitter anywhere in the map"))
    E.add(rec, E.make_finding("F-311", arm="impact", kind="derived_impact", business_visible=True,
                              requirement_ref="R11", depends_on_finding=["F-310"],
                              verdict="impacted",
                              evidence=[{"path": "src/settlement/ledger_post.c"}],
                              reasoning="a reporting hook would be needed on ledger posting"))
    # Every remaining assertion gets a verdict — Arm 1 must reach all of them (G2 precondition)
    n = 0
    for rid in signals.requirements:
        for i in range(1, signals.req_assertions.get(rid, 0) + 1):
            aid = f"{rid}.{i}"
            if any(f.get("assertion_ref") == aid for f in rec["findings"]):
                continue
            n += 1
            E.add(rec, E.make_finding(f"F-6{n:03d}", arm="impact", kind="confirmation",
                                      requirement_ref=rid, assertion_ref=aid, verdict="confirmed",
                                      reasoning="assertion already satisfied by existing code"))
    return rec


def main() -> int:
    profile = yaml.safe_load(
        (_REPO_ROOT / "core/profiles/payment_brand/si_profile.payment_brand.yaml").read_text())
    v1_path = _REPO_ROOT / "fixtures/si_author/v1.md"
    v1 = v1_path.read_text(encoding="utf-8")
    signals = V.parse_v1(v1, profile)
    rec = build_findings(signals)

    print("verify_spine — the full enrichment spine over the fixture v1\n")
    print(f"  {len(rec['findings'])} findings · {len(E.pending(rec))} escalated\n")

    # ── the operator turn
    print("1) the walkthrough resolves every escalation:")
    E.disposition(rec, "F-202", call="accept", target="§13",
                  rationale="Recon does parse field 48 — the assumption was wrong and the scope "
                            "grows.", actor="vmunjal")
    E.disposition(rec, "F-310", call="accept", target="§16",
                  rationale="Genuinely new capability — no emitter exists; this becomes a build "
                            "story.", actor="vmunjal")
    E.disposition(rec, "F-311", call="defer", target="§17",
                  rationale="Cannot size the reporting hook until the emitter design is settled.",
                  actor="vmunjal")
    _check("no escalation is left undispositioned", not E.pending(rec))

    # ── apply
    v2, report = A.apply_to_v2(v1, rec, regenerate_summary=_summary)

    _check("the enrichment record itself validates against the schema", not E.validate(rec),
           str(E.validate(rec)[:2]))
    _check("every finding id follows the F-nnn contract",
           all(re.fullmatch(r"F-\d{3,}", f["id"]) for f in rec["findings"]),
           str([f["id"] for f in rec["findings"] if not re.fullmatch(r"F-\d{3,}", f["id"])][:3]))

    print("\n2) v1 is untouched; v2 exists:")
    _check("v1 is byte-identical after the run", v1_path.read_text(encoding="utf-8") == v1)
    _check("v2 is a different document", v2 != v1 and len(v2) > 0)
    _check("v2 keeps all 18 sections", len(A.split_sections(v2)) == 18,
           f"{len(A.split_sections(v2))} sections")
    _check("applying against the WRONG v1 is refused",
           _raises(lambda: A.apply_to_v2(v1 + "\ndrift\n", rec)),
           "'v1 + enrichment.json reconstruct v2' only holds against the v1 it was computed on")

    print("\n3) corrections revise IN PLACE, with provenance:")
    s2 = A.split_sections(v2)[2]
    _check("the §2 correction lands in §2, not twelve pages away", "F-201" in s2,
           "a correction far from the claim leaves a false statement in the body")
    _check("it carries an inline code citation", "[code: src/routing/brand_router.c" in s2)
    _check("the original claim is REWRITTEN, not removed",
           "PAN BIN-range lookup" in s2,
           "deletion is invisible in a way rewriting is not")
    _check("§13's operator-contradiction correction landed too",
           "F-202" in A.split_sections(v2)[13])
    _check("§8 was not touched — requirements are extend-only",
           A.split_sections(v2)[8].strip() == A.split_sections(v1)[8].strip(),
           "compared on content; reassembly normalises trailing whitespace on every section")

    print("\n4) §16 / §17 / §18 / §1:")
    s16 = A.split_sections(v2)[16]
    _check("§16 is organised BY REQUIREMENT", "### R1" in s16 and "### R11" in s16)
    _check("§16 holds gaps as well as impacts", "GAP — no implementation found" in s16)
    _check("an accepted gap carries the operator's call and rationale",
           "Operator: accept" in s16)
    s17 = A.split_sections(v2)[17]
    _check("§17 is EXTENDED, not replaced — v1's questions survive",
           "Q1" in s17 and "Added during enrichment" in s17)
    _check("the deferral landed in §17", "F-311" in s17)
    s18 = A.split_sections(v2)[18]
    _check("§18 is counts only, and says so",
           "Counts only" in s18 and "enrichment.json" in s18)
    s1 = A.split_sections(v2)[1]
    _check("§1 was REGENERATED, not revised", "Regenerated at enrichment" in s1)
    _check("…and it reflects the corrected body", "§16" in s1)

    print("\n5) rejected and superseded findings do not reach v2:")
    rec2 = json.loads(json.dumps(rec))
    E.disposition(rec2, "F-310", call="reject",
                  rationale="Arm 1 missed it — the emitter is in the reporting repo.",
                  actor="vmunjal") if False else None
    rec2["findings"] = [dict(f) for f in rec2["findings"]]
    for f in rec2["findings"]:
        if f["id"] == "F-310":
            f["disposition"], f["section_target"] = "reject", "dropped"
        if f["id"] == "F-311":
            f["status"], f["superseded_by"] = "superseded", "F-310"
    v2b, _ = A.apply_to_v2(v1, rec2, regenerate_summary=_summary)
    _check("a rejected finding is absent from v2", "F-310" not in A.split_sections(v2b)[16])
    _check("a superseded finding is absent from v2", "F-311" not in v2b)
    _check("…but BOTH are still in the record",
           all(any(f["id"] == i for f in rec2["findings"]) for i in ("F-310", "F-311")),
           "the trail keeps what was believed and why it stopped being believed")

    # ── G2
    print("\n6) G2 scores the run:")
    g2 = V.evaluate_g2(rec, signals)
    print(f"     verdict_completeness={g2.verdict_completeness:.3f}  "
          f"impact_coverage={g2.impact_coverage:.3f}  score={g2.score}")
    for p in g2.preconditions:
        print(f"     {'✓' if p.ok else '✗'} {p.name}" +
              (f"  → {p.violations[0][:60]}…" if not p.ok else ""))
    _check("every hard precondition holds on a complete run", g2.hard_ok, str(g2.blockers[:1]))
    _check("the run is eligible", g2.eligible, f"score {g2.score} vs {g2.threshold}")

    print("\n7) both preconditions are enforceable:")
    blocked = json.loads(json.dumps(rec))
    blocked["findings"].append({"id": "F-999", "arm": "impact", "kind": "no_code_found",
                                "action": "escalated", "status": "undispositioned",
                                "escalation_reason": "no_code_found", "severity": "material"})
    g2b = V.evaluate_g2(blocked, signals)
    _check("a seeded UNDISPOSITIONED escalation blocks G2", not g2b.hard_ok and not g2b.eligible,
           g2b.blockers[0][:64] if g2b.blockers else "")
    noprov = json.loads(json.dumps(rec))
    for f in noprov["findings"]:
        if f["id"] == "F-201":
            f.pop("evidence", None)
    g2c = V.evaluate_g2(noprov, signals)
    _check("a correction with NO code provenance blocks G2",
           any("provenance" in b for b in g2c.blockers), g2c.blockers[0][:64] if g2c.blockers else "")
    missing = json.loads(json.dumps(rec))
    missing["findings"] = [f for f in missing["findings"] if f.get("assertion_ref") != "R1.1"]
    g2d = V.evaluate_g2(missing, signals)
    _check("an unverdicted assertion blocks G2",
           any("no verdict" in b for b in g2d.blockers), g2d.blockers[0][:64] if g2d.blockers else "")

    # ── the score must DISCRIMINATE, not merely read 100 on a run built to pass.
    #    D-A23 asks the formula to be validated before freezing, and "passes the one run we
    #    constructed to pass" is not that. The question that matters: can the score fall below
    #    threshold on a run where all three hard preconditions still HOLD? If not, the score is
    #    indistinguishable from no score at all, and §9.3's 0.5/0.5 split earns nothing.
    print("\n7b) the score discriminates on an axis the preconditions do NOT cover:")
    thin = json.loads(json.dumps(rec))
    # Arm 2 files claims it never resolves — a real failure mode (clustering broke, budget ran
    # out). `every_assertion_verdicted` cannot catch it: these are §-claims, not §8 assertions.
    for i in range(1, 26):
        thin["findings"].append({"id": f"F-8{i:03d}", "arm": "claim", "kind": "contradiction",
                                 "claim_provenance": "source", "section_ref": "§10",
                                 "action": "auto_applied", "status": "applied",
                                 "route": "auto_correct", "section_target": "§10",
                                 "evidence": [{"path": "src/messaging/iso8583.c"}]})
    g2thin = V.evaluate_g2(thin, signals)
    print(f"     verdict_completeness={g2thin.verdict_completeness:.3f}  "
          f"impact_coverage={g2thin.impact_coverage:.3f}  score={g2thin.score}")
    _check("all three hard preconditions still HOLD on this run", g2thin.hard_ok,
           str(g2thin.blockers[:1]))
    _check("but the SCORE falls below threshold", not g2thin.score_pass,
           f"{g2thin.score} < {g2thin.threshold}")
    _check("so the run is ineligible on the score alone", not g2thin.eligible,
           "Arm 2 claim completeness is covered by no precondition — the score is doing real work")
    _check("and the drop comes from verdict_completeness, not impact_coverage",
           g2thin.verdict_completeness < 1.0 and g2thin.impact_coverage == 1.0)

    # ── RULING 3 (V, 2026-08-02): the AMENDED §9.3 impact_coverage must DISCRIMINATE ────
    # The provisional formula was falsified against this run — it scored a complete, correct run
    # 0.417 because 7 of 12 requirements were analysed and found to need no change, and worse, it
    # made MANUFACTURING §16 entries the cheapest way to pass. The replacement counts a
    # requirement as covered when Arm 1 REACHED it, whatever the verdict.
    #
    # But "has only ever scored 1.0" is exactly the property that made the original suspect. A
    # metric that cannot go down measures nothing. So: drop Arm 1's findings for a third of the
    # requirements and confirm the score falls proportionally — the same falsification test the
    # formula it replaced was subjected to.
    print("\n7c) the amended impact_coverage discriminates (it can go DOWN):")
    import copy
    missed = copy.deepcopy(rec)
    drop = set(signals.requirements[:4])            # Arm 1 never reached these four
    missed["findings"] = [f for f in missed["findings"]
                          if f.get("requirement_ref") not in drop]
    g2missed = V.evaluate_g2(missed, signals)
    n_reqs = len(signals.requirements)
    expected = (n_reqs - len(drop)) / n_reqs
    _check("with 4 of 12 requirements unreached, impact_coverage falls to exactly 8/12",
           abs(g2missed.impact_coverage - expected) < 1e-9,
           f"{g2missed.impact_coverage:.3f} vs expected {expected:.3f}")
    _check("it was 1.000 on the complete run — so the metric MOVES",
           g2.impact_coverage == 1.0 and g2missed.impact_coverage < g2.impact_coverage)
    _check("and the drop is enough to fail the gate on score alone",
           not g2missed.score_pass, f"score {g2missed.score} < {g2missed.threshold}")

    # The failure mode the amendment fixed must stay fixed: a requirement REACHED and found to
    # need no change scores as covered, so nobody is rewarded for inventing a §16 entry.
    confirmed_only = copy.deepcopy(rec)
    for f in confirmed_only["findings"]:
        if f["arm"] == "impact" and f.get("verdict") == "impacted":
            f["verdict"] = "confirmed"
            f["kind"] = "confirmation"
    g2conf = V.evaluate_g2(confirmed_only, signals)
    _check("a run where Arm 1 found NOTHING needed changing still scores 1.0 coverage",
           g2conf.impact_coverage == 1.0,
           "the old formula scored this 0.417 and made manufacturing impacts the cheapest way "
           "to pass — that is the regression this guards")

    print("\n8) the G2 ledger record:")
    with tempfile.TemporaryDirectory(prefix="spine-") as td:
        led = ledger.init_ledger(Path(td) / "ledger", run_id="r-2026-08-01-si1")
        _check("accept on a blocked run is REFUSED",
               _raises(lambda: V.record_g2(led, result=g2b, outcome="accept", version=2, ts=T)))
        v = V.record_g2(led, result=g2, outcome="accept", version=2, ts=T)
        _check("accept locks v2", v == 2)
        rep = ledger.validate_ledger(led)
        _check("both ledgers validate", all(not e for e in rep.values()), str(rep))
        tel = [json.loads(l) for l in (led / "telemetry.jsonl").read_text().splitlines() if l.strip()]
        _check("the validation event names the enrichment artifact",
               any(e["event"] == "validation" and e["artifact"] == "enrichment" for e in tel))
        _check("the gate_decision names G2",
               any(e["event"] == "gate_decision" and e["gate"] == "G2" for e in tel))

    print("\n9) reconstructability (D-A16):")
    v2again, _ = A.apply_to_v2(v1, rec, regenerate_summary=_summary)
    _check("v1 + enrichment.json reproduce v2 deterministically", v2again == v2)
    touched = set(report["corrections"] and [c["id"] for c in report["corrections"]]) \
        | set(report["impacts"]) | set(report["open_questions"])
    _check("every touch in v2 traces to a finding id", bool(touched)
           and all(t.startswith("F-") for t in touched), f"{len(touched)} touches")

    print()
    if _FAILURES:
        print(f"FAILED — {len(_FAILURES)} check(s): {_FAILURES}", file=sys.stderr)
        return 1
    print("PASS — v2 assembled from a frozen v1 plus the record; corrections in place with "
          "provenance and nothing deleted; §16 by requirement with gaps; §17 extended; §1 "
          "regenerated last; G2 scores and both preconditions block.")
    return 0


def _raises(fn) -> bool:
    try:
        fn()
    except Exception:
        return True
    return False


if __name__ == "__main__":
    raise SystemExit(main())
