#!/usr/bin/env python3
"""ingest_file.py — the document-source ingestion connector (direct file path), §6.6.2.

Generic and **source-type-keyed** (D7 / FR-DC-11): the connector for ``type: file``
document sources — a local filesystem path to a raw document (e.g. a PDF). It **stages**
the raw document into the run's source area and emits a source descriptor for
``pdf_extract`` (docs_pipeline step 1, §6.6.3) to extract. It assigns **no meaning** —
staging only; tagging is the adapter pack's job downstream.

Contract (§6.6.2):
  consumes : a ``UI_INPUT.sources[]`` entry of ``type: file`` (``path``, optional
             ``source`` / ``url`` / ``auth_ref``) + auth via the seam (``auth_ref``,
             never an inline secret — FR-DC-12). A local file typically needs no auth.
  produces : the raw document staged on disk under ``<dest>/<source>/``; returns / prints
             a JSON source descriptor (``type``, ``source``, ``url``, ``staged_path``,
             ``ingest_ts``) — the handoff ``pdf_extract`` reads (it is given the on-disk
             path + the descriptor, then writes ``context_set/<source>/<doc>.md``).

**Never branches on ``domain`` (D7).** This script does not read ``domain`` at all —
ingestion is identical for every domain (FR-DC-11).

**Slice-1 / Phase-5 note.** The first slice ingests one PDF by **direct path**; §6.6.2
admits the document source as "SharePoint connector, **or a direct file path**". Pulling
the PDF from SharePoint is a deferred "write one more connector" follow-on
(``ingest_sharepoint.py``, §11): purely additive and source-type-keyed off the same
contract — it would stage the same raw document + emit the same descriptor shape, so
nothing downstream (the ``docs_pipeline`` extract lane) changes when
it lands. That is the seam absorbing the change where it is designed to (FR-XS-01).

**Auth (FR-DC-12).** Any ``auth_ref`` is a **pointer** resolved at the seam (§7); the
secret never appears here or in any artifact. A local file path needs no auth, so the
external build's seam resolution is a documented passthrough.
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

SOURCE_TYPE = "file"               # the source type this connector serves (source-type-keyed, D7)


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def resolve_auth(auth_ref: str | None) -> None:
    """Resolve per-instance auth at the seam (§7 / FR-DC-12). Pointer in, no secret out.

    A local ``file`` source typically carries no ``auth_ref``; when present it points at
    the seam and is resolved there, never returned to or logged by the connector. This
    external build has no secret store, so resolution is a passthrough returning ``None``.
    """
    return None


def stage_document(
    path: str | Path,
    dest: str | Path,
    *,
    source: str = SOURCE_TYPE,
    url: str | None = None,
    auth_ref: str | None = None,
    ts: str | None = None,
) -> dict:
    """Stage a raw document into ``<dest>/<source>/`` and return a §6.6.2 source descriptor.

    The file is copied (not moved) so the original is untouched and the run becomes
    self-contained (NFR-01). ``url`` records provenance (the original location — a path
    or, for the future SharePoint connector, a URL); it flows to the manifest entry's
    ``url`` (§3.2). ``source`` is the logical source label used to partition
    ``context_set/<source>/`` and for the §3.2 selective-read routing.
    """
    resolve_auth(auth_ref)                                  # seam passthrough; no secret returned
    src = Path(path)
    if not src.exists() or not src.is_file():
        raise FileNotFoundError(f"document source not found (or not a file): {src}")

    staging_dir = Path(dest) / source
    staging_dir.mkdir(parents=True, exist_ok=True)
    staged_path = staging_dir / src.name
    shutil.copy2(src, staged_path)

    return {
        "type": SOURCE_TYPE,
        "source": source,
        "url": url if url is not None else str(src.resolve()),   # provenance → manifest §3.2
        "staged_path": str(staged_path),                          # raw doc pdf_extract reads
        "auth_ref": auth_ref,                                     # pointer only — never the secret
        "ingest_ts": ts or _now_iso(),
    }


def _source_from_ui_input(ui_input_path: str | Path) -> dict:
    """Load the single ``type: file`` source entry from a ``UI_INPUT.yaml`` (§3.1)."""
    import yaml  # local import: only the UI-INPUT path needs YAML

    cfg = yaml.safe_load(Path(ui_input_path).read_text(encoding="utf-8"))
    matches = [s for s in (cfg.get("sources") or []) if s.get("type") == SOURCE_TYPE]
    if not matches:
        raise ValueError(f"no source of type {SOURCE_TYPE!r} in {ui_input_path}")
    if len(matches) > 1:
        raise ValueError(f"slice-1 expects one {SOURCE_TYPE} source; found {len(matches)} in {ui_input_path}")
    return matches[0]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Document-source connector: stage a local PDF for pdf_extract (§6.6.2).")
    ap.add_argument("--ui-input", help="path to UI_INPUT.yaml; pulls the single type:file source entry")
    ap.add_argument("--path", help="local path to the raw document (overrides UI_INPUT)")
    ap.add_argument("--dest", default="sources", help="staging root (default: sources/); doc lands in <dest>/<source>/")
    ap.add_argument("--source", help="logical source label (default: 'file' or UI_INPUT value)")
    ap.add_argument("--url", help="provenance URL/location (default: the resolved source path)")
    ap.add_argument("--auth-ref", help="auth seam pointer (else from UI_INPUT; a local file needs none)")
    args = ap.parse_args(argv)

    path, source, url, auth_ref = args.path, args.source, args.url, args.auth_ref
    if args.ui_input:
        entry = _source_from_ui_input(args.ui_input)
        path = path or entry.get("path")
        source = source or entry.get("source")
        url = url or entry.get("url")
        auth_ref = auth_ref or entry.get("auth_ref")
    if not path:
        ap.error("need --path or --ui-input with a type:file source")

    try:
        descriptor = stage_document(
            path, args.dest, source=source or SOURCE_TYPE, url=url, auth_ref=auth_ref,
        )
    except (FileNotFoundError, ValueError) as exc:
        print(f"ingest_file.py: {exc}", file=sys.stderr)
        return 1

    print(json.dumps(descriptor, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
