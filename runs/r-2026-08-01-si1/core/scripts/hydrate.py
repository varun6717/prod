#!/usr/bin/env python3
"""hydrate.py — registry → run-scaffold hydration (Appendix B; FR-XS-10, NFR-01, NFR-07).

At **Generate**, a run scaffold is materialized from the version-pinned registry. This
script is that hydration step: it pulls the registry at one pinned `registry_sha` and
**selectively copies** the slice a run needs into the working path —

    core/                         (skills, scripts, extractors, adapters, + the domain's
                                   profiles/templates only — other domains pruned)
    overlays/<runtime_tool>/      (only the selected tool's overlay — the other pruned)

per Appendix B. It is **plumbing, not judgment** (NFR-07): clone, checkout, copy. It makes
no authoring call and — like ingestion — **never branches on domain semantics**; `domain`
and `runtime_tool` are used only to *select which already-authored paths to copy*, never to
alter content.

**SHA-pinning / reproducibility (FR-XS-10, NFR-01).** `registry_sha` is the single pin.
Re-hydrating the same SHA reproduces the scaffold **byte-for-byte** (the generated
instruction file is produced later by `generate.py` (§6) as a pure function of
`UI_INPUT` + manifest — not here). The code repo is pinned separately by `commit_sha` in
`code_map.json` / `run_state.json` at clone time (`clone.py`), not by this script.

Mechanics (Appendix B):
  - **MVP path (here):** `git clone --depth 1 <registry>` → `git checkout <registry_sha>`
    → selective copy. Simple, deterministic, auditable. If the pinned SHA is not in the
    depth-1 shallow fetch, we `fetch --unshallow` and retry the checkout (robustness, not
    a design change).
  - **Optimization (noted, not built):** `--filter=blob:none --sparse` + `sparse-checkout
    set core profiles/<domain> templates/<domain> overlays/<tool>` to materialize only the
    needed paths. Not required for MVP.

**External build (this repo).** The registry *is* this repo, so `--registry` defaults to
the repo root (the dir containing `core/` + `overlays/`). The **mechanism** is what ports
to the VDI; the source location is the only thing that differs. A local non-git registry
is supported as an external-build convenience (direct selective copy, SHA unverified, with
a note) — mirroring `clone.py`'s plain-dir convenience.

Determinism details (NFR-01):
  - copied content is exact (`shutil.copy2`); only *content* matters for "byte-for-byte".
  - build artifacts that would inject non-determinism are skipped: `__pycache__/`, `*.pyc`,
    and any `.git/`.
  - the returned descriptor lists `copied[]` as **sorted** relative paths, so the descriptor
    itself is a deterministic function of the pinned SHA + domain + tool.
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

# repo root for the external build: core/scripts/hydrate.py → parents[2] is the registry root
_REPO_ROOT = Path(__file__).resolve().parents[2]

# names skipped during the selective copy — non-deterministic build artifacts / VCS metadata
_SKIP_NAMES = {"__pycache__", ".git"}
_SKIP_SUFFIXES = (".pyc",)


def _git(args: list[str], cwd: Path | None = None) -> str:
    """Run a git command, returning stripped stdout; raises on non-zero (with stderr)."""
    proc = subprocess.run(
        ["git", *args],
        cwd=str(cwd) if cwd else None,
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed: {proc.stderr.strip()}")
    return proc.stdout.strip()


def resolve_remote_sha(url: str, ref: str | None = None) -> str:
    """Pin the current tip of a remote registry branch (TASK-053): ``git ls-remote`` → SHA.

    ``ref`` is the branch/tag the registry lives on (e.g. ``feature/pdlc_app``); ``None``
    resolves the remote's default ``HEAD``. Used at Generate so the operator supplies repo +
    branch and the ``registry_sha`` is resolved automatically, never hand-entered. Raises if the
    ref does not resolve — a live registry that cannot be pinned fails loud (FR-XS-10/NFR-01).
    """
    target = ref or "HEAD"
    out = _git(["ls-remote", url, target])
    if not out:
        raise RuntimeError(f"registry ref not found: {url}@{target} (ls-remote returned no match)")
    return out.split()[0]


def _is_git_source(path: Path) -> bool:
    """True if ``path`` is a git repo git can clone from — a work tree (has ``.git``) OR a
    **bare** repo (`git init --bare`, the shape a local "Bitbucket" remote takes).

    A bare repo has no ``.git`` subdir; its git internals (``HEAD``, ``objects/``, ``refs/``)
    sit at the top level. Without this, a bare remote misclassifies as a "local non-git
    registry" and takes the unverified direct-copy path — wrong for a real remote (TASK-053
    requires the *verified* clone+checkout path; FR-XS-10/NFR-01).
    """
    if (path / ".git").exists():
        return True
    return (path / "HEAD").is_file() and (path / "objects").is_dir() and (path / "refs").is_dir()


def _is_skipped(rel: Path) -> bool:
    """True if any path part is a skipped name, or the file has a skipped suffix."""
    if any(part in _SKIP_NAMES for part in rel.parts):
        return True
    return rel.suffix in _SKIP_SUFFIXES


def _copy_filtered(
    src: Path, dst: Path, base: Path, *, keep: "callable[[Path], bool]" = lambda _: True,
) -> list[str]:
    """Copy ``src``→``dst`` recursively, skipping build artifacts and anything ``keep`` rejects.

    ``keep`` receives the path **relative to ``src``** and gates the domain/tool pruning.
    Returns the copied file paths reported **relative to ``base``** (the scaffold root) so
    the descriptor's ``copied[]`` has one consistent base. Deterministic: traversal order
    does not affect content; the caller sorts the combined list.
    """
    copied: list[str] = []
    if not src.exists():
        return copied
    for path in src.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(src)
        if _is_skipped(rel) or not keep(rel):
            continue
        target = dst / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, target)
        copied.append(str(target.relative_to(base)))
    return copied


def _core_keep(domain: str) -> "callable[[Path], bool]":
    """Pruning predicate for ``core/``: keep all of core EXCEPT other domains' seam dirs.

    ``profiles/`` and ``templates/`` are domain seams (§2.1) — only the run's ``<domain>``
    subtree is hydrated; sibling domains are pruned. Everything else under core
    (skills, scripts, extractors, adapters, top-level manifests/templates) is kept whole.
    """
    def keep(rel: Path) -> bool:
        parts = rel.parts
        if len(parts) >= 2 and parts[0] in ("profiles", "templates"):
            return parts[1] == domain      # keep only the selected domain's subtree
        return True
    return keep


def hydrate(
    registry: str | Path,
    registry_sha: str,
    domain: str,
    runtime_tool: str,
    dest: str | Path,
    *,
    ref: str | None = None,
    force: bool = False,
) -> dict:
    """Hydrate the run scaffold at ``dest`` from ``registry`` pinned at ``registry_sha``.

    Clones the registry (depth 1), checks out the pinned SHA, then selectively copies
    ``core/`` (domain-pruned) + ``overlays/<runtime_tool>/`` into ``dest``. Returns a
    descriptor recording the verified SHA and the sorted list of copied files. A local
    non-git ``registry`` is copied directly (SHA unverified, noted) — external-build only.

    ``ref`` (optional branch/tag) lands the shallow clone on a specific branch — needed when
    the registry lives on a feature branch (one-repo/two-feature layout), so the pinned SHA is
    reachable. ``registry`` may be a remote URL (``https://…`` / ``git@…``) or a local path; a
    URL is passed to ``git clone`` verbatim (never ``Path``-normalized — that collapses ``//``).
    """
    if runtime_tool not in ("claude", "copilot"):
        raise ValueError(f"runtime_tool must be 'claude' or 'copilot' (got {runtime_tool!r})")

    dest = Path(dest)
    dest_core = dest / "core"
    if dest_core.exists() and any(dest_core.iterdir()) and not force:
        raise FileExistsError(f"scaffold already hydrated: {dest_core} exists (use force=True to overwrite)")

    registry_str = str(registry)
    is_remote = "://" in registry_str or registry_str.startswith("git@")
    local = None if is_remote else Path(registry)   # URLs stay strings — Path() collapses '//'
    note: str | None = None
    tmp: Path | None = None
    try:
        if local is not None and local.is_dir() and not _is_git_source(local):
            # External-build convenience: a local non-git registry — copy current tree.
            source_root = local
            verified_sha = None
            note = "local non-git registry copied directly (external build); registry_sha unverified"
        else:
            clone_src = registry_str if is_remote else str(local)
            tmp = Path(tempfile.mkdtemp(prefix="hydrate-"))
            checkout = tmp / "registry"
            clone_cmd = ["clone", "--depth", "1"]
            if ref:
                clone_cmd += ["--branch", ref]   # land the shallow clone on the registry's branch
            clone_cmd += [clone_src, str(checkout)]
            _git(clone_cmd)
            try:
                _git(["checkout", registry_sha], cwd=checkout)
            except RuntimeError:
                # pinned SHA not in the shallow fetch — deepen, then retry (robustness)
                _git(["fetch", "--unshallow"], cwd=checkout)
                _git(["checkout", registry_sha], cwd=checkout)
            verified_sha = _git(["rev-parse", "HEAD"], cwd=checkout)
            source_root = checkout

        copied: list[str] = []
        copied += _copy_filtered(source_root / "core", dest / "core", dest, keep=_core_keep(domain))
        copied += _copy_filtered(
            source_root / "overlays" / runtime_tool, dest / "overlays" / runtime_tool, dest,
        )
        copied.sort()
    finally:
        if tmp is not None:
            shutil.rmtree(tmp, ignore_errors=True)

    if not copied:
        raise ValueError(
            f"hydration copied nothing — check registry {registry} has core/ and overlays/{runtime_tool}/"
        )

    descriptor: dict = {
        "registry": str(registry),
        "registry_sha": registry_sha,
        "registry_sha_verified": verified_sha,    # None for the local non-git convenience path
        "domain": domain,
        "runtime_tool": runtime_tool,
        "dest": str(dest),
        "file_count": len(copied),
        "copied": copied,
    }
    if note:
        descriptor["note"] = note
    return descriptor


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description="Hydrate a run scaffold from the SHA-pinned registry (Appendix B).",
    )
    ap.add_argument("--ui-input", help="path to UI_INPUT.yaml; pulls registry_sha/domain/runtime_tool/working_path")
    ap.add_argument("--registry", help=f"registry path or URL (default: this repo root, {_REPO_ROOT})")
    ap.add_argument("--registry-sha", help="pinned registry commit (overrides UI_INPUT)")
    ap.add_argument("--registry-ref", help="branch/tag the registry lives on, e.g. feature/pdlc_app (overrides UI_INPUT.registry_ref)")
    ap.add_argument("--domain", help="domain to hydrate (overrides UI_INPUT)")
    ap.add_argument("--runtime-tool", choices=["claude", "copilot"], help="overlay to hydrate (overrides UI_INPUT)")
    ap.add_argument("--dest", help="scaffold destination (default: UI_INPUT.working_path)")
    ap.add_argument("--force", action="store_true", help="overwrite an already-hydrated dest/core")
    args = ap.parse_args(argv)

    registry_sha, domain, runtime_tool, dest, registry_ref = (
        args.registry_sha, args.domain, args.runtime_tool, args.dest, args.registry_ref,
    )
    if args.ui_input:
        import yaml  # local import: only the UI-INPUT path needs YAML

        cfg = yaml.safe_load(Path(args.ui_input).read_text(encoding="utf-8"))
        registry_sha = registry_sha or cfg.get("registry_sha")
        domain = domain or cfg.get("domain")
        runtime_tool = runtime_tool or cfg.get("runtime_tool")
        dest = dest or cfg.get("working_path")
        registry_ref = registry_ref or cfg.get("registry_ref")

    registry = args.registry or str(_REPO_ROOT)
    missing = [n for n, v in (("registry_sha", registry_sha), ("domain", domain),
                              ("runtime_tool", runtime_tool), ("dest", dest)) if not v]
    if missing:
        ap.error(f"missing required: {', '.join(missing)} (pass flags or --ui-input)")

    try:
        descriptor = hydrate(
            registry, registry_sha, domain, runtime_tool, dest, ref=registry_ref or None, force=args.force,
        )
    except (ValueError, FileExistsError, RuntimeError, OSError) as exc:
        print(f"hydrate.py: {exc}", file=sys.stderr)
        return 1

    print(json.dumps(descriptor, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
