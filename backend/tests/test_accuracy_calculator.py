"""Deterministic tests for accuracy metrics with hand-calculated expected values."""

from app.services.accuracy_calculator import calculate_metrics

# pairs: (forecast_mw, actual_mw) -> errors [10, 10, -5]
PAIRS = [(100.0, 90.0), (110.0, 100.0), (90.0, 95.0)]
# Expected:
#   mae   = (10 + 10 + 5) / 3 = 8.3333
#   rmse  = sqrt((100 + 100 + 25) / 3) = sqrt(75) = 8.6603
#   bias  = (10 + 10 - 5) / 3 = 5.0
#   over  = 2 / 3 * 100 = 66.6667


def test_mae_rmse_bias_overforecast_match_hand_calculated():
    result = calculate_metrics(PAIRS)
    assert result["n"] == 3
    assert result["mae"] == 8.3333
    assert result["rmse"] == 8.6603
    assert result["bias"] == 5.0
    assert result["overforecast_percentage"] == 66.6667


def test_empty_pairs_returns_none_metrics():
    result = calculate_metrics([])
    assert result["n"] == 0
    assert result["mae"] is None
    assert result["rmse"] is None
    assert result["bias"] is None
    assert result["overforecast_percentage"] is None


def test_single_pair():
    result = calculate_metrics([(50.0, 40.0)])
    assert result["n"] == 1
    assert result["mae"] == 10.0
    assert result["rmse"] == 10.0
    assert result["bias"] == 10.0
    assert result["overforecast_percentage"] == 100.0


def test_underforecasting_gives_negative_bias():
    result = calculate_metrics([(80.0, 100.0), (90.0, 100.0)])
    assert result["bias"] == -15.0
    assert result["overforecast_percentage"] == 0.0


def test_all_overforecast_gives_100_percent():
    result = calculate_metrics([(110.0, 100.0), (120.0, 100.0)])
    assert result["overforecast_percentage"] == 100.0
