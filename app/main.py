"""FastAPI entry point for LikeC4 Diagram API."""

from fastapi import FastAPI

from app.api.v1.ai_endpoints import router as ai_router
from app.api.v1.endpoints import router as generate_router
from app.core.config import settings

app = FastAPI(
    title=settings.app_name,
    description="Generate LikeC4 diagrams (D2, Mermaid, PlantUML) from a processed view JSON. Optional AI generates LikeC4 DSL from natural language.",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.include_router(generate_router, prefix="/api/v1")
app.include_router(ai_router, prefix="/api/v1")


@app.get("/health")
async def health() -> dict[str, str]:
    """Health check for load balancers and orchestration."""
    return {"status": "ok"}


@app.get("/")
async def root() -> dict[str, str]:
    """Root redirect to API docs."""
    return {"message": "LikeC4 Diagram API", "docs": "/docs"}
