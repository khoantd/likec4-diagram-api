"""Parse/validate LikeC4 DSL source via the Node.js parse-c4.mjs script."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import TypedDict

from app.core.config import settings


class ParseError(TypedDict):
    message: str
    line: int
    sourceFsPath: str
    range: dict | None


class ParseResult(TypedDict):
    valid: bool
    errors: list[ParseError] | None


def _resolve_script_path() -> Path | None:
    """Return an absolute Path to the Node parse script, or None if not configured."""
    raw = settings.parse_script_path
    if not raw:
        return None
    p = Path(raw)
    if not p.is_absolute():
        # Resolve relative to the directory that contains this file (app/services/)
        # → go up two levels to the project root (likec4-diagram-api/)
        base = Path(__file__).parent.parent.parent
        p = base / p
    return p


def parse_c4(dsl: str) -> ParseResult:
    """Validate LikeC4 DSL by calling the Node.js parse script.

    Returns a ParseResult dict: ``{"valid": True}`` or
    ``{"valid": False, "errors": [...]}``.

    Raises:
        RuntimeError: when parse is disabled, the script is not found,
                      Node.js is unavailable, the process times out, or
                      the script output cannot be parsed as JSON.
    """
    if not settings.parse_enabled:
        raise RuntimeError(
            "LikeC4 parse is disabled. "
            "Set LIKEC4_API_PARSE_ENABLED=true and configure LIKEC4_API_PARSE_SCRIPT_PATH."
        )

    script_path = _resolve_script_path()
    if script_path is None:
        raise RuntimeError(
            "Parse script path is not configured. "
            "Set LIKEC4_API_PARSE_SCRIPT_PATH to the path of parse-c4.mjs "
            "(e.g. scripts/parse-c4.mjs relative to the project root)."
        )
    if not script_path.exists():
        raise RuntimeError(
            f"Parse script not found: {script_path}. "
            "Ensure the monorepo has been installed (pnpm install) and the script exists."
        )

    try:
        result = subprocess.run(
            ["node", str(script_path)],
            input=dsl,
            capture_output=True,
            text=True,
            timeout=30,
        )
    except FileNotFoundError as exc:
        raise RuntimeError(
            "Node.js is not installed or not on PATH. "
            "Parse requires Node.js ≥18 to be available."
        ) from exc
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError("Parse timed out after 30 seconds.") from exc

    if result.returncode != 0:
        stderr = result.stderr.strip() if result.stderr else "(no stderr)"
        raise RuntimeError(
            f"Parse script exited with code {result.returncode}. stderr: {stderr}"
        )

    stdout = result.stdout.strip()
    if not stdout:
        stderr = result.stderr.strip() if result.stderr else "(no stderr)"
        raise RuntimeError(
            f"Parse script produced no output. stderr: {stderr}"
        )

    try:
        data = json.loads(stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError(
            f"Parse script returned invalid JSON: {exc}. output: {stdout[:200]}"
        ) from exc

    if "valid" not in data:
        raise RuntimeError(f"Parse script response missing 'valid' field: {stdout[:200]}")

    return ParseResult(valid=data["valid"], errors=data.get("errors"))
