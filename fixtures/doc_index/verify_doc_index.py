#!/usr/bin/env python3
"""verify_doc_index.py — the D-A18 per-artifact index proven against the mock corpus (TASK-106).

Four artifacts, each an extract + its index (the D-A18 two-file pairing):

  mastercard_mandate_part1_2026.{md,index.json}   business_requirement    138 lines, 13 entries
  mastercard_mandate_part2_2026.{md,index.json}   technical_specification 146 lines, 17 entries
  discover_routing_kb.{md,index.json}             product_domain_knowledge 26 lines,  5 entries
  message_format_kb.{md,index.json}               product_domain_knowledge 14 lines,  3 entries

The `.md` files are what `pdf_extract` produces. The mandate pair was transcribed from the real
fixture PDFs (no PDF tooling exists on this box, but the PDFs are generated deterministically by
`fixtures/pdf/gen_fixtures.py`, whose literal strings ARE the page text); the KB pair from the
Confluence HTML fixtures. The `.index.json` files are the ORACLES — what a correct `doc_index`
pass should produce for them.

What is checked here (guardrail 7 lives in the checker; this proves the corpus and the properties
the design rests on):

  1. every artifact has an index and it is TOTAL          → the density claim holds
  2. the degraded case is real, and recorded               → D-A18 rule 2
  3. no entry names a destination                          → D-A18 rule 4 (tags stayed dead)
  4. summaries carry specifics, not restated headings      → why summaries beat headings-only
  5. `disposition` is a list, matching the manifest        → D-A12 typing, one shape everywhere
  6. the whole-read decision is over the SET               → FR-SI-03

Run: python3 fixtures/doc_index/verify_doc_index.py
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_REPO_ROOT = _HERE.parents[1]
sys.path.insert(0, str(_REPO_ROOT / "core" / "scripts" / "checks"))

from check_index_completeness import (  # noqa: E402
    check_paths, count_lines, index_path_for, load_config, needs_index_consult, report,
)

_FAILURES: list[str] = []


def _check(label: str, ok: bool, detail: str = "") -> None:
    print(f"  [{'PASS' if ok else 'FAIL'}] {label}" + (f" — {detail}" if detail else ""))
    if not ok:
        _FAILURES.append(label)


def main() -> int:
    cfg = load_config(_REPO_ROOT)
    extracts = sorted(_HERE.glob("*.md"))
    indexes = {p: json.loads(index_path_for(p).read_text(encoding="utf-8")) for p in extracts}

    print("verify_doc_index — D-A18 per-artifact index over the mock corpus\n")

    # 1) Guardrail 7 — the property everything else rests on.
    print("1) guardrail 7 — every index total (lines_total == lines_indexed, exactly-once):")
    reports = check_paths([_HERE])
    _check("all four indexes total", report(reports, quiet=True) and len(reports) == 4,
           f"{len(reports)} artifacts")

    # 2) The degraded case — a real heading-less run, split at content seams, RECORDED.
    print("\n2) degraded case (flat prose, no sub-headings → synthesised boundaries):")
    p1 = _HERE / "mastercard_mandate_part1_2026.md"
    doc1 = indexes[p1]
    _check("part 1 §4 recorded as subdivided", doc1["subdivided"] == ["4"],
           f"subdivided={doc1['subdivided']}")
    parts = [e for e in doc1["index"] if re.fullmatch(r"4[a-z]", e["id"])]
    _check("§4 split into ≥3 parts", len(parts) >= 3,
           ", ".join(e["id"] for e in parts))
    src = p1.read_text(encoding="utf-8").splitlines()
    first, last = parts[0]["lines"][0], parts[-1]["lines"][1]
    inner = src[first:last]                       # everything after the "## 4." heading line
    _check("the split region genuinely has NO sub-headings to key on",
           not any(ln.startswith("#") for ln in inner),
           "boundaries had to be synthesised from paragraph groups")
    _check("parts are contiguous and cover the whole region",
           all(parts[i]["lines"][1] + 1 == parts[i + 1]["lines"][0] for i in range(len(parts) - 1)),
           f"lines {first}–{last}")
    # every part stays within the granularity budget the split existed to satisfy
    _check("each part within max_entry_lines",
           all(e["lines"][1] - e["lines"][0] + 1 <= cfg["max_entry_lines"] for e in parts),
           f"max_entry_lines={cfg['max_entry_lines']}")

    # 3) Rule 4 — the index describes the document, never the destination.
    print("\n3) rule 4 — no entry names a destination (tags stayed dead):")
    destination_words = re.compile(
        r"\b(feeds?|routes? to|relevant to|belongs in|maps? to)\b.{0,20}"
        r"(§|section \d|business.requirement|technical.specification)", re.I)
    offenders = [(p.name, e["id"]) for p, d in indexes.items() for e in d["index"]
                 if destination_words.search(e["summary"])]
    _check("no summary states where it should land", not offenders, str(offenders[:3]))
    # a bare "§n" reference is also a destination claim
    section_refs = [(p.name, e["id"]) for p, d in indexes.items() for e in d["index"]
                    if re.search(r"§\s*\d", e["summary"])]
    _check("no summary cites an SI section number", not section_refs, str(section_refs[:3]))

    # 4) Summaries carry specifics — the whole reason headings-alone was rejected.
    print("\n4) summaries carry specifics a heading cannot:")
    thin = []
    for p, d in indexes.items():
        for e in d["index"]:
            words = e["summary"].split()
            head_words = {w.lower().strip(".,—") for w in e["heading"].split()}
            novel = [w for w in words if w.lower().strip(".,—") not in head_words]
            if len(words) < 8 or len(novel) < 6:
                thin.append(f"{p.name}:{e['id']}")
    _check("no summary merely restates its heading", not thin, str(thin[:3]))
    # the mandate indexes must name concrete identifiers — that is what selection matches on
    mandate_text = " ".join(e["summary"] for p, d in indexes.items()
                            for e in d["index"] if "mandate" in p.name)
    for token in ("DE 48.66", "DE 48.78", "MCS-2026-R3", "2026-09-30", "RC 55", "MCB-MDES-01"):
        _check(f"identifier {token!r} appears in a summary", token in mandate_text)

    # 5) D-A12 typing — one disposition shape everywhere.
    print("\n5) disposition typing (list, per D-A12 — not D-A18's illustrative string):")
    bad_type = [p.name for p, d in indexes.items() if not isinstance(d.get("disposition"), list)]
    _check("every index carries `disposition` as a list", not bad_type, str(bad_type))
    _check("mandate parts split business_requirement / technical_specification",
           indexes[p1]["disposition"] == ["business_requirement"]
           and indexes[_HERE / "mastercard_mandate_part2_2026.md"]["disposition"]
           == ["technical_specification"])

    # 6) FR-SI-03 — the whole-read check is over the routed SET.
    print("\n6) whole-read decision over the routed SET (FR-SI-03):")
    thr = cfg["whole_read_threshold_lines"]
    sizes = [count_lines(p) for p in extracts]
    _check("this corpus reads whole", not needs_index_consult(sizes, threshold=thr),
           f"sum {sum(sizes)} ≤ {thr} — indexes still built (rule 3)")
    each_under = [180] * 5
    _check("a set of individually-small docs still trips the threshold",
           all(n < thr for n in each_under) and needs_index_consult(each_under, threshold=thr),
           f"5 × 180 = {sum(each_under)} > {thr}; per-file checking would have waved it through")

    print()
    if _FAILURES:
        print(f"FAILED — {len(_FAILURES)} check(s): {_FAILURES}", file=sys.stderr)
        return 1
    print("PASS — four indexes total; the degraded case is real, split at content seams and "
          "recorded; no entry names a destination; summaries carry identifiers; disposition is a "
          "list; whole-read decided over the set.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
