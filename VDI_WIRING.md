# VDI_WIRING.md — environment wiring Copilot performs on the JPMC VDI

**What this is.** The list of **environment-specific actions** that cannot be built or tested in the
external Claude Code repo: filling real API calls, binding auth to the JPMC secret store, setting env
vars, verifying live endpoints.

**What this is NOT.** A task list. It contains **no specifications** — every placeholder named here was
*already built, tested, and proven offline* by a task in `TASK_LIST.md`. A VDI item only says *"fill this
named function with the real call."*

---

## The disjointness rule (read this before adding anything)

| | `TASK_LIST.md` | `VDI_WIRING.md` (this file) |
|---|---|---|
| Contains | what gets **built** — generic, testable externally | what gets **wired** — environment-specific, untestable externally |
| Example | build `ingest_jira.py` with a `_fetch_issue` placeholder, a mock fixture, and a verify script | fill `_fetch_issue` with the real Jira REST call; set `PDLC_AUTH_JIRA` |
| Specs live | here | **also there** — an item below merely *names* the placeholder |

**No task appears in both lists. A VDI item is never a spec.**

> **Why this rule is stated so bluntly.** A previous `TASK_VDI.md` existed in this repo and was **deleted
> on 2026-07-29** because it drifted: it claimed "the full canonical spec is in `TASK_LIST.md`" — which
> was **false for four tasks** — and the checkbox truth had silently migrated into the VDI file. Two files
> specifying the same tasks, neither complete, and a fresh session reading either one got a wrong answer.
> Splitting by *kind of work* rather than by *audience* is what prevents the repeat: neither list is the
> canonical source for the other's items, so there is nothing to drift.

If you find yourself writing acceptance criteria, a fixture, or a design rationale in this file — **stop.**
That belongs in `TASK_LIST.md`, and its absence there is the real bug.

---

## Hard rule S — the edit-in-place discipline

Generic code is built and proven externally. Every real API/secret call is **isolated in its own
function** carrying a `[TBD — VDI]` placeholder that raises `NotImplementedError`, plus an **offline
local-path convenience** so the piece runs end-to-end without the real endpoint.

On the VDI you **edit that one placeholder function in place** — no `/vdi` plugin folder, no auto-load
hook, no separation. Keeping each env-specific call in its own function is what makes the edit
collision-free against future generic changes.

*(V decision 2026-06-30; extended to the ADR-008 design as D-A24.)*

---

## Connectors — fill the placeholder

Each item: **one function, one file.** The surrounding connector, its descriptor contract, its mock
fixture and its verify script already exist and are green offline.

- [ ] **SharePoint — PDF download**
  - Fill `core/scripts/ingest_sharepoint.py :: _download_pdf`
  - Mock it replaces: `fixtures/pdf/`, `fixtures/sharepoint/`
  - **PDFs always arrive via SharePoint** — the `file` source type is local-testing-only, never production
  - Verify: `fixtures/sharepoint/verify_sharepoint.py`

- [ ] **Confluence — page fetch**
  - Fill `core/scripts/ingest_confluence.py :: _fetch_confluence`
  - Mock it replaces: `fixtures/confluence/*.html`
  - Verify: `fixtures/confluence/verify_confluence.py`

- [ ] **Bitbucket — repo clone**
  - `core/scripts/clone.py` through the resolved auth seam
  - Mock it replaces: `fixtures/c_repo/`, `fixtures/code_clone/`

- [ ] **Jira — issue fetch** *(new source type, ADR-008 / D-A12 `Prior Artifact`)*
  - Fill `core/scripts/ingest_jira.py :: _fetch_issue`
  - Mock it replaces: `fixtures/jira/PBI-*.json`
  - Verify: `fixtures/jira/verify_jira.py`
  - Note the shape difference from the document connectors: `_fetch_issue` **returns the parsed
    payload dict**, it does not write bytes to a path. Rendering the payload to the staged `.md`
    is deterministic, shared, and already proven offline — so the VDI edit stays a pure
    "make the network call" change

- [ ] **Jira — push** *(the only external mutation of a run; gated by G3)*
  - Fill `core/adapters/jpmc_adapters/jira.py :: _create_issue` **and** `:: _update_issue`
  - Mock it replaces: the local stub target injected via `set_target()`
  - Verify: `fixtures/jira_push/verify_jira_push.py`
  - **Everything around the two calls is real and proven offline**: push order (parent before
    child), parent linking, idempotency by `local_id`, the G3 authorization gate, the trace, and
    the secret-leak scan. The VDI edit is two REST calls and nothing else
  - Both must **raise on non-2xx**. A silent failure leaves the trace claiming an issue exists
    that does not — and the next re-push would "update" a key that was never created

## Auth — bind to the real secret store

- [ ] Bind `auth_ref` resolution in `core/adapters/jpmc_adapters/auth.py` to the **real JPMC secret
      store** (external build resolves from env vars)
- [ ] Set as **user** env vars so runs inherit them: `PDLC_AUTH_SHAREPOINT` (+ `_USER`),
      `PDLC_AUTH_CONFLUENCE`, `PDLC_AUTH_BITBUCKET` (+ `_USER`), `PDLC_AUTH_JIRA`
- [ ] Confirm no secret ever lands on disk — `auth_ref` is a pointer, resolved at call time

## Environment

- [ ] Python deps importable: `httpx`, `PyYAML`; extractor work also needs `tree-sitter==0.25.2` +
      `tree-sitter-c==0.24.2` (ADR-001). Check: `python -c "import httpx, yaml"`
- [ ] Registry repo on branch `feature/pdlc_app`; Stratus code on `feature/c_repo`
- [ ] Re-publish after any `core/` change:
      `python core/scripts/publish_registry.py <registry-url> --branch feature/pdlc_app`
- [ ] Rebuild the SPA (`vite build`) when UI source changes — `dist/` is otherwise stale

## Live-endpoint verification

Each connector's verify script passes offline against its mock. On the VDI, re-run it against the **live**
endpoint and confirm the descriptor shape is byte-identical to the mock run — descriptor parity is the
contract downstream depends on.

- [ ] SharePoint · [ ] Confluence · [ ] Bitbucket · [ ] Jira fetch · [ ] Jira push (stub target first)

## Port notes carried from the external build

- ~~JPMC-side D5 table (TASK-061 fix)~~ — **moot**: ADR-008 retires the vocabulary (D-A22)
- ~~JPMC-side §6.6.3/§10.5 `docs_pipeline` routing extension (TASK-063B)~~ — **moot**: tag-lane
  routing retired (D-A19); routing is by operator disposition
- [ ] JPMC-side D9 needs the `start-ingest` amendment — start gesture → `start-ingest`, which now
      surfaces `start-si` (re-pointed at TASK-102)
- [ ] **ADR-008 re-cut, whole** — carry across at port time: `REQUIREMENTS.md` v2 (D11) +
      `TECH_SPEC.md` amendments (Phase B), the accepted ADR-008, `ADR-008-impact-analysis.md`
      (Phase C), and the rebuilt `TASK_LIST.md`/this file (Phase D)

---

> **Done means:** the placeholder function contains the real call · the connector's verify script is green
> against the **live** endpoint · the descriptor shape is unchanged from the mock run · no secret on disk ·
> `build_checks.py` green · registry re-published.
