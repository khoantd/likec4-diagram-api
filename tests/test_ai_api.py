"""Tests for AI-powered LikeC4 generation endpoint."""

from unittest.mock import patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app

SAMPLE_DSL = """model {
  user = actor 'User' 'End user'
  app = system 'My App' {
    api = container 'API' 'REST API'
  }
  user -> app.api 'uses'
}

views {
  view index {
    title 'System'
    include *
  }
}
"""


@pytest.fixture
def client():
    return AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    )


@pytest.mark.asyncio
async def test_ai_generate_returns_503_when_not_configured(client):
    """When AI is not enabled or no API key, endpoint returns 503."""
    r = await client.post(
        "/api/v1/ai/generate",
        json={"prompt": "A user and a web app with an API"},
    )
    assert r.status_code == 503
    data = r.json()
    assert "detail" in data
    assert "not configured" in data["detail"].lower() or "AI" in data["detail"]


@pytest.mark.asyncio
async def test_ai_generate_validates_request(client):
    """Empty or missing prompt is rejected."""
    r = await client.post("/api/v1/ai/generate", json={})
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_ai_generate_success_with_mock(client):
    """When AI is configured and mock returns content, endpoint returns 200 and DSL."""
    mock_message = type("Message", (), {"content": SAMPLE_DSL})()
    mock_choice = type("Choice", (), {"message": mock_message})()
    mock_response = type("Response", (), {"choices": [mock_choice]})()

    with (
        patch("app.api.v1.ai_endpoints.settings") as mock_settings,
        patch("openai.OpenAI") as mock_openai_cls,
    ):
        mock_settings.ai_enabled = True
        mock_settings.openai_api_key = "sk-test"
        mock_settings.openai_base_url = None
        mock_settings.ai_model = "gpt-4o-mini"

        mock_client = mock_openai_cls.return_value
        mock_client.chat.completions.create.return_value = mock_response

        r = await client.post(
            "/api/v1/ai/generate",
            json={"prompt": "A user and a web app with an API"},
        )
        assert r.status_code == 200
        data = r.json()
        assert "likec4_dsl" in data
        assert "model {" in data["likec4_dsl"]
        assert "views {" in data["likec4_dsl"]
