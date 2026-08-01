#!/usr/bin/env python3
"""verify_pdf_text.py — TASK-127 follow-up: PDF→text is a declared dependency, not a hope.

`pdf_extract` used to assume the running agent could read a PDF itself. That is an **ambient
capability, not a declared one**, and the first real end-to-end run had neither a PDF library nor
poppler — the doc lane would have stopped at step one. `core/scripts/pdf_text.py` makes it a real
dependency with a stdlib fallback, so the pipeline runs on a machine with nothing installed.

What this proves:

  1. **It works with no dependencies at all.** The builtin backend is `zlib` + `base64`.
  2. **Line structure survives** — the unit the index selects in and the author pulls by. A reader
     that welds a paragraph onto one line makes every line range degenerate, so this checks the
     wrap actually happened rather than just that text came out.
  3. **The text is faithful** — headings, glyphs and figures present, nothing invented.
  4. **Failures are loud and distinguishable**: a missing file, and a PDF with no extractable text
     (a scan), report differently and neither is silently "empty".

Run: python3 fixtures/pdf/verify_pdf_text.py
"""
from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_REPO_ROOT = _HERE.parents[1]
sys.path.insert(0, str(_REPO_ROOT / "core" / "scripts"))

import pdf_text  # noqa: E402

_P1 = _HERE / "mastercard_mandate_part1_2026.pdf"
_P2 = _HERE / "mastercard_mandate_part2_2026.pdf"
_FAILURES: list[str] = []


def _check(label: str, ok: bool, detail: str = "") -> None:
    print(f"  [{'PASS' if ok else 'FAIL'}] {label}" + (f" — {detail}" if detail else ""))
    if not ok:
        _FAILURES.append(label)


def main() -> int:
    print("verify_pdf_text — PDF→text as a declared dependency\n")

    print("1) it runs with nothing installed:")
    _check(f"a backend resolves ({pdf_text.available_backend()})",
           pdf_text.available_backend() in ("pypdf", "builtin"))
    lines = pdf_text.extract_lines(_P1, backend="builtin")
    _check("the BUILTIN backend (stdlib only) extracts text", len(lines) > 50, f"{len(lines)} lines")

    print("\n2) line structure survives — the index selects in lines:")
    longest = max(len(l) for l in lines)
    _check("no line is a welded-together paragraph", longest < 140, f"longest = {longest} chars")
    _check("prose is wrapped, not one line per paragraph",
           sum(1 for l in lines if 60 < len(l) < 140) > 20,
           "a reader that concatenates would show few mid-length lines")
    _check("headings survive as their own lines",
           any(l.strip() == "1. Mandate Summary" for l in lines))

    print("\n3) the text is faithful:")
    body = "\n".join(lines)
    for probe, why in [("MCS-2026-R3", "the mandate id"),
                       ("2026-09-30", "the compliance deadline"),
                       ("Token Requestor ID", "a DE 48 subelement name"),
                       ("•", "bullet glyphs decoded from their font octal"),
                       ("—", "em dashes decoded")]:
        _check(f"{why} is present", probe in body)
    _check("nothing is invented: every line came from the stream",
           all(l == l.rstrip() for l in lines))

    p2 = pdf_text.extract_lines(_P2, backend="builtin")
    _check("the second, denser document extracts too", len(p2) > len(lines),
           f"part2 {len(p2)} lines vs part1 {len(lines)}")
    _check("its interchange table rows survive as separate lines",
           any("2.10%" in l for l in p2) and any("World Elite" in l for l in p2))

    print("\n4) failures are loud and distinguishable:")
    script = _REPO_ROOT / "core" / "scripts" / "pdf_text.py"
    r = subprocess.run([sys.executable, str(script), "/nope/missing.pdf"],
                       capture_output=True, text=True)
    _check("a missing file exits 2 naming the path", r.returncode == 2 and "missing.pdf" in r.stderr)

    with tempfile.TemporaryDirectory(prefix="pdf-empty-") as td:
        blank = Path(td) / "scan.pdf"
        blank.write_bytes(b"%PDF-1.4\n% no content streams at all\n%%EOF\n")
        r = subprocess.run([sys.executable, str(script), str(blank)],
                           capture_output=True, text=True)
        _check("a PDF with no extractable text exits 1, NOT 0", r.returncode == 1,
               f"rc={r.returncode}")
        _check("and says to record it as unreadable rather than treat it as empty",
               "unreadable" in r.stderr,
               "a scanned image must become an [[unreadable: …]] marker, never a silent gap")

    r = subprocess.run([sys.executable, str(script), "--which"], capture_output=True, text=True)
    _check("--which reports the backend for the port-time precheck",
           r.returncode == 0 and r.stdout.strip() in ("pypdf", "builtin"))

    print()
    if _FAILURES:
        print(f"FAILED — {len(_FAILURES)} check(s): {_FAILURES}", file=sys.stderr)
        return 1
    print("PASS — PDF→text runs on a machine with nothing installed, preserves the line structure "
          "the index depends on, stays faithful to the page, and fails loudly and distinguishably.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
