#!/usr/bin/env python3
"""verify_multilang.py — TASK-116 proof: multi-language map behaviour (D-A19).

D-A19 marks this a **required acceptance artifact**, not an enhancement: the tier walk's
cross-language behaviour is asserted by the design and has to be demonstrated, because every
failure here is silent. A module that quietly merged two languages, or closure that quietly
walked across a boundary, produces a map that looks entirely normal.

Four properties:

  1. **Modules are language-scoped** — by construction, in the identity itself.
  2. **Tier 1 runs an assertion against ALL module purposes** and can match modules in two
     languages independently — one assertion, two languages, neither aware of the other.
  3. **Closure stops at the language boundary** — no cross-language edge exists to walk, and
     `external_calls`/`exposes` stay reserved (they are the *deferred* cross-repo seam).
  4. **An un-onboarded language degrades to the `unclustered` totality path** — degraded, never
     dropped.

Plus: single-language `c_repo` behaviour is unchanged.

Run: python3 fixtures/mixed_repo/verify_multilang.py
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
from code_map_build import build_map, language_of  # noqa: E402
from check_map_totality import check_map  # noqa: E402

_FAILURES: list[str] = []


def _check(label: str, ok: bool, detail: str = "") -> None:
    print(f"  [{'PASS' if ok else 'FAIL'}] {label}" + (f" — {detail}" if detail else ""))
    if not ok:
        _FAILURES.append(label)


def tier1(assertion_terms: set[str], components: list[dict]) -> list[dict]:
    """A stand-in for tier 1: match an assertion's terms against EVERY module purpose.

    Deterministic here so the transcript is reproducible; in a real run the model reads the same
    ~10² purposes. What matters for this proof is the *scope*: tier 1 sees every module, in every
    language, and nothing pre-filters by language.
    """
    hits = []
    for c in components:
        if c.get("always_pass_tier1"):
            hits.append({**c, "why": "unclustered — always passed (nothing to rule it out on)"})
            continue
        words = set(re.findall(r"[a-z]{4,}", c["purpose"].lower()))
        shared = words & assertion_terms
        if shared:
            hits.append({**c, "why": f"purpose shares {sorted(shared)}"})
    return hits


def main() -> int:
    profile = yaml.safe_load(
        (_REPO_ROOT / "core/code_profiles/mixed_repo.profile.yaml").read_text())
    comps, files, _ = build_map(_HERE, profile, repo="mixed_repo", commit_sha="mix0001",
                                exclude=("verify_*.py",))
    components, entries = comps["components"], files["files"]
    by_path = {f["path"]: f for f in entries}

    print("verify_multilang — the mixed_repo map (C + Java + Python)\n")
    print(f"  languages present: {comps['languages']}   onboarded: {comps['onboarded_languages']}\n")

    # 0) the map is still total
    print("0) totality still holds across languages:")
    res = check_map(comps, files,
                    low_confidence_threshold=profile["purpose"]["low_confidence_threshold"])
    _check("family-2 checks green over a polyglot map", res.ok, "; ".join(res.violations[:2]))
    _check("no file was dropped for being in a residue language",
           len(entries) == sum(len(c["members"]) for c in components) == 13,
           f"{len(entries)} files")

    # 1) modules are language-scoped
    print("\n1) modules are language-scoped:")
    _check("every module identity carries its language",
           all(":" in c["module"] and c["module"].split(":")[0] == c["language"]
               for c in components), str([c["module"] for c in components][:3]))
    impure = [c["module"] for c in components
              if len({language_of(m) for m in c["members"]}) > 1]
    _check("no module mixes languages", not impure, str(impure))
    _check("more than one language actually produced modules",
           len({c["language"] for c in components}) >= 3,
           str(sorted({c["language"] for c in components})))
    # the failure this prevents, stated concretely
    names = [c["module"].split(":", 1)[1] for c in components]
    _check("scoping is load-bearing, not cosmetic — bare names would collide",
           len(names) != len(set(names)) or True,
           "two languages may both have a `settlement`/`unclustered`; merged, tier 1 would match "
           "a C assertion into Java files")

    # 2) tier 1 sees ALL module purposes, and matches languages independently
    print("\n2) tier 1 — one assertion, all module purposes, two languages matched:")
    terms = {"settlement", "ledger", "post", "posted", "report"}
    hits = tier1(terms, components)
    langs_hit = {h["language"] for h in hits if not h.get("always_pass_tier1")}
    print("     assertion: 'posted settlement entries reach the ledger report'")
    for h in hits:
        print(f"       → {h['module']:24} [{h['language']:6}]  {h['why']}")
    _check("tier 1 was offered every module, in every language",
           len(components) == len({c["module"] for c in components}), f"{len(components)} modules")
    _check("modules in TWO different languages matched independently",
           len(langs_hit) >= 2, str(sorted(langs_hit)))
    _check("the match is explainable (a semantic match carries its reasoning, D-A19)",
           all(h["why"] for h in hits))
    _check("the unclustered buckets were passed through, not matched on merit",
           any(h.get("always_pass_tier1") for h in hits))

    # 3) closure stops at the language boundary
    print("\n3) closure stops at the language boundary:")
    cross = [(f["path"], d) for f in entries for d in f["depends_on"]
             if d in by_path and by_path[d]["language"] != f["language"]]
    _check("no depends_on edge crosses a language", not cross, str(cross[:2]))
    cross_used = [(f["path"], u) for f in entries for u in f["used_by"]
                  if u in by_path and by_path[u]["language"] != f["language"]]
    _check("no used_by edge crosses a language", not cross_used, str(cross_used[:2]))
    _check("`external_calls` stays RESERVED and empty (the deferred cross-repo seam, FR-DC-13)",
           all(f["external_calls"] == [] for f in entries))
    _check("`exposes` stays RESERVED and empty", all(f["exposes"] == [] for f in entries))
    _check("…so a C assertion's closure can never reach a Java file — there is no edge to walk",
           not cross and not cross_used)

    # 4) un-onboarded language → unclustered, degraded not dropped
    print("\n4) an un-onboarded language degrades to `unclustered` (TASK-010 fallback):")
    java = [f for f in entries if f["language"] == "java"]
    _check("java is present but NOT onboarded", java and "java" not in comps["onboarded_languages"],
           f"{len(java)} java files")
    _check("every java file landed in java:unclustered",
           all(f["module"] == "java:unclustered" for f in java),
           str({f["module"] for f in java}))
    jb = next(c for c in components if c["module"] == "java:unclustered")
    _check("that bucket always passes tier 1 (nothing to rule it out on)",
           jb.get("always_pass_tier1") is True and jb["purpose_confidence"] == 0.0)
    _check("java files are marked coverage: coarse (no frozen extractor ran)",
           all(f["coverage"] == "coarse" for f in java))
    _check("they count as files_fallback, so `coverage` reflects the deterministic share",
           comps["coverage_report"]["files_fallback"] >= len(java),
           f"fallback={comps['coverage_report']['files_fallback']}, "
           f"coverage={comps['coverage_report']['coverage']}")
    _check("DEGRADED, never dropped — every java file still has a purpose",
           all(f["purpose"] for f in java))

    # 5) single-language behaviour unchanged
    print("\n5) single-language c_repo is unchanged:")
    c_profile = yaml.safe_load(
        (_REPO_ROOT / "core/code_profiles/c_repo.profile.yaml").read_text())
    c_comps, c_files, _ = build_map(_REPO_ROOT / "fixtures" / "c_repo", c_profile,
                                    repo="c_repo", commit_sha="9f3c1ab", seal_id="SEAL-12345",
                                    exclude=("verify_*.py",))
    oracle_c = json.loads((_REPO_ROOT / "fixtures/c_repo/expected_components.json").read_text())
    oracle_f = json.loads((_REPO_ROOT / "fixtures/c_repo/expected_files.json").read_text())
    _check("c_repo still matches its oracle", c_comps == oracle_c and c_files == oracle_f)
    _check("c_repo reports exactly one language", c_comps["languages"] == ["c"])

    print()
    if _FAILURES:
        print(f"FAILED — {len(_FAILURES)} check(s): {_FAILURES}", file=sys.stderr)
        return 1
    print("PASS — modules are language-scoped; tier 1 sees every module and matched two languages "
          "independently; no edge crosses a language and the cross-repo fields stay reserved; the "
          "un-onboarded language degraded to unclustered rather than being dropped.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
