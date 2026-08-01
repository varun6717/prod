#!/usr/bin/env python3
"""`solution_intent_validator` scoring + G1 wiring + the v1 freeze (§9.2, FR-SI-08).

The deterministic, **model-free** half of G1. Three concerns:

  1. ``parse_v1(...)`` — extract the signals from ``solution_intent/v1.md``. Post-ADR-008 this
     is *mechanical*: the section contract is fixed at 18, IDs follow ``D<n>`` / ``R<n>`` /
     ``R<n>.<m>``, coverage footers are machine-readable, and citations carry an explicit line
     range. None of that needs a model, so none of it gets one. (The BRD-era validator handed
     extraction to the skill because BRD prose had no such structure.)

  2. ``evaluate(...)`` — pure function of those signals → :class:`G1Result`: the §9.2 score and
     the **hard preconditions**. It makes no ledger write and takes no operator outcome — a
     validator never auto-advances (FR-XS-13); it surfaces the score + gap list the human gate
     consults.

  3. ``record_g1(...)`` + ``freeze_v1(...)`` — the G1 wiring. On the operator's ``accept`` both
     ledgers are stamped and **v1 is frozen**: hashed, recorded, and made read-only.

The one thing left to the skill is deciding which sentences are **substantive claims** — the
denominator of ``citation_integrity``. That is a judgment ("is this a business fact or connective
prose?") and cannot be regexed honestly, so the skill counts and this module scores.

§9.2 as amended:

    section_coverage   = satisfied must_capture items / total must_capture items
                         # a checklist, not a controlled vocabulary — survives tag removal
    citation_integrity = cited substantive claims / total substantive claims
    si_score = round(100 * (0.7 * section_coverage + 0.3 * citation_integrity))

**Why an `open` item costs score but does not block the gate.** Cite-or-flag requires the author
to declare what the corpus could not answer. If a single unsatisfied `must_capture` made v1
ineligible, the rule would punish honesty and reward a fabricated citation — the exact failure the
whole grounding discipline exists to prevent. So gaps cost coverage points, and the *hard*
precondition is that every gap is **declared in §17**. An undeclared gap blocks; a declared one
merely costs.
"""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Sequence

# Default single project-level threshold (§9.1; UI_INPUT.gates.score_threshold).
THRESHOLD_DEFAULT = 85

# The three grounded tiers a must_capture item may be satisfied at (§3.7) — the same tiers the
# inline citations use. `open` means unsatisfied and must be declared in §17.
GROUNDED_TIERS = ("source", "frame", "operator")
OPEN = "open"
_VALID_COVERAGE = set(GROUNDED_TIERS) | {OPEN}
_VALID_OUTCOMES = ("accept", "reopen")

# v2-only sections: authored by enrichment, not scored here (D-A3).
V2_ONLY = (16, 18)
SECTION_COUNT = 18

_SECTION_HEAD = re.compile(r"^## (\d+)\. (.+)$", re.M)
_COVERAGE = re.compile(r"<!--\s*coverage:\s*\{(.*?)\}\s*-->", re.S)
_CITE = re.compile(r"\[src:\s*([^\]\s]+)\s+L(\d+)[–-](\d+)\]")
# The reason group is OPTIONAL on purpose: a bare "Not applicable" must still be recognised as an
# N/A disposition so it can be REJECTED for having no reason. Requiring the dash here would let the
# lazy form slip through as ordinary content — an omission with better manners (D-A10).
_NA = re.compile(r"Not applicable\s*(?:[—-]\s*(\S.*))?")
_DELIVERABLE_ID = re.compile(r"\*\*(D\d+)\*\*")
_REQ_HEAD = re.compile(r"^#### (R\d+) — (.+)$", re.M)
_REQ_DELIV = re.compile(r"\*\*Deliverable:\*\*\s*(D\d+)")
_OBJECTIVE_ID = re.compile(r"\*\*(O\d+) —")
_CRITERION_ROW = re.compile(r"^\| (S\d+) \|(.+)$", re.M)
_Q_ID = re.compile(r"^- \*\*(Q\d+)", re.M)


# ── parsed signals ────────────────────────────────────────────────────────────
@dataclass(frozen=True)
class SectionSignals:
    """What the parser extracts for one section."""
    id: int
    title: str
    status: str                      # required | required_may_be_empty | conditional
    body: str
    coverage: tuple[str, ...] = ()   # one value per must_capture, in profile order
    na_reason: str | None = None     # "" when it says "Not applicable" with NO reason

    @property
    def is_na(self) -> bool:
        return self.na_reason is not None

    @property
    def has_content(self) -> bool:
        """Present and saying something — content, "None identified", or a dispositioned N/A."""
        stripped = "\n".join(l for l in self.body.splitlines()[1:]
                             if l.strip() and not l.strip().startswith("<!--"))
        return bool(stripped.strip())


@dataclass(frozen=True)
class V1Signals:
    """Everything ``evaluate`` needs, extracted deterministically from v1.md."""
    sections: tuple[SectionSignals, ...]
    deliverables: tuple[str, ...] = ()
    requirements: tuple[str, ...] = ()
    req_deliverable: dict = field(default_factory=dict)     # R -> D
    req_assertions: dict = field(default_factory=dict)      # R -> assertion count
    objectives: tuple[str, ...] = ()
    criteria: dict = field(default_factory=dict)            # S -> [O, ...]
    open_questions: tuple[str, ...] = ()
    citations: tuple[tuple[str, int, int], ...] = ()

    def by_id(self, sid: int) -> SectionSignals | None:
        return next((s for s in self.sections if s.id == sid), None)


def parse_v1(text: str, profile: dict) -> V1Signals:
    """Extract G1's signals from a v1 document. Deterministic; no model, no I/O."""
    prof = {s["id"]: s for s in profile["sections"]}
    heads = [(int(n), t) for n, t in _SECTION_HEAD.findall(text)]
    sections: list[SectionSignals] = []
    for i, (sid, title) in enumerate(heads):
        start = text.index(f"## {sid}. ")
        end = text.index(f"## {heads[i + 1][0]}. ") if i + 1 < len(heads) else len(text)
        body = text[start:end]
        cov: tuple[str, ...] = ()
        if (m := _COVERAGE.search(body)):
            pairs = [p.split(":", 1) for p in m.group(1).split(",") if ":" in p]
            cov = tuple(v.strip() for _, v in sorted(pairs, key=lambda kv: int(kv[0].strip())))
        na = _NA.search(body)
        sections.append(SectionSignals(
            id=sid, title=title,
            status=prof.get(sid, {}).get("status", "required"),
            body=body, coverage=cov,
            na_reason=((na.group(1) or "").strip() if na else None)))

    s7 = next((s.body for s in sections if s.id == 7), "")
    s8 = next((s.body for s in sections if s.id == 8), "")
    s4 = next((s.body for s in sections if s.id == 4), "")
    s15 = next((s.body for s in sections if s.id == 15), "")
    s17 = next((s.body for s in sections if s.id == 17), "")

    req_deliverable, req_assertions = {}, {}
    for block in re.split(r"^#### ", s8, flags=re.M)[1:]:
        rid = block.split(" —")[0].strip()
        if (m := _REQ_DELIV.search(block)):
            req_deliverable[rid] = m.group(1)
        req_assertions[rid] = len(re.findall(rf"^- {re.escape(rid)}\.\d+ — ", block, re.M))

    criteria = {sid: re.findall(r"O\d+", rest) for sid, rest in _CRITERION_ROW.findall(s15)}

    return V1Signals(
        sections=tuple(sections),
        deliverables=tuple(dict.fromkeys(_DELIVERABLE_ID.findall(s7))),
        requirements=tuple(r for r, _ in _REQ_HEAD.findall(s8)),
        req_deliverable=req_deliverable,
        req_assertions=req_assertions,
        objectives=tuple(dict.fromkeys(_OBJECTIVE_ID.findall(s4))),
        criteria=criteria,
        open_questions=tuple(_Q_ID.findall(s17)),
        citations=tuple((p, int(a), int(b)) for p, a, b in _CITE.findall(text)),
    )


# ── scoring + preconditions ───────────────────────────────────────────────────
@dataclass(frozen=True)
class ScoreBreakdown:
    section_coverage: float
    citation_integrity: float
    score: int


@dataclass(frozen=True)
class Precondition:
    """One hard precondition: it holds, or it names exactly what broke it."""
    name: str
    ok: bool
    violations: tuple[str, ...] = ()


@dataclass(frozen=True)
class G1Result:
    breakdown: ScoreBreakdown
    threshold: int
    score_pass: bool
    preconditions: tuple[Precondition, ...] = ()
    gaps: tuple[str, ...] = ()

    @property
    def score(self) -> int:
        return self.breakdown.score

    @property
    def hard_ok(self) -> bool:
        return all(p.ok for p in self.preconditions)

    @property
    def eligible(self) -> bool:
        """The machine soft-gate answer. It does NOT accept — the operator does (D4)."""
        return self.score_pass and self.hard_ok

    @property
    def blockers(self) -> tuple[str, ...]:
        return tuple(v for p in self.preconditions if not p.ok for v in p.violations)


def compute_section_coverage(signals: V1Signals) -> tuple[int, int, float]:
    """satisfied must_capture items / total, across every authored section (§9.2).

    v2-only sections are excluded — they are not authored at v1, so counting them would make a
    complete v1 look 89% covered forever. A dispositioned-N/A conditional is likewise excluded:
    its content legitimately does not exist, and scoring it would punish an honest N/A.
    """
    num = den = 0
    for s in signals.sections:
        if s.id in V2_ONLY or s.is_na:
            continue
        den += len(s.coverage)
        num += sum(1 for c in s.coverage if c in GROUNDED_TIERS)
    return num, den, (num / den) if den else 1.0


def compute_score(section_coverage: float, citation_integrity: float) -> int:
    """The pinned §9.2 weighting — the 0.7/0.3 split stops a document passing on citations alone."""
    return round(100 * (0.7 * section_coverage + 0.3 * citation_integrity))


def check_preconditions(signals: V1Signals, profile: dict, *,
                        unresolved_flags: Sequence[str] = ()) -> tuple[Precondition, ...]:
    """The absolute G1 preconditions (§9.2, D-A23 family 3). Each names what broke it."""
    prof = {s["id"]: s for s in profile["sections"]}
    by_id = {s.id: s for s in signals.sections}

    # H1 — the fixed contract is complete and every required section says something.
    v: list[str] = []
    missing = [n for n in range(1, SECTION_COUNT + 1) if n not in by_id]
    if missing:
        v.append(f"§{missing} missing — the contract is a fixed {SECTION_COUNT} sections")
    for sid, s in by_id.items():
        if sid in V2_ONLY or prof.get(sid, {}).get("status") == "conditional":
            continue
        if not s.has_content:
            v.append(f"§{sid} {s.title!r} is empty — a required section says its content or "
                     f"'None identified', never nothing")
    h1 = Precondition("sections_complete", not v, tuple(v))

    # H2 — conditionals dispositioned, never absent (D-A10 / FR-SI-06).
    v = []
    for sid, p in prof.items():
        if p.get("status") != "conditional":
            continue
        s = by_id.get(sid)
        if s is None:
            # An absent conditional is the precise failure D-A10 names: an omitted section and a
            # forgotten one look identical, so absence is never a legitimate end state.
            v.append(f"§{sid} is conditional and ABSENT — it must be filled or dispositioned N/A")
            continue
        if not s.has_content:
            v.append(f"§{sid} is conditional and empty — it must be filled or dispositioned N/A")
        elif s.is_na and not s.na_reason:
            v.append(f"§{sid} is N/A with no reason — 'Not applicable' alone is an omission "
                     f"with better manners")
    h2 = Precondition("conditionals_dispositioned", not v, tuple(v))

    # H3 — every declared gap is visible in §17. Gaps cost score, not eligibility; an UNDECLARED
    #      gap is what blocks, because that is the one a reader never learns about.
    open_count = sum(1 for s in signals.sections
                     if s.id not in V2_ONLY for c in s.coverage if c == OPEN)
    v = []
    if open_count and not signals.open_questions:
        v.append(f"{open_count} must_capture item(s) are `open` but §17 lists no open question")
    elif open_count > len(signals.open_questions):
        v.append(f"{open_count} `open` item(s) but only {len(signals.open_questions)} §17 "
                 f"question(s) — every gap must be declared where a reader will see it")
    h3 = Precondition("gaps_declared", not v, tuple(v))

    # H4 — §15 ↔ §4, both directions (D-A11's mechanical guardrail).
    v = []
    objectives = set(signals.objectives)
    if not objectives:
        v.append("§4 declares no objective IDs (O<n>)")
    traced: set[str] = set()
    for cid, objs in signals.criteria.items():
        real = [o for o in objs if o in objectives]
        traced |= set(real)
        if not real:
            v.append(f"§15 {cid} traces to no §4 objective — an orphaned criterion")
    for o in sorted(objectives - traced):
        v.append(f"§4 {o} has no §15 success criterion — an unmeasurable objective")
    h4 = Precondition("trace_15_to_4", not v, tuple(v))

    # H5 — §8 → §7, both directions (D-A14; load-bearing, it builds the Jira hierarchy).
    v = []
    deliverables = set(signals.deliverables)
    if not deliverables:
        v.append("§7 declares no deliverable IDs (D<n>)")
    if not signals.requirements:
        v.append("§8 declares no requirement IDs (R<n>)")
    used: set[str] = set()
    for rid in signals.requirements:
        d = signals.req_deliverable.get(rid)
        if d is None:
            v.append(f"§8 {rid} carries no `Deliverable:` — an unbuildable requirement")
        elif d not in deliverables:
            v.append(f"§8 {rid} names deliverable {d}, which §7 does not declare")
        else:
            used.add(d)
    for d in sorted(deliverables - used):
        v.append(f"§7 {d} has no requirement — an unjustified deliverable")
    h5 = Precondition("trace_8_to_7", not v, tuple(v))

    # H6 — every requirement carries enumerated assertions (FR-SI-04). Without them Arm 1 has
    #      nothing to match per-assertion, and §16 (hence story) granularity collapses.
    v = [f"§8 {rid} has no enumerated assertions ({rid}.1, {rid}.2, …)"
         for rid in signals.requirements if signals.req_assertions.get(rid, 0) < 1]
    h6 = Precondition("assertions_enumerated", not v, tuple(v))

    # H7 — flags dispositioned (D4's backstop).
    h7 = Precondition("flags_resolved", not unresolved_flags,
                      tuple(f"flag not dispositioned: {f}" for f in unresolved_flags))

    return (h1, h2, h3, h4, h5, h6, h7)


def evaluate(signals: V1Signals, profile: dict, *,
             cited_substantive_claims: int, total_substantive_claims: int,
             unresolved_flags: Sequence[str] = (),
             threshold: int = THRESHOLD_DEFAULT,
             gaps: Sequence[str] = ()) -> G1Result:
    """Score v1 and decide G1 eligibility — pure, model-free (§9.2)."""
    if total_substantive_claims < 0 or cited_substantive_claims < 0:
        raise ValueError("claim counts must be non-negative")
    if cited_substantive_claims > total_substantive_claims:
        raise ValueError("cited claims cannot exceed total claims")

    _, _, sc = compute_section_coverage(signals)
    ci = (cited_substantive_claims / total_substantive_claims) if total_substantive_claims else 1.0
    breakdown = ScoreBreakdown(sc, ci, compute_score(sc, ci))
    pre = check_preconditions(signals, profile, unresolved_flags=unresolved_flags)
    return G1Result(breakdown=breakdown, threshold=threshold,
                    score_pass=breakdown.score >= threshold,
                    preconditions=pre, gaps=tuple(gaps))


# ── G1 wiring + the freeze ────────────────────────────────────────────────────
def lock_version(version: int, outcome: str) -> int:
    """FR-XS-14: accept → v``version`` (locked as-is); reopen → v``version+1``."""
    if outcome not in _VALID_OUTCOMES:
        raise ValueError(f"outcome must be one of {_VALID_OUTCOMES}; got {outcome!r}")
    return version if outcome == "accept" else version + 1


def freeze_v1(si_dir: str | Path, *, version: int = 1, ts: str | None = None) -> dict:
    """Freeze ``solution_intent/v1.md`` at G1 accept — hash it, record it, make it read-only.

    v1 is snapshotted because (D-A2): it is the audit record of what we believed *before* looking
    at the code; the v1→v2 diff is the enrichment stage's whole value story; and **G1 accepted
    this document** — if v1 can be mutated afterwards, the artifact the operator accepted no
    longer exists and the gate stops meaning anything.

    The hash is what makes the freeze checkable rather than merely intended: read-only is a file
    mode anyone can flip, but a recorded digest makes a later edit *detectable*.
    """
    d = Path(si_dir)
    v1 = d / "v1.md"
    if not v1.is_file():
        raise FileNotFoundError(f"cannot freeze: no v1.md at {v1}")
    digest = hashlib.sha256(v1.read_bytes()).hexdigest()
    record = {"artifact": "v1.md", "version": version, "sha256": digest,
              "frozen_at": ts or _now_iso(), "bytes": v1.stat().st_size}
    (d / "v1.frozen.json").write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    v1.chmod(0o444)                       # advisory; the digest above is the real guard
    return record


def verify_frozen(si_dir: str | Path) -> bool:
    """True iff v1.md still hashes to what was recorded at the freeze."""
    d = Path(si_dir)
    rec = json.loads((d / "v1.frozen.json").read_text(encoding="utf-8"))
    return hashlib.sha256((d / "v1.md").read_bytes()).hexdigest() == rec["sha256"]


def _now_iso() -> str:
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def record_g1(ledger_dir, *, result: G1Result, outcome: str, version: int,
              si_dir: str | Path | None = None, actor: str = "vmunjal",
              ts: str | None = None):
    """Wire the validator into G1: stamp both ledgers, and on accept FREEZE v1.

    The validator is a soft gate — it never advances itself. The human supplies ``outcome``;
    this records it. An ``accept`` on a non-eligible result is **refused**: the hard
    preconditions are absolute (§9.1), so acceptance cannot pass with an undispositioned
    conditional, a broken trace, or an unresolved flag. ``reopen`` is always allowed.

    Returns ``(locked_version, freeze_record | None)``.
    """
    if outcome not in _VALID_OUTCOMES:
        raise ValueError(f"outcome must be one of {_VALID_OUTCOMES}; got {outcome!r}")
    if outcome == "accept" and not result.eligible:
        raise ValueError(
            "G1 accept refused: hard preconditions not met (§9.1) — "
            f"score_pass={result.score_pass}; blockers={list(result.blockers)}")

    import telemetry  # lazy: pulls in `ledger` (schema I/O)

    locked = lock_version(version, outcome)
    em = telemetry.Emitter(ledger_dir, run_id=_run_id(ledger_dir), domain="payment_brand",
                           tool=_runtime_tool(ledger_dir))
    em.validation(artifact="si_v1", score=float(result.score), ts=ts)
    em.gate_decision(gate="G1", outcome=outcome, actor=actor, version=locked, ts=ts)
    telemetry.gate(Path(ledger_dir) / "decisions.jsonl", gate="G1", outcome=outcome,
                   version=locked, actor=actor, ts=ts)

    frozen = None
    if outcome == "accept" and si_dir is not None:
        frozen = freeze_v1(si_dir, version=locked, ts=ts)
    return locked, frozen


def _run_id(ledger_dir) -> str:
    rs = json.loads((Path(ledger_dir) / "run_state.json").read_text(encoding="utf-8"))
    return rs.get("run_id", "unknown")


def _runtime_tool(ledger_dir, default: str = "claude") -> str:
    """Read ``runtime_tool`` from the run's immutable ``UI_INPUT.yaml`` so G1 telemetry carries the
    run's actual tool rather than a hardcoded default (TASK-060)."""
    import yaml
    ui = Path(ledger_dir).parent / "UI_INPUT.yaml"
    if not ui.exists():
        return default
    return (yaml.safe_load(ui.read_text(encoding="utf-8")) or {}).get("runtime_tool") or default


# ──────────────────────────────────────────────────────────────────────────────
# Proof. Run: python3 core/scripts/solution_intent_validator.py
#   PASS — the TASK-109 authored v1 scores, is eligible, the operator accepts, v1 freezes.
#   FAIL — the purpose-built broken v1 names EVERY violated precondition and refuses accept.
# ──────────────────────────────────────────────────────────────────────────────
def _demo() -> None:
    import shutil
    import tempfile

    import ledger
    import yaml

    root = Path(__file__).resolve().parents[2]
    profile = yaml.safe_load(
        (root / "core/profiles/payment_brand/si_profile.payment_brand.yaml").read_text())
    T = "2026-08-01T00:00:00Z"

    good = parse_v1((root / "fixtures/si_author/v1.md").read_text(encoding="utf-8"), profile)
    bad = parse_v1((root / "fixtures/si_validator/si_fail.md").read_text(encoding="utf-8"), profile)

    ok = evaluate(good, profile, cited_substantive_claims=118, total_substantive_claims=122)
    n, d, _ = compute_section_coverage(good)
    print("PASS case — fixtures/si_author/v1.md (the TASK-109 authored v1):")
    print(f"  section_coverage={ok.breakdown.section_coverage:.3f} ({n}/{d} must_capture items)  "
          f"citation_integrity={ok.breakdown.citation_integrity:.3f}  score={ok.score}")
    for p in ok.preconditions:
        print(f"    {'✓' if p.ok else '✗'} {p.name}")
    assert ok.hard_ok, ok.blockers
    assert ok.eligible, ok

    fail = evaluate(bad, profile, cited_substantive_claims=4, total_substantive_claims=12)
    print(f"\nFAIL case — fixtures/si_validator/si_fail.md: score={fail.score} "
          f"eligible={fail.eligible}")
    broken = [p.name for p in fail.preconditions if not p.ok]
    for p in fail.preconditions:
        if not p.ok:
            print(f"    ✗ {p.name}")
            for v in p.violations[:2]:
                print(f"        - {v}")
    # every precondition except the flag one is broken by construction
    expected = {"sections_complete", "conditionals_dispositioned", "gaps_declared",
                "trace_15_to_4", "trace_8_to_7", "assertions_enumerated"}
    assert expected <= set(broken), f"expected all of {expected}, got {broken}"
    assert not fail.eligible

    # A PASSING score with one unresolved flag still fails — D4's backstop.
    flagged = evaluate(good, profile, cited_substantive_claims=122, total_substantive_claims=122,
                       unresolved_flags=["scope_ripple: settlement reconciliation"])
    assert flagged.score_pass and flagged.hard_ok is False and not flagged.eligible
    assert [p.name for p in flagged.preconditions if not p.ok] == ["flags_resolved"]
    print(f"\nbackstop: score={flagged.score} (passing) but 1 unresolved flag → "
          f"eligible={flagged.eligible} (good)")

    # And the honesty property: v1 declares 5 gaps and still passes. If an `open` item blocked
    # G1, cite-or-flag would punish honesty and reward a fabricated citation.
    assert ok.score < 100 and ok.eligible, "declared gaps must cost score, not eligibility"
    print(f"honesty: v1 declares gaps (coverage {ok.breakdown.section_coverage:.3f}) and still "
          f"passes at {ok.score} — gaps cost score, not eligibility")

    # ── G1 wiring + the freeze, against a real ledger and a real v1. ──
    with tempfile.TemporaryDirectory(prefix="si-validator-proof-") as tmp:
        run = Path(tmp)
        led = ledger.init_ledger(run / "ledger", run_id="r-2026-08-01-si1")
        si = run / "solution_intent"
        si.mkdir()
        shutil.copy2(root / "fixtures/si_author/v1.md", si / "v1.md")

        try:
            record_g1(led, result=fail, outcome="accept", version=1, si_dir=si, ts=T)
        except ValueError:
            print("\nnegative: G1 accept on an ineligible v1 -> REFUSED (good)")
        else:
            raise AssertionError("accept on a non-eligible result must be refused")

        v2, frozen = record_g1(led, result=fail, outcome="reopen", version=1, si_dir=si, ts=T)
        assert v2 == 2 and frozen is None, (v2, frozen)
        assert not (si / "v1.frozen.json").exists(), "reopen must NOT freeze"

        v1v, frozen = record_g1(led, result=ok, outcome="accept", version=1, si_dir=si, ts=T)
        assert v1v == 1 and frozen is not None
        print(f"reopen → v{v2} (no freeze);  accept → v{v1v} frozen "
              f"sha256={frozen['sha256'][:12]}… ({frozen['bytes']} bytes)")
        assert verify_frozen(si), "the freeze record must match the file"
        assert (si / "v1.md").stat().st_mode & 0o222 == 0, "v1.md must be read-only after freeze"

        # Tampering is DETECTABLE — that is what the digest buys over a file mode.
        (si / "v1.md").chmod(0o644)
        (si / "v1.md").write_text("tampered\n", encoding="utf-8")
        assert not verify_frozen(si), "a post-freeze edit must be detectable"
        print("tamper check: editing v1 after the freeze is detected by the recorded digest")

        report = ledger.validate_ledger(led)
        assert all(not e for e in report.values()), report
        tel = [json.loads(l) for l in (led / "telemetry.jsonl").read_text().splitlines() if l.strip()]
        vals = [e for e in tel if e["event"] == "validation" and e["artifact"] == "si_v1"]
        gates = [e for e in tel if e["event"] == "gate_decision" and e["gate"] == "G1"]
        assert len(vals) == 2 and {e["outcome"] for e in gates} == {"reopen", "accept"}
        print(f"ledgers: {len(vals)} validation(si_v1) + {len(gates)} gate_decision(G1) events, "
              f"all schema-valid")

    print("\nPASS — §9.2 scores 0.7×section_coverage + 0.3×citation_integrity deterministically; "
          "every hard precondition is named when broken; accept is the operator's and is refused "
          "when ineligible; accept freezes v1 with a tamper-detectable digest (FR-XS-13/14, D-A2).")


if __name__ == "__main__":
    _demo()
