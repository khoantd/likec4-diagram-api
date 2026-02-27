"""Tests for generate API endpoints."""

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app

VIEW_JSON = {
    "nodes": [
        {"id": "alice", "parent": None, "title": "Alice", "children": [], "shape": "person"},
        {"id": "cloud", "parent": None, "title": "Cloud", "children": ["cloud.api"], "shape": "rectangle"},
        {"id": "cloud.api", "parent": "cloud", "title": "API", "children": [], "shape": "rectangle"},
    ],
    "edges": [
        {"source": "alice", "target": "cloud.api", "label": "uses"},
    ],
    "autoLayout": {"direction": "TB"},
}


@pytest.fixture
def client():
    return AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    )


@pytest.mark.asyncio
async def test_generate_d2(client):
    r = await client.post("/api/v1/generate/d2", json=VIEW_JSON)
    assert r.status_code == 200
    assert "direction: down" in r.text
    assert "Alice" in r.text
    assert "Cloud" in r.text
    assert "Api" in r.text


@pytest.mark.asyncio
async def test_generate_mermaid(client):
    r = await client.post("/api/v1/generate/mermaid", json=VIEW_JSON)
    assert r.status_code == 200
    assert "flowchart" in r.text
    assert "Alice" in r.text


@pytest.mark.asyncio
async def test_generate_puml(client):
    r = await client.post("/api/v1/generate/puml", json=VIEW_JSON)
    assert r.status_code == 200
    assert "@startuml" in r.text
    assert "@enduml" in r.text


@pytest.mark.asyncio
async def test_generate_format_param(client):
    r = await client.post("/api/v1/generate/d2", json=VIEW_JSON)
    assert r.status_code == 200
    r2 = await client.post("/api/v1/generate/unknown", json=VIEW_JSON)
    assert r2.status_code == 400
