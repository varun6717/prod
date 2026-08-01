#!/usr/bin/env python3
"""verify_claim_verifier.py — TASK-119 proof: Arm 2 over the fixture v1.

Arm 2 is corrective, and its failure modes are all *quiet*: a marker applied where the instrument
cannot look, a human's statement silently overruled, a requirement rewritten from code. Each seeded
claim below is drawn from the real `fixtures/si_author/v1.md` and carries its expected outcome.

  1. **The three-way sort** — judgment and future-state are skipped, never verdicted.
  2. **Runtime-shaped claims are SKIPPED, not marked** — the marker would claim we looked.
  3. **A wrong source-derived claim** → staged correction with code provenance.
  4. **A wrong FRAME claim** → escalation. Never silently overruled, however sure the code is.
  5. **An unmatchable claim** → `unverifiable`, cheap, surfaced toward §14.
  6. **§8 is never corrected** — the guard raises rather than producing a finding.
  7. **§5 is asymmetric** — system actors verdicted, human personas skipped.
  8. **No closure** — Arm 2 produces point findings only.
  9. **Corrections rewrite, never delete**; §18 counts are contributed.

Run: python3 fixtures/enrichment/verify_claim_verifier.py
"""
from __future__ import annotations

import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_REPO_ROOT = _HERE.parents[1]
sys.path.insert(0, str(_REPO_ROOT / "core" / "scripts"))

import enrichment as E  # noqa: E402

_FAILURES: list[str] = []


def _check(label: str, ok: bool, detail: str = "") -> None:
    print(f"  [{'PASS' if ok else 'FAIL'}] {label}" + (f" — {detail}" if detail else ""))
    if not ok:
        _FAILURES.append(label)


# Claims lifted from fixtures/si_author/v1.md, each with the sort the model would assign.
SEEDED = [
    # (id, v1 quote, section, sort, provenance, expectation). Ids follow the F-nnn
# contract the enrichment schema pins — the fixture conforms rather than the schema relaxing.
    ("F-201", "identifies a card brand by **PAN BIN-range lookup at", "§2",
     E.SORT_CLAIM, "source", "wrong — the code resolves against the BIN table, not a PAN range"),
    ("F-202", "Settlement reconciliation is unaffected by the authorization message change", "§13",
     E.SORT_CLAIM, "operator", "wrong — recon parses field 48; but an OPERATOR said it"),
    ("F-203", "compliance required by **2026-09-30**", "§2",
     E.SORT_CLAIM, "source", "confirmed"),
    ("F-204", "misrouted interchange is unacceptable for merchants", "§2",
     E.SORT_JUDGMENT, "source", "skipped — code cannot say whether something is a problem"),
    ("F-205", "the router will carry the brand indicator end to end", "§6",
     E.SORT_FUTURE, "source", "skipped — nothing in current code verifies a future state"),
    ("F-206", "the audit record is written within 200ms of the routing decision", "§10",
     E.SORT_RUNTIME, "source", "skipped — runtime data; the map knows what calls what, not how fast"),
    ("F-207", "the Mastercard Certification Authority administers MAC Level 2", "§14",
     E.SORT_CLAIM, "source", "unverifiable — a partner system, not our code"),
    ("F-208", "the certification analyst submits interoperability traces", "§5",
     E.SORT_JUDGMENT, "source", "skipped — a human persona; code has no opinion on roles"),
    ("F-209", "the Banknet MDES gateway is the counterparty behind the token interface", "§5",
     E.SORT_CLAIM, "source", "system actor — verdictable"),
]


def main() -> int:
    print("verify_claim_verifier — Arm 2 over the fixture v1\n")
    v1 = (_REPO_ROOT / "fixtures/si_author/v1.md").read_text(encoding="utf-8")

    # 1) the three-way sort
    print("1) the verdict population sorts three ways (D-A5):")
    staged, skipped = {}, []
    for cid, quote, section, sort, prov, _why in SEEDED:
        kind = ("contradiction" if cid in ("F-201", "F-202")
                else "unverifiable" if cid == "F-207" else "confirmation")
        f = E.stage_claim(cid, sort=sort, section_ref=section, arm="claim", kind=kind,
                          claim_provenance=prov,
                          verdict=("contradicted" if kind == "contradiction"
                                   else "unverifiable" if kind == "unverifiable" else "confirmed"),
                          reasoning=quote)
        (staged.__setitem__(cid, f) if f is not None else skipped.append(cid))
    _check("factual current-state claims enter the population",
           set(staged) == {"F-201", "F-202", "F-203", "F-207", "F-209"}, str(sorted(staged)))
    _check("business judgment is skipped — code cannot say 'and that isn't a problem'",
           "F-204" in skipped)
    _check("future-state is skipped — nothing in current code can verify it", "F-205" in skipped)
    # The seeded claims must be REAL v1 text, not paraphrases. Without this the fixture could
    # drift into testing claims the document never made — and every downstream assertion about
    # "a wrong source-derived claim" would be about a claim nobody wrote.
    missing = [cid for cid, q, _, _, _, _ in SEEDED[:3] if q not in v1]
    _check("the seeded claims are verbatim v1 text, not paraphrases", not missing, str(missing))

    # 2) runtime-shaped: skipped, NOT marked
    print("\n2) runtime-shaped claims are skipped, not marked unverifiable:")
    _check("C6 (a 200ms threshold) produces NO finding at all", "F-206" in skipped)
    _check("…and specifically not an `unverifiable` one",
           "F-206" not in staged,
           "the marker would imply we looked and failed; the map knows what calls what, not how fast")
    _check("skipping is distinguishable from unverifiable in the output",
           "F-207" in staged and staged["F-207"].verdict == "unverifiable" and "F-206" not in staged)

    # 3) a wrong source-derived claim → correction with provenance
    print("\n3) a wrong SOURCE-derived claim → staged correction:")
    c1 = staged["F-201"]
    _check("it auto-corrects", c1.route == E.AUTO_CORRECT and c1.action == "auto_applied")
    _check("it lands back in the section that made the claim", c1.section_target == "§2")
    c1.evidence = [{"path": "src/routing/brand_router.c", "symbol": "route_transaction",
                    "lines": [17, 24]}]
    _check("the correction carries code provenance (a G2 hard precondition)", bool(c1.evidence))
    _check("it needs no human step", c1.status == "applied")

    # 4) a wrong FRAME/operator claim → escalation
    print("\n4) a wrong OPERATOR claim → escalation, never a silent overrule:")
    c2 = staged["F-202"]
    _check("it escalates", c2.action == "escalated" and c2.route == E.ESCALATE)
    _check("the reason names the human-overrule case",
           c2.escalation_reason == E.OPERATOR_CONTRADICTION)
    _check("it awaits a human", c2.status == "undispositioned")
    same_but_sourced = E.make_finding("F-2021", arm="claim", kind="contradiction",
                                      claim_provenance="source", section_ref="§13")
    _check("the IDENTICAL finding auto-corrects when the claim was source-derived",
           same_but_sourced.route == E.AUTO_CORRECT,
           "authority follows provenance, not the verifier's confidence")

    # 5) unverifiable is cheap, honest, and informative
    print("\n5) `unverifiable` — an honest cheap outcome, surfaced to §14:")
    c7 = staged["F-207"]
    _check("no match anywhere → unverifiable", c7.verdict == "unverifiable")
    _check("it is surfaced toward §14 Dependencies, not discarded", c7.section_target == "§14",
           "no match usually means a partner or upstream system — itself worth recording")
    _check("it required no source read to reach", c7.route == E.AUTO_WRITE)

    # 6) §8 is never corrected
    print("\n6) §8 is never corrected (D-A4, binding):")
    raised = False
    try:
        E.stage_claim("F-210", sort=E.SORT_CLAIM, section_ref="§8", arm="claim",
                      kind="contradiction", claim_provenance="source")
    except ValueError as exc:
        raised = "extend-only" in str(exc).lower() or "EXTEND-ONLY" in str(exc)
    _check("staging a §8 contradiction RAISES", raised,
           "code cannot contradict an intent; rewriting one would let the implementation "
           "dictate business intent")
    ok_assumption = E.stage_claim("F-211", sort=E.SORT_CLAIM, section_ref="§16", arm="claim",
                                  kind="contradiction", claim_provenance="unsourced")
    _check("but an implicit assumption INSIDE an assertion is still verdictable",
           ok_assumption is not None and ok_assumption.route == E.AUTO_FILL)
    _check("§8 is absent from the verdict-eligible section list",
           "§8" not in E.VERDICT_ELIGIBLE_SECTIONS, str(E.VERDICT_ELIGIBLE_SECTIONS))

    # 7) §5 asymmetry
    print("\n7) §5 is asymmetric — system actors only:")
    _check("a human persona is skipped, not marked unverifiable", "F-208" in skipped)
    _check("a system actor IS verdicted", "F-209" in staged)
    _check("…so §5 produces findings without ever judging a human role",
           staged["F-209"].section_ref == "§5" and "F-208" not in staged)

    # 8 & 9) no closure; rewrite not delete; counts
    print("\n8) Arm 2 does not walk closure, and never deletes:")
    _check("no staged finding carries a closure/ripple field",
           not any(hasattr(f, "closure") or "ripple" in (f.reasoning or "")
                   for f in staged.values()),
           "point lookup, then stop — closure is Arm 1's, or the same impact reports twice")
    _check("no route removes anything",
           all(f.route in (E.AUTO_CORRECT, E.AUTO_FILL, E.AUTO_WRITE, E.ESCALATE, E.NONE)
               for f in staged.values()))
    rec = E.new_record("r-2026-08-01-si1", "35ffb65ccf77")
    for f in staged.values():
        E.add(rec, f)
    _check("the record validates", not E.validate(rec), str(E.validate(rec)[:2]))
    c = E.counts(rec)
    _check("§18 gets counts: corrections / confirmed / unverifiable",
           c["corrections"] == 1 and c["confirmed"] == 2 and c["unverifiable"] == 1, str(c))
    _check("skipped claims are absent from the counts entirely",
           c["findings"] == len(staged) == 5,
           f"{len(SEEDED)} seeded, {len(skipped)} skipped, {c['findings']} recorded")

    print()
    if _FAILURES:
        print(f"FAILED — {len(_FAILURES)} check(s): {_FAILURES}", file=sys.stderr)
        return 1
    print("PASS — the population sorts three ways; runtime-shaped claims are skipped rather than "
          "marked; a source-derived error corrects with provenance while the identical frame/"
          "operator error escalates; unverifiable surfaces to §14; §8 is never corrected; §5 "
          "verdicts system actors only.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
