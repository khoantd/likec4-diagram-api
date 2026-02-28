"""LikeC4 DSL parse/validate endpoint."""

from fastapi import APIRouter, HTTPException

from app.core.schemas import ParseRequest, ParseResponse
from app.services.parse import parse_c4

router = APIRouter(prefix="/parse", tags=["parse"])

_PARSE_UNAVAILABLE_DETAIL = (
    "Parse service requires Node.js and the parse-c4.mjs script. "
    "Set LIKEC4_API_PARSE_ENABLED=true and optionally LIKEC4_API_PARSE_SCRIPT_PATH, "
    "then ensure Node.js ≥18 and monorepo dependencies (pnpm install) are available."
)


@router.post("", response_model=ParseResponse, summary="Validate LikeC4 DSL")
async def parse_dsl(body: ParseRequest) -> ParseResponse:
    """
    Validate LikeC4 DSL source code using the language server.

    Returns `{"valid": true}` when the DSL has no errors, or
    `{"valid": false, "errors": [...]}` with structured error details.

    Requires Node.js ≥18 and the parse script to be configured:
    set **LIKEC4_API_PARSE_ENABLED=true** (and optionally
    **LIKEC4_API_PARSE_SCRIPT_PATH** for a custom script location).
    Returns **503** when parse is not available.
    """
    try:
        result = parse_c4(body.dsl)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    return ParseResponse(valid=result["valid"], errors=result.get("errors"))
