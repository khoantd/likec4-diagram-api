"""Turso database integration using the pyturso package.

This module provides a process-wide Turso connection that can be initialized on
application startup and closed on shutdown. Turso is optional and disabled by
default; enable it via settings when you want to use a remote or local
SQLite-compatible database.
"""

from __future__ import annotations

import os
from typing import Any

from app.core.config import settings

try:
    import turso
    import turso.sync
except ImportError:  # pragma: no cover - guarded by dependency declaration
    turso = None  # type: ignore[assignment]


_turso_conn: Any | None = None


def init_turso() -> None:
    """Initialise a Turso connection if enabled in settings."""
    global _turso_conn

    if not settings.turso_enabled:
        return

    if turso is None:
        raise RuntimeError(
            "Turso support is enabled but the 'pyturso' package is not installed. "
            "Ensure pyturso is in your dependencies."
        )

    if _turso_conn is not None:
        return

    db_path = settings.turso_db_path
    remote_url = settings.turso_remote_url or os.getenv("LIBSQL_URL")
    auth_token = settings.turso_auth_token or os.getenv("LIBSQL_AUTH_TOKEN")

    connect_kwargs: dict[str, Any] = {}
    if remote_url:
        connect_kwargs["remote_url"] = remote_url
    if auth_token:
        connect_kwargs["auth_token"] = auth_token

    _turso_conn = turso.sync.connect(db_path, **connect_kwargs)  # type: ignore[attr-defined]


def get_turso_connection() -> Any:
    """Return the active Turso connection or raise if not initialised."""
    if _turso_conn is None:
        raise RuntimeError("Turso connection is not initialised")
    return _turso_conn


def close_turso() -> None:
    """Close the Turso connection if it is open."""
    global _turso_conn

    conn = _turso_conn
    if conn is None:
        return

    close = getattr(conn, "close", None)
    if callable(close):
        close()
    _turso_conn = None

