#!/usr/bin/env python3
"""ingest_confluence.py — the Confluence document-source connector, §6.6.2 (TASK-063).

Generic and **source-type-keyed** (D7 / FR-DC-11): the connector for ``type: confluence``
document sources — a Confluence **page** URL. It pulls the page through the auth seam,
**stages** it into the run's source area, and emits the **same** source descriptor shape as
``ingest_file.py`` so the downstream pipeline is unchanged (FR-XS-01, descriptor parity). It
assigns **no meaning** — staging only; tagging is the adapter pack's job downstream (the
``confluence`` docs_pipeline lane, TASK-063B).

**One link = one page** (mirrors one-PDF-one-source). Multiple Confluence pages = multiple
``type: confluence`` source entries; the orchestrator fans out one worker per entry, so each
page becomes its own slice / manifest entry and is tagged independently. Page-tree / space
listing (pull every child) is a deferred enhancement, not this connector's job.

Contract (§6.6.2) — identical descriptor shape to ``ingest_file.py``:
  consumes : a ``UI_INPUT.sources[]`` entry of ``type: confluence`` (``url``, ``source``,
             ``auth_ref: jpmc_adapters:confluence``) + auth via the seam (FR-DC-12).
  produces : the raw page content staged under ``<dest>/<source>/``; returns / prints a JSON
             descriptor (``type``, ``source``, ``url``, ``staged_path``, ``auth_ref``,
             ``ingest_ts``) — the exact handoff the doc pipeline reads.

**Never branches on ``domain`` (D7).** This script does not read ``domain`` (FR-DC-11).

**Auth (FR-DC-12).** ``auth_ref`` is a pointer resolved at the seam
(``jpmc_adapters.auth.resolve_auth``) → an ``AuthHandle``; its secret is used only to
authenticate the fetch and never appears in the descriptor, the staged file, or any artifact.

╔══════════════════════════════════════════════════════════════════════════════════════╗
║  VDI WIRE-UP — the ONE function to edit on the JPMC VDI.                               ║
║                                                                                        ║
║  Everything in this file is real EXCEPT ``_fetch_confluence`` below: the actual         ║
║  Confluence REST fetch (which endpoint, the auth header, page-id resolution) is         ║
║  environment-specific, so it ships as a marked ``[TBD — VDI]`` placeholder. On the VDI  ║
║  you **edit that one function in place** to add the real call + JPMC auth (exactly the   ║
║  way ``ingest_sharepoint.py``'s ``_download_pdf`` was wired) — there is **no /vdi         ║
║  plugin** and no separation. Staging, the descriptor, the auth seam, and source-type     ║
║  routing already work and are proven offline. The external build runs end-to-end NOW     ║
║  via the local-path convenience (a ``file://`` or local path ``url``).                   ║
╚══════════════════════════════════════════════════════════════════════════════════════╝
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import unquote, urlparse

# The auth seam (TASK-052) lives under core/adapters; put it on the path and import it.
_ADAPTERS = Path(__file__).resolve().parents[1] / "adapters"
if str(_ADAPTERS) not in sys.path:
    sys.path.insert(0, str(_ADAPTERS))
from jpmc_adapters import auth as _auth  # noqa: E402

SOURCE_TYPE = "confluence"         # the source type this connector serves (source-type-keyed, D7)

_DEFAULT_AUTH_REF = "jpmc_adapters:confluence"


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# ──────────────────────────────────────────────────────────────────────────────────────
#  ▼▼▼  VDI PLACEHOLDER — EDIT THIS FUNCTION IN PLACE ON THE JPMC VDI  ▼▼▼
# ──────────────────────────────────────────────────────────────────────────────────────
def _fetch_confluence(url: str, handle, target: Path) -> None:
    """[TBD — VDI] Fetch the Confluence page at ``url`` and write its content to ``target``.

    This is the ONLY environment-specific piece. On the VDI, replace this body with the real
    fetch (edit THIS function in place — no /vdi plugin). A typical Confluence REST call:

        import httpx                                     # already a backend dependency
        token = handle.reveal() if handle else None      # the seam-resolved access token
        if not token:
            raise _auth.AuthResolutionError(
                "Confluence fetch needs a token — set auth_ref: jpmc_adapters:confluence")
        headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}
        # Resolve `url` to the page id per your instance, then pull the body (storage/view):
        #   GET {base}/rest/api/content/{page_id}?expand=body.storage
        with httpx.Client(timeout=60) as client:
            r = client.get(api_url, headers=headers)
            r.raise_for_status()
            body = r.json()["body"]["storage"]["value"]   # HTML storage format
            target.write_text(body, encoding="utf-8")

    Contract this MUST honour (already verified by the rest of the pipeline):
      • write the page content to ``target`` (an ``.html`` path under the staging dir);
      • use ``handle.reveal()`` for the credential — NEVER log it, embed it in ``url``, or
        write it anywhere but the request header (FR-DC-12);
      • raise on a non-2xx / empty body so a failed pull is loud, not a 0-byte staged file.
    """
    raise NotImplementedError(
        "[TBD — VDI] Confluence fetch is not wired yet. Edit ingest_confluence._fetch_confluence "
        "in place (or inject via set_fetcher) with your instance's REST call, then re-run. "
        "For offline testing, pass a local path or file:// URL instead (external-build convenience)."
    )
# ──────────────────────────────────────────────────────────────────────────────────────
#  ▲▲▲  END VDI PLACEHOLDER  ▲▲▲
# ──────────────────────────────────────────────────────────────────────────────────────


# Indirection so the VDI / tests can supply a fetcher without editing the function above.
_FETCHER = _fetch_confluence


def set_fetcher(fn) -> None:
    """Install the active Confluence fetcher ``fn(url, handle, target)`` (VDI / tests).

    Editing ``_fetch_confluence`` in place is the primary VDI path; this seam additionally
    lets tests inject a local stub. No other code changes — the seam absorbs it.
    """
    global _FETCHER
    _FETCHER = fn


def _is_local(url: str) -> bool:
    """True if ``url`` is a local path or a ``file://`` URL (the external-build convenience)."""
    scheme = urlparse(url).scheme
    if scheme in ("", "file"):
        return True
    return False


def _local_path(url: str) -> Path:
    """Resolve a local path / ``file://`` URL to a filesystem ``Path``."""
    parsed = urlparse(url)
    return Path(unquote(parsed.path)) if parsed.scheme == "file" else Path(url)


def _filename_for(url: str) -> str:
    """Derive the staged filename from the URL path; default to ``page.html``."""
    name = Path(unquote(urlparse(url).path)).name or "page"
    return name if "." in name else f"{name}.html"


def pull_page(
    url: str,
    dest: str | Path,
    *,
    source: str = SOURCE_TYPE,
    auth_ref: str | None = _DEFAULT_AUTH_REF,
    ts: str | None = None,
) -> dict:
    """Pull a Confluence page into ``<dest>/<source>/`` and return a §6.6.2 descriptor.

    Resolves ``auth_ref`` at the seam (FR-DC-12), fetches via the active fetcher (or the
    local-path convenience), and emits the **same descriptor shape as ``ingest_file.py``** so
    nothing downstream changes. Never branches on ``domain`` (D7).
    """
    staging_dir = Path(dest) / source
    staging_dir.mkdir(parents=True, exist_ok=True)
    target = staging_dir / _filename_for(url)

    if _is_local(url):
        # External-build convenience: stage a local page so the connector runs end-to-end
        # offline (no auth needed) while the real Confluence fetch is wired on the VDI.
        src = _local_path(url)
        if not src.exists() or not src.is_file():
            raise FileNotFoundError(f"local Confluence-stand-in page not found: {src}")
        shutil.copy2(src, target)
    else:
        handle = _auth.resolve_auth(auth_ref)          # AuthHandle | None — secret stays inside it;
        _FETCHER(url, handle, target)                  # resolved lazily, only for the real fetch
        if not target.exists() or target.stat().st_size == 0:
            raise RuntimeError(f"Confluence fetch produced no bytes for {url} → {target}")

    return {
        "type": SOURCE_TYPE,
        "source": source,
        "url": url,                                    # provenance (the Confluence URL) → manifest §3.2
        "staged_path": str(target),                    # raw page the doc pipeline reads
        "auth_ref": auth_ref,                          # pointer only — never the secret (FR-DC-12)
        "ingest_ts": ts or _now_iso(),
    }


def _confluence_sources_from_ui_input(ui_input_path: str | Path) -> list[dict]:
    """Load every ``type: confluence`` source entry from a ``UI_INPUT.yaml`` (§3.1).

    Unlike single-source connectors, Confluence supports **multiple** links (one page each),
    so this returns the full list; ``main`` stages each (the orchestrator does the same via
    per-source fan-out at run time)."""
    import yaml  # local import: only the UI-INPUT path needs YAML

    cfg = yaml.safe_load(Path(ui_input_path).read_text(encoding="utf-8"))
    matches = [s for s in (cfg.get("sources") or []) if s.get("type") == SOURCE_TYPE]
    if not matches:
        raise ValueError(f"no source of type {SOURCE_TYPE!r} in {ui_input_path}")
    return matches


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Confluence page connector: stage a page for the doc pipeline (§6.6.2).")
    ap.add_argument("--ui-input", help="path to UI_INPUT.yaml; stages every type:confluence source entry")
    ap.add_argument("--url", help="Confluence page URL (or a local path / file:// for offline testing); overrides UI_INPUT")
    ap.add_argument("--dest", default="sources", help="staging root (default: sources/); page lands in <dest>/<source>/")
    ap.add_argument("--source", help="logical source label (default: 'confluence' or UI_INPUT value)")
    ap.add_argument("--auth-ref", help="auth seam pointer (default: jpmc_adapters:confluence or UI_INPUT value)")
    args = ap.parse_args(argv)

    try:
        if args.url:
            entries = [{"url": args.url, "source": args.source, "auth_ref": args.auth_ref}]
        elif args.ui_input:
            entries = _confluence_sources_from_ui_input(args.ui_input)
        else:
            ap.error("need --url or --ui-input with a type:confluence source")

        descriptors = [
            pull_page(
                e.get("url"), args.dest,
                source=(args.source or e.get("source") or SOURCE_TYPE),
                auth_ref=(args.auth_ref or e.get("auth_ref") or _DEFAULT_AUTH_REF),
            )
            for e in entries
        ]
    except (FileNotFoundError, ValueError, RuntimeError, NotImplementedError, _auth.AuthResolutionError) as exc:
        print(f"ingest_confluence.py: {exc}", file=sys.stderr)
        return 1

    # One link = one page: print a single descriptor for one, an array for multiple.
    out = descriptors[0] if len(descriptors) == 1 else descriptors
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
