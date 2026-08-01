#!/usr/bin/env python3
"""apply_enrichment.py — v1 + enrichment.json → v2 (D-A2, D-A8 steps 4–6).

The deterministic assembly step. Enrichment produced findings; the walkthrough resolved the ones
needing a human; this writes the document.

────────────────────────────────────────────────────────────────────────────────────────
The placement rule (D-A2)
────────────────────────────────────────────────────────────────────────────────────────
**Corrections revise IN PLACE; discoveries append.** The discriminator is whether the finding
contradicts an existing claim (revise) or adds something absent (append).

A document that goes to stakeholders must never be internally contradictory. A correction sitting
twelve pages from the claim it corrects leaves a false statement in the body — the reader meets
the error first and may never reach the fix.

**Every in-place revision carries provenance** — an inline `[code: path:symbol]` citation in the
same style as the cite-or-flag citations. Silent rewriting of an accepted document is the failure
mode this closes: at G2 the operator can see exactly which sentences enrichment touched, and on
what evidence.

**Nothing is ever deleted** (D-A7). A contradicted claim is rewritten; a claim left vestigial after
correction stays as corrected text. Deletion is invisible in a way rewriting is not.

────────────────────────────────────────────────────────────────────────────────────────
Order (D-A8 steps 4–6) — and why §1 is last
────────────────────────────────────────────────────────────────────────────────────────
    1  apply corrections in place              (§2, §5, §6, §10, §13, §14)
    2  write §16 from impacts + accepted gaps  organised BY REQUIREMENT
    3  extend §17 with deferrals and new gaps
    4  write §18 counts
    5  REGENERATE §1 from the corrected body

§1 regenerates, it does not revise (D-A4). It is derived from the body, so a summary of an
uncorrected problem statement is silently wrong — it must be re-authored *after* every correction
has landed, or v2 ships with an executive summary describing v1.

v1 is never touched. It is frozen at G1 and stays byte-identical; `v1_sha256` in the record is
verified before anything is written, because "v1 + enrichment.json reconstruct v2" is only true if
v1 is the v1 the findings were computed against.
"""
from __future__ import annotations

import hashlib
import re
from collections import defaultdict
from pathlib import Path
from typing import Sequence

_SECTION = re.compile(r"^## (\d+)\. (.+)$", re.M)
_COVERAGE = re.compile(r"<!--\s*coverage:.*?-->", re.S)

# Sections enrichment may revise in place. §8 is absent DELIBERATELY (extend-only, D-A4).
CORRECTABLE = ("§2", "§5", "§6", "§10", "§13", "§14")


def split_sections(text: str) -> dict[int, str]:
    heads = [(int(n), m.start()) for m, n in
             ((m, m.group(1)) for m in _SECTION.finditer(text))]
    out: dict[int, str] = {}
    for i, (sid, start) in enumerate(heads):
        end = heads[i + 1][1] if i + 1 < len(heads) else len(text)
        out[sid] = text[start:end]
    return out


def provenance_note(finding: dict) -> str:
    """The inline citation an in-place revision must carry."""
    ev = (finding.get("evidence") or [{}])[0]
    ref = ev.get("path", "?")
    if ev.get("symbol"):
        ref += f":{ev['symbol']}"
    if ev.get("lines"):
        ref += f" L{ev['lines'][0]}–{ev['lines'][-1]}"
    return f"[code: {ref}]"


def applicable(record: dict) -> list[dict]:
    """Findings that land in v2: auto-applied, plus dispositioned ones the operator kept.

    A `reject` is excluded (the finding was wrong), and a **superseded** finding is excluded too —
    its premise was withdrawn. Both stay in the record; neither reaches the document.
    """
    out = []
    for f in record["findings"]:
        if f["status"] == "superseded":
            continue
        if f["action"] == "auto_applied":
            out.append(f)
        elif f["status"] == "dispositioned" and f.get("disposition") != "reject":
            out.append(f)
    return out


def apply_to_v2(v1_text: str, record: dict, *, regenerate_summary=None) -> tuple[str, dict]:
    """Assemble v2. Returns ``(v2_text, applied_report)``. Never mutates ``v1_text``.

    ``regenerate_summary(body, findings)`` is the model seam for step 5 — §1 is prose derived from
    the corrected body, which is the one part of assembly that is not mechanical.
    """
    digest = hashlib.sha256(v1_text.encode()).hexdigest()[:12]
    if record.get("v1_sha256") and record["v1_sha256"] != digest:
        raise ValueError(
            f"enrichment.json was computed against v1 {record['v1_sha256']}, but this v1 hashes "
            f"to {digest} — 'v1 + enrichment.json reconstruct v2' would not hold")

    sections = split_sections(v1_text)
    applied = applicable(record)
    report = {"corrections": [], "impacts": [], "open_questions": [], "appended": []}

    # ── 1. corrections IN PLACE, each carrying provenance
    for f in applied:
        target = f.get("section_target") or f.get("section_ref")
        # Auto-applied corrections, PLUS escalated contradictions the operator accepted. The
        # escalation was about *authority* (never overrule a human silently), not about what the
        # correction is — once accepted it lands exactly like an auto-corrected one, in place and
        # with provenance. Skipping it would leave the operator's own decision unapplied.
        accepted_correction = (f["kind"] == "contradiction"
                               and f.get("disposition") == "accept")
        if not (f["route"] in ("auto_correct", "auto_fill") or accepted_correction) or not target:
            continue
        sid = int(target.lstrip("§").split()[0]) if target.startswith("§") else None
        if sid not in sections or f"§{sid}" not in CORRECTABLE:
            continue
        note = (f"\n\n> **Corrected during enrichment ({f['id']}).** {f.get('reasoning','')} "
                f"{provenance_note(f)}\n")
        sections[sid] = sections[sid].rstrip() + note
        report["corrections"].append({"id": f["id"], "section": target})

    # ── 2. §16, organised BY REQUIREMENT (FR-EN-06) — impacts AND accepted gaps
    by_req: dict[str, list[dict]] = defaultdict(list)
    for f in applied:
        if f.get("section_target") == "§16" or f["kind"] in ("derived_impact", "no_code_found"):
            by_req[f.get("requirement_ref") or "unassigned"].append(f)
    s16 = ["## 16. Derived system impacts", ""]
    if by_req:
        for req in sorted(by_req):
            s16.append(f"### {req}")
            s16.append("")
            for f in sorted(by_req[req], key=lambda x: x["id"]):
                ev = ", ".join(e.get("path", "?") for e in (f.get("evidence") or [])) or "—"
                kind = "GAP — no implementation found" if f["kind"] == "no_code_found" else "impact"
                s16.append(f"- **{f['id']}** ({kind}) · {f.get('assertion_ref') or req} → `{ev}`  ")
                s16.append(f"  {f.get('reasoning','')}")
                if f.get("disposition"):
                    s16.append(f"  *Operator: {f['disposition']} — {f.get('rationale','')}*")
                report["impacts"].append(f["id"])
            s16.append("")
    else:
        s16 += ["None identified.", ""]
    sections[16] = "\n".join(s16)

    # ── 3. §17 extended — v1's questions PLUS every deferral (never replaced)
    deferrals = [f for f in applied if f.get("disposition") == "defer"]
    s17 = sections.get(17, "## 17. Open questions\n").rstrip()
    s17 = _COVERAGE.sub("", s17).rstrip()
    if deferrals:
        s17 += "\n\n**Added during enrichment:**\n"
        for f in sorted(deferrals, key=lambda x: x["id"]):
            s17 += (f"\n- **{f['id']}** — {f.get('reasoning','')} "
                    f"*Deferred: {f.get('rationale','')}*")
            report["open_questions"].append(f["id"])
    sections[17] = s17 + "\n"

    # ── 4. §18 — counts only, never a ledger (D-A4)
    fs = record["findings"]
    c = {
        "population": sum(1 for f in fs if f.get("verdict")),
        "confirmed": sum(1 for f in fs if f.get("verdict") == "confirmed"),
        "corrected": sum(1 for f in fs if f.get("route") == "auto_correct"),
        "auto_filled": sum(1 for f in fs if f.get("route") == "auto_fill"),
        "unverifiable": sum(1 for f in fs if f.get("verdict") == "unverifiable"),
        "impacts": len(report["impacts"]),
        "escalated": sum(1 for f in fs if f["action"] == "escalated"),
        "superseded": sum(1 for f in fs if f["status"] == "superseded"),
    }
    sections[18] = (
        "## 18. Verification summary\n\n"
        f"- Claims and assertions verdicted: **{c['population']}** — "
        f"{c['confirmed']} confirmed · {c['corrected']} corrected · "
        f"{c['auto_filled']} auto-filled · {c['unverifiable']} unverifiable\n"
        f"- §16 entries produced: **{c['impacts']}**\n"
        f"- Findings escalated to the operator: **{c['escalated']}** "
        f"({c['superseded']} superseded by an upstream reversal)\n\n"
        "*Counts only. The claim-by-claim record is `enrichment.json`.*\n")

    # ── 5. §1 LAST — regenerated from the corrected body, not revised
    body = "\n".join(sections[k] for k in sorted(sections) if k != 1)
    if regenerate_summary is not None:
        sections[1] = regenerate_summary(body, applied)

    head = v1_text[:v1_text.index("## 1. ")] if "## 1. " in v1_text else ""
    v2 = head + "\n".join(sections[k].rstrip() + "\n\n" for k in sorted(sections))
    report["counts"] = c
    return v2.rstrip() + "\n", report
