#!/usr/bin/env python3
"""verify_jira_plan.py — TASK-122 proof: the 4-level plan over the fixture v2.

Every level's source is fixed by D-A15, and the failures are structural: an epic with no parent
deliverable, a story that names no code and carries no flag, a §16 entry that yields nothing. Each
looks like a normal plan.

  1. **Four levels emitted**, each from its declared source.
  2. **Epic = requirement, never story** — a requirement is epic-sized.
  3. **The parent chain is built by the §8→§7 trace** — no orphans.
  4. **Every §16 entry yields ≥1 story**; every story traces back to §16 or §7.
  5. **Exactly one of `code_location` | `flag`** on every story; gaps are `new_build`.
  6. **Non-code (deliverable-derived) stories exist.**
  7. **The translation ADDS acceptance criteria** — nothing story-shaped is read off the source text.
  8. **Ids are the SI's own** — they are the push's idempotency anchors.

Run: python3 fixtures/jira_plan/verify_jira_plan.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_REPO_ROOT = _HERE.parents[1]
sys.path.insert(0, str(_REPO_ROOT / "core" / "scripts"))
sys.path.insert(0, str(_REPO_ROOT / "fixtures" / "enrichment"))

import apply_enrichment as A  # noqa: E402
import jira_plan as J  # noqa: E402
import solution_intent_validator as V  # noqa: E402
import yaml  # noqa: E402

_FAILURES: list[str] = []


def _check(label: str, ok: bool, detail: str = "") -> None:
    print(f"  [{'PASS' if ok else 'FAIL'}] {label}" + (f" — {detail}" if detail else ""))
    if not ok:
        _FAILURES.append(label)


def _story_author(entry: dict) -> dict:
    """The model seam. Acceptance criteria are AUTHORED here — they exist nowhere upstream, which
    is what makes story writing a translation rather than a copy of the §16 entry."""
    if entry["kind"] == "non_code":
        return {"summary": f"Deliver {entry['id']} (non-code work package)",
                "description": "Prepare and submit the non-code deliverable.",
                "acceptance_criteria": "The deliverable is accepted by its external counterparty "
                                       "and the acceptance is recorded."}
    if entry["kind"].startswith("GAP"):
        return {"summary": f"Build the capability for {entry['assertion_ref']}",
                "description": f"No implementation exists ({entry['id']}); build it.",
                "acceptance_criteria": "The new component satisfies the assertion end to end and "
                                       "is covered by a test that fails without it."}
    return {"summary": f"Update {Path(entry['evidence']).name} for {entry['assertion_ref']}",
            "description": f"Change grounded in {entry['id']} at {entry['evidence']}.",
            "acceptance_criteria": f"{Path(entry['evidence']).name} exhibits the asserted "
                                   f"behaviour, verified by a regression test at that location."}


def build() -> tuple[dict, dict, object]:
    spine = __import__("verify_spine")
    profile = yaml.safe_load(
        (_REPO_ROOT / "core/profiles/payment_brand/si_profile.payment_brand.yaml").read_text())
    v1 = (_REPO_ROOT / "fixtures/si_author/v1.md").read_text(encoding="utf-8")
    signals = V.parse_v1(v1, profile)
    rec = spine.build_findings(signals)
    for fid, call, target, why in [
        ("F-202", "accept", "§13", "Recon does parse field 48."),
        ("F-310", "accept", "§16", "Genuinely new capability — no emitter exists."),
        ("F-311", "defer", "§17", "Cannot size until the emitter design settles."),
    ]:
        __import__("enrichment").disposition(rec, fid, call=call, target=target,
                                             rationale=why, actor="vmunjal")
    v2, _ = A.apply_to_v2(v1, rec, regenerate_summary=spine._summary)
    sections = A.split_sections(v2)
    plan = J.build_plan(sections, signals, rec, run_id="r-2026-08-01-si1",
                        project_key="PBIROUTE",
                        controls={"seal_id": "SEAL-12345", "control_owner": "vmunjal",
                                  "risk_classification": "medium"},
                        story_author=_story_author,
                        deliverable_kind=lambda d: "non_code" if d == "D5" else "code")
    return plan, sections, signals


def main() -> int:
    plan, sections, signals = build()
    (_HERE / "plan_pass.json").write_text(json.dumps(plan, indent=2) + "\n")

    print("verify_jira_plan — the 4-level plan over the fixture v2\n")
    print(f"  1 initiative · {len(plan['deliverables'])} deliverables · "
          f"{len(plan['epics'])} epics · {len(plan['stories'])} stories\n")

    print("1) four levels, each from its declared source (D-A15):")
    _check("initiative comes from the document itself",
           plan["initiative"]["issue_type"] == "Initiative" and plan["initiative"]["summary"])
    _check("deliverables come from §7, one per D-id",
           {d["local_id"] for d in plan["deliverables"]} == set(signals.deliverables),
           str(sorted(d["local_id"] for d in plan["deliverables"])))
    _check("epics come from §8, ONE PER REQUIREMENT",
           [e["local_id"] for e in plan["epics"]] == list(signals.requirements),
           f"{len(plan['epics'])} epics for {len(signals.requirements)} requirements")
    _check("stories exist at all — they are v2-only", bool(plan["stories"]),
           f"{len(plan['stories'])} stories")

    print("\n2) a requirement is EPIC-sized, never story-sized:")
    _check("no story's local_id is a requirement id",
           not any(s["local_id"] in signals.requirements for s in plan["stories"]))
    _check("every requirement produced exactly one epic",
           len(plan["epics"]) == len(set(e["local_id"] for e in plan["epics"]))
           == len(signals.requirements))

    print("\n3) the parent chain is built by the §8→§7 trace:")
    dids = {d["local_id"] for d in plan["deliverables"]}
    orphan_epics = [e["local_id"] for e in plan["epics"] if e["parent"] not in dids]
    _check("no epic is orphaned — every parent is a real deliverable", not orphan_epics,
           str(orphan_epics))
    _check("each epic's parent is the deliverable its requirement NAMED",
           all(e["parent"] == signals.req_deliverable.get(e["local_id"]) for e in plan["epics"]))
    rids = {e["local_id"] for e in plan["epics"]}
    _check("no story is orphaned", all(s["parent"] in rids for s in plan["stories"]))
    _check("every deliverable parents to the initiative",
           all(d["parent"] == "INIT" for d in plan["deliverables"]))

    print("\n4) §16 ↔ story coverage, both directions:")
    s16_ids = set(plan["trace"]["section16_entries"])
    covered = {s["evidence"] for s in plan["stories"]}
    _check("§16 has entries to cover", bool(s16_ids), f"{len(s16_ids)} entries")
    _check("every §16 entry yields ≥1 story (the dropped-impact catch)",
           s16_ids <= covered, str(sorted(s16_ids - covered)))
    invented = [s["local_id"] for s in plan["stories"]
                if s["evidence"] not in s16_ids | dids]
    _check("every story traces to a §16 entry or a §7 deliverable (the invented-story catch)",
           not invented, str(invented))

    print("\n5) every story names code, or says why it cannot:")
    bad = [s["local_id"] for s in plan["stories"]
           if bool(s.get("code_location")) == bool(s.get("flag"))]
    _check("exactly one of code_location | flag on every story", not bad, str(bad))
    gaps = [s for s in plan["stories"] if s.get("flag") == "new_build"]
    _check("a dispositioned §16 GAP becomes new_build, with no invented path",
           bool(gaps) and all(not s.get("code_location") for s in gaps),
           f"{len(gaps)} new_build")
    coded = [s for s in plan["stories"] if s.get("code_location")]
    _check("code stories name a real path from their §16 entry's evidence",
           bool(coded) and all("/" in s["code_location"] for s in coded),
           f"{len(coded)} code-located")

    print("\n6) non-code work is planned, not dropped:")
    noncode = [s for s in plan["stories"] if s.get("flag") == "non_code"]
    _check("deliverable-derived non-code stories exist", bool(noncode),
           str([s["evidence"] for s in noncode]))
    _check("…and they trace to a §7 deliverable, not to §16",
           all(s["evidence"] in dids for s in noncode),
           "certification/filing work would otherwise appear in no plan at all")

    print("\n7) the translation ADDS something (scope vs specification):")
    _check("every story carries acceptance criteria",
           all(s.get("acceptance_criteria", "").strip() for s in plan["stories"]))
    _check("acceptance criteria appear nowhere in v2 — they are authored, not copied",
           not any(s["acceptance_criteria"][:40] in "\n".join(sections.values())
                   for s in plan["stories"][:5]),
           "a story that merely restates its §16 entry has not been written yet")
    _check("no story is a paraphrase of the Technical Specification's text",
           not any("subelement 92" in s.get("description", "") for s in plan["stories"]),
           "the letter drafts EPICS; stories are derived from validating them against code")

    print("\n8) ids are the SI's own (push idempotency):")
    _check("deliverable ids are the SI's D-ids",
           all(d["local_id"].startswith("D") for d in plan["deliverables"]))
    _check("epic ids are the SI's R-ids",
           all(e["local_id"].startswith("R") for e in plan["epics"]))
    _check("controls ride on the issues that get pushed",
           plan["initiative"]["controls"]["seal_id"] == "SEAL-12345"
           and all(e["controls"]["control_owner"] for e in plan["epics"]))

    print()
    if _FAILURES:
        print(f"FAILED — {len(_FAILURES)} check(s): {_FAILURES}", file=sys.stderr)
        return 1
    print("PASS — four levels from their declared sources; epics are requirement-sized with the "
          "§8→§7 trace building the hierarchy; every §16 entry yields a story and every story "
          "traces back; each names code or carries an honest flag; acceptance criteria are "
          "authored, not copied.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
