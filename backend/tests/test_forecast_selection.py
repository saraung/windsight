"""Deterministic tests for forecast-vintage selection."""

from datetime import datetime, timezone

from app.schemas.records import NormalizedRecord
from app.services.forecast_selection import (
    default_cutoff,
    select_all,
    select_latest_forecast,
)

DELIVERY = datetime(2026, 1, 15, 12, 0, tzinfo=timezone.utc)


def _forecast(publish_time, generation):
    return NormalizedRecord(
        source="WINDFOR",
        dataset="WINDFOR",
        publish_time=publish_time,
        start_time=DELIVERY,
        generation_mw=generation,
    )


def test_selects_latest_forecast_at_or_before_cutoff():
    forecasts = [
        _forecast(datetime(2026, 1, 14, 10, 0, tzinfo=timezone.utc), 100),
        _forecast(datetime(2026, 1, 14, 12, 0, tzinfo=timezone.utc), 110),
        _forecast(datetime(2026, 1, 14, 14, 0, tzinfo=timezone.utc), 120),
    ]
    cutoff = datetime(2026, 1, 14, 13, 0, tzinfo=timezone.utc)
    selected = select_latest_forecast(forecasts, DELIVERY, cutoff)
    assert selected is not None
    assert selected.generation_mw == 110
    assert selected.publish_time == datetime(2026, 1, 14, 12, 0, tzinfo=timezone.utc)


def test_excludes_forecast_published_after_cutoff():
    forecasts = [
        _forecast(datetime(2026, 1, 14, 10, 0, tzinfo=timezone.utc), 100),
        _forecast(datetime(2026, 1, 14, 14, 0, tzinfo=timezone.utc), 120),
    ]
    cutoff = datetime(2026, 1, 14, 12, 0, tzinfo=timezone.utc)
    selected = select_latest_forecast(forecasts, DELIVERY, cutoff)
    assert selected is not None
    assert selected.generation_mw == 100


def test_returns_none_when_no_eligible_forecast():
    forecasts = [
        _forecast(datetime(2026, 1, 14, 14, 0, tzinfo=timezone.utc), 120),
        _forecast(datetime(2026, 1, 14, 16, 0, tzinfo=timezone.utc), 130),
    ]
    cutoff = datetime(2026, 1, 14, 12, 0, tzinfo=timezone.utc)
    assert select_latest_forecast(forecasts, DELIVERY, cutoff) is None


def test_returns_none_for_missing_delivery_time():
    forecasts = [
        _forecast(datetime(2026, 1, 14, 10, 0, tzinfo=timezone.utc), 100),
    ]
    other_delivery = datetime(2026, 1, 15, 13, 0, tzinfo=timezone.utc)
    cutoff = datetime(2026, 1, 14, 12, 0, tzinfo=timezone.utc)
    assert select_latest_forecast(forecasts, other_delivery, cutoff) is None


def test_tie_break_picks_greatest_generation_at_same_publish_time():
    forecasts = [
        _forecast(datetime(2026, 1, 14, 12, 0, tzinfo=timezone.utc), 100),
        _forecast(datetime(2026, 1, 14, 12, 0, tzinfo=timezone.utc), 110),
        _forecast(datetime(2026, 1, 14, 12, 0, tzinfo=timezone.utc), 105),
    ]
    cutoff = datetime(2026, 1, 14, 12, 0, tzinfo=timezone.utc)
    selected = select_latest_forecast(forecasts, DELIVERY, cutoff)
    assert selected is not None
    assert selected.generation_mw == 110


def test_cutoff_inclusive_at_exact_publish_time():
    forecasts = [
        _forecast(datetime(2026, 1, 14, 12, 0, tzinfo=timezone.utc), 100),
    ]
    cutoff = datetime(2026, 1, 14, 12, 0, tzinfo=timezone.utc)
    selected = select_latest_forecast(forecasts, DELIVERY, cutoff)
    assert selected is not None
    assert selected.generation_mw == 100


def test_default_cutoff_is_day_before_at_noon_utc():
    delivery = datetime(2026, 1, 15, 12, 0, tzinfo=timezone.utc)
    cutoff = default_cutoff(delivery)
    assert cutoff == datetime(2026, 1, 14, 12, 0, tzinfo=timezone.utc)


def test_default_cutoff_for_midnight_delivery():
    # Delivery at 00:00 on Jan 15 → cutoff Jan 14 12:00 (36 hours ahead)
    delivery = datetime(2026, 1, 15, 0, 0, tzinfo=timezone.utc)
    cutoff = default_cutoff(delivery)
    assert cutoff == datetime(2026, 1, 14, 12, 0, tzinfo=timezone.utc)


def test_select_all_matches_by_delivery_time():
    forecasts = [
        _forecast(datetime(2026, 1, 14, 10, 0, tzinfo=timezone.utc), 100),
        _forecast(datetime(2026, 1, 14, 10, 0, tzinfo=timezone.utc), 110),
    ]
    NormalizedRecord(
        source="WINDFOR",
        dataset="WINDFOR",
        publish_time=datetime(2026, 1, 14, 10, 0, tzinfo=timezone.utc),
        start_time=datetime(2026, 1, 15, 13, 0, tzinfo=timezone.utc),
        generation_mw=999,
    )
    actuals = [
        NormalizedRecord(
            source="FUELHH",
            dataset="FUELHH",
            publish_time=datetime(2026, 1, 15, 0, 30, tzinfo=timezone.utc),
            start_time=DELIVERY,
            generation_mw=90,
        ),
        NormalizedRecord(
            source="FUELHH",
            dataset="FUELHH",
            publish_time=datetime(2026, 1, 15, 1, 0, tzinfo=timezone.utc),
            start_time=datetime(2026, 1, 15, 13, 0, tzinfo=timezone.utc),
            generation_mw=50,
        ),
    ]
    cutoff = datetime(2026, 1, 14, 12, 0, tzinfo=timezone.utc)
    matches = select_all(forecasts, actuals, cutoff_func=lambda _: cutoff)

    assert len(matches) == 2
    assert matches[0]["forecast"] is not None
    assert matches[0]["forecast"].generation_mw == 110
    assert matches[0]["delivery_time"] == DELIVERY
    assert matches[1]["forecast"] is None  # no forecast for 13:00 delivery
