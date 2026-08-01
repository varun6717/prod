#!/usr/bin/env python3
"""jira_plan.py — assemble the 4-level plan from v2 + enrichment.json (§3.8, D-A15).

Deterministic assembly. The **judgment** parts — a story's summary, and above all its acceptance
criteria — are the model's, and are injected: acceptance criteria exist nowhere upstream, which is
what makes story authoring a translation rather than a copy.

The hierarchy is JPMC's and each level has exactly one source:

    Initiative  ← the document (§1/§2/§4)                    available at v1
    Deliverable ← §7, one per D-id                           available at v1
    Epic        ← §8, ONE PER REQUIREMENT                    available at v1
    Story       ← §16 impacts + gaps, and §7 non-code work   **v2 only**

The parent chain is built by the SI's **own ids**: an epic's parent is the deliverable its
requirement named in §8. That trace is load-bearing rather than tidy — a requirement with no
`Deliverable:` produces an epic with no parent, which is why G1 made it a hard precondition. The
ids are carried verbatim because they are the push's idempotency anchors.
"""
from __future__ import annotations

import re
from typing import Callable, Sequence

_S16_ENTRY = re.compile(r"^- \*\*(F-\d+)\*\* \((impact|GAP[^)]*)\)\s*·\s*([^→]+)→\s*`([^`]*)`",
                        re.M)
_S16_REQ = re.compile(r"^### (R\d+)\s*$", re.M)
_DELIV_ROW = re.compile(r"^\| \*\*(D\d+)\*\* \| ([^|]+) \| ([^|]+) \|", re.M)


def parse_v2_section16(s16: str) -> list[dict]:
    """§16 entries, with the requirement heading each sits under (FR-EN-06's machine-consumable
    structure earning its keep)."""
    out, current = [], None
    for line in s16.splitlines():
        if (m := _S16_REQ.match(line)):
            current = m.group(1)
            continue
        if (m := _S16_ENTRY.match(line)):
            fid, kind, ref, ev = m.groups()
            out.append({"id": fid, "requirement": current, "kind": kind,
                        "assertion_ref": ref.strip(), "evidence": ev.strip()})
    return out


def build_plan(v2_sections: dict, signals, record: dict, *, run_id: str, project_key: str,
               controls: dict, story_author: Callable[[dict], dict],
               deliverable_kind: Callable[[str], str] | None = None) -> dict:
    """Assemble `jira_plan.json`. ``story_author`` supplies summary + acceptance criteria."""
    s16 = parse_v2_section16(v2_sections.get(16, ""))
    by_req: dict[str, list[dict]] = {}
    for e in s16:
        by_req.setdefault(e["requirement"] or "unassigned", []).append(e)

    deliverables = []
    for did, name, delivered in _DELIV_ROW.findall(v2_sections.get(7, "")):
        kind = deliverable_kind(did) if deliverable_kind else (
            "non_code" if "non-code" in name.lower() or "**non-code**" in delivered.lower()
            else "code")
        deliverables.append({"local_id": did, "issue_type": "Deliverable",
                             "summary": name.strip(), "description": delivered.strip(),
                             "kind": kind, "parent": "INIT"})

    epics, stories, n = [], [], 0
    for rid in signals.requirements:
        parent = signals.req_deliverable.get(rid)
        epics.append({"local_id": rid, "issue_type": "Epic", "parent": parent,
                      "summary": f"{rid}",
                      "assertion_refs": [f"{rid}.{i}" for i in
                                         range(1, signals.req_assertions.get(rid, 0) + 1)],
                      "controls": dict(controls)})
        for entry in by_req.get(rid, []):
            n += 1
            authored = story_author(entry)
            story = {"local_id": f"S{n}", "issue_type": "Story", "parent": rid,
                     "evidence": entry["id"], **authored}
            # Exactly one of code_location | flag. A gap has no code to name, and inventing a
            # path would be the fabrication `new_build` exists to make unnecessary.
            if entry["kind"].startswith("GAP"):
                story["flag"] = "new_build"
                story.pop("code_location", None)
            else:
                story["code_location"] = entry["evidence"]
                story.pop("flag", None)
            stories.append(story)

    # §7 non-code work becomes stories too — it is where a "not code at all" disposition lands,
    # and omitting it would leave certification/filing work in no plan at all.
    for d in deliverables:
        if d["kind"] != "non_code":
            continue
        owning = next((e["local_id"] for e in epics if e["parent"] == d["local_id"]), None)
        if owning is None:
            continue
        n += 1
        authored = story_author({"id": d["local_id"], "requirement": owning,
                                 "kind": "non_code", "evidence": ""})
        stories.append({"local_id": f"S{n}", "issue_type": "Story", "parent": owning,
                        "evidence": d["local_id"], "flag": "non_code", **authored})

    return {
        "run_id": run_id, "project_key": project_key,
        "initiative": {"local_id": "INIT", "issue_type": "Initiative",
                       "summary": _first_heading(v2_sections.get(1, "")),
                       "description": v2_sections.get(1, "").strip()[:600],
                       "controls": dict(controls)},
        "deliverables": deliverables, "epics": epics, "stories": stories,
        "trace": {"section16_entries": [e["id"] for e in s16],
                  "requirements": list(signals.requirements),
                  "deliverables": [d["local_id"] for d in deliverables]},
    }


def _first_heading(text: str) -> str:
    for line in text.splitlines():
        if line.startswith("## "):
            return line[3:].strip()
    return "Initiative"
