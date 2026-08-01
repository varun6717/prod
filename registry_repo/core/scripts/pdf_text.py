#!/usr/bin/env python3
"""pdf_text.py — deterministic PDF → text with line structure preserved (§6.6.3, D-A18).

`pdf_extract` turns a staged PDF into the structural Markdown everything downstream keys on. Until
TASK-127 it assumed **the running agent could read a PDF itself** — an ambient capability, not a
declared dependency. The first real end-to-end run had no PDF library and no poppler, and the doc
lane would have stopped at step one had the extract not been recovered by hand.

That is the same shape `ENV_PRECHECK.md` already records for the C extractor: the JPMC VDI is
AppLocker-locked, so binary installers are blocked while **pip into a venv runs in-policy**. So the
answer here matches ADR-001's: a Python dependency, with a fallback rather than a hard failure.

Two backends, tried in order:

  1. **pypdf** — if importable. Better coverage of real-world PDFs (encryption, odd filters,
     CID fonts), and the one to provision on the VDI.
  2. **the built-in reader** — pure stdlib (`zlib` + `base64`), no install. Decodes the content
     streams and reconstructs lines from the text-positioning operators. Handles the
     ASCII85/Flate PDFs this pipeline actually receives, and needs nothing at all.

**This module extracts text, never meaning.** No summarising, no classification, no reordering —
that is `pdf_extract`'s and `doc_index`'s territory. It returns pages of lines and stops.

The line grouping is the part that matters. `lines` is the unit the index selects in and the SI
author pulls by, so a reader that concatenates a paragraph into one physical line makes every line
range degenerate. Lines are split on the **text-positioning operators** (`Td`/`TD`/`T*`/`Tm`),
because those are emitted exactly once per laid-out line — grouping by y-coordinate *value* fails,
since a paragraph's per-line offsets do not always move y detectably, and the result silently
welds a paragraph together with the spaces eaten at each wrap.
"""
from __future__ import annotations

import base64
import re
import sys
import zlib
from pathlib import Path

# Font-encoding octals that appear in these PDFs' content streams, mapped to their real glyphs.
_GLYPH = {"\x7f": "•", "\x96": "–", "\x97": "—", "\x92": "’",
          "\x93": "“", "\x94": "”", "\xae": "→"}

_TOKENS = re.compile(
    r"(?P<m>[\d.-]+)\s+(?P<n>[\d.-]+)\s+(?P<op>Td|TD)|(?P<nl>T\*)|"
    r"(?P<a>[\d.-]+)\s+[\d.-]+\s+[\d.-]+\s+[\d.-]+\s+(?P<tx>[\d.-]+)\s+(?P<ty>[\d.-]+)\s+Tm|"
    r"(?P<s>\((?:[^()\\]|\\.)*\))\s*Tj|"
    r"(?P<arr>\[(?:[^\[\]\\]|\\.)*\])\s*TJ")
_STR = re.compile(r"\((?:[^()\\]|\\.)*\)")


def available_backend() -> str:
    """Which backend will be used: ``"pypdf"`` or ``"builtin"``. For the port-time precheck."""
    try:
        import pypdf  # noqa: F401
        return "pypdf"
    except ImportError:
        return "builtin"


def _unescape(s: str) -> str:
    s = re.sub(r"\\([0-7]{1,3})", lambda m: chr(int(m.group(1), 8)), s)   # octal escapes
    return re.sub(r"\\([()\\])", r"\1", s)


def _content_streams(raw: bytes):
    """Yield each decoded content stream that carries text operators.

    Tries ASCII85+Flate (reportlab's default), then bare Flate, then raw — a PDF may use any of
    them, and guessing wrong on one stream must not lose the rest of the document.
    """
    for m in re.finditer(rb"stream(?:\r\n|\r|\n)", raw):
        start = m.end()
        end = raw.find(b"endstream", start)
        if end < 0:
            continue
        blob = raw[start:end].strip()
        for decode in (lambda b: zlib.decompress(base64.a85decode(b, adobe=True)),
                       zlib.decompress,
                       lambda b: b):
            try:
                data = decode(blob)
            except Exception:                        # noqa: BLE001 — wrong filter, try the next
                continue
            if b"Tj" in data or b"TJ" in data:
                yield data
                break


def _page_lines(content: bytes) -> list[str]:
    """One entry per laid-out line — see the module note on why the operator, not the y value."""
    text = content.decode("latin-1")
    parts: list[str | None] = []
    for tok in _TOKENS.finditer(text):
        if tok.group("op") or tok.group("nl") or tok.group("tx") is not None:
            parts.append(None)                        # a positioning operator ends the line
        elif tok.group("s"):
            parts.append(_unescape(tok.group("s")[1:-1]))
        elif tok.group("arr"):
            parts.append("".join(_unescape(p[1:-1]) for p in _STR.findall(tok.group("arr"))))

    lines, cur = [], []
    for p in parts:
        if p is None:
            if cur:
                lines.append("".join(cur))
                cur = []
        else:
            cur.append(p)
    if cur:
        lines.append("".join(cur))

    out = []
    for line in lines:
        for bad, good in _GLYPH.items():
            line = line.replace(bad, good)
        if line.strip():
            out.append(line.rstrip())
    return out


def _builtin_pages(path: Path) -> list[list[str]]:
    return [_page_lines(c) for c in _content_streams(path.read_bytes())]


def _pypdf_pages(path: Path) -> list[list[str]]:
    import pypdf
    reader = pypdf.PdfReader(str(path))
    return [[l.rstrip() for l in (page.extract_text() or "").splitlines() if l.strip()]
            for page in reader.pages]


def extract_pages(path: str | Path, *, backend: str | None = None) -> list[list[str]]:
    """Extract ``[[line, …], …]`` — one list of lines per page. Deterministic; no model.

    ``backend`` forces ``"pypdf"`` or ``"builtin"``; omit to auto-select. A pypdf failure falls
    back to the builtin reader rather than raising: a partial extract is recoverable downstream
    (the operator can see the text is thin), whereas a hard failure ends the run.
    """
    p = Path(path)
    if not p.is_file():
        raise FileNotFoundError(f"no such PDF: {p}")
    chosen = backend or available_backend()
    if chosen == "pypdf":
        try:
            pages = _pypdf_pages(p)
            if any(pages):
                return pages
        except Exception as exc:                      # noqa: BLE001
            print(f"pdf_text: pypdf failed ({exc}); falling back to the builtin reader",
                  file=sys.stderr)
    return _builtin_pages(p)


def extract_lines(path: str | Path, *, backend: str | None = None) -> list[str]:
    """Every line of the document in reading order, pages concatenated."""
    return [line for page in extract_pages(path, backend=backend) for line in page]


def main(argv: list[str] | None = None) -> int:
    import argparse
    ap = argparse.ArgumentParser(
        description="Extract text from a PDF with line structure preserved (feeds pdf_extract).")
    ap.add_argument("pdf", nargs="?", help="path to the staged PDF")
    ap.add_argument("--backend", choices=("pypdf", "builtin"), help="force a backend")
    ap.add_argument("--pages", action="store_true", help="mark page boundaries in the output")
    ap.add_argument("--which", action="store_true", help="print the backend that would be used")
    args = ap.parse_args(argv)

    if args.which:
        print(available_backend())
        return 0
    if not args.pdf:
        ap.error("need a PDF path (or --which)")
    try:
        pages = extract_pages(args.pdf, backend=args.backend)
    except FileNotFoundError as exc:
        print(f"pdf_text.py: {exc}", file=sys.stderr)
        return 2
    if not any(pages):
        print(f"pdf_text.py: no extractable text in {args.pdf} — is it a scanned image? "
              f"Record an [[unreadable: …]] marker rather than treating this as empty.",
              file=sys.stderr)
        return 1
    for i, page in enumerate(pages, 1):
        if args.pages:
            print(f"@@PAGE {i}")
        for line in page:
            print(line)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
