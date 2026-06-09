import asyncio
import logging
from datetime import datetime, timezone
from typing import List

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.db.database import get_db
from app.db.models import User, CarbonLog, CarbonPrediction, CategoryEnum
from app.schemas.carbon import (
    CarbonLogCreate,
    CarbonLogResponse,
    CarbonPredictionResponse,
    TwinSimulationRequest,
)
from app.api.deps import get_current_user
from app.services.ai_explain import generate_shap_explanations
from app.services.twin_simulate import simulate_twin
from app.services.ocr import get_ocr_driver

logger = logging.getLogger(__name__)

router = APIRouter()

# ── Constants ────────────────────────────────────────────────────────────────
_MAX_RECEIPT_FILE_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB
_ALLOWED_RECEIPT_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp"}


# ── Carbon Log Endpoints ─────────────────────────────────────────────────────

@router.post(
    "/logs",
    response_model=CarbonLogResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a manual carbon log entry",
)
async def create_carbon_log(
    log_in: CarbonLogCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CarbonLog:
    """Record a new manual carbon emission entry for the authenticated user."""
    db_log = CarbonLog(**log_in.model_dump(), user_id=current_user.id)
    db.add(db_log)
    await db.commit()
    await db.refresh(db_log)
    return db_log


@router.get(
    "/logs",
    response_model=List[CarbonLogResponse],
    summary="Retrieve all carbon logs for the current user",
)
async def get_carbon_logs(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[CarbonLog]:
    """Fetch all carbon logs for the authenticated user, ordered newest-first."""
    result = await db.execute(
        select(CarbonLog)
        .filter(CarbonLog.user_id == current_user.id)
        .order_by(CarbonLog.logged_date.desc())
    )
    return result.scalars().all()


@router.post(
    "/receipt",
    response_model=CarbonLogResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a receipt image to auto-log carbon emissions via OCR",
)
async def upload_receipt(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CarbonLog:
    """
    Accepts a JPG, PNG, or WebP receipt image (max 5 MB), runs OCR extraction,
    and creates a new carbon log entry from the result.
    """
    # Validate content type
    if file.content_type not in _ALLOWED_RECEIPT_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=(
                f"Unsupported file type '{file.content_type}'. "
                "Only JPEG, PNG, and WebP images are accepted."
            ),
        )

    # Validate file size
    content = await file.read()
    if len(content) > _MAX_RECEIPT_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File exceeds the maximum allowed size of 5 MB.",
        )

    # Run OCR in a thread pool to avoid blocking the event loop
    ocr_driver = get_ocr_driver()
    ocr_result = await asyncio.to_thread(ocr_driver.extract_receipt, content)

    if not ocr_result["success"]:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Could not extract carbon data from the uploaded receipt.",
        )

    db_log = CarbonLog(**ocr_result["extracted_data"], user_id=current_user.id)
    db.add(db_log)
    await db.commit()
    await db.refresh(db_log)
    return db_log


# ── AI Insights Endpoint ─────────────────────────────────────────────────────

@router.get(
    "/insights",
    response_model=CarbonPredictionResponse,
    summary="Generate SHAP-powered AI insights for the current user",
)
async def get_ai_insights(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CarbonPredictionResponse:
    """
    Performs DB-level aggregation of the user's carbon logs by category,
    then offloads SHAP value computation to a thread pool to avoid blocking.
    """
    # ── DB-level aggregation (replaces slow Python loop) ──────────────────
    agg_result = await db.execute(
        select(CarbonLog.category, func.sum(CarbonLog.emission_amount))
        .filter(CarbonLog.user_id == current_user.id)
        .group_by(CarbonLog.category)
    )
    aggregated: dict[str, float] = {
        cat.value: float(total) for cat, total in agg_result.all()
    }

    total_recent = sum(aggregated.values())

    # ── Fetch raw logs only for SHAP (needs individual records) ──────────
    logs_result = await db.execute(
        select(CarbonLog).filter(CarbonLog.user_id == current_user.id)
    )
    logs = logs_result.scalars().all()

    # ── Offload CPU-bound SHAP computation to a thread pool ───────────────
    explanations = await asyncio.to_thread(generate_shap_explanations, logs)

    return CarbonPredictionResponse(
        predicted_emission=total_recent,
        target_date=datetime.now(timezone.utc).replace(
            month=(datetime.now(timezone.utc).month % 12) + 1
        ),
        explanations=explanations,
    )


# ── Digital Twin Endpoint ─────────────────────────────────────────────────────

@router.post(
    "/twin/simulate",
    response_model=dict,
    summary="Run a Digital Carbon Twin simulation scenario",
)
async def simulate_carbon_twin(
    request: TwinSimulationRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """
    Fetches the user's historical carbon logs and runs a linear-regression-based
    Digital Twin simulation in a worker thread for the requested scenario.
    """
    result = await db.execute(
        select(CarbonLog).filter(CarbonLog.user_id == current_user.id)
    )
    logs = result.scalars().all()

    # Offload regression calculation to thread pool
    projected_emission = await asyncio.to_thread(simulate_twin, logs, request)

    return {
        "status": "success",
        "projected_emission": projected_emission,
        "scenario": (
            f"Reduced {request.category_to_reduce.value} by "
            f"{request.reduction_percentage}% over {request.days_to_simulate} days."
        ),
    }
