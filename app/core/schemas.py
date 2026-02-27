"""Pydantic schemas for LikeC4 processed view (nodes, edges, autoLayout)."""

from typing import Literal

from pydantic import BaseModel, Field


class AutoLayout(BaseModel):
    """View auto-layout direction (TB, BT, LR, RL)."""

    direction: Literal["TB", "BT", "LR", "RL"] = "TB"


class ViewNode(BaseModel):
    """Computed node in a LikeC4 view."""

    id: str
    parent: str | None = None
    title: str
    children: list[str] = Field(default_factory=list)
    shape: str = "rectangle"


class ViewEdge(BaseModel):
    """Computed edge in a LikeC4 view."""

    source: str
    target: str
    label: str | None = None


class ProcessedView(BaseModel):
    """LikeC4 processed view (computed/layouted) - input for diagram generators."""

    nodes: list[ViewNode]
    edges: list[ViewEdge]
    auto_layout: AutoLayout = Field(default_factory=AutoLayout, alias="autoLayout")

    model_config = {"populate_by_name": True}


# --- AI generation ---


class AIGenerateRequest(BaseModel):
    """Request body for AI-generated LikeC4 diagram from natural language."""

    prompt: str = Field(..., min_length=1, description="Natural language description of the system/diagram")
    hint: str | None = Field(default=None, description="Optional hint (e.g. focus on containers, use C4 style)")


class AIGenerateResponse(BaseModel):
    """Response with AI-generated LikeC4 DSL and optional explanation."""

    likec4_dsl: str = Field(..., description="Generated LikeC4 model and/or views DSL")
    explanation: str | None = Field(default=None, description="Optional short explanation of the generated diagram")
