from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.config import settings
from app.db.database import engine
from app.db import models
from app.api.v1.router import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifecycle manager.
    On startup: creates all database tables (use Alembic for production migrations).
    On shutdown: disposes of the connection pool.
    """
    async with engine.begin() as conn:
        await conn.run_sync(models.Base.metadata.create_all)
    yield
    await engine.dispose()


app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    description=(
        "EcoTrace AI+ — An Explainable AI carbon footprint tracker with "
        "Digital Twin forecasting, OCR receipt intelligence, and community gamification."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

# Restrict CORS to explicitly configured origins. In production, set
# BACKEND_CORS_ORIGINS in your .env (e.g. https://app.ecotrace.ai).
# Never use allow_origins=["*"] in production.
allowed_origins = (
    [str(origin).rstrip("/") for origin in settings.BACKEND_CORS_ORIGINS]
    if settings.BACKEND_CORS_ORIGINS
    else ["http://localhost:3000"]  # Fallback for local development only
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/", tags=["health"])
def root():
    """Root endpoint — used by load balancers and uptime monitors."""
    return {"message": "Welcome to EcoTrace AI+ API", "version": "1.0.0"}
