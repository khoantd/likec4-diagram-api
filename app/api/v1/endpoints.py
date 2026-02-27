"""Diagram generation endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import PlainTextResponse
from app.core.auth import get_current_username
from app.core.schemas import ProcessedView
from app.services.generator import generate_diagram

router = APIRouter(prefix="/generate", tags=["diagram"])


@router.post("/d2", response_class=PlainTextResponse)
async def generate_d2(view: ProcessedView, _username: str = Depends(get_current_username)) -> str:
    """Generate a D2 diagram from a LikeC4 processed view."""
    try:
        return generate_diagram(view, "d2")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.post("/mermaid", response_class=PlainTextResponse)
async def generate_mermaid(view: ProcessedView, _username: str = Depends(get_current_username)) -> str:
    """Generate a Mermaid diagram from a LikeC4 processed view."""
    try:
        return generate_diagram(view, "mermaid")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.post("/puml", response_class=PlainTextResponse)
async def generate_puml(view: ProcessedView, _username: str = Depends(get_current_username)) -> str:
    """Generate a PlantUML diagram from a LikeC4 processed view."""
    try:
        return generate_diagram(view, "puml")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.post("/{format}", response_class=PlainTextResponse)
async def generate(view: ProcessedView, format: str, _username: str = Depends(get_current_username)) -> str:
    """Generate a diagram in the given format (d2, mermaid, puml)."""
    try:
        return generate_diagram(view, format)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
