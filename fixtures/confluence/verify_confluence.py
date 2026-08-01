#!/usr/bin/env python3
"""verify_confluence.py — TASK-063 proof: the Confluence connector honours the contract.

Verifies ``core/scripts/ingest_confluence.py`` offline — the VDI fetch (``_fetch_confluence``)
is the only unwired piece; everything else is proven here (§6.6.2, §3.2, FR-DC-01/11/12):

  1. **Local-path convenience** stages the fixture page and emits a descriptor whose **keys are
     identical to ``ingest_file.py``'s** — so the doc pipeline reads it unchanged (parity).
  2. **Multiple links → independent entries.** Two Confluence pages stage to two distinct
     ``staged_path``s with their own descriptors — the foundation for each carrying its own
     operator-declared ``disposition`` (D-A12: one link = one source row = one disposition).
  3. **Injected fetcher** (the VDI seam stand-in) stages an ``https://`` page through the auth
     seam; with a stub token backend the secret (a canary) appears NOWHERE in the descriptor or
     the staged file, and the fetcher receives the resolved handle.
  4. **Placeholder fails loud** — the un-wired ``_fetch_confluence`` raises ``NotImplementedError``
     for an ``https://`` URL (not a silent 0-byte stage), pointing at the VDI wire-up.
  5. **§10.4 connector coverage** maps ``type: confluence → ingest_confluence.py`` green, and the
     connector does **not** branch on ``domain`` (AST check).

Run:  python fixtures/confluence/verify_confluence.py
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
import ingest_confluence  # noqa: E402
from jpmc_adapters import auth as _auth  # noqa: E402
from build_checks import branches_on_domain, check_connector_coverage  # noqa: E402

_PAGE_A = _REPO_ROOT / "fixtures" / "confluence" / "discover_routing_kb.html"
_PAGE_B = _REPO_ROOT / "fixtures" / "confluence" / "message_format_kb.html"
_CANARY = "cf-canary-token-DEADBEEF-LEAKCANARY"
_DESCRIPTOR_KEYS = {"type", "source", "url", "staged_path", "auth_ref", "ingest_ts"}


class StubBackend:
    def __init__(self, secrets):
        self._secrets = secrets

    def get(self, key):
        return self._secrets.get(key)


def _check(label, cond):
    print(f"  [{'PASS' if cond else 'FAIL'}] {label}")
    if not cond:
        raise SystemExit(f"verify_confluence: FAILED — {label}")


def main() -> int:
    print("verify_confluence.py — TASK-063 Confluence connector proof")
    with tempfile.TemporaryDirectory(prefix="verify-confluence-") as td:
        root = Path(td)

        # 1) Local-path convenience → descriptor shape identical to ingest_file's.
        d_cf = ingest_confluence.pull_page(str(_PAGE_A), root / "c1", source="confluence", auth_ref=None)
        d_file = ingest_file.stage_document(str(_PAGE_A), root / "c_file", source="confluence")
        _check("staged the page on disk", Path(d_cf["staged_path"]).is_file())
        _check("descriptor keys == ingest_file's contract", set(d_cf) == _DESCRIPTOR_KEYS == set(d_file))
        _check("descriptor type is 'confluence'", d_cf["type"] == "confluence")
        _check("provenance url recorded", d_cf["url"] == str(_PAGE_A))

        # 2) Multiple links → two independent staged entries (tagged separately downstream).
        d_a = ingest_confluence.pull_page(str(_PAGE_A), root / "m", source="confluence", auth_ref=None)
        d_b = ingest_confluence.pull_page(str(_PAGE_B), root / "m", source="confluence", auth_ref=None)
        _check("two links → two distinct staged_paths", d_a["staged_path"] != d_b["staged_path"])
        _check("both pages staged on disk",
               Path(d_a["staged_path"]).is_file() and Path(d_b["staged_path"]).is_file())

        # 3) Injected fetcher (VDI stand-in) over an https URL, through the auth seam.
        saved = _auth.get_backend()
        _auth.set_backend(StubBackend({"confluence": _CANARY}))
        seen = {}

        def fake_fetch(url, handle, target):
            seen["handle_secret"] = handle.reveal() if handle else None
            shutil.copy2(_PAGE_A, target)                    # stand in for the real REST fetch

        ingest_confluence.set_fetcher(fake_fetch)
        try:
            url = "https://confluence.jpmc.net/display/PBI/Card+Brand+Routing"
            d_http = ingest_confluence.pull_page(url, root / "c2", auth_ref="jpmc_adapters:confluence")
            _check("https pull staged via the injected fetcher", Path(d_http["staged_path"]).is_file())
            _check("fetcher received the seam-resolved token", seen.get("handle_secret") == _CANARY)
            _check("descriptor keeps auth_ref pointer, not the secret",
                   d_http["auth_ref"] == "jpmc_adapters:confluence" and _CANARY not in json.dumps(d_http))
            # No secret on disk: scan the staged tree + a written descriptor for the canary.
            (root / "c2" / "descriptor.json").write_text(json.dumps(d_http), encoding="utf-8")
            leak = any(_CANARY in p.read_text(encoding="utf-8", errors="ignore")
                       for p in (root / "c2").rglob("*") if p.is_file())
            _check("token appears NOWHERE under the staging dir", not leak)

            # 4) The un-wired placeholder fails loud for an https URL.
            ingest_confluence.set_fetcher(ingest_confluence._fetch_confluence)  # restore the [TBD] stub
            raised = False
            try:
                ingest_confluence.pull_page(url, root / "c3", auth_ref="jpmc_adapters:confluence")
            except NotImplementedError as exc:
                raised = "VDI" in str(exc)
            _check("un-wired _fetch_confluence raises NotImplementedError naming the VDI wire-up", raised)
        finally:
            ingest_confluence.set_fetcher(ingest_confluence._fetch_confluence)
            _auth.set_backend(saved)

        # 5) §10.4 connector coverage maps confluence → ingest_confluence.py, no domain branch.
        cov = check_connector_coverage([{"type": "confluence"}], repo_root=_REPO_ROOT)
        _check("§10.4 maps type:confluence → ingest_confluence.py (green)", cov.ok)
        _check("ingest_confluence.py does not branch on `domain`",
               not branches_on_domain(_REPO_ROOT / "core" / "scripts" / "ingest_confluence.py"))

    # ── the LANE, not just the connector (TASK-127) ───────────────────────────────────────
    # Staging a page is only half the contract. Until TASK-127 the connector was green while
    # the pipeline had nowhere to send its output: §6.6.3's amended per-type lanes named
    # `confluence_extract`, nothing had built it, and a Confluence page stopped dead as raw
    # `.html` because `doc_index` requires a `.md` extract. A connector check alone could
    # never see that — it ends at `staged_path`.
    print("\nthe confluence LANE resolves end to end:")
    import yaml

    adapter = yaml.safe_load(
        (_REPO_ROOT / "core/profiles/payment_brand/adapter/adapter.yaml").read_text())
    lanes = adapter["docs_pipeline"]
    _check("docs_pipeline is the per-type mapping form (§6.6.3)", isinstance(lanes, dict))
    _check("a `confluence` lane exists", "confluence" in lanes)
    _check("a `default` lane still exists (the required fallback)", "default" in lanes)

    lane = [s["skill"] for s in lanes.get("confluence", [])]
    _check("the confluence lane is <extract> → doc_index", lane == ["confluence_extract", "doc_index"])
    _check("its extract step ends the lane in `.md`, which is what doc_index consumes",
           lane and lane[0].endswith("_extract"))

    skill = _REPO_ROOT / "core/skills/confluence_extract.skill.md"
    _check("confluence_extract lives in core/skills (referenced, not packed per domain)",
           skill.is_file())
    _check("it is NOT duplicated into the domain pack",
           not (_REPO_ROOT / "core/profiles/payment_brand/adapter/confluence_extract.skill.md").exists())
    _check("confluence_extract does not branch on `domain` (D7)",
           "payment_brand" not in skill.read_text(encoding="utf-8").split("*(Design call")[0])

    # Every doc lane must end in doc_index — that is the D-A18 invariant the mapping form
    # makes easy to violate by adding a lane and forgetting the index step.
    tail_ok = {k: [s["skill"] for s in v][-1] == "doc_index" for k, v in lanes.items()}
    if not all(tail_ok.values()):
        print(f"    lanes missing the index step: "
              f"{sorted(k for k, v in tail_ok.items() if not v)}")
    _check("EVERY doc lane ends in doc_index (D-A18)", all(tail_ok.values()))

    print("\nverify_confluence: ALL CHECKS PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
