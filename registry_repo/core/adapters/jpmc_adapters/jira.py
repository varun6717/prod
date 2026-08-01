#!/usr/bin/env python3
"""jira.py — the Jira push connector (§7.1/§7.2, D-A24). **The only external mutation.**

Everything else in this design is reversible: documents can be re-authored, maps rebuilt, gates
reopened. This one function writes to a system outside the run, and after it Jira contains issues
someone will act on. So the discipline here is heavier than anywhere else:

  - **Nothing is written without an accepted G3.** Enforced structurally, not by convention:
    `push_plan` requires a `G3Authorization` that only `authorize(...)` mints, and `authorize`
    refuses an ineligible result. There is no argument combination that writes without one.
  - **Idempotent by `local_id`** (NFR-09). Re-push updates; it never duplicates. The plan's ids
    are the SI's own (`D1`, `R3`), which is why `jira_author` was forbidden from inventing new
    ones.
  - **Each result is recorded as it returns.** A mid-batch failure leaves prior successes in the
    trace, so a retry resumes the remainder instead of re-creating what already exists. This is
    the difference between a partial push being recoverable and being a mess.
  - **The adapter returns data; the caller persists it.** Keeping the file-as-state rule intact
    means a crash between "wrote to Jira" and "wrote the trace" is *detectable* — the next
    dry-run reports issues that exist without a trace entry.

╔══════════════════════════════════════════════════════════════════════════════════════╗
║  VDI WIRE-UP — the ONE function to edit on the JPMC VDI.                               ║
║                                                                                        ║
║  Everything here is real EXCEPT ``_create_issue`` / ``_update_issue``: the actual Jira  ║
║  REST calls are environment-specific, so they ship as marked ``[TBD — VDI]``            ║
║  placeholders. On the VDI you edit them in place — no /vdi plugin. Ordering, parent     ║
║  linking, idempotency, the trace and the gate check are all real and proven offline     ║
║  against the local stub target.                                                        ║
╚══════════════════════════════════════════════════════════════════════════════════════╝
"""
from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Sequence

_ADAPTERS = Path(__file__).resolve().parents[1]
if str(_ADAPTERS) not in sys.path:
    sys.path.insert(0, str(_ADAPTERS))
from jpmc_adapters import auth as _auth  # noqa: E402

SERVICE = "jira"
_DEFAULT_AUTH_REF = "jpmc_adapters:jira"

# Push order is parent-before-child and is NOT a preference: an issue cannot be linked to a
# parent that does not exist yet, so a child pushed first would either fail or land orphaned.
PUSH_ORDER = ("initiative", "deliverables", "epics", "stories")


# ──────────────────────────────────────────────────────────────────────────────────────
#  ▼▼▼  VDI PLACEHOLDERS — EDIT THESE TWO IN PLACE ON THE JPMC VDI  ▼▼▼
# ──────────────────────────────────────────────────────────────────────────────────────
def _create_issue(issue: dict, *, project_key: str, parent_key: str | None, handle) -> dict:
    """[TBD — VDI] Create one Jira issue. Return ``{"key", "url"}``.

        headers = {"Authorization": f"Bearer {handle.reveal()}", ...}
        POST {base}/rest/api/3/issue  with fields: project, issuetype, summary, description,
             parent (when parent_key), and the controls custom fields.

    Contract: raise on non-2xx. A silent failure here would leave the trace claiming an issue
    exists that does not, and the next re-push would "update" a key that was never created.
    """
    raise NotImplementedError(
        "[TBD — VDI] Jira create is not wired. Edit jira._create_issue in place with the real "
        "REST call, or inject a target via set_target() for offline testing.")


def _update_issue(key: str, issue: dict, *, handle) -> dict:
    """[TBD — VDI] Update the existing issue ``key``. Return ``{"key", "url"}``.

        PUT {base}/rest/api/3/issue/{key}

    Contract: raise on non-2xx. Update, never create — the key came from the trace, so creating
    here would duplicate exactly what idempotency exists to prevent.
    """
    raise NotImplementedError(
        "[TBD — VDI] Jira update is not wired. Edit jira._update_issue in place.")
# ──────────────────────────────────────────────────────────────────────────────────────
#  ▲▲▲  END VDI PLACEHOLDERS  ▲▲▲
# ──────────────────────────────────────────────────────────────────────────────────────


_TARGET: dict[str, Callable] = {"create": _create_issue, "update": _update_issue}


def set_target(create: Callable, update: Callable) -> None:
    """Install create/update implementations (the VDI seam's test stand-in)."""
    _TARGET["create"], _TARGET["update"] = create, update


def reset_target() -> None:
    _TARGET["create"], _TARGET["update"] = _create_issue, _update_issue


# ── the G3 authorization token ────────────────────────────────────────────────
@dataclass(frozen=True)
class G3Authorization:
    """Proof that a human accepted G3. Structural, not advisory.

    `push_plan` will not write without one, and only `authorize()` can mint one — so "the push is
    gated" is a property of the type system rather than a rule someone must remember. There is no
    flag, no override, and no default that bypasses it.
    """
    run_id: str
    actor: str
    score: int
    authorized_ts: str


def authorize(result, *, run_id: str, actor: str, ts: str) -> G3Authorization:
    """Mint the authorization. Refuses an ineligible G3 result.

    This is the single point where an irreversible action becomes possible, so the refusal is
    here rather than at the call site: a caller that forgot to check could still not push.
    """
    if not getattr(result, "eligible", False):
        raise ValueError(
            f"G3 authorization refused — the plan is not eligible: "
            f"{list(getattr(result, 'blockers', ()))[:3]}")
    return G3Authorization(run_id=run_id, actor=actor, score=result.score, authorized_ts=ts)


# ── the push ──────────────────────────────────────────────────────────────────
def _issues_in_order(plan: dict) -> list[tuple[str, dict, str | None]]:
    """Every issue as ``(local_id, issue, parent_local_id)``, parents before children."""
    out: list[tuple[str, dict, str | None]] = []
    init = plan.get("initiative")
    if init:
        out.append((init["local_id"], init, None))
    for level in ("deliverables", "epics", "stories"):
        for issue in plan.get(level, []):
            out.append((issue["local_id"], issue, issue.get("parent")))
    return out


def push_plan(plan: dict, trace: dict, *, project_key: str, dry_run: bool = True,
              authorization: G3Authorization | None = None,
              auth_ref: str | None = _DEFAULT_AUTH_REF, ts: str = "") -> dict:
    """Push the 4-level plan. Returns the updated trace — **does not write it to disk**.

    ``dry_run=True`` (the default, deliberately) validates completeness and reports the planned
    actions **without writing**. `jira_validator` and the G3 preview use it. The default is the
    safe direction: a caller who forgets the argument previews, they do not push.

    A real push requires ``authorization`` from :func:`authorize`.
    """
    if not dry_run and authorization is None:
        raise PermissionError(
            "refusing to push without a G3 authorization — this is the run's ONLY external "
            "mutation, and it happens exactly once a human has accepted G3")

    handle = None
    if not dry_run:
        handle = _auth.resolve_auth(auth_ref)      # resolved lazily: a dry run needs no secret

    out = dict(trace)
    planned: list[dict] = []
    for local_id, issue, parent_local in _issues_in_order(plan):
        existing = out.get(local_id)
        action = "updated" if existing else "created"
        parent_key = out.get(parent_local, {}).get("key") if parent_local else None
        if dry_run:
            planned.append({"local_id": local_id, "action": action,
                            "issue_type": issue.get("issue_type"),
                            "parent": parent_local, "parent_key": parent_key})
            # A dry run must still model the keys it WOULD create, or every child would report a
            # missing parent and the preview would be useless exactly where it matters most.
            out.setdefault(local_id, {"key": f"{project_key}-DRY-{local_id}", "url": "",
                                      "action": "planned", "pushed_ts": ts})
            continue
        try:
            if existing:
                res = _TARGET["update"](existing["key"], issue, handle=handle)
            else:
                res = _TARGET["create"](issue, project_key=project_key,
                                        parent_key=parent_key, handle=handle)
        except Exception as exc:
            # Attach what DID succeed to the exception before it propagates. Without this the
            # partial trace dies with the stack frame, and every caller has to track successes
            # independently to resume — which makes "a mid-batch failure leaves prior successes
            # in the trace" true of this function's local variable and of nothing the caller can
            # reach. Additive: the exception type and message are unchanged, so existing handlers
            # are unaffected; a caller that wants to resume reads `exc.partial_trace`.
            exc.partial_trace = out           # type: ignore[attr-defined]
            exc.pushed_before_failure = local_id   # type: ignore[attr-defined]
            raise
        # Recorded AS IT RETURNS — a mid-batch failure leaves prior successes in the trace and a
        # retry resumes the remainder rather than re-creating them.
        out[local_id] = {"key": res["key"], "url": res.get("url", ""),
                         "action": action, "pushed_ts": ts}
    if dry_run:
        return {"dry_run": True, "planned": planned,
                "would_create": sum(1 for p in planned if p["action"] == "created"),
                "would_update": sum(1 for p in planned if p["action"] == "updated")}
    return out


def push_epics(plan: dict, trace: dict, *, project_key: str, dry_run: bool = False, **kw) -> dict:
    """§7.1's pinned signature, kept as the compatibility surface over :func:`push_plan`.

    The name is pre-ADR-008 — the plan is four levels now, not epics — but §7.1 pins the
    signature, so it stays and delegates rather than being silently renamed.
    """
    return push_plan(plan, trace, project_key=project_key, dry_run=dry_run, **kw)
