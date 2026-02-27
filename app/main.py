"""FastAPI entry point for LikeC4 Diagram API."""

from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.auth_endpoints import router as auth_router
from app.api.v1.ai_endpoints import router as ai_router
from app.api.v1.endpoints import router as generate_router
from app.core.config import settings
from app.services.db import close_turso, init_turso


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    init_turso()
    try:
        yield
    finally:
        close_turso()


app = FastAPI(
    title=settings.app_name,
    description="Generate LikeC4 diagrams (D2, Mermaid, PlantUML) from a processed view JSON. Optional AI generates LikeC4 DSL from natural language.",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS configuration for playground/docs frontends.
# Adjust origins as needed for your deployments.
origins = [
    "http://localhost:5173",  # local playground
    "http://localhost:4321",  # local docs (if used)
    "https://likec4.dev",  # production docs
    "https://likec4-playground.vercel.app",
    # Add your deployed playground/other domains here, e.g.:
    # "https://your-playground-domain",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(generate_router, prefix="/api/v1")
app.include_router(ai_router, prefix="/api/v1")
app.include_router(auth_router, prefix="/api/v1")


@app.get("/health")
async def health() -> dict[str, str]:
    """Health check for load balancers and orchestration."""
    return {"status": "ok"}


@app.get("/")
async def root() -> dict[str, str]:
    """Root redirect to API docs."""
    return {"message": "LikeC4 Diagram API", "docs": "/docs"}
