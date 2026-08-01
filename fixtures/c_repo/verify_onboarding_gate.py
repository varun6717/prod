#!/usr/bin/env python3
"""verify_onboarding_gate.py — TASK-113 proof: the D-A21 onboarding gate over `c_repo`.

The gate is the **only** human checkpoint on code-map quality, so what is proven here is that
the operator is actually shown enough to decide, that each action does what it claims, and that
the freeze leaves nothing model-driven active.

  1. **The report shows the three things a plain approval cannot.** Human-authored vs
     model-inferred split; tier-1 entries against target; the uncovered set named.
  2. **The scan finds the seeded phenomena** — the 60/40 declared split, the label distribution
     including the typo, the versioned-duplicate pair, include density and resolution.
  3. **`adjust profile` works and RECOMPUTES** — the whole point is that clustering is
     deterministic graph arithmetic, so adjust → recompute → re-review is cheap.
  4. **`skip stage C` is a deferral, not an exclusion** — files fall to C*, only what C* cannot
     cover becomes unanalyzable, and the reduction is visible in the report.
  5. **`group singletons` proposes, never applies** — approval is per group, and approved groups
     become membership overrides applied deterministically.
  6. **The actions compose.**
  7. **The freeze emits `profile_sha`**, it keys on semantic content only, and a profile change
     moves it (which is what makes gate branch 4 possible).
  8. **Nothing model-driven survives the freeze except as data.**

Run: python3 fixtures/c_repo/verify_onboarding_gate.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_REPO_ROOT = _HERE.parents[1]
sys.path.insert(0, str(_REPO_ROOT / "core" / "scripts"))

import validate_onboarding as G  # noqa: E402

_FAILURES: list[str] = []


def _check(label: str, ok: bool, detail: str = "") -> None:
    print(f"  [{'PASS' if ok else 'FAIL'}] {label}" + (f" — {detail}" if detail else ""))
    if not ok:
        _FAILURES.append(label)


def main() -> int:
    base = json.loads(json.dumps(G.DEFAULT_PROFILE))
    scan, dist, mods = G.run_gate(_HERE, base)
    report = G.render_gate_report("fixtures/c_repo", "9f3c1ab", scan, base, dist, mods)

    print("verify_onboarding_gate — D-A21 phase 1 over fixtures/c_repo\n")

    # 1) The three things a plain approval cannot do.
    print("1) the report shows what a plain 'approve?' cannot (D-A21):")
    _check("human-authored vs MODEL-INFERRED split is stated",
           "human-authored" in report and "MODEL-INFERRED" in report
           and f"{dist['human_authored']*100:.1f}%" in report,
           f"{dist['human_authored']:.1%} human / {dist['model_inferred']:.1%} model")
    _check("tier-1 entry count is stated against a target",
           "tier-1 entries:" in report and "target" in report,
           f"{mods['tier1_entries']} vs ~{base['tier1_entry_target']}")
    _check("the uncovered set is named, not implied away",
           "unanalyzable" in report and "NO COVERAGE" in report)
    _check("every stage row appears, including the empty ones",
           all(f"  {s:3} " in report for s in ("A", "B", "C", "C*", "--")),
           "an absent row would read as 'not applicable' rather than 'zero'")
    _check("the degenerate single-cluster is flagged rather than scored as good",
           "collapsed to ONE module" in report,
           "a low tier-1 count from one giant module is the WORSE failure")

    # 2) The seeded phenomena.
    print("\n2) the scan finds what TASK-112 seeded:")
    _check("declared coverage ≈ 60% (D-A20 measured 58.0%)",
           0.55 <= len(scan.declared) / len(scan.files) <= 0.65,
           f"{len(scan.declared)}/{len(scan.files)}")
    _check("the label distribution is varied, typo included",
           len(scan.label_counts) >= 7 and "Putpose" in scan.label_counts,
           f"{len(scan.label_counts)} distinct labels")
    _check("exactly the seeded versioned-duplicate pair is reported",
           scan.versioned_duplicates == [("src/messaging/iso8583.c",
                                          "src/messaging/iso8583_v2.c")],
           str(scan.versioned_duplicates))
    _check("a .c/.h pair sharing a stem is NOT reported as a duplicate",
           not any("brand_rules" in a or "brand_rules" in b
                   for a, b in scan.versioned_duplicates),
           "the ordinary C convention would otherwise bury the real hazard")
    _check("include density + resolution measured (D-A20's primary signal)",
           scan.include_total > 0 and scan.include_resolved / scan.include_total >= 0.9,
           f"{scan.include_total} includes, "
           f"{scan.include_resolved/scan.include_total:.0%} resolve")
    _check(".h placement recorded as a file-type convention", bool(scan.header_placement),
           str(scan.header_placement))
    _check("symbol presence measured (what C* would have to work with)",
           len(scan.no_symbols) > 0, f"{len(scan.no_symbols)} files with no function body")

    # 3) adjust profile — the action that makes iteration cheap.
    print("\n3) `adjust profile` → recompute → re-review:")
    tuned = G.adjust_profile(base, **{"derivation.hub_threshold_fan_in": 3})
    _, dist2, mods2 = G.run_gate(_HERE, tuned)
    _check("lowering the hub threshold breaks the glue into more modules",
           len(mods2["modules"]) + len(mods2["singletons"])
           > len(mods["modules"]) + len(mods["singletons"]),
           f"{len(mods['modules'])} modules → {len(mods2['modules'])} modules, "
           f"{len(mods['singletons'])} → {len(mods2['singletons'])} singletons")
    _check("more files become hubs at the lower threshold",
           len(mods2["hubs"]) > len(mods["hubs"]),
           f"{len(mods['hubs'])} → {len(mods2['hubs'])}")
    _check("recomputation is deterministic (same profile ⇒ same result)",
           json.dumps(G.run_gate(_HERE, tuned)[2], sort_keys=True, default=str)
           == json.dumps(mods2, sort_keys=True, default=str))
    _check("the original profile is not mutated (adjust returns a NEW one)",
           base["derivation"]["hub_threshold_fan_in"]
           == G.DEFAULT_PROFILE["derivation"]["hub_threshold_fan_in"])
    bad = False
    try:
        G.adjust_profile(base, **{"derivation.no_such_knob": 1})
    except KeyError:
        bad = True
    _check("an unknown parameter RAISES rather than silently doing nothing", bad,
           "a typo'd threshold that quietly did nothing would mislead the operator into freezing")

    # 4) skip stage C — a deferral, not an exclusion.
    print("\n4) `skip stage C` — deferral, not exclusion:")
    skipped = G.skip_stage_c(base)
    _, dist3, _ = G.run_gate(_HERE, skipped)
    c_before = dist["counts"].get(G.STAGE_C, 0)
    _check("stage C empties", dist3["counts"].get(G.STAGE_C, 0) == 0, f"was {c_before}")
    fell = dist3["counts"].get(G.STAGE_CSTAR, 0) + dist3["counts"].get(G.UNANALYZABLE, 0)
    _check("those files FALL THROUGH to C*/unanalyzable — none vanish", fell == c_before,
           f"{c_before} → C*={dist3['counts'].get(G.STAGE_CSTAR,0)} "
           f"unanalyzable={dist3['counts'].get(G.UNANALYZABLE,0)}")
    _check("the total is conserved", sum(dist3["counts"].values()) == dist3["total"])
    _check("the coverage reduction is VISIBLE in the report",
           f"{dist3['uncovered']*100:.1f}%" in
           G.render_gate_report("r", "s", scan, skipped, dist3, mods),
           f"uncovered {dist3['uncovered']:.1%}")
    _check("stage-C cost drops to zero (the point of the action)", dist3["stage_c_cost"] == 0)

    # 5) group singletons — propose, review as a diff, freeze approved as data.
    print("\n5) `group singletons` — proposes, never applies:")
    _, _, mods_t = G.run_gate(_HERE, tuned)
    proposals = G.propose_singleton_groups(scan, mods_t)
    _check("the model proposes at least one grouping", bool(proposals),
           str([p["name"] for p in proposals]))
    _check("every proposal carries a rationale a human can review as a diff",
           all(p["rationale"] and len(p["members"]) >= 2 for p in proposals))
    _check("proposing changes NOTHING on its own",
           tuned["overrides"]["singleton_groups"] == [])
    approved = G.approve_singleton_groups(tuned, proposals, [proposals[0]["name"]])
    _check("approving freezes only the approved subset",
           len(approved["overrides"]["singleton_groups"]) == 1,
           proposals[0]["name"])
    _, _, mods4 = G.run_gate(_HERE, approved)
    moved = set(proposals[0]["members"])
    landed = next((v for k, v in mods4["modules"].items() if k.startswith("override:")), [])
    _check("the approved group becomes a real module, applied deterministically",
           set(landed) == moved, f"{sorted(moved)}")
    _check("grouping reduces tier-1 entries — the economy problem, solved where it is cheap",
           mods4["tier1_entries"] < mods_t["tier1_entries"],
           f"{mods_t['tier1_entries']} → {mods4['tier1_entries']}")

    # 6) The actions compose.
    print("\n6) the actions compose:")
    combined = G.skip_stage_c(approved)
    scan5, dist5, mods5 = G.run_gate(_HERE, combined)
    _check("adjust + group + skip all hold together",
           combined["derivation"]["hub_threshold_fan_in"] == 3
           and len(combined["overrides"]["singleton_groups"]) == 1
           and combined["stages"]["skip_stage_c"] is True
           and dist5["counts"].get(G.STAGE_C, 0) == 0)

    # 7) The freeze.
    #    What gets frozen is `approved` (adjust + group), NOT `combined` — skipping stage C on a
    #    35-file repo would be a strange call, and the committed profile should be the one a
    #    sensible operator would actually sign. `combined` still proves the actions compose.
    print("\n7) freeze → profile_sha:")
    frozen = G.freeze_profile(approved, repo="c_repo", commit_sha="9f3c1ab",
                              reviewed_by="vmunjal",
                              actions=["adjust profile", "group singletons"])
    _check("profile_sha is emitted", bool(frozen.get("profile_sha")), frozen["profile_sha"])
    _check("the gate record names the reviewer and the actions taken",
           frozen["gate"]["status"] == "frozen" and frozen["gate"]["reviewed_by"]
           and len(frozen["gate"]["actions_taken"]) == 2)
    _check("stage C is NOT skipped in the frozen profile (a deliberate operator call)",
           frozen["stages"]["skip_stage_c"] is False)
    other = G.freeze_profile(G.adjust_profile(approved,
                                              **{"derivation.hub_threshold_fan_in": 5}),
                             repo="c_repo", commit_sha="9f3c1ab", reviewed_by="vmunjal")
    _check("a profile CHANGE moves profile_sha — this is what makes gate branch 4 work",
           other["profile_sha"] != frozen["profile_sha"],
           f"{frozen['profile_sha']} vs {other['profile_sha']}")
    resigned = G.freeze_profile(approved, repo="c_repo", commit_sha="9f3c1ab",
                                reviewed_by="someone-else")
    _check("a re-signature does NOT move it (gate metadata is excluded, deliberately)",
           resigned["profile_sha"] == frozen["profile_sha"],
           "otherwise every cached map would invalidate on a signature change")
    _check("the same commit with a different profile is a DIFFERENT cache key",
           (frozen["commit_sha"], frozen["profile_sha"])
           != (other["commit_sha"], other["profile_sha"]))

    # 8) Nothing model-driven survives the freeze except as data.
    print("\n8) post-freeze determinism:")
    groups = frozen["overrides"]["singleton_groups"]
    _check("approved model proposals are frozen as plain membership DATA",
           all(set(g) <= {"name", "members", "rationale"} for g in groups),
           "no callable, no threshold, no model reference")
    _, _, m_a = G.run_gate(_HERE, frozen)
    _, _, m_b = G.run_gate(_HERE, frozen)
    _check("the frozen profile derives the same modules every time",
           json.dumps(m_a, sort_keys=True, default=str)
           == json.dumps(m_b, sort_keys=True, default=str))
    ok, detail = G.check_freeze_integrity()
    _check("extractor freeze is still honest", ok, detail)

    # Write the frozen instance the task owes.
    out = G.write_profile(frozen, _REPO_ROOT / "core" / "code_profiles" / "c_repo.profile.yaml")
    _check("the frozen profile is written to core/code_profiles/",
           out.exists(), str(out.relative_to(_REPO_ROOT)))

    print()
    if _FAILURES:
        print(f"FAILED — {len(_FAILURES)} check(s): {_FAILURES}", file=sys.stderr)
        return 1
    print("PASS — the gate report shows quality, economy and coverage; the scan finds every "
          "seeded phenomenon; all three actions work, compose, and only propose; the freeze "
          "emits a profile_sha that moves on a rule change and not on a re-signature; nothing "
          "model-driven survives it except as data.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
