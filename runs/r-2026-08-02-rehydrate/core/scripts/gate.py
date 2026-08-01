#!/usr/bin/env python3
"""The 4-branch onboarding/cache gate — the deterministic decision (§5.3 as amended, FR-DC-15).

This module is the part of the gate that MUST be provably model-free: the *branch selection* and
the *coverage-floor predicate*. Both are pure functions of deterministic signals — language, the
frozen ``extractor_sha``, the repo's frozen ``profile_sha``, its ``commit_sha``, and the cached
map's recorded build keys. **No model participates**, by construction: there is no model call
anywhere in this file. That is what makes "the map is reproducible from (commit_sha, profile_sha)"
a checkable statement rather than an aspiration.

The `code_map_build` skill orchestrates around these: it gathers the signals, calls
``select_branch`` to decide, then performs the branch's *action*. The actions involve the frozen
extractor (deterministic) and model purpose work; the **decision** never does.

Branch map (D-A21's build-frequency table):

  1 ONBOARD      — no frozen extractor for the language, OR no signal profile for this repo.
                   Human-gated; there is no frozen rule set to build against, and inventing one
                   at runtime is what the binding rule forbids.
  2 REUSE        — ``(commit_sha, profile_sha)`` both match (and the extractor sha) → **no work**.
  3 INCREMENTAL  — commit moved, profile unchanged → structure + clustering recomputed globally
                   (cheap, deterministic); model purposes only for changed file hashes; module
                   purposes re-synthesised for **affected** modules (see ``affected_modules`` —
                   wider than "modules containing changed files").
  4 REBUILD_FULL — ``profile_sha`` changed (or the extractor was re-frozen, or first build) →
                   **everything**. The derivation rules themselves moved.

**Branch 4 is the one ADR-008 added**, and the asymmetry it encodes is the point: *a profile
change invalidates wholesale; a commit change invalidates selectively.* If re-onboarding moves the
hub threshold from 500 to 200, every module boundary can shift — so nothing in the old map is
trustworthy, not the clustering, not the module purposes, not even which files were hubs.

``retag`` is **gone**: it existed for a vocabulary-only amendment, and there is no vocabulary
(D-A22). Nothing tags, so nothing can be re-tagged.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping, Optional, Sequence

# Branch labels (stable strings — the skill + telemetry key off these).
# Recast to the FOUR branches at TASK-115: `retag` died with the vocabulary (nothing tags, so
# nothing can be re-tagged), and `profile_sha` joined the cache key.
ONBOARD = "onboard"              # 1 — no frozen extractor, or no signal profile for this repo
REUSE = "reuse"                  # 2 — (commit_sha, profile_sha) both match: NO WORK
INCREMENTAL = "incremental"      # 3 — commit moved, profile unchanged: selective invalidation
REBUILD_FULL = "rebuild_full"    # 4 — profile_sha changed (or extractor re-frozen): wholesale


@dataclass(frozen=True)
class GateDecision:
    branch: str
    reason: str
    rebuilds: bool = field(default=False)   # True iff the frozen extractor must run
    repurpose_all: bool = field(default=False)  # True iff EVERY file's purpose is invalidated


def select_branch(
    *,
    language: str,
    extractor_sha: Optional[str],
    profile_sha: Optional[str],
    commit_sha: str,
    repo_cache: Optional[Mapping[str, str]],
) -> GateDecision:
    """Decide onboard / reuse / incremental / full-rebuild from deterministic signals only (§5.3).

    **No model participates in the branch decision.** Language detection, sha comparison, and cache
    lookup are all deterministic, which is what makes "the map is reproducible from
    (commit_sha, profile_sha)" a checkable statement rather than an aspiration.

    The asymmetry between branches 3 and 4 is the point (D-A21): **a profile change invalidates
    wholesale; a commit change invalidates selectively.** If re-onboarding moves the hub threshold
    from 500 to 200, *every* module boundary can shift, so nothing in the old map is trustworthy —
    not the clustering, not the module purposes, not even which files are hubs. A commit that
    touches four files invalidates four files' purposes plus the modules those files affect.

    Args:
      language:      the dominant language (``detect_language``).
      extractor_sha: the frozen extractor's sha for ``language``, or ``None`` if unregistered.
      profile_sha:   the repo's frozen signal-profile sha, or ``None`` if never onboarded.
      commit_sha:    the repo's current commit.
      repo_cache:    the ``cache/code_maps/index.yaml`` record for this repo, or ``None``.

    Returns a :class:`GateDecision`. Pure — no I/O, no model, no git; same inputs → same branch.
    """
    # ── BRANCH 1 — nothing frozen to build against → ONBOARD (human-gated).
    #    Either the language has no extractor, or this repo has never been through the profile
    #    gate. Both mean there is no frozen rule set, and inventing one at runtime is exactly what
    #    the binding rule forbids.
    if extractor_sha is None:
        return GateDecision(ONBOARD, f"no frozen extractor for language {language!r}")
    if profile_sha is None:
        return GateDecision(ONBOARD, "no signal profile for this repo — run the onboarding gate")

    if repo_cache is None:
        return GateDecision(REBUILD_FULL, "no cached map (first build); full build over all files",
                            rebuilds=True, repurpose_all=True)

    same_commit = repo_cache.get("commit_sha") == commit_sha
    same_profile = repo_cache.get("profile_sha") == profile_sha
    same_extractor = repo_cache.get("built_with_extractor_sha") == extractor_sha

    # ── BRANCH 2 — both keys match → REUSE. Literally no work.
    if same_commit and same_profile and same_extractor:
        return GateDecision(REUSE, "cache hit: commit_sha + profile_sha + extractor_sha all match")

    # ── BRANCH 4 — the derivation RULES changed → everything is suspect.
    if not same_profile:
        return GateDecision(REBUILD_FULL,
                            "profile_sha changed — the derivation rules themselves moved, so every "
                            "module boundary may have moved with them",
                            rebuilds=True, repurpose_all=True)
    if not same_extractor:
        return GateDecision(REBUILD_FULL, "extractor re-frozen (sha changed); full build",
                            rebuilds=True, repurpose_all=True)

    # ── BRANCH 3 — commit moved, rules unchanged → selective.
    return GateDecision(INCREMENTAL,
                        "commit moved, profile unchanged: recompute structure + clustering "
                        "(cheap, deterministic), re-purpose only changed file hashes",
                        rebuilds=True)


def affected_modules(old_files: Sequence[Mapping], new_files: Sequence[Mapping],
                     changed_paths: Sequence[str]) -> list[str]:
    """Modules whose purpose must be re-synthesised after an incremental build.

    **Wider than "modules containing changed files", and that is the wrinkle** (D-A21). Clustering
    is global: a changed file's new includes can shift module membership *beyond that file*, so a
    module can need re-synthesis because a file left it, or joined it, even though nothing in that
    module was edited. A purely local rule would leave stale module purposes describing a
    membership that no longer exists.

    So: modules containing a changed file, PLUS any module whose membership differs at all between
    the two builds. Bounded, but not local.
    """
    old_by_path = {f["path"]: f.get("module") for f in old_files}
    new_by_path = {f["path"]: f.get("module") for f in new_files}
    affected: set[str] = set()
    for p in changed_paths:
        for src in (old_by_path, new_by_path):
            if src.get(p):
                affected.add(src[p])
    for p in set(old_by_path) | set(new_by_path):
        if old_by_path.get(p) != new_by_path.get(p):
            affected.update(m for m in (old_by_path.get(p), new_by_path.get(p)) if m)
    return sorted(affected)


def check_coverage(coverage_report: Mapping[str, object], floor: float) -> Optional[dict]:
    """The extractor coverage-floor predicate (§5.4, FR-DC-16) — deterministic.

    Returns ``None`` if ``coverage >= floor`` (the map is adequate), or a dict of the
    ``reonboard_flag`` fields if it is below floor (caller routes it to the ledger via
    ``decisions.reonboard_flag``). It NEVER modifies the extractor — a frozen tool
    raises its hand; it does not rewrite itself.
    """
    coverage = float(coverage_report.get("coverage", 0.0))
    if coverage >= floor:
        return None
    return {
        "coverage": coverage,
        "floor": floor,
        "patterns": list(coverage_report.get("unresolved_patterns", [])),
    }


# ──────────────────────────────────────────────────────────────────────────────
# Demonstration (TASK-013 fixture/proof) — runnable, deterministic, model-free.
# Shows: no-op → REUSE; content change → REBUILD_CHANGED; new extractor → REBUILD_FULL;
# vocab bump → RETAG; un-onboarded language → ONBOARD; and a coverage-floor bust →
# reonboard_flag fields. Run: python3 core/scripts/gate.py
# ──────────────────────────────────────────────────────────────────────────────
def _demo() -> None:
    cached = {"commit_sha": "e94c70d", "profile_sha": "52dd3db",
              "built_with_extractor_sha": "ed703ff"}
    base = dict(language="c", extractor_sha="ed703ff", profile_sha="52dd3db",
                commit_sha="e94c70d", repo_cache=cached)
    scenarios = [
        ("2 · nothing moved", base),
        ("3 · commit moved", {**base, "commit_sha": "ffff999"}),
        ("4 · profile re-frozen", {**base, "profile_sha": "NEWprof"}),
        ("4 · extractor re-frozen", {**base, "extractor_sha": "NEWextr"}),
        ("4 · first build (no cache)", {**base, "repo_cache": None}),
        ("1 · repo never onboarded", {**base, "profile_sha": None}),
        ("1 · un-onboarded language", {**base, "language": "java", "extractor_sha": None}),
    ]
    print("select_branch (deterministic, model-free):")
    for name, kw in scenarios:
        d = select_branch(**kw)
        print(f"  {name:28s} → {d.branch:14s} rebuilds={str(d.rebuilds):5s} "
              f"repurpose_all={str(d.repurpose_all):5s}")
        print(f"  {'':28s}   {d.reason}")

    # The asymmetry, stated as an assertion rather than a comment.
    assert select_branch(**base).branch == REUSE
    assert not select_branch(**base).rebuilds
    inc = select_branch(**{**base, "commit_sha": "ffff999"})
    full = select_branch(**{**base, "profile_sha": "NEWprof"})
    assert inc.branch == INCREMENTAL and inc.rebuilds and not inc.repurpose_all
    assert full.branch == REBUILD_FULL and full.repurpose_all
    print("\nasymmetry: a commit change invalidates SELECTIVELY (repurpose_all=False); "
          "a profile change invalidates WHOLESALE (repurpose_all=True)")

    print("\naffected_modules — wider than 'modules containing changed files' (D-A21):")
    old = [{"path": "a.c", "module": "m1"}, {"path": "b.c", "module": "m1"},
           {"path": "c.c", "module": "m2"}]
    new = [{"path": "a.c", "module": "m1"}, {"path": "b.c", "module": "m2"},
           {"path": "c.c", "module": "m2"}]
    aff = affected_modules(old, new, ["b.c"])
    print(f"  changed b.c; its includes moved it m1 → m2  ⇒  affected {aff}")
    assert aff == ["m1", "m2"], aff
    print("  m1 is affected although NOTHING in it changed — a file LEFT it, so its synthesised "
          "purpose now describes a membership that no longer exists")

    print("\ncheck_coverage (REONBOARD_FLAG predicate):")
    ok = check_coverage({"coverage": 0.82, "unresolved_patterns": []}, 0.80)
    bust = check_coverage({"coverage": 0.67,
                           "unresolved_patterns": ["#ifdef-gated reg in feature_flags.c"]}, 0.80)
    print(f"  coverage 0.82 vs floor 0.80 → {'OK (no flag)' if ok is None else ok}")
    print(f"  coverage 0.67 vs floor 0.80 → REONBOARD_FLAG {bust}")

    print("\nPASS — four branches, decided from deterministic signals only; branch 2 does no "
          "work; a profile change invalidates wholesale and a commit change selectively.")


if __name__ == "__main__":
    _demo()
