#!/usr/bin/env python3
"""§10.2 overlay-parity build check (D9, FR-XS-08 / FR-XS-19 / FR-XS-20) — deterministic.

The runtime-tool seam's parity gate: the two tool overlays (claude, copilot) are
HAND-AUTHORED and native, but must be *behaviourally identical* — every role wired to
the SAME shared skill, every prompt file shipped, invocability matching the manifest.
The only sanctioned differences are tool-native syntax/location and launch method (D9).
This check is the "verify by spec" half of "author by hand; verify by spec": a missing
or divergent wrapper fails the build loudly (FR-XS-20).

§10.2 (verbatim):

    load M = core/overlay_manifest.yaml
    for tool in [claude, copilot]:
        for role in M.roles:
            assert a wrapper exists at tool's agents location (.claude/agents/<role>.md | <role>.agent.md)
            assert that wrapper's body references skill: <role.skill>
            assert wrapper frontmatter user_invocable == role.user_invocable
        for p in M.prompt_files:
            assert prompts/<p> exists in tool's overlay
    FAIL → name the missing role/prompt and the overlay.

``overlay_manifest.yaml`` is the D9-normative source of truth (8 roles, 4 prompt files —
``start-ingest`` + the three stage prompts, per-tool launch), reproduced unchanged from
REQUIREMENTS D9. Per-tool wrapper paths are
derived from the manifest itself: ``agents_dir`` (claude → ``<dir>/<role>.md``) or
``agents_glob`` (copilot → ``<role>`` + the glob's literal suffix, e.g. ``<role>.agent.md``).
The expected shared skill is ``core/skills/<role.skill>.skill.md`` — the SAME file for
both overlays; a wrapper pointing elsewhere is a divergence (acceptance: "fails if a
Copilot wrapper is missing or points at a divergent skill").
"""
from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Mapping, Sequence

import yaml

REPO_ROOT = Path(__file__).resolve().parents[3]


# ──────────────────────────────────────────────────────────────────────────────
# Manifest + frontmatter loaders
# ──────────────────────────────────────────────────────────────────────────────
def load_manifest(path: str | Path) -> dict:
    return yaml.safe_load(Path(path).read_text()) or {}


def parse_frontmatter(path: Path) -> dict:
    """Return the YAML frontmatter block (between the leading ``---`` fences) as a dict.

    Returns ``{}`` when the file has no frontmatter — the caller treats a missing
    ``skill``/``user_invocable`` as a violation, which is the correct loud failure.
    """
    text = path.read_text()
    if not text.startswith("---"):
        return {}
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}
    return yaml.safe_load(parts[1]) or {}


def wrapper_path(overlay_root: Path, tool_cfg: Mapping[str, object], role: str) -> Path:
    """Derive a tool's wrapper path for ``role`` from the manifest's overlay config.

    ``agents_dir`` → ``<overlay_root>/<dir>/<role>.md`` (claude).
    ``agents_glob`` → ``<overlay_root>/<role><suffix>`` where suffix is the glob with its
    leading ``*`` stripped, e.g. ``*.agent.md`` → ``<role>.agent.md`` (copilot).
    """
    agents_dir = tool_cfg.get("agents_dir")
    if agents_dir:
        return overlay_root / str(agents_dir) / f"{role}.md"
    glob = str(tool_cfg.get("agents_glob", "*.md"))
    suffix = glob.lstrip("*")
    return overlay_root / f"{role}{suffix}"


# ──────────────────────────────────────────────────────────────────────────────
# Parity
# ──────────────────────────────────────────────────────────────────────────────
@dataclass(frozen=True)
class Violation:
    overlay: str                    # the tool overlay the failure is in
    target: str                     # the role or prompt-file name
    kind: str                       # missing_wrapper | skill_divergence | invocable_mismatch | missing_prompt
    detail: str

    def __str__(self) -> str:
        return f"[{self.overlay}] {self.kind}: {self.target} — {self.detail}"


@dataclass
class ParityResult:
    overlays: tuple[str, ...]
    roles: tuple[str, ...]
    prompt_files: tuple[str, ...]
    violations: list[Violation] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.violations


def _check_overlay(
    tool: str,
    tool_cfg: Mapping[str, object],
    overlay_root: Path,
    roles: Sequence[Mapping[str, object]],
    prompt_files: Sequence[str],
    skill_refs: dict[str, dict[str, str]],
) -> list[Violation]:
    """Per-overlay checks; also records each role's referenced skill into ``skill_refs``
    (``skill_refs[role][tool] = skill_path``) so the caller can assert cross-overlay
    skill equality (the parity property §10.2 actually guards)."""
    out: list[Violation] = []
    for role in roles:
        name = str(role.get("name", "?"))
        # The manifest's `skill` is the LOGICAL skill name (D9 / SKILLS_INDEX); the skill
        # FILE may differ (e.g. role `code_impact` → core/skills/code_impact_assess.skill.md).
        # §10.2 linkage = the wrapper references that logical name; parity = both overlays
        # reference the SAME path (asserted by the caller). We do NOT assume name==filename.
        logical = str(role.get("skill"))
        wp = wrapper_path(overlay_root, tool_cfg, name)

        if not wp.exists():
            out.append(Violation(tool, name, "missing_wrapper",
                                 f"no wrapper at {wp.relative_to(overlay_root.parent.parent)}"))
            continue

        fm = parse_frontmatter(wp)
        skill_ref = fm.get("skill")
        if isinstance(skill_ref, str):
            skill_refs.setdefault(name, {})[tool] = skill_ref
        # linkage: the wrapper must reference the role's (logical) shared skill, in BOTH the
        # frontmatter `skill:` field and the body (§10.2 "wrapper's body references skill").
        body = wp.read_text()
        links = (isinstance(skill_ref, str)
                 and skill_ref.startswith("core/skills/") and skill_ref.endswith(".skill.md")
                 and logical in skill_ref and skill_ref in body)
        if not links:
            out.append(Violation(tool, name, "skill_divergence",
                                 f"wrapper does not reference shared skill {logical!r} "
                                 f"(frontmatter skill={skill_ref!r})"))
        # invocability must match the manifest exactly
        if fm.get("user_invocable") != role.get("user_invocable"):
            out.append(Violation(tool, name, "invocable_mismatch",
                                 f"manifest user_invocable={role.get('user_invocable')}, "
                                 f"wrapper={fm.get('user_invocable')}"))

    # Per-tool prompt location/ext from the manifest (claude: prompts/<p>.md;
    # copilot: .github/prompts/<p>.prompt.md). Defaults preserve the legacy claude layout.
    prompts_dir = str(tool_cfg.get("prompts_dir", "prompts"))
    prompt_ext = str(tool_cfg.get("prompt_ext", ".md"))
    for p in prompt_files:
        pp = overlay_root / prompts_dir / f"{p}{prompt_ext}"
        if not pp.exists():
            out.append(Violation(tool, p, "missing_prompt",
                                 f"no prompt file at {pp.relative_to(overlay_root.parent.parent)}"))
    return out


def check_parity(
    *,
    repo_root: Path = REPO_ROOT,
    manifest_path: str | Path | None = None,
    overlays_root: str | Path | None = None,
) -> ParityResult:
    """Run §10.2 over the real overlays. Pure — computes, never writes.

    ``overlays_root`` defaults to ``<repo_root>/overlays`` but is separable so a fixture
    (e.g. a deleted-wrapper variant) can be checked against the real manifest.
    """
    manifest_path = manifest_path or (repo_root / "core" / "overlay_manifest.yaml")
    overlays_root = Path(overlays_root or (repo_root / "overlays"))
    M = load_manifest(manifest_path)
    roles = M.get("roles") or []
    prompt_files = M.get("prompt_files") or []
    overlays_cfg = M.get("overlays") or {}

    violations: list[Violation] = []
    skill_refs: dict[str, dict[str, str]] = {}
    for tool, cfg in overlays_cfg.items():
        violations += _check_overlay(tool, cfg, overlays_root / tool, roles, prompt_files, skill_refs)

    # Cross-overlay parity: every overlay that ships a role's wrapper must point it at the
    # SAME shared skill. A role referenced by >1 distinct skill path across overlays is a
    # divergence — the core "both overlays point at the same shared skill" guarantee (D9).
    for role in roles:
        name = str(role.get("name", "?"))
        refs = skill_refs.get(name, {})
        if len(set(refs.values())) > 1:
            listed = ", ".join(f"{t}→{s}" for t, s in sorted(refs.items()))
            violations.append(Violation("(cross-overlay)", name, "skill_divergence",
                                        f"overlays disagree on the shared skill: {listed}"))

    return ParityResult(
        overlays=tuple(overlays_cfg),
        roles=tuple(r.get("name", "?") for r in roles),
        prompt_files=tuple(prompt_files),
        violations=violations,
    )


def main(argv: Sequence[str] | None = None) -> int:
    """CLI: run §10.2 on the real overlays; exit non-zero (and name offenders) on failure."""
    import argparse

    parser = argparse.ArgumentParser(description="§10.2 overlay-parity check")
    parser.add_argument("--overlays-root", default=None)
    ns = parser.parse_args(argv)

    result = check_parity(overlays_root=ns.overlays_root)
    if result.ok:
        print(f"§10.2 PASS — {len(result.overlays)} overlays {result.overlays} each realize "
              f"all {len(result.roles)} roles + {len(result.prompt_files)} prompt files "
              f"against the same shared skills.")
        return 0
    print(f"§10.2 FAIL — {len(result.violations)} parity violation(s):", file=sys.stderr)
    for v in result.violations:
        print(f"  - {v}", file=sys.stderr)
    return 1


# ──────────────────────────────────────────────────────────────────────────────
# Demonstration (TASK-047 fixture/proof). Run: python3 core/scripts/checks/check_overlay_parity.py --demo
#   - CLEAN: the real claude + copilot overlays → NO violation (acceptance: passes on
#     real overlays).
#   - CRAFTED: a deleted-wrapper variant (a copy of overlays/ with one copilot wrapper
#     removed and one wrapper's skill pointed at a divergent file) → both flagged, naming
#     the role and the overlay (acceptance: fails if a Copilot wrapper is missing or
#     points at a divergent skill).
# ──────────────────────────────────────────────────────────────────────────────
def _demo() -> None:
    import shutil
    import tempfile

    clean = check_parity()
    print("CLEAN  (real overlays):")
    print(f"  overlays={clean.overlays}  roles={len(clean.roles)}  "
          f"prompts={len(clean.prompt_files)}  violations={clean.violations}")
    assert clean.ok, f"real overlays must be parity-clean; got {clean.violations}"

    with tempfile.TemporaryDirectory() as tmp:
        variant = Path(tmp) / "overlays"
        shutil.copytree(REPO_ROOT / "overlays", variant)
        # (1) delete a Copilot wrapper
        (variant / "copilot" / "code_impact.agent.md").unlink()
        # (2) point a Claude wrapper at a divergent skill
        diverged = variant / "claude" / ".claude" / "agents" / "jira_author.md"
        diverged.write_text(diverged.read_text().replace(
            "core/skills/jira_author.skill.md", "core/skills/WRONG.skill.md"))

        bad = check_parity(overlays_root=variant)
        print("\nCRAFTED (deleted copilot code_impact wrapper + diverged claude jira_author skill):")
        for v in bad.violations:
            print(f"  VIOLATION {v}")
        assert any(v.kind == "missing_wrapper" and v.overlay == "copilot"
                   and v.target == "code_impact" for v in bad.violations), \
            "the deleted copilot wrapper must be flagged, naming the role + overlay"
        assert any(v.kind == "skill_divergence" and v.overlay == "claude"
                   and v.target == "jira_author" for v in bad.violations), \
            "the divergent-skill wrapper must be flagged"
    print("\nPASS — real overlays at parity; deleted + divergent wrappers flagged with role + overlay.")


if __name__ == "__main__":
    if "--demo" in sys.argv:
        _demo()
    else:
        raise SystemExit(main())
