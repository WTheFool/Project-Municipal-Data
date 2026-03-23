# apps/api/src/municipal_api/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from municipal_api.infra.db import Base, engine
from municipal_api.infra.settings import settings
from municipal_api.infra.storage_s3 import ensure_bucket_exists
from municipal_api.web.routes import (
    artifacts_router,
    health_router,
    projects_router,
    runs_router,
    uploads_router,
)
from municipal_api.web.routes import job_status

app = FastAPI(
    title="Dynamic Indicator Generation & AI-Assisted Reporting Framework",
    description="Upload Excel files, auto-detect variables, generate indicators, compute stats, ML analysis, graphs, and reports.",
    version="1.0.0",
)

# Allow CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.cors_origins.split(",") if o.strip()] or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def _startup():
    # Ensure DB schema exists (no Alembic migrations in repo yet)
    import municipal_api.infra.models  # noqa: F401

    Base.metadata.create_all(bind=engine)
    ensure_bucket_exists()

# Include routers
app.include_router(health_router, prefix="/api", tags=["Health"])
app.include_router(projects_router, prefix="/api", tags=["Projects"])
app.include_router(uploads_router, prefix="/api", tags=["Uploads"])
app.include_router(runs_router, prefix="/api", tags=["Runs"])
app.include_router(artifacts_router, prefix="/api", tags=["Artifacts"])
app.include_router(job_status.router, prefix="/api", tags=["Jobs"])

# Root and health
@app.get("/", summary="Health check / welcome message")
def root():
    return {"message": "Municipal Data Analytics API is running!"}

@app.get("/health", summary="API health check")
def health():
    return {"status": "ok"}