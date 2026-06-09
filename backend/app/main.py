import sys
import subprocess
import traceback

# Try to install email-validator at runtime if it is missing
try:
    import email_validator
except ImportError:
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "--no-cache-dir", "install", "email-validator"])
    except Exception as e:
        sys.stderr.write(f"Runtime pip install failed: {e}\n")

# Safely import the rest of the application
import_error_message = None
try:
    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware
    from contextlib import asynccontextmanager

    from app.core.config import settings
    from app.db.database import engine
    from app.db import models
    from app.api.v1.router import api_router
except Exception as e:
    import_error_message = traceback.format_exc()

if import_error_message:
    from fastapi import FastAPI
    app = FastAPI(title="EcoTrace AI+ Diagnostics")

    @app.get("/{path:path}")
    def diagnostics(path: str = ""):
        return {
            "status": "diagnostics_mode",
            "error": "Failed to import application dependencies",
            "traceback": import_error_message,
            "python_version": sys.version,
            "sys_path": sys.path,
        }
else:
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
