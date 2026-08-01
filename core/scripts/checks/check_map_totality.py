#!/usr/bin/env python3
"""check_map_totality.py — family-2 context checks on the code map (D-A23, D-A19).

Run **in-build**, not at §10: these need a produced artifact, so they cannot run at build-check
time at all. They are the code-side twin of `check_index_completeness.py` on the doc side, and
they exist for the same reason — the design's central claim is that nothing is silently
invisible, and a claim like that is worth exactly as much as the check behind it.

  1. **Module totality** — every file is in exactly one module. A file in no module is invisible
     to tier 1 **forever**: no assertion can ever reach it, and nothing in the output looks
     wrong. This is *the* failure mode the whole design exists to avoid.
  2. **Purpose totality** — every file has a purpose **or** appears in `unanalyzable[]` with a
     reason. A file with neither is indistinguishable from one nobody looked at.
  3. **`members[]` ↔ `files[].module` consistency** — the two representations are generated
     together and must agree. They are redundant on purpose (tier 1 reads `members[]` to avoid
     loading every file entry), and redundancy without a check is just two things that can drift.
  4. **No module purpose is a copy of a member's** — synthesis must *abstract*. A copied purpose
     describes one member and tells tier 1 nothing about the rest, while looking perfectly
     healthy. Only checkable because synthesis runs after resolution.
  5. **`unclustered` always passes tier 1** — the doubly-unknown bucket cannot be ruled out,
     because there is nothing to rule it out *on*.
  6. **Low confidence widens, never excludes** — a module whose purpose cannot be trusted to
     describe it cannot be trusted to exclude it either.

Run: python3 core/scripts/checks/check_map_totality.py <code_map_dir> | --demo
"""
from __future__ import annotations

import json
import sys
from dataclasses import dataclass, field
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]

UNCLUSTERED = "unclustered"


@dataclass
class MapCheckResult:
    name: str = "family-2 context checks (code map)"
    violations: list = field(default_factory=list)
    files: int = 0
    modules: int = 0

    @property
    def ok(self) -> bool:
        return not self.violations


def check_map(components: dict, files: dict, *, low_confidence_threshold: float = 0.5
              ) -> MapCheckResult:
    res = MapCheckResult()
    comps = components.get("components") or []
    file_entries = files.get("files") or []
    res.files, res.modules = len(file_entries), len(comps)
    report = components.get("coverage_report") or {}

    by_path = {f["path"]: f for f in file_entries}
    if len(by_path) != len(file_entries):
        res.violations.append("duplicate path in files[]")

    # 1) module totality — exactly one, never zero
    seen: dict[str, list[str]] = {}
    for c in comps:
        for m in c.get("members") or []:
            seen.setdefault(m, []).append(c["module"])
    for path, mods in sorted(seen.items()):
        if len(mods) > 1:
            res.violations.append(
                f"{path} is a member of {len(mods)} modules {mods} — membership must be exactly one")
    orphans = sorted(set(by_path) - set(seen))
    if orphans:
        res.violations.append(
            f"{len(orphans)} file(s) belong to NO module (first: {orphans[0]}) — invisible to "
            f"tier 1 forever, which is the failure this design exists to prevent")
    ghosts = sorted(set(seen) - set(by_path))
    if ghosts:
        res.violations.append(f"members[] names {len(ghosts)} path(s) with no file entry: {ghosts[:3]}")

    # 2) purpose totality — a purpose, or a NAMED reason
    declared_unanalyzable = {u["path"] for u in (report.get("unanalyzable") or [])}
    for f in file_entries:
        if f.get("purpose"):
            continue
        if f["path"] not in declared_unanalyzable:
            res.violations.append(
                f"{f['path']} has no purpose and is not in unanalyzable[] — silently absent")
        elif not f.get("unanalyzable_reason"):
            res.violations.append(f"{f['path']} is unanalyzable with no reason given")
    for u in report.get("unanalyzable") or []:
        if by_path.get(u["path"], {}).get("purpose"):
            res.violations.append(f"{u['path']} is listed unanalyzable but HAS a purpose")

    # 3) members[] ↔ files[].module
    for c in comps:
        for m in c.get("members") or []:
            actual = by_path.get(m, {}).get("module")
            if actual is not None and actual != c["module"]:
                res.violations.append(
                    f"{m}: components says {c['module']!r} but files[].module says {actual!r}")
    for f in file_entries:
        mods = seen.get(f["path"], [])
        if mods and f["module"] not in mods:
            res.violations.append(
                f"{f['path']}: files[].module {f['module']!r} is not in any component's members[]")

    # 4) synthesis abstracts, never copies
    for c in comps:
        mem = c.get("members") or []
        if len(mem) < 2:
            continue                      # a singleton's purpose IS its file's (D-A19)
        purposes = {by_path[m]["purpose"] for m in mem if m in by_path and by_path[m].get("purpose")}
        if c.get("purpose") in purposes:
            res.violations.append(
                f"module {c['module']!r} purpose is a VERBATIM COPY of one member's — synthesis "
                f"must abstract; a copy describes one file and tells tier 1 nothing about the rest")

    # 5) the unclustered bucket always passes tier 1
    for c in comps:
        if c["module"].split(":")[-1] == UNCLUSTERED and not c.get("always_pass_tier1"):
            res.violations.append(
                "the `unclustered` bucket must carry always_pass_tier1 — it is the doubly-unknown "
                "population, so there is nothing it could be safely ruled out on")

    # 6) low confidence widens rather than excludes
    for c in comps:
        if c.get("purpose_confidence", 1.0) < low_confidence_threshold:
            if c["module"] not in (report.get("low_confidence_modules") or []):
                res.violations.append(
                    f"module {c['module']!r} is low-confidence but absent from the coverage "
                    f"report's low_confidence_modules — tier 1 must know to widen on it")
    return res


def _demo() -> int:
    import copy

    sys.path.insert(0, str(REPO_ROOT / "core" / "scripts"))
    import validate_onboarding as G
    import yaml
    from code_map_build import build_map

    profile = yaml.safe_load(
        (REPO_ROOT / "core" / "code_profiles" / "c_repo.profile.yaml").read_text())
    comps, files, _ = build_map(REPO_ROOT / "fixtures" / "c_repo", profile,
                                repo="c_repo", commit_sha="9f3c1ab", seal_id="SEAL-12345",
                                exclude=("verify_*.py",))
    res = check_map(comps, files,
                    low_confidence_threshold=profile["purpose"]["low_confidence_threshold"])
    print(f"{res.name} — {res.files} files / {res.modules} modules")
    for v in res.violations:
        print(f"  - {v}")
    assert res.ok, "the real map must pass every family-2 check"
    print("  [PASS] module totality · purpose totality · members↔module · abstraction · "
          "unclustered · confidence")

    mutations = [
        ("a file in no module",
         lambda c, f: c["components"][0]["members"].pop(),
         "belong to NO module"),
        ("a file in two modules",
         lambda c, f: c["components"][1]["members"].append(c["components"][0]["members"][0]),
         "must be exactly one"),
        ("a purpose silently dropped",
         lambda c, f: f["files"][0].__setitem__("purpose", None),
         "silently absent"),
        ("unanalyzable with no reason",
         lambda c, f: (f["files"][0].__setitem__("purpose", None),
                       c["coverage_report"]["unanalyzable"].append({"path": f["files"][0]["path"],
                                                                    "reason": "x"}),
                       f["files"][0].pop("unanalyzable_reason", None)),
         "no reason given"),
        ("members[] and files[].module disagree",
         lambda c, f: f["files"][0].__setitem__("module", "somewhere_else"),
         "is not in any component's members"),
        ("a module purpose copied from a member",
         lambda c, f: _copy_member_purpose(c, f),
         "VERBATIM COPY"),
    ]
    print("\nnegatives (each must be caught by the RIGHT check):")
    for label, mutate, expect in mutations:
        bad_c, bad_f = copy.deepcopy(comps), copy.deepcopy(files)
        mutate(bad_c, bad_f)
        r = check_map(bad_c, bad_f)
        assert not r.ok, f"{label!r} should have been caught"
        hit = next((v for v in r.violations if expect in v), None)
        assert hit, f"{label!r} caught, but not by {expect!r}: {r.violations}"
        print(f"  {label:38} -> CAUGHT: {hit[:56]}…")

    print("\nPASS — every file is in exactly one module with a purpose or a named reason; "
          "members[] and files[].module agree; synthesis abstracts; the unclustered bucket "
          "always passes tier 1.")
    return 0


def _copy_member_purpose(c: dict, f: dict) -> None:
    by_path = {x["path"]: x for x in f["files"]}
    for comp in c["components"]:
        mem = [m for m in comp["members"] if by_path.get(m, {}).get("purpose")]
        if len(comp["members"]) >= 2 and mem:
            comp["purpose"] = by_path[mem[0]]["purpose"]
            return


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if "--demo" in argv or not argv:
        return _demo()
    d = Path(argv[0])
    res = check_map(json.loads((d / "components.json").read_text()),
                    json.loads((d / "files.json").read_text()))
    print(f"{res.name} — {'PASS' if res.ok else 'FAIL'} ({res.files} files, {res.modules} modules)")
    for v in res.violations:
        print(f"  - {v}")
    return 0 if res.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
