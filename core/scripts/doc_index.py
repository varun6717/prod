#!/usr/bin/env python3
"""doc_index.py — derive an index's STRUCTURE deterministically (D-A18, amended TASK-127).

An index entry is `{id, heading, lines, summary}`. Three of those four are **facts about the
extract** — where a heading is, what it says, which lines it owns — and one is judgment. Until now
a model produced all four.

That was backwards in the one place it matters. **A wrong line range is invisible.** A wrong
summary is visible the moment anyone reads it against the section, but a range that is off by a few
lines sends the author to the wrong text with no signal at all — and `lines` is exactly what the
author pulls by. So the field with no error signal was the one being guessed, while the field a
reader can check was the one being computed. This module inverts that: structure is derived here,
and the model supplies **only the summary**.

*(Raised by V on the Jira lane — the connector already knows every heading's line range at render
time, so re-deriving it with a model is waste plus a hallucination surface. It generalises: the
same is true of every extract, because the headings are in the text.)*

Determinism also buys **guardrail 7 by construction**. Every line lands in exactly one entry
because the ranges are computed as a partition, not asserted and then checked. `verify()` still
checks it — but it now confirms an invariant rather than catching a mistake.

What stays the model's, and why: a summary must carry *the specifics a heading cannot* ("PAN ranges
cannot distinguish co-badged products; cites 2026 dispute volumes"), so that the author can choose
without reading. No amount of structure derivation produces that.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

_HEAD = re.compile(r"^(#{1,6})\s+(.*\S)\s*$")
# A heading that numbers itself owns that number as its id — "## 3. Brand Rules" → "3",
# "### 3.1 MDES Token Handling" → "3.1". Ids are stable across re-extraction that way, where an
# ordinal would shift the moment a section is inserted above.
_NUMBERED = re.compile(r"^(\d+(?:\.\d+)*)\.?\s+\S")

DEFAULT_MAX_ENTRY_LINES = 25          # core/retrieval_config.yaml: max_entry_lines


def _config(repo_root: Path | None = None) -> dict:
    """Read `retrieval_config.yaml` — the tunables are data, never hardcoded (D-A18)."""
    root = repo_root or Path(__file__).resolve().parents[1]
    p = root / "retrieval_config.yaml"
    if not p.is_file():
        return {"max_entry_lines": DEFAULT_MAX_ENTRY_LINES}
    import yaml
    return yaml.safe_load(p.read_text(encoding="utf-8")) or {}


def _heading_id(text: str, ordinal: int) -> str:
    m = _NUMBERED.match(text)
    return m.group(1) if m else str(ordinal)


def _seam(lines: list[str], lo: int, hi: int, target: int, min_part: int) -> int:
    """Pick a split point at a CONTENT seam near ``target`` (1-based, inclusive bounds).

    A blank line is the seam a document offers; splitting mid-paragraph or mid-table-row produces
    a boundary no reader would recognise, and D-A18 rule 2 requires synthetic boundaries to be
    auditable — which they cannot be if they land arbitrarily.

    **But a seam must leave both sides usable.** Preferring the nearest blank outright produced a
    one-line part: a dense table's only blank line is the one right after its heading, so the
    "nearest" seam sat at the very start of the span and left the remainder still over the limit —
    subdividing in name only. Candidates are therefore restricted to those leaving at least
    ``min_part`` lines on each side, and only if none qualifies does it cut at ``target``, which
    always splits evenly even if it lands mid-paragraph.
    """
    blanks = [n for n in range(lo, hi)
              if not lines[n - 1].strip() and n - lo + 1 >= min_part and hi - n >= min_part]
    return min(blanks, key=lambda n: abs(n - target)) if blanks else target


def derive_structure(extract: str | Path, *, max_entry_lines: int | None = None) -> dict:
    """Extract → the index's structural skeleton. Deterministic; no model, no summaries.

    Returns the D-A18 shape minus `summary` on each entry (and minus `path`/`disposition`, which
    the caller supplies): ``{lines_total, entries, subdivided, index: [{id, heading, lines}]}``.
    """
    p = Path(extract)
    text = p.read_text(encoding="utf-8")
    lines = text.splitlines()
    total = len(lines)
    limit = max_entry_lines or _config().get("max_entry_lines", DEFAULT_MAX_ENTRY_LINES)

    heads = [(n, m.group(2), len(m.group(1)))
             for n, l in enumerate(lines, 1) if (m := _HEAD.match(l))]
    spans: list[tuple[str, str, int, int]] = []

    if not heads:
        # No headings at all — one entry over the whole file rather than none. An extract with no
        # structure is still fully citable, and dropping it would break exactly-once coverage.
        if total:
            spans.append(("0", p.stem, 1, total))
    else:
        first_line, first_title, first_level = heads[0][0], heads[0][1], heads[0][2]
        if first_line > 1:
            # Front matter is always id "0" (D-A18): title block, cover, anything before the
            # first heading. It is content, and it has to belong somewhere.
            spans.append(("0", "Front matter", 1, first_line - 1))

        # A leading level-1 heading is the DOCUMENT TITLE, not a section, so it is front matter
        # too and takes id "0". Treating it as an ordinary heading gave it ordinal "1" — which
        # collided head-on with "## 1. Mandate Summary" claiming "1" from its own numbering, and
        # a duplicate id silently makes one of two entries unreachable by reference.
        title_is_front = (first_line == 1 and first_level == 1 and len(heads) > 1)
        body = heads[1:] if title_is_front else heads
        if title_is_front:
            spans.append(("0", first_title, 1, heads[1][0] - 1))
        for i, (start, text, _lvl) in enumerate(body):
            end = body[i + 1][0] - 1 if i + 1 < len(body) else total
            spans.append((_heading_id(text, i + 1), text, start, end))

    index, subdivided = [], []
    for hid, title, start, end in spans:
        span = end - start + 1
        if span <= limit:
            index.append({"id": hid, "heading": title, "lines": [start, end]})
            continue
        # Too coarse to be a selection unit — subdivide at content seams. Parts take a lowercase
        # letter suffix (D-A18 rule 2), which is what lets a checker reconcile them against
        # `subdivided[]` in both directions; a dotted id would read as deeper nesting instead.
        parts = -(-span // limit)
        step = -(-span // parts)
        min_part = max(3, limit // 3)      # a part below this is not a selection unit
        cuts, cur = [], start
        for k in range(1, parts):
            target = min(start + k * step, end)
            cut = _seam(lines, cur + 1, end, target, min_part)
            if cut > cur:
                cuts.append(cut)
                cur = cut
        bounds = [start] + cuts + [end + 1]
        made = []
        for k in range(len(bounds) - 1):
            a, b = bounds[k], bounds[k + 1] - 1
            if a > b:
                continue
            made.append({"id": f"{hid}{chr(ord('a') + len(made))}", "heading": title,
                         "lines": [a, b]})
        if len(made) > 1:
            subdivided.append(hid)
            index.extend(made)
        else:
            index.append({"id": hid, "heading": title, "lines": [start, end]})

    out = {"lines_total": total, "entries": len(index), "index": index}
    if subdivided:
        out["subdivided"] = subdivided
    return out


def verify(structure: dict) -> list[str]:
    """Guardrail 7 over a derived structure. Should always pass — it confirms, not catches."""
    total, seen, errs = structure["lines_total"], {}, []
    for e in structure["index"]:
        a, b = e["lines"]
        if a > b:
            errs.append(f"{e['id']}: inverted range {a}..{b}")
        for n in range(a, b + 1):
            if n in seen:
                errs.append(f"line {n} in both {seen[n]} and {e['id']}")
            seen[n] = e["id"]
    ids = [e["id"] for e in structure["index"]]
    dupes = sorted({i for i in ids if ids.count(i) > 1})
    if dupes:
        errs.append(f"duplicate entry id(s) {dupes} — an id must address exactly one range")
    missing = [n for n in range(1, total + 1) if n not in seen]
    if missing:
        errs.append(f"{len(missing)} line(s) in no entry, first at {missing[0]}")
    if any(n > total for n in seen):
        errs.append("an entry runs past EOF")
    return errs


def build(extract: str | Path, *, disposition: list[str], summaries: dict[str, str] | None = None,
          max_entry_lines: int | None = None) -> dict:
    """The full D-A18 index. ``summaries`` maps entry id → the model's summary for it.

    A missing summary becomes an explicit marker rather than an empty string: an unwritten summary
    and a summary that says nothing must not look the same to the author choosing from the index.
    """
    s = derive_structure(extract, max_entry_lines=max_entry_lines)
    errs = verify(s)
    if errs:                                          # a derived partition failing is a real bug
        raise AssertionError(f"derived structure violates guardrail 7: {errs}")
    summaries = summaries or {}
    doc = {"path": str(extract), "disposition": list(disposition),
           "lines_total": s["lines_total"], "lines_indexed": s["lines_total"],
           "entries": s["entries"]}
    if "subdivided" in s:
        doc["subdivided"] = s["subdivided"]
    doc["index"] = [{**e, "summary": summaries.get(e["id"], "[TBD — summary not written]")}
                    for e in s["index"]]
    return doc


def main(argv: list[str] | None = None) -> int:
    import argparse
    ap = argparse.ArgumentParser(
        description="Derive an index's structure from an extract (D-A18). Summaries are the "
                    "model's; everything else is computed here.")
    ap.add_argument("extract", help="path to the <doc>.md structural extract")
    ap.add_argument("--max-entry-lines", type=int, help="override retrieval_config")
    ap.add_argument("--json", action="store_true", help="emit the structure as JSON")
    args = ap.parse_args(argv)

    if not Path(args.extract).is_file():
        print(f"doc_index.py: no such extract: {args.extract}", file=sys.stderr)
        return 2
    s = derive_structure(args.extract, max_entry_lines=args.max_entry_lines)
    errs = verify(s)
    if args.json:
        print(json.dumps(s, indent=2, ensure_ascii=False))
    else:
        print(f"{args.extract}: {s['lines_total']} lines / {s['entries']} entries"
              + (f"  subdivided={s['subdivided']}" if "subdivided" in s else ""))
        for e in s["index"]:
            print(f"  {e['id']:<6} {e['lines'][0]:>4}-{e['lines'][1]:<4} {e['heading'][:60]}")
    if errs:
        print("GUARDRAIL 7 VIOLATED: " + "; ".join(errs), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
