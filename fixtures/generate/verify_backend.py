#!/usr/bin/env python3
"""verify_backend.py — TASK-050 proof: the Generate backend is a faithful CLI wrapper.

Replays the P0-locked ``fixtures/UI_INPUT.example.yaml`` *fields* through the FastAPI
service (``app/backend/app.py``) via the in-process ``TestClient`` (offline, no socket)
and asserts the TASK-050 acceptance:

  * valid config  → ``UI_INPUT.yaml`` written + §2.2 workspace scaffolded + G0 descriptor
                    with ``ran_workflow: False`` (Generate stopped before run, FR-XS-09);
  * the API path is **byte-identical** to the CLI path — the ``UI_INPUT.yaml`` the API writes
    and the descriptor it returns match ``generate.py`` run on the same config;
  * ``GET /runs/{id}/status`` **mirrors the ledger** (run_state.json + telemetry.jsonl);
  * ``GET /runs/{id}/ui_input`` returns the immutable run config;
  * invalid config → **422 naming the failing field**.

Offline + deterministic, exactly like ``verify_generate.py``: the locked fixture pins
``registry_sha: 7d2e9a1`` (not a git object here), so the registry is staged as a non-git
copy of ``core/`` + ``overlays/`` — hydrate's documented external-build direct-copy path. A
fixed ``ts`` is passed so the API and CLI descriptors are byte-comparable.

Run:  .venv/bin/python fixtures/generate/verify_backend.py
"""
from __future__ import annotations

import datetime as _dt
import os
import shutil
import sys
import tempfile
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_REPO_ROOT / "core" / "scripts"))
sys.path.insert(0, str(_REPO_ROOT))  # for `app.backend` package import

import yaml  # noqa: E402

_LOCKED_UI_INPUT = _REPO_ROOT / "fixtures" / "UI_INPUT.example.yaml"
_FIXED_TS = "2026-06-22T12:00:00Z"

# Descriptor keys that legitimately differ between the API run and the CLI run because each
# lays its scaffold at a different destination. Equality is asserted on everything else.
_PATH_KEYS = {"working_path", "registry", "run_started"}


def _stage_nongit_registry(root: Path) -> Path:
    reg = root / "registry"
    shutil.copytree(_REPO_ROOT / "core", reg / "core")
    shutil.copytree(_REPO_ROOT / "overlays", reg / "overlays")
    return reg


def _strip_paths(desc: dict) -> dict:
    """Drop the destination-specific keys so two scaffolds of the same config compare equal."""
    return {k: v for k, v in desc.items() if k not in _PATH_KEYS}


def _jsonable(value):
    """Mirror what the browser sends over JSON: YAML dates become ISO strings.

    ``yaml.safe_load`` turns ``2026-09-30`` into a ``datetime.date``; a real JSON client
    transmits it as the string ``"2026-09-30"``. Normalizing here keeps the proof honest
    about the wire format the API actually receives.
    """
    if isinstance(value, dict):
        return {k: _jsonable(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_jsonable(v) for v in value]
    if isinstance(value, (_dt.date, _dt.datetime)):
        return value.isoformat()
    return value


def main() -> int:
    failures: list[str] = []

    def check(cond: bool, label: str) -> None:
        print(f"  [{'OK' if cond else 'FAIL'}] {label}")
        if not cond:
            failures.append(label)

    config = _jsonable(yaml.safe_load(_LOCKED_UI_INPUT.read_text(encoding="utf-8")))

    with tempfile.TemporaryDirectory(prefix="backend-proof-") as tmp:
        tmp_path = Path(tmp)
        registry = _stage_nongit_registry(tmp_path)
        api_dest = tmp_path / "work" / "api" / "SEAL-12345-routing"
        cli_dest = tmp_path / "work" / "cli" / "SEAL-12345-routing"

        # Isolate the runs index inside the temp dir so the proof never touches the repo.
        os.environ["PDLC_RUNS_INDEX"] = str(tmp_path / ".runs_index.jsonl")

        # Import AFTER PDLC_RUNS_INDEX is set; the service reads it at call time anyway.
        from fastapi.testclient import TestClient  # noqa: E402

        from app.backend import app as backend_app  # noqa: E402
        import generate  # noqa: E402

        client = TestClient(backend_app.app)

        # --- POST /generate with the locked config → G0 ---------------------------------
        api_config = dict(config)
        api_config["working_path"] = str(api_dest)
        resp = client.post(
            "/generate",
            json={"config": api_config, "registry": str(registry), "ts": _FIXED_TS},
        )
        print("POST /generate (locked config) → G0 assertions:")
        check(resp.status_code == 200, f"200 OK (got {resp.status_code}: {resp.text[:200]})")
        body = resp.json() if resp.status_code == 200 else {}
        desc_api = body.get("descriptor", {})

        check(desc_api.get("checkpoint") == "G0" and desc_api.get("ran_workflow") is False,
              "descriptor marks G0, ran_workflow=False (config + Generate only, FR-XS-09)")
        check((api_dest / "UI_INPUT.yaml").is_file(), "UI_INPUT.yaml written into the workspace")
        check((api_dest / ".github" / "copilot-instructions.md").is_file(),
              "instruction file generated at .github/copilot-instructions.md (runtime_tool=copilot, §6.3)")
        check((api_dest / "ledger" / "run_state.json").is_file(), "ledger initialized")
        check((api_dest / "context_set").is_dir() and not any((api_dest / "context_set").iterdir()),
              "context_set/ present and empty (no ingest — Generate stopped at G0)")
        check(not (api_dest / "BRD.md").exists() and not (api_dest / "FRD.md").exists(),
              "no BRD.md/FRD.md (run artifacts; not laid at Generate)")
        check("G0 — scaffold inspection checkpoint" in body.get("checklist", ""),
              "G0 checklist returned for the operator (D4)")
        check(body.get("scaffold_path") == str(api_dest), "scaffold_path returned")

        # --- CLI on the same config → byte-equality + same descriptor -------------------
        # Feed the CLI the exact UI_INPUT.yaml the API wrote, at a different dest + fixed ts.
        api_ui_input = (api_dest / "UI_INPUT.yaml").read_text(encoding="utf-8")
        cli_ui_path = tmp_path / "cli_UI_INPUT.yaml"
        cli_ui_path.write_text(api_ui_input, encoding="utf-8")
        desc_cli = generate.generate(
            cli_ui_path, registry=str(registry), working_path=cli_dest, ts=_FIXED_TS
        )

        print("\nAPI ≡ CLI assertions:")
        check((cli_dest / "UI_INPUT.yaml").read_text(encoding="utf-8") == api_ui_input,
              "UI_INPUT.yaml byte-identical between the API workspace and the CLI workspace")
        check(_strip_paths(desc_api) == _strip_paths(desc_cli),
              "G0 descriptor identical to the CLI's (modulo destination path)")
        check(desc_api.get("run_id") == config["run_id"],
              f"run_id preserved from config ({config['run_id']})")
        check(desc_api.get("registry_sha") == "7d2e9a1" and desc_api.get("domain") == "payment_brand",
              "descriptor carries the locked registry_sha + domain")

        # --- GET /runs/{id}/status mirrors the ledger -----------------------------------
        run_id = config["run_id"]
        st = client.get(f"/runs/{run_id}/status")
        print("\nGET /runs/{id}/status assertions:")
        check(st.status_code == 200, f"200 OK (got {st.status_code})")
        sbody = st.json() if st.status_code == 200 else {}
        rs = yaml.safe_load((api_dest / "ledger" / "run_state.json").read_text(encoding="utf-8"))
        check(sbody.get("current_stage") == rs["current_stage"] == "ingest",
              "status.current_stage mirrors run_state.json (ingest)")
        check(sbody.get("stages") == rs["stages"]
              and all(s["status"] == "pending" for s in sbody["stages"].values()),
              "status.stages mirror run_state.json (all pending — nothing ran)")
        tel_lines = (api_dest / "ledger" / "telemetry.jsonl").read_text().splitlines()
        check(len(sbody.get("events", [])) == len(tel_lines) == 1
              and sbody["events"][0].get("event") == "run_started",
              "status.events mirror telemetry.jsonl (single run_started)")
        check(client.get("/runs/does-not-exist/status").status_code == 404,
              "unknown run_id → 404")

        # --- GET /runs/{id}/ui_input returns the immutable config ------------------------
        ui = client.get(f"/runs/{run_id}/ui_input")
        print("\nGET /runs/{id}/ui_input assertions:")
        check(ui.status_code == 200, f"200 OK (got {ui.status_code})")
        check(ui.json().get("raw") == api_ui_input,
              "ui_input.raw byte-identical to the workspace UI_INPUT.yaml")
        check(ui.json().get("ui_input", {}).get("registry_sha") == "7d2e9a1",
              "ui_input parsed config carries the locked registry_sha")

        # --- invalid config → 422 naming the failing field ------------------------------
        print("\nInvalid config → 422 naming the field:")
        bad = dict(config)
        bad["working_path"] = str(tmp_path / "work" / "bad")
        bad["runtime_tool"] = "emacs"          # not claude|copilot (FR-XS-06)
        del bad["gates"]                        # required block missing (§3.1, §9)
        bad["sources"] = [{"type": "bitbucket", "seal_id": "X"}]  # missing repo_url + auth_ref
        r422 = client.post("/generate", json={"config": bad, "registry": str(registry)})
        check(r422.status_code == 422, f"422 Unprocessable (got {r422.status_code})")
        errs = " | ".join(r422.json().get("detail", {}).get("errors", [])) if r422.status_code == 422 else ""
        check("runtime_tool" in errs, "422 names runtime_tool")
        check("gates" in errs, "422 names gates (missing block)")
        check("sources[0].repo_url" in errs and "sources[0].auth_ref" in errs,
              "422 names the missing per-source fields")
        check(not (Path(bad["working_path"]) / "UI_INPUT.yaml").exists(),
              "invalid config wrote nothing (no scaffold on a rejected request)")

    # ── TASK-129: the jira block's level/parent_link asymmetry ────────────────────────
    # Not symmetric by accident. Below the top level a parent is REQUIRED — its absence would
    # push an orphan into Jira, the run's only irreversible act. At `initiative` it is FORBIDDEN,
    # because nothing sits above one and accepting it would let a run claim a parent it will
    # never attach to. A validator that merely made it "optional" would allow both mistakes.
    print("\njira block — §3.1 validation (TASK-129):")
    from app.backend import validation as V

    base = yaml.safe_load(_LOCKED_UI_INPUT.read_text(encoding="utf-8"))
    check(V.validate_ui_input(base) == [],
          "the locked example — with its jira block — is §3.1-valid")

    def _with_jira(**over):
        cfg = yaml.safe_load(_LOCKED_UI_INPUT.read_text(encoding="utf-8"))
        cfg["jira"] = {**cfg["jira"], **over}
        return V.validate_ui_input(cfg)

    errs = _with_jira(level="epic")          # parent_link absent
    check(any("jira.parent_link" in e for e in errs),
          f"level 'epic' with no parent_link is REFUSED, naming the field (got {errs})")
    errs = _with_jira(level="initiative", parent_link="PBI-1000")
    check(any("jira.parent_link" in e for e in errs),
          "a parent_link at level 'initiative' is REFUSED — nothing sits above an Initiative")
    check(_with_jira(level="epic", parent_link="PBI-2000") == [],
          "level 'epic' WITH a parent_link is accepted")
    errs = _with_jira(level="story")
    check(any("jira.level" in e for e in errs), "an unknown level is refused, naming the field")

    cfg = yaml.safe_load(_LOCKED_UI_INPUT.read_text(encoding="utf-8"))
    cfg["jira"]["controls"].pop("seal_id")
    check(any("jira.controls.seal_id" in e for e in V.validate_ui_input(cfg)),
          "a missing control is caught HERE, not left to fail the hard G3 check later")

    cfg = yaml.safe_load(_LOCKED_UI_INPUT.read_text(encoding="utf-8"))
    cfg.pop("jira")
    check(V.validate_ui_input(cfg) == [],
          "the block stays OPTIONAL — it is consumed only at L4, so an L1-only run is still valid")

    print()
    if failures:
        print(f"FAIL — {len(failures)} assertion(s) failed: {failures}")
        return 1
    print("PASS — backend replays the locked config to a byte-equal §2.2 scaffold + identical "
          "G0 descriptor as the CLI; status/ui_input mirror the ledger; invalid config → 422 "
          "naming the field (FR-XS-02, FR-XS-09, FR-XS-16, NFR-01).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
