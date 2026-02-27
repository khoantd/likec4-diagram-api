"""Turso database integration using the pyturso package.

This module provides a process-wide Turso connection that can be initialized on
application startup and closed on shutdown. Turso is optional and disabled by
default; enable it via settings when you want to use a remote or local
SQLite-compatible database.
"""

from __future__ import annotations

import os
from datetime import datetime
from typing import Any

from app.core.config import settings
from app.core.schemas import AIRequestLog

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

    conn = turso.sync.connect(db_path, **connect_kwargs)  # type: ignore[attr-defined]
    _ensure_schema(conn)
    _turso_conn = conn


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


def _ensure_schema(conn: Any) -> None:
    """Create required tables if they do not exist and migrate schema as needed."""
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS ai_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            prompt TEXT NOT NULL,
            hint TEXT,
            model TEXT NOT NULL,
            business_domain TEXT,
            likec4_dsl TEXT,
            explanation TEXT,
            success INTEGER NOT NULL DEFAULT 1,
            error TEXT,
            created_at TEXT NOT NULL,
            client_ip TEXT,
            geo TEXT
        )
        """
    )
    # For existing databases that might miss the new columns, add them if needed
    try:
        columns = {row[1] for row in conn.execute("PRAGMA table_info(ai_requests)")}
        if "business_domain" not in columns:
            conn.execute("ALTER TABLE ai_requests ADD COLUMN business_domain TEXT")
        if "client_ip" not in columns:
            conn.execute("ALTER TABLE ai_requests ADD COLUMN client_ip TEXT")
        if "geo" not in columns:
            conn.execute("ALTER TABLE ai_requests ADD COLUMN geo TEXT")
    finally:
        conn.commit()


def log_ai_request(
    *,
    prompt: str,
    hint: str | None,
    model: str,
    business_domain: str | None = None,
    likec4_dsl: str | None,
    explanation: str | None,
    success: bool,
    error: str | None = None,
    client_ip: str | None = None,
    geo: str | None = None,
) -> None:
    """
    Persist a single AI generation request/response into Turso when enabled.

    This is a best-effort logger: failures are silently ignored so that
    the main API flow is never affected by logging issues.
    """
    if not settings.turso_enabled or turso is None:
        return

    try:
        conn = get_turso_connection()
    except RuntimeError:
        return

    created_at = datetime.utcnow().isoformat(timespec="seconds") + "Z"
    try:
        conn.execute(
            """
            INSERT INTO ai_requests (
                prompt,
                hint,
                model,
                business_domain,
                likec4_dsl,
                explanation,
                success,
                error,
                created_at,
                client_ip,
                geo
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                prompt,
                hint,
                model,
                business_domain,
                likec4_dsl,
                explanation,
                1 if success else 0,
                error,
                created_at,
                client_ip,
                geo,
            ),
        )
        conn.commit()
    except Exception:
        # Logging must never break the main request flow
        return


def list_ai_requests(*, limit: int = 50, offset: int = 0) -> list[AIRequestLog]:
    """
    Retrieve AI request/response records from the database, newest first.

    Raises RuntimeError when the Turso connection is not initialised.
    """
    if not settings.turso_enabled or turso is None:
        raise RuntimeError("Turso database logging is not enabled")

    conn = get_turso_connection()
    rows = list(
        conn.execute(
            """
            SELECT
                id,
                prompt,
                hint,
                model,
                business_domain,
                likec4_dsl,
                explanation,
                success,
                error,
                created_at,
                client_ip,
                geo
            FROM ai_requests
            ORDER BY id DESC
            LIMIT ? OFFSET ?
            """,
            (limit, offset),
        )
    )

    return [
        AIRequestLog(
            id=row[0],
            prompt=row[1],
            hint=row[2],
            model=row[3],
            business_domain=row[4],
            likec4_dsl=row[5],
            explanation=row[6],
            success=bool(row[7]),
            error=row[8],
            created_at=row[9],
            client_ip=row[10],
            geo=row[11],
        )
        for row in rows
    ]

