#!/usr/bin/env python3
"""ingest_jira.py — the Jira issue connector, §6.6.2 (TASK-107; D-A24's one genuinely new type).

Generic and **source-type-keyed** (D7 / FR-DC-11): the connector for ``type: jira`` sources — a
Jira **issue** (an epic, a story, a previous Solution Intent's issue tree). It pulls the issue
through the auth seam, **stages** it into the run's source area, and emits the **same** source
descriptor shape as ``ingest_file.py`` so nothing downstream changes (FR-XS-01, descriptor parity).

**One issue = one source entry**, exactly as one Confluence link = one page. Multiple issues are
multiple ``type: jira`` entries; the orchestrator fans out one worker per entry, so each becomes its
own slice / manifest entry and carries its own disposition. Walking an epic's children (JQL, issue
links) is a deferred enhancement, not this connector's job.

────────────────────────────────────────────────────────────────────────────────────────
Why this one connector renders, when the others only copy
────────────────────────────────────────────────────────────────────────────────────────
SharePoint and Confluence stage a **document** — a PDF or an HTML page — and the doc lane's
extract step turns it into Markdown. A Jira issue is not a document: it arrives as a **JSON
payload** with named fields. So this connector renders that payload to the ``.md`` extract itself.

That rendering is **strictly mechanical** and stays inside "a connector assigns no meaning":
every field maps to a fixed heading, values are copied verbatim, nothing is summarised, reordered
by importance, or interpreted. It is a format transform (JSON → Markdown), the same kind of work
``pdf_extract`` does for PDFs — just deterministic enough to live in the connector rather than
needing a model. A field the payload does not carry is **omitted, never invented**.

**`prior_artifact` is the disposition, and it carries a hazard** (D-A12): a previous BRD or Jira
epic in the corpus lets an agent **copy** from it instead of deriving from the mandate — and the
copy will look properly cited. That is enforced at authoring time (reference-only, never the sole
citation for a new requirement), not here; this connector only stages what it is pointed at.

Contract (§6.6.2) — identical descriptor shape to ``ingest_file.py``:
  consumes : a ``UI_INPUT.sources[]`` entry of ``type: jira`` (``url``, ``source``,
             ``auth_ref: jpmc_adapters:jira``) + auth via the seam (FR-DC-12).
  produces : the rendered issue staged under ``<dest>/<source>/``; returns / prints a JSON
             descriptor (``type``, ``source``, ``url``, ``staged_path``, ``auth_ref``,
             ``ingest_ts``) — the exact handoff the doc pipeline reads.

**Never branches on ``domain`` (D7).** This script does not read ``domain`` (FR-DC-11).

**Auth (FR-DC-12).** ``auth_ref`` is a pointer resolved at the seam
(``jpmc_adapters.auth.resolve_auth``) → an ``AuthHandle``; its secret is used only to authenticate
the fetch and never appears in the descriptor, the staged file, or any artifact.

╔══════════════════════════════════════════════════════════════════════════════════════╗
║  VDI WIRE-UP — the ONE function to edit on the JPMC VDI.                               ║
║                                                                                        ║
║  Everything in this file is real EXCEPT ``_fetch_issue`` below: the actual Jira REST    ║
║  call (which base URL, the auth header, issue-key resolution) is environment-specific,  ║
║  so it ships as a marked ``[TBD — VDI]`` placeholder. On the VDI you **edit that one     ║
║  function in place** to add the real call + JPMC auth (exactly the way                  ║
║  ``ingest_sharepoint.py``'s ``_download_pdf`` and ``ingest_confluence.py``'s            ║
║  ``_fetch_confluence`` were wired) — there is **no /vdi plugin**. Staging, rendering,    ║
║  the descriptor, the auth seam, and source-type routing already work and are proven      ║
║  offline. The external build runs end-to-end NOW via the local-path convenience (a       ║
║  local path or ``file://`` URL pointing at an issue payload JSON).                       ║
╚══════════════════════════════════════════════════════════════════════════════════════╝
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import unquote, urlparse

# The auth seam (TASK-052) lives under core/adapters; put it on the path and import it.
_ADAPTERS = Path(__file__).resolve().parents[1] / "adapters"
if str(_ADAPTERS) not in sys.path:
    sys.path.insert(0, str(_ADAPTERS))
from jpmc_adapters import auth as _auth  # noqa: E402

SOURCE_TYPE = "jira"               # the source type this connector serves (source-type-keyed, D7)

_DEFAULT_AUTH_REF = "jpmc_adapters:jira"


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# ──────────────────────────────────────────────────────────────────────────────────────
#  ▼▼▼  VDI PLACEHOLDER — EDIT THIS FUNCTION IN PLACE ON THE JPMC VDI  ▼▼▼
# ──────────────────────────────────────────────────────────────────────────────────────
def _fetch_issue(url: str, handle) -> dict:
    """[TBD — VDI] Fetch the Jira issue at ``url`` and return its JSON payload as a dict.

    This is the ONLY environment-specific piece. On the VDI, replace this body with the real
    fetch (edit THIS function in place — no /vdi plugin). A typical Jira REST call:

        import httpx                                     # already a backend dependency
        token = handle.reveal() if handle else None      # the seam-resolved access token
        if not token:
            raise _auth.AuthResolutionError(
                "Jira fetch needs a token — set auth_ref: jpmc_adapters:jira")
        headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}
        # Resolve `url` to an issue key (…/browse/PBI-1234) then pull it:
        #   GET {base}/rest/api/2/issue/{key}?fields=summary,description,issuetype,status,…
        with httpx.Client(timeout=60) as client:
            r = client.get(api_url, headers=headers)
            r.raise_for_status()
            return r.json()

    Contract this MUST honour (already verified by the rest of the pipeline):
      • return the parsed issue payload as a **dict** — ``render_issue`` turns it into the
        staged Markdown, so this function does no formatting of its own;
      • use ``handle.reveal()`` for the credential — NEVER log it, embed it in ``url``, or
        write it anywhere but the request header (FR-DC-12);
      • raise on a non-2xx / empty payload so a failed pull is loud, not a 0-byte staged file.

    Note the shape difference from the document connectors: they write bytes to a target path,
    this **returns a payload**. Rendering is shared, deterministic and proven offline, so the
    VDI edit stays a pure "make the network call" change.
    """
    raise NotImplementedError(
        "[TBD — VDI] Jira fetch is not wired yet. Edit ingest_jira._fetch_issue in place "
        "(or inject via set_fetcher) with your instance's REST call, then re-run. For offline "
        "testing, pass a local path or file:// URL to an issue payload JSON instead "
        "(external-build convenience)."
    )
# ──────────────────────────────────────────────────────────────────────────────────────
#  ▲▲▲  END VDI PLACEHOLDER  ▲▲▲
# ──────────────────────────────────────────────────────────────────────────────────────


# Indirection so the VDI / tests can supply a fetcher without editing the function above.
_FETCHER = _fetch_issue


def set_fetcher(fn) -> None:
    """Install the active Jira fetcher ``fn(url, handle) -> dict`` (VDI / tests).

    Editing ``_fetch_issue`` in place is the primary VDI path; this seam additionally lets tests
    inject a local stub. No other code changes — the seam absorbs it.
    """
    global _FETCHER
    _FETCHER = fn


def _is_local(url: str) -> bool:
    """True if ``url`` is a local path or a ``file://`` URL (the external-build convenience)."""
    return urlparse(url).scheme in ("", "file")


def _local_path(url: str) -> Path:
    """Resolve a local path / ``file://`` URL to a filesystem ``Path``."""
    parsed = urlparse(url)
    return Path(unquote(parsed.path)) if parsed.scheme == "file" else Path(url)


def issue_key(payload: dict, url: str = "") -> str:
    """The issue key — from the payload, else parsed off the URL, else ``issue``.

    Used for the staged filename and the extract's title, so a manifest entry is recognisable
    without opening it.
    """
    key = str(payload.get("key") or "").strip()
    if key:
        return key
    tail = Path(unquote(urlparse(url).path)).name
    stem = tail.split(".")[0]
    return stem or "issue"


# Payload field → extract heading, in render order. Data, not branches: a new field is one row
# here (D7 keeps this table source-type-keyed, never domain-keyed). Values are copied verbatim;
# a field the payload lacks is OMITTED, never invented (cite-or-flag).
_FIELD_HEADINGS: tuple[tuple[str, str], ...] = (
    ("summary", "Summary"),
    ("issuetype", "Issue type"),
    ("status", "Status"),
    ("priority", "Priority"),
    ("resolution", "Resolution"),
    ("labels", "Labels"),
    ("components", "Components"),
    ("fixVersions", "Fix versions"),
    ("created", "Created"),
    ("updated", "Updated"),
    ("description", "Description"),
    ("acceptance_criteria", "Acceptance criteria"),
    ("comment", "Comments"),
)


def _flatten(value) -> str:
    """Render one Jira field value to plain text — mechanically, never interpretively.

    Jira wraps most things in objects (``{"name": …}``, ``{"value": …}``) and repeats them in
    arrays. This unwraps those shapes and joins lists; it does not summarise, reorder, or drop
    content. Anything it does not recognise is emitted as JSON rather than silently skipped.
    """
    if value is None or value == "" or value == []:
        return ""
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, (int, float, bool)):
        return str(value)
    if isinstance(value, dict):
        for k in ("name", "value", "displayName", "key"):
            if isinstance(value.get(k), str):
                return value[k].strip()
        # A comment-ish object: author + body reads better than raw JSON, still verbatim.
        if "body" in value:
            who = _flatten(value.get("author")) or "unknown"
            when = _flatten(value.get("created"))
            head = f"{who}" + (f" ({when})" if when else "")
            return f"**{head}:** {_flatten(value['body'])}"
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    if isinstance(value, list):
        parts = [p for p in (_flatten(v) for v in value) if p]
        if not parts:
            return ""
        # A list renders as a LIST. Blank-line-joining made three labels occupy eight lines of
        # index surface, and `lines` is the unit the index selects in and the author pulls by —
        # so padding inflates every range that covers it for no content. Multi-line members
        # (comments carry author + body) keep the blank-line form, since bulleting a paragraph
        # block would misrepresent its structure rather than tighten it.
        if any("\n" in p for p in parts):
            return "\n\n".join(parts)
        return "\n".join(f"- {p}" for p in parts)
    return str(value)


def render_issue(payload: dict, *, url: str = "") -> str:
    """Render an issue payload to the Markdown extract. Deterministic; assigns no meaning.

    Every recognised field becomes a fixed heading in a fixed order with its value copied
    verbatim. Fields the payload does not carry are omitted. Fields this table does not know
    are collected under "Other fields" rather than dropped — an unknown field silently
    disappearing is exactly the invisibility this design refuses (totality).
    """
    fields = payload.get("fields") if isinstance(payload.get("fields"), dict) else payload
    key = issue_key(payload, url)
    summary = _flatten(fields.get("summary"))

    lines: list[str] = [f"# {key}" + (f" — {summary}" if summary else ""), ""]
    if url:
        lines += [f"Source: {url}", ""]

    rendered: set[str] = {"summary"} if summary else set()
    for field, heading in _FIELD_HEADINGS:
        if field == "summary":
            continue
        text = _flatten(fields.get(field))
        if not text:
            continue
        rendered.add(field)
        lines += [f"## {heading}", "", text, ""]

    extra = {k: v for k, v in fields.items()
             if k not in rendered and k != "summary" and _flatten(v)}
    if extra:
        lines += ["## Other fields", ""]
        for k in sorted(extra):
            lines.append(f"- **{k}:** {_flatten(extra[k])}")
        lines.append("")

    while lines and lines[-1] == "":
        lines.pop()
    return "\n".join(lines) + "\n"


def pull_issue(
    url: str,
    dest: str | Path,
    *,
    source: str = SOURCE_TYPE,
    auth_ref: str | None = _DEFAULT_AUTH_REF,
    ts: str | None = None,
) -> dict:
    """Pull a Jira issue into ``<dest>/<source>/`` and return a §6.6.2 descriptor.

    Resolves ``auth_ref`` at the seam (FR-DC-12), fetches via the active fetcher (or reads a
    local payload JSON — the external-build convenience), renders it to Markdown, and emits the
    **same descriptor shape as ``ingest_file.py``** so nothing downstream changes. Never branches
    on ``domain`` (D7).
    """
    staging_dir = Path(dest) / source
    staging_dir.mkdir(parents=True, exist_ok=True)

    if _is_local(url):
        # External-build convenience: read a mock payload so the connector runs end-to-end
        # offline (no auth needed) while the real Jira fetch is wired on the VDI.
        src = _local_path(url)
        if not src.exists() or not src.is_file():
            raise FileNotFoundError(f"local Jira issue payload not found: {src}")
        try:
            payload = json.loads(src.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise ValueError(f"local Jira payload is not valid JSON: {src} ({exc})") from exc
    else:
        handle = _auth.resolve_auth(auth_ref)          # AuthHandle | None — secret stays inside it;
        payload = _FETCHER(url, handle)                # resolved lazily, only for the real fetch

    if not isinstance(payload, dict) or not payload:
        raise RuntimeError(f"Jira fetch produced no usable payload for {url}")

    target = staging_dir / f"{issue_key(payload, url)}.md"
    target.write_text(render_issue(payload, url=url), encoding="utf-8")

    return {
        "type": SOURCE_TYPE,
        "source": source,
        "url": url,                                    # provenance (the Jira issue URL) → manifest §3.2
        "staged_path": str(target),                    # rendered issue the doc pipeline reads
        "auth_ref": auth_ref,                          # pointer only — never the secret (FR-DC-12)
        "ingest_ts": ts or _now_iso(),
    }


def _jira_sources_from_ui_input(ui_input_path: str | Path) -> list[dict]:
    """Load every ``type: jira`` source entry from a ``UI_INPUT.yaml`` (§3.1).

    Like Confluence, Jira supports **multiple** entries (one issue each), so this returns the
    full list; ``main`` stages each (the orchestrator does the same via per-source fan-out).
    """
    import yaml  # local import: only the UI-INPUT path needs YAML

    cfg = yaml.safe_load(Path(ui_input_path).read_text(encoding="utf-8"))
    matches = [s for s in (cfg.get("sources") or []) if s.get("type") == SOURCE_TYPE]
    if not matches:
        raise ValueError(f"no source of type {SOURCE_TYPE!r} in {ui_input_path}")
    return matches


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description="Jira issue connector: stage an issue for the doc pipeline (§6.6.2).")
    ap.add_argument("--ui-input", help="path to UI_INPUT.yaml; stages every type:jira source entry")
    ap.add_argument("--url", help="Jira issue URL (or a local path / file:// to a payload JSON for offline testing); overrides UI_INPUT")
    ap.add_argument("--dest", default="sources", help="staging root (default: sources/); issue lands in <dest>/<source>/")
    ap.add_argument("--source", help="logical source label (default: 'jira' or UI_INPUT value)")
    ap.add_argument("--auth-ref", help="auth seam pointer (default: jpmc_adapters:jira or UI_INPUT value)")
    args = ap.parse_args(argv)

    try:
        if args.url:
            entries = [{"url": args.url, "source": args.source, "auth_ref": args.auth_ref}]
        elif args.ui_input:
            entries = _jira_sources_from_ui_input(args.ui_input)
        else:
            ap.error("need --url or --ui-input with a type:jira source")

        descriptors = [
            pull_issue(
                e.get("url"), args.dest,
                source=(args.source or e.get("source") or SOURCE_TYPE),
                auth_ref=(args.auth_ref or e.get("auth_ref") or _DEFAULT_AUTH_REF),
            )
            for e in entries
        ]
    except (FileNotFoundError, ValueError, RuntimeError, NotImplementedError,
            _auth.AuthResolutionError) as exc:
        print(f"ingest_jira.py: {exc}", file=sys.stderr)
        return 1

    # One issue = one entry: print a single descriptor for one, an array for multiple.
    out = descriptors[0] if len(descriptors) == 1 else descriptors
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
