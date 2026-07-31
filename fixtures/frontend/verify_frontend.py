#!/usr/bin/env python3
"""verify_frontend.py — TASK-051 proof: the Run Configurator emits a §3.1 UI_INPUT that Generates.

A "click-through" (``fixtures/frontend/sample_form.json`` — the form-state a non-technical
operator produces by filling the 5 tabs) is run through the **real** frontend emit code
(``app/frontend/src/emit.js`` via the ``emit_cli.mjs`` bridge), then asserted to:

  * conform to TECH_SPEC §3.1 (the backend's own validator returns no errors);
  * map fields per the contract — frame.title seeded from project_name, auth_ref injected per
    source, run_id omitted (assigned by Generate), schema_version 1, score_threshold an int;
  * include only the **5A-live** connectors (SharePoint + Bitbucket) — Confluence + Lucid are
    shown in the UI but **deferred (5B)** and never emitted;
  * match the locked example contract on every operator-entered value;
  * **drive Generate to G0** through the TASK-050 backend → a real §2.2 scaffold +
    ``UI_INPUT.yaml``, ``ran_workflow: False`` (the UI never runs the agent, FR-XS-09).

Offline + deterministic: Node runs the emit locally; the backend runs in-process via
``TestClient`` against a staged non-git registry (hydrate's external-build direct-copy path),
exactly like the TASK-050 proof.

Run:  .venv/bin/python fixtures/frontend/verify_frontend.py   (requires Node on PATH)
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_REPO_ROOT / "core" / "scripts"))
sys.path.insert(0, str(_REPO_ROOT))

import yaml  # noqa: E402

from app.backend import validation  # noqa: E402

_SAMPLE_FORM = _REPO_ROOT / "fixtures" / "frontend" / "sample_form.json"
_EMIT_CLI = _REPO_ROOT / "app" / "frontend" / "scripts" / "emit_cli.mjs"
_LOCKED_UI_INPUT = _REPO_ROOT / "fixtures" / "UI_INPUT.example.yaml"
_FIXED_TS = "2026-06-22T12:00:00Z"


def _stage_nongit_registry(root: Path) -> Path:
    reg = root / "registry"
    shutil.copytree(_REPO_ROOT / "core", reg / "core")
    shutil.copytree(_REPO_ROOT / "overlays", reg / "overlays")
    return reg


def _emit_config() -> dict:
    """Run the real frontend emit (src/emit.js) on the sample form → the POST config object."""
    proc = subprocess.run(
        ["node", str(_EMIT_CLI), str(_SAMPLE_FORM)],
        capture_output=True, text=True, cwd=str(_REPO_ROOT),
    )
    if proc.returncode != 0:
        raise RuntimeError(f"emit_cli.mjs failed: {proc.stderr.strip()}")
    return json.loads(proc.stdout)


def main() -> int:
    failures: list[str] = []

    def check(cond: bool, label: str) -> None:
        print(f"  [{'OK' if cond else 'FAIL'}] {label}")
        if not cond:
            failures.append(label)

    config = _emit_config()
    example = yaml.safe_load(_LOCKED_UI_INPUT.read_text(encoding="utf-8"))

    print("emit.js (sample click-through) → §3.1 config assertions:")
    check(validation.validate_ui_input(config) == [],
          f"emitted config is §3.1-valid (errors: {validation.validate_ui_input(config)})")
    check("run_id" not in config, "run_id omitted — assigned by Generate (§3.1)")
    check(config.get("schema_version") == 1, "schema_version == 1")
    check(config.get("registry_sha") == example["registry_sha"],
          f"registry_sha defaulted to the locked pin ({example['registry_sha']})")
    check(config.get("frame", {}).get("title") == config["project_metadata"]["project_name"],
          "frame.title seeded from project_name (§3.1)")
    check(isinstance(config.get("gates", {}).get("score_threshold"), int)
          and config["gates"]["score_threshold"] == 85,
          "gates.score_threshold coerced to int 85")
    check("jira" not in config, "jira omitted — deferred this slice")

    print("\nSources: SharePoint + Bitbucket + Confluence (5B); Lucid still deferred:")
    types = [s["type"] for s in config.get("sources", [])]
    check(types == ["sharepoint", "bitbucket", "confluence"],
          f"sources = sharepoint + bitbucket + confluence (got {types})")
    cf = next((s for s in config["sources"] if s["type"] == "confluence"), None)
    check(cf is not None and cf.get("auth_ref") == "jpmc_adapters:confluence" and cf.get("url"),
          "Confluence emitted with url + auth_ref pointer (TASK-063B)")
    check("lucid" not in types, "Lucid NOT emitted (shown in UI but still deferred)")
    sp = next(s for s in config["sources"] if s["type"] == "sharepoint")
    bb = next(s for s in config["sources"] if s["type"] == "bitbucket")
    check(sp.get("auth_ref") == "jpmc_adapters:sharepoint"
          and bb.get("auth_ref") == "jpmc_adapters:bitbucket",
          "auth_ref injected per source type (pointer only — no secret)")
    check(bb.get("repo_url") and bb.get("seal_id") == "SEAL-12345",
          "bitbucket source carries repo_url + seal_id")

    print("\nDispositions — D-A12: operator-declared per doc source, auto-set for code:")
    check(all(isinstance(s.get("disposition"), list) and s["disposition"]
              for s in config["sources"]),
          "every source carries a non-empty disposition LIST (one-or-more, default one)")
    check(sp["disposition"] == ["technical_specification"],
          "SharePoint carries the OPERATOR'S pick, not the default "
          f"(form said technical_specification, got {sp['disposition']})")
    check(cf["disposition"] == ["product_domain_knowledge"],
          "Confluence falls back to its type DEFAULT when the operator leaves it alone "
          f"(got {cf['disposition']})")
    check(bb["disposition"] == ["codebase"],
          f"Bitbucket is auto-set [codebase] — never operator-chosen (got {bb['disposition']})")
    check("codebase" not in sp["disposition"] + cf["disposition"],
          "no doc source can claim `codebase` (it is what routes the code arm)")

    print("\nMatches the locked example contract on operator-entered values:")
    check(config["project_metadata"] == example["project_metadata"], "project_metadata matches")
    check(config["domain"] == example["domain"]
          and config["runtime_tool"] == example["runtime_tool"]
          and config["working_path"] == example["working_path"],
          "domain + runtime_tool + working_path match")
    check(config["frame"]["intent"] == example["frame"]["intent"]
          and config["frame"]["scope_hints"] == example["frame"]["scope_hints"]
          and config["frame"]["stakeholders"] == example["frame"]["stakeholders"],
          "frame intent/scope_hints/stakeholders match")
    check(config["frame"].get("overview", "").strip()
          == example["frame"]["overview"].strip(),
          "frame.overview emitted and matches the example (D-A13: §1 identity, seeds §7, "
          "Arm 1's query context)")
    check(str(example["frame"]["key_dates"]["compliance_deadline"])
          == config["frame"]["key_dates"]["compliance_deadline"],
          "frame.key_dates.compliance_deadline matches")
    check(config["gates"] == {"score_threshold": example["gates"]["score_threshold"]},
          "gates match")

    print("\nGenerate to G0 through the TASK-050 backend:")
    with tempfile.TemporaryDirectory(prefix="frontend-proof-") as tmp:
        tmp_path = Path(tmp)
        registry = _stage_nongit_registry(tmp_path)
        dest = tmp_path / "work" / "SEAL-12345-routing"
        os.environ["PDLC_RUNS_INDEX"] = str(tmp_path / ".runs_index.jsonl")

        # Point the emitted config at the temp dest so the proof never writes outside tmp.
        posted = dict(config)
        posted["working_path"] = str(dest)

        from fastapi.testclient import TestClient  # noqa: E402
        from app.backend import app as backend_app  # noqa: E402

        client = TestClient(backend_app.app)
        resp = client.post(
            "/generate", json={"config": posted, "registry": str(registry), "ts": _FIXED_TS}
        )
        check(resp.status_code == 200, f"POST /generate → 200 (got {resp.status_code}: {resp.text[:160]})")
        body = resp.json() if resp.status_code == 200 else {}
        desc = body.get("descriptor", {})
        check(desc.get("checkpoint") == "G0" and desc.get("ran_workflow") is False,
              "scaffold at G0, ran_workflow=False (config + Generate only, FR-XS-09)")
        check((dest / "UI_INPUT.yaml").is_file() and (dest / ".github" / "copilot-instructions.md").is_file(),
              "§2.2 workspace scaffolded (UI_INPUT.yaml + .github/copilot-instructions.md)")
        written = yaml.safe_load((dest / "UI_INPUT.yaml").read_text(encoding="utf-8"))
        check(validation.validate_ui_input(written) == [],
              "written UI_INPUT.yaml is itself §3.1-valid")
        check(desc.get("run_id", "").startswith("r-"),
              f"Generate assigned a run_id ({desc.get('run_id')})")

    print()
    if failures:
        print(f"FAIL — {len(failures)} assertion(s) failed: {failures}")
        return 1
    print("PASS — the Run Configurator's emit produces a §3.1-conformant UI_INPUT (live "
          "connectors only; Confluence/Lucid deferred) that Generates to a G0 scaffold "
          "(FR-XS-02, FR-XS-06, FR-XS-16).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
