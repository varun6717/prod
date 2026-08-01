#!/usr/bin/env python3
"""enrichment.py — the `enrichment.json` record + the D-A16 finding router.

Two things live here, and they are here **together on purpose**: the file that records what
enrichment found, and the rule that decides what happens to each finding. Both arms and the
disposition walkthrough consume this one router, so the "what reaches the operator" table cannot
be implemented three times and drift twice.

────────────────────────────────────────────────────────────────────────────────────────
The routing rule, in one sentence
────────────────────────────────────────────────────────────────────────────────────────
**Findings that are grounded and unambiguous apply themselves; findings that are ambiguous,
scope-moving, or would overrule a human escalate.**

That filtering happens *before* the walkthrough, and it is what keeps the operator turn tractable
— D-A16 is explicit that most findings never reach a human. It is not "review all findings", it is
"review the ones needing judgment".

The discriminator is usually **not** the finding's content but the **provenance of the claim it
touches** (D-A6). The same contradiction auto-corrects or escalates depending on where the v1
claim came from:

  source-derived  → auto-correct in place, with code provenance
  operator/frame  → ESCALATE — never overrule a human silently
  `[TBD]` unsourced → auto-fill; not a correction, a gap closure

────────────────────────────────────────────────────────────────────────────────────────
What this module deliberately does NOT do
────────────────────────────────────────────────────────────────────────────────────────
It never *applies* anything and never decides a disposition. It classifies. The apply pass
(TASK-121) writes v2; the walkthrough (TASK-120) takes the operator's call. Keeping classification
pure is what lets the same rule be tested exhaustively against D-A16's table — which is the proof
this task owes.

**Enrichment never deletes** (D-A7). A contradicted claim is rewritten, not removed: deletion is
invisible in a way rewriting is not — at G2 an operator can see a changed sentence but cannot see
a missing one. Nothing here ever produces a "remove" action.
"""
from __future__ import annotations

import json
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Sequence

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "core" / "scripts"))

import ledger  # noqa: E402

# Routes (mirrors telemetry's `route` enum — one vocabulary, two files).
AUTO_CORRECT, AUTO_FILL, AUTO_WRITE, ESCALATE, NONE = (
    "auto_correct", "auto_fill", "auto_write", "escalate", "none")

# The four D-A16 escalation triggers.
OPERATOR_CONTRADICTION = "operator_contradiction"
BUSINESS_VISIBLE = "business_visible"
NO_CODE_FOUND = "no_code_found"
SCOPE_MOVING = "scope_moving"

# D-A16's four-way routing table for a dispositioned no-code gap. The operator's call decides;
# this records where each call LANDS. `reject` maps to `dropped` rather than to a section: the
# finding was wrong, so it leaves the document — but it is logged to decisions.jsonl, never
# silently discarded.
NO_CODE_GAP_ROUTING = {
    "new_capability": "§16",     # genuinely new — becomes a build story
    "search_miss":    "dropped", # Arm 1 was wrong; logged, not kept
    "other_repo":     "§14",     # lives elsewhere → Dependencies
    "not_code":       "§7",      # not code at all → Deliverables, as non-code work
    "cannot_determine": "§17",   # the REQUIRED defer path → Open questions
}

# Where an escalated finding lands by default once accepted, per D-A16's per-type tables.
ESCALATION_DEFAULT_TARGET = {
    OPERATOR_CONTRADICTION: None,   # back into whichever section made the claim, or §17 if deferred
    BUSINESS_VISIBLE: "§8",         # a new requirement (or §12 if excluded — operator's call)
    NO_CODE_FOUND: "§16",
    SCOPE_MOVING: "§12",
}


@dataclass
class Route:
    """The router's verdict on one finding. Classification only — nothing is applied."""
    route: str
    action: str                       # auto_applied | escalated | none
    section_target: str | None = None
    escalation_reason: str | None = None
    severity: str | None = None
    why: str = ""

    @property
    def escalates(self) -> bool:
        return self.route == ESCALATE


def route_finding(*, arm: str, kind: str, claim_provenance: str | None = None,
                  business_visible: bool | None = None, scope_moving: bool = False,
                  section_ref: str | None = None) -> Route:
    """Classify one finding per D-A16. Pure — no I/O, no model, no side effects.

    The order of the tests is the rule's meaning, not an implementation detail:

    **scope-moving is checked FIRST**, before anything else, because "anything scope-moving"
    escalates regardless of how well grounded it is. A perfectly evidenced, source-derived
    contradiction that moves a scope boundary is still an operator decision — scope changes are
    operator-decided, always.
    """
    # Anything scope-moving escalates, whatever else is true of it.
    if scope_moving or kind == "scope_move":
        return Route(ESCALATE, "escalated", ESCALATION_DEFAULT_TARGET[SCOPE_MOVING],
                     SCOPE_MOVING, "material",
                     "scope changes are operator-decided, however well grounded the finding")

    if kind == "no_code_found":
        # Four-way ambiguous: new build / search miss / other repo / not code. The code cannot
        # distinguish them, so a human must.
        return Route(ESCALATE, "escalated", ESCALATION_DEFAULT_TARGET[NO_CODE_FOUND],
                     NO_CODE_FOUND, "material",
                     "no implementation found — four-way ambiguous (new capability / search miss "
                     "/ another repo / not code at all)")

    if kind == "derived_impact":
        # D-A9's single follow-up question: technical consequence, or does someone have to decide?
        if business_visible:
            return Route(ESCALATE, "escalated", ESCALATION_DEFAULT_TARGET[BUSINESS_VISIBLE],
                         BUSINESS_VISIBLE, "material",
                         "business-visible consequence — a human must decide, not merely be told")
        return Route(AUTO_WRITE, "auto_applied", "§16", why="technical consequence — documented")

    if kind == "contradiction":
        # THE provenance rule (D-A6). Same finding, different authority.
        if claim_provenance in ("operator", "frame"):
            return Route(ESCALATE, "escalated", section_ref, OPERATOR_CONTRADICTION, "material",
                         "code contradicts a human's statement — never overrule one silently")
        if claim_provenance == "unsourced":
            return Route(AUTO_FILL, "auto_applied", section_ref,
                         why="code answers an unsourced [TBD] — a gap closure, not a correction")
        return Route(AUTO_CORRECT, "auto_applied", section_ref,
                     why="source-derived claim contradicted by code — corrected in place with "
                         "code provenance (rewritten, never deleted)")

    if kind == "gap_fill":
        return Route(AUTO_FILL, "auto_applied", section_ref,
                     why="code answers an unsourced [TBD] — free value from the code arm")

    if kind == "unverifiable":
        # Often informative rather than a dead end: no match anywhere usually means the claim
        # concerns a partner or upstream system, which is itself worth surfacing (D-A8).
        return Route(AUTO_WRITE, "auto_applied", "§14",
                     why="no match anywhere — usually a partner/upstream system, surfaced to "
                         "Dependencies rather than silently marked unverified")

    if kind == "versioned_duplicate":
        return Route(ESCALATE, "escalated", None, NO_CODE_FOUND, "material",
                     "versioned duplicate — which of v1/v2 does this land on? The code cannot "
                     "say, so it must never be resolved silently (D-A20 finding 3)")

    if kind == "confirmation":
        return Route(NONE, "none", None, why="claim confirmed against code — nothing to do")

    raise ValueError(f"unroutable finding kind {kind!r}")


# ── Arm 2's population rules (D-A5 / D-A4), enforced rather than trusted ──────
SORT_CLAIM, SORT_JUDGMENT, SORT_FUTURE, SORT_RUNTIME = (
    "factual_current_state", "business_judgment", "future_state", "runtime_shaped")

# Sorts that produce NO finding at all. Skipping is not the same as verdicting `unverifiable`:
# the marker implies we looked and failed, and for these we cannot look at all. If every business
# sentence acquired one, the marker would stop meaning anything (D-A5).
SKIPPED_SORTS = frozenset({SORT_JUDGMENT, SORT_FUTURE, SORT_RUNTIME})

# Sections whose claims Arm 2 may verdict (D-A5). §8 is absent DELIBERATELY.
VERDICT_ELIGIBLE_SECTIONS = ("§2", "§5", "§6", "§10", "§13", "§14")


def stage_claim(fid: str, *, sort: str, section_ref: str, **kw) -> Finding | None:
    """Stage one Arm-2 claim. Returns ``None`` when the claim is out of population.

    Two rules are enforced here rather than left to the skill's discipline, because both failures
    would be invisible in the output:

    - **A skipped sort produces no finding.** Not an `unverifiable` one — none. Marking a latency
      NFR "unverified against code" claims we looked; the instrument cannot look at all.
    - **§8 is never corrected** (D-A4, binding). Code cannot contradict an intent; it can only
      show a requirement is incomplete (escalate) or unachievable (a risk, §13). Letting
      enrichment rewrite a requirement from code inverts the ladder and lets the existing
      implementation dictate business intent — the worst failure available here.
    """
    if sort in SKIPPED_SORTS:
        return None
    if sort != SORT_CLAIM:
        raise ValueError(f"unknown claim sort {sort!r}")
    if section_ref and section_ref.startswith("§8") and kw.get("kind") == "contradiction":
        raise ValueError(
            "§8 requirements are EXTEND-ONLY — code cannot contradict an intent (D-A4). Verdict "
            "the implicit current-state assumption inside the assertion instead, and route an "
            "incompleteness to escalation.")
    return make_finding(fid, section_ref=section_ref, **kw)


# ── the record ────────────────────────────────────────────────────────────────
@dataclass
class Finding:
    id: str
    arm: str
    kind: str
    action: str
    status: str = "undispositioned"
    route: str | None = None
    requirement_ref: str | None = None
    assertion_ref: str | None = None
    section_ref: str | None = None
    claim_provenance: str | None = None
    verdict: str | None = None
    evidence: list = field(default_factory=list)
    reasoning: str | None = None
    business_visible: bool | None = None
    scope_moving: bool | None = None
    escalation_reason: str | None = None
    severity: str | None = None
    section_target: str | None = None
    disposition: str | None = None
    rationale: str | None = None
    actor: str | None = None
    depends_on_finding: list = field(default_factory=list)
    applied_at: str | None = None

    def to_json(self) -> dict:
        return {k: v for k, v in asdict(self).items()
                if v is not None and not (isinstance(v, list) and not v)}


def make_finding(fid: str, *, arm: str, kind: str, **kw) -> Finding:
    """Build a Finding with its route already classified — the two cannot get out of step."""
    r = route_finding(arm=arm, kind=kind,
                      claim_provenance=kw.get("claim_provenance"),
                      business_visible=kw.get("business_visible"),
                      scope_moving=bool(kw.get("scope_moving")),
                      section_ref=kw.get("section_ref"))
    f = Finding(id=fid, arm=arm, kind=kind, action=r.action, route=r.route, **kw)
    f.section_target = f.section_target or r.section_target
    f.escalation_reason = r.escalation_reason
    f.severity = r.severity
    # An auto-applied finding is applied by definition — there is no human step left for it.
    f.status = "undispositioned" if r.escalates else "applied"
    return f


def new_record(run_id: str, v1_sha256: str, generated_at: str = "2026-08-01T00:00:00Z") -> dict:
    return {"run_id": run_id, "v1_sha256": v1_sha256, "generated_at": generated_at,
            "findings": []}


def add(record: dict, finding: Finding) -> dict:
    record["findings"].append(finding.to_json())
    return record


def disposition(record: dict, finding_id: str, *, call: str, rationale: str,
                actor: str, target: str | None = None) -> dict:
    """Record the operator's walkthrough call. Never applies it — that is the apply pass."""
    f = next(x for x in record["findings"] if x["id"] == finding_id)
    if f["action"] != "escalated":
        raise ValueError(f"{finding_id} did not escalate — there is nothing for an operator to "
                         f"disposition (it was {f['action']})")
    f["disposition"] = call
    f["rationale"] = rationale
    f["actor"] = actor
    f["status"] = "dispositioned"
    if call == "reject":
        f["section_target"] = "dropped"
    elif target:
        f["section_target"] = target
    return record


def pending(record: dict) -> list[dict]:
    """Findings still awaiting a human — what the walkthrough resumes to (D-A17)."""
    return [f for f in record["findings"] if f["status"] == "undispositioned"]


def counts(record: dict) -> dict:
    """§18's payload — counts only, never a ledger (D-A4)."""
    fs = record["findings"]
    return {
        "findings": len(fs),
        "auto_applied": sum(1 for f in fs if f["action"] == "auto_applied"),
        "escalated": sum(1 for f in fs if f["action"] == "escalated"),
        "undispositioned": sum(1 for f in fs if f["status"] == "undispositioned"),
        "corrections": sum(1 for f in fs if f.get("route") == AUTO_CORRECT),
        "auto_fills": sum(1 for f in fs if f.get("route") == AUTO_FILL),
        "derived_impacts": sum(1 for f in fs if f.get("route") == AUTO_WRITE),
        "confirmed": sum(1 for f in fs if f.get("verdict") == "confirmed"),
        "unverifiable": sum(1 for f in fs if f.get("verdict") == "unverifiable"),
    }


def validate(record: dict) -> list[str]:
    """Validate against `schemas/enrichment.schema.json`. ``[]`` == valid."""
    schema = ledger.load_schema("enrichment")
    errs = ledger.validate_record(record, schema)
    for f in record.get("findings", []):
        errs += [f"finding {f.get('id')}: {m}"
                 for m in ledger.validate_record(f, {**schema["$defs"]["finding"],
                                                     "$defs": schema["$defs"]})]
    return errs


def write(record: dict, si_dir: Path) -> Path:
    si_dir.mkdir(parents=True, exist_ok=True)
    p = si_dir / "enrichment.json"
    p.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    return p


# ── ledger wiring ─────────────────────────────────────────────────────────────
def emit_finding_events(emitter, finding: Finding, *, ts: str | None = None) -> None:
    """Stamp the telemetry a finding owes: a `verdict`, plus an `escalation` when it escalates."""
    if finding.verdict:
        emitter.verdict(finding_id=finding.id, arm=finding.arm, verdict=finding.verdict,
                        route=finding.route or NONE, ts=ts)
    if finding.action == "escalated":
        emitter.escalation(finding_id=finding.id, reason=finding.escalation_reason,
                           severity=finding.severity, ts=ts)


def emit_disposition_events(emitter, decisions_path, record: dict, finding_id: str,
                            *, ts: str | None = None) -> None:
    """Stamp both ledgers for a dispositioned finding — telemetry counts, decisions carries WHY."""
    import decisions as dec

    f = next(x for x in record["findings"] if x["id"] == finding_id)
    target = None if f.get("section_target") == "dropped" else f.get("section_target")
    emitter.disposition(finding_id=finding_id, call=f["disposition"], actor=f["actor"],
                        target=target, ts=ts)
    dec.disposition(decisions_path, finding_id=finding_id, call=f["disposition"],
                    rationale=f["rationale"], target=target, actor=f["actor"], ts=ts)
