#!/usr/bin/env python3
"""dispositions.py — the D-A12 disposition taxonomy (§3.1 amendment, FR-DC-24).

A **disposition** declares the role an input artifact plays *in this run*. It is
orthogonal to source **type**: type is *where it came from* (`sharepoint`, `confluence`,
`bitbucket`, `jira`), disposition is *what it is for*. Before ADR-008 the doc/code class
was **derived** from type; D-A12 makes it **operator-declared**, because the same PDF is a
`business_requirement` in one run and a `technical_specification` in the next.

One definition, four consumers — this module exists so they cannot drift:
  - ``app/backend/validation.py``      — rejects an unknown/missing disposition at POST time
  - ``core/scripts/merge_manifest.py`` — rejects a manifest entry with no valid disposition at
                                         fan-in (an unroutable entry is one silently never read)
  - ``core/scripts/checks/…`` (§10.5′) — asserts every class the UI offers is routed by the
                                         SI profile's D-A13 matrix (TASK-108)
  - the SI profile / routing matrix     — ``classes`` per section keys on these exact strings

Two rules the taxonomy itself encodes (D-A12):
  - **`codebase` is auto-set, never operator-chosen.** It is the one disposition derivable
    from type (a repo URL), and it routes down the code arm rather than the doc arm.
  - **`other` is second-class.** Readable by the discovery pass, but **never valid as the
    sole citation for a claim** — a fallback class with no routing rule would either do
    nothing silently or pollute every section. Frequent use of `other` is the signal to add
    a class, not evidence that `other` works.

Multi-disposition is allowed (a 200-page architecture doc containing three pages of
requirements is real) but defaults to one, so the narrowing disposition exists to provide
survives.
"""
from __future__ import annotations

# Operator-selectable in the UI, in the order D-A12 presents them.
OPERATOR_DISPOSITIONS: tuple[str, ...] = (
    "business_requirement",        # the ask: mandates, BRDs — obligation, scope, deadline
    "technical_specification",     # normative detail: network specs, tech letters, field formats
    "product_domain_knowledge",    # how the product works today: KB, product guides
    "architecture",                # system design: architecture docs, diagrams, integration maps
    "prior_artifact",              # decisions already made: Jira epics, previous SIs (reference-only)
    "other",                       # background context only — never a sole citation
)

# Auto-set for code sources; not offered to the operator, not editable.
CODEBASE_DISPOSITION = "codebase"

ALL_DISPOSITIONS: tuple[str, ...] = OPERATOR_DISPOSITIONS + (CODEBASE_DISPOSITION,)

# Source types whose disposition is auto-set to `codebase` (D-A12; matches §10.4's code types).
CODE_SOURCE_TYPES: frozenset[str] = frozenset({"bitbucket"})

# Never the primary citation for a *new* claim (D-A12 "two consequences"). `prior_artifact`
# carries the copy-instead-of-derive hazard; `other` is background only. Enforced by the
# authoring/validator skills at cite time, declared here so there is one list.
NON_PRIMARY_DISPOSITIONS: frozenset[str] = frozenset({"prior_artifact", "other"})

# Classes that appear in NO cell of the D-A13 routing matrix, by design. `other` is background
# context only: never primary, never supporting — "the empty column IS the definition" (D-A12).
#
# This is declared here rather than special-cased inside the §10.5′ check for one reason: that
# check's whole job is to catch an orphan class (one the UI offers but nothing routes). An
# exception buried in the checker would be indistinguishable from the bug it hunts. Recording
# it as data means the check reports what it excluded and why, and adding a second never-routed
# class is a data edit that stays visible.
NEVER_ROUTED: frozenset[str] = frozenset({"other"})

# The non-disposition input sources of the D-A13 matrix — the OPERATOR, in two forms. They are
# not dispositions and never appear on a manifest entry, which is why the SI profile keeps them
# under `inputs:` rather than `classes:`. Frame is one text, up front, global in effect;
# discovery is many answers, elicited per section, accruing during authoring.
NON_DISPOSITION_INPUTS: tuple[str, ...] = ("frame", "discovery")


def default_for(source_type: str) -> list[str]:
    """The disposition a source of ``source_type`` starts with.

    Code sources are auto-set (non-editable). Doc types get a sensible operator default that
    the UI lets them change — never a guess the pipeline relies on.
    """
    if source_type in CODE_SOURCE_TYPES:
        return [CODEBASE_DISPOSITION]
    return [_DOC_DEFAULTS.get(source_type, "business_requirement")]


# Per-doc-type starting selection. Deliberately data, not a branch: adding a source type is
# a dict entry. These are *defaults the operator overrides*, never a classification.
_DOC_DEFAULTS: dict[str, str] = {
    "sharepoint": "business_requirement",      # the mandate/BRD lane in practice
    "file": "business_requirement",            # local-testing twin of sharepoint
    "confluence": "product_domain_knowledge",  # KB pages describe steady state
    "jira": "prior_artifact",                  # decisions already made (TASK-107)
}
