#!/usr/bin/env python3
"""generate.py — slice-1 Generate scaffolder + G0 checkpoint (§2.2, §6.3, Appendix B).

This is the central **Generate** step: from one P0-locked ``UI_INPUT.yaml`` it lays a
complete run workspace (§2.2), generates the per-tool instruction file (§6.3), hydrates
the SHA-pinned registry slice (Appendix B), initializes the ledger, records a
``run_started`` telemetry event — and then **STOPS**. It never runs the workflow.

**Two steps, not one (FR-XS-09).** Generate-scaffold and run-workflow are deliberately
separate so the laid scaffold + the immutable ``UI_INPUT.yaml`` can be inspected at the
**G0 checkpoint** (D4) before any stage executes. This script is the *Generate* half; the
operator inspects (G0), then a *separate* invocation runs the spine. Generate stopping at
G0 — printing the inspection checklist and returning without touching ``context_set/`` or
``repo/`` content — is the whole contract here.

**Plumbing, not judgment (FR-XS-03, NFR-07).** Everything here is filesystem / subprocess /
hydration / template-fill / ledger-seed. No authoring call is made; nothing branches on
domain *semantics* (``domain`` and ``runtime_tool`` only *select which already-authored
paths to hydrate*, exactly as in ``hydrate.py``). The work is composed from the existing
deterministic units:

  - ``hydrate.hydrate``                 → core/ (domain-pruned) + overlays/<tool>/  (Appendix B)
  - ``generate_instruction.render_instruction_file`` → CLAUDE.md | copilot-instructions.md (§6.3)
  - ``ledger.init_ledger``              → telemetry.jsonl + run_state.json + decisions.jsonl (§2.2, §3.4–3.6)

The resulting workspace is the §2.2 layout::

    <working_path>/
      UI_INPUT.yaml                      # immutable run config — the run's identity
      CLAUDE.md | copilot-instructions.md
      .claude/agents/ | *.agent.md       # hydrated overlay wrappers, lifted to run root
      prompts/                           # start-ingest, start-si, start-enrich, start-jira
      core/                              # hydrated shared core (domain-pruned seams)
      repo/                              # empty — code clone happens at run (clone.py)
      context_set/                       # empty — ingestion fills it at run
      solution_intent/                   # empty — v1.md/v2.md/enrichment.json land at run
      ledger/                            # telemetry.jsonl, run_state.json, decisions.jsonl

``solution_intent/`` contents and ``jira_plan.json`` / ``jira_trace.json`` are *incremental
run artifacts* (§3.7/§3.8) — the run stages create them, not Generate, so the directory is
present but empty at G0.

**Reproducibility (NFR-01, FR-XS-10).** The scaffold is a pure function of
``UI_INPUT.yaml`` + the pinned ``registry_sha``. ``registry_sha`` pins the core/profiles;
the repo is pinned later by ``commit_sha`` at clone time. No secret ever enters the
workspace — sources carry ``auth_ref`` pointers only.

**External build (this repo IS the registry).** ``--registry`` defaults to the repo root.
Two external-build conveniences mirror the sibling connectors: ``--working-path`` overrides
``UI_INPUT.working_path`` (the locked fixture points at an absolute VDI path), and pointing
``--registry`` at a non-git tree makes ``hydrate.py`` copy it directly (``registry_sha``
recorded but unverified) — which lets the locked fixture's pinned SHA be consumed verbatim
here without a matching git object. The mechanism is what ports to the VDI; only the source
location and the (real) secret store differ.
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

# Sibling deterministic units live in this same dir; running as a script puts it on sys.path.
import hydrate
import ledger
import telemetry
from generate_instruction import render_instruction_file

# Overlay files that are authoring-time/port-time docs, NOT runtime workspace artifacts:
# the launch gesture is already baked into the generated instruction file's per-tool tail
# (§6.3), and VDI_PREREQUISITES.md is a port note. Everything else under overlays/<tool>/
# already sits at its §2.2 run-root-relative path (.claude/agents/…, *.agent.md, prompts/…),
# so lifting the overlay to the run root is a straight copy minus these names.
_OVERLAY_SKIP_NAMES = {"launch.md", "VDI_PREREQUISITES.md", ".gitkeep", "__pycache__"}

# Empty workspace dirs Generate creates so the §2.2 skeleton is complete at G0; the run
# stages fill them (clone.py → repo/, ingestion → context_set/, the SI author →
# solution_intent/). Present-but-empty makes the "ready for ingest" state inspectable
# rather than implicit.
_EMPTY_RUN_DIRS = ("context_set", "repo", "solution_intent")


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _load_yaml(path: Path) -> dict:
    import yaml  # local import: only callers reading YAML need it

    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _place_overlay(dest: Path, runtime_tool: str) -> list[str]:
    """Lift the hydrated ``overlays/<tool>/`` content up to the run root (§2.2).

    ``hydrate.py`` drops the overlay under ``dest/overlays/<tool>/`` (its packaging path);
    the runtime tool discovers agents at ``.claude/agents/`` | ``*.agent.md`` and prompts at
    ``prompts/`` *relative to the working dir*. Those overlay-internal paths already match
    the §2.2 run-root positions, so this is a straight recursive copy minus the
    authoring/port-only files in ``_OVERLAY_SKIP_NAMES``. The now-redundant ``overlays/``
    tree is then removed — §2.2 lists no ``overlays/`` dir in the workspace.

    Tool-agnostic by construction: the only per-tool difference (claude nests wrappers under
    ``.claude/agents/``, copilot puts ``*.agent.md`` at the overlay root) is already encoded
    in the overlay's own layout, so no branching on ``runtime_tool`` is needed here.
    """
    overlay_root = dest / "overlays" / runtime_tool
    if not overlay_root.is_dir():
        raise FileNotFoundError(f"hydrated overlay missing: {overlay_root}")

    placed: list[str] = []
    for path in sorted(overlay_root.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(overlay_root)
        if any(part in _OVERLAY_SKIP_NAMES for part in rel.parts):
            continue
        target = dest / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, target)
        placed.append(str(rel))

    shutil.rmtree(dest / "overlays", ignore_errors=True)
    placed.sort()
    return placed


def _g0_checklist(descriptor: dict) -> str:
    """The G0 scaffold-inspection checklist (D4). Generate has stopped BEFORE run (FR-XS-09);
    the operator inspects this, then either proceeds to Run (a separate step) or regenerates."""
    d = descriptor
    return "\n".join(
        [
            "─" * 72,
            "G0 — scaffold inspection checkpoint (D4). Generate STOPPED before run (FR-XS-09).",
            f"  run_id={d['run_id']}  domain={d['domain']}  runtime_tool={d['runtime_tool']}",
            f"  working_path={d['working_path']}",
            "Inspect, then either PROCEED TO RUN (separate step) or REGENERATE after editing config:",
            f"  [ ] working_path laid at {d['working_path']}",
            "  [ ] UI_INPUT.yaml present — the run's identity, immutable (run_id, domain,",
            "      runtime_tool, registry_sha, sources, gates)",
            f"  [ ] instruction file {d['instruction_file']} generated for runtime_tool={d['runtime_tool']}",
            f"  [ ] overlay wrappers placed ({d['agents_count']} roles) + prompts/ "
            f"({', '.join(d['prompt_files'])})",
            f"  [ ] core/ hydrated @ registry_sha={d['registry_sha']}"
            f"{'' if d['registry_sha_verified'] else ' (UNVERIFIED — non-git registry, external build)'}"
            f" — domain {d['domain']} profiles/templates only",
            "  [ ] ledger/ initialized — telemetry.jsonl, run_state.json @ ingest/pending, decisions.jsonl",
            "  [ ] context_set/ and repo/ empty — ready for ingest (clone + ingestion run later)",
            "  [ ] run_started event recorded in ledger/telemetry.jsonl",
            "Decide: proceed to Run, or regenerate. Generate makes NO authoring judgment (FR-XS-03).",
            "─" * 72,
        ]
    )


def generate(
    ui_input_path: str | Path,
    *,
    registry: str | Path | None = None,
    working_path: str | Path | None = None,
    force: bool = False,
    ts: str | None = None,
) -> dict:
    """Lay the §2.2 run workspace from ``ui_input_path`` and stop at G0.

    Deterministic plumbing only (FR-XS-03): hydrate → place overlay → render instruction
    file → init ledger → emit ``run_started``. Returns a descriptor of the scaffold; the
    caller surfaces the G0 checklist. Does **not** run the workflow (FR-XS-09).
    """
    ui_input_path = Path(ui_input_path)
    ui = _load_yaml(ui_input_path)

    required = ("run_id", "domain", "runtime_tool", "registry_sha")
    missing = [k for k in required if not ui.get(k)]
    if missing:
        raise ValueError(f"UI_INPUT.yaml missing required field(s): {', '.join(missing)} (§3.1)")

    run_id = str(ui["run_id"])
    domain = str(ui["domain"])
    runtime_tool = str(ui["runtime_tool"])
    registry_sha = str(ui["registry_sha"])

    # working_path: the locked fixture points at an absolute VDI path; --working-path is the
    # external-build override (the embedded UI_INPUT stays verbatim — it is the run identity).
    dest = Path(working_path) if working_path else Path(ui.get("working_path", ""))
    if not str(dest):
        raise ValueError("no working_path: set it in UI_INPUT.yaml or pass working_path=")

    # Registry source precedence: explicit param (env / external-build override) > UI_INPUT's
    # registry_url (the operator-entered Bitbucket repo) > repo root (external build). A URL is
    # kept as a raw string — hydrate detects remote-vs-local; Path() would collapse '//'.
    registry = registry or ui.get("registry_url") or hydrate._REPO_ROOT
    registry_ref = ui.get("registry_ref") or None   # optional branch/tag for the registry repo

    # Live registry → pin the branch tip at Generate (TASK-053): the operator supplies repo +
    # branch and registry_sha is resolved via ls-remote, never hand-entered. A local / external-
    # build registry keeps the UI_INPUT pin (the placeholder the UI emits).
    registry_str = str(registry)
    if "://" in registry_str or registry_str.startswith("git@"):
        registry_sha = hydrate.resolve_remote_sha(registry_str, registry_ref)

    dest.mkdir(parents=True, exist_ok=True)

    # 1) Hydrate the SHA-pinned registry slice → core/ (domain-pruned) + overlays/<tool>/.
    hydrate_desc = hydrate.hydrate(
        registry, registry_sha, domain, runtime_tool, dest, ref=registry_ref, force=force
    )

    # 2) Lift the overlay wrappers + prompts to the run root (§2.2), drop the overlays/ tree.
    placed = _place_overlay(dest, runtime_tool)
    agents_count = sum(1 for p in placed if p.endswith(".agent.md") or p.startswith(".claude/agents/"))
    prompt_files = sorted(Path(p).stem for p in placed if p.startswith("prompts/"))

    # 3) Write UI_INPUT.yaml into the workspace verbatim — immutable run identity (FR-XS-16).
    shutil.copy2(ui_input_path, dest / "UI_INPUT.yaml")

    # 4) Generate the per-tool instruction file from the *hydrated* (pinned) template + manifest,
    #    so the instruction file is itself a function of the pinned core (§6.3, NFR-02).
    template = (dest / "core" / "instruction_file.template.md").read_text(encoding="utf-8")
    manifest = _load_yaml(dest / "core" / "overlay_manifest.yaml")
    instruction_file, content = render_instruction_file(ui, manifest, template)
    instr_out = dest / instruction_file
    instr_out.parent.mkdir(parents=True, exist_ok=True)   # copilot writes under .github/
    instr_out.write_text(content, encoding="utf-8")

    # 5) Initialize the ledger (telemetry.jsonl, run_state.json @ ingest/pending, decisions.jsonl).
    ledger.init_ledger(dest / "ledger", run_id=run_id)

    # 6) Empty workspace dirs so the §2.2 skeleton is complete + inspectable at G0.
    for name in _EMPTY_RUN_DIRS:
        (dest / name).mkdir(parents=True, exist_ok=True)

    # 7) Record the run_started telemetry event (the only state Generate writes to the stream).
    #    Via telemetry.emit (TASK-032) — validated against §8.1 before it lands.
    event = telemetry.emit(
        dest / "ledger", "run_started",
        run_id=run_id, domain=domain, tool=runtime_tool,
        path=str(dest), registry_sha=registry_sha, ts=ts or _now_iso(),
    )

    descriptor = {
        "run_id": run_id,
        "domain": domain,
        "runtime_tool": runtime_tool,
        "working_path": str(dest),
        "registry": str(registry),
        "registry_sha": registry_sha,
        "registry_sha_verified": hydrate_desc.get("registry_sha_verified"),
        "instruction_file": instruction_file,
        "core_file_count": hydrate_desc["file_count"],
        "overlay_files_placed": placed,
        "agents_count": agents_count,
        "prompt_files": prompt_files,
        "run_started": event,
        "checkpoint": "G0",          # Generate stops here; run is a separate step (FR-XS-09)
        "ran_workflow": False,
    }
    if hydrate_desc.get("note"):
        descriptor["hydrate_note"] = hydrate_desc["note"]
    return descriptor


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description="Generate-scaffold a run workspace from UI_INPUT.yaml and stop at G0 (§2.2, FR-XS-09).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument("ui_input", help="path to the P0-locked UI_INPUT.yaml")
    ap.add_argument("--registry", help=f"registry path or URL (default: this repo root, {hydrate._REPO_ROOT})")
    ap.add_argument("--working-path", help="scaffold destination (overrides UI_INPUT.working_path; external build)")
    ap.add_argument("--force", action="store_true", help="overwrite an already-hydrated working_path/core")
    args = ap.parse_args(argv)

    try:
        descriptor = generate(
            args.ui_input,
            registry=args.registry,
            working_path=args.working_path,
            force=args.force,
        )
    except (ValueError, FileExistsError, FileNotFoundError, RuntimeError, OSError, KeyError) as exc:
        print(f"generate.py: {exc}", file=sys.stderr)
        return 1

    print(json.dumps(descriptor, ensure_ascii=False, indent=2))
    print("\n" + _g0_checklist(descriptor), file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
