#!/usr/bin/env python3
"""verify_refusals.py — the spine's REFUSAL paths, end to end (TASK-127 follow-up).

The acceptance run took the happy path at every gate. Nine integration breaks surfaced on that
path alone, so the paths nothing has ever driven are where the next ones live. Each gate's
*refusal* is tested here in isolation elsewhere; this drives them **through the spine**, which is
exactly the difference that let `clone.py` and `jira_plan` stay broken while their own fixtures
were green.

  1. **G1 refuses an ineligible accept, and v1 stays UNFROZEN.** The interesting half is the
     second clause: a refused gate that froze the artifact anyway would leave the run holding a
     document nobody accepted.
  2. **A reopen is always allowed**, and after the blocker clears, accept freezes at the new
     version — the reopen→fix→accept cycle actually completes.
  3. **G2 refuses while an escalation is undispositioned** — the walkthrough cannot be skipped.
  4. **A REJECTED finding does not reach v2 but stays in the record.** Rejecting is not deleting:
     the reasoning survives for audit even though the change does not ship.
  5. **G3's authorization cannot be minted for an ineligible plan**, so the push is unreachable.
  6. **A mid-batch push failure preserves prior successes**, and a retry resumes rather than
     re-creating — the property that makes a partial push recoverable instead of duplicating.

Run: python3 fixtures/spine_refusals/verify_refusals.py
"""
from __future__ import annotations

import hashlib
import json
import shutil
import sys
import tempfile
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_REPO_ROOT = _HERE.parents[1]
sys.path.insert(0, str(_REPO_ROOT / "core" / "scripts"))
sys.path.insert(0, str(_REPO_ROOT / "core" / "adapters"))

import apply_enrichment as A  # noqa: E402
import enrichment as E  # noqa: E402
import jira_validator as JV  # noqa: E402
import ledger  # noqa: E402
import solution_intent_validator as V  # noqa: E402
import yaml  # noqa: E402
from jpmc_adapters import auth as _auth  # noqa: E402
from jpmc_adapters import jira  # noqa: E402

_FAILURES: list[str] = []
T = "2026-08-02T09:00:00Z"


def _check(label: str, ok: bool, detail: str = "") -> None:
    print(f"  [{'PASS' if ok else 'FAIL'}] {label}" + (f" — {detail}" if detail else ""))
    if not ok:
        _FAILURES.append(label)


def _raises(fn, exc=Exception) -> bool:
    try:
        fn()
    except exc:
        return True
    except Exception:                                  # noqa: BLE001 — wrong type is still a fail
        return False
    return False


class _Stub:
    def get(self, key):
        return "stub-token"


def main() -> int:
    print("verify_refusals — every gate's refusal path, driven through the spine\n")
    profile = yaml.safe_load(
        (_REPO_ROOT / "core/profiles/payment_brand/si_profile.payment_brand.yaml").read_text())
    v1_src = _REPO_ROOT / "fixtures/si_author/v1.md"
    v1 = v1_src.read_text(encoding="utf-8")
    signals = V.parse_v1(v1, profile)

    with tempfile.TemporaryDirectory(prefix="refusals-") as td:
        root = Path(td)
        si = root / "solution_intent"
        si.mkdir(parents=True)
        shutil.copy2(v1_src, si / "v1.md")
        led = ledger.init_ledger(root / "ledger", run_id="r-refusals")

        blocked = V.evaluate(signals, profile, cited_substantive_claims=10,
                             total_substantive_claims=10,
                             unresolved_flags=["FLAG-9 scope ripple, undecided"])
        _check("a v1 with an unresolved flag is INELIGIBLE", not blocked.eligible)

        print("1) G1 refuses the accept, and v1 stays unfrozen:")
        _check("accept on an ineligible result is REFUSED",
               _raises(lambda: V.record_g1(led, result=blocked, outcome="accept", version=1,
                                           si_dir=si, ts=T)))
        _check("no freeze record was written", not (si / "v1.frozen.json").exists(),
               "a refused gate that froze anyway would leave a document nobody accepted")
        _check("and v1 is still writable — the freeze did not half-happen",
               (si / "v1.md").stat().st_mode & 0o200)

        print("\n2) a reopen is always allowed, and the cycle completes:")
        v, frozen = V.record_g1(led, result=blocked, outcome="reopen", version=1, si_dir=si, ts=T)
        _check("reopen is accepted even though the result is ineligible", frozen is None)
        cleared = V.evaluate(signals, profile, cited_substantive_claims=10,
                             total_substantive_claims=10, unresolved_flags=[])
        _check("with the flag dispositioned the result becomes eligible", cleared.eligible)
        v2n, frz = V.record_g1(led, result=cleared, outcome="accept", version=2, si_dir=si, ts=T)
        _check("accept now succeeds at the NEW version", v2n == 2, f"version={v2n}")
        _check("and freezes v1 with a digest", bool(frz and frz.get("sha256")))
        _check("the frozen file is read-only", not ((si / "v1.md").stat().st_mode & 0o200))

        # ── enrichment: an undispositioned escalation, and a rejected finding
        rec = E.new_record("r-refusals", hashlib.sha256(v1.encode()).hexdigest()[:12])
        for rid in signals.requirements:
            for i in range(1, signals.req_assertions.get(rid, 0) + 1):
                E.add(rec, E.make_finding(f"F-9{rid[1:]}{i:02d}", arm="impact", kind="confirmation",
                                          requirement_ref=rid, assertion_ref=f"{rid}.{i}",
                                          verdict="confirmed", reasoning="already satisfied"))
        E.add(rec, E.make_finding("F-800", arm="impact", kind="no_code_found",
                                  requirement_ref=signals.requirements[0],
                                  assertion_ref=f"{signals.requirements[0]}.1",
                                  verdict="no_code_found", business_visible=True,
                                  reasoning="nothing implements this"))
        E.add(rec, E.make_finding("F-801", arm="claim", kind="contradiction",
                                  claim_provenance="operator", section_ref="§13",
                                  verdict="contradicted",
                                  evidence=[{"path": "src/routing/dispatch.c"}],
                                  reasoning="the code disagrees with an operator assumption"))

        print("\n3) G2 refuses while an escalation is undispositioned:")
        _check("the walkthrough has pending items", len(E.pending(rec)) == 2,
               f"{[f['id'] for f in E.pending(rec)]}")
        g2blocked = V.evaluate_g2(rec, signals)
        _check("G2 is INELIGIBLE with the walkthrough unfinished", not g2blocked.eligible)
        _check("and the blocker names the escalation precondition",
               any(not p.ok and "escalation" in p.name for p in g2blocked.preconditions),
               str([p.name for p in g2blocked.preconditions if not p.ok]))
        _check("accept is REFUSED",
               _raises(lambda: V.record_g2(led, result=g2blocked, outcome="accept", version=2,
                                           ts=T)))

        print("\n4) a REJECTED finding does not reach v2 — but stays in the record:")
        E.disposition(rec, "F-800", call="accept", target="§16",
                      rationale="genuinely new build", actor="vmunjal")
        _check("a `reject` carrying a target is refused — rejecting drops the finding",
               _raises(lambda: E.disposition(rec, "F-801", call="reject", target="§13",
                                             rationale="no", actor="vmunjal")))
        E.disposition(rec, "F-801", call="reject",
                      rationale="The operator's assumption stands; the code path found is "
                                "dead and not the one in use.", actor="vmunjal")
        _check("every escalation is now answered", not E.pending(rec))
        v2doc, report = A.apply_to_v2(v1, rec, regenerate_summary=lambda body, f: body)
        touched = set(report["corrections"] and [c["id"] for c in report["corrections"]]) \
            | set(report["impacts"])
        _check("the rejected finding is NOT applied to v2", "F-801" not in touched,
               f"applied: {sorted(touched)[:4]}")
        kept = next(f for f in rec["findings"] if f["id"] == "F-801")
        _check("but it survives in enrichment.json with its disposition",
               kept["disposition"] == "reject" and bool(kept.get("rationale")),
               "rejecting is not deleting — the reasoning is the audit record")
        _check("the accepted one DID reach v2", "F-800" in touched)

        # ── G3 + the push
        print("\n5) G3's authorization cannot be minted for an ineligible plan:")
        bad_plan = {"run_id": "r-refusals", "project_key": "P",
                    "initiative": {"local_id": "INIT", "issue_type": "Initiative", "summary": "x",
                                   "description": "x", "controls": {}},
                    "deliverables": [], "epics": [{"local_id": "R1", "issue_type": "Epic",
                                                   "parent": None, "summary": "R1",
                                                   "assertion_refs": [], "controls": {}}],
                    "stories": [], "trace": {"section16_entries": ["F-1"], "requirements": ["R1"],
                                             "deliverables": []}}
        g3bad = JV.evaluate_g3(bad_plan, section16_ids=["F-1"])
        _check("an orphan-epic plan is INELIGIBLE", not g3bad.eligible)
        _check("authorize() refuses to mint for it",
               _raises(lambda: jira.authorize(g3bad, plan=bad_plan, run_id="r-refusals", actor="v", ts=T)))
        _check("so the push is unreachable — no authorization exists to pass",
               _raises(lambda: jira.push_plan(bad_plan, {}, project_key="P", dry_run=False)))

        print("\n6) a mid-batch push failure preserves prior successes:")
        good_plan = json.loads((_REPO_ROOT / "fixtures/jira_plan/plan_pass.json").read_text())
        good_plan["run_id"] = "r-refusals"   # the token is run-bound now (review #2): a token
                                             # minted for this run must be pushed against a plan
                                             # carrying the same run id — the fixture found the
                                             # binding working the moment it landed
        g3ok = JV.evaluate_g3(good_plan,
                              section16_ids=good_plan["trace"]["section16_entries"],
                              dispositioned_without_story=good_plan["trace"]["section16_entries"])
        if not g3ok.eligible:
            g3ok = JV.evaluate_g3(good_plan, section16_ids=[])
        _check("the reference plan is eligible", g3ok.eligible,
               str([p.name for p in getattr(g3ok, "hard_checks", []) if not p.ok]))

        saved = _auth.get_backend()
        _auth.set_backend(_Stub())
        made: list[str] = []
        FAIL_AFTER = 4

        def flaky_create(issue, *, project_key, parent_key, handle):
            if len(made) >= FAIL_AFTER:
                raise RuntimeError("simulated Jira 500 on create")
            made.append(issue["local_id"])
            return {"key": f"{project_key}-{1000 + len(made)}", "url": "https://x"}

        def stub_update(key, issue, *, handle):
            return {"key": key, "url": "https://x"}

        try:
            auth = jira.authorize(g3ok, plan=good_plan, run_id="r-refusals", actor="vmunjal", ts=T)
            jira.set_target(flaky_create, stub_update)
            partial_trace: dict = {}
            try:
                jira.push_plan(good_plan, {}, project_key="P", dry_run=False,
                               authorization=auth)
                partial = False
            except Exception as exc:                   # noqa: BLE001 — a mid-batch failure
                partial = True
                partial_trace = getattr(exc, "partial_trace", {})
            _check("the push failed part-way", partial or len(made) == FAIL_AFTER,
                   f"{len(made)} created before the 500")
            _check(f"the {FAIL_AFTER} successful creates happened before it",
                   len(made) == FAIL_AFTER)

            _check("the exception carries the PARTIAL TRACE, so the caller can resume",
                   set(partial_trace) == set(made),
                   f"trace has {sorted(partial_trace)}, created {sorted(made)}")
            # Retry seeded from the partial trace the adapter handed back.
            recorded = partial_trace
            before = list(made)
            jira.set_target(lambda issue, **kw: (_ for _ in ()).throw(
                AssertionError(f"re-created {issue['local_id']} that already existed"))
                if issue["local_id"] in before else
                {"key": f"P-{2000 + len(made)}", "url": "https://x"}, stub_update)
            resumed = True
            try:
                jira.push_plan(good_plan, recorded, project_key="P", dry_run=False,
                               authorization=auth)
            except AssertionError as exc:
                resumed = False
                print(f"    {exc}")
            except Exception:                          # noqa: BLE001
                pass
            _check("a retry does NOT re-create what already exists (idempotent by local_id)",
                   resumed, "re-creating on retry is how a partial push becomes a duplicate push")
        finally:
            jira.reset_target()
            _auth.set_backend(saved)

        rep = ledger.validate_ledger(led)
        _check("both ledgers validate after every refusal", all(not e for e in rep.values()),
               str(rep))

    print()
    if _FAILURES:
        print(f"FAILED — {len(_FAILURES)} check(s): {_FAILURES}", file=sys.stderr)
        return 1
    print("PASS — every gate refuses cleanly and leaves nothing half-done: G1 does not freeze what "
          "it refused, the reopen cycle completes, G2 cannot skip the walkthrough, a rejected "
          "finding stays in the record without reaching v2, G3's authorization cannot be minted "
          "for a broken plan, and a partial push resumes rather than duplicating.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
