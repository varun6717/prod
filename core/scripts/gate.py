#!/usr/bin/env python3
"""The 3-branch onboarding/cache gate — the deterministic decision (§5.3, FR-DC-15).

This module is the part of the gate that MUST be provably model-free: the *branch
selection* and the *coverage-floor predicate*. Both are pure functions of
deterministic signals — language, frozen ``extractor_sha``, ``vocab_sha``, the repo
``content_hash`` (= git commit_sha), and the cached map's recorded build keys. **No
model participates**, by construction: there is no model call anywhere in this file.

The `code_map_build` skill (§5.5) orchestrates around these: it gathers the signals
(``detect_language``/``extractor_for`` from ``core.extractors``, the repo commit, the
cache record from ``cache/code_maps/index.yaml`` — D-A22; TASK-115 recasts this gate
to the 4-branch `(commit_sha, profile_sha)` form), calls ``select_branch`` to decide,
then performs the branch's
*action* (reuse the cached map / run the frozen extractor over a file set / re-tag).
The actions involve the extractor (deterministic) and model enrichment (purpose/tags
only); the **decision** here never does. Keeping the decision a pure function is what
makes "no model in the branch decision" testable rather than merely asserted.

Branch map (mirrors the §5.3 pseudocode exactly):

  A  ONBOARD          — no frozen extractor for the language (→ human-gated onboarding;
                        model-only fallback meanwhile). Inert on the slice (C is frozen).
  B  REUSE            — content + extractor_sha + vocab_sha all match the cache → load it.
  C  RETAG            — content + extractor match but vocab_sha differs → re-tag only
                        (structure + purpose reused; only the tag pass re-runs).
  C  REBUILD_FULL     — no cache, or extractor re-blessed (sha changed) → full build.
  C  REBUILD_CHANGED  — content changed (same extractor) → rebuild changed files only
                        (``git_diff_names`` delta).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping, Optional, Sequence

# Branch labels (stable strings — the skill/telemetry key off these).
ONBOARD = "onboard"                  # A
REUSE = "reuse"                      # B
RETAG = "retag"                      # C — vocab-only amendment
REBUILD_FULL = "rebuild_full"        # C — new repo or re-blessed extractor
REBUILD_CHANGED = "rebuild_changed"  # C — content changed, same extractor


@dataclass(frozen=True)
class GateDecision:
    branch: str
    reason: str
    rebuilds: bool = field(default=False)   # True iff the frozen extractor must run


def select_branch(
    *,
    language: str,
    extractor_sha: Optional[str],
    vocab_sha: str,
    content_hash_new: str,
    repo_cache: Optional[Mapping[str, str]],
) -> GateDecision:
    """Decide onboard / reuse / retag / rebuild from deterministic signals only (§5.3).

    Args:
      language:          the dominant language (``detect_language``).
      extractor_sha:     the frozen extractor's sha for ``language``, or ``None`` if no
                         extractor is registered (→ Branch A). (``extractor_for`` is
                         None ⇒ pass ``None`` here.)
      vocab_sha:         the manifest's current vocabulary version.
      content_hash_new:  the repo's current commit_sha.
      repo_cache:        the ``cache/code_maps/index.yaml`` record for this repo (D-A22),
                         or ``None`` if the repo has never been built. Must carry
                         ``content_hash``, ``built_with_extractor_sha``,
                         ``built_with_vocab_sha`` when present.

    Returns a :class:`GateDecision`. Pure — no I/O, no model, no git; same inputs →
    same branch, every time.
    """
    # ── BRANCH A — no frozen extractor for the language → ONBOARD (human-gated).
    if extractor_sha is None:
        return GateDecision(ONBOARD, f"no frozen extractor for language {language!r}")

    if repo_cache is not None:
        same_content = repo_cache.get("content_hash") == content_hash_new
        same_extractor = repo_cache.get("built_with_extractor_sha") == extractor_sha
        same_vocab = repo_cache.get("built_with_vocab_sha") == vocab_sha
    else:
        same_content = same_extractor = same_vocab = False

    # ── BRANCH B — full cache hit → REUSE (no rebuild).
    if repo_cache is not None and same_content and same_extractor and same_vocab:
        return GateDecision(REUSE, "cache hit: content + extractor_sha + vocab_sha all match")

    # ── BRANCH C — rebuild / re-tag. Order mirrors §5.3 exactly.
    if repo_cache is not None and same_content and same_extractor:
        # content + extractor match but vocab_sha differs → vocab-only change.
        return GateDecision(RETAG, "vocab_sha changed; reuse structure+purpose, re-tag only")
    if repo_cache is None or not same_extractor:
        why = "no cached map (first build)" if repo_cache is None else "extractor re-blessed (sha changed)"
        return GateDecision(REBUILD_FULL, f"{why}; full build over all files", rebuilds=True)
    # repo_cache present, extractor same, content differs.
    return GateDecision(REBUILD_CHANGED, "content changed; rebuild changed files only", rebuilds=True)


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
    cache = {"content_hash": "e94c70d", "built_with_extractor_sha": "125a6ca",
             "built_with_vocab_sha": "d5frozen"}
    scenarios = [
        ("no-op (same commit)", dict(language="c", extractor_sha="125a6ca", vocab_sha="d5frozen",
                                     content_hash_new="e94c70d", repo_cache=cache)),
        ("content changed", dict(language="c", extractor_sha="125a6ca", vocab_sha="d5frozen",
                                 content_hash_new="ffff999", repo_cache=cache)),
        ("extractor re-blessed", dict(language="c", extractor_sha="NEWsha0", vocab_sha="d5frozen",
                                      content_hash_new="e94c70d", repo_cache=cache)),
        ("vocab amended", dict(language="c", extractor_sha="125a6ca", vocab_sha="d6next",
                               content_hash_new="e94c70d", repo_cache=cache)),
        ("first build (no cache)", dict(language="c", extractor_sha="125a6ca", vocab_sha="d5frozen",
                                        content_hash_new="e94c70d", repo_cache=None)),
        ("un-onboarded language", dict(language="java", extractor_sha=None, vocab_sha="d5frozen",
                                       content_hash_new="abc1234", repo_cache=None)),
    ]
    print("select_branch (deterministic, model-free):")
    for name, kw in scenarios:
        d = select_branch(**kw)
        print(f"  {name:28s} → {d.branch:16s} ({d.reason})")

    print("\ncheck_coverage (REONBOARD_FLAG predicate):")
    ok = check_coverage({"coverage": 0.82, "unresolved_patterns": []}, 0.80)
    bust = check_coverage({"coverage": 0.67, "unresolved_patterns": ["#ifdef-gated reg in feature_flags.c"]}, 0.80)
    print(f"  coverage 0.82 vs floor 0.80 → {'OK (no flag)' if ok is None else ok}")
    print(f"  coverage 0.67 vs floor 0.80 → REONBOARD_FLAG {bust}")


if __name__ == "__main__":
    _demo()
