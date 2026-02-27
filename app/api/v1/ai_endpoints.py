"""AI-powered LikeC4 diagram generation endpoints."""

from fastapi import APIRouter, HTTPException

from app.core.config import settings
from app.core.schemas import AIGenerateRequest, AIGenerateResponse
from app.services.ai import generate_likec4_dsl

router = APIRouter(prefix="/ai", tags=["ai"])


def _ai_available() -> bool:
    return bool(settings.ai_enabled and settings.openai_api_key)


@router.post("/generate", response_model=AIGenerateResponse)
async def ai_generate_from_description(body: AIGenerateRequest) -> AIGenerateResponse:
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
    try:
        dsl, explanation = generate_likec4_dsl(
            body.prompt,
            body.hint,
            api_key=settings.openai_api_key,
            model=settings.ai_model,
            base_url=base_url,
        )
        return AIGenerateResponse(likec4_dsl=dsl, explanation=explanation)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e)) from e
