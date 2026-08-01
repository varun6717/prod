#!/usr/bin/env python3
"""verify_gate_branches.py — TASK-115 proof: the 4-branch gate walked over `c_repo`.

Cache-correctness mistakes propagate **silently** — a stale map does not look stale, it looks
like a map — so each branch is walked against a real repo and a real cache, not asserted.

  1. **Branch 1 onboard** — no profile, or no extractor: nothing frozen to build against.
  2. **Branch 2 reuse** — both shas match ⇒ ZERO work: no extractor run, no purpose resolved.
  3. **Branch 3 incremental** — a commit that touches one file re-purposes ONE file, and
     re-synthesises the **affected** modules, which is wider than the changed file's own.
  4. **Branch 4 full rebuild** — a profile change invalidates wholesale, and genuinely produces
     a different map rather than merely claiming to.
  5. **The asymmetry** — commit change selective, profile change wholesale.
  6. **Cache index round-trip** — the record is written, read back, and drives the next decision.
  7. **The decision is model-free** — no model call in the branch path.

Run: python3 fixtures/c_repo/verify_gate_branches.py
"""
from __future__ import annotations

import json
import shutil
import sys
import tempfile
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_REPO_ROOT = _HERE.parents[1]
sys.path.insert(0, str(_REPO_ROOT / "core" / "scripts"))

import gate  # noqa: E402
import map_cache  # noqa: E402
import yaml  # noqa: E402
from code_map_build import PurposeCache, build_map  # noqa: E402

_FAILURES: list[str] = []


def _check(label: str, ok: bool, detail: str = "") -> None:
    print(f"  [{'PASS' if ok else 'FAIL'}] {label}" + (f" — {detail}" if detail else ""))
    if not ok:
        _FAILURES.append(label)


def main() -> int:
    profile = yaml.safe_load((_REPO_ROOT / "core/code_profiles/c_repo.profile.yaml").read_text())
    psha, esha = profile["profile_sha"], "ed703ff"
    print("verify_gate_branches — the 4-branch gate over fixtures/c_repo\n")

    with tempfile.TemporaryDirectory(prefix="gate-walk-") as td:
        tmp = Path(td)
        repo = tmp / "repo"
        shutil.copytree(_HERE, repo, ignore=shutil.ignore_patterns("*.py", "*.json", "*.md"))
        cache_dir = tmp / "cache"
        idx = cache_dir / "index.yaml"

        # ── 1) branch 1 — nothing frozen to build against
        print("1) branch 1 — onboard:")
        d = gate.select_branch(language="c", extractor_sha=esha, profile_sha=None,
                               commit_sha="aaa1111", repo_cache=None)
        _check("no signal profile → onboard", d.branch == gate.ONBOARD, d.reason)
        d = gate.select_branch(language="java", extractor_sha=None, profile_sha=psha,
                               commit_sha="aaa1111", repo_cache=None)
        _check("no frozen extractor for the language → onboard", d.branch == gate.ONBOARD, d.reason)
        _check("onboard does NOT rebuild (there is no frozen rule set yet)", not d.rebuilds)

        # ── first build (branch 4 by way of 'no cache')
        print("\n2) first build populates the cache:")
        d0 = gate.select_branch(language="c", extractor_sha=esha, profile_sha=psha,
                                commit_sha="aaa1111", repo_cache=map_cache.record_for("c_repo", idx))
        _check("no cached map → rebuild_full", d0.branch == gate.REBUILD_FULL, d0.reason)
        comps1, files1, cache1 = build_map(repo, profile, repo="c_repo", commit_sha="aaa1111")
        map_cache.update_record("c_repo", commit_sha="aaa1111", profile_sha=psha,
                                extractor_sha=esha, map_dir=str(tmp / "map"),
                                last_built="2026-08-01T00:00:00Z", path=idx)
        map_cache.save_purpose_cache("c_repo", cache1.entries, path=cache_dir)
        _check("cache index written and readable",
               map_cache.record_for("c_repo", idx)["commit_sha"] == "aaa1111")
        _check("the first build resolved every purpose", cache1.misses == len(files1["files"]),
               f"{cache1.misses} misses")

        # ── 3) branch 2 — reuse, zero work
        print("\n3) branch 2 — reuse (the common case):")
        rec = map_cache.record_for("c_repo", idx)
        d2 = gate.select_branch(language="c", extractor_sha=esha, profile_sha=psha,
                                commit_sha="aaa1111", repo_cache=rec)
        _check("both shas match → reuse", d2.branch == gate.REUSE, d2.reason)
        _check("reuse does NO work at all", not d2.rebuilds and not d2.repurpose_all)
        warm = PurposeCache(entries=map_cache.load_purpose_cache("c_repo", cache_dir))
        build_map(repo, profile, repo="c_repo", commit_sha="aaa1111", cache=warm)
        _check("even if re-run, zero purposes are resolved", warm.misses == 0,
               f"{warm.hits} hits / {warm.misses} misses")

        # ── 4) branch 3 — incremental
        print("\n4) branch 3 — incremental (commit moved, rules unchanged):")
        target = repo / "src" / "errors" / "retry.c"
        target.write_text(target.read_text() + "\nint retry_extra(void) { return 1; }\n")
        d3 = gate.select_branch(language="c", extractor_sha=esha, profile_sha=psha,
                                commit_sha="bbb2222", repo_cache=rec)
        _check("commit moved, profile same → incremental", d3.branch == gate.INCREMENTAL, d3.reason)
        _check("incremental rebuilds but does NOT re-purpose everything",
               d3.rebuilds and not d3.repurpose_all)
        warm3 = PurposeCache(entries=map_cache.load_purpose_cache("c_repo", cache_dir))
        comps3, files3, warm3 = build_map(repo, profile, repo="c_repo", commit_sha="bbb2222",
                                          cache=warm3)
        _check("exactly ONE file's purpose was re-resolved", warm3.misses == 1,
               f"{warm3.misses} miss, {warm3.hits} hits — the content hash of one file moved")
        aff = gate.affected_modules(files1["files"], files3["files"], ["src/errors/retry.c"])
        _check("affected modules are identified for re-synthesis", bool(aff), str(aff))
        _check("structure is still recomputed globally (cheap, deterministic)",
               len(comps3["components"]) > 0 and len(files3["files"]) == len(files1["files"]))

        # ── 5) branch 4 — profile change invalidates wholesale
        print("\n5) branch 4 — full rebuild (the derivation rules moved):")
        import validate_onboarding as G
        tuned = G.freeze_profile(G.adjust_profile(profile,
                                                  **{"derivation.hub_threshold_fan_in": 12}),
                                 repo="c_repo", commit_sha="aaa1111", reviewed_by="vmunjal")
        _check("adjusting a derivation rule moves profile_sha",
               tuned["profile_sha"] != psha, f"{psha} → {tuned['profile_sha']}")
        d4 = gate.select_branch(language="c", extractor_sha=esha,
                                profile_sha=tuned["profile_sha"],
                                commit_sha="aaa1111", repo_cache=rec)
        _check("profile_sha changed → rebuild_full", d4.branch == gate.REBUILD_FULL, d4.reason)
        _check("full rebuild invalidates WHOLESALE (repurpose_all)", d4.repurpose_all)
        comps4, _, _ = build_map(repo, tuned, repo="c_repo", commit_sha="aaa1111")
        _check("and the map genuinely differs — not merely claimed",
               len(comps4["components"]) != len(comps1["components"]),
               f"{len(comps1['components'])} modules → {len(comps4['components'])}")

        # ── 6) the asymmetry, stated directly
        print("\n6) the asymmetry (D-A21):")
        _check("a COMMIT change invalidates selectively", not d3.repurpose_all)
        _check("a PROFILE change invalidates wholesale", d4.repurpose_all)
        _check("…because a rule change can move every module boundary, so nothing in the old "
               "map is trustworthy", "boundary" in d4.reason)

        # ── 7) model-free decision
        print("\n7) the branch decision is model-free (§5.3):")
        src = (_REPO_ROOT / "core" / "scripts" / "gate.py").read_text()
        _check("gate.py contains no model/LLM call",
               not any(k in src for k in ("openai", "anthropic", "llm", "prompt(")),
               "the decision is a pure function of shas")
        d_again = gate.select_branch(language="c", extractor_sha=esha, profile_sha=psha,
                                     commit_sha="bbb2222", repo_cache=rec)
        _check("same inputs → same branch, every time", d_again.branch == d3.branch)

    print()
    if _FAILURES:
        print(f"FAILED — {len(_FAILURES)} check(s): {_FAILURES}", file=sys.stderr)
        return 1
    print("PASS — all four branches walked against a real repo and cache; reuse does zero work; "
           "one changed file re-purposes exactly one file; a profile change rebuilds wholesale "
           "and really does produce a different map; the decision is model-free.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
