#!/usr/bin/env python3
"""publish_registry.py — package the registry subset and push it to Bitbucket as repo #1.

This is the *publish* half of the registry lifecycle (TASK-053; §2.1, §6.6.1, Appendix B,
FR-XS-10, NFR-01). `hydrate.py` is the *pull* half. Together they make the registry a
SHA-pinned Bitbucket repo: published here, hydrated into each run scaffold there.

What it does, in order:

  1. **HARD build-checks gate (§10).** Runs all five §10 checks (`build_checks.run_all`)
     against the SOURCE repo. If ANY is red, publishing is BLOCKED — `PublishBlocked` is
     raised naming the violations and **nothing is pushed**. "A registry push is blocked
     unless build checks are green" (TASK-053 acceptance) is enforced here, not advised.
  2. **Collect the subset** declared by `registry_manifest.yaml` (core/ + overlays/ +
     the curated docs subset), applying the manifest's exclude globs (no __pycache__/.pyc/
     .git/.DS_Store). The published tree is EXACTLY this subset — nothing else.
  3. **Publish to the remote.** Clone the target Bitbucket repo, replace its tracked content
     with the collected subset, commit, and push. The resulting commit SHA is the
     `registry_sha` an operator pins into `UI_INPUT.yaml`; `hydrate.py --registry <url>`
     then reproduces the scaffold byte-for-byte at that SHA (NFR-01).

**Auth (FR-DC-12).** The push uses ambient git transport — SSH for the external build
(`git@bitbucket.org:...`), the JPMC HTTP-access-token path at VDI port. No secret is read
or written here; the seam (`jpmc_adapters.auth`) is bypassed for ambient SSH by design.

**External build / proof.** The "Bitbucket remote" may be a local bare git repo
(`git init --bare`), which behaves identically to a remote URL for clone/push — so the whole
publish→hydrate round-trip is exercised on one machine with no network (see
`fixtures/registry/verify_registry.py`). The mechanism is what ports to the VDI; only the
remote URL and the (ambient) credential transport differ.
"""
from __future__ import annotations

import argparse
import fnmatch
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import build_checks  # sibling: the §10 gate

_REPO_ROOT = Path(__file__).resolve().parents[2]
_DEFAULT_MANIFEST = _REPO_ROOT / "core" / "registry_manifest.yaml"

# Identity for the publish commit — bare/CI environments may have no configured git user.
_COMMIT_NAME = "PDLC Registry Publisher"
_COMMIT_EMAIL = "registry@pdlc.local"


class PublishBlocked(RuntimeError):
    """Raised when the §10 build-checks gate is red — publishing is refused, nothing pushed."""


def _git(args: list[str], cwd: Path | None = None) -> str:
    proc = subprocess.run(["git", *args], cwd=str(cwd) if cwd else None, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed: {proc.stderr.strip()}")
    return proc.stdout.strip()


def _load_yaml(path: Path) -> dict:
    import yaml

    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def gate_build_checks(source_root: Path) -> list[str]:
    """Run the five §10 checks against ``source_root``; return [] if green, else the violations.

    The single green/red signal that the seam is internally consistent (FR-DC-09, NFR-06) —
    the publish precondition.
    """
    results = build_checks.run_all(repo_root=source_root)
    violations: list[str] = []
    for r in results:
        if not r.ok:
            violations.append(f"{r.name}: " + ("; ".join(r.violations) or "failed"))
    return violations


def _excluded(rel: str, patterns: list[str]) -> bool:
    rel_posix = Path(rel).as_posix()
    return any(fnmatch.fnmatch(rel_posix, pat) for pat in patterns)


def collect_subset(manifest: dict, source_root: Path) -> list[tuple[Path, str]]:
    """Resolve the manifest into (abs_path, rel_path) pairs — the exact files to publish.

    ``trees`` are walked recursively; ``docs`` are explicit files. The ``exclude`` globs are
    applied to every candidate (matched against the POSIX relative path). Deterministic: the
    returned list is sorted by relative path.
    """
    include = manifest.get("include") or {}
    excludes = manifest.get("exclude") or []
    out: dict[str, Path] = {}

    for tree in include.get("trees") or []:
        base = source_root / tree
        if not base.is_dir():
            raise FileNotFoundError(f"registry manifest tree missing: {tree} (under {source_root})")
        for path in base.rglob("*"):
            if not path.is_file():
                continue
            rel = path.relative_to(source_root).as_posix()
            if not _excluded(rel, excludes):
                out[rel] = path

    for doc in include.get("docs") or []:
        path = source_root / doc
        if not path.is_file():
            raise FileNotFoundError(f"registry manifest doc missing: {doc} (under {source_root})")
        rel = path.relative_to(source_root).as_posix()
        if not _excluded(rel, excludes):
            out[rel] = path

    return [(path, rel) for rel, path in sorted(out.items())]


def stage_registry(
    dest: str | Path,
    *,
    source_root: str | Path = _REPO_ROOT,
    manifest_path: str | Path = _DEFAULT_MANIFEST,
    force: bool = False,
) -> dict:
    """Gate on §10, collect the manifest subset, and lay it into ``dest`` as a pushable tree.

    Same content `publish_registry` would push, but written to a local folder instead of a
    remote — for a manual/offline push (e.g. on the VDI: ``git init`` ``dest``, add the remote,
    commit, push). ``core/`` and ``overlays/`` land at the ROOT of ``dest`` so the published
    repo is hydrate-shaped. Raises :class:`PublishBlocked` if the build checks are red.
    """
    source_root = Path(source_root)
    dest = Path(dest)
    manifest = _load_yaml(Path(manifest_path))

    violations = gate_build_checks(source_root)
    if violations:
        raise PublishBlocked(
            "registry stage blocked — §10 build checks are RED:\n  - " + "\n  - ".join(violations)
        )

    subset = collect_subset(manifest, source_root)
    if not subset:
        raise ValueError("registry manifest resolved to zero files — check include/ trees and docs")

    if dest.exists() and any(dest.iterdir()) and not force:
        raise FileExistsError(f"stage dest already populated: {dest} (use --force to overwrite)")
    if dest.exists() and force:
        for entry in dest.iterdir():
            shutil.rmtree(entry) if entry.is_dir() else entry.unlink()

    for abs_path, rel in subset:
        target = dest / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(abs_path, target)

    return {
        "staged_to": str(dest),
        "source_root": str(source_root),
        "checks": "green",
        "file_count": len(subset),
        "published_paths": [rel for _, rel in subset],
    }


def _clear_worktree(clone: Path) -> None:
    """Remove every tracked/working entry except ``.git`` so the published tree is EXACTLY the subset."""
    for entry in clone.iterdir():
        if entry.name == ".git":
            continue
        if entry.is_dir():
            shutil.rmtree(entry)
        else:
            entry.unlink()


def publish_registry(
    registry_url: str,
    *,
    source_root: str | Path = _REPO_ROOT,
    manifest_path: str | Path = _DEFAULT_MANIFEST,
    branch: str = "main",
    message: str = "Publish PDLC registry subset",
    dry_run: bool = False,
) -> dict:
    """Gate on §10, package the manifest subset, and push it to ``registry_url`` as repo #1.

    Returns a descriptor with the published ``registry_sha`` (the new commit) and the file
    count. ``dry_run`` runs the gate + collection and reports what *would* publish without
    touching the remote. Raises :class:`PublishBlocked` if the build checks are red.
    """
    source_root = Path(source_root)
    manifest = _load_yaml(Path(manifest_path))

    # 1) HARD GATE — no push if the seam is red.
    violations = gate_build_checks(source_root)
    if violations:
        raise PublishBlocked(
            "registry publish blocked — §10 build checks are RED:\n  - " + "\n  - ".join(violations)
        )

    # 2) Collect the exact subset.
    subset = collect_subset(manifest, source_root)
    if not subset:
        raise ValueError("registry manifest resolved to zero files — check include/ trees and docs")
    rel_paths = [rel for _, rel in subset]

    descriptor: dict = {
        "registry_url": registry_url,
        "branch": branch,
        "source_root": str(source_root),
        "checks": "green",
        "file_count": len(subset),
        "published_paths": rel_paths,
        "dry_run": dry_run,
    }

    if dry_run:
        descriptor["registry_sha"] = None
        descriptor["pushed"] = False
        return descriptor

    # 3) Publish: clone remote → replace content with subset → commit → push.
    tmp = Path(tempfile.mkdtemp(prefix="publish-registry-"))
    try:
        clone = tmp / "registry"
        _git(["clone", registry_url, str(clone)])  # works for empty remotes too (warns, rc 0)

        has_head = subprocess.run(
            ["git", "rev-parse", "--verify", "HEAD"], cwd=str(clone), capture_output=True, text=True
        ).returncode == 0
        # Land on the target branch in both the empty-repo and existing-repo cases.
        _git(["checkout", "-B", branch], cwd=clone) if has_head else _git(["checkout", "-b", branch], cwd=clone)

        _clear_worktree(clone)
        for abs_path, rel in subset:
            target = clone / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(abs_path, target)

        _git(["add", "-A"], cwd=clone)
        status = _git(["status", "--porcelain"], cwd=clone)
        if not status and has_head:
            # Remote already matches the subset — nothing to push; report current HEAD.
            descriptor["registry_sha"] = _git(["rev-parse", "HEAD"], cwd=clone)
            descriptor["pushed"] = False
            descriptor["note"] = "remote already up to date with the registry subset"
            return descriptor

        _git(["-c", f"user.name={_COMMIT_NAME}", "-c", f"user.email={_COMMIT_EMAIL}",
              "commit", "-m", message], cwd=clone)
        registry_sha = _git(["rev-parse", "HEAD"], cwd=clone)
        _git(["push", "origin", f"HEAD:refs/heads/{branch}"], cwd=clone)

        descriptor["registry_sha"] = registry_sha
        descriptor["pushed"] = True
        return descriptor
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Publish (or stage) the SHA-pinned registry subset for Bitbucket (repo #1, §2.1).")
    ap.add_argument("registry_url", nargs="?", help="target registry repo (e.g. git@bitbucket.org:vm1999/registry.git) or a local bare repo path; omit when --stage")
    ap.add_argument("--stage", help="write the registry subset into this folder (pushable tree) instead of pushing to a remote")
    ap.add_argument("--source-root", default=str(_REPO_ROOT), help=f"repo to publish from (default: {_REPO_ROOT})")
    ap.add_argument("--manifest", default=str(_DEFAULT_MANIFEST), help="registry manifest (default: core/registry_manifest.yaml)")
    ap.add_argument("--branch", default="main", help="branch to publish (default: main)")
    ap.add_argument("--message", default="Publish PDLC registry subset", help="commit message")
    ap.add_argument("--force", action="store_true", help="overwrite a populated --stage folder")
    ap.add_argument("--dry-run", action="store_true", help="gate + collect, report what would publish; no push")
    args = ap.parse_args(argv)

    if args.stage:
        try:
            desc = stage_registry(args.stage, source_root=args.source_root,
                                  manifest_path=args.manifest, force=args.force)
        except PublishBlocked as exc:
            print(f"publish_registry.py: {exc}", file=sys.stderr)
            return 2
        except (ValueError, FileExistsError, FileNotFoundError, OSError) as exc:
            print(f"publish_registry.py: {exc}", file=sys.stderr)
            return 1
        print(json.dumps({k: v for k, v in desc.items() if k != "published_paths"}, ensure_ascii=False, indent=2))
        print(f"\nStaged {desc['file_count']} files → {desc['staged_to']}  "
              f"(git init, add remote, commit, push — core/ + overlays/ at the root)", file=sys.stderr)
        return 0

    if not args.registry_url:
        ap.error("need a registry_url (or use --stage <dir>)")

    try:
        descriptor = publish_registry(
            args.registry_url,
            source_root=args.source_root,
            manifest_path=args.manifest,
            branch=args.branch,
            message=args.message,
            dry_run=args.dry_run,
        )
    except PublishBlocked as exc:
        print(f"publish_registry.py: {exc}", file=sys.stderr)
        return 2  # distinct from generic failure: the gate refused the push
    except (ValueError, FileNotFoundError, RuntimeError, OSError) as exc:
        print(f"publish_registry.py: {exc}", file=sys.stderr)
        return 1

    # Keep the full file list off stdout unless asked — print a compact summary + the SHA.
    summary = {k: v for k, v in descriptor.items() if k != "published_paths"}
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    if descriptor.get("registry_sha"):
        print(f"\nregistry_sha = {descriptor['registry_sha']}  "
              f"({'pushed' if descriptor['pushed'] else 'unchanged'} → pin this in UI_INPUT.yaml)", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
