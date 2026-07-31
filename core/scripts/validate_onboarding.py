#!/usr/bin/env python3
"""TASK-012 — onboarding validation + freeze-integrity harness.

This is the regression gate that grades the frozen C extractor against the
**human-signed-off** oracle (`fixtures/c_repo/expected_code_map.json`, TASK-005)
and proves the freeze recorded in `core/extractor_manifest.yaml` (D-A22 split;
was §5.2's onboarding_manifest) is honest. It is deterministic and model-free — exactly the property the freeze
exists to guarantee (FR-DC-14): the same fixture in always grades the same way.

What it checks (all HARD unless marked NOTE):

  1. STRUCTURAL match — every oracle file's `path/module/interfaces/depends_on/
     used_by/coverage` equals the extractor's, no missing/extra files. The model
     fields (`purpose`/`tags`) and the volatile top-level fields the SIGNOFF lists
     as ignorable (`commit_sha`/`generated_at`/`seal_id`/`built_with_extractor_sha`)
     are deliberately out of scope.
  2. coverage_report buckets — `files_seen/extracted/fallback/unresolved/coverage`
     equal the oracle, and the buckets sum to `files_seen`.
  3. COVERAGE FLOOR — `coverage >= coverage_floor` read from the manifest (§5.4,
     floor 0.80). A genuinely polyglot/under-covered repo would trip this →
     REONBOARD_FLAG at TASK-013; single-language `fixtures/c_repo` clears it.
  4. unresolved_patterns — the SET OF FILES flagged unresolved must match the
     oracle exactly (HARD). The free-text *prose* of each pattern is compared and
     any drift is reported as a NOTE, not a failure: it is a human-authored
     description, and where the oracle names a symbol differently from the source
     the extractor (reading the real source) is authoritative — surfaced, never
     silently absorbed (mirrors the SIGNOFF D-1/D-2 "recommend patching" stance).
  5. FREEZE INTEGRITY — the `extractor_sha` recorded in the manifest equals the
     live `git hash-object` of `core/extractors/c_extractor.py`. A drift here means
     the frozen artifact was edited after the manifest was written: the cache key
     (§5.3 Branch B) would be stale and the freeze a lie. This is what makes the
     manifest a real freeze record, not a comment.

Run: `python3 core/scripts/validate_onboarding.py` → prints a report, exits 0 on
all-green, 1 on any hard failure. Re-run at TASK-013/036 and any time the
extractor changes; it is the standing regression guard for the freeze.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from core.extractors import (  # noqa: E402  (path set above)
    c_extractor,
    merge_edges,
    normalize,
    partition_by_language,
)

FIXTURE = REPO_ROOT / "fixtures" / "c_repo"
ORACLE = FIXTURE / "expected_code_map.json"
MANIFEST = REPO_ROOT / "core" / "extractor_manifest.yaml"   # per-language freeze (D-A22 split)
EXTRACTOR = REPO_ROOT / "core" / "extractors" / "c_extractor.py"

# Structural fields the extractor owns (§3.3 / §5.5). The model fields
# (`purpose`/`tags`) are TASK-011's and are intentionally excluded from grading.
STRUCT_FIELDS = ("path", "module", "interfaces", "depends_on", "used_by", "coverage")
COVERAGE_REPORT_NUMERIC = ("files_seen", "files_extracted", "files_fallback",
                           "files_unresolved", "coverage")

# Fields that are inherently order-independent (sets); compared as sorted lists so
# a different-but-equivalent emission order is not a false mismatch. This matches
# the signed oracle's intent (it grades *content*, not list order).
_SET_FIELDS = frozenset({"interfaces", "depends_on", "used_by"})

_FILE_IN_PATTERN = re.compile(r"\bin\s+([\w./-]+\.[ch])\b")


def _manifest_scalar(text: str, key: str) -> str | None:
    """Read a single top-level-or-nested scalar from the manifest by key.

    A deliberately minimal reader (the build venv has no YAML parser yet — see
    `core/extractors/__init__.py`): the manifest is flat enough that a
    ``key: value  # comment`` line match is unambiguous for the two scalars this
    harness needs (`coverage_floor`, `extractor_sha`). Returns the first match's
    value with any trailing comment and quotes stripped, or ``None``.
    """
    m = re.search(rf"^\s*{re.escape(key)}:\s*([^\n#]+?)\s*(?:#.*)?$", text, re.MULTILINE)
    if not m:
        return None
    return m.group(1).strip().strip("'\"")


def _norm(field: str, value):
    if field in _SET_FIELDS and isinstance(value, list):
        return sorted(value)
    return value


def _files_flagged(patterns) -> set[str]:
    """The set of source files each unresolved-pattern string names (deterministic)."""
    out: set[str] = set()
    for p in patterns:
        m = _FILE_IN_PATTERN.search(p)
        if m:
            out.add(m.group(1))
    return out


def build_actual():
    """Run the deterministic dispatch over the fixture exactly as the gate would."""
    partitions = partition_by_language(str(FIXTURE))
    raw = c_extractor.run(partitions["c"], str(FIXTURE))
    entries = merge_edges(normalize(raw["entries"]))
    return entries, raw["coverage_report"]


def main() -> int:
    failures: list[str] = []
    notes: list[str] = []

    oracle = json.loads(ORACLE.read_text())
    manifest_text = MANIFEST.read_text() if MANIFEST.exists() else ""
    entries, cov = build_actual()

    # ── 1. structural match ────────────────────────────────────────────────────
    oracle_by_path = {f["path"]: f for f in oracle["files"]}
    got_by_path = {e["path"]: e for e in entries}
    missing = sorted(set(oracle_by_path) - set(got_by_path))
    extra = sorted(set(got_by_path) - set(oracle_by_path))
    if missing:
        failures.append(f"files in oracle but not extracted: {missing}")
    if extra:
        failures.append(f"files extracted but not in oracle: {extra}")
    struct_mismatches = []
    for path, o in oracle_by_path.items():
        g = got_by_path.get(path)
        if g is None:
            continue
        for field in STRUCT_FIELDS:
            if _norm(field, o.get(field)) != _norm(field, g.get(field)):
                struct_mismatches.append((path, field, o.get(field), g.get(field)))
    if struct_mismatches:
        for path, field, ov, gv in struct_mismatches[:20]:
            failures.append(f"struct mismatch {path}.{field}: oracle={ov!r} got={gv!r}")
        if len(struct_mismatches) > 20:
            failures.append(f"... +{len(struct_mismatches) - 20} more struct mismatches")

    # ── 2. coverage_report buckets ─────────────────────────────────────────────
    ocov = oracle["coverage_report"]
    for k in COVERAGE_REPORT_NUMERIC:
        if ocov.get(k) != cov.get(k):
            failures.append(f"coverage_report.{k}: oracle={ocov.get(k)} got={cov.get(k)}")
    bucket_sum = cov["files_extracted"] + cov["files_fallback"] + cov["files_unresolved"]
    if bucket_sum != cov["files_seen"]:
        failures.append(f"buckets {bucket_sum} != files_seen {cov['files_seen']}")

    # ── 3. coverage floor (§5.4) ───────────────────────────────────────────────
    floor_raw = _manifest_scalar(manifest_text, "coverage_floor")
    if floor_raw is None:
        failures.append("coverage_floor not found in extractor_manifest.yaml")
    else:
        floor = float(floor_raw)
        if cov["coverage"] < floor:
            failures.append(f"coverage {cov['coverage']} < floor {floor} (→ REONBOARD_FLAG)")

    # ── 4. unresolved_patterns: file-set HARD, prose drift NOTE ────────────────
    o_files = _files_flagged(ocov.get("unresolved_patterns", []))
    g_files = _files_flagged(cov.get("unresolved_patterns", []))
    if o_files != g_files:
        failures.append(
            f"unresolved files differ: oracle-only={sorted(o_files - g_files)} "
            f"got-only={sorted(g_files - o_files)}"
        )
    o_pat, g_pat = set(ocov.get("unresolved_patterns", [])), set(cov.get("unresolved_patterns", []))
    for p in sorted(o_pat - g_pat):
        notes.append(f"oracle pattern prose not emitted verbatim: {p!r}")
    for p in sorted(g_pat - o_pat):
        notes.append(f"extractor pattern prose (authoritative, reads source): {p!r}")

    # ── 5. freeze integrity ────────────────────────────────────────────────────
    recorded_sha = _manifest_scalar(manifest_text, "extractor_sha")
    live_sha = subprocess.check_output(
        ["git", "hash-object", str(EXTRACTOR)], cwd=REPO_ROOT, text=True
    ).strip()
    if recorded_sha is None:
        failures.append("extractor_sha not found in extractor_manifest.yaml")
    elif not live_sha.startswith(recorded_sha):
        failures.append(
            f"FREEZE DRIFT: manifest extractor_sha={recorded_sha} but live "
            f"git hash-object={live_sha[:len(recorded_sha)]} — extractor edited post-freeze"
        )

    # ── report ─────────────────────────────────────────────────────────────────
    print(f"coverage = {cov['coverage']}  (floor {floor_raw})  "
          f"files {cov['files_seen']} = {cov['files_extracted']} extracted "
          f"+ {cov['files_fallback']} fallback + {cov['files_unresolved']} unresolved")
    print(f"structural fields: {len(oracle_by_path)} files compared, "
          f"{len(struct_mismatches)} mismatches")
    print(f"extractor_sha recorded={recorded_sha} live={live_sha[:7]}")
    for n in notes:
        print(f"  NOTE: {n}")
    if failures:
        print(f"\nFAIL ({len(failures)}):")
        for f in failures:
            print(f"  - {f}")
        return 1
    print("\nPASS — extractor output matches signed oracle; coverage clears floor; freeze honest.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
