#!/usr/bin/env python3
"""`brd_validator` scoring + G1 gate wiring — the deterministic soft-gate (§9.2, FR-BR-09).

The `brd_validator` skill (`core/skills/brd_validator.skill.md`) is the *reader*: it parses
`BRD.md`'s per-section ``<!-- coverage: {...} -->`` footers + inline citations against the
domain `brd_profile`, classifying each required topic and counting cited-vs-substantive
claims. That extraction is the model's job. This module is the part that MUST be
deterministic and **model-free**: the §9.2 score arithmetic and the three hard-precondition
predicates that decide **G1 eligibility**. Same parsed signals → same score + same verdict,
every time — so "0.7/0.3 weighting" and "cannot pass with an unsatisfied required topic or an
unresolved flag" are *tested*, not merely asserted. There is no model call anywhere here.

Two stages, mirroring `gate.py` (which does the same split for the onboarding gate):

  1. ``evaluate(...)`` — pure function of the parsed signals → :class:`G1Result`: the score,
     its breakdown, the three hard preconditions, and ``eligible`` (all three hold). It makes
     NO ledger write and takes NO operator outcome — a validator **never auto-advances**
     (FR-XS-13); it only surfaces the score + gap list the human gate consults.

  2. ``record_g1(...)`` — the G1 **wiring**: given the report and the **operator's** chosen
     ``outcome`` (``accept`` | ``reopen``), it stamps both ledgers — the ``validation`` +
     ``gate_decision`` telemetry events (§8.1) and the ``decisions.jsonl`` ``gate`` audit
     record (§3.6) — and returns the locked artifact version (FR-XS-14: accept → BRD vN;
     reopen → vN+1). It **refuses an ``accept`` when the artifact is not eligible** — the
     hard preconditions are absolute (§9.1), so acceptance cannot pass with an unsatisfied
     required topic or an unresolved flag (D4: G1 is the backstop for any missed flag).

§9.2:
    topic_coverage     = satisfied_required_topics / total_required_topics
    citation_integrity = cited_substantive_claims / total_substantive_claims
    brd_score = round(100 * (0.7 * topic_coverage + 0.3 * citation_integrity))
    G1 passes iff  brd_score >= threshold  AND (hard) every required topic satisfied/waived
                   AND (hard) all flags resolved/recorded in decisions.jsonl.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Sequence

# Default single project-level threshold (§9.1; UI_INPUT.gates.score_threshold).
THRESHOLD_DEFAULT = 85

# The three grounded coverage tiers a topic's footer may carry (§3.7) — the same tiers the
# inline citations use (`[src: …]` / `[frame]` / `[operator]`). A topic at one of these is
# "satisfied": its must_capture is met and grounded, not `[TBD — unsourced]`.
GROUNDED_TIERS = ("source", "frame", "operator")
# A required topic the operator explicitly excused (FR-BR: required satisfied *or waived*).
WAIVED = "waived"
# An unsatisfied topic — must_capture not met / marked `[TBD — unsourced]`.
OPEN = "open"

_VALID_COVERAGE = set(GROUNDED_TIERS) | {WAIVED, OPEN}
_VALID_OUTCOMES = ("accept", "reopen")


@dataclass(frozen=True)
class TopicResult:
    """One topic's coverage as parsed from the BRD footers + the profile's ``required`` flag.

    ``coverage`` ∈ ``source`` | ``frame`` | ``operator`` (grounded/satisfied) | ``waived``
    (operator-excused) | ``open`` (unsatisfied). The skill builds one of these per
    ``requirements[].topic`` in the merged authoring plan.
    """
    topic: str
    required: bool
    coverage: str

    def __post_init__(self) -> None:
        if self.coverage not in _VALID_COVERAGE:
            raise ValueError(
                f"topic {self.topic!r}: coverage {self.coverage!r} not in {sorted(_VALID_COVERAGE)}"
            )

    @property
    def satisfied(self) -> bool:
        return self.coverage in GROUNDED_TIERS


@dataclass(frozen=True)
class ScoreBreakdown:
    topic_coverage: float       # satisfied_required / scored_required (waived excluded)
    citation_integrity: float   # cited_substantive / total_substantive
    score: int                  # round(100 * (0.7*tc + 0.3*ci))


@dataclass(frozen=True)
class G1Result:
    """The validator's full verdict — the score + the three hard preconditions + eligibility.

    ``eligible`` is the machine soft-gate answer: ``score_pass AND required_satisfied AND
    flags_resolved`` (§9.2). It is what the human G1 gate consults; it does NOT itself accept.
    """
    breakdown: ScoreBreakdown
    threshold: int
    score_pass: bool                      # score >= threshold
    required_satisfied: bool              # hard: every required topic satisfied or waived
    flags_resolved: bool                  # hard: no flag left unresolved in decisions.jsonl
    unsatisfied_required: tuple = ()      # required topics still `open` (the G1 blockers)
    unresolved_flags: tuple = ()          # flags surfaced but not dispositioned
    gaps: tuple = field(default=())       # section-level gap suggestions for in-chat fill-in

    @property
    def score(self) -> int:
        return self.breakdown.score

    @property
    def eligible(self) -> bool:
        return self.score_pass and self.required_satisfied and self.flags_resolved


def compute_topic_coverage(topics: Sequence[TopicResult]) -> tuple[int, int, float]:
    """``satisfied_required / total_required`` (§9.2). Waived required topics are excused —
    removed from BOTH numerator and denominator (an operator-excused topic neither earns nor
    costs coverage). Optional topics never enter the ratio. Returns ``(num, den, ratio)``;
    ``ratio = 1.0`` when no required topic remains to score (vacuously complete).
    """
    scored = [t for t in topics if t.required and t.coverage != WAIVED]
    den = len(scored)
    num = sum(1 for t in scored if t.satisfied)
    ratio = (num / den) if den else 1.0
    return num, den, ratio


def compute_score(topic_coverage: float, citation_integrity: float) -> int:
    """The pinned §9.2 weighting — round(100 * (0.7*tc + 0.3*ci)). The 0.7/0.3 split prevents
    a BRD passing on citations alone."""
    return round(100 * (0.7 * topic_coverage + 0.3 * citation_integrity))


def evaluate(
    *,
    topics: Sequence[TopicResult],
    cited_substantive_claims: int,
    total_substantive_claims: int,
    unresolved_flags: Sequence[str] = (),
    threshold: int = THRESHOLD_DEFAULT,
    gaps: Sequence[str] = (),
) -> G1Result:
    """Score the BRD and decide G1 eligibility — pure, model-free (§9.2).

    Args:
      topics:                    one :class:`TopicResult` per profile ``requirements[].topic``.
      cited_substantive_claims:  count of substantive claims carrying a valid inline citation.
      total_substantive_claims:  count of substantive claims (cited or `[TBD — unsourced]`).
      unresolved_flags:          flags `code_impact` returned that have NO matching disposition
                                 in ``decisions.jsonl`` (the skill cross-checks; empty ⇒ all
                                 resolved). Their presence fails the absolute flag precondition.
      threshold:                 the G1 score bar (default 85, §9.1).
      gaps:                      section-level gap suggestions for in-chat fill-in (FR-BR-09).

    Returns a :class:`G1Result`. No I/O, no operator outcome — eligibility only.
    """
    if total_substantive_claims < 0 or cited_substantive_claims < 0:
        raise ValueError("claim counts must be non-negative")
    if cited_substantive_claims > total_substantive_claims:
        raise ValueError("cited claims cannot exceed total claims")

    _, _, tc = compute_topic_coverage(topics)
    # No substantive claim ⇒ citation integrity is vacuously 1.0 (nothing to ground).
    ci = (cited_substantive_claims / total_substantive_claims) if total_substantive_claims else 1.0
    breakdown = ScoreBreakdown(topic_coverage=tc, citation_integrity=ci, score=compute_score(tc, ci))

    unsatisfied = tuple(t.topic for t in topics if t.required and t.coverage == OPEN)
    return G1Result(
        breakdown=breakdown,
        threshold=threshold,
        score_pass=breakdown.score >= threshold,
        required_satisfied=not unsatisfied,          # every required topic satisfied or waived
        flags_resolved=not unresolved_flags,
        unsatisfied_required=unsatisfied,
        unresolved_flags=tuple(unresolved_flags),
        gaps=tuple(gaps),
    )


def lock_version(version: int, outcome: str) -> int:
    """The FR-XS-14 versioned lock: accept → BRD v``version`` (locked as-is); reopen → v``version+1``
    (a fresh draft cycle). Pure."""
    if outcome not in _VALID_OUTCOMES:
        raise ValueError(f"outcome must be one of {_VALID_OUTCOMES}; got {outcome!r}")
    return version if outcome == "accept" else version + 1


def record_g1(
    ledger_dir,
    *,
    result: G1Result,
    outcome: str,
    version: int,
    actor: str = "vmunjal",
    ts: str | None = None,
):
    """Wire the validator into G1: stamp both ledgers for the operator's decision (§8.1 / §3.6).

    The validator is a **soft gate** — it never advances itself. The human supplies ``outcome``
    (``accept`` | ``reopen``); this records it. Because the hard preconditions are absolute
    (§9.1), an ``accept`` on a non-eligible result is refused here — acceptance cannot pass
    with an unsatisfied required topic or an unresolved flag (D4 backstop). ``reopen`` is
    always allowed.

    Writes, in order: the ``validation`` telemetry event (the score, always); the
    ``gate_decision`` telemetry event (M03 first-pass-acceptance feed); the ``decisions.jsonl``
    ``gate`` audit twin (who/when/outcome/version, NFR-03). Returns the locked version
    (``lock_version``).
    """
    if outcome not in _VALID_OUTCOMES:
        raise ValueError(f"outcome must be one of {_VALID_OUTCOMES}; got {outcome!r}")
    if outcome == "accept" and not result.eligible:
        raise ValueError(
            "G1 accept refused: hard preconditions not met (§9.1) — "
            f"score_pass={result.score_pass} required_satisfied={result.required_satisfied} "
            f"flags_resolved={result.flags_resolved} "
            f"(unsatisfied={result.unsatisfied_required} unresolved_flags={result.unresolved_flags})"
        )

    import telemetry  # lazy: telemetry/decisions pull in `ledger` (schema I/O)

    locked = lock_version(version, outcome)
    em = telemetry.Emitter(ledger_dir, run_id=_run_id(ledger_dir), domain="payment_brand",
                           tool=_runtime_tool(ledger_dir))
    em.validation(artifact="brd", score=float(result.score), ts=ts)
    em.gate_decision(gate="G1", outcome=outcome, actor=actor, version=locked, ts=ts)
    from pathlib import Path
    telemetry.gate(Path(ledger_dir) / "decisions.jsonl", gate="G1", outcome=outcome,
                   version=locked, actor=actor, ts=ts)
    return locked


def _run_id(ledger_dir) -> str:
    """Read the run_id seeded into run_state.json so the validator's events carry the run's
    envelope without the caller threading it (the skill runs inside an active run)."""
    import json
    from pathlib import Path
    rs = json.loads((Path(ledger_dir) / "run_state.json").read_text(encoding="utf-8"))
    return rs.get("run_id", "unknown")


def _runtime_tool(ledger_dir, default: str = "claude") -> str:
    """Read ``runtime_tool`` from the run's immutable ``UI_INPUT.yaml`` (written verbatim into the
    workspace at Generate — FR-XS-16) so G1/G2 telemetry envelopes carry the run's actual tool
    (``claude`` | ``copilot``, §8.1 enum) instead of a hardcoded default (TASK-060). The validator
    runs in-session inside the run dir, so UI_INPUT.yaml is ``ledger_dir``'s sibling — same read
    pattern as ``_run_id``. Falls back to ``default`` when no UI_INPUT.yaml is present (the
    standalone proof), preserving prior behaviour."""
    import yaml
    from pathlib import Path
    ui = Path(ledger_dir).parent / "UI_INPUT.yaml"
    if not ui.exists():
        return default
    cfg = yaml.safe_load(ui.read_text(encoding="utf-8")) or {}
    return cfg.get("runtime_tool") or default


# ──────────────────────────────────────────────────────────────────────────────
# Proof (TASK-043 fixture/proof) — runnable, deterministic. Run: python3 core/scripts/brd_validator.py
#   Two BRDs against the payment_brand required set {mandate, card_brand, certification,
#   routing, compliance_deadline}:
#     FAIL — one required topic (`routing`) unsatisfied → score below bar AND hard precondition
#            broken → eligible=False; an `accept` is refused; operator `reopen` → v2.
#     PASS — every required topic satisfied, citations clean, no open flags → eligible=True;
#            operator `accept` locks BRD v1; both ledgers stamped.
# ──────────────────────────────────────────────────────────────────────────────
def _demo() -> None:
    import json
    import tempfile
    from pathlib import Path

    import ledger

    T = "2026-06-22T00:00:00Z"  # fixed ts → deterministic proof

    # The five required payment_brand topics (brd_profile.payment_brand.yaml) + optionals.
    def topics(routing_cov: str):
        return [
            TopicResult("mandate", True, "source"),
            TopicResult("brand_rules", False, "operator"),
            TopicResult("card_brand", True, "source"),
            TopicResult("certification", True, "frame"),
            TopicResult("routing", True, routing_cov),     # the lever between the two cases
            TopicResult("settlement", False, OPEN),
            TopicResult("compliance_deadline", True, "source"),
            TopicResult("reporting", False, OPEN),
        ]

    # ── FAIL case: routing left `open`; one substantive claim un-cited. ──
    fail = evaluate(topics=topics(OPEN), cited_substantive_claims=23, total_substantive_claims=25,
                    gaps=["code_impact: routing impact unsourced — probe affected brand handlers"])
    print("FAIL case (required topic `routing` unsatisfied):")
    print(f"  topic_coverage={fail.breakdown.topic_coverage:.2f}  "
          f"citation_integrity={fail.breakdown.citation_integrity:.2f}  score={fail.score}")
    print(f"  score_pass={fail.score_pass} required_satisfied={fail.required_satisfied} "
          f"flags_resolved={fail.flags_resolved} → eligible={fail.eligible}")
    print(f"  unsatisfied_required={fail.unsatisfied_required}  gaps={fail.gaps}")
    assert fail.unsatisfied_required == ("routing",), fail.unsatisfied_required
    assert not fail.required_satisfied and not fail.eligible
    # 4/5 required satisfied (0.8) + 23/25 cited (0.92) → round(100*(0.56+0.276))=84 < 85.
    assert fail.score == 84, fail.score
    assert not fail.score_pass

    # ── PASS case: routing grounded; citations clean; no open flags. ──
    ok = evaluate(topics=topics("source"), cited_substantive_claims=25, total_substantive_claims=25)
    print("\nPASS case (every required topic satisfied):")
    print(f"  topic_coverage={ok.breakdown.topic_coverage:.2f}  "
          f"citation_integrity={ok.breakdown.citation_integrity:.2f}  score={ok.score}")
    print(f"  score_pass={ok.score_pass} required_satisfied={ok.required_satisfied} "
          f"flags_resolved={ok.flags_resolved} → eligible={ok.eligible}")
    assert ok.score == 100 and ok.eligible, ok

    # An unresolved code_impact flag alone breaks G1 even with a perfect score (D4 backstop).
    flagged = evaluate(topics=topics("source"), cited_substantive_claims=25,
                       total_substantive_claims=25, unresolved_flags=["scope_ripple: settlement/reconciler"])
    assert flagged.score == 100 and not flagged.eligible and not flagged.flags_resolved, flagged
    print(f"\nbackstop: perfect score but 1 unresolved flag → eligible={flagged.eligible} (good)")

    # ── G1 wiring against a real ledger: accept refused on FAIL; reopen → v2; PASS accept → v1. ──
    with tempfile.TemporaryDirectory(prefix="brd-validator-proof-") as tmp:
        led = ledger.init_ledger(Path(tmp) / "ledger", run_id="r-brd-001")

        # Soft-gate: an accept on a non-eligible BRD is refused (hard preconditions are absolute).
        try:
            record_g1(led, result=fail, outcome="accept", version=1, ts=T)
        except ValueError:
            print("\nnegative: G1 accept on unsatisfied BRD -> REFUSED (good)")
        else:
            raise AssertionError("accept on non-eligible result must be refused")

        # Operator reopens the failed draft → v2 (FR-XS-14 increment); both ledgers stamped.
        v2 = record_g1(led, result=fail, outcome="reopen", version=1, ts=T)
        assert v2 == 2, v2

        # Operator accepts the passing BRD → locked as v1.
        v1 = record_g1(led, result=ok, outcome="accept", version=1, ts=T)
        assert v1 == 1, v1
        print(f"reopen failed draft → BRD v{v2};  accept passing draft → locked BRD v{v1}")

        # Both ledgers validate and carry the events the metrics derive from (M03/M04).
        report = ledger.validate_ledger(led)
        assert all(not e for e in report.values()), report
        tel = [json.loads(l) for l in (led / "telemetry.jsonl").read_text().splitlines() if l.strip()]
        dec = [json.loads(l) for l in (led / "decisions.jsonl").read_text().splitlines() if l.strip()]
        val_events = [e for e in tel if e["event"] == "validation" and e["artifact"] == "brd"]
        gate_events = [e for e in tel if e["event"] == "gate_decision" and e["gate"] == "G1"]
        gate_audit = [d for d in dec if d["kind"] == "gate" and d["gate"] == "G1"]
        assert len(val_events) == 2, val_events                       # one per record_g1 call
        assert {e["outcome"] for e in gate_events} == {"reopen", "accept"}, gate_events
        assert len(gate_audit) == 2, gate_audit                       # decisions.jsonl audit twins
        print(f"ledgers: {len(val_events)} validation + {len(gate_events)} gate_decision events, "
              f"{len(gate_audit)} decisions.jsonl gate records — all schema-valid")

    print("\nPASS — §9.2 score is deterministic + 0.7/0.3-weighted; an unsatisfied required topic "
          "OR an unresolved flag fails G1 regardless of score; the gate never auto-advances "
          "(accept is the operator's, refused when ineligible); accept→vN, reopen→vN+1 (FR-XS-13/14).")


if __name__ == "__main__":
    _demo()
