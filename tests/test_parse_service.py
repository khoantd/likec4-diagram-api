"""Unit tests for the parse_c4() service (no FastAPI app import required)."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest

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
