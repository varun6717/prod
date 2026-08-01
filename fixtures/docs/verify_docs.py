#!/usr/bin/env python3
"""verify_docs.py — TASK-126 proof: the docs point at things that exist and say things that are true.

Two sweeps, and the first is the one that matters:

  1. **Every repo path a doc names must exist on disk.** Not a grep for a hand-listed set of dead
     names — a dead name nobody thought to list would sail straight through that. Instead: pull
     every backticked token that *looks like a repo path* out of the docs and resolve it. A pointer
     to a file that no longer exists is the actual failure mode, and this catches the ones nobody
     went looking for.
  2. **No doc presents a retired thing as live.** The naive form of this ("the word `BRD` never
     appears") is both unachievable and wrong: a doc *should* say what died, and punishing it for
     saying so would push the retirement notices out of the docs a fresh session reads first. The
     real proposition is narrower — a retired thing may be **named in prose about its retirement**,
     but never as a **backticked identifier on a line that reads as current**, because a backticked
     identifier asserts "this exists."

Then a coherence check: what `CLAUDE.md` and `SKILLS_INDEX.md` assert about the landed build (the
eight roles, the four prompt files) is read back off `overlay_manifest.yaml` and off disk.

Run: python3 fixtures/docs/verify_docs.py
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_REPO_ROOT = _HERE.parents[1]
sys.path.insert(0, str(_REPO_ROOT / "core" / "scripts"))

import yaml  # noqa: E402

_FAILURES: list[str] = []

# The docs a fresh session actually reads to orient itself.
_ORIENTATION = ["CLAUDE.md", "VDI_WIRING.md", "docs/BUILD_OVERVIEW.md", "docs/SKILLS_INDEX.md",
                "docs/design/README.md"]

# Produced BY a run or generated INTO a scaffold — correctly absent from the repo. Naming one is
# not a dangling pointer; it is the doc describing an output. Kept explicit rather than pattern-
# matched so that adding an artifact is a deliberate act.
_RUN_ARTIFACTS = {
    "UI_INPUT.yaml", "index.json", "context_set/index.json", "_slice.json",
    "components.json", "files.json", "code_map/components.json", "code_map/files.json",
    "v1.md", "v2.md", "solution_intent/v1.md", "solution_intent/v2.md",
    "enrichment.json", "solution_intent/enrichment.json", "jira_plan.json", "jira_trace.json",
    "telemetry.jsonl", "decisions.jsonl", "index.yaml", "code_maps/index.yaml",
    "copilot-instructions.md",              # generated into the overlay from one template
    "<doc>.md", "<doc>.index.json",
}
# Not repo files at all.
_EXTERNAL = {"settings.json", "PDLC_Platform_Design_Spec_v1.md", "pdlc_platform_app.html"}

# Retired identifiers. A doc may name these in prose about the retirement; it may not present one
# as a live, backticked identifier.
_RETIRED = ["brd", "frd", "brd_profile", "frd_profile", "brd_author", "frd_author",
            "brd_validator", "frd_validator", "brd_authoring", "frd_authoring", "brd_baseline",
            "vocab_sha", "vocab_gap_flag", "vocab_gap_assess", "vocabulary.payment_brand",
            "code_map.json", "brd_frd_overview.html", "onboarding_manifest.yaml",
            "start-brd", "start-frd", "TASK_VDI.md", "TASK_VDI_BOOTSTRAPS.md"]
_RETIRED_SCOPE = ["CLAUDE.md", "docs/BUILD_OVERVIEW.md", "docs/SKILLS_INDEX.md",
                  "docs/design/README.md"]
# A line carrying one of these is *about* the retirement — naming the dead thing there is correct.
_RETIREMENT_MARKER = re.compile(
    r"retire|superse|deleted|no longer|died|dead|removed|⛔|🗄️|historical|do not (build|recreate)"
    r"|moot|consolidated from|stays deferred|is gone|pre-pivot|pre-ADR-008|BRD/FRD", re.I)

# A backticked token counts as a repo path when it carries a known extension.
_PATHLIKE = re.compile(r"`([A-Za-z0-9_][A-Za-z0-9_./<>*-]*\.(?:md|py|yaml|yml|json|jsx|html|jsonl))`")
_PLACEHOLDER = re.compile(r"[<>*]")


def _check(label: str, ok: bool, detail: str = "") -> None:
    print(f"  [{'PASS' if ok else 'FAIL'}] {label}" + (f" — {detail}" if detail else ""))
    if not ok:
        _FAILURES.append(label)


def _resolve(token: str, doc: Path) -> bool:
    """Repo-root-relative, doc-relative, or a unique tail match anywhere in the tree."""
    if (_REPO_ROOT / token).exists() or (doc.parent / token).exists():
        return True
    hits = [p for p in _REPO_ROOT.rglob(Path(token).name)
            if ".git" not in p.parts and "__pycache__" not in p.parts]
    return any(str(p).endswith(token) for p in hits) or (
        "/" not in token and bool(hits))


def _sweep_paths() -> int:
    total = 0
    for rel in _ORIENTATION:
        doc = _REPO_ROOT / rel
        if not doc.exists():
            _check(f"{rel} exists", False, "the orientation set itself is broken")
            continue
        tokens = set()
        for line in doc.read_text(encoding="utf-8").splitlines():
            for t in _PATHLIKE.findall(line):
                if t in _RUN_ARTIFACTS or t in _EXTERNAL or _PLACEHOLDER.search(t):
                    continue
                # A file the doc itself says is gone is a correct mention, not a pointer.
                if _RETIREMENT_MARKER.search(line):
                    continue
                tokens.add(t)
        dangling = sorted(t for t in tokens if not _resolve(t, doc))
        total += len(tokens)
        _check(f"{rel} — {len(tokens)} live path references, all resolve", not dangling,
               f"dangling: {dangling}")
    return total


def _blocks(text: str):
    """Yield (first_line_no, block_text) over markdown blocks.

    The unit has to be the **block**, not the line: markdown hard-wraps, so a retirement marker and
    the identifier it retires routinely land on different physical lines, and a line-based sweep
    would flag a correct sentence purely for where the wrap fell. A block is too coarse the other
    way round — a bullet list has no blank lines, so one 'retired' bullet would cover the whole
    list. So a list item starts its own block; continuations attach to it; a blank line ends it.
    """
    cur, start = [], 1
    for n, line in enumerate(text.splitlines(), 1):
        starts_item = bool(re.match(r"\s*(?:[-*+]|\d+\.|\||#{1,6} |> )", line))
        if not line.strip() or (starts_item and cur):
            if cur:
                yield start, "\n".join(cur)
            cur, start = ([line], n) if line.strip() else ([], n + 1)
        else:
            if not cur:
                start = n
            cur.append(line)
    if cur:
        yield start, "\n".join(cur)


def _flagged(block: str) -> list[str]:
    """The retired identifiers this block presents as live. THE sweep — the probe calls this too,
    so the demonstration that it has teeth exercises the shipped path, not a lookalike."""
    if _RETIREMENT_MARKER.search(block):
        return []                             # the block is about the retirement — correct
    return [tok for tok in re.findall(r"`([^`]+)`", block)
            if any(re.search(rf"(^|[^A-Za-z0-9_]){re.escape(w)}([^A-Za-z0-9_]|$)", tok, re.I)
                   for w in _RETIRED)]


def _sweep_retired() -> None:
    for rel in _RETIRED_SCOPE:
        bad = [f"L{n}: `{tok}`"
               for n, block in _blocks((_REPO_ROOT / rel).read_text(encoding="utf-8"))
               for tok in _flagged(block)]
        _check(f"{rel} presents no retired identifier as live", not bad, str(sorted(set(bad))[:4]))


def main() -> int:
    print("verify_docs — the docs point at things that exist\n")

    print("1) every live repo path named in an orientation doc resolves:")
    total = _sweep_paths()
    print(f"     {total} live path references checked across {len(_ORIENTATION)} docs")

    print("\n2) no re-cut doc presents a retired identifier as live:")
    _sweep_retired()

    print("\n   (the sweep has teeth — a known-bad line is caught:)")
    live = _flagged("- **Consumes:** `brd_profile.<domain>.yaml` and the accepted `BRD.md`")
    _check("a live `brd_profile` reference IS flagged", len(live) == 2, str(live))
    _check("the same names inside a retirement note are NOT",
           not _flagged("> `brd_author` and `frd_author` no longer exist."))
    _check("and a hard wrap between marker and identifier does not fool it",
           not _flagged("Neither is authoritative; `brd_author`,\n`frd_author` no longer exist."),
           "the block, not the line, is the unit")

    print("\n3) what the docs assert about the build matches the manifest and disk:")
    man = yaml.safe_load((_REPO_ROOT / "core/overlay_manifest.yaml").read_text())
    roles, prompts = [r["name"] for r in man["roles"]], man["prompt_files"]
    idx = (_REPO_ROOT / "docs/SKILLS_INDEX.md").read_text(encoding="utf-8")
    ovw = (_REPO_ROOT / "docs/BUILD_OVERVIEW.md").read_text(encoding="utf-8")

    _check(f"the manifest declares {len(roles)} roles", len(roles) == 8, str(roles))
    _check("SKILLS_INDEX names every role in the manifest",
           not [r for r in roles if f"`{r}`" not in idx],
           str([r for r in roles if f"`{r}`" not in idx]))
    _check("both orientation docs name every prompt file",
           not [p for p in prompts if f"`{p}`" not in idx or f"`{p}`" not in ovw],
           str([p for p in prompts if f"`{p}`" not in idx or f"`{p}`" not in ovw]))
    for r in man["roles"]:
        stem = "code_impact_assess" if r["skill"] == "code_impact" else r["skill"]
        if not (_REPO_ROOT / "core/skills" / f"{stem}.skill.md").exists():
            _check(f"role {r['name']} resolves to a skill file", False, stem)
    _check("every role resolves to a skill file on disk",
           not any("resolves to a skill file" in f for f in _FAILURES))
    _check("the parity check backing the eight-roles claim exists",
           (_REPO_ROOT / "core/scripts/checks/check_overlay_parity.py").exists())

    print("\n4) a fresh session's read order is intact:")
    claude = (_REPO_ROOT / "CLAUDE.md").read_text(encoding="utf-8")
    _check("CLAUDE.md points at TASK_LIST.md as the single task list",
           "`TASK_LIST.md` is the single task list" in claude)
    _check("CLAUDE.md states the publish suspension it would otherwise send you into",
           "SUSPENDED" in claude and "TASK-127" in claude,
           "protocol step 5 suspends publish; CLAUDE.md used to say 're-publish the registry'")
    _check("CLAUDE.md says disk is ground truth", "ground truth" in claude.lower())

    print()
    if _FAILURES:
        print(f"FAILED — {len(_FAILURES)} check(s): {_FAILURES}", file=sys.stderr)
        return 1
    print("PASS — every live repo path named in the orientation docs resolves; no re-cut doc "
          "presents a retired identifier as live; the roles and prompts they assert match the "
          "manifest and disk.")
    return 0



if __name__ == "__main__":
    raise SystemExit(main())
