#!/usr/bin/env python3
"""auth.py — the credential-resolution half of the integration seam (TECH_SPEC §7).

This is the ONE place a per-instance ``auth_ref`` becomes real credentials. All secret
handling is isolated here (NFR-09): connectors (``clone.py``, ``ingest_sharepoint.py``)
and skills reference a source's ``auth_ref`` and never touch the secret themselves.

Contract (TASK-052 / §7.1, FR-DC-12):

  * ``auth_context(service)``    — normative §7.1 entry point. ``service`` is one of
                                   ``{bitbucket, sharepoint, confluence, jira}``. Resolves
                                   credentials from the active secret backend and returns
                                   an :class:`AuthHandle`.
  * ``resolve_auth(auth_ref)``   — the consumer-facing wrapper called by the connectors.
                                   Parses the ``jpmc_adapters:<service>`` pointer and
                                   delegates to ``auth_context``. ``None``/absent → ``None``
                                   (ambient credentials / local paths — the documented
                                   external-build passthrough).

Three invariants this module enforces (FR-DC-12):

  1. **Secret in, pointer out.** A resolved secret is reachable only via
     :meth:`AuthHandle.reveal`. The handle's ``repr``/``str`` and :meth:`AuthHandle.pointer`
     are redacted, so logging a handle — or recording it in a descriptor/ledger/telemetry
     — can never leak the secret. ``auth_ref`` is the only thing that lands in artifacts.
  2. **Fail loud, named.** A missing/empty secret raises :class:`AuthResolutionError`
     naming the service and the exact key that was looked up — never a silent ``None``
     that degrades to anonymous access.
  3. **Pluggable backend.** The secret source is swappable without touching callers:
     env vars now (``EnvSecretBackend``), the JPMC secret store at VDI port — bound behind
     the *same* ``auth_ref`` via :func:`set_backend`. Nothing else in the codebase changes.

Backend selection (external build): ``EnvSecretBackend`` reads, per service,
``PDLC_AUTH_<SERVICE>`` (the secret/token, required) and ``PDLC_AUTH_<SERVICE>_USER``
(the username, optional — e.g. a Bitbucket app-password username). For real external
Bitbucket testing you set ``PDLC_AUTH_BITBUCKET`` (+ ``_USER`` if needed) and the connector
clones through the resolved handle; the VDI port swaps the backend, not the env names.
"""
from __future__ import annotations

import os
from typing import Protocol, runtime_checkable

# The services the seam knows how to authenticate (§7.1). ``jira`` is listed for the
# deferred 5B push; the slice-1 connectors use bitbucket/sharepoint/confluence.
SERVICES = ("bitbucket", "sharepoint", "confluence", "jira")

# The ``auth_ref`` namespace prefix every pointer carries (e.g. ``jpmc_adapters:bitbucket``).
_AUTH_REF_PREFIX = "jpmc_adapters:"

_REDACTED = "***REDACTED***"


class AuthResolutionError(RuntimeError):
    """Raised when an ``auth_ref`` cannot be resolved to a usable secret.

    The message names the service and the key that was looked up (never the value) so a
    misconfiguration fails the run loudly and points at the fix — without leaking anything.
    """


@runtime_checkable
class SecretBackend(Protocol):
    """A pluggable secret source. ``get`` returns the raw secret for ``key`` or ``None``.

    The env backend is the external-build default; the VDI port supplies a backend that
    reads the JPMC secret store. Callers never see the backend — only :class:`AuthHandle`.
    """

    def get(self, key: str) -> str | None: ...  # pragma: no cover - interface


class EnvSecretBackend:
    """Reads secrets from environment variables — the external-build default backend.

    Lookup key ``<SERVICE>`` maps to env var ``PDLC_AUTH_<SERVICE>`` (uppercased). The
    secret never appears in code or artifacts; it lives only in the process environment.
    """

    PREFIX = "PDLC_AUTH_"

    def _var(self, key: str) -> str:
        return f"{self.PREFIX}{key.upper()}"

    def get(self, key: str) -> str | None:
        val = os.environ.get(self._var(key))
        return val if val else None  # treat empty string as absent (fail loud upstream)


# Module-level active backend. ``set_backend`` swaps it (VDI port / tests) without
# touching any caller. Default: env vars (external build).
_backend: SecretBackend = EnvSecretBackend()


def set_backend(backend: SecretBackend) -> None:
    """Install the active secret backend (VDI port binds the JPMC store; tests inject a stub).

    This is the single swap point that re-homes every ``auth_ref`` from env vars to the
    real secret store. No connector or skill changes — the seam is the only thing that moves.
    """
    global _backend
    _backend = backend


def get_backend() -> SecretBackend:
    """Return the active secret backend (introspection / test restore)."""
    return _backend


class AuthHandle:
    """A resolved credential — secret-safe by construction.

    The secret is name-mangled and reachable only through :meth:`reveal`. Every other
    surface (``repr``, ``str``, :meth:`pointer`) is redacted, so a handle is safe to log
    or record: the secret cannot leak through stringification or serialization (FR-DC-12).
    """

    __slots__ = ("service", "username", "source", "__secret")

    def __init__(self, service: str, secret: str, *, username: str | None = None, source: str = "env") -> None:
        self.service = service
        self.username = username
        self.source = source           # provenance label (e.g. "env", "jpmc_store") — not the secret
        self.__secret = secret

    def reveal(self) -> str:
        """Return the raw secret. The ONLY accessor; call it at the point of use, never log it."""
        return self.__secret

    def pointer(self) -> dict:
        """A redacted, artifact-safe view — what *may* be recorded (secret stays masked)."""
        return {
            "service": self.service,
            "username": self.username,
            "source": self.source,
            "secret": _REDACTED,
        }

    def __repr__(self) -> str:
        return f"AuthHandle(service={self.service!r}, username={self.username!r}, source={self.source!r}, secret={_REDACTED})"

    __str__ = __repr__


def _service_of(auth_ref: str) -> str:
    """Parse ``jpmc_adapters:<service>`` → ``<service>`` (validated). Fail loud on a bad ref."""
    if not auth_ref.startswith(_AUTH_REF_PREFIX):
        raise AuthResolutionError(
            f"auth_ref {auth_ref!r} is not in the {_AUTH_REF_PREFIX!r} namespace "
            f"(expected e.g. {_AUTH_REF_PREFIX}bitbucket)"
        )
    service = auth_ref[len(_AUTH_REF_PREFIX):]
    if service not in SERVICES:
        raise AuthResolutionError(
            f"unknown service {service!r} in auth_ref {auth_ref!r}; known: {', '.join(SERVICES)}"
        )
    return service


def auth_context(service: str) -> AuthHandle:
    """Resolve credentials for ``service`` from the active backend (normative §7.1).

    Returns an :class:`AuthHandle`. Raises :class:`AuthResolutionError`, naming the
    service and the looked-up key, if no secret is configured — never a silent fallback.
    """
    if service not in SERVICES:
        raise AuthResolutionError(f"unknown service {service!r}; known: {', '.join(SERVICES)}")

    backend = _backend
    secret = backend.get(service)
    if not secret:
        # Name the fix without leaking anything. For the env backend, that's the env var.
        where = getattr(backend, "_var", lambda k: k)(service) if isinstance(backend, EnvSecretBackend) else f"backend key {service!r}"
        raise AuthResolutionError(
            f"no secret configured for service {service!r} (looked up {where}); "
            f"set it before resolving this auth_ref"
        )

    username = None
    if isinstance(backend, EnvSecretBackend):
        username = os.environ.get(f"{backend._var(service)}_USER") or None
    source = "env" if isinstance(backend, EnvSecretBackend) else type(backend).__name__
    return AuthHandle(service, secret, username=username, source=source)


def resolve_auth(auth_ref: str | None) -> AuthHandle | None:
    """Resolve a source's ``auth_ref`` to an :class:`AuthHandle` (consumer-facing wrapper).

    ``None``/empty ``auth_ref`` → ``None``: the external-build passthrough for ambient git
    credentials or local paths (a local bare-repo "Bitbucket" needs no secret). A present
    ``jpmc_adapters:<service>`` pointer is parsed and resolved via :func:`auth_context`;
    a malformed/unknown ref or a missing secret raises :class:`AuthResolutionError`.

    The return value carries the secret only inside the handle (via :meth:`AuthHandle.reveal`);
    callers record ``auth_ref`` as a pointer, never the handle's secret (FR-DC-12).
    """
    if not auth_ref:
        return None
    return auth_context(_service_of(auth_ref))
