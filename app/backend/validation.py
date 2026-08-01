"""validation.py — §3.1 ``UI_INPUT`` config validator (TASK-050).

The backend accepts posted config and must reject anything that does not conform to
``TECH_SPEC`` §3.1 with a **422 naming the failing field** (TASK-050 acceptance). This
module is the single source of that shape check: it returns a list of human-readable
``field — reason`` strings (empty list == valid). It validates *shape and vocabulary*
only — it is **plumbing, not judgment** (FR-XS-03): it never branches on ``domain``
semantics, never resolves a source, never touches a secret. Deeper failures (a domain
with no registered profile, an unreachable registry) surface later from ``generate.py``
and the build checks, not here.

Kept deliberately dependency-free (stdlib only) so it can be imported by the FastAPI app,
the proof harness, or a CLI without pulling the web stack.
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

# The D-A12 taxonomy lives in core (one definition, shared with the §10.5′ build check) —
# reached the same way service.py reaches generate.py.
_SCRIPTS = Path(__file__).resolve().parents[2] / "core" / "scripts"
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from dispositions import (  # noqa: E402  (core/scripts/dispositions.py)
    ALL_DISPOSITIONS,
    CODE_SOURCE_TYPES,
    CODEBASE_DISPOSITION,
    OPERATOR_DISPOSITIONS,
)

# §6.4 / FR-XS-06 — the only two runtime tools the overlays realize.
_RUNTIME_TOOLS = ("claude", "copilot")

# §3.1 ``project_metadata`` block — config-only governance identity (all required).
_PROJECT_METADATA_KEYS = (
    "project_name",
    "application_name",
    "line_of_business",
    "requestor",
    "requestor_sid",
)

# §3.1 ``frame`` — the operator's authoritative seed. ``overview`` is the free-form Initiative
# Overview added by ADR-008 (D-A13/D-A14): it supplies §1's initiative identity, **seeds the §7
# deliverables**, and is the semantic query context Arm 1 matches against code — so it is
# required, not decorative. scope_hints/stakeholders/key_dates stay optional refinements.
_FRAME_REQUIRED_KEYS = ("title", "intent", "overview")

# Per-source-type required instance fields (§3.1 ``sources[]``, §6.6.2 connector contract).
# Every source carries a ``type``; the rest is what that type's connector needs to locate the
# content. ``auth_ref`` is required for the networked connectors (never inline — §7) and is
# absent only for a direct ``file`` path. Keyed by ``type`` so adding a source type stays a
# pure data edit (no domain fork — D7).
_SOURCE_REQUIRED_FIELDS: dict[str, tuple[str, ...]] = {
    "file": ("path",),
    "bitbucket": ("repo_url", "auth_ref"),
    "sharepoint": ("url", "auth_ref"),
    "confluence": ("url", "auth_ref"),
    "jira": ("url", "auth_ref"),          # an issue URL (TASK-107); D-A24's one new source type
}


def _is_nonempty_str(value: Any) -> bool:
    return isinstance(value, str) and value.strip() != ""


def validate_ui_input(config: Any) -> list[str]:
    """Validate ``config`` against §3.1. Returns ``[]`` if valid, else ``field — reason`` strings.

    The first element of each message is the dotted field path (e.g. ``sources[1].repo_url``)
    so the API can surface *which* field failed (TASK-050 acceptance: "422 naming the field").
    """
    errors: list[str] = []

    if not isinstance(config, dict):
        return ["config — must be a mapping of §3.1 fields"]

    # run_id is "assigned by Generate" (§3.1) — optional on input (the service assigns one when
    # absent); when present it must be a usable string since it names the run + ledger.
    if "run_id" in config and not _is_nonempty_str(config["run_id"]):
        errors.append("run_id — must be a non-empty string when provided")

    # schema_version pins the contract revision; slice 1 is exactly 1.
    if config.get("schema_version") != 1:
        errors.append("schema_version — must be 1 (§3.1)")

    for field in ("working_path", "domain", "registry_sha"):
        if not _is_nonempty_str(config.get(field)):
            errors.append(f"{field} — required non-empty string (§3.1)")

    runtime_tool = config.get("runtime_tool")
    if runtime_tool not in _RUNTIME_TOOLS:
        errors.append(
            f"runtime_tool — must be one of {list(_RUNTIME_TOOLS)} (FR-XS-06); got {runtime_tool!r}"
        )

    # registry_url / registry_ref are OPTIONAL: when absent, Generate falls back to the env /
    # repo-root registry. When present they must be usable strings (registry_ref = the branch/tag
    # the registry lives on, for a one-repo/two-feature layout).
    for field in ("registry_url", "registry_ref"):
        if field in config and not _is_nonempty_str(config[field]):
            errors.append(f"{field} — must be a non-empty string when provided (§3.1)")

    errors.extend(_validate_project_metadata(config.get("project_metadata")))
    errors.extend(_validate_frame(config.get("frame")))
    errors.extend(_validate_sources(config.get("sources")))
    errors.extend(_validate_gates(config.get("gates")))

    return errors


def _validate_project_metadata(pm: Any) -> list[str]:
    if not isinstance(pm, dict):
        return ["project_metadata — required mapping (§3.1)"]
    return [
        f"project_metadata.{k} — required non-empty string (§3.1)"
        for k in _PROJECT_METADATA_KEYS
        if not _is_nonempty_str(pm.get(k))
    ]


def _validate_frame(frame: Any) -> list[str]:
    if not isinstance(frame, dict):
        return ["frame — required mapping (§3.1)"]
    return [
        f"frame.{k} — required non-empty string (§3.1)"
        for k in _FRAME_REQUIRED_KEYS
        if not _is_nonempty_str(frame.get(k))
    ]


def _validate_sources(sources: Any) -> list[str]:
    if not isinstance(sources, list) or not sources:
        return ["sources — required non-empty list of source descriptors (§3.1)"]

    errors: list[str] = []
    for i, src in enumerate(sources):
        where = f"sources[{i}]"
        if not isinstance(src, dict):
            errors.append(f"{where} — must be a mapping")
            continue
        stype = src.get("type")
        if not _is_nonempty_str(stype):
            errors.append(f"{where}.type — required (§3.1)")
            continue
        required = _SOURCE_REQUIRED_FIELDS.get(stype)
        if required is None:
            errors.append(
                f"{where}.type — unknown source type {stype!r}; "
                f"known: {sorted(_SOURCE_REQUIRED_FIELDS)} (§6.6.2)"
            )
            continue
        errors.extend(
            f"{where}.{field} — required for type {stype!r} (§3.1, §6.6.2)"
            for field in required
            if not _is_nonempty_str(src.get(field))
        )
        errors.extend(_validate_disposition(src.get("disposition"), stype, where))
    return errors


def _validate_disposition(value: Any, stype: str, where: str) -> list[str]:
    """Validate ``sources[].disposition`` against the D-A12 taxonomy (§3.1 amendment).

    Always a **list** — "one or more", defaulting to one (multi is allowed because mixed
    documents are real). A single shape keeps every consumer's parse trivial; the UI emits
    a one-element list rather than a bare string.

    Two asymmetries the taxonomy encodes: ``codebase`` is auto-set for code sources and may
    not be operator-chosen, and a doc source may never carry it — that is what keeps the
    code arm and doc arm from crossing.
    """
    field = f"{where}.disposition"
    if not isinstance(value, list) or not value:
        return [f"{field} — required non-empty list of D-A12 classes "
                f"(operator-selectable: {list(OPERATOR_DISPOSITIONS)}); "
                f"code sources carry [{CODEBASE_DISPOSITION!r}] (§3.1, D-A12)"]

    errors: list[str] = []
    unknown = [d for d in value if d not in ALL_DISPOSITIONS]
    if unknown:
        errors.append(f"{field} — unknown disposition(s) {unknown}; "
                      f"known: {list(ALL_DISPOSITIONS)} (D-A12)")
    if len(set(value)) != len(value):
        errors.append(f"{field} — duplicate entries {value}")

    if stype in CODE_SOURCE_TYPES:
        if value != [CODEBASE_DISPOSITION]:
            errors.append(f"{field} — code source type {stype!r} is auto-set to "
                          f"[{CODEBASE_DISPOSITION!r}], not operator-chosen; got {value} (D-A12)")
    elif CODEBASE_DISPOSITION in value:
        errors.append(f"{field} — {CODEBASE_DISPOSITION!r} is auto-set for code sources only; "
                      f"a {stype!r} source cannot declare it (D-A12)")
    return errors


def _validate_gates(gates: Any) -> list[str]:
    if not isinstance(gates, dict):
        return ["gates — required mapping with score_threshold (§3.1, §9)"]
    threshold = gates.get("score_threshold")
    if not isinstance(threshold, int) or isinstance(threshold, bool) or not (0 <= threshold <= 100):
        return ["gates.score_threshold — required integer in [0, 100] (§9)"]
    return []
