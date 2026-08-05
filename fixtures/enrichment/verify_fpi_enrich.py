#!/usr/bin/env python3
"""verify_fpi_enrich.py — TASK-130 proof: the FPI → mnemonic bridge lands in v2.

The pass itself is a **skill** (a model reads v1 + a reference table and stages findings), so what
is provable here is the *mechanism it rides on*: that a `gap_fill` finding citing a corpus document
routes without an operator turn, that the apply pass writes it into the right section, and that its
citation says `ref:` rather than `code:`.

**Why that last one matters enough to test.** `provenance_note` hardcoded `[code: …]`. A mnemonic
resolved from a Confluence table would have been written into an ACCEPTED document claiming code
provenance it never had — a false claim about where a fact came from, in the one artifact whose
whole value is that its claims are traceable.

Run:  python3 fixtures/enrichment/verify_fpi_enrich.py
"""
from __future__ import annotations

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_REPO_ROOT / "core" / "scripts"))

import apply_enrichment as A  # noqa: E402
import enrichment as E  # noqa: E402

_FAILURES: list[str] = []
_TABLE = "context_set/confluence/interchange_levels.md"


def _check(label: str, cond: bool, detail: str = "") -> None:
    print(f"  [{'PASS' if cond else 'FAIL'}] {label}" + (f" — {detail}" if detail else ""))
    if not cond:
        _FAILURES.append(label)


def main() -> int:
    print("verify_fpi_enrich — the FPI → mnemonic bridge\n")

    print("1) a requirement-linked resolution targets §16, so it can become a story:")
    # The design error this kills: emitting a §8 correction. §8 is NEVER corrected (D-A4), so the
    # apply pass drops it silently — and §16 is what `jira_plan` reads stories from, so a mnemonic
    # landing anywhere else is identified and then never planned. That is the whole PeopleSoft
    # path failing quietly, which is exactly the shape of failure this repo keeps finding.
    f = E.make_finding("F-901", arm="claim", kind="derived_impact",
                       requirement_ref="R1", assertion_ref="R1.1",
                       evidence=[{"path": _TABLE, "lines": [45, 52]}],
                       reasoning="FPI 0501 → interchange level VACD (Visa Adj Consumer Debit); "
                                 "rate configuration lives in boarding/PeopleSoft, not repo/")
    _check("routes AUTO_WRITE — a technical consequence, not a decision",
           f.route == E.AUTO_WRITE, f.route)
    _check("targets §16 — the only section jira_plan builds stories from",
           f.section_target == "§16", str(f.section_target))
    _check("status is 'applied', not 'undispositioned'", f.status == "applied", f.status)
    # If it escalated, every run with mnemonics would drag the operator through a second turn.
    _check("it does NOT reach the walkthrough queue",
           f.action == "auto_applied", f.action)
    biz = E.make_finding("F-903", arm="claim", kind="derived_impact", requirement_ref="R1",
                         business_visible=True, evidence=[{"path": _TABLE, "lines": [45, 52]}])
    _check("...but a business-visible resolution DOES escalate",
           biz.action == "escalated", biz.action)

    print("\n2) the citation names a REFERENCE, not code:")
    note = A.provenance_note(f.to_json())
    _check("prefix is `ref:` for a context_set/ path", note.startswith("[ref: "), note)
    _check("...and carries the table's LINE RANGE, not just the file",
           "L45" in note and "52" in note, note)
    # The wrong-but-plausible implementation this kills: one hardcoded prefix for all evidence.
    code_f = E.make_finding("F-902", arm="impact", kind="derived_impact",
                            requirement_ref="R1", assertion_ref="R1.1",
                            evidence=[{"path": "src/routing/brand_router.c", "symbol": "route_txn"}])
    _check("a repo-path finding still says `code:` (the existing contract is intact)",
           A.provenance_note(code_f.to_json()).startswith("[code: "),
           A.provenance_note(code_f.to_json()))

    print("\n3) the apply pass writes it into v2:")
    v1 = ("## 1. Executive summary\n\nSeed.\n\n"
          "## 8. Business requirements\n\n"
          "**R1** — Apply the revised rates for FPI 0501.\n"
          "  - R1.1 The rate table must carry the new value.\n\n"
          "## 16. Derived system impacts\n\nNone identified.\n\n"
          "## 17. Open questions\n\nNone.\n")
    # The real digest — apply_to_v2 refuses a record computed against a different v1, which is
    # what makes "v1 + enrichment.json reconstruct v2" a checked property rather than a claim.
    import hashlib
    rec = E.new_record("r-fpi-proof", hashlib.sha256(v1.encode()).hexdigest()[:12])
    E.add(rec, f)
    v2, report = A.apply_to_v2(v1, rec)
    _check("the mnemonic reaches v2", "VACD" in v2)
    _check("...in §16, grouped under its requirement — where stories are read from",
           "VACD" in A.split_sections(v2).get(16, "") and "R1" in A.split_sections(v2).get(16, ""))
    _check("...carrying its reference citation", _TABLE in v2)
    _check("v1 is untouched — the pass stages, it never edits", "VACD" not in v1)

    print("\n4) both overlays name the skill (§10.2 parity, by hand):")
    skill = _REPO_ROOT / "core/profiles/payment_brand/fpi_mnemonic_enrich.skill.md"
    _check("the skill file exists on disk", skill.is_file())
    for p in (_REPO_ROOT / "overlays/claude/prompts/start-enrich.md",
              _REPO_ROOT / "overlays/copilot/.github/prompts/start-enrich.prompt.md"):
        body = p.read_text(encoding="utf-8")
        _check(f"{p.parent.parent.name}: start-enrich names it", "fpi_mnemonic_enrich" in body)
        # Ordering is the substance: after G2 the mnemonics can never become stories.
        _check(f"{p.parent.parent.name}: ...BEFORE the walkthrough",
               body.index("fpi_mnemonic_enrich") < body.index("disposition walkthrough"))

    print()
    if _FAILURES:
        print(f"FAILED — {len(_FAILURES)} check(s): {_FAILURES}", file=sys.stderr)
        return 1
    print("PASS — an FPI resolution routes without an operator turn, lands in the section that "
          "referenced it, and cites the reference table by line range as `ref:` rather than "
          "claiming code provenance; both overlays run it before the walkthrough.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
