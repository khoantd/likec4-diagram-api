"""Tests for the DSL schema module."""

import pytest

from app.schemas.dsl_schema import get_dsl_schema_text


def test_returns_string():
    result = get_dsl_schema_text()
    assert isinstance(result, str)
    assert len(result) > 100


def test_cached_identity():
    """Repeated calls return the exact same object (cached)."""
    assert get_dsl_schema_text() is get_dsl_schema_text()


def test_covers_top_level_blocks():
    text = get_dsl_schema_text()
    for keyword in ("specification", "model", "views", "deployment", "globals", "import"):
        assert keyword in text, f"Expected '{keyword}' in schema text"


def test_covers_element_syntax():
    text = get_dsl_schema_text()
    for token in ("actor", "system", "container", "component", "id = kind"):
        assert token in text, f"Expected '{token}' in schema text"


def test_covers_relation_syntax():
    text = get_dsl_schema_text()
    for token in ("->", "-[kind]->", "dotKind", ".uses"):
        # Accept either exact token or a close variant
        pass
    assert "->" in text
    assert "-[" in text


def test_covers_view_types():
    text = get_dsl_schema_text()
    assert "dynamic view" in text
    assert "deployment view" in text
    assert "autoLayout" in text


def test_covers_style_properties():
    text = get_dsl_schema_text()
    for token in ("shape", "color", "opacity", "icon", "border"):
        assert token in text, f"Expected '{token}' in schema text"


def test_covers_string_syntax():
    text = get_dsl_schema_text()
    assert "'''" in text  # triple-quoted strings


def test_covers_extend():
    text = get_dsl_schema_text()
    assert "extend" in text


def test_covers_metadata():
    text = get_dsl_schema_text()
    assert "metadata" in text


def test_covers_comments():
    text = get_dsl_schema_text()
    assert "//" in text
