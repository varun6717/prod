#!/usr/bin/env python3
"""clone.py — the code-source ingestion connector (Bitbucket → ``repo/``), §6.6.2.

Generic and **source-type-keyed** (D7 / FR-DC-11): this is the connector for code
sources (``type: bitbucket``). "Ingest" for code = **git clone** the SEAL-ID repo into
the run's ``repo/`` (FR-DC-02), pinned by the resolved ``commit_sha`` so the run is
reproducible (NFR-01 — the repo is pinned by ``commit_sha`` recorded at clone time).
The cloned tree is then handed to ``code_map_build`` via the adapter ``code_pipeline``
(§6.6.3). This script is the code analogue of the document connectors (``ingest_<type>.py``);
§10.4 maps every ``code`` source type to ``clone.py``.

Contract (§6.6.2):
  consumes : a ``UI_INPUT.sources[]`` entry of ``type: bitbucket`` (``repo_url``,
             ``seal_id``, ``auth_ref``) + auth via the seam (``auth_ref``, never an
             inline secret — FR-DC-12).
  produces : the repo staged on disk under ``repo/``; returns / prints a JSON source
             descriptor including the pinned ``commit_sha`` (NFR-01).

**Never branches on ``domain`` (D7).** This script does not read ``domain`` at all —
ingestion is identical for every domain; a new source type is one new connector in
``core/scripts/``, never a domain fork (FR-DC-11).

**Auth (FR-DC-12 / §7 — TASK-054).** Per-instance auth is a pointer ``auth_ref`` (e.g.
``jpmc_adapters:bitbucket``) resolved at the seam: ``jpmc_adapters.auth.resolve_auth``
returns an ``AuthHandle`` (or ``None``). The handle's secret is injected into ``git`` only
through a temporary ``GIT_ASKPASS`` helper that reads it from the child process
environment — it never appears in the clone URL, the argv, ``git config``, the descriptor,
or any artifact/ledger. ``auth_ref`` is recorded in the descriptor as a **pointer only**.
  - ``auth_ref`` absent / ``None`` → ``resolve_auth`` returns ``None`` → **ambient**
    credentials: an SSH key (the external build's ``git@bitbucket.org:…``) or a local path.
  - ``auth_ref: jpmc_adapters:bitbucket`` → the seam resolves the token (env now, JPMC
    HTTP-access-token store at VDI port) → secret-safe HTTPS clone. Same code path; only the
    secret backend differs.

**Idempotency (D8b).** A re-run that finds ``repo/`` already populated at a ``commit_sha``
trusts it as already cloned and **skips** the clone (returning the recorded ``commit_sha``),
unless ``force`` is set. A populated ``repo/`` at a different ``ref`` is a conflict, not a
silent overwrite.

**External-build convenience.** If ``repo_url`` is a local directory that is *not* a git
repo (e.g. the plain-dir ``fixtures/c_repo``), a tree copy stages it into ``repo/`` with
``commit_sha: null`` and a note — so the slice can be exercised end-to-end here without
forcing fixtures into git. A real URL / local git (work-tree or bare) repo always takes the
``git clone`` path.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

# The auth seam (TASK-052) lives under core/adapters; put it on the path and import it.
_ADAPTERS = Path(__file__).resolve().parents[1] / "adapters"
if str(_ADAPTERS) not in sys.path:
    sys.path.insert(0, str(_ADAPTERS))
from jpmc_adapters import auth as _auth  # noqa: E402

SOURCE_TYPE = "bitbucket"          # the source type this connector serves (source-type-keyed, D7)

# GIT_ASKPASS helper: git invokes it with the prompt as $1 and uses its stdout as the answer.
# The secret is read from the (child-process) ENVIRONMENT, so this *script file* contains no
# secret, and the token never reaches argv / git config / the URL (FR-DC-12).
_ASKPASS_SCRIPT = (
    "#!/bin/sh\n"
    'case "$1" in\n'
    "  Username*) printf '%s' \"$GIT_AUTH_USER\" ;;\n"
    "  *)         printf '%s' \"$GIT_AUTH_SECRET\" ;;\n"
    "esac\n"
)


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _is_bare_repo(path: Path) -> bool:
    """True if ``path`` is a bare git repo (HEAD + objects/ + refs/ at top level, no .git)."""
    return (path / "HEAD").is_file() and (path / "objects").is_dir() and (path / "refs").is_dir()


def _git_auth_env(handle) -> tuple[dict, Path | None]:
    """Build a secret-safe git environment for an ``AuthHandle`` (HTTPS + token).

    Returns ``(env_overrides, askpass_path)``. For ``handle is None`` (ambient SSH / local
    path / anonymous) there is nothing to inject → ``({}, None)``. Otherwise a temp
    ``GIT_ASKPASS`` script is written (mode 0700) and the username/secret are passed via the
    environment — never via argv, the URL, or git config. The caller MUST delete the script.
    """
    if handle is None:
        return {}, None
    fd, name = tempfile.mkstemp(prefix="clone-askpass-", suffix=".sh")
    os.close(fd)
    askpass = Path(name)
    askpass.write_text(_ASKPASS_SCRIPT, encoding="utf-8")
    askpass.chmod(0o700)
    env = {
        "GIT_ASKPASS": str(askpass),
        "GIT_TERMINAL_PROMPT": "0",                      # never fall back to an interactive prompt
        "GIT_AUTH_USER": handle.username or "x-token-auth",
        "GIT_AUTH_SECRET": handle.reveal(),              # secret lives only in the child env
    }
    return env, askpass


def _git(args: list[str], cwd: Path | None = None, *, env_overrides: dict | None = None) -> str:
    """Run a git command, returning stripped stdout; raises on non-zero (with stderr).

    ``env_overrides`` is merged onto ``os.environ`` for this call only (used to pass the
    ``GIT_ASKPASS`` auth env without leaking the secret into the parent process state).
    """
    env = {**os.environ, **env_overrides} if env_overrides else None
    proc = subprocess.run(
        ["git", *args],
        cwd=str(cwd) if cwd else None,
        capture_output=True,
        text=True,
        env=env,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed: {proc.stderr.strip()}")
    return proc.stdout.strip()


def _descriptor(repo_url: str, dest: Path, *, ref: str | None, commit_sha: str | None,
                seal_id: str | None, auth_ref: str | None, ts: str | None,
                note: str | None = None) -> dict:
    """Assemble the §6.6.2 source descriptor (stable shape — no contract change at TASK-054)."""
    d = {
        "type": SOURCE_TYPE,
        "seal_id": seal_id,
        "repo_url": repo_url,
        "dest": str(dest),
        "ref": ref,
        "commit_sha": commit_sha,          # NFR-01: pins the repo for reproducibility
        "auth_ref": auth_ref,              # pointer only — never the secret (FR-DC-12)
        "ingest_ts": ts or _now_iso(),
    }
    if note:
        d["note"] = note
    return d


def _existing_commit(dest: Path) -> str | None:
    """If ``dest`` is a populated git work tree, return its HEAD sha; else ``None``."""
    if not (dest / ".git").exists():
        return None
    try:
        return _git(["rev-parse", "HEAD"], cwd=dest)
    except RuntimeError:
        return None


def _ref_matches(dest: Path, ref: str, head: str) -> bool:
    """Best-effort: does ``ref`` resolve to the already-checked-out ``head`` in ``dest``?"""
    try:
        return _git(["rev-parse", f"{ref}^{{commit}}"], cwd=dest) == head
    except RuntimeError:
        return head.startswith(ref) or ref == head      # ref may be a sha (prefix)


def clone_repo(
    repo_url: str,
    dest: str | Path,
    *,
    ref: str | None = None,
    seal_id: str | None = None,
    auth_ref: str | None = None,
    ts: str | None = None,
    force: bool = False,
) -> dict:
    """Clone ``repo_url`` into ``dest`` (through the auth seam) and return a §6.6.2 descriptor.

    ``git clone`` by default; a full clone + checkout when ``ref`` is given. ``commit_sha`` is
    read back via ``rev-parse HEAD`` (NFR-01). Auth is resolved from ``auth_ref`` at the seam
    and injected secret-safely (``GIT_ASKPASS``); ``None``/absent ``auth_ref`` → ambient creds.
    Idempotent (D8b): a populated ``repo/`` at a ``commit_sha`` is trusted and the clone is
    skipped unless ``force``. A local non-git directory is tree-copied (external-build only).
    """
    dest = Path(dest)

    # Idempotency (D8b): a populated repo/ already at a commit is trusted (pin recorded at
    # first clone). force re-clones; a populated non-git dir or a ref mismatch is a conflict.
    if dest.exists() and any(dest.iterdir()):
        head = _existing_commit(dest)
        if force:
            shutil.rmtree(dest)
        elif head is not None:
            if ref and not _ref_matches(dest, ref, head):
                raise FileExistsError(
                    f"repo/ already at {head[:10]} but requested ref {ref!r} differs — "
                    f"clear {dest} or pass force=True"
                )
            return _descriptor(repo_url, dest, ref=ref, commit_sha=head, seal_id=seal_id,
                               auth_ref=auth_ref, ts=ts,
                               note="idempotent: repo/ already present at commit_sha; clone skipped (D8b)")
        else:
            raise FileExistsError(
                f"clone dest already populated and not a git repo: {dest} (clear it or pass force=True)"
            )

    dest.parent.mkdir(parents=True, exist_ok=True)

    src = Path(repo_url)
    is_local_nongit = (
        src.exists() and src.is_dir() and not (src / ".git").exists() and not _is_bare_repo(src)
    )
    if is_local_nongit:
        # External-build convenience: stage a plain local tree (e.g. fixtures/c_repo).
        shutil.copytree(src, dest)
        return _descriptor(repo_url, dest, ref=ref, commit_sha=None, seal_id=seal_id,
                           auth_ref=auth_ref, ts=ts,
                           note="local non-git directory staged by tree copy (external build); commit_sha unavailable")

    # Real clone (URL or local git/bare repo): resolve auth at the seam, inject secret-safely.
    handle = _auth.resolve_auth(auth_ref)                  # AuthHandle | None (None = ambient)
    auth_env, askpass = _git_auth_env(handle)
    try:
        if ref:
            _git(["clone", repo_url, str(dest)], env_overrides=auth_env)
            _git(["checkout", ref], cwd=dest)
        else:
            _git(["clone", "--depth", "1", repo_url, str(dest)], env_overrides=auth_env)
        commit_sha = _git(["rev-parse", "HEAD"], cwd=dest)
    finally:
        if askpass is not None:
            askpass.unlink(missing_ok=True)                # the secret never persisted on disk

    return _descriptor(repo_url, dest, ref=ref, commit_sha=commit_sha, seal_id=seal_id,
                       auth_ref=auth_ref, ts=ts)


def _source_from_ui_input(ui_input_path: str | Path) -> dict:
    """Load the single ``type: bitbucket`` source entry from a ``UI_INPUT.yaml`` (§3.1)."""
    import yaml  # local import: only the UI-INPUT path needs YAML

    cfg = yaml.safe_load(Path(ui_input_path).read_text(encoding="utf-8"))
    matches = [s for s in (cfg.get("sources") or []) if s.get("type") == SOURCE_TYPE]
    if not matches:
        raise ValueError(f"no source of type {SOURCE_TYPE!r} in {ui_input_path}")
    if len(matches) > 1:
        raise ValueError(f"slice-1 expects one {SOURCE_TYPE} source; found {len(matches)} in {ui_input_path}")
    return matches[0]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Code-source connector: git clone a Bitbucket repo into repo/ (§6.6.2).")
    ap.add_argument("--ui-input", help="path to UI_INPUT.yaml; pulls the single type:bitbucket source entry")
    ap.add_argument("--repo-url", help="repo URL or local git path (overrides UI_INPUT)")
    ap.add_argument("--dest", default="repo", help="clone destination (default: repo/)")
    ap.add_argument("--ref", help="branch/tag/commit to check out (default: clone HEAD)")
    ap.add_argument("--seal-id", help="SEAL ID for provenance (else from UI_INPUT)")
    ap.add_argument("--auth-ref", help="auth seam pointer, e.g. jpmc_adapters:bitbucket (else from UI_INPUT)")
    ap.add_argument("--force", action="store_true", help="re-clone even if repo/ is already populated (D8b override)")
    args = ap.parse_args(argv)

    repo_url, seal_id, auth_ref, ref = args.repo_url, args.seal_id, args.auth_ref, args.ref
    if args.ui_input:
        entry = _source_from_ui_input(args.ui_input)
        repo_url = repo_url or entry.get("repo_url")
        seal_id = seal_id or entry.get("seal_id")
        auth_ref = auth_ref or entry.get("auth_ref")
        ref = ref or entry.get("ref")          # optional branch/tag/commit from the UI source entry
    if not repo_url:
        ap.error("need --repo-url or --ui-input with a type:bitbucket source")

    try:
        descriptor = clone_repo(
            repo_url, args.dest, ref=ref, seal_id=seal_id, auth_ref=auth_ref, force=args.force,
        )
    except (RuntimeError, FileExistsError, ValueError, _auth.AuthResolutionError) as exc:
        print(f"clone.py: {exc}", file=sys.stderr)
        return 1

    print(json.dumps(descriptor, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
