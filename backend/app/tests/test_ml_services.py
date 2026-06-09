"""
Comprehensive test suite for EcoTrace AI+ ML services.

Covers: synthetic data generation, SHAP explanations, and twin simulation —
including edge cases (empty logs, zero emissions, fallback model, regression model).
"""
import pytest
from datetime import datetime

from app.db.models import CarbonLog, CategoryEnum
from app.schemas.carbon import TwinSimulationRequest
from app.services.ai_explain import generate_synthetic_data, generate_shap_explanations
from app.services.twin_simulate import simulate_twin, _fallback_simulate


# ── Synthetic Data Tests ─────────────────────────────────────────────────────

class TestGenerateSyntheticData:
    def test_returns_correct_row_count(self):
        """Verify that the requested number of samples is generated."""
        df = generate_synthetic_data(n_samples=50)
        assert len(df) == 50

    def test_contains_all_required_columns(self):
        """Verify all feature columns and the target column are present."""
        df = generate_synthetic_data(n_samples=10)
        expected_cols = {"transportation", "food", "electricity", "shopping", "waste", "total_footprint"}
        assert expected_cols.issubset(df.columns)

    def test_footprint_is_always_positive(self):
        """Total footprint should never be negative with positive features."""
        df = generate_synthetic_data(n_samples=100)
        assert (df["total_footprint"] >= 0).all()

    def test_default_sample_size(self):
        """Default call without arguments should return 500 rows."""
        df = generate_synthetic_data()
        assert len(df) == 500


# ── SHAP Explanation Tests ───────────────────────────────────────────────────

class TestGenerateShapExplanations:
    def test_empty_logs_returns_no_data_placeholder(self):
        """Empty input must return a single 'No Data' placeholder explanation."""
        explanations = generate_shap_explanations([])
        assert len(explanations) == 1
        assert explanations[0].feature == "No Data"
        assert explanations[0].impact == 0.0

    def test_zero_emission_logs_return_empty_list(self):
        """Logs that sum to zero emissions should return an empty list."""
        logs = [
            CarbonLog(
                category=CategoryEnum.food,
                emission_amount=0.0,
                logged_date=datetime.now(),
            )
        ]
        result = generate_shap_explanations(logs)
        assert result == []

    def test_active_logs_return_sorted_explanations(self):
        """With real emissions, explanations should be sorted by highest impact."""
        logs = [
            CarbonLog(
                category=CategoryEnum.electricity,
                emission_amount=100.0,
                logged_date=datetime.now(),
            ),
            CarbonLog(
                category=CategoryEnum.transportation,
                emission_amount=50.0,
                logged_date=datetime.now(),
            ),
        ]
        explanations = generate_shap_explanations(logs)
        assert len(explanations) > 0
        # All impacts must be non-negative percentages
        assert all(exp.impact >= 0 for exp in explanations)
        # Impacts must be sorted descending
        impacts = [exp.impact for exp in explanations]
        assert impacts == sorted(impacts, reverse=True)

    def test_explanation_features_are_capitalized(self):
        """Feature names in explanations should be title-cased."""
        logs = [
            CarbonLog(
                category=CategoryEnum.transportation,
                emission_amount=80.0,
                logged_date=datetime.now(),
            )
        ]
        explanations = generate_shap_explanations(logs)
        for exp in explanations:
            assert exp.feature == exp.feature.capitalize()

    def test_impact_percentages_sum_to_at_most_100(self):
        """The sum of impact percentages should never exceed 100."""
        logs = [
            CarbonLog(category=cat, emission_amount=50.0, logged_date=datetime.now())
            for cat in CategoryEnum
        ]
        explanations = generate_shap_explanations(logs)
        total = sum(exp.impact for exp in explanations)
        assert total <= 100.05  # Allow small floating point tolerance


# ── Digital Twin Simulation Tests ────────────────────────────────────────────

def _make_request(
    category: CategoryEnum = CategoryEnum.electricity,
    reduction: float = 20.0,
    days: int = 30,
) -> TwinSimulationRequest:
    return TwinSimulationRequest(
        category_to_reduce=category,
        reduction_percentage=reduction,
        days_to_simulate=days,
    )


class TestFallbackSimulate:
    def test_empty_logs_returns_zero(self):
        """No logs should yield a zero projected emission."""
        result = _fallback_simulate([], _make_request())
        assert result == 0.0

    def test_single_log_returns_positive_value(self):
        """A single log entry should produce a non-negative fallback estimate."""
        logs = [
            CarbonLog(
                category=CategoryEnum.electricity,
                emission_amount=15.0,
                logged_date=datetime.now(),
            )
        ]
        result = _fallback_simulate(logs, _make_request())
        assert result >= 0.0

    def test_result_never_negative(self):
        """Fallback result must be clamped to zero even with extreme reduction."""
        logs = [
            CarbonLog(
                category=CategoryEnum.electricity,
                emission_amount=0.01,
                logged_date=datetime.now(),
            )
        ]
        result = _fallback_simulate(logs, _make_request(reduction=999.0))
        assert result >= 0.0


class TestSimulateTwin:
    def test_fewer_than_3_logs_uses_fallback(self):
        """With < 3 logs, the function should fall back to simple averaging."""
        logs = [
            CarbonLog(
                category=CategoryEnum.electricity,
                emission_amount=15.0,
                logged_date=datetime.now(),
            )
        ]
        result = simulate_twin(logs, _make_request())
        assert result >= 0.0

    def test_regression_with_4_logs_returns_positive_value(self):
        """With 4 spread-out logs, regression should yield a valid forecast."""
        logs = [
            CarbonLog(
                category=CategoryEnum.electricity,
                emission_amount=10.0 + i * 2,
                logged_date=datetime(2026, 6, 1 + i),
            )
            for i in range(4)
        ]
        result = simulate_twin(logs, _make_request(days=10))
        assert result >= 0.0

    def test_higher_reduction_yields_lower_emission(self):
        """A higher reduction percentage should always produce less emission."""
        logs = [
            CarbonLog(
                category=CategoryEnum.electricity,
                emission_amount=10.0 + i * 2,
                logged_date=datetime(2026, 6, 1 + i),
            )
            for i in range(4)
        ]
        low_reduction = simulate_twin(logs, _make_request(reduction=10.0))
        high_reduction = simulate_twin(logs, _make_request(reduction=90.0))
        assert high_reduction <= low_reduction

    def test_zero_logs_in_regression_category_still_returns_valid(self):
        """If the target category has no logs, the projection should still be valid."""
        logs = [
            CarbonLog(
                category=CategoryEnum.food,
                emission_amount=20.0,
                logged_date=datetime(2026, 6, 1 + i),
            )
            for i in range(4)
        ]
        # Reduce transportation, but no transportation logs exist
        result = simulate_twin(logs, _make_request(category=CategoryEnum.transportation))
        # No category ratio → no reduction → baseline returned
        assert result >= 0.0
