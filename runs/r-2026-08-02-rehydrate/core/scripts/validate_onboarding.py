#!/usr/bin/env python3
"""validate_onboarding.py — the repo onboarding gate: profile scan → report → freeze (D-A21).

**The gate is the only human checkpoint on code-map quality.** Everything downstream — tier-1
matching, §16 impact entries, ultimately which stories get written — rests on a map whose
derivation rules were chosen here, once, per repo.

So the report is not a summary; it is the thing the human is deciding on. D-A21 names three things
a plain "approve?" cannot do, and each is a section of the report:

  1. **Distinguish human-authored from model-inferred purposes.** A map that is 85% declared
     purposes is a fundamentally better analysis substrate than one that is 60% model-inferred.
     Without the split the operator cannot see *what quality of map they are approving*, and
     D-A20's "a one-time scan bakes in a quality ceiling" risk is invisible.
  2. **Surface tier-1 entry count against target** — the economy problem, while it is still cheap
     to fix (`group singletons` at onboarding, not per run).
  3. **State the uncovered set explicitly** rather than implying completeness. A file in no module
     is invisible to tier 1 *forever*, so it has to be named.

Phase 1 (D-A21), which this module implements:

    1 clone + pin commit_sha        (the caller's; we take the tree as given)
    2 PROFILE SCAN   — label variants + coverage · include density/resolution · prefix-token
                       quality · .h placement · versioned duplicates · graph isolation
                       (degree zero BOTH directions) · symbol presence
    3 STAGE-B SAMPLE — measure header-prose recovery on the population B targets
    4 PROJECT        — stage distribution + stage-C cost from the sample
    5 GATE           — render the report; the human may `adjust profile`, `skip stage C`,
                       `group singletons`, or approve
    6 FREEZE         — profile_sha; approved model proposals bake in as DATA

The scan is deterministic and model-free. The only model-assisted step is `group singletons`,
which **proposes** groupings a human reviews as a diff — and its output freezes as data, so
nothing model-driven survives the freeze in an active form. That is the determinism guarantee,
and it is why the actions may be as model-assisted as they like.

Also retained from TASK-012: **freeze integrity** — the `extractor_sha` in
`core/extractor_manifest.yaml` must equal the live `git hash-object` of the extractor. A drift
means the frozen artifact was edited after the manifest was written, which would make the map
cache key stale and the freeze a lie.

Run: `python3 core/scripts/validate_onboarding.py`
"""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Sequence

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from core.extractors import c_extractor  # noqa: E402

FIXTURE = REPO_ROOT / "fixtures" / "c_repo"
MANIFEST = REPO_ROOT / "core" / "extractor_manifest.yaml"
EXTRACTOR = REPO_ROOT / "core" / "extractors" / "c_extractor.py"
PROFILE_DIR = REPO_ROOT / "core" / "code_profiles"

# D-A21's stage ladder. A/B are human-authored, C is model-inferred, C* is deterministic but thin,
# and `unanalyzable` is the population that must be NAMED rather than implied away.
STAGE_A, STAGE_B, STAGE_C, STAGE_CSTAR, UNANALYZABLE = "A", "B", "C", "C*", "--"

_INCLUDE = re.compile(rb'^\s*#\s*include\s+"([^"]+)"', re.M)
_VERSION_SUFFIX = re.compile(r"^(?P<stem>.+?)_(v\d+|old|test|bak|orig)$", re.I)
_TOKEN_SPLIT = re.compile(r"[_\-]|(?<=[a-z0-9])(?=[A-Z])")
_HAS_FUNCTION = re.compile(rb"\b\w+\s*\([^;]*\)\s*\{")

DEFAULT_PROFILE: dict = {
    "derivation": {
        # D-A20's survey INVERTED the first draft's ordering. Include-graph cohesion is primary
        # (56.5% of real files use local includes, 95.1% resolving to a repo file); prefixes are a
        # weak tie-break (24% singleton tokens; `s`/`md`/`or` are naming noise); directory is
        # worthless in a flat tree.
        "priority": ["include_graph_cohesion", "declared_purpose_similarity", "prefix_family"],
        "hub_threshold_fan_in": 8,
        "cluster_min_size": 2,
        "cluster_max_size": 40,
    },
    "purpose": {
        "label_aliases": list(c_extractor.DEFAULT_PURPOSE_LABELS),
        "fuzzy_edit_distance": 1,
        "warn_if_human_authored_below": 0.70,
        "low_confidence_threshold": 0.50,
    },
    "stages": {"skip_stage_c": False},
    "overrides": {"singleton_groups": []},
    "tier1_entry_target": 12,
}


# ──────────────────────────────────────────────────────────────────────────────
# Step 2 — the profile scan (deterministic, model-free)
# ──────────────────────────────────────────────────────────────────────────────
@dataclass
class Scan:
    root: Path
    files: list[str] = field(default_factory=list)
    label_counts: dict = field(default_factory=dict)
    declared: dict = field(default_factory=dict)          # path -> declared purpose
    generic: list[str] = field(default_factory=list)
    include_edges: dict = field(default_factory=dict)     # path -> [resolved repo paths]
    include_total: int = 0
    include_resolved: int = 0
    header_placement: dict = field(default_factory=dict)
    versioned_duplicates: list = field(default_factory=list)
    isolated: list = field(default_factory=list)          # degree zero BOTH directions
    no_symbols: list = field(default_factory=list)
    has_leading_comment: set = field(default_factory=set)
    prefix_tokens: dict = field(default_factory=dict)


def scan_repo(root: Path, files: Sequence[str], profile: dict) -> Scan:
    """D-A21 step 2 — the automated survey. A pure function of the tree + the profile."""
    s = Scan(root=root, files=list(files))
    aliases = profile["purpose"]["label_aliases"]
    stems: dict[str, list[str]] = defaultdict(list)
    by_name = {Path(f).name: f for f in files}

    for rel in files:
        src = (root / rel).read_bytes()

        block = c_extractor._leading_comment_block(src)
        if block is not None:
            s.has_leading_comment.add(rel)
        decl = c_extractor.extract_declared(src, label_aliases=aliases)
        if decl.get("purpose_declared"):
            s.declared[rel] = decl["purpose_declared"]
            if decl.get("purpose_quality") == "generic":
                s.generic.append(rel)
            if block is not None:
                idx = decl["purpose_declared_line"] - block[1]
                lines = block[0].splitlines()
                if 0 <= idx < len(lines) and (m := c_extractor._LABEL_LINE.match(lines[idx])):
                    lbl = m.group(1).strip()
                    s.label_counts[lbl] = s.label_counts.get(lbl, 0) + 1

        targets = []
        for inc in _INCLUDE.findall(src):
            s.include_total += 1
            name = Path(inc.decode()).name
            if name in by_name and by_name[name] != rel:
                s.include_resolved += 1
                targets.append(by_name[name])
        s.include_edges[rel] = targets

        # symbol presence — what stage C* would have to work with if C is skipped
        if not _HAS_FUNCTION.search(src):
            s.no_symbols.append(rel)

        if rel.endswith(".h"):
            top = rel.split("/")[0]
            s.header_placement[top] = s.header_placement.get(top, 0) + 1

        stem = Path(rel).stem
        base = m.group("stem") if (m := _VERSION_SUFFIX.match(stem)) else stem
        # Key on (base, EXTENSION): a `.c`/`.h` pair sharing a stem is the ordinary C convention,
        # not a versioned duplicate, and reporting it as one would bury the real hazard in noise.
        stems[(base, Path(rel).suffix)].append(rel)
        for tok in _TOKEN_SPLIT.split(stem):
            if tok:
                s.prefix_tokens[tok] = s.prefix_tokens.get(tok, 0) + 1

    for (base, _ext), group in sorted(stems.items()):
        # A duplicate needs a genuine SUFFIXED variant present (`_v2`, `_old`, `_test`), not just
        # two files that happen to share a base — which is what D-A20 counted (38 repo-wide, no
        # silent duplicate stems).
        variants = [g for g in group if _VERSION_SUFFIX.match(Path(g).stem)]
        if not variants or len(group) < 2:
            continue
        base_files = sorted(g for g in group if g not in variants)
        for other in sorted(variants):
            s.versioned_duplicates.append((base_files[0] if base_files else base, other))

    # Graph isolation — degree ZERO IN BOTH DIRECTIONS. One direction is ordinary (a leaf, an
    # entry point); both means the include graph says nothing at all about the file, so module
    # derivation has no signal for it and it lands in `unclustered`.
    fan_in: dict[str, int] = defaultdict(int)
    for f, targets in s.include_edges.items():
        for t in targets:
            fan_in[t] += 1
    s.isolated = sorted(f for f in files if not s.include_edges.get(f) and not fan_in.get(f))
    return s


# ──────────────────────────────────────────────────────────────────────────────
# Steps 3–4 — stage-B sample + projection
# ──────────────────────────────────────────────────────────────────────────────
def sample_stage_b(scan: Scan, *, sample_size: int = 100) -> tuple[int, int, float]:
    """D-A21 step 3 — header-prose recovery rate on the population stage B targets.

    That population is D-A20's "recoverable" one: ~2 300 real files carrying a header block with
    **no purpose-labelled field**, some of which is usable purpose prose sitting under no label.

    Sampling is deterministic (sorted order, not random) so the projection is reproducible — a
    gate report that changed between runs would be impossible to review.
    """
    population = sorted(f for f in scan.files
                        if f in scan.has_leading_comment and f not in scan.declared)
    sample = population[:sample_size]
    recovered = 0
    for rel in sample:
        block = c_extractor._leading_comment_block((scan.root / rel).read_bytes())
        if block and any(len(l.strip(" */\t")) > 24 for l in block[0].splitlines()[1:]):
            recovered += 1
    return len(population), len(sample), (recovered / len(sample)) if sample else 0.0


def project_distribution(scan: Scan, profile: dict) -> dict:
    """D-A21 step 4 — project the stage distribution and the stage-C cost from the sample."""
    pop, sampled, rate = sample_stage_b(scan)
    skip_c = profile["stages"]["skip_stage_c"]
    counts: dict[str, int] = defaultdict(int)
    b_left = round(pop * rate)
    for rel in scan.files:
        if rel in scan.declared:
            counts[STAGE_A] += 1
        elif rel in scan.has_leading_comment and b_left > 0:
            counts[STAGE_B] += 1
            b_left -= 1
        elif not skip_c:
            counts[STAGE_C] += 1
        # `skip stage C`: these files do NOT vanish — they fall through to C*, and only what C*
        # cannot cover becomes unanalyzable. A visible coverage reduction, not a hidden one.
        elif rel in scan.no_symbols:
            counts[UNANALYZABLE] += 1
        else:
            counts[STAGE_CSTAR] += 1

    total = len(scan.files)
    human = counts[STAGE_A] + counts[STAGE_B]
    return {
        "counts": dict(counts), "total": total,
        "stage_b_population": pop, "stage_b_sampled": sampled, "stage_b_rate": rate,
        "human_authored": human / total if total else 0.0,
        "model_inferred": counts[STAGE_C] / total if total else 0.0,
        "uncovered": counts[UNANALYZABLE] / total if total else 0.0,
        "stage_c_cost": counts[STAGE_C],
    }


# ──────────────────────────────────────────────────────────────────────────────
# Module derivation — deterministic graph arithmetic
# ──────────────────────────────────────────────────────────────────────────────
def derive_modules(scan: Scan, profile: dict) -> dict:
    """Hub exclusion → include-graph components → frozen overrides → singletons/unclustered.

    Deterministic by construction, which is exactly what makes the gate's `adjust profile` action
    cheap: adjust → recompute → updated distribution → adjust again. Only the freeze is one-way.
    """
    d = profile["derivation"]
    fan_in: dict[str, int] = defaultdict(int)
    for f, targets in scan.include_edges.items():
        for t in targets:
            fan_in[t] += 1
    hubs = sorted(f for f in scan.files if fan_in.get(f, 0) > d["hub_threshold_fan_in"])

    parent = {f: f for f in scan.files}

    def find(x: str) -> str:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a: str, b: str) -> None:
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[max(ra, rb)] = min(ra, rb)

    # Hubs are removed from the cluster glue: a file everything includes would otherwise merge
    # the entire repo into one component, which is the failure D-A21's hub threshold prevents.
    for f, targets in scan.include_edges.items():
        if f in hubs:
            continue
        for t in targets:
            if t not in hubs:
                union(f, t)

    groups: dict[str, list[str]] = defaultdict(list)
    for f in scan.files:
        if f not in hubs:
            groups[find(f)].append(f)

    # Frozen human-approved overrides win over derived membership. They are DATA a human signed,
    # applied deterministically — propose-never-bless.
    for override in profile["overrides"]["singleton_groups"]:
        members = [m for m in override["members"] if m in parent]
        if len(members) < 2:
            continue
        for key in list(groups):
            groups[key] = [m for m in groups[key] if m not in members]
            if not groups[key]:
                del groups[key]
        groups[f"override:{override['name']}"] = sorted(members)

    modules = {k: sorted(v) for k, v in groups.items() if len(v) >= d["cluster_min_size"]}
    singles = sorted(v[0] for v in groups.values() if len(v) == 1)
    unclustered = sorted(set(scan.isolated) & set(singles))
    singletons = [s for s in singles if s not in unclustered]
    return {
        "modules": modules, "singletons": singletons,
        "unclustered": unclustered, "hubs": hubs,
        # every singleton is its own tier-1 entry — the economy problem the gate surfaces while
        # it is still cheap to solve
        "tier1_entries": len(modules) + len(singletons) + (1 if unclustered else 0),
    }


# ──────────────────────────────────────────────────────────────────────────────
# Step 5 — the gate report (D-A21 layout)
# ──────────────────────────────────────────────────────────────────────────────
def _bar(frac: float, width: int = 20) -> str:
    filled = round(frac * width)
    return "█" * filled + "░" * (width - filled)


def render_gate_report(repo: str, commit_sha: str, scan: Scan, profile: dict,
                       dist: dict, mods: dict) -> str:
    d, p = profile["derivation"], profile["purpose"]
    total = dist["total"] or 1
    L = [f"═══ CODE MAP ONBOARDING — {repo} @ {commit_sha} " + "═" * 16, ""]

    L.append("SIGNAL PROFILE (proposed)")
    L.append(f"  module derivation   {d['priority'][0]} (primary)")
    L.append(f"  purpose labels      {' · '.join(p['label_aliases'][:5])} … "
             f"({len(p['label_aliases'])} aliases, fuzzy ≤{p['fuzzy_edit_distance']})")
    L.append(f"  hub threshold       fan-in > {d['hub_threshold_fan_in']}  →  shared_interfaces")
    L.append("  prefix families     tiebreak only")
    dirs = len({f.split('/')[0] for f in scan.files})
    L.append(f"  directory signal    {'usable' if dirs > 2 else 'unusable (flat tree)'} "
             f"({dirs} top-level dirs)")
    L.append("")

    L.append("PURPOSE RESOLUTION — projected distribution")
    for stage, label, note in (
        (STAGE_A, "declared label", "human-authored"),
        (STAGE_B, "header prose",
         f"human-authored   ← sampled {dist['stage_b_sampled']}/{dist['stage_b_population']}"),
        (STAGE_C, "whole-file read", "MODEL-INFERRED"),
        (STAGE_CSTAR, "symbol names", "deterministic"),
        (UNANALYZABLE, "unanalyzable", "NO COVERAGE"),
    ):
        n = dist["counts"].get(stage, 0)
        L.append(f"  {stage:3} {label:16} {n:5}  {n/total*100:5.1f}%  {_bar(n/total)}  {note}")
    L.append(" " * 24 + "─────")
    L.append(" " * 24 + f"{dist['total']:5}")
    L.append(f"      human-authored {dist['human_authored']*100:.1f}%  ·  "
             f"model-inferred {dist['model_inferred']*100:.1f}%  ·  "
             f"uncovered {dist['uncovered']*100:.1f}%")
    if dist["human_authored"] < p["warn_if_human_authored_below"]:
        L.append(f"      ⚠  below warn_if_human_authored_below "
                 f"({p['warn_if_human_authored_below']:.0%}) — this map's quality ceiling is set "
                 f"here; raising it later means re-onboarding")
    L.append("")

    L.append("MODULE DERIVATION")
    n_clustered = sum(len(v) for v in mods["modules"].values())
    L.append(f"  clustered by graph  {n_clustered:5}  {n_clustered/total*100:5.1f}%   →  "
             f"{len(mods['modules'])} modules")
    L.append(f"  singleton           {len(mods['singletons']):5}  "
             f"{len(mods['singletons'])/total*100:5.1f}%   →  {len(mods['singletons'])} "
             f"singleton modules")
    L.append(f"  unclustered bucket  {len(mods['unclustered']):5}  "
             f"{len(mods['unclustered'])/total*100:5.1f}%   →  "
             f"{1 if mods['unclustered'] else 0} bucket, always passed to tier 2")
    L.append(f"  hubs                {len(mods['hubs']):5}  "
             f"{len(mods['hubs'])/total*100:5.1f}%   →  shared_interfaces")
    target = profile["tier1_entry_target"]
    L.append(f"  tier-1 entries: {mods['tier1_entries']}" + (
        f"   ⚠  above target (~{target}) — singleton grouping recommended"
        if mods["tier1_entries"] > target else f"   (target ~{target}) ✓"))
    # A low tier-1 count is NOT automatically good: one giant cluster also scores low, and it is
    # the worse failure — tier 1 then filters nothing and every assertion falls through to tier 2
    # over the whole repo. Both size bounds are checked, not just the count.
    oversized = {k: len(v) for k, v in mods["modules"].items() if len(v) > d["cluster_max_size"]}
    if oversized:
        L.append(f"  ⚠  {len(oversized)} module(s) exceed cluster_max_size "
                 f"({d['cluster_max_size']}): {sorted(oversized.values(), reverse=True)} — "
                 f"tier 1 will not discriminate inside them; lower the hub threshold")
    if len(mods["modules"]) == 1 and n_clustered > 3 * d["cluster_min_size"]:
        L.append(f"  ⚠  the graph collapsed to ONE module of {n_clustered} files — the hub "
                 f"threshold is too high to break the glue; `adjust profile` before approving")
    L.append("")

    L.append("COVERAGE GAPS")
    L.append(f"  unanalyzable         {dist['counts'].get(UNANALYZABLE, 0):4}   listed — impact "
             f"findings will not cover these")
    L.append(f"  versioned duplicates {len(scan.versioned_duplicates):4}   require disposition (D-A16)")
    for a, b in scan.versioned_duplicates:
        L.append(f"       {a}  ↔  {b}")
    L.append(f"  generic purposes     {len(scan.generic):4}   flagged — tier 1 will not weight these")
    L.append(f"  isolated (deg 0 ↔)   {len(scan.isolated):4}   no graph signal at all")
    for f in scan.isolated:
        L.append(f"       {f}")
    L.append("")

    L.append("SCAN DETAIL")
    res = (scan.include_resolved / scan.include_total) if scan.include_total else 0.0
    L.append(f"  local includes      {scan.include_total} total, {res:.1%} resolve to a repo file "
             f"(avg {scan.include_total/total:.1f}/file)")
    L.append(f"  purpose labels seen {dict(sorted(scan.label_counts.items(), key=lambda kv: -kv[1]))}")
    L.append(f"  .h placement        {scan.header_placement}  (file-type convention, no module signal)")
    L.append(f"  files with symbols  {dist['total'] - len(scan.no_symbols)}/{dist['total']}")
    L.append("")
    L.append(f"ESTIMATED COST   stage C ≈ {dist['stage_c_cost']} whole-file reads")
    L.append("")
    L.append("[ approve ]  [ adjust profile ]  [ skip stage C ]  [ group singletons ]")
    return "\n".join(L)


# ──────────────────────────────────────────────────────────────────────────────
# The three gate actions — PRE-FREEZE ONLY, and they compose freely.
# After the freeze none of them exist at runtime: that is the determinism guarantee,
# and it is what lets them be model-assisted without weakening the binding rule.
# ──────────────────────────────────────────────────────────────────────────────
def adjust_profile(profile: dict, **changes) -> dict:
    """Edit signal-profile parameters → recompute → re-review. Returns a NEW profile.

    Keys are dotted (`derivation.hub_threshold_fan_in`). An unknown key raises rather than being
    silently ignored — a typo'd threshold that quietly did nothing would send the operator into
    the freeze believing they had changed something.
    """
    out = json.loads(json.dumps(profile))
    for dotted, value in changes.items():
        block, _, key = dotted.partition(".")
        if not key or block not in out or not isinstance(out[block], dict) or key not in out[block]:
            raise KeyError(f"unknown profile parameter {dotted!r}")
        out[block][key] = value
    return out


def skip_stage_c(profile: dict) -> dict:
    """Decline the expensive whole-file model pass.

    Those files do not vanish: they fall to C* (symbol names), and only what C* cannot cover
    becomes unanalyzable. **Reversible** — purposes cache per file content hash, so running C
    later fills the gaps incrementally. Skipping at onboarding is a deferral, not an exclusion.
    """
    return adjust_profile(profile, **{"stages.skip_stage_c": True})


def propose_singleton_groups(scan: Scan, mods: dict, *, max_groups: int = 8) -> list[dict]:
    """Model-PROPOSED groupings of the singleton population, for human review **as a diff**.

    In a real run the model reads the singletons' purposes — short strings, cheap — and groups by
    semantic similarity. Here that judgment is stood in for deterministically (shared leading
    prefix token) so the fixture proof stays reproducible.

    Nothing is applied. The human approves or rejects **per group**; approved groups freeze as
    membership overrides. Reviewing as a diff is the safeguard: a bad grouping produces a module
    with a vague synthesised purpose, which is the cluster-quality problem arriving by another
    route.
    """
    buckets: dict[str, list[str]] = defaultdict(list)
    for f in mods["singletons"]:
        stem = Path(f).stem
        buckets[(_TOKEN_SPLIT.split(stem)[0] or stem).lower()].append(f)
    out = []
    for head, members in sorted(buckets.items()):
        if len(members) < 2:
            continue
        out.append({
            "name": f"{head}_group",
            "members": sorted(members),
            "rationale": f"shared prefix token {head!r}; purposes: "
                         + " | ".join(scan.declared.get(m, "(none declared)")[:38]
                                      for m in sorted(members)),
        })
    return out[:max_groups]


def approve_singleton_groups(profile: dict, proposals: Sequence[dict],
                             approved: Sequence[str]) -> dict:
    """Freeze the human-approved subset as membership overrides — data, never behaviour."""
    out = json.loads(json.dumps(profile))
    out["overrides"]["singleton_groups"] = [p for p in proposals if p["name"] in approved]
    return out


# ──────────────────────────────────────────────────────────────────────────────
# Step 6 — the freeze
# ──────────────────────────────────────────────────────────────────────────────
def compute_profile_sha(profile: dict) -> str:
    """Digest over the profile's SEMANTIC content — half of the map cache key.

    This is what makes gate branch 4 possible: if re-onboarding moves the hub threshold from 500
    to 200, every module boundary can shift, so nothing in the old map is trustworthy. A profile
    change invalidates wholesale; a commit change invalidates selectively.

    Gate metadata is excluded deliberately — who reviewed the profile does not change how the repo
    is read, and including it would invalidate every cached map on a re-signature.
    """
    body = {k: v for k, v in profile.items()
            if k not in ("gate", "profile_sha", "repo", "commit_sha")}
    return hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest()[:7]


def freeze_profile(profile: dict, *, repo: str, commit_sha: str, reviewed_by: str,
                   actions: Sequence[str] = (), ts: str = "2026-08-01T00:00:00Z") -> dict:
    out = json.loads(json.dumps(profile))
    out["repo"] = repo
    out["commit_sha"] = commit_sha
    out["gate"] = {"status": "frozen", "reviewed_by": reviewed_by, "reviewed_at": ts,
                   "actions_taken": list(actions)}
    out["profile_sha"] = compute_profile_sha(out)
    return out


def write_profile(profile: dict, path: Path) -> Path:
    import yaml
    header = (
        "# Frozen signal profile — how THIS repo is read (D-A21 step 6, D-A22).\n"
        "#\n"
        "# Written by core/scripts/validate_onboarding.py at the onboarding gate. `profile_sha` is\n"
        "# half the map cache key `(commit_sha, profile_sha)`: a profile change invalidates every\n"
        "# cached map WHOLESALE (gate branch 4), because if the derivation rules moved then every\n"
        "# module boundary can have moved with them. A commit change invalidates selectively.\n"
        "#\n"
        "# `overrides.singleton_groups` are model-PROPOSED and human-APPROVED, frozen here as data.\n"
        "# Nothing model-driven survives the freeze in an active form — the three gate actions are\n"
        "# pre-freeze only, which is the determinism guarantee.\n")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(header + yaml.safe_dump(profile, sort_keys=False), encoding="utf-8")
    return path


# ──────────────────────────────────────────────────────────────────────────────
# Freeze integrity (retained from TASK-012)
# ──────────────────────────────────────────────────────────────────────────────
def check_freeze_integrity() -> tuple[bool, str]:
    """The recorded `extractor_sha` must equal the live file's git hash.

    A drift means the frozen artifact was edited after the manifest was written: the map cache key
    would be stale and the freeze a lie. This is what makes the manifest a real freeze record
    rather than a comment.
    """
    import yaml
    manifest = yaml.safe_load(MANIFEST.read_text())
    recorded = next(e["extractor_sha"] for e in manifest["extractors"] if e["language"] == "c")
    live = subprocess.run(["git", "hash-object", "core/extractors/c_extractor.py"],
                          cwd=REPO_ROOT, capture_output=True, text=True).stdout.strip()
    return recorded == live[:len(recorded)], f"recorded={recorded} live={live[:len(recorded)]}"


def c_files(root: Path) -> list[str]:
    return sorted(str(p.relative_to(root)) for p in root.rglob("*") if p.suffix in (".c", ".h"))


def run_gate(root: Path = FIXTURE, profile: dict | None = None) -> tuple[Scan, dict, dict]:
    """Steps 2–4 for a tree: scan → project → derive. Returns ``(scan, dist, mods)``."""
    prof = profile if profile is not None else json.loads(json.dumps(DEFAULT_PROFILE))
    scan = scan_repo(root, c_files(root), prof)
    return scan, project_distribution(scan, prof), derive_modules(scan, prof)


def _commit_of(root: Path) -> str:
    """The repo's HEAD, or a marker when it is not a git checkout (external-build tree copy)."""
    import subprocess
    r = subprocess.run(["git", "-C", str(root), "rev-parse", "--short", "HEAD"],
                       capture_output=True, text=True)
    return r.stdout.strip() if r.returncode == 0 and r.stdout.strip() else "not-a-git-checkout"


def main(argv: Sequence[str] | None = None) -> int:
    """Run the D-A21 onboarding gate against a repo.

    Until TASK-127 this took ``argv`` and **never parsed it** — no argparse — and was hardcoded
    to the fixture tree with literal "fixtures/c_repo" / "9f3c1ab" strings in the report. It was
    a proof harness wearing a CLI's clothes: an operator had no way to point the gate at their
    own repo, which is the one thing an onboarding gate is for. Found on the first real run,
    where `--help` printed a gate report for a directory that was not there.
    """
    import argparse

    ap = argparse.ArgumentParser(
        description="D-A21 code-map onboarding gate: scan a repo, project purpose coverage, "
                    "derive modules, and report what a human must decide before freezing.")
    ap.add_argument("--repo", default=str(FIXTURE),
                    help="repo to onboard (default: the c_repo fixture)")
    ap.add_argument("--commit", help="commit sha for the report header (default: the repo's HEAD)")
    ap.add_argument("--profile", help="frozen signal profile to read this repo WITH "
                                      "(core/code_profiles/<repo>.profile.yaml). Omit to run in "
                                      "PROPOSE mode against the unfrozen defaults.")
    args = ap.parse_args(argv)

    root = Path(args.repo)
    if not root.is_dir():
        ap.error(f"--repo is not a directory: {root}")

    # A scan that found nothing is an ERROR, not 0% coverage. Rendering it as a distribution
    # produces a plausible report — "0.0% human-authored, below the warn threshold" — that
    # points at map QUALITY when the real fault is that the gate was aimed at the wrong path.
    # Same failure shape as hydrate's `--unshallow`: a true statement about the wrong thing.
    files = c_files(root)
    if not files:
        print(f"validate_onboarding.py: no .c/.h files under {root} — nothing to onboard. "
              f"Check the --repo path.", file=sys.stderr)
        return 2

    # The gate has two modes, and conflating them was a real defect (TASK-127):
    #
    #   PROPOSE  — no frozen profile yet. Scan with the defaults, report, the operator picks
    #              one of the four actions, and the outcome is FROZEN as data.
    #   VALIDATE — a frozen profile exists. Read the repo WITH IT and confirm it still holds.
    #
    # Until now `main()` always used DEFAULT_PROFILE, so a repo whose profile was already frozen
    # got re-reported against rules nobody was using: `c_repo.profile.yaml` had
    # `hub_threshold_fan_in: 3` (plus approved singleton_groups) while the gate reported on 8,
    # and duly warned that the graph had collapsed — a decision the operator had already made
    # and frozen. Worse than noise: `profile_sha` is half the map cache key, so a map derived
    # from the defaults would be keyed against a profile that governs nothing.
    if args.profile:
        import yaml
        frozen = yaml.safe_load(Path(args.profile).read_text(encoding="utf-8"))
        profile = {**json.loads(json.dumps(DEFAULT_PROFILE)), **frozen}
        mode = f"VALIDATE against frozen {Path(args.profile).name}"
    else:
        profile = json.loads(json.dumps(DEFAULT_PROFILE))
        mode = "PROPOSE (unfrozen defaults — the four actions below are live)"

    print(f"mode: {mode}\n")
    scan, dist, mods = run_gate(root, profile)
    print(render_gate_report(str(root), args.commit or _commit_of(root), scan, profile, dist, mods))
    ok, detail = check_freeze_integrity()
    print(f"\nfreeze integrity: {'OK' if ok else 'DRIFT'} — {detail}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
