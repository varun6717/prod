"""jpmc_adapters — the single external-integration seam (TECH_SPEC §7).

This package is the ONLY module that imports a credential/secret SDK and the only
external mutation point (NFR-09). Skills, connectors, and scripts never see raw
credentials; they reference a source's ``auth_ref`` and resolve it here.

Slice-1 ships the auth resolver (``auth.py``). The Jira write interface (``jira.py``,
§7.1) is deferred to Milestone 5B with G3.
"""
