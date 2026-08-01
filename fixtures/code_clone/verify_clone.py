#!/usr/bin/env python3
"""verify_clone.py — TASK-054 proof: code-source clone through the auth seam, secret-safe.

Exercises ``core/scripts/clone.py`` against a local bare git "Bitbucket" remote (identical
clone semantics to a real host, no network) and asserts the TASK-054 acceptance
(§6.6.2, §7, FR-DC-02/11/12, NFR-01, D8b):

  1. **Ambient clone** (no ``auth_ref``) — clones the bare remote into ``repo/``;
     ``commit_sha`` is pinned + recorded.
  2. **Idempotent on SHA match (D8b)** — a second clone into the populated ``repo/`` skips
     (returns the same ``commit_sha``, notes idempotency); a different ``ref`` is a conflict.
  3. **Token path is wired through the seam** — with ``auth_ref: jpmc_adapters:bitbucket``
     and a stub secret backend, ``resolve_auth`` is invoked and the clone authenticates via a
     ``GIT_ASKPASS`` helper. The token (a canary) appears NOWHERE: not in the descriptor, not
     under ``repo/``, not in a written ledger line, not even in the askpass *script file*
     (which references ``$GIT_AUTH_SECRET``, never the value).
  4. **No domain branch** — ``clone.py`` does not branch on ``domain`` (§10.4 stays green).

Offline + deterministic. Run:  .venv/bin/python fixtures/code_clone/verify_clone.py
"""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_REPO_ROOT / "core" / "scripts"))
sys.path.insert(0, str(_REPO_ROOT / "core" / "adapters"))

import clone  # noqa: E402
from jpmc_adapters import auth as _auth  # noqa: E402
from jpmc_adapters.auth import AuthHandle  # noqa: E402
from build_checks import branches_on_domain  # noqa: E402  (§10.4 static check)

_CANARY = "canary-token-DEADBEEF-LEAKCANARY"


class StubBackend:
    def __init__(self, secrets: dict[str, str]) -> None:
        self._secrets = secrets

    def get(self, key: str) -> str | None:
        return self._secrets.get(key)


def _check(label: str, cond: bool) -> None:
    print(f"  [{'PASS' if cond else 'FAIL'}] {label}")
    if not cond:
        raise SystemExit(f"verify_clone: FAILED — {label}")


def _git(args: list[str], cwd: Path | None = None) -> str:
    p = subprocess.run(["git", *args], cwd=str(cwd) if cwd else None, capture_output=True, text=True)
    if p.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed: {p.stderr.strip()}")
    return p.stdout.strip()


def _make_bare_remote(root: Path) -> tuple[Path, str]:
    """Create a work repo with one commit, mirror it to a bare 'Bitbucket' remote; return (bare, sha)."""
    work = root / "work"
    work.mkdir()
    _git(["init", "-b", "main", str(work)])
    _git(["-c", "user.name=t", "-c", "user.email=t@t", "commit", "--allow-empty", "-m", "seed"], cwd=work)
    (work / "main.c").write_text("int main(void){return 0;}\n", encoding="utf-8")
    _git(["add", "-A"], cwd=work)
    _git(["-c", "user.name=t", "-c", "user.email=t@t", "commit", "-m", "code"], cwd=work)
    sha = _git(["rev-parse", "HEAD"], cwd=work)
    bare = root / "code.git"
    _git(["clone", "--bare", str(work), str(bare)])
    return bare, sha


def _files_contain(root: Path, needle: str) -> bool:
    for p in root.rglob("*"):
        if p.is_file():
            try:
                if needle in p.read_text(encoding="utf-8", errors="ignore"):
                    return True
            except OSError:
                pass
    return False


def main() -> int:
    print("verify_clone.py — TASK-054 code-source clone through the auth seam")
    with tempfile.TemporaryDirectory(prefix="verify-clone-") as td:
        root = Path(td)
        bare, sha = _make_bare_remote(root)

        # 1) Ambient clone (no auth_ref) → commit_sha pinned.
        dest = root / "run" / "repo"
        d1 = clone.clone_repo(str(bare), dest)
        _check("ambient clone pinned commit_sha", d1["commit_sha"] == sha)
        _check("descriptor records auth_ref as None pointer", d1["auth_ref"] is None)
        _check("repo/ staged with the code", (dest / "main.c").is_file())

        # 2) Idempotent on SHA match (D8b) — second clone into populated repo/ is a no-op.
        d2 = clone.clone_repo(str(bare), dest)
        _check("idempotent re-clone returns same commit_sha", d2["commit_sha"] == sha)
        _check("idempotent re-clone notes the skip", "idempotent" in (d2.get("note") or ""))
        # ...and a different requested ref is a conflict, not a silent overwrite.
        conflict = False
        try:
            clone.clone_repo(str(bare), dest, ref="0000000")
        except FileExistsError:
            conflict = True
        _check("populated repo/ at a different ref raises a conflict", conflict)

        # 3) Token path wired through the seam — and the token never leaks.
        saved = _auth.get_backend()
        _auth.set_backend(StubBackend({"bitbucket": _CANARY}))
        try:
            dest2 = root / "run2" / "repo"
            d3 = clone.clone_repo(str(bare), dest2, auth_ref="jpmc_adapters:bitbucket")
            _check("token-path clone pinned commit_sha", d3["commit_sha"] == sha)
            _check("descriptor keeps auth_ref pointer (not the secret)",
                   d3["auth_ref"] == "jpmc_adapters:bitbucket" and _CANARY not in json.dumps(d3))
            # Mirror a ledger write + the descriptor to disk, then scan for the canary.
            (dest2.parent / "descriptor.json").write_text(json.dumps(d3), encoding="utf-8")
            (dest2.parent / "ledger.jsonl").write_text(
                json.dumps({"event": "ingest", "auth_ref": d3["auth_ref"]}) + "\n", encoding="utf-8")
            _check("token appears NOWHERE under the run workspace", not _files_contain(dest2.parent, _CANARY))

            # The GIT_ASKPASS mechanism: script file is secret-free; secret only in the child env.
            handle = AuthHandle("bitbucket", _CANARY, username="x-token-auth")
            env, askpass = clone._git_auth_env(handle)
            try:
                _check("askpass script file contains NO secret (reads $GIT_AUTH_SECRET)",
                       _CANARY not in askpass.read_text(encoding="utf-8"))
                user_out = subprocess.run(["sh", str(askpass), "Username for 'https://x':"],
                                          capture_output=True, text=True, env={**env}).stdout
                pass_out = subprocess.run(["sh", str(askpass), "Password for 'https://x':"],
                                          capture_output=True, text=True, env={**env}).stdout
                _check("askpass returns the username on a Username prompt", user_out == "x-token-auth")
                _check("askpass returns the token on a Password prompt", pass_out == _CANARY)
            finally:
                askpass.unlink(missing_ok=True)
        finally:
            _auth.set_backend(saved)

        # 4) §10.4 — clone.py does not branch on domain.
        _check("clone.py does not branch on `domain` (§10.4)",
               not branches_on_domain(_REPO_ROOT / "core" / "scripts" / "clone.py"))

    # ── the EMPTY-dest case (TASK-127 regression) ──────────────────────────────────────
    # generate.py lays repo/ as one of the §2.2 empty run dirs, so this is the state every
    # freshly generated scaffold is in. clone.py guarded for populated and for missing but not
    # for existing-and-empty, and fell through to a clone that cannot write to a directory that
    # already exists — a 100% failure rate on the code lane's first step. This fixture never saw
    # it because it clones into a temp path that does not exist yet, which is the one arrangement
    # a real run never has.
    print("\nempty destination (the shape a generated scaffold hands us):")
    with tempfile.TemporaryDirectory(prefix="verify-clone-empty-") as td:
        _bare_for_empty_test, _ = _make_bare_remote(Path(td))
        dest = Path(td) / "repo"
        dest.mkdir()                                   # exactly what generate.py leaves behind
        _check("dest exists and is empty before cloning",
               dest.is_dir() and not any(dest.iterdir()))
        d = clone.clone_repo(str(_bare_for_empty_test), dest)
        _check("clone into an existing EMPTY dir succeeds", any(dest.iterdir()))
        _check("and returns a descriptor", isinstance(d, dict) and d.get("dest"))

    print("verify_clone: ALL CHECKS PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
