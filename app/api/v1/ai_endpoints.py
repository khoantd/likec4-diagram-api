"""AI-powered LikeC4 diagram generation endpoints."""

import json
from collections.abc import Mapping

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from app.core.auth import get_current_username
from app.core.config import settings
from app.core.schemas import AIGenerateRequest, AIGenerateResponse, AIRequestLog
from app.services.ai import generate_likec4_dsl
from app.services.db import list_ai_requests, log_ai_request

router = APIRouter(prefix="/ai", tags=["ai"])


def _ai_available() -> bool:
    return bool(settings.ai_enabled and settings.openai_api_key)


def _extract_client_ip_and_geo(request: Request) -> tuple[str | None, str | None]:
    """Best-effort extraction of client IP and geo information from headers."""
    headers: Mapping[str, str] = request.headers  # type: ignore[assignment]

    # Prefer X-Forwarded-For when behind proxies/CDNs
    xff = headers.get("x-forwarded-for") or headers.get("X-Forwarded-For")
    client_ip: str | None = None
    if xff:
        client_ip = xff.split(",")[0].strip() or None
    if not client_ip and request.client:
        client_ip = request.client.host

    geo_data: dict[str, str] = {}
    country = (
        headers.get("cf-ipcountry")
        or headers.get("CF-IPCountry")
        or headers.get("x-geo-country")
        or headers.get("X-Geo-Country")
        or headers.get("x-appengine-country")
        or headers.get("X-AppEngine-Country")
    )
    if country:
        geo_data["country"] = country

    region = (
        headers.get("cf-region")
        or headers.get("CF-Region")
        or headers.get("x-geo-region")
        or headers.get("X-Geo-Region")
        or headers.get("x-appengine-region")
        or headers.get("X-AppEngine-Region")
    )
    if region:
        geo_data["region"] = region

    city = (
        headers.get("cf-city")
        or headers.get("CF-City")
        or headers.get("x-geo-city")
        or headers.get("X-Geo-City")
        or headers.get("x-appengine-city")
        or headers.get("X-AppEngine-City")
    )
    if city:
        geo_data["city"] = city

    geo_json: str | None = json.dumps(geo_data) if geo_data else None
    return client_ip, geo_json


@router.get("/requests", response_model=list[AIRequestLog])
async def get_ai_requests(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    _username: str = Depends(get_current_username),
) -> list[AIRequestLog]:
    """
    Retrieve recent AI generation requests logged in the Turso database.

    Requires Turso logging to be enabled and configured.
    """
    if not settings.turso_enabled:
        raise HTTPException(
            status_code=503,
            detail=(
                "Turso database logging is not enabled. Set LIKEC4_API_TURSO_ENABLED=true, "
                "configure Turso connection settings, and install optional deps: pyturso"
            ),
        )

    try:
        return list_ai_requests(limit=limit, offset=offset)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.post("/generate", response_model=AIGenerateResponse)
async def ai_generate_from_description(
    body: AIGenerateRequest,
    request: Request,
    _username: str = Depends(get_current_username),
) -> AIGenerateResponse:
    """
    Generate LikeC4 DSL from a natural language description using AI.

    Requires AI to be enabled and configured (LIKEC4_API_AI_ENABLED=true,
    LIKEC4_API_OPENAI_API_KEY set). Optionally set LIKEC4_API_LITELLM_BASE_URL to use a LiteLLM proxy,
    or LIKEC4_API_OPENAI_BASE_URL for any OpenAI-compatible endpoint (e.g. Azure).
    """
    if not _ai_available():
        raise HTTPException(
            status_code=503,
            detail=(
                "AI generation is not configured. Set LIKEC4_API_AI_ENABLED=true and "
                "LIKEC4_API_OPENAI_API_KEY, and install optional deps: pip install likec4-diagram-api[ai]"
            ),
        )
    # Prefer LiteLLM proxy URL when set; otherwise use generic OpenAI-compatible base URL
    base_url = settings.litellm_base_url or settings.openai_base_url
    client_ip, geo = _extract_client_ip_and_geo(request)
    try:
        dsl, explanation = generate_likec4_dsl(
            body.prompt,
            body.hint,
            api_key=settings.openai_api_key,
            model=settings.ai_model,
            base_url=base_url,
            current_dsl=body.current_dsl,
            view_id=body.view_id,
        )
        # Best-effort logging of successful AI requests
        log_ai_request(
            prompt=body.prompt,
            hint=body.hint,
            model=settings.ai_model,
            likec4_dsl=dsl,
            explanation=explanation,
            success=True,
            client_ip=client_ip,
            geo=geo,
        )
        return AIGenerateResponse(likec4_dsl=dsl, explanation=explanation)
    except ValueError as e:
        # Best-effort logging of failed AI requests
        log_ai_request(
            prompt=body.prompt,
            hint=body.hint,
            model=settings.ai_model,
            likec4_dsl=None,
            explanation=None,
            success=False,
            error=str(e),
            client_ip=client_ip,
            geo=geo,
        )
        raise HTTPException(status_code=422, detail=str(e)) from e
