#!/usr/bin/env python3
"""generate_instruction.py — fill the one canonical instruction template (§6.3, FR-XS-07, D9).

One canonical `core/instruction_file.template.md` → **exactly one** of
`CLAUDE.md` | `copilot-instructions.md`, keyed by `UI_INPUT.runtime_tool`. There is **no
runtime `AGENTS.md` pointer** (FR-XS-07). This is the *generation logic* TASK-026 owns;
the TASK-031 scaffolder (`generate.py`) imports `render_instruction_file` and writes the
result into the run scaffold.

It is **plumbing, not judgment** (NFR-07): it substitutes placeholders and selects a
per-tool tail. It makes no authoring call. Placeholders come from `UI_INPUT.yaml` +
`core/overlay_manifest.yaml` exactly as §6.3 pins them::

    {{domain}} {{runtime_tool}} {{registry_sha}} {{run_id}}
    {{roles}}            ← overlay_manifest.roles (name → skill, user_invocable)
    {{prompt_files}}     ← overlay_manifest.prompt_files
    {{stage_transition}} ← overlays[tool].launch + gesture
                            claude → "/clear or new session"   copilot → "Ctrl+N + /start-<stage>"
    {{start_gesture}}    ← exact per-tool start gesture surfaced at hand-off (FR-XS-22)

**Portability invariant (NFR-02).** The template body is single-source; the only per-tool
variation is the runtime-tool tail (start gesture / stage transition / the `runtime_tool`
label). Generating for `claude` vs `copilot` from the *same* `UI_INPUT` therefore yields
files that differ **only** in that tail — verified by `--check-parity` (the §10.2 / TASK-026
fixture proof) and re-asserted by the overlay-parity build check (TASK-047).
"""
from __future__ import annotations

import argparse
import difflib
import sys
from pathlib import Path

# Repo-root-relative defaults (this repo IS the registry — see hydrate.py).
_THIS = Path(__file__).resolve()
_CORE = _THIS.parent.parent                       # core/
_TEMPLATE = _CORE / "instruction_file.template.md"
_MANIFEST = _CORE / "overlay_manifest.yaml"

# Per-tool tail (§6.3). Keyed by runtime_tool; the value of overlays[tool].launch from the
# manifest is the only thing that selects between them, so we assert it matches.
_TAIL = {
    "claude": {
        "instruction_file": "CLAUDE.md",
        "launch": "terminal_interactive",
        "start_gesture": (
            "open a Claude Code **terminal session** at the run working path and invoke "
            "`/start-ingest` (the Layer-1 kickoff prompt — it fires the data-&-context fan-out; "
            "it then surfaces `/start-si` for the Solution Intent stage)."
        ),
        "stage_transition": (
            "at the close of each stage, surface the advance gesture — **`/clear` or a new "
            "session**, then invoke the next stage prompt (e.g. `/start-si` → `/start-enrich` → `/start-jira`). The operator performs "
            "it; you never self-issue it."
        ),
    },
    "copilot": {
        # GitHub Copilot only auto-loads repo instructions from .github/copilot-instructions.md
        # (root is ignored) — empirically confirmed on the VDI. The .github/ prefix is the
        # relative write path under the run root; generate.py mkdirs the parent.
        "instruction_file": ".github/copilot-instructions.md",
        "launch": "agent_mode",
        "start_gesture": (
            "open VS Code **Copilot agent mode** at the run working path and run the "
            "`start-ingest` prompt file (the Layer-1 kickoff — it fires the data-&-context "
            "fan-out, then surfaces `start-si` for the Solution Intent stage)."
        ),
        "stage_transition": (
            "at the close of each stage, surface the advance gesture — **`Ctrl+N`** for a fresh "
            "agent, then run the next stage prompt file (e.g. `start-si` → `start-enrich` → `start-jira`). The operator performs it; "
            "you never self-issue it."
        ),
    },
}


def _load_yaml(path: Path) -> dict:
    import yaml  # local import: only callers passing a path need YAML
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _render_roles(roles: list[dict]) -> str:
    """overlay_manifest.roles → a markdown table (name → skill, operator-invocable?)."""
    lines = [
        "| Role | Skill (`core/skills/`) | Operator-invocable |",
        "|------|------------------------|--------------------|",
    ]
    for r in roles:
        invocable = "yes — interactive session" if r.get("user_invocable") else "no — subagent"
        lines.append(f"| `{r['name']}` | `{r['skill']}` | {invocable} |")
    return "\n".join(lines)


def _render_prompt_files(prompt_files: list[str]) -> str:
    """overlay_manifest.prompt_files → a bullet list; mark the deferred (jira) stage."""
    lines = []
    for p in prompt_files:
        note = " *(deferred this slice — do not invoke)*" if "jira" in p else ""
        lines.append(f"- `{p}`{note}")
    return "\n".join(lines)


def render_instruction_file(ui_input: dict, manifest: dict, template: str) -> tuple[str, str]:
    """Pure function: (UI_INPUT, overlay_manifest, template text) → (filename, content).

    Returns the per-tool output filename (`CLAUDE.md` | `copilot-instructions.md`) and the
    filled instruction-file text. Raises ValueError on an unknown / missing `runtime_tool`
    or a launch-method mismatch between the manifest and the pinned tail.
    """
    tool = ui_input.get("runtime_tool")
    if tool not in _TAIL:
        raise ValueError(
            f"runtime_tool must be one of {sorted(_TAIL)} (FR-XS-06); got {tool!r}"
        )
    tail = _TAIL[tool]

    # Cross-check the launch method against the manifest — the per-tool tail is keyed off it,
    # so a drift between this script and overlay_manifest.yaml is a defect, not a silent pick.
    manifest_launch = (manifest.get("overlays", {}).get(tool, {}) or {}).get("launch")
    if manifest_launch is not None and manifest_launch != tail["launch"]:
        raise ValueError(
            f"overlay_manifest.overlays.{tool}.launch={manifest_launch!r} disagrees with the "
            f"pinned tail launch={tail['launch']!r} — reconcile §6.3 / overlay_manifest first"
        )

    subs = {
        "domain": str(ui_input["domain"]),
        "runtime_tool": tool,
        "registry_sha": str(ui_input["registry_sha"]),
        "run_id": str(ui_input["run_id"]),
        "roles": _render_roles(manifest["roles"]),
        "prompt_files": _render_prompt_files(manifest["prompt_files"]),
        "stage_transition": tail["stage_transition"],
        "start_gesture": tail["start_gesture"],
    }

    content = template
    for key, value in subs.items():
        content = content.replace("{{" + key + "}}", value)

    leftover = [tok for tok in ("{{", "}}") if tok in content]
    if leftover:
        # Any unfilled placeholder is a template/logic drift — fail loud, never emit a hole.
        raise ValueError(f"unfilled placeholder(s) remain in rendered instruction file: {content!r}")

    return tail["instruction_file"], content


def _check_parity(ui_input: dict, manifest: dict, template: str) -> int:
    """Fixture proof (TASK-026 acceptance): render both tools from one UI_INPUT; the diff
    must be the runtime-tool tail only. Body lines above the tail marker must be identical."""
    rendered = {}
    for tool in ("claude", "copilot"):
        ui = dict(ui_input, runtime_tool=tool)
        _, rendered[tool] = render_instruction_file(ui, manifest, template)

    marker = "## Runtime-tool tail"
    c_lines = rendered["claude"].splitlines()
    p_lines = rendered["copilot"].splitlines()
    c_body = c_lines[: next(i for i, l in enumerate(c_lines) if l.startswith(marker))]
    p_body = p_lines[: next(i for i, l in enumerate(p_lines) if l.startswith(marker))]

    if c_body != p_body:
        diff = "\n".join(difflib.unified_diff(c_body, p_body, "claude", "copilot", lineterm=""))
        print("PARITY FAIL — body differs above the runtime-tool tail:\n" + diff, file=sys.stderr)
        return 1

    if "AGENTS.md" in rendered["claude"] or "AGENTS.md" in rendered["copilot"]:
        print("PARITY FAIL — runtime AGENTS.md pointer present (FR-XS-07 forbids it)", file=sys.stderr)
        return 1

    print(
        "PARITY OK — body identical across claude/copilot; diff is the runtime-tool tail only "
        "(NFR-02); no AGENTS.md pointer (FR-XS-07).",
        file=sys.stderr,
    )
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("ui_input", help="path to UI_INPUT.yaml")
    ap.add_argument("--manifest", default=str(_MANIFEST), help=f"overlay_manifest.yaml (default: {_MANIFEST})")
    ap.add_argument("--template", default=str(_TEMPLATE), help=f"instruction_file.template.md (default: {_TEMPLATE})")
    ap.add_argument("-o", "--out", help="write the instruction file here (default: ./<filename>; '-' for stdout)")
    ap.add_argument(
        "--check-parity", action="store_true",
        help="render both tools from this UI_INPUT and assert the diff is the tail only (fixture proof)",
    )
    args = ap.parse_args(argv)

    try:
        ui_input = _load_yaml(Path(args.ui_input))
        manifest = _load_yaml(Path(args.manifest))
        template = Path(args.template).read_text(encoding="utf-8")

        if args.check_parity:
            return _check_parity(ui_input, manifest, template)

        filename, content = render_instruction_file(ui_input, manifest, template)
    except (ValueError, OSError, KeyError) as exc:
        print(f"generate_instruction.py: {exc}", file=sys.stderr)
        return 1

    out = args.out or filename
    if out == "-":
        sys.stdout.write(content)
    else:
        Path(out).write_text(content, encoding="utf-8")
        print(f"generate_instruction.py: wrote {out} (runtime_tool={ui_input['runtime_tool']})", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
