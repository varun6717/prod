#!/usr/bin/env python3
"""build_checks.py — the §10 build checks in one runner (FR-DC-09, FR-XS-01/20, NFR-06).

"Author by hand; verify by spec." This runner is the *verify* half: it executes every
REGISTERED §10 check over the seam and exits non-zero if ANY fails, naming every offender.
It is the build's single green/red signal that the seam is internally consistent before the
spine runs on it.

Post-ADR-008 register (complete at TASK-108 — §10 is 5 → 4, D-A23 family 1):

  §10.2  overlay parity           — both overlays realize every role at the same shared skill.
                                    (delegated to checks/check_overlay_parity.py, TASK-047)
  §10.3  domain artifact presence — the seam files for UI_INPUT.domain exist (jira_template
                                    required only when L4/Jira is in run scope), AND every
                                    adapter-pack pipeline pointer resolves to a real skill file.
  §10.4  connector coverage       — every UI_INPUT source type has a non-domain-branching
                                    connector (code type → clone.py).
  §10.5′ disposition-class totality — every SI section routed ≥1 input; every class the UI
                                    offers routed by ≥1 section; conditionals marked.
                                    (delegated to checks/check_disposition_totality.py)

Retired by ADR-008: §10.1 vocabulary containment (the vocabulary is deleted, D-A22) and
§10.5 adapter emit no-drift (`emits` is deleted, D-A19).

**The pack-pointer half of §10.3** is §10.5's surviving residue, which the spec says lives on
"inside §10.4/§10.3" — it had never actually been implemented there. Found at TASK-105 and
folded in here: between TASK-100 and TASK-105 `adapter.yaml` named `article_summarize` and
`confluence_tag`, both deleted in the retirement sweep, and §10 stayed fully green. A seam
that points at nothing is invisible until a run reaches it.
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
from checks.check_disposition_totality import check_disposition_totality  # §10.5′

# Source types whose connector is the shared git clone (D7 / §10.4 "code type → clone.py").
CODE_SOURCE_TYPES = {"bitbucket"}


@dataclass
class CheckResult:
    name: str
    ok: bool
    violations: list[str] = field(default_factory=list)


# ──────────────────────────────────────────────────────────────────────────────
# §10.3 — domain artifact presence + adapter-pack pointer resolution (§6.6.1, §10.5 residue)
# ──────────────────────────────────────────────────────────────────────────────
def _pipeline_steps(pipeline) -> list[str]:
    """Skill names from a `docs_pipeline` / `code_pipeline` value, in either 063B form.

    Accepts the bare list (== the `default` lane) and the mapping keyed by source `type`.
    Returns ``[]`` for anything unrecognised — the caller reports emptiness separately, so a
    malformed pipeline is never mistaken for a legitimately empty one.
    """
    def names(lane) -> list[str]:
        return [str(s["skill"]) for s in lane if isinstance(s, dict) and s.get("skill")]

    if isinstance(pipeline, list):
        return names(pipeline)
    if isinstance(pipeline, dict):
        return [n for lane in pipeline.values() if isinstance(lane, list) for n in names(lane)]
    return []


def _skill_file(skill: str, domain: str, repo_root: Path) -> Path | None:
    """Resolve a pipeline skill name to its file — pack skill, else shared core skill.

    Both homes are legitimate: `pdf_extract` lives in the domain pack (document formats are
    where a domain actually shows up), while `code_map_build` and `doc_index` live in
    `core/skills/` and are *referenced* rather than copied, because they carry no domain
    knowledge. So the check accepts either and only fails when neither exists.
    """
    for p in (repo_root / "core" / "profiles" / domain / "adapter" / f"{skill}.skill.md",
              repo_root / "core" / "skills" / f"{skill}.skill.md"):
        if p.is_file():
            return p
    return None


def check_domain_artifacts(domain: str, *, jira_in_scope: bool = False,
                           repo_root: Path = REPO_ROOT) -> CheckResult:
    """§10.3 — the domain seam's files exist AND its pipeline pointers resolve.

    Presence: the SI profile + the adapter manifest (plus `jira_template` once L4 is in scope).
    Pointers (the §10.5 residue, folded in at TASK-108): every skill named by `docs_pipeline` /
    `code_pipeline` resolves to a real file, and a mapping-form `docs_pipeline` carries its
    required `default` lane (063B).
    """
    pdir = repo_root / "core" / "profiles" / domain
    adapter_path = pdir / "adapter" / "adapter.yaml"
    required = [pdir / f"si_profile.{domain}.yaml", adapter_path]
    if jira_in_scope:   # ONLY when L4 (Jira) is in run scope — required from TASK-122 on
        required.append(repo_root / "core" / "templates" / domain / f"jira_template.{domain}.yaml")
    violations = [f"missing seam artifact for domain {domain!r}: {p.relative_to(repo_root)}"
                  for p in required if not p.exists()]

    if adapter_path.exists():          # pointers are only checkable once the manifest is there
        try:
            adapter = yaml.safe_load(adapter_path.read_text()) or {}
        except yaml.YAMLError as exc:
            violations.append(f"adapter.yaml is not valid YAML: {exc}")
            adapter = {}
        docs = adapter.get("docs_pipeline")
        if isinstance(docs, dict) and "default" not in docs:
            violations.append(
                "docs_pipeline uses the per-type mapping form but has no `default` lane — a "
                "source type with no matching key would route nowhere (063B)")
        for field_name in ("docs_pipeline", "code_pipeline"):
            if field_name not in adapter:
                violations.append(f"adapter.yaml has no `{field_name}`")
                continue
            steps = _pipeline_steps(adapter[field_name])
            if not steps:
                violations.append(f"`{field_name}` names no skill (empty or malformed)")
            violations += [
                f"`{field_name}` points at skill {s!r}, which has no file in the pack "
                f"(profiles/{domain}/adapter/) or in core/skills/"
                for s in steps if _skill_file(s, domain, repo_root) is None]

    return CheckResult("§10.3 domain artifacts", not violations, violations)


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

    def r5():   # §10.5′ likewise — the SI profile's routing matrix, both directions.
        c = check_disposition_totality(domain, repo_root=repo_root)
        return CheckResult("§10.5′ disposition-class totality", c.ok, list(c.violations))

    return [
        _safe("§10.2 overlay parity", r2),
        _safe("§10.3 domain artifacts",
              lambda: check_domain_artifacts(domain, jira_in_scope=jira_in_scope, repo_root=repo_root)),
        _safe("§10.4 connector coverage",
              lambda: check_connector_coverage(sources, repo_root=repo_root)),
        _safe("§10.5′ disposition-class totality", r5),
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

        def red(label: str, mutate, expect: str) -> None:
            """Inject one defect; assert the NAMED check goes red (not merely some check)."""
            fresh = Path(tempfile.mkdtemp(prefix="bc-variant-"))
            shutil.copytree(root, fresh / "r")
            mutate(fresh / "r")
            res = run_all(repo_root=fresh / "r")
            bad = [r.name for r in res if not r.ok]
            print(f"  injected[{label}] → red: {bad}")
            assert any(expect in n for n in bad), \
                f"variant {label!r} should have turned {expect} red; red were {bad}"
            shutil.rmtree(fresh)

        def edit_yaml(path: str, mutate):
            """Return a mutator that loads a YAML file, mutates it, and writes it back."""
            def _do(r: Path) -> None:
                p = r / path
                doc = yaml.safe_load(p.read_text())
                mutate(doc)
                p.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
            return _do

        # §10.3 — a missing seam artifact
        red("10.3 missing si_profile",
            lambda r: (r / "core/profiles/payment_brand/si_profile.payment_brand.yaml").unlink(),
            "§10.3")
        # §10.3 — a pack pointer that resolves to nothing. This is the §10.5 residue TASK-105
        # found unimplemented: exactly the state adapter.yaml was in while it still named the
        # deleted `article_summarize`, with §10 fully green.
        red("10.3 dangling docs_pipeline pointer",
            edit_yaml("core/profiles/payment_brand/adapter/adapter.yaml",
                      lambda d: d["docs_pipeline"].__setitem__(
                          0, {"skill": "article_summarize"})),
            "§10.3")
        # §10.4 — connector that branches on domain
        red("10.4 domain-branch connector",
            lambda r: (r / "core/scripts/ingest_file.py").write_text(
                "import sys\n\ndef run(domain):\n    if domain == 'payment_brand':\n        return 1\n    return 0\n"),
            "§10.4")
        # §10.5′ — a deleted matrix cell orphans the class nothing else routes.
        red("10.5' deleted matrix cell (architecture)",
            edit_yaml("core/profiles/payment_brand/si_profile.payment_brand.yaml",
                      lambda d: [s["classes"].pop("architecture", None)
                                 for s in d["sections"] if isinstance(s.get("classes"), dict)]),
            "§10.5′")
        # §10.5′ — a section left with no routed input at all.
        red("10.5' starved section (§13)",
            edit_yaml("core/profiles/payment_brand/si_profile.payment_brand.yaml",
                      lambda d: [(s.__setitem__("classes", {}), s.__setitem__("inputs", {}))
                                 for s in d["sections"] if s["id"] == 13]),
            "§10.5′")

    print("\nPASS — real seam green on every registered §10 check; each injected variant goes red.")


if __name__ == "__main__":
    if "--demo" in sys.argv:
        _demo()
    else:
        raise SystemExit(main())
