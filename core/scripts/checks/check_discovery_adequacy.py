#!/usr/bin/env python3
"""check_discovery_adequacy.py — every `must_capture` has an eliciting question (TASK-111, D-A13).

D-A13's most consequential finding is easy to read past: **discovery is primary for exactly three
sections — §9, §12, §13.** No document in the corpus answers them. Disposition routing and the
per-artifact index — the entire retrieval apparatus — buy those sections **nothing**. Their quality
rests *entirely* on the questions the author thinks to ask.

That promotes question adequacy from a nice-to-have to a load-bearing property, and load-bearing
properties get checked rather than hoped for.

**The mechanism.** Each `probe_if_missing` entry declares which `must_capture` items it elicits:

    probe_if_missing:
      - { ask: "What are we assuming this does NOT affect? Name the systems.", elicits: [2] }

So the mapping is **data, not prose**, and "is every must_capture reachable by a question?" becomes
a set-cover check anyone can run. Without the `elicits` link the assessment would be a document
someone read once, which is exactly how the gap it found got there.

**Tiers, because not every section is elicited the same way.** A section fed by documents can
legitimately answer a `must_capture` from a source. A section fed by the *operator* cannot — there
is nothing else to fall back on:

  - **discovery-primary (`discovery: P`)** — §9/§12/§13. Every `must_capture` MUST be elicited.
    A gap here is unrecoverable: no source can cover for it. **Error.**
  - **operator-fed (`discovery: S` or any `frame`)** — every `must_capture` SHOULD be elicited;
    a gap is reported as a warning, since a source may cover it.
  - **derived (§1, §16, §17, §18)** — no probes by design. §1 summarises the body; §16/§18 are
    enrichment's output; §17 accumulates. Asking a question here would be a category error.

Run: python3 core/scripts/checks/check_discovery_adequacy.py [--domain payment_brand] [--demo]
"""
from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]

# D-A13: sections derived from other content rather than elicited. Probes here are a category
# error, not an omission — §1 summarises the body, §16/§18 are enrichment's output, §17 accrues.
DERIVED_SECTIONS: frozenset[int] = frozenset({1, 16, 17, 18})


@dataclass
class AdequacyResult:
    name: str = "discovery-question adequacy (D-A13)"
    ok: bool = True
    errors: list[str] = field(default_factory=list)      # discovery-primary gaps — unrecoverable
    warnings: list[str] = field(default_factory=list)    # operator-fed gaps — a source may cover
    covered: int = 0
    total: int = 0
    primary_sections: list[int] = field(default_factory=list)


def load_profile(domain: str, repo_root: Path = REPO_ROOT) -> dict:
    import yaml
    path = repo_root / "core" / "profiles" / domain / f"si_profile.{domain}.yaml"
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def check_discovery_adequacy(domain: str = "payment_brand", *,
                             repo_root: Path = REPO_ROOT) -> AdequacyResult:
    res = AdequacyResult()
    profile = load_profile(domain, repo_root)

    for s in profile.get("sections") or []:
        sid = s["id"]
        inputs = s.get("inputs") or {}
        must = s.get("must_capture") or []
        probes = s.get("probe_if_missing") or []
        title = s.get("title", "?")

        if sid in DERIVED_SECTIONS:
            if probes:
                res.warnings.append(
                    f"§{sid} {title!r} is derived (D-A13) but declares probes — it is summarised "
                    f"or accumulated, not elicited")
            continue

        discovery_primary = inputs.get("discovery") == "P"
        operator_fed = "discovery" in inputs or "frame" in inputs
        if discovery_primary:
            res.primary_sections.append(sid)

        # Every probe must be the {ask, elicits} shape, or the mapping is not checkable at all.
        elicited: set[int] = set()
        for n, p in enumerate(probes, 1):
            if not isinstance(p, dict) or "ask" not in p or "elicits" not in p:
                res.errors.append(
                    f"§{sid} probe {n} is not {{ask, elicits}} — without the link the mapping "
                    f"is prose and cannot be checked")
                continue
            for idx in p["elicits"]:
                if not 1 <= idx <= len(must):
                    res.errors.append(
                        f"§{sid} probe {n} elicits must_capture #{idx}, which does not exist "
                        f"(section has {len(must)})")
                else:
                    elicited.add(idx)

        gaps = [i for i in range(1, len(must) + 1) if i not in elicited]
        res.total += len(must)
        res.covered += len(must) - len(gaps)
        for i in gaps:
            msg = (f"§{sid} {title!r} must_capture #{i} has no eliciting question: "
                   f"{must[i-1][:72]}…")
            if discovery_primary:
                res.errors.append(msg + "  [discovery-PRIMARY: no source can cover this]")
            elif operator_fed:
                res.warnings.append(msg)
            else:
                res.warnings.append(msg + "  [source-fed: a document may cover it]")

    res.ok = not res.errors
    return res


def _demo() -> int:
    import copy
    import tempfile

    import yaml

    domain = "payment_brand"
    res = check_discovery_adequacy(domain)
    print(f"{res.name} — domain {domain!r}")
    print(f"  discovery-PRIMARY sections: §{res.primary_sections} "
          f"(D-A13: no document answers these)")
    print(f"  must_capture coverage: {res.covered}/{res.total} elicited")
    for w in res.warnings:
        print(f"  warn: {w}")
    for e in res.errors:
        print(f"  ERROR: {e}")
    assert res.ok, "the frozen profile must leave no discovery-primary gap"
    assert res.covered == res.total, f"expected full coverage, got {res.covered}/{res.total}"
    print("  [PASS] every must_capture in every elicited section has a question")

    good = load_profile(domain)
    mutations = [
        ("drop a §13 question (discovery-primary)",
         lambda p: next(s for s in p["sections"] if s["id"] == 13)["probe_if_missing"].pop(1),
         True),
        ("drop a §9 question (discovery-primary)",
         lambda p: next(s for s in p["sections"] if s["id"] == 9)["probe_if_missing"].pop(0),
         True),
        ("drop a §15 question (discovery-supporting)",
         lambda p: next(s for s in p["sections"] if s["id"] == 15)["probe_if_missing"].pop(4),
         False),
        ("probe reverts to a bare string",
         lambda p: next(s for s in p["sections"] if s["id"] == 12)["probe_if_missing"].__setitem__(
             0, "What are we not doing?"),
         True),
        ("elicits points at a must_capture that does not exist",
         lambda p: next(s for s in p["sections"] if s["id"] == 12)["probe_if_missing"][0]
                   .__setitem__("elicits", [9]),
         True),
    ]
    print("\nnegatives (a discovery-PRIMARY gap must error; a supporting gap must only warn):")
    with tempfile.TemporaryDirectory(prefix="adequacy-") as tmp:
        root = Path(tmp)
        pdir = root / "core" / "profiles" / domain
        pdir.mkdir(parents=True)
        for label, mutate, should_error in mutations:
            bad = copy.deepcopy(good)
            mutate(bad)
            (pdir / f"si_profile.{domain}.yaml").write_text(
                yaml.safe_dump(bad, sort_keys=False), encoding="utf-8")
            r = check_discovery_adequacy(domain, repo_root=root)
            if should_error:
                assert r.errors and not r.ok, f"{label!r} should have errored"
                print(f"  {label:46} -> ERROR: {r.errors[0][:52]}…")
            else:
                assert r.ok and r.warnings, f"{label!r} should have warned, not errored"
                print(f"  {label:46} -> warn only: {r.warnings[0][:44]}…")

    # ── The sparse-corpus proof: WHY discovery-primary sections need total question coverage.
    # Route a deliberately thin corpus — only product_domain_knowledge (the two KB pages), no
    # mandate — and count what each section can still see. Where nothing routes, the probes are
    # the ONLY path to content, so anything they miss is content that can never be authored.
    print("\nsparse-corpus routing (only `product_domain_knowledge` present — no mandate):")
    sparse = {"product_domain_knowledge"}
    for s in good["sections"]:
        sid = s["id"]
        if sid in DERIVED_SECTIONS:
            continue
        classes = {k: v for k, v in (s.get("classes") or {}).items() if v != "E"}
        routed = sorted(set(classes) & sparse)
        if routed:
            continue
        must, probes = len(s["must_capture"]), s.get("probe_if_missing") or []
        elicited = {i for p in probes for i in p["elicits"]}
        tier = "PRIMARY" if (s.get("inputs") or {}).get("discovery") == "P" else "supporting"
        print(f"  §{sid:>2} {s['title'][:30]:32} routes 0 artifacts → all {must} must_capture "
              f"depend on {len(probes)} question(s); elicited {len(elicited)}/{must}  [{tier}]")
        assert len(elicited) == must, \
            f"§{sid} sees no source in a sparse corpus and its questions do not cover it"
    print("  every section starved by the sparse corpus is still fully reachable by question")

    print("\nPASS — every must_capture is reachable by a question; a gap in §9/§12/§13 errors "
          "(no source can cover it), a gap in a supporting section warns; and under a sparse "
          "corpus the starved sections remain fully elicitable.")
    return 0


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if "--demo" in argv:
        return _demo()
    domain = argv[argv.index("--domain") + 1] if "--domain" in argv else "payment_brand"
    res = check_discovery_adequacy(domain)
    print(f"{res.name} — {'PASS' if res.ok else 'FAIL'} "
          f"({res.covered}/{res.total} must_capture elicited)")
    for w in res.warnings:
        print(f"  warn:  {w}")
    for e in res.errors:
        print(f"  ERROR: {e}")
    return 0 if res.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
