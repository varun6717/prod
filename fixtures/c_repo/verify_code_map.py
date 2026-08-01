#!/usr/bin/env python3
"""verify_code_map.py — TASK-114 proof: the two-file code map over `c_repo` (§3.3 amended).

The map is the substrate everything downstream matches against, so what is proven here is that it
is TOTAL (nothing silently invisible), DETERMINISTIC (the cache key means what it says), and that
the model/deterministic split held.

  1. **Oracle match, twice** — the build reproduces the re-signed oracle, byte-identical on a
     second run.
  2. **Two files with the §3.3 shape** — components + files, no `tags` anywhere.
  3. **Family-2 totality** — every file in exactly one module with a purpose or a named reason.
  4. **Synthesis abstracted** — no module purpose is a copy of a member's.
  5. **The purpose ladder ran** — A/B/C* all populated, provenance recorded, declared purposes
     still citable to a line.
  6. **Caching** — a second build over unchanged files does NO new purpose work.
  7. **The seeded phenomena surface** — the versioned pair in
     `duplicates_requiring_disposition[]`, the unanalyzable file named with a reason.
  8. **The map is requirement-blind** — no requirement, assertion or section reference anywhere.

Run: python3 fixtures/c_repo/verify_code_map.py
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_REPO_ROOT = _HERE.parents[1]
sys.path.insert(0, str(_REPO_ROOT / "core" / "scripts"))
sys.path.insert(0, str(_REPO_ROOT / "core" / "scripts" / "checks"))

import yaml  # noqa: E402
from code_map_build import PurposeCache, build_map, write_map  # noqa: E402
from check_map_totality import check_map  # noqa: E402

_FAILURES: list[str] = []


def _check(label: str, ok: bool, detail: str = "") -> None:
    print(f"  [{'PASS' if ok else 'FAIL'}] {label}" + (f" — {detail}" if detail else ""))
    if not ok:
        _FAILURES.append(label)


def main() -> int:
    profile = yaml.safe_load((_REPO_ROOT / "core/code_profiles/c_repo.profile.yaml").read_text())
    kw = dict(repo="c_repo", commit_sha="9f3c1ab", seal_id="SEAL-12345",
              exclude=("verify_*.py",))   # the fixture's own harness is not repo content
    comps, files, cache = build_map(_HERE, profile, **kw)
    report = comps["coverage_report"]

    print("verify_code_map — the two-file map over fixtures/c_repo\n")

    # The oracle grades nothing until a human signs it (the TASK-005 binding rule). Two
    # amendments are outstanding, so this run proves the map MATCHES the oracle without
    # proving the oracle is right. Surfaced loudly rather than left to a reader of SIGNOFF.md,
    # because an all-green sweep otherwise overstates what has been established.
    signoff = (_REPO_ROOT / "fixtures/c_repo/SIGNOFF.md").read_text(encoding="utf-8")
    if "PENDING RE-SIGN-OFF" in signoff:
        print("  ⚠  ORACLE IS UNSIGNED — SIGNOFF.md carries a PENDING RE-SIGN-OFF. The checks")
        print("     below prove the build MATCHES the oracle; they do NOT establish that the")
        print("     oracle is correct. That needs an operator signature (TASK-005 rule).\n")

    # 1) oracle match, twice
    print("1) oracle match + determinism:")
    oc = json.loads((_HERE / "expected_components.json").read_text())
    of = json.loads((_HERE / "expected_files.json").read_text())
    _check("components matches the re-signed oracle", comps == oc)
    _check("files matches the re-signed oracle", files == of)
    comps2, files2, _ = build_map(_HERE, profile, **kw)
    _check("a second build is byte-identical (the cache key means what it says)",
           json.dumps(comps2, sort_keys=True) == json.dumps(comps, sort_keys=True)
           and json.dumps(files2, sort_keys=True) == json.dumps(files, sort_keys=True))

    # 2) the §3.3 shape
    print("\n2) §3.3 amended shape — two files, no tags:")
    _check("components carries modules with explicit members[]",
           all({"module", "purpose", "members", "purpose_confidence"} <= set(c)
               for c in comps["components"]), f"{len(comps['components'])} modules")
    _check("files carries per-file purpose + provenance",
           all({"path", "module", "purpose_source", "interfaces", "depends_on", "used_by"} <= set(f)
               for f in files["files"]), f"{len(files['files'])} files")
    blob = json.dumps(comps) + json.dumps(files)
    _check("`tags` appears nowhere in the map (deleted with the vocabulary)", '"tags"' not in blob)
    _check("both files carry the profile_sha half of the cache key",
           comps.get("profile_sha") and files.get("profile_sha"), comps.get("profile_sha"))
    c_path, f_path = write_map(comps, files, _REPO_ROOT / "runs" / "_scratch_map")
    _check("writes components.json + files.json", c_path.exists() and f_path.exists())
    for p in (c_path, f_path):
        p.unlink()
    c_path.parent.rmdir()

    # 3) family-2 totality
    print("\n3) family-2 context checks:")
    res = check_map(comps, files,
                    low_confidence_threshold=profile["purpose"]["low_confidence_threshold"])
    _check("module totality · purpose totality · members↔module · abstraction", res.ok,
           "; ".join(res.violations[:2]))
    members = [m for c in comps["components"] for m in c["members"]]
    _check("every file is a member of exactly one module",
           sorted(members) == sorted(f["path"] for f in files["files"])
           and len(members) == len(set(members)), f"{len(members)} memberships")

    # 4) synthesis abstracted, never copied
    print("\n4) module purpose synthesis:")
    by_path = {f["path"]: f for f in files["files"]}
    multi = [c for c in comps["components"] if len(c["members"]) > 1]
    _check("there ARE multi-member modules to synthesise for", bool(multi), f"{len(multi)}")
    copies = [c["module"] for c in multi
              if c["purpose"] in {by_path[m]["purpose"] for m in c["members"]}]
    _check("no multi-member module purpose is a verbatim copy of a member's", not copies, str(copies))
    singles = [c for c in comps["components"] if len(c["members"]) == 1]
    _check("a singleton's purpose IS its file's (no synthesis needed)",
           all(c["purpose"] == by_path[c["members"][0]]["purpose"] for c in singles),
           f"{len(singles)} singletons")

    # 5) the purpose ladder
    print("\n5) purpose resolution ladder (A → B → C → C* → unanalyzable):")
    dist = report["stage_distribution"]
    _check("stage A (declared) dominates — the D-A20 finding", dist.get("A", 0) >= 20, str(dist))
    _check("stage B (header prose) fired", dist.get("B", 0) > 0)
    _check("stage C* (symbols/prototypes) fired — headers are not unanalyzable",
           dist.get("C*", 0) > 0,
           "a body-only scan would have called every declaration header unanalyzable")
    _check("provenance recorded on every resolved file",
           all(f["purpose_source"] for f in files["files"] if f["purpose"]))
    declared = [f for f in files["files"] if f["purpose_source"] == "declared"]
    _check("declared purposes stay citable to a line",
           all("purpose_declared_line" in f for f in declared), f"{len(declared)} declared")
    ok_lines = all(
        f["purpose"] in (_HERE / f["path"]).read_text().splitlines()[f["purpose_declared_line"] - 1]
        for f in declared)
    _check("each cited line actually contains the purpose", ok_lines)

    # 6) caching
    print("\n6) purpose caching (per file CONTENT hash, D-A21):")
    warm = PurposeCache(entries=dict(cache.entries))
    build_map(_HERE, profile, cache=warm, **kw)
    _check("a second build over unchanged files does NO new purpose work",
           warm.misses == 0, f"{warm.hits} hits / {warm.misses} misses")
    _check("the first build did the work", cache.misses > 0, f"{cache.misses} misses")

    # 7) the seeded phenomena surface for a human
    print("\n7) coverage report surfaces what needs a human:")
    _check("the versioned pair is reported for disposition (D-A16), not silently resolved",
           report["duplicates_requiring_disposition"]
           == [{"base": "src/messaging/iso8583.c", "variant": "src/messaging/iso8583_v2.c"}])
    _check("both duplicate files are mapped normally",
           all(p in by_path for p in ("src/messaging/iso8583.c", "src/messaging/iso8583_v2.c")))
    _check("unanalyzable files are NAMED with a reason", 
           all(u.get("reason") for u in report["unanalyzable"]),
           f"{len(report['unanalyzable'])} unanalyzable")
    _check("low-confidence modules are listed so tier 1 knows to widen",
           "low_confidence_modules" in report, str(report["low_confidence_modules"]))

    # 8) requirement-blindness
    print("\n8) the map is requirement-blind (D-A21):")
    _check("no requirement/assertion/section reference anywhere in the map",
           not re.search(r"\b(assertion|requirement|R\d+\.\d+|§\d+)\b", blob, re.I),
           "'in scope' is computed per assertion at impact time, never stored in the map")

    print()
    if _FAILURES:
        print(f"FAILED — {len(_FAILURES)} check(s): {_FAILURES}", file=sys.stderr)
        return 1
    print("PASS — the map matches the re-signed oracle and rebuilds identically; every file is in "
          "exactly one module with a purpose or a named reason; synthesis abstracted; purposes "
          "cache on content hash; the duplicate pair and the unanalyzable file surface for a "
          "human; the map names no requirement.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
