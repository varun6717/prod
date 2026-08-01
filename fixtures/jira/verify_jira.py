#!/usr/bin/env python3
"""verify_jira.py — TASK-107 proof: the Jira connector honours the contract.

Verifies ``core/scripts/ingest_jira.py`` offline — the VDI fetch (``_fetch_issue``) is the only
unwired piece; everything else is proven here (§6.6.2, §3.2, D-A24, FR-DC-01/11/12):

  1. **Local-path convenience** stages the mock payload and emits a descriptor whose **keys are
     identical to ``ingest_file.py``'s** — so the doc pipeline reads it unchanged (parity).
  2. **Rendering is mechanical and TOTAL.** Every payload field reaches the extract: the known
     ones under their fixed headings, the unknown ones under "Other fields". A field the payload
     lacks is omitted, never rendered empty or invented. Nothing is summarised.
  3. **Multiple issues → independent entries.** Two issues stage to two distinct ``staged_path``s
     (one issue = one source row = one disposition, D-A12).
  4. **Injected fetcher** (the VDI seam stand-in) pulls an ``https://`` issue through the auth
     seam; with a stub token backend the secret (a canary) appears NOWHERE in the descriptor or
     the staged file, and the fetcher receives the resolved handle.
  5. **Placeholder fails loud** — the un-wired ``_fetch_issue`` raises ``NotImplementedError``
     for an ``https://`` URL (not a silent 0-byte stage), pointing at the VDI wire-up.
  6. **§10.4 connector coverage** maps ``type: jira → ingest_jira.py`` green, and the connector
     does **not** branch on ``domain`` (AST check).
  7. **`prior_artifact` is the declared default** for this source type, in the one taxonomy
     definition every consumer shares.

Run:  python fixtures/jira/verify_jira.py
"""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_REPO_ROOT / "core" / "scripts"))
sys.path.insert(0, str(_REPO_ROOT / "core" / "adapters"))

import dispositions  # noqa: E402
import ingest_file  # noqa: E402
import ingest_jira  # noqa: E402
from jpmc_adapters import auth as _auth  # noqa: E402
from build_checks import branches_on_domain, check_connector_coverage  # noqa: E402

_EPIC = _REPO_ROOT / "fixtures" / "jira" / "PBI-4471.json"
_STORY = _REPO_ROOT / "fixtures" / "jira" / "PBI-4602.json"
_CANARY = "jira-canary-token-DEADBEEF-LEAKCANARY"
_DESCRIPTOR_KEYS = {"type", "source", "url", "staged_path", "auth_ref", "ingest_ts"}


class StubBackend:
    def __init__(self, secrets):
        self._secrets = secrets

    def get(self, key):
        return self._secrets.get(key)


def _check(label, cond):
    print(f"  [{'PASS' if cond else 'FAIL'}] {label}")
    if not cond:
        raise SystemExit(f"verify_jira: FAILED — {label}")


def main() -> int:
    print("verify_jira.py — TASK-107 Jira connector proof")
    with tempfile.TemporaryDirectory(prefix="verify-jira-") as td:
        root = Path(td)

        # 1) Local-path convenience → descriptor shape identical to ingest_file's.
        d_ji = ingest_jira.pull_issue(str(_EPIC), root / "j1", source="jira", auth_ref=None)
        d_file = ingest_file.stage_document(str(_EPIC), root / "j_file", source="jira")
        staged = Path(d_ji["staged_path"])
        _check("staged the issue on disk", staged.is_file())
        _check("descriptor keys == ingest_file's contract", set(d_ji) == _DESCRIPTOR_KEYS == set(d_file))
        _check("descriptor type is 'jira'", d_ji["type"] == "jira")
        _check("provenance url recorded", d_ji["url"] == str(_EPIC))
        _check("staged file is named for the issue key", staged.name == "PBI-4471.md")

        # 2) Rendering is mechanical and total — nothing dropped, nothing invented.
        text = staged.read_text(encoding="utf-8")
        payload = json.loads(_EPIC.read_text(encoding="utf-8"))
        fields = payload["fields"]
        _check("title carries key + summary", text.startswith("# PBI-4471 — Discover brand"))
        for heading in ("## Description", "## Acceptance criteria", "## Comments",
                        "## Issue type", "## Status", "## Labels", "## Components"):
            _check(f"extract carries {heading!r}", heading in text)
        _check("object-wrapped values unwrapped verbatim (issuetype → 'Epic')",
               "Epic" in text and '{"name"' not in text)
        _check("list values joined (labels)", all(l in text for l in fields["labels"]))
        _check("description copied verbatim, not summarised",
               fields["description"].splitlines()[0] in text)
        _check("comment author + body both rendered",
               "A. Rahman" in text and "co-badged Discover/Diners" in text)
        # totality: a field the heading table does not know must still surface
        _check("unknown field surfaces under 'Other fields' (never silently dropped)",
               "## Other fields" in text and "customfield_10021" in text and "SEAL-12345" in text)
        # the payload's own _comment sits OUTSIDE `fields`, so it must not leak into the extract
        _check("fixture's top-level _comment is not rendered", "Offline Jira-stand-in" not in text)

        # A sparse payload: absent fields are omitted, not rendered empty.
        d_sparse = ingest_jira.pull_issue(str(_STORY), root / "j1", source="jira", auth_ref=None)
        sparse = Path(d_sparse["staged_path"]).read_text(encoding="utf-8")
        _check("sparse issue renders the fields it has", "## Description" in sparse)
        for absent in ("## Priority", "## Resolution", "## Comments", "## Fix versions",
                       "## Acceptance criteria", "## Other fields"):
            _check(f"absent field {absent!r} omitted, not empty", absent not in sparse)

        # 3) Multiple issues → two independent staged entries.
        _check("two issues → two distinct staged_paths",
               d_ji["staged_path"] != d_sparse["staged_path"])
        _check("both issues staged on disk",
               Path(d_ji["staged_path"]).is_file() and Path(d_sparse["staged_path"]).is_file())

        # 4) Injected fetcher (VDI stand-in) over an https URL, through the auth seam.
        saved = _auth.get_backend()
        _auth.set_backend(StubBackend({"jira": _CANARY}))
        seen = {}

        def fake_fetch(url, handle):
            seen["handle_secret"] = handle.reveal() if handle else None
            return json.loads(_EPIC.read_text(encoding="utf-8"))   # stand in for the REST fetch

        ingest_jira.set_fetcher(fake_fetch)
        try:
            url = "https://jira.jpmc.net/browse/PBI-4471"
            d_http = ingest_jira.pull_issue(url, root / "j2", auth_ref="jpmc_adapters:jira")
            _check("https pull staged via the injected fetcher", Path(d_http["staged_path"]).is_file())
            _check("fetcher received the seam-resolved token", seen.get("handle_secret") == _CANARY)
            _check("descriptor keeps auth_ref pointer, not the secret",
                   d_http["auth_ref"] == "jpmc_adapters:jira" and _CANARY not in json.dumps(d_http))
            _check("provenance url is the Jira URL", d_http["url"] == url)
            _check("extract records its source URL", url in Path(d_http["staged_path"]).read_text())
            # No secret on disk: scan the staged tree + a written descriptor for the canary.
            (root / "j2" / "descriptor.json").write_text(json.dumps(d_http), encoding="utf-8")
            leak = any(_CANARY in p.read_text(encoding="utf-8", errors="ignore")
                       for p in (root / "j2").rglob("*") if p.is_file())
            _check("token appears NOWHERE under the staging dir", not leak)

            # 5) The un-wired placeholder fails loud for an https URL.
            ingest_jira.set_fetcher(ingest_jira._fetch_issue)      # restore the [TBD] stub
            raised = False
            try:
                ingest_jira.pull_issue(url, root / "j3", auth_ref="jpmc_adapters:jira")
            except NotImplementedError as exc:
                raised = "VDI" in str(exc)
            _check("un-wired _fetch_issue raises NotImplementedError naming the VDI wire-up", raised)
        finally:
            ingest_jira.set_fetcher(ingest_jira._fetch_issue)
            _auth.set_backend(saved)

        # 6) §10.4 connector coverage maps jira → ingest_jira.py, no domain branch.
        cov = check_connector_coverage([{"type": "jira"}], repo_root=_REPO_ROOT)
        _check("§10.4 maps type:jira → ingest_jira.py (green)", cov.ok)
        _check("ingest_jira.py does not branch on `domain`",
               not branches_on_domain(_REPO_ROOT / "core" / "scripts" / "ingest_jira.py"))

        # 7) The disposition default lives in the one shared taxonomy definition (D-A12).
        _check("dispositions.default_for('jira') == ['prior_artifact']",
               dispositions.default_for("jira") == ["prior_artifact"])
        _check("prior_artifact is never a sole citation (reference-only hazard, D-A12)",
               "prior_artifact" in dispositions.NON_PRIMARY_DISPOSITIONS)

    print("verify_jira: ALL CHECKS PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
