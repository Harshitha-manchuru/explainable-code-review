"""
FastAPI application entrypoint.

Mounts the submission router, configures CORS for the Vite dev server
(and any production frontend origin set via environment), and exposes
a lightweight health check that reports whether the LLM is running in
live (Gemini) or offline stub mode.
"""

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes_submission import router as submission_router
from app.api.schemas import HealthResponse
from app.config import ALLOWED_ORIGINS, USE_LLM_STUB

logging.basicConfig(level=logging.INFO)

app = FastAPI(
    title="Explainable RAG-Based Code Review System",
    description=(
        "Submits Python code for static analysis, retrieves grounded "
        "style/anti-pattern rules via RAG, generates LLM explanations, "
        "and verifies explanation faithfulness via NLI entailment."
    ),
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(submission_router)


@app.get("/api/health", response_model=HealthResponse)
def health_check() -> HealthResponse:
    """Reports service status and whether the LLM is live or stubbed."""
    return HealthResponse(
        status="ok",
        llm_mode="stub" if USE_LLM_STUB else "live",
    )


@app.get("/")
def root() -> dict:
    return {
        "service": "Explainable RAG-Based Code Review System",
        "docs": "/docs",
        "health": "/api/health",
    }
