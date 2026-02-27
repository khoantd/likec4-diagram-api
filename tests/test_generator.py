"""Tests for diagram generator (D2 output matches snapshot-style)."""

import pytest

from app.core.schemas import AutoLayout, ProcessedView, ViewEdge, ViewNode
from app.services.generator import generate_diagram


def _view_two_levels() -> ProcessedView:
    return ProcessedView(
        nodes=[
            ViewNode(id="alice", parent=None, title="Alice", children=[], shape="person"),
            ViewNode(id="bob", parent=None, title="Bob", children=[], shape="person"),
            ViewNode(
                id="cloud",
                parent=None,
                title="Cloud",
                children=["cloud.frontend", "cloud.backend"],
                shape="rectangle",
            ),
            ViewNode(id="cloud.frontend", parent="cloud", title="frontend", children=[], shape="rectangle"),
            ViewNode(id="cloud.backend", parent="cloud", title="Backend", children=[], shape="rectangle"),
        ],
        edges=[
            ViewEdge(source="alice", target="cloud.frontend", label="uses"),
            ViewEdge(source="bob", target="cloud.frontend", label="uses"),
            ViewEdge(source="cloud.frontend", target="cloud.backend", label="requests"),
        ],
        auto_layout=AutoLayout(direction="TB"),
    )


def test_generate_d2_basic():
    view = _view_two_levels()
    out = generate_diagram(view, "d2")
    assert "direction: down" in out
    assert "Alice" in out
    assert "Cloud" in out
    assert "Frontend" in out
    assert "Backend" in out
    assert "Alice -> Cloud.Frontend" in out
    assert "Cloud.Frontend -> Cloud.Backend" in out


def test_generate_d2_unsupported_format():
    view = _view_two_levels()
    with pytest.raises(ValueError, match="Unsupported diagram format"):
        generate_diagram(view, "svg")


def test_generate_mermaid_basic():
    view = _view_two_levels()
    out = generate_diagram(view, "mermaid")
    assert "flowchart TB" in out
    assert "Alice" in out
    assert "Cloud" in out
    assert "Frontend" in out
    assert "Backend" in out


def test_generate_puml_basic():
    view = _view_two_levels()
    out = generate_diagram(view, "puml")
    assert "@startuml" in out
    assert "@enduml" in out
    assert "Alice" in out or "alice" in out
    assert "Cloud" in out
