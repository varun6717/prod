#!/usr/bin/env python3
"""verify_generate.py — TASK-031 proof: Generate the locked UI_INPUT → §2.2 scaffold + G0.

Consumes the P0-locked ``fixtures/UI_INPUT.example.yaml`` (the contract input, registry_sha
and all) and asserts the Generate scaffolder (``core/scripts/generate.py``) produces the
full §2.2 run workspace, the per-tool instruction file (§6.3), a schema-valid ``run_started``
telemetry event (§8.1), a valid ledger, and the G0 inspection checklist (D4) — and that it
**stops** at G0 without running the workflow (FR-XS-09).

Offline + deterministic. The locked fixture pins ``registry_sha: 7d2e9a1``, which is not a
git object in this repo, so the registry is staged as a **non-git** copy of ``core/`` +
``overlays/`` — exactly the external-build convenience ``hydrate.py`` documents (direct
copy, SHA recorded-but-unverified). That lets the locked fixture be consumed verbatim.

Run:  python3 fixtures/generate/verify_generate.py
"""
from __future__ import annotations

import io
import shutil
import sys
import tempfile
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_REPO_ROOT / "core" / "scripts"))

import generate  # noqa: E402
import ledger  # noqa: E402

_LOCKED_UI_INPUT = _REPO_ROOT / "fixtures" / "UI_INPUT.example.yaml"


def _stage_nongit_registry(root: Path) -> Path:
    """Copy core/ + overlays/ into a non-git dir → triggers hydrate's direct-copy path."""
    reg = root / "registry"
    shutil.copytree(_REPO_ROOT / "core", reg / "core")
    shutil.copytree(_REPO_ROOT / "overlays", reg / "overlays")
    return reg


def main() -> int:
    failures: list[str] = []

    def check(cond: bool, label: str) -> None:
        print(f"  [{'OK' if cond else 'FAIL'}] {label}")
        if not cond:
            failures.append(label)

    with tempfile.TemporaryDirectory(prefix="gen-proof-") as tmp:
        tmp_path = Path(tmp)
        registry = _stage_nongit_registry(tmp_path)
        dest = tmp_path / "work" / "SEAL-12345-routing"

        # Capture stdout (JSON descriptor) + stderr (G0 checklist) like the CLI emits them.
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            rc = generate.main([str(_LOCKED_UI_INPUT), "--registry", str(registry),
                                "--working-path", str(dest)])
        checklist = err.getvalue()

        print("Generate (locked UI_INPUT) → scaffold assertions:")
        check(rc == 0, "generate.main returned 0")

        # §2.2 workspace layout — the locked fixture selects runtime_tool: copilot.
        check((dest / "UI_INPUT.yaml").is_file(), "UI_INPUT.yaml written (immutable run identity)")
        check((dest / "UI_INPUT.yaml").read_text() == _LOCKED_UI_INPUT.read_text(),
              "UI_INPUT.yaml copied verbatim (byte-identical to the locked input)")
        check((dest / ".github" / "copilot-instructions.md").is_file(),
              "instruction file .github/copilot-instructions.md generated (runtime_tool=copilot, §6.3)")
        check(not (dest / "CLAUDE.md").exists(), "no CLAUDE.md (the unselected tool's file is absent)")
        check(not (dest / "overlays").exists(), "overlays/ lifted to run root and removed (§2.2)")

        agents = sorted(p.name for p in dest.glob("*.agent.md"))
        check(len(agents) == 8, f"8 copilot agent wrappers at run root (got {len(agents)})")

        # copilot prompts land at .github/prompts/<p>.prompt.md (GitHub Copilot's discovered layout)
        prompts = sorted(p.name[:-len(".prompt.md")] for p in (dest / ".github" / "prompts").glob("*.prompt.md"))
        check(prompts == ["start-enrich", "start-ingest", "start-jira", "start-si"],
              f".github/prompts/ has the ADR-008 stage set — start-ingest + "
              f"start-si/enrich/jira (got {prompts})")

        check((dest / "core" / "overlay_manifest.yaml").is_file(), "core/ hydrated")
        # domain seam pruned — only payment_brand profiles/templates hydrated.
        other_domains = [p for p in (dest / "core").rglob("*")
                         if p.is_file() and len(p.relative_to(dest / "core").parts) >= 2
                         and p.relative_to(dest / "core").parts[0] in ("profiles", "templates")
                         and p.relative_to(dest / "core").parts[1] != "payment_brand"]
        check(not other_domains, "domain seam pruned (no non-payment_brand profiles/templates)")

        # Empty, ready-for-ingest dirs — Generate stops before the run fills them (FR-XS-09).
        check((dest / "context_set").is_dir() and not any((dest / "context_set").iterdir()),
              "context_set/ present and empty (ready for ingest)")
        check((dest / "repo").is_dir() and not any((dest / "repo").iterdir()),
              "repo/ present and empty (clone happens at run)")
        check((dest / "solution_intent").is_dir()
              and not any((dest / "solution_intent").iterdir()),
              "solution_intent/ present and empty (v1/v2/enrichment.json land at run — ADR-008)")
        # Incremental run artifacts must NOT exist yet — they are run output, not Generate's.
        check(not any((dest / n).exists() for n in ("BRD.md", "FRD.md", "jira_plan.json")),
              "no BRD.md/FRD.md/jira_plan.json (incremental run artifacts, not laid at Generate)")

        # Ledger valid + run_started recorded and schema-valid (§8.1).
        report = ledger.validate_ledger(dest / "ledger")
        check(all(not e for e in report.values()), f"ledger validates clean: {report}")

        tel_lines = (dest / "ledger" / "telemetry.jsonl").read_text().splitlines()
        check(len(tel_lines) == 1, f"exactly one telemetry event written (got {len(tel_lines)})")
        import json
        event = json.loads(tel_lines[0]) if tel_lines else {}
        check(event.get("event") == "run_started", "the event is run_started")
        check(event.get("path") == str(dest) and event.get("registry_sha") == "7d2e9a1",
              "run_started carries path + the locked registry_sha (§8.1 payload)")
        check(not ledger.validate_record(event, ledger.load_schema("telemetry")),
              "run_started event is telemetry-schema-valid")

        rs = json.loads((dest / "ledger" / "run_state.json").read_text())
        check(rs["current_stage"] == "ingest"
              and all(s["status"] == "pending" for s in rs["stages"].values()),
              "run_state @ ingest with all stages pending (nothing has run — G0)")

        # G0 checkpoint surfaced; Generate did not run the workflow.
        desc = json.loads(out.getvalue())
        check(desc.get("checkpoint") == "G0" and desc.get("ran_workflow") is False,
              "descriptor marks G0 checkpoint, ran_workflow=False (two steps, FR-XS-09)")
        check("G0 — scaffold inspection checkpoint" in checklist
              and "PROCEED TO RUN" in checklist,
              "G0 inspection checklist printed for the operator (D4)")

        # ── A domain with NO pack must fail AT GENERATE, not at authoring ────────────
        # The wrong-but-plausible implementation this kills: trusting hydration's success.
        # Pruning profiles/ + templates/ to a domain that has neither still copies the rest
        # of core/, so hydrate returns a non-empty `copied` and the scaffold passes every
        # structural assertion above. Without this check the operator inspects a complete-
        # looking G0 scaffold and only learns the truth when the SI author cannot find its
        # profile — by which point they have been told the run is ready.
        print("\nunknown domain → refused at Generate:")
        import yaml as _yaml
        bad_cfg = _yaml.safe_load(_LOCKED_UI_INPUT.read_text(encoding="utf-8"))
        bad_cfg["domain"] = "no_such_domain"
        bad_input = tmp_path / "bad_UI_INPUT.yaml"
        bad_input.write_text(_yaml.safe_dump(bad_cfg, sort_keys=False), encoding="utf-8")
        bad_dest = tmp_path / "work" / "SEAL-99999-baddomain"

        try:
            with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                generate.generate(bad_input, registry=str(registry), working_path=bad_dest)
            raised = ""
        except ValueError as exc:
            raised = str(exc)
        check(bool(raised), "generate() refuses a domain with no seam artifacts")
        check("no_such_domain" in raised and "si_profile.no_such_domain.yaml" in raised,
              "the refusal names the domain AND the missing artifact, not just 'failed'")
        check("payment_brand" in raised,
              "and names the domains the registry DOES publish (an operator typo is one glance)")
        # It must fail at the SEAM check, not incidentally later — core/ did hydrate fine.
        check((bad_dest / "core" / "overlay_manifest.yaml").is_file(),
              "core/ hydrated before the refusal — proving the check is what caught it, "
              "not a hydration failure")
        check(not (bad_dest / "ledger").exists(),
              "no ledger and no run_started for a refused run (nothing is recorded as started)")

    print()
    if failures:
        print(f"FAIL — {len(failures)} assertion(s) failed: {failures}")
        return 1
    print("PASS — locked UI_INPUT → §2.2 scaffold + instruction file + valid ledger + "
          "run_started + G0 checklist; workflow not run (FR-XS-03, FR-XS-09, D4/G0).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
