#!/usr/bin/env python3
"""verify_tier_walk.py — TASK-118 proof: Arm 1's three-tier walk over the c_repo map.

The closure properties are what §16 completeness rests on, and each failure mode here is silent:
a one-directional walk misses half the ripple and returns a plausible list; a walk that stops at a
hop budget cannot tell "done" from "out of budget"; a walk that ignores the map's own
`unresolved_patterns` stops dead at a boundary that is not real.

  1. **Multi-hop closure reaches the oracle fixed point.**
  2. **Both directions** — files reachable only through `used_by` are reached.
  3. **A single-hop control does not over-report** — the walk does not leak into the global graph.
  4. **Source extends the map** — a recovered edge reaches files the map alone cannot.
  5. **Tier 1 can only over-include** — low confidence widens, `unclustered` always searched.
  6. **A no-code assertion escalates** rather than emitting a build story.
  7. **Implicit current-state assumptions** surface as findings.
  8. **The ripple is reviewable** — every reached file records why.

Run: python3 fixtures/code_impact/verify_tier_walk.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_REPO_ROOT = _HERE.parents[1]
sys.path.insert(0, str(_REPO_ROOT / "core" / "scripts"))

import enrichment as E  # noqa: E402
import tier_walk as T  # noqa: E402

_FAILURES: list[str] = []


def _check(label: str, ok: bool, detail: str = "") -> None:
    print(f"  [{'PASS' if ok else 'FAIL'}] {label}" + (f" — {detail}" if detail else ""))
    if not ok:
        _FAILURES.append(label)


def _directed_reach(files, seeds):
    """Follow `depends_on` FORWARD only — the one-directional control."""
    by_identity = {}
    for f in files:
        by_identity.setdefault(T._identity(f["path"]), []).append(f["path"])
    by_path = {f["path"]: f for f in files}
    seen, stack = set(seeds), list(seeds)
    while stack:
        cur = stack.pop()
        for d in by_path.get(cur, {}).get("depends_on", []):
            for t in by_identity.get(d, ()):
                if t not in seen:
                    seen.add(t)
                    stack.append(t)
    return seen


def main() -> int:
    files = json.loads((_REPO_ROOT / "fixtures/c_repo/expected_files.json").read_text())["files"]
    comps = json.loads(
        (_REPO_ROOT / "fixtures/c_repo/expected_components.json").read_text())["components"]
    oracle = json.loads((_HERE / "expected_closure.json").read_text())

    print("verify_tier_walk — Arm 1 over the c_repo map\n")

    # 1 & 2) multi-hop closure, both directions, fixed point
    print("1) multi-hop closure — the scope_ripple chain:")
    mh = oracle["multi_hop"]
    r = T.closure(files, mh["seeds"])
    _check("reaches the oracle set exactly", set(r["reached"]) == set(mh["expected_reached"]),
           f"{len(r['reached'])} files in {r['hops']} hops")
    _check("it is a FIXED POINT — one more expansion adds nothing",
           T.is_fixed_point(files, r["reached"]),
           "a hop budget could not tell 'done' from 'out of budget'")
    _check("closure is genuinely multi-hop (not one big fan-out)", r["hops"] >= 3,
           f"{r['hops']} hops, by_hop sizes {[len(v) for v in r['by_hop'].values()]}")

    print("\n2) both directions — reverse edges carry real ripple:")
    for p in mh["reached_only_by_reverse_edge"]:
        _check(f"{Path(p).name} reached (it appears only in a `used_by`)", p in r["reached"])
    # The honest control is a DIRECTED walk. Stripping `used_by` from the entries proves
    # nothing, because merge_edges derives it from the other files' depends_on — the graph is
    # already symmetric in the data. What has to be shown is that following edges one way only
    # loses reach.
    directed = _directed_reach(files, mh["seeds"])
    lost = set(r["reached"]) - directed
    _check("a one-directional (depends_on-only) walk misses files — and misses them silently",
           lost, f"{len(directed)} vs {len(r['reached'])} — {len(lost)} files lost, "
                 f"e.g. {sorted(lost)[:2]}")
    _check("the lost files include ones reachable ONLY by a reverse edge",
           set(mh["reached_only_by_reverse_edge"]) & lost,
           str(sorted(set(mh["reached_only_by_reverse_edge"]) & lost)))

    # 3) the over-reporting control
    print("\n3) single-hop control — no over-reporting:")
    sh = oracle["single_hop_control"]
    rc = T.closure(files, sh["seeds"])
    _check("reaches exactly its 2-file component", set(rc["reached"]) == set(sh["expected_reached"]),
           str(sorted(rc["reached"])))
    _check("does NOT leak into the global graph", len(rc["reached"]) < len(r["reached"]) // 4,
           "a leaking walk would return the repo and look thorough")
    _check("its hop count is 1", rc["hops"] == sh["expected_hops"])

    # 4) source extends the map
    print("\n4) source extends the map (tier 3a → tier 3b):")
    se = oracle["source_extends_map"]
    r_map = T.closure(files, se["seeds"])
    edge = se["recovered_edge"]
    r_ext = T.closure(files, se["seeds"], extra_edges={edge["from"]: [edge["to"]]})
    _check("the map alone stops at the disconnected boundary",
           set(r_map["reached"]) == set(se["expected_reached_map_only"]),
           f"{len(r_map['reached'])} files")
    _check("the recovered edge reaches strictly more",
           set(r_ext["reached"]) > set(r_map["reached"]),
           f"{len(r_map['reached'])} → {len(r_ext['reached'])}")
    _check("and reaches exactly the files only it can",
           set(r_ext["reached"]) - set(r_map["reached"])
           == set(se["only_reachable_via_recovered_edge"]),
           str(se["only_reachable_via_recovered_edge"]))
    _check("the extended walk is itself a fixed point",
           T.is_fixed_point(files, r_ext["reached"], {edge["from"]: [edge["to"]]}))

    # 5) tier 1 over-includes, never under-includes
    print("\n5) tier 1 — low confidence widens, unclustered always searched:")
    never = lambda q, c: False          # a matcher that matches NOTHING  # noqa: E731
    t1 = T.tier1("anything", comps, never, low_confidence_threshold=0.8)
    low = [c["module"] for c in comps if c.get("purpose_confidence", 1) < 0.8]
    _check("a module nothing matched is still included when confidence is low",
           set(t1.widened) == set(low) - set(t1.always_passed), f"widened {t1.widened}")
    _check("tier 1 considered EVERY module", t1.considered == len(comps), f"{len(comps)} modules")
    # c_repo places every file, so its `unclustered` bucket is empty — a vacuous check here.
    # mixed_repo genuinely has one (the un-onboarded Java partition), so the rule is tested
    # where it actually bites.
    mixed = json.loads((_REPO_ROOT / "fixtures/mixed_repo/expected_components.json").read_text())
    mixed_unclustered = [c["module"] for c in mixed["components"]
                         if c.get("always_pass_tier1")]
    t1m = T.tier1("anything", mixed["components"], never)
    _check("unclustered buckets are searched even by a matcher that matches NOTHING",
           bool(mixed_unclustered) and set(mixed_unclustered) <= set(t1m.matched),
           str(mixed_unclustered))
    always = lambda q, c: True          # noqa: E731
    _check("a matcher that matches everything cannot exceed the module set",
           len(T.tier1("x", comps, always).matched) == len(comps))
    # tier 2 stays inside tier 1's scope — the economy tier 1 bought
    scope = max({c["module"] for c in comps},
                key=lambda m: sum(1 for f in files if f.get("module") == m))
    t2 = T.tier2("x", files, [scope], always)
    _check("tier 2 searches ONLY within matched modules",
           bool(t2) and all(next(f for f in files if f["path"] == p)["module"] == scope
                            for p in t2),
           f"{len(t2)} files in {scope}")
    _check("…and a module tier 1 did NOT match is invisible to tier 2",
           not T.tier2("x", files, [], always))

    # 6) a no-code assertion escalates
    print("\n6) a no-code assertion escalates, never auto-builds:")
    gap = E.make_finding("F-101", arm="impact", kind="no_code_found",
                         requirement_ref="R11", assertion_ref="R11.5",
                         reasoning="no MDES coverage report emitter anywhere in the map or source")
    _check("it escalates", gap.action == "escalated" and gap.route == E.ESCALATE)
    _check("it is undispositioned — a human owes an answer", gap.status == "undispositioned")
    _check("it did NOT become a §16 build entry on its own", gap.section_target == "§16"
           and gap.action != "auto_applied",
           "it is a §16 GAP awaiting disposition, not an impact")
    dup = E.make_finding("F-102", arm="impact", kind="versioned_duplicate",
                         reasoning="iso8583.c and iso8583_v2.c both build field 48")
    _check("a versioned duplicate escalates rather than being picked silently",
           dup.action == "escalated")

    # 7) implicit current-state assumptions
    print("\n7) implicit current-state assumptions surface (D-A8):")
    implicit = E.make_finding(
        "F-103", arm="impact", kind="contradiction", claim_provenance="unsourced",
        requirement_ref="R2", assertion_ref="R2.1", section_ref="§16",
        verdict="contradicted",
        evidence=[{"path": "src/messaging/iso8583.c", "symbol": "build_iso8583"}],
        reasoning="R2.1 assumes field 48 has room for a new subelement; the builder writes into "
                  "a fixed ISO_MAX_FIELDS buffer, so this is a structural change, not an addition")
    _check("an unstated assumption becomes a finding with evidence",
           implicit.evidence and implicit.reasoning)
    _check("…and it routes as a gap closure, since nobody wrote the assumption down",
           implicit.route == E.AUTO_FILL,
           "invisible in v1: no reviewer could have checked it")

    # 8) reviewable ripple
    print("\n8) the ripple is reviewable:")
    _check("every reached file records WHY it was reached",
           all(p in r["via"] for p in r["reached"]))
    _check("seeds are labelled as seeds",
           all("seed" in r["via"][s] for s in mh["seeds"]))
    sample = next(p for p in r["reached"] if p not in mh["seeds"])
    _check("a rippled file names the file and hop it came from",
           "reached from" in r["via"][sample] and "hop" in r["via"][sample],
           f"{Path(sample).name}: {r['via'][sample]}")

    print()
    if _FAILURES:
        print(f"FAILED — {len(_FAILURES)} check(s): {_FAILURES}", file=sys.stderr)
        return 1
    print("PASS — closure reaches its fixed point in both directions; the single-hop control does "
          "not over-report; a source-recovered edge reaches what the map cannot; tier 1 only ever "
          "over-includes; no-code gaps and versioned duplicates escalate; the ripple is reviewable.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
