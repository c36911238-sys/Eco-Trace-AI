import warnings
from typing import List

import numpy as np
import pandas as pd
import shap
from sklearn.ensemble import RandomForestRegressor

from app.db.models import CarbonLog, CategoryEnum
from app.schemas.carbon import SHAPExplanation

# Suppress verbose SHAP internal warnings
warnings.filterwarnings("ignore")

# ── Lazy-Loaded Global Model Singletons ──────────────────────────────────────
# Model and explainer are initialized on first use, not at import time.
# This avoids penalising application cold-start time (critical for serverless).
_rf_model: RandomForestRegressor | None = None
_explainer: shap.TreeExplainer | None = None

_FEATURE_ORDER: List[str] = [
    "transportation",
    "food",
    "electricity",
    "shopping",
    "waste",
]


def generate_synthetic_data(n_samples: int = 500) -> pd.DataFrame:
    """
    Generate a realistic synthetic dataset for training the Random Forest model.

    Args:
        n_samples: Number of data points to generate.

    Returns:
        A DataFrame with feature columns and a 'total_footprint' target.
    """
    rng = np.random.default_rng(seed=42)
    data = {
        "transportation": rng.uniform(10, 100, n_samples),
        "food": rng.uniform(5, 50, n_samples),
        "electricity": rng.uniform(20, 80, n_samples),
        "shopping": rng.uniform(0, 40, n_samples),
        "waste": rng.uniform(1, 20, n_samples),
    }
    df = pd.DataFrame(data)
    # Non-linear interaction term: high transport + high shopping → delivery surge
    df["total_footprint"] = (
        df["transportation"] * 1.2
        + df["food"] * 0.9
        + df["electricity"] * 1.5
        + df["shopping"]
        + df["waste"]
        + (df["transportation"] * df["shopping"]) * 0.01
    )
    return df


def _get_explainer() -> shap.TreeExplainer:
    """
    Return the singleton SHAP TreeExplainer, training the Random Forest
    model on first call only (lazy initialization).

    Returns:
        A cached shap.TreeExplainer instance.
    """
    global _rf_model, _explainer
    if _explainer is None:
        synth_df = generate_synthetic_data()
        X_train = synth_df.drop(columns=["total_footprint"])
        y_train = synth_df["total_footprint"]

        _rf_model = RandomForestRegressor(n_estimators=50, random_state=42)
        _rf_model.fit(X_train, y_train)
        _explainer = shap.TreeExplainer(_rf_model)

    return _explainer


def generate_shap_explanations(logs: List[CarbonLog]) -> List[SHAPExplanation]:
    """
    Compute SHAP (SHapley Additive exPlanations) values for a user's carbon logs.

    This function is CPU-bound and should be called via asyncio.to_thread
    from async endpoints to avoid blocking the event loop.

    Args:
        logs: List of CarbonLog ORM objects for the current user.

    Returns:
        A list of SHAPExplanation objects sorted by highest absolute impact.
    """
    if not logs:
        return [
            SHAPExplanation(
                feature="No Data",
                impact=0.0,
                description="Start logging activities to see AI-powered insights.",
            )
        ]

    # Aggregate user's logs into category totals
    user_features: dict[str, float] = {cat.value: 0.0 for cat in CategoryEnum}
    total_emission = 0.0

    for log in logs:
        user_features[log.category.value] += log.emission_amount
        total_emission += log.emission_amount

    if total_emission == 0:
        return []

    # Build a single-row DataFrame matching the training feature order
    user_df = pd.DataFrame(
        [[user_features.get(f, 0.0) for f in _FEATURE_ORDER]],
        columns=_FEATURE_ORDER,
    )

    explainer = _get_explainer()
    shap_values = explainer.shap_values(user_df)

    # shap_values is shape (n_samples, n_features); take first row
    impacts: np.ndarray = shap_values[0]
    total_abs_shap = float(np.sum(np.abs(impacts))) or 1.0  # Guard div-by-zero

    explanations: List[SHAPExplanation] = []
    for i, feature in enumerate(_FEATURE_ORDER):
        shap_val = float(impacts[i])
        if abs(shap_val) <= 0.1:
            continue

        impact_percent = round((abs(shap_val) / total_abs_shap) * 100, 1)
        direction = (
            "driving your footprint higher" if shap_val > 0 else "keeping your footprint low"
        )
        description = (
            f"{feature.capitalize()} is {direction}. "
            f"Marginal contribution: {abs(round(shap_val, 1))} kg CO₂."
        )
        explanations.append(
            SHAPExplanation(
                feature=feature.capitalize(),
                impact=impact_percent,
                description=description,
            )
        )

    return sorted(explanations, key=lambda x: x.impact, reverse=True)
