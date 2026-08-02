#!/usr/bin/env python3
"""verify_registry.py — TASK-053 proof: registry publish→hydrate over a local "Bitbucket" remote.

Exercises the registry lifecycle end-to-end with **no network** — a local bare git repo
(`git init --bare`) stands in for the Bitbucket remote (identical clone/push semantics) — and
asserts the TASK-053 acceptance (§2.1, §6.6.1, Appendix B, FR-XS-10, NFR-01):

  1. **Publish is gated on §10.** `publish_registry` runs `build_checks` first; a green seam
     publishes the manifest subset and returns the new commit as `registry_sha`.
  2. **A red seam BLOCKS the push.** Against a broken source (a deleted seam artifact),
     `publish_registry` raises `PublishBlocked` and the remote stays empty — nothing pushed.
  3. **Verified hydrate.** `hydrate(--registry <bare remote>, registry_sha)` takes the
     clone+checkout+verify path (NOT the non-git convenience) and `registry_sha_verified`
     equals the requested SHA — reproducible by the single pin (NFR-01).
  4. **Published tree = the manifest subset.** core/ + overlays/ + the docs subset are
     present; build artifacts (`__pycache__`, `*.pyc`) are excluded.

Offline + deterministic. Run:  .venv/bin/python fixtures/registry/verify_registry.py
"""
from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_REPO_ROOT / "core" / "scripts"))

import hydrate  # noqa: E402
import publish_registry  # noqa: E402
import publish_registry  # noqa: E402
from publish_registry import PublishBlocked  # noqa: E402

_DOMAIN = "payment_brand"
_TOOL = "copilot"


def _check(label: str, cond: bool) -> None:
    print(f"  [{'PASS' if cond else 'FAIL'}] {label}")
    if not cond:
        raise SystemExit(f"verify_registry: FAILED — {label}")


def _git(args: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=str(cwd) if cwd else None, capture_output=True, text=True)


def _bare_remote(at: Path) -> Path:
    remote = at
    _git(["init", "--bare", "-b", "main", str(remote)])
    return remote


def _remote_is_empty(remote: Path) -> bool:
    out = _git(["ls-remote", str(remote)]).stdout.strip()
    return out == ""


def _broken_source(into: Path) -> Path:
    """A minimal copy of the repo (core/overlays/docs/fixtures) with one seam artifact deleted."""
    src = into / "broken_src"
    for sub in ("core", "overlays", "docs", "fixtures"):
        shutil.copytree(_REPO_ROOT / sub, src / sub,
                        ignore=shutil.ignore_patterns("__pycache__", "*.pyc", ".git"))
    # Delete a required seam artifact → §10.3 goes red. `adapter.yaml` is the durable choice
    # across the ADR-008 re-cut: the vocabulary this used to delete no longer exists (D-A22),
    # and the profile it might otherwise delete was itself renamed (brd_profile → si_profile
    # at TASK-108). Deleting the adapter also exercises §10.3's pack-pointer half, which
    # cannot run without it.
    (src / "core" / "profiles" / _DOMAIN / "adapter" / "adapter.yaml").unlink()
    return src


def main() -> int:
    print("verify_registry.py — TASK-053 registry publish→hydrate proof")
    with tempfile.TemporaryDirectory(prefix="verify-registry-") as td:
        root = Path(td)

        # 1) GREEN publish to a bare "Bitbucket" remote.
        #
        # `stage_dir` is passed for two reasons. It keeps this proof side-effect-free — a publish
        # now refreshes the tracked snapshot, and without an override that would rewrite the real
        # `registry_repo/` in the working tree just by running the fixture. And it is what lets
        # the coupling be asserted below against a KNOWN-STALE directory.
        snapshot = root / "snapshot"
        snapshot.mkdir()
        (snapshot / "retired_skill.md").write_text("a file the manifest does not publish\n")
        (snapshot / "core").mkdir()
        (snapshot / "core" / "registry_manifest.yaml").write_text("stale: true\n")

        remote = _bare_remote(root / "registry.git")
        desc = publish_registry.publish_registry(str(remote), source_root=_REPO_ROOT,
                                                 message="proof publish", stage_dir=snapshot)
        _check("build checks gated green", desc["checks"] == "green")
        _check("publish pushed a commit", desc["pushed"] is True)
        _check("registry_sha returned", bool(desc.get("registry_sha")))
        registry_sha = desc["registry_sha"]

        # ── a successful push leaves the tracked snapshot CURRENT ──────────────────────────
        # The wrong-but-plausible implementation this kills: publish pushes and leaves the
        # snapshot alone, which is what it did until now. `verify_registry`'s drift check
        # compares snapshot ↔ source and would stay GREEN while the remote lagged — and a run
        # resolves registry_sha from the branch tip, so it would pin the stale commit and
        # hydrate old core/ silently. The snapshot is seeded stale above precisely so "it
        # happened to already match" cannot pass this.
        _check("publish reports the snapshot it refreshed",
               desc.get("snapshot_refreshed") == str(snapshot))
        manifest_ = publish_registry._load_yaml(publish_registry._DEFAULT_MANIFEST)
        expected_ = {rel for _, rel in publish_registry.collect_subset(manifest_, _REPO_ROOT)}
        actual_ = {p.relative_to(snapshot).as_posix() for p in snapshot.rglob("*") if p.is_file()}
        _check("the pushed subset and the snapshot hold exactly the same files",
               actual_ == expected_)
        _check("the seeded stale file is GONE (refresh replaces, never merges)",
               not (snapshot / "retired_skill.md").exists())
        _check("and every snapshot file is byte-identical to source",
               not [r for r in sorted(expected_)
                    if (snapshot / r).read_bytes() != (_REPO_ROOT / r).read_bytes()])

        # 4) Published tree = the manifest subset (clone the remote and inspect).
        published = root / "published"
        _git(["clone", str(remote), str(published)])
        present = {p.relative_to(published).as_posix() for p in published.rglob("*") if p.is_file()}
        _check("core/ published", any(p.startswith("core/") for p in present))
        _check("overlays/ published", any(p.startswith("overlays/") for p in present))
        _check("docs subset published (TECH_SPEC)", "docs/TECH_SPEC.md" in present)
        _check("registry_manifest.yaml published", "core/registry_manifest.yaml" in present)
        _check("no __pycache__/.pyc published", not any("__pycache__" in p or p.endswith(".pyc") for p in present))

        # 3) VERIFIED hydrate from the bare remote at the pinned SHA.
        scaffold = root / "scaffold"
        h = hydrate.hydrate(remote, registry_sha, _DOMAIN, _TOOL, scaffold)
        _check("hydrate took the VERIFIED git path (not the non-git convenience)",
               h.get("note") is None and h["registry_sha_verified"] is not None)
        _check("registry_sha_verified == requested", h["registry_sha_verified"] == registry_sha)
        _check("hydrated core/ is non-empty", (scaffold / "core").is_dir() and h["file_count"] > 0)
        _check("hydrated only the requested domain's profiles",
               not list((scaffold / "core" / "profiles").glob("*")) or
               all(d.name == _DOMAIN for d in (scaffold / "core" / "profiles").iterdir()))

        # 2) RED seam BLOCKS the push — to a fresh empty remote.
        remote2 = _bare_remote(root / "registry2.git")
        broken = _broken_source(root)
        blocked = False
        try:
            publish_registry.publish_registry(str(remote2), source_root=broken, message="should not publish")
        except PublishBlocked as exc:
            blocked = True
            _check("PublishBlocked names a §10 check", "§10" in str(exc))
        _check("red seam raised PublishBlocked", blocked)
        _check("blocked publish pushed NOTHING (remote still empty)", _remote_is_empty(remote2))

    # ── a bad registry_sha must name ITSELF (TASK-127 regression) ──────────────────────
    # hydrate retried `git fetch --unshallow` unconditionally when the pinned SHA was not found.
    # Git IGNORES --depth for local clones ("--depth is ignored in local clones; use file://"),
    # so against any local registry the clone is complete and that retry always failed with
    # "--unshallow on a complete repository does not make sense" — an error about shallowness
    # that says nothing about the real fault, which is a bad registry_sha. The message pointed
    # the operator at the wrong thing entirely.
    print("\na bad registry_sha reports the SHA, not shallowness:")
    with tempfile.TemporaryDirectory(prefix="verify-registry-badsha-") as td:
        dest = Path(td) / "scaffold"
        raised = ""
        try:
            hydrate.hydrate(str(_REPO_ROOT), "deadbeefdeadbeef", _DOMAIN, _TOOL, dest)
        except Exception as exc:                       # noqa: BLE001 — the message IS the test
            raised = str(exc)
        _check("hydrating at a nonexistent SHA fails", bool(raised))
        _check("the error names the offending registry_sha", "deadbeef" in raised)
        _check("and does NOT blame shallowness", "unshallow" not in raised.lower())

    # ── the TRACKED snapshot must not drift from core/ (TASK-127 defect 1) ─────────────
    # `registry_repo/` is committed so the push-ready registry can travel to the VDI. Being a
    # tracked COPY of core/ + overlays/ + docs/, it drifts the moment anyone edits the original
    # and forgets to re-stage — and it did: after the ADR-008 cutover it still held
    # `brd_author.skill.md` and `brd_validator.skill.md`, retired skills, while lacking
    # `confluence_extract`. A tracked duplicate of the dead pipeline, in the very artifact meant
    # to carry to the VDI. Nothing checked it, so nothing said so.
    #
    # This check makes the duplicate honest: re-stage after any core/ change, exactly as protocol
    # step 5 already requires you to re-publish.
    print("\nthe tracked registry snapshot matches core/:")
    snapshot = _REPO_ROOT / "registry_repo"
    _check("registry_repo/ exists", snapshot.is_dir())
    manifest = publish_registry._load_yaml(publish_registry._DEFAULT_MANIFEST)
    expected = {rel for _, rel in publish_registry.collect_subset(manifest, _REPO_ROOT)}
    actual = {str(f.relative_to(snapshot)) for f in snapshot.rglob("*")
              if f.is_file() and "__pycache__" not in f.parts}
    _check(f"the snapshot holds exactly the {len(expected)} published files",
           actual == expected)
    if actual != expected:
        print(f"    missing from snapshot: {sorted(expected - actual)[:6]}")
        print(f"    stale in snapshot:     {sorted(actual - expected)[:6]}")
        print("    fix: python3 core/scripts/publish_registry.py --stage registry_repo --force")
    drifted = [rel for rel in sorted(expected & actual)
               if (snapshot / rel).read_bytes() != (_REPO_ROOT / rel).read_bytes()]
    _check("and every one is byte-identical to its source", not drifted)
    if drifted:
        print(f"    drifted: {drifted[:6]}")
        print("    fix: python3 core/scripts/publish_registry.py --stage registry_repo --force")

    print("verify_registry: ALL CHECKS PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
