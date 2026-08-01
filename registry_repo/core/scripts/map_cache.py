#!/usr/bin/env python3
"""map_cache.py — `cache/code_maps/index.yaml`, the 4-branch gate's lookup (D-A22, TASK-115).

**Mutable build state, deliberately outside the frozen registry.** The retired
`onboarding_manifest.yaml` mixed a SHA-pinned registry artifact with build records, so every map
build wanted to dirty a frozen file. Three lifetimes, three homes: language freeze in
`extractor_manifest.yaml`, repo reading-rules in `code_profiles/`, build state here.

One record per repo, keyed by the map-validity pair `(commit_sha, profile_sha)` plus the extractor
sha. Per-file purposes cache separately, on **file content hash** — the two keys answer different
questions: the pair says *is this map still valid at all*, the content hash says *is this
particular purpose still valid*. That split is exactly what makes branch 3 incremental.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

REPO_ROOT = Path(__file__).resolve().parents[2]
CACHE_DIR = REPO_ROOT / "cache" / "code_maps"
INDEX = CACHE_DIR / "index.yaml"


def load_index(path: Path | None = None) -> dict:
    import yaml
    p = path or INDEX
    if not p.exists():
        return {"repos": []}
    return yaml.safe_load(p.read_text(encoding="utf-8")) or {"repos": []}


def record_for(repo: str, path: Path | None = None) -> Optional[dict]:
    """The cache record for ``repo``, or ``None`` if it has never been built."""
    return next((r for r in load_index(path).get("repos") or [] if r.get("repo") == repo), None)


def update_record(repo: str, *, seal_id: str = "", commit_sha: str, profile_sha: str,
                  extractor_sha: str, map_dir: str, last_built: str,
                  path: Path | None = None) -> dict:
    """Upsert this repo's build record. Last-write-wins; one record per repo."""
    import yaml
    p = path or INDEX
    index = load_index(p)
    rec = {"repo": repo, "seal_id": seal_id, "commit_sha": commit_sha,
           "profile_sha": profile_sha, "built_with_extractor_sha": extractor_sha,
           "map_dir": map_dir, "last_built": last_built}
    index["repos"] = [r for r in index.get("repos") or [] if r.get("repo") != repo] + [rec]
    index["repos"].sort(key=lambda r: r["repo"])
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(yaml.safe_dump(index, sort_keys=False), encoding="utf-8")
    return rec


def load_purpose_cache(repo: str, path: Path | None = None) -> dict:
    """Per-file purposes, keyed on file CONTENT hash — not path.

    Content-hash keying is what makes a rename free and a one-line edit cheap: the renamed file
    keeps its purpose, and only genuinely changed content pays for a new one.
    """
    p = (path or CACHE_DIR) / f"{repo}.purposes.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


def save_purpose_cache(repo: str, entries: dict, path: Path | None = None) -> Path:
    d = path or CACHE_DIR
    d.mkdir(parents=True, exist_ok=True)
    p = d / f"{repo}.purposes.json"
    p.write_text(json.dumps(entries, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return p
