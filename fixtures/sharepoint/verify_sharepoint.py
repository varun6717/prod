#!/usr/bin/env python3
"""verify_sharepoint.py — TASK-055 proof: the SharePoint connector skeleton honours the contract.

Verifies ``core/scripts/ingest_sharepoint.py`` offline — the VDI fetch (``_download_pdf``)
is the only unwired piece; everything else is proven here (§6.6.2, §3.2, FR-DC-01/11/12):

  1. **Local-path convenience** stages the fixture PDF and emits a descriptor whose **keys
     are identical to ``ingest_file.py``'s** — so ``pdf_extract`` reads it unchanged.
  2. **Injected downloader** (the VDI seam stand-in) stages an ``https://`` SharePoint URL
     through the auth seam; with a stub token backend the secret (a canary) appears NOWHERE
     in the descriptor or the staged file, and the downloader receives the resolved handle.
  3. **Placeholder fails loud** — the un-wired ``_download_pdf`` raises ``NotImplementedError``
     for an ``https://`` URL (not a silent 0-byte stage), pointing at the VDI wire-up.
  4. **§10.4 connector coverage** maps ``type: sharepoint → ingest_sharepoint.py`` green, and
     the connector does **not** branch on ``domain`` (AST check).

Run:  .venv/bin/python fixtures/sharepoint/verify_sharepoint.py
"""
from __future__ import annotations

import json
import shutil
import sys
import tempfile
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_REPO_ROOT / "core" / "scripts"))
sys.path.insert(0, str(_REPO_ROOT / "core" / "adapters"))

import ingest_file  # noqa: E402
import ingest_sharepoint  # noqa: E402
from jpmc_adapters import auth as _auth  # noqa: E402
from build_checks import branches_on_domain, check_connector_coverage  # noqa: E402

_PDF_A = _REPO_ROOT / "fixtures" / "pdf" / "mastercard_mandate_part1_2026.pdf"
_PDF_B = _REPO_ROOT / "fixtures" / "pdf" / "mastercard_mandate_part2_2026.pdf"
_CANARY = "sp-canary-token-DEADBEEF-LEAKCANARY"
_DESCRIPTOR_KEYS = {"type", "source", "url", "staged_path", "auth_ref", "ingest_ts"}


class StubBackend:
    def __init__(self, secrets):
        self._secrets = secrets

    def get(self, key):
        return self._secrets.get(key)


def _check(label, cond):
    print(f"  [{'PASS' if cond else 'FAIL'}] {label}")
    if not cond:
        raise SystemExit(f"verify_sharepoint: FAILED — {label}")


def main() -> int:
    print("verify_sharepoint.py — TASK-055 SharePoint connector proof")
    with tempfile.TemporaryDirectory(prefix="verify-sharepoint-") as td:
        root = Path(td)

        # 1) Local-path convenience → descriptor shape identical to ingest_file's.
        d_sp = ingest_sharepoint.pull_document(str(_PDF_A), root / "s1", source="sharepoint", auth_ref=None)
        d_file = ingest_file.stage_document(str(_PDF_A), root / "s_file", source="sharepoint")
        _check("staged the PDF on disk", Path(d_sp["staged_path"]).is_file())
        _check("descriptor keys == ingest_file's contract", set(d_sp) == _DESCRIPTOR_KEYS == set(d_file))
        _check("descriptor type is 'sharepoint'", d_sp["type"] == "sharepoint")
        _check("provenance url recorded", d_sp["url"] == str(_PDF_A))

        # 2) Injected downloader (VDI stand-in) over an https URL, through the auth seam.
        saved = _auth.get_backend()
        _auth.set_backend(StubBackend({"sharepoint": _CANARY}))
        seen = {}

        def fake_download(url, handle, target):
            seen["handle_secret"] = handle.reveal() if handle else None
            shutil.copy2(_PDF_A, target)                       # stand in for the real Graph fetch

        ingest_sharepoint.set_downloader(fake_download)
        try:
            url = "https://jpmc.sharepoint.com/sites/PBI/Shared%20Documents/mandate.pdf"
            d_http = ingest_sharepoint.pull_document(url, root / "s2", auth_ref="jpmc_adapters:sharepoint")
            _check("https pull staged via the injected downloader", Path(d_http["staged_path"]).is_file())
            _check("downloader received the seam-resolved token", seen.get("handle_secret") == _CANARY)
            _check("descriptor keeps auth_ref pointer, not the secret",
                   d_http["auth_ref"] == "jpmc_adapters:sharepoint" and _CANARY not in json.dumps(d_http))
            # No secret on disk: scan the staged tree + a written descriptor for the canary.
            (root / "s2" / "descriptor.json").write_text(json.dumps(d_http), encoding="utf-8")
            leak = any(_CANARY in p.read_text(encoding="utf-8", errors="ignore")
                       for p in (root / "s2").rglob("*") if p.is_file())
            _check("token appears NOWHERE under the staging dir", not leak)

            # 3) The un-wired placeholder fails loud for an https URL.
            ingest_sharepoint.set_downloader(ingest_sharepoint._download_pdf)  # restore the [TBD] stub
            raised = False
            try:
                ingest_sharepoint.pull_document(url, root / "s3", auth_ref="jpmc_adapters:sharepoint")
            except NotImplementedError as exc:
                raised = "VDI" in str(exc)
            _check("un-wired _download_pdf raises NotImplementedError naming the VDI wire-up", raised)
        finally:
            ingest_sharepoint.set_downloader(ingest_sharepoint._download_pdf)
            _auth.set_backend(saved)

        # 4) §10.4 connector coverage maps sharepoint → ingest_sharepoint.py, no domain branch.
        cov = check_connector_coverage([{"type": "sharepoint"}], repo_root=_REPO_ROOT)
        _check("§10.4 maps type:sharepoint → ingest_sharepoint.py (green)", cov.ok)
        _check("ingest_sharepoint.py does not branch on `domain`",
               not branches_on_domain(_REPO_ROOT / "core" / "scripts" / "ingest_sharepoint.py"))

    # ── MULTIPLE SharePoint documents (TASK-127 regression) ────────────────────────────
    # This refused anything but a single entry ("slice-1 expects one sharepoint source") while
    # ingest_confluence and ingest_jira had both been generalised. VDI_WIRING states PDFs ALWAYS
    # arrive via SharePoint, so multi-document is the production norm, not an edge case — and the
    # fixture corpus is itself one mandate split across two PDFs with different dispositions.
    print("\nmultiple SharePoint sources in one UI_INPUT:")
    with tempfile.TemporaryDirectory(prefix="verify-sp-multi-") as td:
        root = Path(td)
        ui = root / "UI_INPUT.yaml"
        ui.write_text(
            "sources:\n"
            f"  - {{type: sharepoint, url: '{_PDF_A}', source: sharepoint, "
            "auth_ref: 'jpmc_adapters:sharepoint', disposition: [business_requirement]}\n"
            f"  - {{type: sharepoint, url: '{_PDF_B}', source: sharepoint, "
            "auth_ref: 'jpmc_adapters:sharepoint', disposition: [technical_specification]}\n",
            encoding="utf-8")
        entries = ingest_sharepoint._sources_from_ui_input(ui)
        _check("both type:sharepoint entries are returned, not refused", len(entries) == 2)
        _check("each keeps its own operator-declared disposition",
               [e["disposition"] for e in entries]
               == [["business_requirement"], ["technical_specification"]])

    print("verify_sharepoint: ALL CHECKS PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
