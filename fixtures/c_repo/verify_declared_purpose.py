#!/usr/bin/env python3
"""verify_declared_purpose.py — TASK-112 proof: declared-purpose extraction (D-A20).

The extractor is **frozen and deterministic** (a binding rule), so the first thing to prove is
that it still is: two runs over the same tree must be byte-identical. Everything after that
checks the D-A20 phenomena the additive fixture pass seeded.

  1. **Determinism** — two runs, byte-identical JSON.
  2. **Label variance** — every seeded label form is caught, including the `Putpose` typo. This
     is the one that matters: assuming a single keyword would have been a 5.7× under-report on
     the real corpus.
  3. **Headerless files declare nothing** — no invented purpose. The 40% fallback population is
     a normal outcome, not an error.
  4. **The versioned duplicate extracts as two ordinary files** — surfacing the pair is the map
     build's job (D-A16), never the extractor's silent pick.
  5. **Provenance is citable** — every declared purpose carries the line it was read from.
  6. **Noise is not mistaken for a declaration** — a URL or licence boilerplate in a leading
     comment must not become a purpose.
  7. **The alias set is profile data** — passing a narrower set changes what is found, which is
     what makes it per-repo configuration rather than a constant.
  8. **`extractor_sha` matches the live file** — a post-freeze edit cannot pass silently.

Run: python3 fixtures/c_repo/verify_declared_purpose.py
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_REPO_ROOT = _HERE.parents[1]
sys.path.insert(0, str(_REPO_ROOT / "core"))

import yaml  # noqa: E402
from extractors import c_extractor as X  # noqa: E402

_FAILURES: list[str] = []


def _check(label: str, ok: bool, detail: str = "") -> None:
    print(f"  [{'PASS' if ok else 'FAIL'}] {label}" + (f" — {detail}" if detail else ""))
    if not ok:
        _FAILURES.append(label)


def _files() -> list[str]:
    return sorted(str(p.relative_to(_HERE)) for p in _HERE.rglob("*")
                  if p.suffix in (".c", ".h"))


def main() -> int:
    files = _files()
    print(f"verify_declared_purpose — {len(files)} C files under fixtures/c_repo\n")

    # 1) Determinism — the frozen extractor's binding property.
    print("1) determinism (the extractor is frozen — same tree in, same bytes out):")
    a = json.dumps(X.run(files, str(_HERE)), sort_keys=True)
    b = json.dumps(X.run(files, str(_HERE)), sort_keys=True)
    _check("two runs are byte-identical", a == b, f"{len(a)} bytes")

    result = X.run(files, str(_HERE))
    entries = {e["path"]: e for e in result["entries"]}
    cr = result["coverage_report"]
    declared = {p: e for p, e in entries.items() if e.get("purpose_declared")}

    # 2) Label variance — the D-A20 distribution, typo included.
    print("\n2) label variance — every seeded form is caught (D-A20: fuzzy, not exact):")
    expected_labels = {
        "src/routing/brand_router.c": "PURPOSE",
        "src/routing/dispatch.c": "Intention",
        "src/routing/brand_registry.c": "Description",
        "src/settlement/ledger_post.c": "SYNOPSIS",
        "src/messaging/field_codec.c": "Desc",
        "src/errors/error_codes.c": "Descr",
        "src/transaction/settle_handler.c": "Purpose",
        "src/routing/capture_route.c": "Putpose",          # the typo
        "src/transaction/txn_lifecycle.c": "DESCRIPTION",
    }
    for path, label in expected_labels.items():
        e = entries.get(path, {})
        _check(f"{label:12} caught in {Path(path).name}", bool(e.get("purpose_declared")),
               (e.get("purpose_declared") or "")[:44])
    typo = entries["src/routing/capture_route.c"]
    _check("the TYPO label yields a real purpose, not a truncated one",
           typo["purpose_declared"] == "route capture-stage traffic to settlement",
           typo["purpose_declared"])
    _check("declared coverage is ~60% (D-A20 measured 58.0%)",
           0.55 <= cr["declared_purpose_coverage"] <= 0.65,
           f"{cr['files_declared_purpose']}/{cr['files_seen']} = {cr['declared_purpose_coverage']}")

    # 3) Headerless files declare nothing — no invention.
    print("\n3) headerless files (the ~40% fallback population):")
    headerless = [p for p in entries if p not in declared]
    _check("a substantial headerless population exists", len(headerless) >= 10,
           f"{len(headerless)} files")
    _check("no headerless file carries a declared purpose",
           all(not entries[p].get("purpose_declared") for p in headerless))
    _check("no headerless file carries a version or date either",
           all(not (entries[p].get("declared_version") or entries[p].get("declared_date"))
               for p in headerless))

    # 4) The versioned duplicate — two ordinary files.
    print("\n4) versioned duplicate `iso8583.c` + `iso8583_v2.c` (D-A20 finding 3):")
    v1 = entries.get("src/messaging/iso8583.c")
    v2 = entries.get("src/messaging/iso8583_v2.c")
    _check("both files are present and extracted", bool(v1) and bool(v2))
    _check("both declare a purpose (neither is marked dead)",
           bool(v1.get("purpose_declared")) and bool(v2.get("purpose_declared")))
    _check("both expose their own interfaces",
           bool(v1["interfaces"]) and bool(v2["interfaces"]),
           f"v1={len(v1['interfaces'])} v2={len(v2['interfaces'])}")
    _check("the extractor adds NO duplicate marking — surfacing is the map build's job (D-A16)",
           not any(k for k in v2 if "duplicate" in k.lower() or "version_of" in k.lower()))
    _check("static helpers stay out of the interface list",
           not any("set_bit" in i for i in v2["interfaces"]), str(v2["interfaces"]))

    # 5) Provenance — a declared purpose is citable to a line.
    print("\n5) provenance — declared purposes are citable (the point of `declared` over `inferred`):")
    _check("every declared purpose carries its line number",
           all("purpose_declared_line" in e for e in declared.values()))
    ok_lines = True
    for path, e in declared.items():
        line = (_HERE / path).read_text(encoding="utf-8").splitlines()[e["purpose_declared_line"] - 1]
        if e["purpose_declared"] not in line:
            ok_lines = False
            break
    _check("each cited line actually contains the purpose text", ok_lines)
    _check("versions and dates parse where stamped",
           sum(1 for e in declared.values() if e.get("declared_date")) == len(declared),
           f"{sum(1 for e in declared.values() if e.get('declared_date'))} dates")
    _check("quality is classified on every declaration",
           all(e.get("purpose_quality") in ("specific", "generic") for e in declared.values()))

    # 6) Noise is not a declaration.
    print("\n6) parser noise is refused (D-A20's named false positives):")
    noise = b"""/*
 * See http: //wiki.example.net/routing for background.
 * Redistribution is permitted provided that the following
 * conditions are met: the notice is retained.
 */
int f(void) { return 0; }
"""
    _check("a URL in a leading comment is not a purpose",
           not X.extract_declared(noise).get("purpose_declared"),
           str(X.extract_declared(noise)))
    generic = b"/* x.c  v001  210714  mtm  */\n/*\n Purpose:  utility functions\n*/\n"
    g = X.extract_declared(generic)
    _check("a stock purpose is FLAGGED generic, not dropped",
           g.get("purpose_declared") == "utility functions" and g["purpose_quality"] == "generic",
           str(g.get("purpose_quality")))

    # 7) The alias set is profile data, not a constant.
    print("\n7) the label alias set is PROFILE data (per repo, D-A22):")
    narrow = X.run(files, str(_HERE), label_aliases=["Intention"])
    n_declared = sum(1 for e in narrow["entries"] if e.get("purpose_declared"))
    _check("a narrower alias set finds strictly fewer purposes",
           n_declared < cr["files_declared_purpose"],
           f"{n_declared} with ['Intention'] vs {cr['files_declared_purpose']} with the default set")
    _check("…which is the 5.7× under-report D-A20 warns about, reproduced",
           n_declared <= cr["files_declared_purpose"] // 3,
           f"{n_declared} vs {cr['files_declared_purpose']}")

    # 8) The freeze is honest.
    print("\n8) freeze integrity:")
    manifest = yaml.safe_load((_REPO_ROOT / "core" / "extractor_manifest.yaml").read_text())
    recorded = next(e["extractor_sha"] for e in manifest["extractors"] if e["language"] == "c")
    live = subprocess.run(["git", "hash-object", "core/extractors/c_extractor.py"],
                          cwd=_REPO_ROOT, capture_output=True, text=True).stdout.strip()[:len(recorded)]
    _check("extractor_sha matches the live file", recorded == live, f"{recorded} == {live}")

    print()
    if _FAILURES:
        print(f"FAILED — {len(_FAILURES)} check(s): {_FAILURES}", file=sys.stderr)
        return 1
    print("PASS — extraction is deterministic; every label variant including the typo is caught; "
          "headerless files declare nothing; the versioned pair extracts as two ordinary files; "
          "declared purposes are citable to a line; noise is refused; the alias set is profile "
          "data; the freeze is honest.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
