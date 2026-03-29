"""FastAPI application entry point for the Revue.ai backend."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes.job_postings import router as job_postings_router
from api.routes.report import router as report_router
from api.routes.resume import router as resume_router
from api.services.database import initialize_database


def create_app() -> FastAPI:
    """Create the backend application with route registration and local CORS."""
    app = FastAPI(
        title="Revue.ai API",
        version="0.1.0",
        description=(
            "Minimal FastAPI backend shell for the Revue.ai prototype. "
            "Pipeline and infrastructure integrations are intentionally deferred."
        ),
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:3100",
            "http://127.0.0.1:3100",
            "http://localhost:3101",
            "http://127.0.0.1:3101",
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "http://localhost:4173",
            "http://127.0.0.1:4173",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health", tags=["system"])
    def healthcheck() -> dict[str, str]:
        return {
            "status": "ok",
            "service": "revue-backend",
        }

    @app.get("/", tags=["system"])
    def root() -> dict[str, str]:
        return {
            "name": "Revue.ai API",
            "docs": "/docs",
        }

    app.include_router(job_postings_router, prefix="/api")
    app.include_router(resume_router, prefix="/api")
    app.include_router(report_router, prefix="/api")

    @app.on_event("startup")
    def setup_database() -> None:
        """Ensure local PostgreSQL tables exist before serving requests."""
        initialize_database()

    return app


app = create_app()