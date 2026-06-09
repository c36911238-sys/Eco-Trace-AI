"""
Digital Carbon Twin Service — Linear Regression–based emission forecasting.

This module is CPU-bound. All public functions should be called via
asyncio.to_thread from async FastAPI endpoints.
"""
from typing import List

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression

from app.db.models import CarbonLog
from app.schemas.carbon import TwinSimulationRequest

_MIN_LOGS_FOR_REGRESSION = 3


def simulate_twin(logs: List[CarbonLog], request: TwinSimulationRequest) -> float:
    """
    Forecast future carbon emissions using a Digital Carbon Twin model.

    For users with fewer than 3 logs, falls back to a simple daily-average
    model. Otherwise, fits a linear regression on historical daily totals to
    extrapolate the baseline, then applies the requested scenario reduction.

    Args:
        logs: Historical CarbonLog records for the user.
        request: Simulation parameters (category, reduction %, days).

    Returns:
        Projected total emission (kg CO₂) for the simulation period.
    """
    if len(logs) < _MIN_LOGS_FOR_REGRESSION:
        return _fallback_simulate(logs, request)

    df = _build_daily_dataframe(logs)
    daily_totals = df.groupby("day_idx")["amount"].sum().reset_index()

    X = daily_totals[["day_idx"]].values
    y = daily_totals["amount"].values

    model = LinearRegression()
    model.fit(X, y)

    last_day = int(daily_totals["day_idx"].max())
    future_days = np.array(
        [[last_day + i] for i in range(1, request.days_to_simulate + 1)]
    )

    # Clamp to non-negative — emissions can't go below zero
    predicted_baseline = np.maximum(model.predict(future_days), 0.0)
    projected_total = float(predicted_baseline.sum())

    return _apply_scenario_reduction(df, projected_total, request)


def _build_daily_dataframe(logs: List[CarbonLog]) -> pd.DataFrame:
    """Convert CarbonLog records into a daily-indexed DataFrame."""
    records = [
        {
            "date": log.logged_date.date(),
            "category": log.category.value,
            "amount": log.emission_amount,
        }
        for log in logs
    ]
    df = pd.DataFrame(records)
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date")
    min_date = df["date"].min()
    df["day_idx"] = (df["date"] - min_date).dt.days
    return df


def _apply_scenario_reduction(
    df: pd.DataFrame,
    projected_total: float,
    request: TwinSimulationRequest,
) -> float:
    """
    Apply the user's target category reduction to the projected baseline.

    Args:
        df: The full daily emissions DataFrame.
        projected_total: Baseline total emission for the simulation window.
        request: The simulation request parameters.

    Returns:
        Rounded final projected emission after applying the reduction factor.
    """
    all_total = float(df["amount"].sum())
    if all_total <= 0:
        return round(projected_total, 2)

    cat_total = float(
        df.loc[df["category"] == request.category_to_reduce.value, "amount"].sum()
    )
    cat_ratio = cat_total / all_total
    reduction_factor = cat_ratio * (request.reduction_percentage / 100.0)
    return round(projected_total * (1.0 - reduction_factor), 2)


def _fallback_simulate(
    logs: List[CarbonLog], request: TwinSimulationRequest
) -> float:
    """
    Simple fallback model for users with fewer than 3 log entries.
    Uses a 30-day rolling average as the daily baseline.

    Args:
        logs: The user's carbon logs.
        request: Simulation parameters.

    Returns:
        Estimated total emission for the simulation period.
    """
    if not logs:
        return 0.0

    daily_avg = sum(log.emission_amount for log in logs) / 30.0
    baseline = daily_avg * request.days_to_simulate

    # Apply a conservative 20% weight for the category's share
    reduction = (
        (request.reduction_percentage / 100.0) * (daily_avg * 0.2)
        * request.days_to_simulate
    )
    return round(max(baseline - reduction, 0.0), 2)
