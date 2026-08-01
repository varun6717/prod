#!/usr/bin/env python3
"""check_disposition_totality.py — §10.5′ (D11.3, D-A23): the routing matrix is TOTAL.

The §10 build check that replaces the retired §10.1 vocabulary containment. Where §10.1 asked
"is every tag in the dictionary?", this asks the two questions the tag-free design needs:

  1. **No orphan section.** Every SI section (except §1/§17/§18) has at least one routed input.
     A section nothing routes to is a section that will be authored from nothing — and the
     failure is silent, because an empty section and a starved section look identical.
  2. **No orphan class.** Every disposition the UI offers appears in at least one matrix cell.
     A class the operator can pick that nothing routes means the operator labels an artifact,
     the artifact is ingested, and it is then read by no section — the upload that silently
     does nothing, which is the exact failure D-A12 called out.
  3. **Conditional sections are marked conditional**, so FR-SI-06 can render them dispositioned
     ("Not applicable — <reason>") rather than absent. An omitted section and a forgotten
     section look identical (D-A10).

The two directions are deliberately both checked. Section-side alone would pass a taxonomy with
a dead class; class-side alone would pass a profile with a starved section.

**§1/§17/§18 are the declared exceptions** (D-A13): §1 is derived from the body, §17 accumulates
gaps, §18 counts verdicts. None takes an input class. They are named here as data so the
exemption is visible rather than implicit in a passing check.

Consumes the SI profile (`core/profiles/<domain>/si_profile.<domain>.yaml`) and the taxonomy in
`core/scripts/dispositions.py` — the same definition the UI and the backend validate against, so
the check cannot drift from what the operator is actually offered.

Run standalone:  python3 core/scripts/checks/check_disposition_totality.py [--domain payment_brand]
Registered in `build_checks.py` as §10.5′.
"""
from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT / "core" / "scripts") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "core" / "scripts"))

from dispositions import (  # noqa: E402
    NEVER_ROUTED, NON_DISPOSITION_INPUTS, OPERATOR_DISPOSITIONS, ALL_DISPOSITIONS,
)

# D-A13: the three sections that take no input class, by design.
NO_INPUT_SECTIONS: frozenset[int] = frozenset({1, 17, 18})

# D-A10: the three conditional sections. A profile that fails to mark one cannot render it
# dispositioned, so FR-SI-06's "never absent" guarantee quietly stops holding.
CONDITIONAL_SECTIONS: frozenset[int] = frozenset({3, 6, 9})

SECTION_COUNT = 18                      # D11.1 — fixed contract, not per-domain
VALID_MARKS = frozenset({"P", "S", "E"})


@dataclass
class TotalityResult:
    name: str = "§10.5′ disposition-class totality"
    ok: bool = True
    violations: list[str] = field(default_factory=list)
    sections: int = 0
    routed_classes: set[str] = field(default_factory=set)
    excluded: set[str] = field(default_factory=set)


def load_profile(domain: str, repo_root: Path = REPO_ROOT) -> dict:
    """Load ``core/profiles/<domain>/si_profile.<domain>.yaml``."""
    import yaml

    path = repo_root / "core" / "profiles" / domain / f"si_profile.{domain}.yaml"
    if not path.is_file():
        raise FileNotFoundError(f"no SI profile for domain {domain!r} at {path}")
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def check_disposition_totality(domain: str = "payment_brand", *,
                               repo_root: Path = REPO_ROOT) -> TotalityResult:
    """Run §10.5′ for ``domain``. Returns a result; raises only if the profile is unreadable."""
    res = TotalityResult()
    profile = load_profile(domain, repo_root)
    sections = profile.get("sections") or []
    res.sections = len(sections)

    by_id: dict[int, dict] = {}
    for s in sections:
        sid = s.get("id")
        if not isinstance(sid, int):
            res.violations.append(f"section {s.get('title', '?')!r} has a non-integer id {sid!r}")
            continue
        if sid in by_id:
            res.violations.append(f"duplicate section id {sid}")
        by_id[sid] = s

    # The contract is fixed at 18 (D11.1) — a profile that drops one has silently narrowed it.
    missing = [n for n in range(1, SECTION_COUNT + 1) if n not in by_id]
    if missing:
        res.violations.append(
            f"SI contract is a FIXED {SECTION_COUNT} sections (D11.1); profile is missing {missing}")
    extra = [n for n in by_id if not 1 <= n <= SECTION_COUNT]
    if extra:
        res.violations.append(f"section id(s) outside 1–{SECTION_COUNT}: {sorted(extra)}")

    for sid in sorted(by_id):
        s = by_id[sid]
        where = f"§{sid} {s.get('title', '?')!r}"
        classes = s.get("classes") or {}
        inputs = s.get("inputs") or {}

        if not isinstance(classes, dict) or not isinstance(inputs, dict):
            res.violations.append(f"{where}: `classes` and `inputs` must be mappings")
            continue

        # Keys must be real: a typo'd class silently routes nothing.
        for cls in classes:
            if cls not in ALL_DISPOSITIONS:
                res.violations.append(
                    f"{where}: `classes` names {cls!r}, which is not a disposition "
                    f"(valid: {list(ALL_DISPOSITIONS)})")
            if cls in NEVER_ROUTED:
                res.violations.append(
                    f"{where}: routes {cls!r}, which is declared NEVER_ROUTED — it is "
                    f"background context only and must not be a section's input (D-A12)")
        for inp in inputs:
            if inp not in NON_DISPOSITION_INPUTS:
                res.violations.append(
                    f"{where}: `inputs` names {inp!r}; only {list(NON_DISPOSITION_INPUTS)} are "
                    f"non-disposition input sources (a disposition belongs under `classes`)")

        # Marks must be P/S/E.
        for key, mark in list(classes.items()) + list(inputs.items()):
            if mark not in VALID_MARKS:
                res.violations.append(
                    f"{where}: {key!r} has mark {mark!r}; expected one of {sorted(VALID_MARKS)}")

        # 1) No orphan section.
        if sid not in NO_INPUT_SECTIONS and not classes and not inputs:
            res.violations.append(
                f"{where}: no routed input at all — it would be authored from nothing. Only "
                f"§{sorted(NO_INPUT_SECTIONS)} may take none (D-A13)")
        if sid in NO_INPUT_SECTIONS and classes and sid != 16:
            # §16/§18 legitimately take `codebase`; §1/§17 must take no class.
            if sid in (1, 17):
                res.violations.append(
                    f"{where}: declared as taking no input class (D-A13) but routes {list(classes)}")

        # 3) Conditional sections are marked.
        status = s.get("status")
        if sid in CONDITIONAL_SECTIONS and status != "conditional":
            res.violations.append(
                f"{where}: D-A10 marks this section conditional but the profile says "
                f"status={status!r} — FR-SI-06 could not render it dispositioned")
        if status == "conditional":
            if sid not in CONDITIONAL_SECTIONS:
                res.violations.append(
                    f"{where}: marked conditional, but D-A10's conditional set is "
                    f"§{sorted(CONDITIONAL_SECTIONS)}")
            if not str(s.get("conditional_reason", "")).strip():
                res.violations.append(
                    f"{where}: conditional sections need a `conditional_reason` — "
                    f"'Not applicable' without a reason is an omission with better manners")

        res.routed_classes |= {c for c in classes if c in ALL_DISPOSITIONS}

    # 2) No orphan class — every class the UI OFFERS must be routed somewhere.
    offered = set(OPERATOR_DISPOSITIONS)
    res.excluded = offered & NEVER_ROUTED
    orphans = sorted(offered - res.routed_classes - NEVER_ROUTED)
    if orphans:
        res.violations.append(
            f"disposition class(es) {orphans} are offered by the UI but routed by no section — "
            f"an operator could label an artifact with one and it would be read by nothing")

    res.ok = not res.violations
    return res


# ──────────────────────────────────────────────────────────────────────────────
# Proof. Run: python3 core/scripts/checks/check_disposition_totality.py --demo
#   The real profile passes; each way the matrix can go untotal is caught.
# ──────────────────────────────────────────────────────────────────────────────
def _demo() -> int:
    import copy
    import tempfile

    import yaml

    domain = "payment_brand"
    res = check_disposition_totality(domain)
    print(f"real seam: {res.name} over {domain}")
    print(f"  sections={res.sections}  routed classes={sorted(res.routed_classes)}")
    print(f"  excluded by declaration: {sorted(res.excluded)} (NEVER_ROUTED — D-A12)")
    for v in res.violations:
        print(f"  - {v}")
    assert res.ok, "the real SI profile must pass §10.5′"
    print("  [PASS]")

    good = load_profile(domain)
    mutations = [
        ("orphan section (§13 loses every input)",
         lambda p: (p["sections"][12].__setitem__("classes", {}),
                    p["sections"][12].__setitem__("inputs", {})),
         "no routed input at all"),
        ("orphan class (architecture routed nowhere)",
         lambda p: [s["classes"].pop("architecture", None) for s in p["sections"]
                    if isinstance(s.get("classes"), dict)],
         "routed by no section"),
        ("conditional §9 demoted to required",
         lambda p: next(s for s in p["sections"] if s["id"] == 9).__setitem__("status", "required"),
         "could not render it dispositioned"),
        ("conditional without a reason",
         lambda p: next(s for s in p["sections"] if s["id"] == 3).__setitem__("conditional_reason", ""),
         "need a `conditional_reason`"),
        ("a section dropped from the fixed 18",
         lambda p: p["sections"].pop(5),
         "FIXED 18 sections"),
        ("`other` routed into a section",
         lambda p: next(s for s in p["sections"] if s["id"] == 2)["classes"].__setitem__("other", "S"),
         "declared NEVER_ROUTED"),
        ("frame placed under `classes`",
         lambda p: next(s for s in p["sections"] if s["id"] == 2)["classes"].__setitem__("frame", "S"),
         "is not a disposition"),
        ("a bad mark",
         lambda p: next(s for s in p["sections"] if s["id"] == 2)["classes"].__setitem__(
             "business_requirement", "X"),
         "expected one of"),
    ]

    print("\nnegatives (each must be caught, by the RIGHT check):")
    with tempfile.TemporaryDirectory(prefix="totality-proof-") as tmp:
        root = Path(tmp)
        pdir = root / "core" / "profiles" / domain
        pdir.mkdir(parents=True)
        for label, mutate, expect in mutations:
            bad = copy.deepcopy(good)
            mutate(bad)
            (pdir / f"si_profile.{domain}.yaml").write_text(
                yaml.safe_dump(bad, sort_keys=False), encoding="utf-8")
            r = check_disposition_totality(domain, repo_root=root)
            assert not r.ok, f"{label!r} should have been caught"
            hit = next((v for v in r.violations if expect in v), None)
            assert hit, f"{label!r} caught, but not by {expect!r}: {r.violations}"
            print(f"  {label:42} -> CAUGHT: {hit[:58]}…")

    print("\nPASS — the real matrix is total in both directions; orphan sections, orphan "
          "classes, unmarked conditionals and malformed cells are all caught.")
    return 0


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if "--demo" in argv:
        return _demo()
    domain = "payment_brand"
    if "--domain" in argv:
        domain = argv[argv.index("--domain") + 1]
    res = check_disposition_totality(domain)
    print(f"{res.name} — domain {domain!r}: {'PASS' if res.ok else 'FAIL'}")
    for v in res.violations:
        print(f"  - {v}")
    return 0 if res.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
