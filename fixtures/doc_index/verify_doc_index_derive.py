#!/usr/bin/env python3
"""verify_doc_index_derive.py — the index's STRUCTURE is derived, not guessed (D-A18, TASK-127).

An index entry is `{id, heading, lines, summary}`. Three of those are facts about the extract; one
is judgment. A model used to produce all four — and that was backwards in the one place it matters:
**a wrong line range is invisible.** A wrong summary is caught the moment someone reads it against
the section; a range off by a few lines silently sends the author to the wrong text. So the field
with no error signal was the guessed one.

  1. **Guardrail 7 holds BY CONSTRUCTION** — the ranges are computed as a partition, so exactly-once
     coverage is a property of the algorithm rather than something asserted and then checked.
  2. **Ids are stable and unique.** A self-numbered heading owns its number; ordinals would shift
     the moment a section is inserted above. The document title is front matter (`0`), not a
     section — treating it as one collided with a `## 1.` heading claiming `1`.
  3. **Subdivision produces usable parts**, at content seams, with letter suffixes recorded in
     `subdivided[]`.
  4. **Determinism** — same input, same output, every time.

Run: python3 fixtures/doc_index/verify_doc_index_derive.py
"""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_REPO_ROOT = _HERE.parents[1]
sys.path.insert(0, str(_REPO_ROOT / "core" / "scripts"))

import doc_index as D  # noqa: E402

_FAILURES: list[str] = []


def _check(label: str, ok: bool, detail: str = "") -> None:
    print(f"  [{'PASS' if ok else 'FAIL'}] {label}" + (f" — {detail}" if detail else ""))
    if not ok:
        _FAILURES.append(label)


DOC = """# Mandate MCS-2026-R3 — Part 1

Version 1.2 | Approved-Final
Compliance deadline 2026-09-30

## 1. Mandate Summary

Binding on all licensed acquirers.
Supersedes MCS-2024-R7.

## 2. Scope

In scope: Mastercard Credit, Debit, Maestro.

### 2.1 BIN ranges

""" + "\n".join(f"row {i}: 5{i:05d}-5{i:05d}9  in scope" for i in range(40)) + """

## 3. References

Mastercard Rules, April 2026.
"""


def main() -> int:
    print("verify_doc_index_derive — structure is computed, only the summary is judged\n")
    with tempfile.TemporaryDirectory(prefix="doc-index-") as td:
        p = Path(td) / "mandate.md"
        p.write_text(DOC, encoding="utf-8")
        total = len(DOC.splitlines())

        s = D.derive_structure(p, max_entry_lines=25)
        print("1) guardrail 7 holds by construction:")
        _check("no violations at all", not D.verify(s), str(D.verify(s)[:2]))
        covered = sorted(n for e in s["index"] for n in range(e["lines"][0], e["lines"][1] + 1))
        _check(f"every one of the {total} lines is covered", covered == list(range(1, total + 1)))
        _check("and covered EXACTLY once", len(covered) == len(set(covered)))
        _check("lines_total matches the file", s["lines_total"] == total)
        _check("entries matches the index length", s["entries"] == len(s["index"]))

        print("\n2) ids are stable and unique:")
        ids = [e["id"] for e in s["index"]]
        _check("no duplicate ids", len(ids) == len(set(ids)), str(ids))
        _check("the document title is front matter, id '0', NOT ordinal '1'",
               s["index"][0]["id"] == "0" and s["index"][0]["lines"][0] == 1,
               "an ordinal title collides with '## 1.' claiming its own number")
        _check("a self-numbered heading owns its number",
               {"1", "2", "3"} <= set(ids), str(ids))
        _check("a nested self-numbered heading keeps its dotted id",
               any(i.startswith("2.1") for i in ids), str(ids))
        _check("ranges are in document order",
               all(s["index"][i]["lines"][1] < s["index"][i + 1]["lines"][0]
                   for i in range(len(s["index"]) - 1)))

        print("\n3) subdivision produces USABLE parts:")
        _check("the oversized section was subdivided", s.get("subdivided") == ["2.1"],
               str(s.get("subdivided")))
        parts = [e for e in s["index"] if e["id"].startswith("2.1")]
        _check("into ≥2 parts with letter suffixes",
               len(parts) >= 2 and all(e["id"][-1].isalpha() for e in parts),
               str([e["id"] for e in parts]))
        sizes = [e["lines"][1] - e["lines"][0] + 1 for e in parts]
        _check("no part is a sliver — a 1-line part is subdividing in name only",
               min(sizes) >= 3, f"sizes {sizes}")
        _check("and the parts are balanced rather than one-and-a-remainder",
               max(sizes) - min(sizes) <= 25, f"sizes {sizes}")
        big = [e["id"] for e in s["index"]
               if e["lines"][1] - e["lines"][0] + 1 > 25 and not e["id"][-1].isalpha()]
        _check("nothing over the limit survives unsplit", not big, str(big))

        print("\n4) it is deterministic:")
        _check("same input → identical output", D.derive_structure(p, max_entry_lines=25) == s)

        print("\n5) the model supplies ONLY summaries:")
        doc = D.build(p, disposition=["business_requirement"], summaries={"1": "What it binds."})
        _check("build() returns the full D-A18 shape",
               {"path", "disposition", "lines_total", "lines_indexed", "entries", "index"}
               <= set(doc))
        _check("lines_indexed == lines_total", doc["lines_indexed"] == doc["lines_total"])
        e1 = next(e for e in doc["index"] if e["id"] == "1")
        _check("a supplied summary is used", e1["summary"] == "What it binds.")
        missing = next(e for e in doc["index"] if e["id"] == "0")
        _check("a MISSING summary is marked, not left blank",
               "[TBD" in missing["summary"],
               "an unwritten summary and one that says nothing must not look alike")

        print("\n6) degenerate inputs do not break coverage:")
        flat = Path(td) / "flat.md"
        flat.write_text("no headings at all\njust two lines\n", encoding="utf-8")
        fs = D.derive_structure(flat)
        _check("an extract with NO headings still yields one covering entry",
               len(fs["index"]) == 1 and not D.verify(fs),
               "dropping it would break exactly-once coverage")

    print()
    if _FAILURES:
        print(f"FAILED — {len(_FAILURES)} check(s): {_FAILURES}", file=sys.stderr)
        return 1
    print("PASS — structure is a computed partition (guardrail 7 by construction), ids are stable "
          "and unique, subdivision yields usable parts at seams, and the model is left only the "
          "one field a reader can actually check.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
