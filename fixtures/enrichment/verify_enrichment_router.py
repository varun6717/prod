#!/usr/bin/env python3
"""verify_enrichment_router.py — TASK-117 proof: D-A16's routing tables, reproduced.

The router is the filter that keeps the operator turn tractable: most findings must never reach a
human, and the ones that do must be exactly the ones needing judgment. Both arms and the
walkthrough consume this one implementation, so a mistake here is a mistake in three places.

  1. **D-A16's "what actually reaches the operator" table**, row by row.
  2. **Provenance decides authority** — the SAME contradiction auto-corrects or escalates purely
     on where the v1 claim came from (D-A6).
  3. **Scope-moving escalates regardless** — checked before anything else.
  4. **The no-code four-way** and its routing table, including the REQUIRED defer path.
  5. **The record is a permanent audit trail** — undispositioned findings live here and not in
     the document; status is per finding, so the walkthrough is resumable.
  6. **Enrichment never deletes** — no route produces a removal.
  7. **Schema validation** accepts the real shapes and rejects malformed ones.
  8. **Ledger wiring** — verdict/escalation/disposition events, and the rationale landing in
     decisions.jsonl rather than telemetry.

Run: python3 fixtures/enrichment/verify_enrichment_router.py
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


def _check(label: str, ok: bool, detail: str = "") -> None:
    print(f"  [{'PASS' if ok else 'FAIL'}] {label}" + (f" — {detail}" if detail else ""))
    if not ok:
        _FAILURES.append(label)


def main() -> int:
    print("verify_enrichment_router — D-A16 routing over a crafted finding set\n")

    # ── 1) D-A16's table, row by row. Each tuple IS a row of the ADR.
    print("1) 'what actually reaches the operator' (D-A16) — every row:")
    rows = [
        ("code contradicts a source-derived claim", dict(
            arm="claim", kind="contradiction", claim_provenance="source", section_ref="§2"),
         E.AUTO_CORRECT, "auto_applied"),
        ("code answers an unsourced [TBD]", dict(
            arm="claim", kind="contradiction", claim_provenance="unsourced", section_ref="§2"),
         E.AUTO_FILL, "auto_applied"),
        ("derived impact, technical consequence", dict(
            arm="impact", kind="derived_impact", business_visible=False),
         E.AUTO_WRITE, "auto_applied"),
        ("code contradicts an OPERATOR answer", dict(
            arm="claim", kind="contradiction", claim_provenance="operator", section_ref="§13"),
         E.ESCALATE, "escalated"),
        ("code contradicts the FRAME", dict(
            arm="claim", kind="contradiction", claim_provenance="frame", section_ref="§4"),
         E.ESCALATE, "escalated"),
        ("derived impact, business-visible", dict(
            arm="impact", kind="derived_impact", business_visible=True),
         E.ESCALATE, "escalated"),
        ("no code found for a requirement", dict(arm="impact", kind="no_code_found"),
         E.ESCALATE, "escalated"),
        ("anything scope-moving", dict(
            arm="impact", kind="derived_impact", business_visible=False, scope_moving=True),
         E.ESCALATE, "escalated"),
    ]
    for label, kw, want_route, want_action in rows:
        r = E.route_finding(**kw)
        _check(f"{label:44} → {want_route}", r.route == want_route and r.action == want_action,
               r.why[:52])

    # ── 2) provenance is the discriminator, not the finding's content
    print("\n2) provenance decides authority (D-A6) — same finding, different outcome:")
    same = dict(arm="claim", kind="contradiction", section_ref="§2")
    routes = {p: E.route_finding(**same, claim_provenance=p).route
              for p in ("source", "operator", "frame", "unsourced")}
    _check("one contradiction, four provenances, three different routes",
           len(set(routes.values())) == 3, str(routes))
    _check("a human's statement is never overruled silently",
           routes["operator"] == routes["frame"] == E.ESCALATE)
    _check("a source-derived claim is corrected in place", routes["source"] == E.AUTO_CORRECT)
    _check("an unsourced gap is FILLED, which is not a correction",
           routes["unsourced"] == E.AUTO_FILL)

    # ── 3) scope-moving wins over everything
    print("\n3) scope-moving escalates regardless of grounding:")
    grounded = E.route_finding(arm="claim", kind="contradiction", claim_provenance="source",
                               section_ref="§2", scope_moving=True)
    _check("a perfectly grounded source contradiction still escalates if it moves scope",
           grounded.escalates and grounded.escalation_reason == E.SCOPE_MOVING, grounded.why[:60])
    _check("…because scope changes are operator-decided, always", "operator-decided" in grounded.why)

    # ── 4) the no-code four-way + the defer path
    print("\n4) the no-code gap is four-way ambiguous (D-A16):")
    r = E.route_finding(arm="impact", kind="no_code_found")
    _check("it always escalates", r.escalates and r.escalation_reason == E.NO_CODE_FOUND)
    _check("all four operator calls have a destination", len(E.NO_CODE_GAP_ROUTING) == 5,
           str(E.NO_CODE_GAP_ROUTING))
    _check("'search miss' DROPS the finding (it was wrong) rather than filing it",
           E.NO_CODE_GAP_ROUTING["search_miss"] == "dropped")
    _check("the DEFER path exists and lands in §17 — without it the walkthrough would "
           "pressure people into fabricating certainty",
           E.NO_CODE_GAP_ROUTING["cannot_determine"] == "§17")
    _check("a versioned duplicate is never resolved silently",
           E.route_finding(arm="impact", kind="versioned_duplicate").escalates)

    # ── 5) the record
    print("\n5) enrichment.json as a permanent, resumable record:")
    rec = E.new_record("r-2026-08-01-si1", "35ffb65ccf77")
    made = [
        E.make_finding("F-001", arm="claim", kind="contradiction", claim_provenance="source",
                       section_ref="§2", verdict="contradicted",
                       evidence=[{"path": "src/routing/brand_router.c", "symbol": "route_transaction"}],
                       reasoning="brand resolution reads the BIN table, not a PAN range"),
        E.make_finding("F-002", arm="claim", kind="contradiction", claim_provenance="operator",
                       section_ref="§13", verdict="contradicted",
                       evidence=[{"path": "src/settlement/reconciler.c"}],
                       reasoning="settlement recon parses field 48; the assumption is wrong"),
        E.make_finding("F-003", arm="impact", kind="derived_impact", business_visible=False,
                       requirement_ref="R2", assertion_ref="R2.1", verdict="impacted",
                       evidence=[{"path": "src/messaging/iso8583.c"}], reasoning="field 48 build"),
        E.make_finding("F-004", arm="impact", kind="no_code_found", requirement_ref="R11",
                       assertion_ref="R11.5", verdict="no_code_found",
                       reasoning="no MDES coverage report emitter found anywhere"),
        E.make_finding("F-005", arm="claim", kind="confirmation", section_ref="§6",
                       verdict="confirmed", evidence=[{"path": "src/routing/dispatch.c"}]),
    ]
    for f in made:
        E.add(rec, f)
    _check("auto-applied findings need no human step", 
           all(f.status == "applied" for f in made if f.action == "auto_applied"))
    _check("escalated findings start undispositioned", 
           all(f.status == "undispositioned" for f in made if f.action == "escalated"))
    _check("`pending()` is what the walkthrough resumes to", len(E.pending(rec)) == 2,
           str([f["id"] for f in E.pending(rec)]))
    E.disposition(rec, "F-002", call="accept", rationale="Recon does parse field 48 — the v1 "
                  "assumption was wrong and the scope grows.", actor="vmunjal", target="§13")
    _check("dispositioning removes it from pending", len(E.pending(rec)) == 1)
    _check("the rationale is recorded on the finding", 
           next(f for f in rec["findings"] if f["id"] == "F-002")["rationale"])
    refused = False
    try:
        E.disposition(rec, "F-001", call="accept", rationale="x", actor="v")
    except ValueError:
        refused = True
    _check("an AUTO-APPLIED finding cannot be dispositioned — there is nothing to decide", refused)
    E.disposition(rec, "F-004", call="reject", rationale="Arm 1 missed it; the emitter is in "
                  "the reporting repo.", actor="vmunjal")
    _check("a 'reject' marks the finding dropped, not deleted",
           next(f for f in rec["findings"] if f["id"] == "F-004")["section_target"] == "dropped")
    c = E.counts(rec)
    _check("counts feed §18 (counts only, never a ledger)",
           c["corrections"] == 1 and c["derived_impacts"] == 1 and c["escalated"] == 2, str(c))

    # ── 6) never deletes
    print("\n6) enrichment never deletes (D-A7):")
    all_routes = {E.route_finding(arm="claim", kind=k, claim_provenance="source").route
                  for k in ("contradiction", "gap_fill", "unverifiable", "confirmation")}
    all_routes |= {E.route_finding(arm="impact", kind=k, business_visible=False).route
                   for k in ("derived_impact", "no_code_found", "versioned_duplicate")}
    _check("no route removes anything — contradicted claims are REWRITTEN",
           not any("delete" in r or "remove" in r for r in all_routes), str(sorted(all_routes)))
    _check("…because a changed sentence is visible at G2 and a missing one is not",
           E.AUTO_CORRECT in all_routes)

    # ── 7) schema
    print("\n7) schema validation:")
    _check("the real record validates", not E.validate(rec), str(E.validate(rec)[:2]))
    negatives = [
        ("escalated with no reason/severity",
         {**rec, "findings": [{"id": "F-900", "arm": "impact", "kind": "no_code_found",
                               "action": "escalated", "status": "undispositioned"}]}),
        ("dispositioned with no rationale",
         {**rec, "findings": [{"id": "F-901", "arm": "claim", "kind": "contradiction",
                               "action": "escalated", "status": "dispositioned",
                               "disposition": "accept", "actor": "v",
                               "escalation_reason": "operator_contradiction",
                               "severity": "material"}]}),
        ("unknown finding kind",
         {**rec, "findings": [{"id": "F-902", "arm": "claim", "kind": "invented",
                               "action": "none", "status": "applied"}]}),
        ("malformed finding id",
         {**rec, "findings": [{"id": "nope", "arm": "claim", "kind": "confirmation",
                               "action": "none", "status": "applied"}]}),
    ]
    for label, bad in negatives:
        _check(f"rejects: {label}", bool(E.validate(bad)))
    _check("an unroutable kind raises rather than defaulting to auto-apply",
           _raises(lambda: E.route_finding(arm="claim", kind="mystery")))

    # ── 8) ledger wiring
    print("\n8) ledger wiring (TASK-104 events):")
    with tempfile.TemporaryDirectory(prefix="enrich-") as td:
        led = ledger.init_ledger(Path(td) / "ledger", run_id="r-2026-08-01-si1")
        em = telemetry.Emitter(led, run_id="r-2026-08-01-si1", domain="payment_brand", tool="claude")
        T = "2026-08-01T00:00:00Z"
        for f in made:
            E.emit_finding_events(em, f, ts=T)
        E.emit_disposition_events(em, led / "decisions.jsonl", rec, "F-002", ts=T)
        E.emit_disposition_events(em, led / "decisions.jsonl", rec, "F-004", ts=T)
        report = ledger.validate_ledger(led)
        _check("both ledgers validate", all(not e for e in report.values()), str(report))
        tel = [json.loads(l) for l in (led / "telemetry.jsonl").read_text().splitlines() if l.strip()]
        dec = [json.loads(l) for l in (led / "decisions.jsonl").read_text().splitlines() if l.strip()]
        _check("one verdict event per verdicted finding",
               sum(1 for e in tel if e["event"] == "verdict") == 5)
        _check("one escalation event per escalated finding",
               sum(1 for e in tel if e["event"] == "escalation") == 2)
        _check("one disposition event per dispositioned finding",
               sum(1 for e in tel if e["event"] == "disposition") == 2)
        _check("the RATIONALE is in decisions.jsonl, not telemetry",
               all(d.get("rationale") for d in dec if d["kind"] == "disposition")
               and not any("rationale" in e for e in tel),
               "telemetry counts; decisions explains")
        _check("a rejected finding's disposition carries no section target",
               not any(d.get("target") for d in dec
                       if d["kind"] == "disposition" and d["call"] == "reject"))

    print()
    if _FAILURES:
        print(f"FAILED — {len(_FAILURES)} check(s): {_FAILURES}", file=sys.stderr)
        return 1
    print("PASS — every row of D-A16's table is reproduced; provenance decides authority; "
          "scope-moving escalates regardless; the no-code four-way keeps its defer path; the "
          "record is resumable and never deletes; both ledgers are stamped with the rationale "
          "in the right one.")
    return 0


def _raises(fn) -> bool:
    try:
        fn()
    except Exception:
        return True
    return False


if __name__ == "__main__":
    raise SystemExit(main())
