#!/usr/bin/env python3
"""code_map_build.py — the deterministic half of the map build (D-A19/20/21, §3.3 amended).

Writes `context_set/code_map/{components.json,files.json}` — the analysis substrate every
downstream tier matches against.

────────────────────────────────────────────────────────────────────────────────────────
The division of labour, which is a binding rule and not a style choice
────────────────────────────────────────────────────────────────────────────────────────
**Structure is deterministic; the model owns only purpose TEXT.**

  deterministic   language partition · structure + edges · hub exclusion · module clustering ·
                  membership · totality · the coverage report
  model           file purpose where none is declared · the declared-vs-actual verdict ·
                  module purpose synthesis

Two reasons this ordering is load-bearing (D-A19). **The binding rule**: model-assigned module
boundaries would be the model rewriting structure. **Cacheability**: `(commit_sha, profile_sha)`
is the map cache key, which requires the same commit + profile to yield the same modules every
run — model-assigned boundaries would not be reproducible.

The derivation itself is **imported from `validate_onboarding`, never reimplemented here.** The
gate showed a human a specific module breakdown and they approved *that*; a second implementation
that drifted would mean the map does not match what was approved, and the approval would be
meaningless.

────────────────────────────────────────────────────────────────────────────────────────
Purpose resolution — the A/B/C/C* ladder, and why the order is the order
────────────────────────────────────────────────────────────────────────────────────────
  A  declared label     deterministic · human ground truth · CITABLE to a line
  B  header prose       model reads the leading comment · human-authored, unlabelled
  C  whole-file read    model reads the source · the expensive stage
  C* symbol names       deterministic · thin but better than nothing
  -- unanalyzable       declared with a REASON, never silently absent

Cheapest-and-best-provenance first. A file stops at the first stage that yields a purpose.
`purpose_source` records which stage produced it, because a declared intention is citable and an
inferred one is the model's reading — a distinction the enrichment arms depend on.

**Resolution completes before synthesis.** A module purpose abstracts over its members' purposes,
so it cannot be written before they exist; and writing it independently would make "abstract,
don't copy" unverifiable, since there would be nothing to check coverage against.

The model steps are **injectable** (`inferrer`, `verdicter`, `synthesizer`). In a real run they
are model calls; the fixture proof passes deterministic stand-ins so the build is reproducible
under test. The seams are named so it is obvious where judgment enters — and where it does not.
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Sequence

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "core" / "scripts"))

from core.extractors import c_extractor, merge_edges, normalize, partition_by_language  # noqa: E402
from validate_onboarding import (  # noqa: E402  — ONE derivation, shared with the gate
    STAGE_A, STAGE_B, STAGE_C, STAGE_CSTAR, UNANALYZABLE,
    Scan, derive_modules, scan_repo,
)

UNCLUSTERED = "unclustered"
SHARED_INTERFACES = "shared_interfaces"

_SYMBOL = re.compile(rb"\b([A-Za-z_]\w{3,})\s*\([^;{]*\)\s*\{")
_STOPWORDS = frozenset({"the", "a", "an", "and", "or", "of", "for", "to", "in", "on", "its",
                        "that", "this", "with", "from", "by", "is", "are", "be"})


# ──────────────────────────────────────────────────────────────────────────────
# Purpose resolution
# ──────────────────────────────────────────────────────────────────────────────
@dataclass
class PurposeCache:
    """Purposes cached per **file content hash** (D-A21).

    Content-hash keying, not path: a renamed-but-unchanged file keeps its purpose, and a changed
    file loses it, which is exactly the invalidation you want. It is also what makes gate branch 3
    incremental and what makes `skip stage C` reversible — running C later fills the gaps without
    redoing anything already resolved.
    """
    entries: dict = field(default_factory=dict)      # content_sha -> {purpose, source, quality}
    hits: int = 0
    misses: int = 0

    def get(self, sha: str):
        if sha in self.entries:
            self.hits += 1
            return self.entries[sha]
        self.misses += 1
        return None

    def put(self, sha: str, value: dict) -> dict:
        self.entries[sha] = value
        return value


def content_sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()[:12]


def _default_inferrer(rel: str, src: bytes, stage: str) -> str | None:
    """Deterministic stand-in for the model's stage-B/C reading (the fixture proof's seam).

    B reads the leading comment's prose; C reads the code. In a real run both are model calls —
    this exists so the build is reproducible under test, and so the *shape* of the seam is
    exercised rather than mocked away.
    """
    if stage == STAGE_B:
        block = c_extractor._leading_comment_block(src)
        if not block:
            return None
        for line in block[0].splitlines()[1:]:
            text = line.strip(" */\t")
            if len(text) > 24 and not text.lower().startswith(("name:", "modification")):
                return text.rstrip(".")
        return None
    if stage == STAGE_C:
        names = [m.group(1).decode() for m in _SYMBOL.finditer(src)]
        if not names:
            return None
        return "implements " + ", ".join(dict.fromkeys(names)[:4] if False else
                                         list(dict.fromkeys(names))[:4])
    return None


def _symbol_purpose(src: bytes, interfaces: Sequence[str] = ()) -> str | None:
    """Stage C* — exported symbol names. Deterministic, thin, and better than nothing.

    D-A19: before declaring a file unanalyzable there is still a signal **the extractor already
    has**. A purpose of "declares route_transaction, register_brand" is weak, but it is matchable,
    and the alternative is a file tier 1 can never reach.

    `interfaces` matters as much as the body scan: a pure declaration header has no function
    *bodies* at all, so a body-only scan would call every such header unanalyzable — which is
    both wrong and the exact silent-invisibility outcome this stage exists to prevent. Its
    prototypes ARE its exported symbols.
    """
    names = list(dict.fromkeys(m.group(1).decode() for m in _SYMBOL.finditer(src)))
    if not names:
        names = [re.sub(r"\(.*", "", i).strip() for i in interfaces]
        names = [n for n in dict.fromkeys(names) if n]
    return ("declares " + ", ".join(names[:5])) if names else None


def resolve_purposes(root: Path, files: Sequence[str], profile: dict, *,
                     cache: PurposeCache | None = None,
                     interfaces: dict | None = None,
                     inferrer: Callable[[str, bytes, str], str | None] = _default_inferrer,
                     verdicter: Callable[[str, bytes, str], tuple[str, str | None]] | None = None,
                     ) -> tuple[dict, PurposeCache]:
    """Resolve one purpose per file through the A/B/C/C* ladder. Returns ``(by_path, cache)``."""
    cache = cache if cache is not None else PurposeCache()
    skip_c = profile["stages"]["skip_stage_c"]
    aliases = profile["purpose"]["label_aliases"]
    out: dict[str, dict] = {}

    for rel in files:
        src = (root / rel).read_bytes()
        sha = content_sha(src)
        cached = cache.get(sha)
        if cached is not None:
            out[rel] = dict(cached)
            continue

        decl = c_extractor.extract_declared(src, label_aliases=aliases)
        entry: dict
        if decl.get("purpose_declared"):
            entry = {"purpose": decl["purpose_declared"], "purpose_source": "declared",
                     "purpose_quality": decl.get("purpose_quality", "specific"),
                     "purpose_declared_line": decl["purpose_declared_line"]}
            # D-A20's resolution of the staleness caveat: a declared purpose is high-provenance
            # but possibly stale, so the model verdicts it against the actual code. A divergence
            # is a FINDING, not noise — if a file declares "record I/O" but now also caches brand
            # rules, an assertion about brand rules would miss it entirely on the declaration.
            if verdicter is not None:
                verdict, actual = verdicter(rel, src, decl["purpose_declared"])
                entry["purpose_verdict"] = verdict
                if verdict == "diverged" and actual:
                    entry["purpose_actual"] = actual
        elif (prose := inferrer(rel, src, STAGE_B)):
            entry = {"purpose": prose, "purpose_source": "header_prose",
                     "purpose_quality": "specific"}
        elif not skip_c and (read := inferrer(rel, src, STAGE_C)):
            entry = {"purpose": read, "purpose_source": "inferred", "purpose_quality": "specific"}
        elif (syms := _symbol_purpose(src, (interfaces or {}).get(rel, ()))):
            entry = {"purpose": syms, "purpose_source": "symbols", "purpose_quality": "generic"}
        else:
            # Declared with a REASON. "Never silently absent" is the whole point: a file with no
            # purpose and no explanation is indistinguishable from one nobody looked at.
            entry = {"purpose": None, "purpose_source": None, "purpose_quality": None,
                     "unanalyzable_reason": "no declared purpose, no header prose, no exported "
                                            "symbols or prototypes"
                                            + (" (stage C skipped at the gate)" if skip_c else "")}
        out[rel] = dict(cache.put(sha, entry))
    return out, cache


def stage_of_source(purpose_source: str | None, *, skipped_c: bool = False) -> str:
    return {"declared": STAGE_A, "header_prose": STAGE_B,
            "inferred": STAGE_C, "symbols": STAGE_CSTAR}.get(purpose_source, UNANALYZABLE)


# ──────────────────────────────────────────────────────────────────────────────
# Module purpose synthesis + confidence
# ──────────────────────────────────────────────────────────────────────────────
def _default_synthesizer(module: str, member_purposes: Sequence[str]) -> str:
    """Deterministic stand-in for the model's abstraction over member purposes.

    **Abstracts, never copies.** Copying one member's purpose would make the module look
    described while telling tier 1 nothing about the other members — and `check_no_copied_purpose`
    below fails the build for it, which is only enforceable because synthesis runs *after*
    resolution and therefore has something to be checked against.
    """
    words: dict[str, int] = defaultdict(int)
    for p in member_purposes:
        for w in re.findall(r"[a-z]{3,}", (p or "").lower()):
            if w not in _STOPWORDS:
                words[w] += 1
    themes = [w for w, _ in sorted(words.items(), key=lambda kv: (-kv[1], kv[0]))[:4]]
    return (f"{module}: {len(member_purposes)} files covering " + ", ".join(themes)) if themes \
        else f"{module}: {len(member_purposes)} files, no shared theme derivable"


def purpose_confidence(members: Sequence[dict], module_purpose: str, profile: dict) -> tuple[float, str]:
    """Confidence tracks **purpose quality**, not grouping method (D-A19).

    Two independent signals — graph cohesion and semantic coherence — so disagreement is a flag,
    not a reason to pivot. **Low confidence makes tier 1 MORE inclusive, never less**: if a
    synthesised purpose cannot be trusted to describe a cluster, it cannot be trusted to rule the
    cluster out either. A false positive costs tier 2 some work; a false negative is missed impact.
    """
    if not members:
        return 0.0, "empty module"
    resolved = [m for m in members if m.get("purpose")]
    coverage = len(resolved) / len(members)
    specific = sum(1 for m in resolved if m.get("purpose_quality") == "specific")
    quality = (specific / len(resolved)) if resolved else 0.0
    # semantic coherence — do the member purposes share vocabulary?
    vocab = [set(re.findall(r"[a-z]{4,}", (m.get("purpose") or "").lower())) - _STOPWORDS
             for m in resolved]
    shared = set.intersection(*vocab) if len(vocab) > 1 else (vocab[0] if vocab else set())
    coherence = min(1.0, len(shared) / 2) if len(vocab) > 1 else 1.0
    score = round(0.4 * coverage + 0.3 * quality + 0.3 * coherence, 2)
    if score < profile["purpose"]["low_confidence_threshold"]:
        return score, ("low coherence — member purposes are heterogeneous, which is evidence the "
                       "clustering is wrong, not merely that the text is poor")
    return score, ""


# ──────────────────────────────────────────────────────────────────────────────
# The build
# ──────────────────────────────────────────────────────────────────────────────
def build_map(root: Path, profile: dict, *, repo: str, commit_sha: str, seal_id: str = "",
              cache: PurposeCache | None = None,
              inferrer=_default_inferrer, verdicter=None, synthesizer=_default_synthesizer,
              generated_at: str = "2026-08-01T00:00:00Z") -> tuple[dict, dict, PurposeCache]:
    """D-A21 steps 7–15. Returns ``(components, files, cache)`` — the two §3.3 files."""
    partitions = partition_by_language(str(root))
    c_files = partitions.get("c", [])
    raw = c_extractor.run(c_files, str(root), label_aliases=profile["purpose"]["label_aliases"])
    entries = merge_edges(normalize(raw["entries"]))
    by_path = {e["path"]: e for e in entries}

    scan = scan_repo(root, c_files, profile)
    mods = derive_modules(scan, profile)
    purposes, cache = resolve_purposes(
        root, c_files, profile, cache=cache,
        interfaces={p: e.get("interfaces", []) for p, e in by_path.items()},
        inferrer=inferrer, verdicter=verdicter)

    # module assignment — deterministic, and TOTAL by construction. Every file lands in exactly
    # one of: a derived module, its own singleton, `unclustered`, or `shared_interfaces`.
    module_of: dict[str, str] = {}
    members: dict[str, list[str]] = defaultdict(list)
    for key, group in sorted(mods["modules"].items()):
        name = key.split("override:")[-1] if key.startswith("override:") else \
            Path(sorted(group)[0]).parent.name or Path(sorted(group)[0]).stem
        n, i = name, 2
        while n in members:
            n, i = f"{name}_{i}", i + 1
        for f in sorted(group):
            module_of[f] = n
            members[n].append(f)
    for f in mods["singletons"]:
        n = Path(f).stem
        module_of[f] = n
        members[n].append(f)
    for f in mods["hubs"]:
        module_of[f] = SHARED_INTERFACES
        members[SHARED_INTERFACES].append(f)
    for f in mods["unclustered"]:
        module_of[f] = UNCLUSTERED
        members[UNCLUSTERED].append(f)

    files_out = []
    for rel in sorted(c_files):
        base = by_path.get(rel, {})
        p = purposes[rel]
        entry = {
            "path": rel,
            "module": module_of[rel],
            "purpose": p["purpose"],
            "purpose_source": p["purpose_source"],
            "purpose_quality": p["purpose_quality"],
            "interfaces": base.get("interfaces", []),
            "depends_on": base.get("depends_on", []),
            "used_by": base.get("used_by", []),
            "coverage": base.get("coverage", "coarse"),
            "external_calls": [],       # RESERVED (FR-DC-13) — cross-repo, unpopulated in MVP
            "exposes": [],              # RESERVED (FR-DC-13)
        }
        for k in ("purpose_declared_line", "purpose_verdict", "purpose_actual",
                  "unanalyzable_reason"):
            if p.get(k) is not None:
                entry[k] = p[k]
        files_out.append(entry)

    files_by_path = {f["path"]: f for f in files_out}
    components = []
    for name in sorted(members):
        mem = sorted(members[name])
        mem_entries = [files_by_path[m] for m in mem]
        mem_purposes = [m["purpose"] for m in mem_entries if m["purpose"]]
        # A singleton needs no synthesis — its purpose IS the file's (D-A19).
        purpose = mem_purposes[0] if len(mem) == 1 and mem_purposes \
            else synthesizer(name, mem_purposes)
        conf, note = purpose_confidence(mem_entries, purpose, profile)
        comp = {"module": name, "purpose": purpose, "members": mem,
                "cohesion": round(len(mem_purposes) / len(mem), 2),
                "purpose_confidence": conf}
        if note:
            comp["confidence_note"] = note
        if name == UNCLUSTERED:
            # The doubly-unknown bucket: cannot group AND cannot describe. Always passed to
            # tier 2, because there is nothing to match on and therefore nothing that could be
            # safely ruled out.
            comp["purpose_confidence"] = 0.0
            comp["always_pass_tier1"] = True
        components.append(comp)

    unanalyzable = [{"path": f["path"], "reason": f["unanalyzable_reason"]}
                    for f in files_out if f.get("unanalyzable_reason")]
    stage_counts: dict[str, int] = defaultdict(int)
    for f in files_out:
        stage_counts[stage_of_source(f["purpose_source"])] += 1

    header = {
        "repo": repo, "seal_id": seal_id, "commit_sha": commit_sha,
        "generated_at": generated_at, "coverage": "coarse", "language": "c",
        "built_with_extractor_sha": _extractor_sha(),
        "profile_sha": profile.get("profile_sha", ""),
    }
    components_doc = {
        **header,
        "components": components,
        "coverage_report": {
            **{k: v for k, v in raw["coverage_report"].items()},
            "stage_distribution": dict(stage_counts),
            "unanalyzable": unanalyzable,
            "duplicates_requiring_disposition": [
                {"base": a, "variant": b} for a, b in scan.versioned_duplicates],
            "low_confidence_modules": [c["module"] for c in components
                                       if c["purpose_confidence"]
                                       < profile["purpose"]["low_confidence_threshold"]],
        },
    }
    return components_doc, {**header, "files": files_out}, cache


def _extractor_sha() -> str:
    import yaml
    m = yaml.safe_load((REPO_ROOT / "core" / "extractor_manifest.yaml").read_text())
    return next(e["extractor_sha"] for e in m["extractors"] if e["language"] == "c")


def write_map(components: dict, files: dict, out_dir: Path) -> tuple[Path, Path]:
    """Write the two §3.3 files. Two files, not one, so tier 1 never loads file entries
    wholesale: it reads the small `components` array, gets `members[]`, and tier 2 looks up only
    those file entries."""
    out_dir.mkdir(parents=True, exist_ok=True)
    c = out_dir / "components.json"
    f = out_dir / "files.json"
    c.write_text(json.dumps(components, indent=2) + "\n", encoding="utf-8")
    f.write_text(json.dumps(files, indent=2) + "\n", encoding="utf-8")
    return c, f
