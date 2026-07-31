#!/usr/bin/env python3
"""build_checks.py — the §10 build checks in one runner (FR-DC-09, FR-XS-01/20, NFR-06).

"Author by hand; verify by spec." This runner is the *verify* half: it executes every
REGISTERED §10 check over the seam and exits non-zero if ANY fails, naming every offender.
It is the build's single green/red signal that the seam is internally consistent before the
spine runs on it.

Post-ADR-008 register (TASK-100 re-cut — §10 shrinks 5 → 4, D-A23 family 1):

  §10.2  overlay parity           — both overlays realize every role at the same shared skill.
                                    (delegated to checks/check_overlay_parity.py, TASK-047)
  §10.3  domain artifact presence — the seam files for UI_INPUT.domain exist (jira_template
                                    required only when L4/Jira is in run scope).
  §10.4  connector coverage       — every UI_INPUT source type has a non-domain-branching
                                    connector (code type → clone.py).
  §10.5′ disposition-class totality — registers at TASK-108 with the SI profile (every SI
                                    section routed ≥1 input class; every UI class in the
                                    matrix). Not yet registered.

Retired by ADR-008: §10.1 vocabulary containment (the vocabulary is deleted, D-A22) and
§10.5 adapter emit no-drift (`emits` is deleted, D-A19). Transitional note: §10.3 requires
`brd_profile` until TASK-108 swaps in `si_profile`.
"""
from __future__ import annotations

import ast
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Sequence

import yaml

SCRIPTS_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPTS_DIR.parent.parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from checks.check_overlay_parity import check_parity                    # §10.2

# Source types whose connector is the shared git clone (D7 / §10.4 "code type → clone.py").
CODE_SOURCE_TYPES = {"bitbucket"}


@dataclass
class CheckResult:
    name: str
    ok: bool
    violations: list[str] = field(default_factory=list)


# ──────────────────────────────────────────────────────────────────────────────
# §10.3 — domain artifact presence (§6.6.1)
# ──────────────────────────────────────────────────────────────────────────────
def check_domain_artifacts(domain: str, *, jira_in_scope: bool = False,
                           repo_root: Path = REPO_ROOT) -> CheckResult:
    pdir = repo_root / "core" / "profiles" / domain
    required = [
        # brd_profile is TRANSITIONAL — TASK-108 replaces it with si_profile.<domain>.yaml.
        pdir / f"brd_profile.{domain}.yaml",
        pdir / "adapter" / "adapter.yaml",
    ]
    if jira_in_scope:   # ONLY when L4 (Jira) is in run scope — required from TASK-122 on
        required.append(repo_root / "core" / "templates" / domain / f"jira_template.{domain}.yaml")
    missing = [str(p.relative_to(repo_root)) for p in required if not p.exists()]
    return CheckResult("§10.3 domain artifacts", not missing,
                       [f"missing seam artifact for domain {domain!r}: {m}" for m in missing])


# ──────────────────────────────────────────────────────────────────────────────
# §10.4 — connector coverage (§6.6.2, D7)
# ──────────────────────────────────────────────────────────────────────────────
def _refs_domain(node: ast.AST) -> bool:
    """True iff the expression subtree references an identifier/attribute named ``domain``."""
    for n in ast.walk(node):
        if isinstance(n, ast.Name) and n.id == "domain":
            return True
        if isinstance(n, ast.Attribute) and n.attr == "domain":
            return True
    return False


def branches_on_domain(path: Path) -> bool:
    """Static, comment-immune check: does the connector BRANCH on ``domain`` (D7 forbids it)?

    Parses the AST and inspects every conditional's test (``if`` / ternary / ``match`` /
    comprehension filter). A connector that merely mentions ``domain`` in a docstring or
    comment is fine; one that *branches* on it is a domain fork (FR-DC-11 violation).
    """
    tree = ast.parse(path.read_text())
    for node in ast.walk(tree):
        if isinstance(node, (ast.If, ast.IfExp)) and _refs_domain(node.test):
            return True
        if isinstance(node, ast.Match) and _refs_domain(node.subject):
            return True
        if isinstance(node, ast.comprehension) and any(_refs_domain(c) for c in node.ifs):
            return True
    return False


def _connector_for(source_type: str, repo_root: Path) -> Path:
    name = "clone.py" if source_type in CODE_SOURCE_TYPES else f"ingest_{source_type}.py"
    return repo_root / "core" / "scripts" / name


def check_connector_coverage(sources: Sequence[dict], *,
                             repo_root: Path = REPO_ROOT) -> CheckResult:
    violations: list[str] = []
    for s in sources:
        stype = s.get("type", "?")
        conn = _connector_for(stype, repo_root)
        if not conn.exists():
            violations.append(f"source type {stype!r}: no connector at "
                              f"{conn.relative_to(repo_root)}")
            continue
        if branches_on_domain(conn):
            violations.append(f"connector {conn.name} branches on `domain` "
                              f"(must be source-type-keyed only, D7)")
    return CheckResult("§10.4 connector coverage", not violations, violations)


# ──────────────────────────────────────────────────────────────────────────────
# Runner — all registered checks
# ──────────────────────────────────────────────────────────────────────────────
def _safe(name: str, fn) -> CheckResult:
    """Run a check, converting any exception (e.g. a missing seam file) into a clean FAIL —
    a build runner reports red, it does not crash on a broken seam."""
    try:
        return fn()
    except Exception as exc:                       # noqa: BLE001 — any failure ⇒ red, named
        return CheckResult(name, False, [f"{type(exc).__name__}: {exc}"])


def run_all(*, ui_input: str | Path | None = None, repo_root: Path = REPO_ROOT,
            jira_in_scope: bool = False) -> list[CheckResult]:
    ui_path = Path(ui_input or (repo_root / "fixtures" / "UI_INPUT.example.yaml"))
    ui = yaml.safe_load(ui_path.read_text()) or {}
    domain = ui.get("domain", "payment_brand")
    sources = ui.get("sources") or []

    def r2():   # §10.2 reuses the dedicated module; map its violations to strings.
        c = check_parity(repo_root=repo_root)
        return CheckResult("§10.2 overlay parity", c.ok, [str(v) for v in c.violations])

    return [
        _safe("§10.2 overlay parity", r2),
        _safe("§10.3 domain artifacts",
              lambda: check_domain_artifacts(domain, jira_in_scope=jira_in_scope, repo_root=repo_root)),
        _safe("§10.4 connector coverage",
              lambda: check_connector_coverage(sources, repo_root=repo_root)),
    ]


def main(argv: Sequence[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Run all registered §10 build checks")
    parser.add_argument("--ui-input", default=None, help="UI_INPUT.yaml (default: fixtures example)")
    parser.add_argument("--jira", action="store_true", help="treat L4/Jira as in scope (§10.3)")
    ns = parser.parse_args(argv)

    results = run_all(ui_input=ns.ui_input, jira_in_scope=ns.jira)
    failed = [r for r in results if not r.ok]
    for r in results:
        print(f"  [{'PASS' if r.ok else 'FAIL'}] {r.name}")
        for v in r.violations:
            print(f"         - {v}", file=sys.stderr)
    if failed:
        print(f"\nBUILD CHECKS FAILED — {len(failed)}/{len(results)} check(s) red.", file=sys.stderr)
        return 1
    print(f"\nBUILD CHECKS PASSED — all {len(results)} registered §10 checks green.")
    return 0


# ──────────────────────────────────────────────────────────────────────────────
# Demonstration (TASK-048 fixture/proof, re-cut at TASK-100 — seam green + each
# injected failure red). Run: python3 core/scripts/build_checks.py --demo
# ──────────────────────────────────────────────────────────────────────────────
def _demo() -> None:
    import shutil
    import tempfile

    results = run_all()
    print("CLEAN (real seam):")
    for r in results:
        print(f"  [{'PASS' if r.ok else 'FAIL'}] {r.name}"
              + ("" if r.ok else f"  → {r.violations}"))
    assert all(r.ok for r in results), "the real seam must pass every registered §10 check"

    # Injected-failure variants (each check goes red in isolation), against a temp repo copy.
    with tempfile.TemporaryDirectory(prefix="build-checks-") as tmp:
        root = Path(tmp) / "repo"
        shutil.copytree(REPO_ROOT, root, ignore=shutil.ignore_patterns(
            ".git", "__pycache__", "node_modules", "runs"))

        def red(label: str, mutate) -> None:
            fresh = Path(tempfile.mkdtemp(prefix="bc-variant-"))
            shutil.copytree(root, fresh / "r")
            mutate(fresh / "r")
            res = run_all(repo_root=fresh / "r")
            bad = [r.name for r in res if not r.ok]
            print(f"  injected[{label}] → red checks: {bad}")
            assert bad, f"variant {label!r} should have failed at least one check"
            shutil.rmtree(fresh)

        # §10.3 — delete a seam artifact
        red("10.3 missing profile",
            lambda r: (r / "core/profiles/payment_brand/brd_profile.payment_brand.yaml").unlink())
        # §10.4 — connector that branches on domain
        red("10.4 domain-branch connector",
            lambda r: (r / "core/scripts/ingest_file.py").write_text(
                "import sys\n\ndef run(domain):\n    if domain == 'payment_brand':\n        return 1\n    return 0\n"))

    print("\nPASS — real seam green on every registered §10 check; each injected variant goes red.")


if __name__ == "__main__":
    if "--demo" in sys.argv:
        _demo()
    else:
        raise SystemExit(main())
