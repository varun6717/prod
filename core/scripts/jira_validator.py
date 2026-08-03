#!/usr/bin/env python3
"""jira_validator.py — the G3 score + hard checks over the 4-level plan (§9.4, FR-JR-04).

**G3 is the real technical-quality gate** (D-A1). G1 accepted business intent; G2 accepted that
intent checked against code; G3 is the last point at which anything is reviewable before the run's
**only external mutation**. After it, issues exist in Jira.

    traceability       = valid_links / total_links_required
    testability        = stories with acceptance criteria AND (code location | flag) / total
    field_completeness = issues with all required + controls fields / total issues
    jira_score = round(100 * (0.4 * traceability + 0.3 * testability + 0.3 * field_completeness))

*(§9.4 pins the three-part weighting. The TASK-123 line item summarised it as 0.5/0.5 — the spec
block is normative, so the three-part form is implemented and the discrepancy is noted rather than
silently resolved either way.)*

**The two story guardrails are the substance** (D-A23 family 3), and they run in opposite
directions because they catch opposite failures:

  every §16 entry → ≥1 story        catches a **dropped impact** — work that enrichment found
                                    and the plan silently lost
  every story → §16 or §7           catches an **invented story** — work in the plan that no
                                    evidence supports

One direction alone would pass a plan that is complete but fabricated, or grounded but missing
half the work. Both are silent: neither produces a malformed plan.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Sequence

THRESHOLD_DEFAULT = 85
_VALID_OUTCOMES = ("accept", "reopen")
REQUIRED_CONTROLS = ("seal_id", "control_owner", "risk_classification")


@dataclass(frozen=True)
class Check:
    name: str
    ok: bool
    violations: tuple = ()


@dataclass(frozen=True)
class G3Result:
    traceability: float
    testability: float
    field_completeness: float
    score: int
    threshold: int
    checks: tuple = ()

    @property
    def score_pass(self) -> bool:
        return self.score >= self.threshold

    @property
    def hard_ok(self) -> bool:
        return all(c.ok for c in self.checks)

    @property
    def eligible(self) -> bool:
        return self.score_pass and self.hard_ok

    @property
    def blockers(self) -> tuple:
        return tuple(v for c in self.checks if not c.ok for v in c.violations)


def evaluate_g3(plan: dict, *, section16_ids: Sequence[str] = (),
                dispositioned_without_story: Sequence[str] = (),
                threshold: int = THRESHOLD_DEFAULT) -> G3Result:
    """Score the plan and decide G3 eligibility. Pure — no I/O, no model."""
    deliverables = {d["local_id"]: d for d in plan.get("deliverables", [])}
    epics = {e["local_id"]: e for e in plan.get("epics", [])}
    stories = plan.get("stories", [])
    s16 = set(section16_ids)
    excused = set(dispositioned_without_story)

    # TASK-129 — a run may create only part of the tree, attaching to a standing Jira issue.
    # `parent_link` is then a legitimate parent that the plan does NOT declare, so the two
    # "names a parent the plan does not declare" checks below have to know about it.
    push_root = plan.get("push_root") or {}
    parent_link = push_root.get("parent_link")
    # §7 ids come from `trace`, not from the pushed deliverables: at level `epic` nothing declares
    # them, yet a non-code story still legitimately cites one. Evidence is provenance in the SI,
    # not an assertion about what exists in Jira — reading it off the pushed set would report a
    # correctly-grounded story as invented work.
    declared_deliverables = set(deliverables) | set((plan.get("trace") or {}).get("deliverables", []))

    # ── traceability: every required parent link resolves
    links, valid = 0, 0
    v_trace: list[str] = []
    for d in deliverables.values():
        links += 1
        if d.get("parent") == plan.get("initiative", {}).get("local_id") or (
                parent_link and d.get("parent") == parent_link):
            valid += 1
        else:
            v_trace.append(f"deliverable {d['local_id']} has no initiative parent")
    for e in epics.values():
        links += 1
        if e.get("parent") in deliverables or (parent_link and e.get("parent") == parent_link):
            valid += 1
        else:
            v_trace.append(f"epic {e['local_id']} names deliverable {e.get('parent')!r}, which "
                           f"the plan does not declare — the §8→§7 trace is broken")
    for s in stories:
        links += 2
        valid += 1 if s.get("parent") in epics else 0
        if s.get("parent") not in epics:
            v_trace.append(f"story {s['local_id']} has no epic parent")
        ev = s.get("evidence")
        if ev in s16 or ev in declared_deliverables:
            valid += 1
        else:
            # the INVENTED-STORY catch
            v_trace.append(f"story {s['local_id']} traces to {ev!r}, which is neither a §16 entry "
                           f"nor a §7 deliverable — invented work")
    # the DROPPED-IMPACT catch
    covered = {s.get("evidence") for s in stories}
    for eid in sorted(s16 - covered - excused):
        links += 1
        v_trace.append(f"§16 entry {eid} yields no story and carries no explicit disposition — "
                       f"enrichment found this impact and the plan lost it")
    traceability = (valid / links) if links else 1.0

    # ── testability: a story must be verifiable AND locatable
    ok_stories, v_test = 0, []
    for s in stories:
        has_ac = bool(str(s.get("acceptance_criteria", "")).strip())
        located = bool(s.get("code_location")) ^ bool(s.get("flag"))
        if has_ac and located:
            ok_stories += 1
            continue
        if not has_ac:
            v_test.append(f"story {s['local_id']} has no acceptance criteria — nothing states "
                          f"when it is done")
        if not located:
            v_test.append(f"story {s['local_id']} must carry exactly one of code_location | flag "
                          f"(new_build | non_code)")
    testability = (ok_stories / len(stories)) if stories else 1.0

    # ── field completeness: controls ride on every pushed issue
    # An absent initiative is legitimate below level `initiative` (TASK-129). Including a bare {}
    # would report "issue ? missing local_id or summary" — a controls failure invented by the
    # scoring code rather than found in the plan.
    issues = ([plan["initiative"]] if plan.get("initiative") else []) \
        + list(deliverables.values()) + list(epics.values()) + list(stories)
    complete, v_fields = 0, []
    for i in issues:
        if not i.get("local_id") or not str(i.get("summary", "")).strip():
            v_fields.append(f"issue {i.get('local_id', '?')} missing local_id or summary")
            continue
        ctrl = i.get("controls")
        if ctrl is not None and not all(ctrl.get(k) for k in REQUIRED_CONTROLS):
            v_fields.append(f"issue {i['local_id']} is missing controls "
                            f"{[k for k in REQUIRED_CONTROLS if not ctrl.get(k)]}")
            continue
        complete += 1
    field_completeness = (complete / len(issues)) if issues else 1.0

    score = round(100 * (0.4 * traceability + 0.3 * testability + 0.3 * field_completeness))

    checks = (
        # HARD: traceability must be TOTAL, not merely high. A 0.98 traceability means one piece
        # of work is unaccounted for, and after the push there is no cheap way to find which.
        Check("hierarchy_traceability_complete", traceability == 1.0, tuple(v_trace)),
        Check("controls_present", not v_fields, tuple(v_fields)),
        Check("stories_locatable_and_testable", not v_test, tuple(v_test)),
    )
    return G3Result(traceability, testability, field_completeness, score, threshold, checks)


def record_g3(ledger_dir, *, result: G3Result, outcome: str, version: int,
              actor: str = "vmunjal", ts: str | None = None):
    """G3 wiring. Accept is **one combined sign-off**: review the plan *and* authorise the push.

    Refused when ineligible — and this refusal matters more than G1's or G2's, because the next
    thing that happens is the run's only external mutation.
    """
    from pathlib import Path

    import telemetry
    if outcome not in _VALID_OUTCOMES:
        raise ValueError(f"outcome must be one of {_VALID_OUTCOMES}; got {outcome!r}")
    if outcome == "accept" and not result.eligible:
        raise ValueError(f"G3 accept refused: {list(result.blockers)[:3]}")
    locked = version if outcome == "accept" else version + 1
    import solution_intent_validator as V
    em = telemetry.Emitter(ledger_dir, run_id=V._run_id(ledger_dir), domain="payment_brand",
                           tool=V._runtime_tool(ledger_dir))
    em.validation(artifact="jira", score=float(result.score), ts=ts)
    em.gate_decision(gate="G3", outcome=outcome, actor=actor, version=locked, ts=ts)
    telemetry.gate(Path(ledger_dir) / "decisions.jsonl", gate="G3", outcome=outcome,
                   version=locked, actor=actor, ts=ts)
    return locked
