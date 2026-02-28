"""Tests for the LikeC4 DSL parse service and endpoint."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app

VALID_DSL = """
specification {
  element actor { style { shape person } }
  element system
}
model {
  user = actor 'User'
  svc  = system 'Service'
  user -> svc 'uses'
}
views {
  view index { include * }
}
"""

INVALID_DSL = "model { badSyntax ??? }"


# ---------------------------------------------------------------------------
# Unit tests for parse_c4()
# ---------------------------------------------------------------------------


def test_parse_c4_raises_when_disabled():
    with patch("app.services.parse.settings") as mock_settings:
        mock_settings.parse_enabled = False
        mock_settings.parse_script_path = "scripts/parse-c4.mjs"
        from app.services.parse import parse_c4
        with pytest.raises(RuntimeError, match="disabled"):
            parse_c4("model {}")


def test_parse_c4_raises_when_script_missing():
    with patch("app.services.parse.settings") as mock_settings:
        mock_settings.parse_enabled = True
        mock_settings.parse_script_path = "/nonexistent/parse-c4.mjs"
        from app.services.parse import parse_c4
        with pytest.raises(RuntimeError, match="not found"):
            parse_c4("model {}")


def test_parse_c4_raises_when_node_not_found(tmp_path):
    # Create a dummy script so the path check passes
    script = tmp_path / "parse-c4.mjs"
    script.write_text("// dummy")

    with (
        patch("app.services.parse.settings") as mock_settings,
        patch("subprocess.run", side_effect=FileNotFoundError),
    ):
        mock_settings.parse_enabled = True
        mock_settings.parse_script_path = str(script)
        from app.services.parse import parse_c4
        with pytest.raises(RuntimeError, match="Node.js"):
            parse_c4("model {}")


def test_parse_c4_returns_valid_on_success(tmp_path):
    script = tmp_path / "parse-c4.mjs"
    script.write_text("// dummy")

    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = json.dumps({"valid": True})
    mock_result.stderr = ""

    with (
        patch("app.services.parse.settings") as mock_settings,
        patch("subprocess.run", return_value=mock_result),
    ):
        mock_settings.parse_enabled = True
        mock_settings.parse_script_path = str(script)
        from app.services.parse import parse_c4
        result = parse_c4(VALID_DSL)
        assert result["valid"] is True
        assert result["errors"] is None


def test_parse_c4_returns_errors_on_invalid(tmp_path):
    script = tmp_path / "parse-c4.mjs"
    script.write_text("// dummy")

    errors = [{"message": "Unexpected token", "line": 1, "sourceFsPath": "source.c4", "range": None}]
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = json.dumps({"valid": False, "errors": errors})
    mock_result.stderr = ""

    with (
        patch("app.services.parse.settings") as mock_settings,
        patch("subprocess.run", return_value=mock_result),
    ):
        mock_settings.parse_enabled = True
        mock_settings.parse_script_path = str(script)
        from app.services.parse import parse_c4
        result = parse_c4(INVALID_DSL)
        assert result["valid"] is False
        assert len(result["errors"]) == 1
        assert result["errors"][0]["message"] == "Unexpected token"


def test_parse_c4_raises_on_nonzero_exit(tmp_path):
    script = tmp_path / "parse-c4.mjs"
    script.write_text("// dummy")

    mock_result = MagicMock()
    mock_result.returncode = 1
    mock_result.stdout = ""
    mock_result.stderr = "something went wrong"

    with (
        patch("app.services.parse.settings") as mock_settings,
        patch("subprocess.run", return_value=mock_result),
    ):
        mock_settings.parse_enabled = True
        mock_settings.parse_script_path = str(script)
        from app.services.parse import parse_c4
        with pytest.raises(RuntimeError, match="exit"):
            parse_c4("model {}")


def test_parse_c4_raises_on_invalid_json(tmp_path):
    script = tmp_path / "parse-c4.mjs"
    script.write_text("// dummy")

    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = "not json"
    mock_result.stderr = ""

    with (
        patch("app.services.parse.settings") as mock_settings,
        patch("subprocess.run", return_value=mock_result),
    ):
        mock_settings.parse_enabled = True
        mock_settings.parse_script_path = str(script)
        from app.services.parse import parse_c4
        with pytest.raises(RuntimeError, match="invalid JSON"):
            parse_c4("model {}")


# ---------------------------------------------------------------------------
# API endpoint tests
# ---------------------------------------------------------------------------


@pytest.fixture
def client():
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


@pytest.mark.asyncio
async def test_parse_endpoint_returns_503_when_disabled(client):
    """When parse is not enabled, endpoint returns 503."""
    with patch("app.services.parse.settings") as mock_settings:
        mock_settings.parse_enabled = False
        mock_settings.parse_script_path = None
        r = await client.post("/api/v1/parse", json={"dsl": "model {}"})
    assert r.status_code == 503
    assert "disabled" in r.json()["detail"].lower() or "parse" in r.json()["detail"].lower()


@pytest.mark.asyncio
async def test_parse_endpoint_rejects_empty_dsl(client):
    r = await client.post("/api/v1/parse", json={"dsl": ""})
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_parse_endpoint_missing_body(client):
    r = await client.post("/api/v1/parse", json={})
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_parse_endpoint_returns_valid(client):
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = json.dumps({"valid": True})
    mock_result.stderr = ""

    with patch("app.services.parse.subprocess.run", return_value=mock_result):
        with patch("app.services.parse.settings") as mock_settings:
            mock_settings.parse_enabled = True
            mock_settings.parse_script_path = __file__  # any existing file path
            r = await client.post("/api/v1/parse", json={"dsl": VALID_DSL})

    assert r.status_code == 200
    data = r.json()
    assert data["valid"] is True
    assert data["errors"] is None


@pytest.mark.asyncio
async def test_parse_endpoint_returns_invalid(client):
    errors = [{"message": "Parse error", "line": 0, "sourceFsPath": "source.c4", "range": None}]
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = json.dumps({"valid": False, "errors": errors})
    mock_result.stderr = ""

    with patch("app.services.parse.subprocess.run", return_value=mock_result):
        with patch("app.services.parse.settings") as mock_settings:
            mock_settings.parse_enabled = True
            mock_settings.parse_script_path = __file__
            r = await client.post("/api/v1/parse", json={"dsl": INVALID_DSL})

    assert r.status_code == 200
    data = r.json()
    assert data["valid"] is False
    assert len(data["errors"]) == 1
    assert data["errors"][0]["message"] == "Parse error"
