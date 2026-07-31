#!/usr/bin/env python3
"""ingest_sharepoint.py — the SharePoint document-source connector, §6.6.2 (TASK-055).

Generic and **source-type-keyed** (D7 / FR-DC-11): the connector for ``type: sharepoint``
document sources — a SharePoint URL to a raw document (a PDF). It pulls the document through
the auth seam, **stages** it into the run's source area, and emits the **same** source
descriptor shape as ``ingest_file.py`` so the downstream pipeline
(the ``docs_pipeline`` extract lane) is unchanged (FR-XS-01). It
assigns **no meaning** — staging only; extraction is the adapter pack's job downstream, and
what the artifact is *for* is the operator's declared ``disposition`` (D-A12), never inferred here.

Contract (§6.6.2) — identical descriptor shape to ``ingest_file.py``:
  consumes : a ``UI_INPUT.sources[]`` entry of ``type: sharepoint`` (``url``, ``source``,
             ``auth_ref: jpmc_adapters:sharepoint``) + auth via the seam (FR-DC-12).
  produces : the raw document staged under ``<dest>/<source>/``; returns / prints a JSON
             descriptor (``type``, ``source``, ``url``, ``staged_path``, ``auth_ref``,
             ``ingest_ts``) — the exact handoff ``pdf_extract`` reads.

**Never branches on ``domain`` (D7).** This script does not read ``domain`` (FR-DC-11).

**Auth (FR-DC-12).** ``auth_ref`` is a pointer resolved at the seam
(``jpmc_adapters.auth.resolve_auth``) → an ``AuthHandle``; its secret is used only to
authenticate the fetch and never appears in the descriptor, the staged file, or any artifact.

╔══════════════════════════════════════════════════════════════════════════════════════╗
║  VDI WIRE-UP — the ONE placeholder to implement on the JPMC VDI.                       ║
║                                                                                        ║
║  Everything in this file is real EXCEPT ``_download_pdf`` below: the actual SharePoint  ║
║  fetch (which REST/Graph endpoint, the auth header, site/drive/item resolution) is      ║
║  environment-specific, so it is left as a marked ``[TBD — VDI]`` stub. Implement it     ║
║  there (or inject via ``set_downloader``); staging, the descriptor, the auth seam, and  ║
║  source-type routing already work and are proven offline. The external build can run    ║
║  end-to-end NOW via the local-path convenience (a ``file://`` or local path ``url``).   ║
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

SOURCE_TYPE = "sharepoint"         # the source type this connector serves (source-type-keyed, D7)

_DEFAULT_AUTH_REF = "jpmc_adapters:sharepoint"


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# ──────────────────────────────────────────────────────────────────────────────────────
#  ▼▼▼  VDI PLACEHOLDER — IMPLEMENT THIS ON THE JPMC VDI  ▼▼▼
# ──────────────────────────────────────────────────────────────────────────────────────
def _download_pdf(url: str, handle, target: Path) -> None:
    """[TBD — VDI] Fetch the PDF at ``url`` from SharePoint and write its bytes to ``target``.

    This is the ONLY environment-specific piece. On the VDI, implement the real fetch here
    (or inject an implementation via :func:`set_downloader` without editing this file).
    Model it on the tenant's working API example kept under ``core/scripts/_refs/`` — drop
    your reference at ``core/scripts/_refs/sharepoint_graph_reference.py`` (see that dir's
    README; reference material only, no secrets). A typical Microsoft Graph implementation:

        import httpx                                    # already a backend dependency
        token = handle.reveal() if handle else None     # the seam-resolved access token
        if not token:
            raise _auth.AuthResolutionError(
                "SharePoint fetch needs an access token — set auth_ref: jpmc_adapters:sharepoint")
        headers = {"Authorization": f"Bearer {token}"}
        # `url` may be a sharing URL or a Graph drive-item URL; resolve to a download URL per
        # your tenant's API, then stream the bytes:
        with httpx.stream("GET", download_url, headers=headers, timeout=60) as r:
            r.raise_for_status()
            with open(target, "wb") as fh:
                for chunk in r.iter_bytes():
                    fh.write(chunk)

    Contract this MUST honour (already verified by the rest of the pipeline):
      • write the raw document bytes to ``target`` (a ``.pdf`` path under the staging dir);
      • use ``handle.reveal()`` for the credential — NEVER log it, embed it in ``url``, or
        write it anywhere but the request header (FR-DC-12);
      • raise on a non-2xx / empty body so a failed pull is loud, not a 0-byte staged file.
    """
    raise NotImplementedError(
        "[TBD — VDI] SharePoint download is not wired yet. Implement ingest_sharepoint._download_pdf "
        "(or inject via set_downloader) with your tenant's Graph/REST fetch, then re-run. "
        "For offline testing, pass a local path or file:// URL instead (external-build convenience)."
    )
# ──────────────────────────────────────────────────────────────────────────────────────
#  ▲▲▲  END VDI PLACEHOLDER  ▲▲▲
# ──────────────────────────────────────────────────────────────────────────────────────


# Indirection so the VDI / tests can supply a downloader without editing the file above.
_DOWNLOADER = _download_pdf


def set_downloader(fn) -> None:
    """Install the active SharePoint downloader ``fn(url, handle, target)`` (VDI / tests).

    The single injection point: the VDI binds the real Graph/REST fetch behind the same
    connector; tests inject a local stub. No other code changes — the seam absorbs it.
    """
    global _DOWNLOADER
    _DOWNLOADER = fn


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
    """Derive the staged filename from the URL path; default to ``document.pdf``."""
    name = Path(unquote(urlparse(url).path)).name or "document.pdf"
    return name if name.lower().endswith(".pdf") else f"{name}.pdf"


def pull_document(
    url: str,
    dest: str | Path,
    *,
    source: str = SOURCE_TYPE,
    auth_ref: str | None = _DEFAULT_AUTH_REF,
    ts: str | None = None,
) -> dict:
    """Pull a SharePoint document into ``<dest>/<source>/`` and return a §6.6.2 descriptor.

    Resolves ``auth_ref`` at the seam (FR-DC-12), fetches via the active downloader (or the
    local-path convenience), and emits the **same descriptor shape as ``ingest_file.py``** so
    nothing downstream changes. Never branches on ``domain`` (D7).
    """
    handle = _auth.resolve_auth(auth_ref)              # AuthHandle | None — secret stays inside it

    staging_dir = Path(dest) / source
    staging_dir.mkdir(parents=True, exist_ok=True)
    target = staging_dir / _filename_for(url)

    if _is_local(url):
        # External-build convenience: stage a local PDF so the connector runs end-to-end
        # offline while the real SharePoint fetch (_download_pdf) is wired on the VDI.
        src = _local_path(url)
        if not src.exists() or not src.is_file():
            raise FileNotFoundError(f"local SharePoint-stand-in document not found: {src}")
        shutil.copy2(src, target)
    else:
        _DOWNLOADER(url, handle, target)               # VDI fetch (placeholder until implemented)
        if not target.exists() or target.stat().st_size == 0:
            raise RuntimeError(f"SharePoint fetch produced no bytes for {url} → {target}")

    return {
        "type": SOURCE_TYPE,
        "source": source,
        "url": url,                                    # provenance (the SharePoint URL) → manifest §3.2
        "staged_path": str(target),                    # raw doc pdf_extract reads
        "auth_ref": auth_ref,                          # pointer only — never the secret (FR-DC-12)
        "ingest_ts": ts or _now_iso(),
    }


def _source_from_ui_input(ui_input_path: str | Path) -> dict:
    """Load the single ``type: sharepoint`` source entry from a ``UI_INPUT.yaml`` (§3.1)."""
    import yaml  # local import: only the UI-INPUT path needs YAML

    cfg = yaml.safe_load(Path(ui_input_path).read_text(encoding="utf-8"))
    matches = [s for s in (cfg.get("sources") or []) if s.get("type") == SOURCE_TYPE]
    if not matches:
        raise ValueError(f"no source of type {SOURCE_TYPE!r} in {ui_input_path}")
    if len(matches) > 1:
        raise ValueError(f"slice-1 expects one {SOURCE_TYPE} source; found {len(matches)} in {ui_input_path}")
    return matches[0]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="SharePoint document connector: pull a PDF for pdf_extract (§6.6.2).")
    ap.add_argument("--ui-input", help="path to UI_INPUT.yaml; pulls the single type:sharepoint source entry")
    ap.add_argument("--url", help="SharePoint URL (or a local path / file:// for offline testing); overrides UI_INPUT")
    ap.add_argument("--dest", default="sources", help="staging root (default: sources/); doc lands in <dest>/<source>/")
    ap.add_argument("--source", help="logical source label (default: 'sharepoint' or UI_INPUT value)")
    ap.add_argument("--auth-ref", help="auth seam pointer (default: jpmc_adapters:sharepoint or UI_INPUT value)")
    args = ap.parse_args(argv)

    url, source, auth_ref = args.url, args.source, args.auth_ref
    if args.ui_input:
        entry = _source_from_ui_input(args.ui_input)
        url = url or entry.get("url")
        source = source or entry.get("source")
        auth_ref = auth_ref or entry.get("auth_ref")
    if not url:
        ap.error("need --url or --ui-input with a type:sharepoint source")

    try:
        descriptor = pull_document(
            url, args.dest, source=source or SOURCE_TYPE,
            auth_ref=auth_ref or _DEFAULT_AUTH_REF,
        )
    except (FileNotFoundError, ValueError, RuntimeError, NotImplementedError, _auth.AuthResolutionError) as exc:
        print(f"ingest_sharepoint.py: {exc}", file=sys.stderr)
        return 1

    print(json.dumps(descriptor, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
