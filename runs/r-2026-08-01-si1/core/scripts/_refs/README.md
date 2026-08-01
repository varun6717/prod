# core/scripts/_refs/ — connector reference implementations

Drop **non-secret, illustrative** API examples here that a connector's VDI placeholder is
modeled on. They are *reference material*, not executed by the pipeline — the real wiring
lives in the connector itself. This dir travels with the registry, so the reference is
available wherever the connector runs.

## SharePoint (V-07)

Place the tenant's working SharePoint/Graph fetch example at:

    core/scripts/_refs/sharepoint_graph_reference.py

It is the model for `core/scripts/ingest_sharepoint.py` → `_download_pdf(url, handle, target)`
(the `[TBD — VDI]` placeholder). When you implement `_download_pdf`, mirror this file's:

- auth header construction (`Authorization: Bearer <token>`),
- site / drive / item → download-URL resolution,
- streamed byte download.

## Rules

- **No secrets.** Tokens, passwords, and tenant secrets must NOT live here — this dir is
  published with the registry. The live credential comes only from the auth seam
  (`handle.reveal()`), never from a file.
- **Reference only.** Nothing here is imported or run by the spine; it documents *how*, the
  connector does *what*.
