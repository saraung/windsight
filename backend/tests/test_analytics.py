"""Integration-style tests for the analysis orchestration layer."""

from datetime import datetime, timezone

from app.schemas.records import NormalizedRecord
from app.services.analytics import aggregate_actuals_to_hourly, compute_analysis
from app.services.forecast_selection import default_cutoff

DELIVERY_12 = datetime(2026, 1, 15, 12, 0, tzinfo=timezone.utc)
DELIVERY_13 = datetime(2026, 1, 15, 13, 0, tzinfo=timezone.utc)


def _actual(start_time, generation):
    return NormalizedRecord(
        source="FUELHH",
        dataset="FUELHH",
        publish_time=start_time.replace(minute=30),
        start_time=start_time,
        settlement_date="2026-01-15",
        settlement_period=25 if start_time.hour == 12 else 27,
        fuel_type="WIND",
        generation_mw=generation,
    )


def _forecast(publish_time, start_time, generation):
    return NormalizedRecord(
        source="WINDFOR",
        dataset="WINDFOR",
        publish_time=publish_time,
        start_time=start_time,
        generation_mw=generation,
    )


def test_aggregate_actuals_to_hourly_means_two_half_hours():
    h1_0 = _actual(datetime(2026, 1, 15, 12, 0, tzinfo=timezone.utc), 100)
    h1_30 = _actual(datetime(2026, 1, 15, 12, 30, tzinfo=timezone.utc), 110)
    hourly = aggregate_actuals_to_hourly([h1_0, h1_30])
    assert len(hourly) == 1
    assert hourly[0].start_time == datetime(2026, 1, 15, 12, 0, tzinfo=timezone.utc)
    assert hourly[0].generation_mw == 105.0


def test_aggregate_actuals_skips_hour_with_no_valid_generation():
    h1_0 = _actual(datetime(2026, 1, 15, 12, 0, tzinfo=timezone.utc), None)
    h1_30 = _actual(datetime(2026, 1, 15, 12, 30, tzinfo=timezone.utc), None)
    hourly = aggregate_actuals_to_hourly([h1_0, h1_30])
    assert len(hourly) == 1
    assert hourly[0].generation_mw is None


def test_compute_analysis_counts_and_metrics():
    # One missing forecast (no WINDFOR for 13:00), one valid pair at 12:00
    forecasts = [
        _forecast(datetime(2026, 1, 14, 10, 0, tzinfo=timezone.utc), DELIVERY_12, 100),
    ]
    actuals = [
        _actual(DELIVERY_12, 90),  # valid pair: error +10
        _actual(DELIVERY_13, 80),  # missing forecast
    ]
    cutoff = datetime(2026, 1, 14, 12, 0, tzinfo=timezone.utc)
    result = compute_analysis(
        forecasts,
        actuals,
        cutoff_func=lambda _: cutoff,
    )

    assert result["total_delivery_intervals"] == 2
    assert result["matched_pairs"] == 1
    assert result["missing_forecast"] == 1
    assert result["missing_actual"] == 0
    assert result["metrics"]["n"] == 1
    assert result["metrics"]["mae"] == 10.0
    assert result["metrics"]["bias"] == 10.0
    assert result["metrics"]["overforecast_percentage"] == 100.0


def test_compute_analysis_missing_actual_not_zero():
    forecasts = [
        _forecast(datetime(2026, 1, 14, 10, 0, tzinfo=timezone.utc), DELIVERY_12, 100),
    ]
    actuals = [
        _actual(DELIVERY_12, None),  # missing actual → excluded, not zero
    ]
    cutoff = datetime(2026, 1, 14, 12, 0, tzinfo=timezone.utc)
    result = compute_analysis(
        forecasts,
        actuals,
        cutoff_func=lambda _: cutoff,
    )
    assert result["total_delivery_intervals"] == 1
    assert result["matched_pairs"] == 0
    assert result["invalid_actual"] == 1
    assert result["metrics"]["n"] == 0
    assert result["metrics"]["mae"] is None


def test_compute_analysis_uses_default_cutoff():
    forecasts = [
        _forecast(datetime(2026, 1, 13, 22, 30, tzinfo=timezone.utc), DELIVERY_12, 100),
        _forecast(datetime(2026, 1, 14, 10, 0, tzinfo=timezone.utc), DELIVERY_12, 110),
        # Published after D-1 12:00 cutoff → must not be selected
        _forecast(datetime(2026, 1, 14, 13, 0, tzinfo=timezone.utc), DELIVERY_12, 999),
    ]
    actuals = [_actual(DELIVERY_12, 90)]
    result = compute_analysis(forecasts, actuals, cutoff_func=default_cutoff)

    assert result["matched_pairs"] == 1
    m = result["matches"][0]
    assert m["forecast"] is not None
    assert m["forecast"].generation_mw == 110
    assert m["cutoff"] == datetime(2026, 1, 14, 12, 0, tzinfo=timezone.utc)
