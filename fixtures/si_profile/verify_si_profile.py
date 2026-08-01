#!/usr/bin/env python3
"""verify_si_profile.py — TASK-108 proof: the SI profile transcribes the ladder exactly.

§10.5′ (`check_disposition_totality.py`) proves the routing matrix is **total** — no orphan
section, no orphan class. That is a property check: it would pass a matrix that is complete but
*wrong*, e.g. one where §14 Dependencies was marked `architecture: S` instead of `P`.

D-A13 says **transcribe exactly**, so this file is the **oracle**: the matrix, the section
table and the status assignments re-typed here straight from the ADR, and compared cell by
cell against the profile. Two independent transcriptions disagreeing is the only reliable way
to catch a slip in a 18 × 8 grid.

What it checks:

  1. **D-A13 routing matrix, cell-identical** — all 18 rows × 8 columns, P/S/E/blank.
  2. **D-A3 section table** — title, `authored`, and enrichment `touch` per section.
  3. **D-A10 statuses** — conditional / required-may-be-empty / required.
  4. **D-A11 boundaries** — §4, §9, §15 each carry their boundary line, and it says the thing
     that distinguishes them (no dates/metrics · external reference · measurable).
  5. **must_capture is usable as a retrieval query** (D-A18's third job) — present, plural,
     and concrete rather than a restatement of the section title.
  6. **D-A4 binding rules are recorded** where a later reader could otherwise undo them —
     §8 extend-only, §12 two-way, §5 asymmetric verdict, §1 regenerate-not-revise.

Run: python3 fixtures/si_profile/verify_si_profile.py
"""
from __future__ import annotations

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_REPO_ROOT / "core" / "scripts"))
sys.path.insert(0, str(_REPO_ROOT / "core" / "scripts" / "checks"))

import yaml  # noqa: E402

sys.path.insert(0, str(_REPO_ROOT / "core" / "scripts" / "checks"))
from check_discovery_adequacy import check_discovery_adequacy  # noqa: E402

_DOMAIN = "payment_brand"
_FAILURES: list[str] = []

# ── ORACLE 1 — D-A13, re-typed from the ADR. Columns in the ADR's own order. ───────────────
# BizReq · TechSpec · DomKnow · Arch · Prior · Frame · Discovery · Code
_COLS = ("business_requirement", "technical_specification", "product_domain_knowledge",
         "architecture", "prior_artifact", "frame", "discovery", "codebase")
_DA13 = {
    1:  ("",  "",  "",  "",  "",  "P", "",  ""),
    2:  ("P", "",  "S", "S", "",  "",  "",  "E"),
    3:  ("P", "",  "S", "",  "",  "",  "",  ""),
    4:  ("P", "",  "",  "",  "",  "S", "",  ""),
    5:  ("",  "",  "P", "S", "",  "",  "",  "E"),
    6:  ("S", "",  "P", "",  "",  "",  "",  "E"),
    7:  ("P", "S", "",  "",  "",  "S", "S", "E"),
    8:  ("P", "P", "",  "",  "S", "",  "",  "E"),
    9:  ("",  "",  "",  "",  "S", "S", "P", ""),
    10: ("",  "P", "",  "P", "",  "",  "",  "E"),
    11: ("",  "",  "",  "",  "S", "P", "S", ""),
    12: ("P", "",  "",  "",  "",  "S", "P", "E"),
    13: ("",  "",  "S", "S", "",  "",  "P", "E"),
    14: ("",  "S", "",  "P", "",  "",  "",  "E"),
    15: ("P", "S", "",  "",  "",  "S", "S", ""),
    16: ("",  "",  "",  "",  "",  "",  "",  "P"),
    17: ("",  "",  "",  "",  "",  "",  "",  ""),
    18: ("",  "",  "",  "",  "",  "",  "",  "P"),
}

# ── ORACLE 2 — D-A3 section table: title, authored, enrichment touch. ──────────────────────
_DA3 = {
    1:  ("Executive summary",             "v1",                ["regenerate"]),
    2:  ("Problem statement",             "v1",                ["verdict", "correct"]),
    3:  ("Client need & demand",          "v1",                ["none"]),
    4:  ("Business objectives",           "v1",                ["none"]),
    5:  ("Personas & actors",             "v1",                ["verdict"]),
    6:  ("High-level use case",           "v1",                ["verdict", "correct"]),
    7:  ("Deliverables",                  "v1",                ["extend"]),
    8:  ("Business requirements",         "v1",                ["extend"]),
    9:  ("Strategic alignment",           "v1",                ["none"]),
    10: ("Constraints & design principles", "v1",              ["verdict", "extend"]),
    11: ("Stakeholders",                  "v1",                ["none"]),
    12: ("Out of scope",                  "v1",                ["extend"]),
    13: ("Assumptions & risks",           "v1",                ["verdict", "correct"]),
    14: ("Dependencies",                  "v1",                ["verdict", "extend"]),
    15: ("Success criteria",              "v1",                ["none"]),
    16: ("Derived system impacts",        "v2_only",           []),
    17: ("Open questions",                "v1_extended_in_v2", ["extend"]),
    18: ("Verification summary",          "v2_only",           []),
}

# ── ORACLE 3 — D-A10 statuses. ────────────────────────────────────────────────────────────
_CONDITIONAL = {3, 6, 9}
_MAY_BE_EMPTY = {5, 14, 17}


def _check(label: str, ok: bool, detail: str = "") -> None:
    print(f"  [{'PASS' if ok else 'FAIL'}] {label}" + (f" — {detail}" if detail else ""))
    if not ok:
        _FAILURES.append(label)


def main() -> int:
    path = _REPO_ROOT / "core" / "profiles" / _DOMAIN / f"si_profile.{_DOMAIN}.yaml"
    profile = yaml.safe_load(path.read_text(encoding="utf-8"))
    by_id = {s["id"]: s for s in profile["sections"]}

    print(f"verify_si_profile — {path.relative_to(_REPO_ROOT)}\n")

    # 1) The D-A13 matrix, cell by cell.
    print("1) D-A13 routing matrix — cell-identical (18 rows × 8 columns):")
    mismatches: list[str] = []
    for sid, row in _DA13.items():
        s = by_id.get(sid, {})
        actual = {**(s.get("classes") or {}), **(s.get("inputs") or {})}
        for col, expected in zip(_COLS, row):
            got = actual.get(col, "")
            if got != expected:
                mismatches.append(
                    f"§{sid}.{col}: profile={got or '(blank)'} expected={expected or '(blank)'}")
    _check("all 144 cells match D-A13", not mismatches, "; ".join(mismatches[:4]))
    _check("`other` appears in no row (the empty column IS the definition, D-A12)",
           not any("other" in (s.get("classes") or {}) for s in profile["sections"]))

    # 2) The D-A3 section table.
    print("\n2) D-A3 section table — title, authored, enrichment touch:")
    bad_title = [f"§{i}" for i, (t, _, _) in _DA3.items() if by_id.get(i, {}).get("title") != t]
    bad_auth = [f"§{i}" for i, (_, a, _) in _DA3.items() if by_id.get(i, {}).get("authored") != a]
    bad_touch = [f"§{i}: {by_id.get(i, {}).get('touch')} != {t}"
                 for i, (_, _, t) in _DA3.items() if (by_id.get(i, {}).get("touch") or []) != t]
    _check("all 18 titles match", not bad_title, ", ".join(bad_title))
    _check("`authored` matches (v1 / v1_extended_in_v2 / v2_only)", not bad_auth, ", ".join(bad_auth))
    _check("enrichment `touch` matches", not bad_touch, "; ".join(bad_touch[:3]))
    _check("§3/§4/§9/§11/§15 are never touched by enrichment (D-A3)",
           all((by_id[i].get("touch") or []) == ["none"] for i in (3, 4, 9, 11, 15)))

    # 3) D-A10 statuses.
    print("\n3) D-A10 statuses — dispositioned, never absent:")
    cond = {i for i, s in by_id.items() if s.get("status") == "conditional"}
    empt = {i for i, s in by_id.items() if s.get("status") == "required_may_be_empty"}
    _check("conditional set is exactly §3/§6/§9", cond == _CONDITIONAL, f"got {sorted(cond)}")
    _check("required-may-be-empty set is exactly §5/§14/§17", empt == _MAY_BE_EMPTY,
           f"got {sorted(empt)}")
    _check("every other section is `required`",
           all(by_id[i]["status"] == "required"
               for i in by_id if i not in _CONDITIONAL | _MAY_BE_EMPTY))
    _check("each conditional carries a reason (N/A without one is an omission with manners)",
           all(str(by_id[i].get("conditional_reason", "")).strip() for i in _CONDITIONAL))

    # 4) D-A11 boundaries — the three sections that blur.
    print("\n4) D-A11 boundaries — §4 intent · §9 portfolio fit · §15 measurable outcome:")
    for sid in (4, 9, 15):
        _check(f"§{sid} carries a boundary line", bool(str(by_id[sid].get("boundary", "")).strip()))
    b4, b9, b15 = (by_id[i]["boundary"].lower() for i in (4, 9, 15))
    _check("§4's boundary forbids dates and metrics", "no dates" in b4 and "no metrics" in b4)
    _check("§9's boundary demands something external to the project", "external" in b9)
    _check("§15's boundary demands measurability + a trace to an objective",
           "measurable" in b15 and "trace" in b15)

    # 5) must_capture as a retrieval query (D-A18's third job).
    print("\n5) must_capture — checklist, G1 score input, AND retrieval query:")
    authored_sections = [s for s in profile["sections"]]
    thin = [f"§{s['id']}" for s in authored_sections if len(s.get("must_capture") or []) < 3]
    _check("every section carries ≥3 must_capture items", not thin, ", ".join(thin))
    # A must_capture that merely echoes the title matches every index entry and selects nothing.
    echoes = []
    for s in authored_sections:
        title_words = {w.lower().strip(",&") for w in s["title"].split()}
        for item in s.get("must_capture") or []:
            words = item.split()
            novel = [w for w in words if w.lower().strip(".,—") not in title_words]
            if len(words) < 6 or len(novel) < 5:
                echoes.append(f"§{s['id']}: {item[:40]}")
    _check("no must_capture merely restates its section title", not echoes, "; ".join(echoes[:3]))
    # Sections that elicit from the operator must be able to probe; derived ones must not.
    derived = {1, 16, 17, 18}
    no_probe = [f"§{s['id']}" for s in authored_sections
                if s["id"] not in derived and not (s.get("probe_if_missing") or [])]
    _check("every non-derived section can probe for what it is missing", not no_probe,
           ", ".join(no_probe))
    _check("derived sections (§1/§16/§17/§18) carry no probes — they are not elicited",
           all(not (by_id[i].get("probe_if_missing") or []) for i in derived))

    # 6) D-A4's binding rules are recorded where they could otherwise be undone.
    print("\n6) D-A4 binding rules recorded on the sections they constrain:")
    note = lambda i: str(by_id[i].get("touch_note", "")).lower()  # noqa: E731
    _check("§8 records extend-only + why (code cannot contradict an intent)",
           by_id[8]["touch"] == ["extend"] and "never corrected" in note(8) and "intent" in note(8))
    _check("§12 records the two-way door", "two-way" in note(12))
    _check("§5 records the asymmetric verdict (system actors only)",
           "asymmetric" in note(5) and "system actor" in note(5))
    _check("§1 records regenerate-not-revise", "regenerate" in by_id[1]["touch"]
           and "never revises" in note(1))
    _check("§13 records that v1 must author assumptions in checkable form",
           "checkable" in note(13))
    _check("§18 records summary-not-ledger", "not a ledger" in note(18))

    # 7) Discovery adequacy — run HERE because the SI profile is the artifact it checks, and
    #    until now nothing in the routine sweep invoked it. A check with no caller is a check
    #    that stops being true the first time someone edits what it guards.
    print("\n7) discovery-question adequacy (D-A13) over this profile:")
    adq = check_discovery_adequacy("payment_brand", repo_root=_REPO_ROOT)
    _check("no discovery-primary must_capture is left unelicited", adq.ok,
           "; ".join(adq.errors[:2]))
    _check("every must_capture in every elicited section has a question",
           adq.covered == adq.total, f"{adq.covered}/{adq.total}")
    _check("§9/§12/§13 are the discovery-primary set (D-A13)",
           adq.primary_sections == [9, 12, 13], str(adq.primary_sections))

    print()
    if _FAILURES:
        print(f"FAILED — {len(_FAILURES)} check(s): {_FAILURES}", file=sys.stderr)
        return 1
    print("PASS — the SI profile is a cell-identical transcription of D-A13, matches D-A3's "
          "section table and D-A10's statuses, carries D-A11's boundaries, and records D-A4's "
          "binding rules where they constrain.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
