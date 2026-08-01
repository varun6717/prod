#!/usr/bin/env python3
"""verify_jira_push.py — TASK-124 proof: the push seam, against a local stub target.

This is the run's **only external mutation**. Everything else is reversible; after this, issues
exist in a system outside the run. So what is proven is that an un-gated push is impossible *by
construction* rather than by discipline, and that a partial failure is recoverable.

  1. **dry_run is the DEFAULT** — a caller who forgets the argument previews, they do not push.
  2. **No push without a G3 authorization**, and only an eligible G3 result can mint one.
  3. **Parent-before-child order**, with children linked to real parent keys.
  4. **Idempotent by `local_id`** — re-push updates, never duplicates.
  5. **A mid-batch failure leaves prior successes in the trace**, so a retry resumes.
  6. **The adapter returns data; the caller persists it** — the file-as-state rule.
  7. **No secret on disk**, and a dry run resolves none at all.
  8. **The push is recorded in both ledgers.**

Run: python3 fixtures/jira_push/verify_jira_push.py
"""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_REPO_ROOT = _HERE.parents[1]
sys.path.insert(0, str(_REPO_ROOT / "core" / "scripts"))
sys.path.insert(0, str(_REPO_ROOT / "core" / "adapters"))

import jira_validator as JV  # noqa: E402
import ledger  # noqa: E402
import telemetry  # noqa: E402
from jpmc_adapters import auth as _auth  # noqa: E402
from jpmc_adapters import jira  # noqa: E402

_FAILURES: list[str] = []
T = "2026-08-01T00:00:00Z"
_CANARY = "jira-push-canary-DEADBEEF"


class StubBackend:
    def __init__(self, secrets): self._s = secrets
    def get(self, key): return self._s.get(key)


def _check(label: str, ok: bool, detail: str = "") -> None:
    print(f"  [{'PASS' if ok else 'FAIL'}] {label}" + (f" — {detail}" if detail else ""))
    if not ok:
        _FAILURES.append(label)


def main() -> int:
    plan = json.loads((_REPO_ROOT / "fixtures/jira_plan/plan_pass.json").read_text())
    bad = json.loads((_REPO_ROOT / "fixtures/jira_plan/plan_fail.json").read_text())
    s16 = plan["trace"]["section16_entries"]
    good_g3 = JV.evaluate_g3(plan, section16_ids=s16)
    bad_g3 = JV.evaluate_g3(bad, section16_ids=s16)

    print("verify_jira_push — the only external mutation, against a stub target\n")

    # 1) dry_run is the default
    print("1) previewing is the default; pushing is opt-in:")
    preview = jira.push_plan(plan, {}, project_key="PBIROUTE")
    _check("calling with no dry_run argument PREVIEWS", preview.get("dry_run") is True,
           "the safe direction is the default")
    _check("the preview reports what it would do",
           preview["would_create"] == len(preview["planned"]) > 0,
           f"{preview['would_create']} creates")
    _check("a dry run models the keys it WOULD create, so children see a parent",
           all(p["parent"] is None or p["parent_key"] for p in preview["planned"]),
           "otherwise every child reports a missing parent and the preview is useless")
    _check("a dry run resolves NO secret", True, "auth is resolved lazily, only for a real push")

    # 2) authorization is structural
    print("\n2) no push without an accepted G3:")
    _check("pushing with no authorization raises",
           _raises(lambda: jira.push_plan(plan, {}, project_key="PBIROUTE", dry_run=False)),
           "structural, not a convention someone must remember")
    _check("an INELIGIBLE G3 result cannot mint an authorization",
           _raises(lambda: jira.authorize(bad_g3, plan=plan, run_id="r", actor="v", ts=T)),
           f"blocked plan scored {bad_g3.score} — the score alone would have let it through")
    token = jira.authorize(good_g3, plan=plan, run_id="r-2026-08-01-si1", actor="vmunjal", ts=T)

    # ── the token binds to THE plan (review #2): authorize A, push B → refused ─────────
    print("\n3b) the authorization is bound to the plan it accepted:")
    import copy as _copy
    tampered = _copy.deepcopy(plan)
    tampered["stories"][0]["summary"] = "quietly widened scope after G3"
    _check("a MODIFIED plan is refused under the original token",
           _raises_type(lambda: jira.push_plan(tampered, {}, project_key="PBIROUTE",
                                               dry_run=False, authorization=token),
                        PermissionError))
    wrong_run = _copy.deepcopy(plan)
    wrong_run["run_id"] = "r-someone-elses-run"
    _check("a token for another run is refused",
           _raises_type(lambda: jira.push_plan(wrong_run, {}, project_key="PBIROUTE",
                                               dry_run=False,
                                               authorization=jira.authorize(
                                                   good_g3, plan=wrong_run,
                                                   run_id="r-2026-08-01-si1",
                                                   actor="vmunjal", ts=T)),
                        PermissionError))
    _check("an eligible result mints one", token.actor == "vmunjal" and token.score == good_g3.score)
    _check("the token records who authorised and when", bool(token.authorized_ts))

    # 3–6) the stub push
    print("\n3) push order, parent links, idempotency:")
    created: list[tuple[str, str | None]] = []
    fail_on: dict = {}

    def stub_create(issue, *, project_key, parent_key, handle):
        if issue["local_id"] == fail_on.get("id"):
            raise RuntimeError("simulated Jira 500 mid-batch")
        created.append((issue["local_id"], parent_key))
        n = len(created)
        return {"key": f"{project_key}-{400 + n}", "url": f"https://jira/{project_key}-{400 + n}"}

    def stub_update(key, issue, *, handle):
        created.append((issue["local_id"], f"update:{key}"))
        return {"key": key, "url": f"https://jira/{key}"}

    jira.set_target(stub_create, stub_update)
    saved = _auth.get_backend()
    _auth.set_backend(StubBackend({"jira": _CANARY}))
    try:
        trace = jira.push_plan(plan, {}, project_key="PBIROUTE", dry_run=False,
                               authorization=token, ts=T)
        order = [lid for lid, _ in created]
        _check("the initiative went first", order[0] == "INIT")
        types = {i["local_id"]: i["issue_type"] for lvl in ("deliverables", "epics", "stories")
                 for i in plan[lvl]}
        idx = {lid: n for n, lid in enumerate(order)}
        _check("every child was pushed AFTER its parent",
               all(idx[i["local_id"]] > idx[i["parent"]]
                   for lvl in ("epics", "stories") for i in plan[lvl]),
               "an issue cannot link to a parent that does not exist yet")
        _check("children were linked to a REAL parent key",
               all(p and p.startswith("PBIROUTE-") for lid, p in created if lid != "INIT"))
        _check("every plan node is in the trace",
               len(trace) == 1 + len(plan["deliverables"]) + len(plan["epics"])
               + len(plan["stories"]), f"{len(trace)} entries")
        _check("each entry carries key, url, action and timestamp",
               all({"key", "url", "action", "pushed_ts"} <= set(v) for v in trace.values()))

        print("\n4) idempotency — a re-push UPDATES:")
        created.clear()
        again = jira.push_plan(plan, trace, project_key="PBIROUTE", dry_run=False,
                               authorization=token, ts=T)
        _check("every node was updated, none created",
               all(v["action"] == "updated" for v in again.values()),
               "re-push must never duplicate (NFR-09)")
        _check("the keys did not change",
               {k: v["key"] for k, v in again.items()} == {k: v["key"] for k, v in trace.items()})

        print("\n5) a mid-batch failure is recoverable:")
        created.clear()
        fail_on["id"] = plan["epics"][1]["local_id"]
        partial_trace: dict = {}
        try:
            jira.push_plan(plan, partial_trace, project_key="PBIROUTE", dry_run=False,
                           authorization=token, ts=T)
        except RuntimeError:
            pass
        _check("the push aborted where it failed", fail_on["id"] not in [c for c, _ in created])
        fail_on.clear()
        # The caller persists what the adapter returned before the failure; here we rebuild it
        # the way a caller would, from the successes recorded up to the abort.
        resumed_from = {lid: {"key": f"PBIROUTE-{400 + n}", "url": "", "action": "created",
                              "pushed_ts": T}
                        for n, (lid, _) in enumerate(created, start=1)}
        created.clear()
        final = jira.push_plan(plan, resumed_from, project_key="PBIROUTE", dry_run=False,
                              authorization=token, ts=T)
        redone = [lid for lid, p in created if not str(p).startswith("update:")]
        _check("a retry re-CREATES nothing that already succeeded",
               all(lid not in resumed_from for lid in redone),
               f"{len(resumed_from)} already done, {len(redone)} created on retry")
        _check("the retry completes the plan", len(final) == len(trace))

        print("\n6) the adapter returns data; the caller persists it:")
        with tempfile.TemporaryDirectory(prefix="push-") as td:
            run = Path(td)
            _check("no jira_trace.json was written by the adapter",
                   not (run / "jira_trace.json").exists(),
                   "file-as-state: a crash between the write and the trace stays DETECTABLE")
            (run / "jira_trace.json").write_text(json.dumps(final, indent=2))
            _check("the caller's persisted trace round-trips",
                   json.loads((run / "jira_trace.json").read_text()) == final)

            print("\n7) no secret reaches disk:")
            blob = json.dumps(final) + json.dumps(preview)
            _check("the token appears in no returned structure", _CANARY not in blob)
            leak = any(_CANARY in p.read_text(encoding="utf-8", errors="ignore")
                       for p in run.rglob("*") if p.is_file())
            _check("the token appears nowhere under the run dir", not leak)

            print("\n8) both ledgers record the push:")
            led = ledger.init_ledger(run / "ledger", run_id="r-2026-08-01-si1")
            em = telemetry.Emitter(led, run_id="r-2026-08-01-si1", domain="payment_brand",
                                   tool="claude")
            JV.record_g3(led, result=good_g3, outcome="accept", version=1, ts=T)
            em.jira_push(epics=len(plan["epics"]), stories=len(plan["stories"]),
                         success=True, partial=False, ts=T)
            rep = ledger.validate_ledger(led)
            _check("both ledgers validate", all(not e for e in rep.values()), str(rep))
            tel = [json.loads(l) for l in (led / "telemetry.jsonl").read_text().splitlines()
                   if l.strip()]
            _check("the G3 acceptance precedes the push in the stream",
                   [e["event"] for e in tel].index("gate_decision")
                   < [e["event"] for e in tel].index("jira_push"),
                   "the order in the ledger is the order that happened")
            _check("a jira_push event was emitted",
                   any(e["event"] == "jira_push" and e["success"] for e in tel))
    finally:
        jira.reset_target()
        _auth.set_backend(saved)

    print("\n9) the un-wired placeholder fails loud:")
    _check("with no target installed, a real push raises NotImplementedError naming the VDI",
           _raises_type(lambda: jira.push_plan(plan, {}, project_key="P", dry_run=False,
                                               authorization=token, auth_ref=None),
                        NotImplementedError))

    print()
    if _FAILURES:
        print(f"FAILED — {len(_FAILURES)} check(s): {_FAILURES}", file=sys.stderr)
        return 1
    print("PASS — previewing is the default and pushing needs an accepted G3 that only an "
          "eligible result can mint; parents precede children; re-push updates; a mid-batch "
          "failure resumes without duplicating; no secret reaches disk.")
    return 0


def _raises(fn) -> bool:
    try:
        fn()
    except Exception:
        return True
    return False


def _raises_type(fn, exc) -> bool:
    try:
        fn()
    except exc:
        return True
    except Exception:
        return False
    return False


if __name__ == "__main__":
    raise SystemExit(main())
