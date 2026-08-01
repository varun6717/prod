#!/usr/bin/env python3
"""tier_walk.py — the deterministic core of Arm 1's three-tier walk (§5.6, D-A19).

Arm 1 asks *"what did we miss?"* per assertion. The walk narrows, then widens:

    tier 1   assertion vs **module** purposes        ~10²   → matched modules
    tier 2   vs **file** purposes, matched only      ~10³   → candidate files
    tier 3a  read the **source** of those files             → confirm / refute landings
    tier 3b  walk `depends_on`/`used_by` to closure          → RIPPLE, reaching files no tier picked

Tier 1 is what makes tier 2 affordable, and the argument is **attention** before cost: a model can
weigh ten module purposes carefully; over five thousand the matching is shallow and unreliable.

**`purpose` seeds; source establishes.** Nothing is ever concluded from a purpose alone.

This module owns the parts that must be deterministic — selection *scope* (what tier 1 is obliged
to consider) and the closure walk. The semantic matching itself is model judgment and is injected,
so the seam is visible rather than pretended away.
"""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from typing import Callable, Iterable, Sequence

UNCLUSTERED_SUFFIX = ":unclustered"


def assertion_query(frame: str, req_title: str, req_description: str, assertion: str) -> str:
    """The tier-1/2 query — **raw text**, no keyword extraction, no intermediate artifact (D-A19).

    All four parts are required, and a bare assertion is the failure case the design calls out:
    *"accepted values are 01–04"* matches nothing on its own. The assertion narrows **what to
    verify**; the requirement context supplies **what to search for**.
    """
    return "\n".join(x for x in (frame, req_title, req_description, assertion) if x)


@dataclass
class Tier1Result:
    matched: list[str] = field(default_factory=list)
    widened: list[str] = field(default_factory=list)     # included because confidence was low
    always_passed: list[str] = field(default_factory=list)
    considered: int = 0


def tier1(query: str, components: Sequence[dict], matcher: Callable[[str, dict], bool], *,
          low_confidence_threshold: float = 0.5) -> Tier1Result:
    """Match the assertion against **every** module purpose. Returns the matched module set.

    Two inclusion rules that are not the matcher's business, which is why they live here:

    - **Low confidence WIDENS, never excludes.** If a synthesised purpose cannot be trusted to
      describe its cluster, it cannot be trusted to rule the cluster out either. The asymmetry is
      the point: a false positive costs tier 2 some work; a false negative is missed impact.
    - **`unclustered` always passes.** It is the doubly-unknown bucket — cannot group, cannot
      describe — so there is nothing to match on and therefore nothing that could be safely ruled
      out.

    Both mean tier 1 can only ever be *over*-inclusive, which is the correct failure direction.
    """
    res = Tier1Result(considered=len(components))
    for c in components:
        module = c["module"]
        if c.get("always_pass_tier1") or module.endswith(UNCLUSTERED_SUFFIX):
            res.matched.append(module)
            res.always_passed.append(module)
            continue
        if matcher(query, c):
            res.matched.append(module)
        elif c.get("purpose_confidence", 1.0) < low_confidence_threshold:
            res.matched.append(module)
            res.widened.append(module)
    return res


def tier2(query: str, files: Sequence[dict], matched_modules: Iterable[str],
          matcher: Callable[[str, dict], bool]) -> list[str]:
    """File purposes, **within matched modules only** — the economy tier 1 bought."""
    scope = set(matched_modules)
    return [f["path"] for f in files if f.get("module") in scope and matcher(query, f)]


# ──────────────────────────────────────────────────────────────────────────────
# Tier 3b — closure
# ──────────────────────────────────────────────────────────────────────────────
def _identity(path: str) -> str:
    """`src/routing/brand_router.c` → `routing/brand_router` — the edge naming scheme."""
    parts = path.replace("\\", "/").split("/")
    stem = parts[-1].rsplit(".", 1)[0]
    return f"{parts[-2]}/{stem}" if len(parts) >= 2 else stem


def closure(files: Sequence[dict], seeds: Iterable[str], *,
            extra_edges: dict | None = None, max_hops: int | None = None) -> dict:
    """Walk `depends_on`/`used_by` outward from ``seeds`` to a **fixed point**.

    **Both directions, deliberately.** A change to a file affects what it calls *and* everything
    that calls it; walking one way would systematically miss half the ripple, and the half missed
    would be silent. Termination is a fixed point rather than a hop budget — with a budget you
    cannot tell "nothing more to find" from "ran out of hops".

    ``extra_edges`` is the **source-extends** seam (tier 3a feeding tier 3b): where reading the
    source reveals an edge the map missed — an indirect dispatch the parser could not resolve —
    that edge joins the walk. The map is a starting point, not the boundary of what is true.

    Returns ``{"reached", "hops", "by_hop", "via"}``; ``via`` records why each file was reached,
    which is what makes the ripple reviewable instead of a bare list.
    """
    # An identity resolves to EVERY file carrying it — `config/brand_rules` names both
    # `brand_rules.c` and `brand_rules.h`, which are one compilation unit. Resolving to a single
    # file would be both wrong (a change to the unit touches its header) and, worse,
    # ORDER-DEPENDENT: a last-wins dict would pick whichever of the pair was enumerated last, and
    # the ripple would silently differ between runs while looking perfectly stable.
    by_identity: dict[str, list[str]] = {}
    for f in files:
        by_identity.setdefault(_identity(f["path"]), []).append(f["path"])
    by_identity = {k: sorted(v) for k, v in by_identity.items()}
    by_path = {f["path"]: f for f in files}

    out: dict[str, set[str]] = {p: set() for p in by_path}
    for f in files:
        p = f["path"]
        for ref in list(f.get("depends_on", [])) + list(f.get("used_by", [])):
            for t in by_identity.get(ref, ()):
                if t == p:
                    continue
                out[p].add(t)
                out.setdefault(t, set()).add(p)      # both directions, always
    for src, targets in (extra_edges or {}).items():
        for t in targets:
            out.setdefault(src, set()).add(t)
            out.setdefault(t, set()).add(src)

    reached = {s: 0 for s in seeds if s in by_path}
    via: dict[str, str] = {s: "seed (tier 2 landing point)" for s in reached}
    frontier = deque(reached)
    hops = 0
    while frontier:
        nxt: deque = deque()
        hops += 1
        if max_hops is not None and hops > max_hops:
            break
        while frontier:
            cur = frontier.popleft()
            for nb in sorted(out.get(cur, ())):
                if nb not in reached:
                    reached[nb] = hops
                    via[nb] = f"reached from {cur} at hop {hops}"
                    nxt.append(nb)
        frontier = nxt
    by_hop: dict[int, list[str]] = {}
    for p, h in sorted(reached.items()):
        by_hop.setdefault(h, []).append(p)
    return {"reached": sorted(reached), "hops": max(reached.values()) if reached else 0,
            "by_hop": by_hop, "via": via}


def is_fixed_point(files: Sequence[dict], reached: Sequence[str],
                   extra_edges: dict | None = None) -> bool:
    """True iff one more expansion adds nothing — the actual termination condition."""
    again = closure(files, reached, extra_edges=extra_edges)
    return set(again["reached"]) == set(reached)
