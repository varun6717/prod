#!/usr/bin/env python3
"""verify_si_author.py — TASK-109 proof: the authored v1 satisfies the SI contract.

`v1.md` here is the output of running `core/skills/solution_intent_author.skill.md` in-session
over the mock corpus (2 mandate PDFs + 2 Confluence KB pages + the Stratus repo, dispositioned
per `UI_INPUT.yaml`). This script is the acceptance check on that output.

The corpus is assembled at verify time from `fixtures/doc_index/` — the single source of truth
for the extracts and their indexes — into a temp `context_set/`, and `merge_manifest.py` fans it
in for real. So the manifest this checks citations against is produced by the actual pipeline,
not hand-written, and the extracts cannot drift from the doc-index oracles.

What it checks:

  1. **All 18 sections present**, in order, none missing (D11.1's fixed contract).
  2. **Conditional sections dispositioned** — filled, or "Not applicable — <reason>" (D-A10);
     never simply absent.
  3. **§16/§18 are v2-only stubs** — present so the shape is visible, but not authored.
  4. **§7 precedes §8**, and every §8 requirement carries a `Deliverable:` pointing at a real
     §7 ID (D-A14's load-bearing trace — it builds the Jira hierarchy).
  5. **Stable IDs + enumerated assertions** — `R<n>` unique and sequential, `R<n>.<m>` numbered
     within their requirement (FR-SI-04/05).
  6. **Per-section coverage footers** with one entry per profile `must_capture`, valued from
     {source, frame, operator, open}.
  7. **CITATION SPOT-CHECK** — every `[src: <path> L<a>–<b>]` resolves: the path is a manifest
     entry, and the line range exists in that entry's extract. This is the check that separates
     a grounded document from a plausible one.
  8. **Cite-or-flag closes** — every `open` coverage entry has a matching §17 open question, and
     every `[TBD — unsourced]` appears in a section whose footer records an `open`.
  9. **Code-blind (FR-SI-02)** — v1 cites no repository path and no code map, even though the
     corpus contains a `codebase` source.
 10. **§15 → §4 traces** both ways (D-A11's mechanical guardrail).

Run: python3 fixtures/si_author/verify_si_author.py
"""
from __future__ import annotations

import json
import re
import shutil
import sys
import tempfile
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_REPO_ROOT = _HERE.parents[1]
sys.path.insert(0, str(_REPO_ROOT / "core" / "scripts"))

import merge_manifest  # noqa: E402
import yaml  # noqa: E402

_DOC_FIXTURES = _REPO_ROOT / "fixtures" / "doc_index"
_V1 = _HERE / "v1.md"
_UI_INPUT = _HERE / "UI_INPUT.yaml"
_PROFILE = _REPO_ROOT / "core" / "profiles" / "payment_brand" / "si_profile.payment_brand.yaml"

# corpus artifact -> (logical source, disposition) — mirrors UI_INPUT.yaml's sources[]
_CORPUS = {
    "mastercard_mandate_part1_2026": ("sharepoint", ["business_requirement"]),
    "mastercard_mandate_part2_2026": ("sharepoint", ["technical_specification"]),
    "discover_routing_kb":           ("confluence", ["product_domain_knowledge"]),
    "message_format_kb":             ("confluence", ["product_domain_knowledge"]),
}

_CITE = re.compile(r"\[src:\s*([^\]\s]+)\s+L(\d+)[–-](\d+)\]")
_COVERAGE = re.compile(r"<!--\s*coverage:\s*\{(.*?)\}\s*-->", re.S)
_COVERAGE_VALUES = {"source", "frame", "operator", "open"}

_FAILURES: list[str] = []


def _check(label: str, ok: bool, detail: str = "") -> None:
    print(f"  [{'PASS' if ok else 'FAIL'}] {label}" + (f" — {detail}" if detail else ""))
    if not ok:
        _FAILURES.append(label)


def _build_corpus(root: Path) -> dict:
    """Assemble a real context_set from the doc-index fixtures and fan it in with merge_manifest."""
    cs = root / "context_set"
    slices: dict[str, dict] = {}
    for stem, (source, disposition) in _CORPUS.items():
        d = cs / source
        d.mkdir(parents=True, exist_ok=True)
        shutil.copy2(_DOC_FIXTURES / f"{stem}.md", d / f"{stem}.md")
        shutil.copy2(_DOC_FIXTURES / f"{stem}.index.json", d / f"{stem}.index.json")
        slices.setdefault(source, {"source": source, "status": "ok",
                                   "domain": "payment_brand", "files": []})
        slices[source]["files"].append({
            "path": f"context_set/{source}/{stem}.md",
            "source": source,
            "url": f"https://example.invalid/{stem}",
            "ingest_ts": "2026-08-01T09:00:00Z",
            "adapter": "pdf_extract",
            "disposition": disposition,
            "descriptor": f"{stem} extract",
            "index_path": f"context_set/{source}/{stem}.index.json",
        })
    # the code source contributes no doc entries — and must contribute nothing to v1 at all
    slices["bitbucket"] = {"source": "bitbucket", "status": "ok", "files": [],
                           "note": "code_map built"}
    for source, data in slices.items():
        (cs / source).mkdir(parents=True, exist_ok=True)
        (cs / source / "_slice.json").write_text(json.dumps(data), encoding="utf-8")
    loaded = [merge_manifest.load_slice(p) for p in merge_manifest.discover_slices(cs)]
    index = merge_manifest.merge(loaded, run_id="r-2026-08-01-si1")
    (cs / "index.json").write_text(merge_manifest.dumps(index), encoding="utf-8")
    return index


def main() -> int:
    v1 = _V1.read_text(encoding="utf-8")
    profile = yaml.safe_load(_PROFILE.read_text(encoding="utf-8"))
    ui = yaml.safe_load(_UI_INPUT.read_text(encoding="utf-8"))
    by_id = {s["id"]: s for s in profile["sections"]}

    print("verify_si_author — the authored v1 against the SI contract\n")

    with tempfile.TemporaryDirectory(prefix="si-author-") as td:
        root = Path(td)
        index = _build_corpus(root)
        entries = {e["path"]: e for e in index["files"]}

        # 1) All 18 sections, in order.
        print("1) the fixed 18-section contract (D11.1):")
        heads = re.findall(r"^## (\d+)\. (.+)$", v1, re.M)
        got = [int(n) for n, _ in heads]
        _check("all 18 sections present, in order", got == list(range(1, 19)), f"got {got}")
        titles_ok = [n for n, t in heads if by_id[int(n)]["title"].split(" (")[0].lower() not in t.lower()]
        _check("each heading matches the profile title", not titles_ok, f"mismatched §{titles_ok}")

        # 2) Conditional sections dispositioned, never absent.
        print("\n2) conditional sections dispositioned (D-A10 / FR-SI-06):")
        bodies = {}
        for i, (n, _) in enumerate(heads):
            start = v1.index(f"## {n}. ")
            end = v1.index(f"## {heads[i+1][0]}. ") if i + 1 < len(heads) else len(v1)
            bodies[int(n)] = v1[start:end]
        conditional = [i for i, s in by_id.items() if s["status"] == "conditional"]
        for sid in conditional:
            body = bodies[sid]
            na = "Not applicable —" in body
            filled = len(body.strip().splitlines()) > 4
            _check(f"§{sid} is filled or explicitly N/A with a reason", na or filled,
                   "N/A + reason" if na else "filled")
        na_sections = [s for s in conditional if "Not applicable —" in bodies[s]]
        _check("at least one conditional is N/A and one is filled (both states exercised)",
               0 < len(na_sections) < len(conditional), f"N/A: §{na_sections}")

        # 3) v2-only sections are stubs, not authored.
        print("\n3) §16/§18 are v2-only stubs:")
        for sid in (16, 18):
            _check(f"§{sid} present as a stub naming what will fill it",
                   "enrichment" in bodies[sid].lower() and "v2" in bodies[sid].lower())
            _check(f"§{sid} carries no coverage footer (nothing authored to cover)",
                   not _COVERAGE.search(bodies[sid]))

        # 4) §7 before §8; every requirement traces to a real deliverable.
        print("\n4) §7 → §8 trace (D-A14, load-bearing — it builds the Jira hierarchy):")
        _check("§7 precedes §8", v1.index("## 7. ") < v1.index("## 8. "))
        deliverables = set(re.findall(r"\*\*(D\d+)\*\*", bodies[7]))
        _check("§7 declares stable deliverable IDs", len(deliverables) >= 3, str(sorted(deliverables)))
        reqs = re.findall(r"^#### (R\d+) — (.+)$", bodies[8], re.M)
        req_ids = [r for r, _ in reqs]
        _check("§8 declares stable requirement IDs", len(req_ids) >= 5, str(req_ids))
        _check("requirement IDs are unique", len(req_ids) == len(set(req_ids)))
        _check("requirement IDs are sequential from R1",
               req_ids == [f"R{i}" for i in range(1, len(req_ids) + 1)])
        blocks = re.split(r"^#### ", bodies[8], flags=re.M)[1:]
        no_deliv, bad_deliv = [], []
        for b in blocks:
            rid = b.split(" —")[0]
            m = re.search(r"\*\*Deliverable:\*\*\s*(D\d+)", b)
            if not m:
                no_deliv.append(rid)
            elif m.group(1) not in deliverables:
                bad_deliv.append(f"{rid}→{m.group(1)}")
        _check("every requirement carries a Deliverable:", not no_deliv, str(no_deliv))
        _check("every Deliverable: names a real §7 ID", not bad_deliv, str(bad_deliv))
        used = {re.search(r"\*\*Deliverable:\*\*\s*(D\d+)", b).group(1) for b in blocks
                if re.search(r"\*\*Deliverable:\*\*\s*(D\d+)", b)}
        _check("no deliverable is unjustified (every D has ≥1 requirement)",
               deliverables <= used, f"unused: {sorted(deliverables - used)}")

        # 5) Enumerated assertions per requirement.
        print("\n5) enumerated assertions — the checkable units (FR-SI-04):")
        thin = []
        for b in blocks:
            rid = b.split(" —")[0]
            asserts = re.findall(rf"^- ({re.escape(rid)}\.\d+) — ", b, re.M)
            if len(asserts) < 2:
                thin.append(f"{rid}({len(asserts)})")
            expected = [f"{rid}.{i}" for i in range(1, len(asserts) + 1)]
            if asserts != expected:
                thin.append(f"{rid} misnumbered")
        _check("every requirement enumerates ≥2 numbered assertions", not thin, str(thin))
        total_assertions = len(re.findall(r"^- R\d+\.\d+ — ", bodies[8], re.M))
        _check("the assertion set is substantial", total_assertions >= 20, f"{total_assertions} assertions")

        # 6) Coverage footers, one entry per must_capture.
        print("\n6) per-section coverage footers:")
        missing_footer, wrong_len, bad_val = [], [], []
        for sid, s in by_id.items():
            if sid in (16, 18):
                continue
            m = _COVERAGE.search(bodies[sid])
            if not m:
                missing_footer.append(sid)
                continue
            pairs = dict(p.split(":") for p in m.group(1).split(","))
            vals = {v.strip() for v in pairs.values()}
            if len(pairs) != len(s["must_capture"]):
                wrong_len.append(f"§{sid}: {len(pairs)} vs {len(s['must_capture'])} must_capture")
            if not vals <= _COVERAGE_VALUES:
                bad_val.append(f"§{sid}: {vals - _COVERAGE_VALUES}")
        _check("every authored section carries a footer", not missing_footer, str(missing_footer))
        _check("each footer has one entry per must_capture", not wrong_len, "; ".join(wrong_len))
        _check("footer values are source/frame/operator/open", not bad_val, "; ".join(bad_val))

        # 7) THE citation spot-check.
        print("\n7) citation spot-check — every [src:] resolves to a real line range:")
        cites = _CITE.findall(v1)
        _check("v1 carries citations", len(cites) >= 40, f"{len(cites)} source citations")
        unknown_path, bad_range = [], []
        for path, a, b in cites:
            if path not in entries:
                unknown_path.append(path)
                continue
            extract = root / path
            n_lines = len(extract.read_text(encoding="utf-8").splitlines())
            lo, hi = int(a), int(b)
            if not (1 <= lo <= hi <= n_lines):
                bad_range.append(f"{path} L{lo}–{hi} (file has {n_lines} lines)")
        _check("every cited path is a manifest entry", not unknown_path,
               str(sorted(set(unknown_path))))
        _check("every cited line range exists in its extract", not bad_range,
               "; ".join(bad_range[:3]))
        # and the citations actually spread across the corpus rather than leaning on one doc
        cited_docs = {p for p, _, _ in cites}
        _check("citations span the whole routed corpus", len(cited_docs) == 4,
               f"{len(cited_docs)}/4 artifacts cited")

        # 8) Cite-or-flag closes into §17.
        print("\n8) cite-or-flag closes — gaps are surfaced, not swallowed:")
        open_sections = [sid for sid in bodies if sid not in (16, 18)
                         and (m := _COVERAGE.search(bodies[sid]))
                         and "open" in m.group(1)]
        _check("some section records an `open` gap (the corpus does not answer everything)",
               bool(open_sections), f"§{open_sections}")
        q_count = len(re.findall(r"^- \*\*Q\d+", bodies[17], re.M))
        _check("§17 lists open questions", q_count >= len(open_sections), f"{q_count} questions")
        tbds = re.findall(r"\[TBD — unsourced\]", v1)
        _check("every [TBD — unsourced] sits in a section whose footer records `open`",
               all(sid in open_sections or sid == 17
                   for sid in bodies if "[TBD — unsourced]" in bodies[sid]),
               f"{len(tbds)} TBD markers")

        # 9) Code-blind.
        print("\n9) code-blind (FR-SI-02) — the repo source routed E and stayed invisible:")
        code_src = [s for s in ui["sources"] if s.get("disposition") == ["codebase"]]
        _check("the corpus DOES contain a codebase source (so this is a real test)", bool(code_src))
        _check("v1 cites no code_map", "code_map" not in v1)
        _check("v1 cites no repo/ path", "repo/" not in v1 and "[code:" not in v1)
        _check("no citation resolves to the bitbucket source",
               not any("bitbucket" in p for p, _, _ in cites))

        # 10) §15 ↔ §4 (D-A11's mechanical guardrail).
        print("\n10) §15 → §4 traces, both directions (D-A11):")
        objectives = set(re.findall(r"\*\*(O\d+) —", bodies[4]))
        criteria = re.findall(r"^\| (S\d+) \| .+? \| ([^|]+) \|", bodies[15], re.M)
        _check("§4 declares objective IDs", len(objectives) >= 2, str(sorted(objectives)))
        _check("§15 declares criterion IDs", len(criteria) >= 3, str([c for c, _ in criteria]))
        orphan_c = [c for c, t in criteria if not set(re.findall(r"O\d+", t)) & objectives]
        _check("no criterion is orphaned (each traces to a real objective)", not orphan_c, str(orphan_c))
        traced = {o for _, t in criteria for o in re.findall(r"O\d+", t)}
        _check("no objective is unmeasurable (each has ≥1 criterion)", objectives <= traced,
               f"unmeasured: {sorted(objectives - traced)}")

    print()
    if _FAILURES:
        print(f"FAILED — {len(_FAILURES)} check(s): {_FAILURES}", file=sys.stderr)
        return 1
    print("PASS — 18 sections present-or-dispositioned; §7→§8 and §15→§4 traces intact; every "
          "requirement carries a deliverable and enumerated assertions; every citation resolves "
          "to a real line range; gaps surface in §17; v1 is code-blind.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
