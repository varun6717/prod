#!/usr/bin/env python3
"""check_index_completeness.py — guardrail 7: the per-artifact index is TOTAL (D-A18).

A **family-2 context check**: it runs at **ingest**, over the artifacts a run produced, and is
reported in coverage. It is deliberately **not** a §10 build check — §10 checks the seam before
a run, this checks a run's own output — so it does not appear in ``build_checks.py``.

────────────────────────────────────────────────────────────────────────────────────────
Why this check is load-bearing rather than hygiene
────────────────────────────────────────────────────────────────────────────────────────
The whole argument for replacing tags with an index is **density**: a tag exists only where
someone applied it, so "no tag matched" cannot distinguish *the content isn't there* from
*the tagger missed it*; an index summarises everything **by construction**, so "not in the
index" is a defensible negative.

"By construction" is doing a lot of work in that sentence — and it is only true if somebody
checks. An index that silently skipped twenty pages looks exactly like a complete one, and
puts you back in sparse coverage with no signal: the precise failure mode being escaped.
This module is what makes the density claim a checked property instead of an assumption.

Hence: a gap is an **error**, never a warning.

────────────────────────────────────────────────────────────────────────────────────────
What is asserted
────────────────────────────────────────────────────────────────────────────────────────
  1. ``lines_total`` matches the extract's real line count      (the index is about THIS file)
  2. ``lines_total == lines_indexed``                           (the declared identity, D-A18)
  3. every line 1..lines_total is inside **exactly one** entry  (no gap AND no overlap)
  4. ``entries == len(index)``                                  (the count is not decorative)
  5. every id in ``subdivided[]`` has ≥2 parts present          (a recorded split is a real one)
  6. shape: ids unique, ranges well-formed + in document order, summaries non-empty

(3) is the substance; the rest keep the file self-consistent so (3) cannot be satisfied by a
mislabelled index. Overlap matters as much as gaps — double-covered lines inflate
``lines_indexed`` and can mask a hole elsewhere.

Usage::

    python3 core/scripts/checks/check_index_completeness.py <dir-or-extract> [...]
    python3 core/scripts/checks/check_index_completeness.py --demo

Given a directory, every ``*.md`` with a sibling ``*.index.json`` is checked; an extract with
no index is reported as a violation (build always — D-A18 rule 3), never skipped.
"""
from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Sequence

REPO_ROOT = Path(__file__).resolve().parents[3]
INDEX_SUFFIX = ".index.json"


@dataclass
class IndexReport:
    """Per-artifact result. ``ok`` iff no violations."""
    extract: Path
    lines_total: int = 0
    entries: int = 0
    subdivided: list[str] = field(default_factory=list)
    violations: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.violations


def _split_base(entry_id: str) -> str | None:
    """``"4b"`` → ``"4"``; ``"3.2.2a"`` → ``"3.2.2"``; a plain id → ``None``.

    Synthetic parts are the original id plus a lowercase letter suffix (D-A18 rule 2), which
    is what lets the checker reconcile them against ``subdivided[]`` in both directions.
    """
    m = re.fullmatch(r"(.*\d)([a-z])", entry_id)
    return m.group(1) if m else None


def index_path_for(extract: Path) -> Path:
    """``<doc>.md`` → ``<doc>.index.json`` (the D-A18 two-file pairing)."""
    return extract.with_suffix("").with_suffix(INDEX_SUFFIX) if extract.suffix == ".md" \
        else Path(str(extract) + INDEX_SUFFIX)


def count_lines(path: Path) -> int:
    """Physical line count of the extract — what the index's ranges are measured in.

    A trailing newline ends the last line; it does not begin a new empty one (this is
    ``wc -l`` semantics, and it is what the index's ``lines_total`` must agree with).
    """
    text = path.read_text(encoding="utf-8")
    if not text:
        return 0
    return len(text.splitlines())


def check_index(extract: Path) -> IndexReport:
    """Validate one ``(extract, index)`` pair. Returns a report; never raises on content."""
    rep = IndexReport(extract=extract)
    idx_path = index_path_for(extract)

    if not idx_path.is_file():
        rep.violations.append(
            f"no index beside the extract ({idx_path.name}) — every doc artifact is indexed, "
            f"whatever its size (D-A18 rule 3: build always, consult conditionally)")
        return rep

    try:
        doc = json.loads(idx_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        rep.violations.append(f"{idx_path.name} is not valid JSON: {exc}")
        return rep

    actual_lines = count_lines(extract)
    rep.lines_total = int(doc.get("lines_total", -1))
    entries = doc.get("index")
    rep.subdivided = list(doc.get("subdivided", []) or [])

    if not isinstance(entries, list) or not entries:
        rep.violations.append("`index` must be a non-empty list of entries")
        return rep
    rep.entries = len(entries)

    # (1) the index is about THIS extract
    if rep.lines_total != actual_lines:
        rep.violations.append(
            f"lines_total={rep.lines_total} but {extract.name} has {actual_lines} lines")

    # (4) the declared count is real
    declared = doc.get("entries")
    if declared is not None and declared != len(entries):
        rep.violations.append(f"entries={declared} but `index` holds {len(entries)}")

    # (6) shape, and gather the ranges
    seen_ids: set[str] = set()
    ranges: list[tuple[int, int, str]] = []
    for n, e in enumerate(entries):
        eid = str(e.get("id", f"<entry {n}>"))
        if eid in seen_ids:
            rep.violations.append(f"duplicate entry id {eid!r}")
        seen_ids.add(eid)
        rng = e.get("lines")
        if not (isinstance(rng, list) and len(rng) == 2
                and all(isinstance(v, int) for v in rng)):
            rep.violations.append(f"entry {eid!r}: `lines` must be [first, last] integers")
            continue
        first, last = rng
        if first < 1 or last < first:
            rep.violations.append(f"entry {eid!r}: malformed range {rng}")
            continue
        if not str(e.get("summary", "")).strip():
            rep.violations.append(f"entry {eid!r}: empty summary — a heading alone is not an index")
        ranges.append((first, last, eid))

    if not ranges:
        return rep

    # document order — the author reads the index top-down and packs groups in document order
    if ranges != sorted(ranges):
        rep.violations.append("entries are not in document order (sort by `lines`)")

    # (3) THE check: exactly-once coverage of 1..lines_total
    total = actual_lines if actual_lines > 0 else rep.lines_total
    owner: dict[int, str] = {}
    for first, last, eid in ranges:
        for ln in range(first, last + 1):
            if ln in owner:
                rep.violations.append(
                    f"line {ln} covered twice — by {owner[ln]!r} and {eid!r}")
                continue
            owner[ln] = eid
        if last > total:
            rep.violations.append(f"entry {eid!r} range ends at {last}, past the file's {total} lines")

    missing = [ln for ln in range(1, total + 1) if ln not in owner]
    if missing:
        rep.violations.append(
            f"{len(missing)} line(s) in no entry — first gap at line {missing[0]} "
            f"(a silently skipped region is the tag failure mode returning)")

    # (2) the declared identity
    indexed = doc.get("lines_indexed")
    if indexed is not None and indexed != rep.lines_total:
        rep.violations.append(f"lines_indexed={indexed} != lines_total={rep.lines_total}")
    covered = len(owner)
    if indexed is not None and indexed != covered:
        rep.violations.append(f"lines_indexed={indexed} but entries actually cover {covered} lines")

    # (5) subdivisions and their records agree — BOTH directions.
    #     Declared-but-absent is a bookkeeping slip; present-but-undeclared is the one that
    #     matters: a synthetic boundary the reader cannot see is precisely the silent
    #     decision D-A18 rule 2 exists to forbid.
    for orig in rep.subdivided:
        parts = [i for i in seen_ids if _split_base(i) == orig]
        if len(parts) < 2:
            rep.violations.append(
                f"subdivided[] names {orig!r} but only {len(parts)} part(s) present — "
                f"a recorded split must be visible in the index")
    for eid in sorted(seen_ids):
        base = _split_base(eid)
        if base and base not in rep.subdivided:
            rep.violations.append(
                f"entry {eid!r} is a synthetic part of {base!r} but {base!r} is not in "
                f"subdivided[] — an unrecorded split is exactly the silent boundary "
                f"D-A18 rule 2 forbids")

    return rep


def check_paths(targets: Sequence[str | Path]) -> list[IndexReport]:
    """Check every extract under the given files/dirs. Directories are scanned for ``*.md``."""
    extracts: list[Path] = []
    for t in targets:
        p = Path(t)
        if p.is_dir():
            extracts.extend(sorted(p.rglob("*.md")))
        elif p.is_file():
            extracts.append(p)
    return [check_index(e) for e in extracts]


def report(reports: Sequence[IndexReport], *, quiet: bool = False) -> bool:
    """Print a per-artifact table; return True iff every index is total."""
    all_ok = True
    for r in reports:
        status = "OK" if r.ok else "FAIL"
        if not quiet or not r.ok:
            extra = f" subdivided={r.subdivided}" if r.subdivided else ""
            print(f"  [{status:4}] {r.extract.name:38} {r.lines_total:>5} lines / "
                  f"{r.entries:>2} entries{extra}")
        for v in r.violations:
            print(f"           - {v}")
        all_ok &= r.ok
    return all_ok


# ──────────────────────────────────────────────────────────────────────────────
# Whole-read decision (D-A18 / FR-SI-03) — lives here because it reads the same config
# ──────────────────────────────────────────────────────────────────────────────
def load_config(repo_root: Path = REPO_ROOT) -> dict:
    """Read ``core/retrieval_config.yaml``. Falls back to the documented defaults."""
    path = repo_root / "core" / "retrieval_config.yaml"
    defaults = {"whole_read_threshold_lines": 500, "max_entry_lines": 25,
                "extract_wrap_columns": 100}
    try:
        import yaml
        loaded = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except (ImportError, OSError):
        return defaults
    return {**defaults, **loaded}


def needs_index_consult(routed_lines: Sequence[int], *, threshold: int) -> bool:
    """Does this routed SET exceed the whole-read budget? (D-A18 / FR-SI-03)

    The check is over the **sum**, deliberately: five 10-page documents are each comfortably
    under threshold but collectively fifty pages, and per-file checking waves the whole set
    through. Under budget → read the extracts whole (the index hop can only *lose*
    information). Over → consult indexes, demoting the largest members first.
    """
    return sum(routed_lines) > threshold


def demote_order(routed: Sequence[tuple[str, int]]) -> list[str]:
    """Order in which to switch a set's members to index-guided retrieval: largest first.

    Largest-first buys the most budget per document demoted, so the fewest documents lose
    their whole-read fidelity. Ties break on name so the order is reproducible.
    """
    return [name for name, _ in sorted(routed, key=lambda kv: (-kv[1], kv[0]))]


# ──────────────────────────────────────────────────────────────────────────────
# Proof (TASK-106). Run: python3 core/scripts/checks/check_index_completeness.py --demo
#   1. the four committed oracles under fixtures/doc_index/ are total (guardrail 7 green);
#   2. each way an index can be incomplete is CAUGHT — a dropped entry (gap), a widened
#      range (overlap), a miscounted total, an unrecorded split, a missing index file;
#   3. the whole-read decision is over the SET, using D-A18's own five-10-page example.
# ──────────────────────────────────────────────────────────────────────────────
def _demo() -> int:
    import copy
    import tempfile

    cfg = load_config()
    corpus = REPO_ROOT / "fixtures" / "doc_index"

    print(f"config: whole_read_threshold_lines={cfg['whole_read_threshold_lines']} "
          f"max_entry_lines={cfg['max_entry_lines']}\n")
    print("guardrail 7 over the committed oracles:")
    reports = check_paths([corpus])
    assert report(reports), "the committed doc-index oracles must be total"
    assert len(reports) == 4, f"expected 4 indexed artifacts, got {len(reports)}"

    # No entry exceeds max_entry_lines — the subdivision rule actually held.
    for r in reports:
        doc = json.loads(index_path_for(r.extract).read_text())
        for e in doc["index"]:
            span = e["lines"][1] - e["lines"][0] + 1
            assert span <= cfg["max_entry_lines"], \
                f"{r.extract.name} entry {e['id']} spans {span} lines > max_entry_lines"
    print(f"  every entry within max_entry_lines={cfg['max_entry_lines']}")

    # Each way an index can lie must be caught.
    good_extract = corpus / "mastercard_mandate_part1_2026.md"
    good_index = json.loads(index_path_for(good_extract).read_text())
    def _drop_entry(d: dict) -> None:
        """Remove one entry AND fix the bookkeeping, so the ONLY remaining signal is the
        hole it leaves. Otherwise the count check would catch it and the gap detector —
        the check that actually matters — would never be exercised."""
        gone = d["index"].pop(4)
        d["entries"] = len(d["index"])
        span = gone["lines"][1] - gone["lines"][0] + 1
        d["lines_indexed"] -= span

    # Each case names the substring that MUST appear, so a mutation cannot pass on an
    # unrelated violation.
    mutations = [
        ("dropped entry (gap)",     _drop_entry,                                       "in no entry"),
        ("widened range (overlap)", lambda d: d["index"][2].__setitem__("lines", [32, 60]), "covered twice"),
        ("miscounted lines_total",  lambda d: d.__setitem__("lines_total", 999),        "lines_total=999"),
        ("unrecorded split",        lambda d: d.__setitem__("subdivided", []),          "not in subdivided[]"),
        ("declared split, no parts", lambda d: d.__setitem__("subdivided", ["9"]),      "only 0 part(s)"),
        ("blank summary",           lambda d: d["index"][1].__setitem__("summary", "  "), "empty summary"),
    ]
    print("\nnegatives (each must be caught, by the RIGHT check):")
    with tempfile.TemporaryDirectory(prefix="doc-index-proof-") as tmp:
        for label, mutate, expect in mutations:
            d = Path(tmp) / "case"
            d.mkdir(exist_ok=True)
            ext = d / good_extract.name
            ext.write_text(good_extract.read_text(encoding="utf-8"), encoding="utf-8")
            bad = copy.deepcopy(good_index)
            mutate(bad)
            index_path_for(ext).write_text(json.dumps(bad), encoding="utf-8")
            r = check_index(ext)
            assert not r.ok, f"{label!r} should have been caught"
            hit = next((v for v in r.violations if expect in v), None)
            assert hit, f"{label!r} caught, but not by {expect!r}: {r.violations}"
            print(f"  {label:26} -> CAUGHT: {hit[:64]}…")

        # An extract with no index at all is a violation, not a skip.
        lone = Path(tmp) / "lone"
        lone.mkdir()
        (lone / "orphan.md").write_text("# no index beside me\n", encoding="utf-8")
        r = check_index(lone / "orphan.md")
        assert not r.ok
        print(f"  {'extract with no index':26} -> CAUGHT: {r.violations[0][:62]}…")

    # The whole-read decision is over the SET (D-A18's own counterexample).
    thr = cfg["whole_read_threshold_lines"]
    five_tens = [180] * 5            # five ~10-page docs: each under, together 900
    assert all(n < thr for n in five_tens), "each member is individually under budget"
    assert needs_index_consult(five_tens, threshold=thr), \
        "the SET is over budget — per-file checking would have waved it through"
    mandate_set = [count_lines(r.extract) for r in reports]
    assert not needs_index_consult(mandate_set, threshold=thr)
    order = demote_order([(r.extract.name, count_lines(r.extract)) for r in reports])
    print(f"\nwhole-read decision (threshold={thr} lines, over the SET):")
    print(f"  five 10-page docs {five_tens} -> sum {sum(five_tens)} -> CONSULT INDEXES "
          f"(each member individually under budget)")
    print(f"  this mock corpus  {mandate_set} -> sum {sum(mandate_set)} -> READ WHOLE "
          f"(indexes built anyway, D-A18 rule 3)")
    print(f"  demotion order if it were over: {order[0]} first (largest)")

    print("\nPASS — four oracles total (guardrail 7); gaps, overlaps, miscounts, unrecorded "
          "splits and missing indexes all caught; whole-read decided over the set.")
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if "--demo" in argv:
        return _demo()
    # Reject unknown flags. argv is a bare path list, so an unrecognised `--flag` was silently
    # treated as a path that matches nothing and dropped — the run still exited 0. A typo'd or
    # renamed flag then looks like a passing check while narrowing what was actually scanned,
    # which is the same misdirection class as a check aimed at the wrong directory (TASK-127).
    unknown = [a for a in argv if a.startswith("-") and a not in ("--demo",)]
    if unknown:
        print(f"unknown option(s): {' '.join(unknown)}", file=sys.stderr)
        print("usage: check_index_completeness.py <dir-or-extract> [...] | --demo", file=sys.stderr)
        return 2
    if not argv:
        print(__doc__.strip().splitlines()[0], file=sys.stderr)
        print("usage: check_index_completeness.py <dir-or-extract> [...] | --demo",
              file=sys.stderr)
        return 2
    reports = check_paths(argv)
    if not reports:
        print("no .md extracts found under the given paths", file=sys.stderr)
        return 2
    print("index completeness (guardrail 7, D-A18):")
    ok = report(reports)
    if not ok:
        n = sum(1 for r in reports if not r.ok)
        print(f"\nINDEX COMPLETENESS FAILED — {n}/{len(reports)} artifact(s) incomplete.",
              file=sys.stderr)
        return 1
    print(f"\nOK — all {len(reports)} index(es) total.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
