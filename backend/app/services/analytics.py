"""Orchestration for matched series and accuracy summaries.

Combines forecast selection, matching to actuals, and metric calculation.
Keeps forecast selection and metric math independent of HTTP endpoint code.
"""

from collections import defaultdict
from collections.abc import Callable
from datetime import date, datetime, timedelta, timezone

from app.schemas.records import NormalizedRecord
from app.services.accuracy_calculator import calculate_daily_metrics, calculate_metrics
from app.services.data_loader import DataLoader
from app.services.data_validation import filter_fuel_type
from app.services.forecast_selection import (
    DEFAULT_CUTOFF_PRESET,
    CutoffPreset,
    cutoff_description,
    cutoff_for_preset,
    cutoff_label,
    default_cutoff,
    make_cutoff_func,
    parse_cutoff_preset,
    select_for_delivery_times,
    select_latest_forecast,
)
from app.utils.datetime_utils import parse_utc


def expected_hourly_intervals(date_from: date, date_to: date) -> list[datetime]:
    """Return every hourly UTC delivery interval in an inclusive date period."""
    current = datetime(date_from.year, date_from.month, date_from.day, tzinfo=timezone.utc)
    end = datetime(date_to.year, date_to.month, date_to.day, tzinfo=timezone.utc) + timedelta(
        days=1
    )
    intervals: list[datetime] = []
    while current < end:
        intervals.append(current)
        current += timedelta(hours=1)
    return intervals


def aggregate_actuals_to_hourly(
    actuals: list[NormalizedRecord],
) -> list[NormalizedRecord]:
    """Aggregate half-hourly FUELHH actuals to hourly means.

    WINDFOR forecasts are hourly. To match by delivery interval, each
    delivery hour's actual is the mean of its two half-hourly FUELHH records.
    An hour is only valid when both half-hour records are present and have a
    numeric generation value. Records without an hourly-aligned ``start_time``
    (minute not 0 or 30) are passed through unchanged.
    """
    by_hour: dict[datetime, list[NormalizedRecord]] = defaultdict(list)
    passthrough: list[NormalizedRecord] = []

    for actual in actuals:
        start_time = actual.start_time.astimezone(timezone.utc)
        if start_time.minute in (0, 30):
            hour_start = start_time.replace(minute=0, second=0, microsecond=0)
            by_hour[hour_start].append(actual)
        else:
            passthrough.append(actual)

    aggregated: list[NormalizedRecord] = []
    for hour_start, records in sorted(by_hour.items()):
        minutes = {record.start_time.astimezone(timezone.utc).minute for record in records}
        valid_generations = [
            record.generation_mw for record in records if record.generation_mw is not None
        ]
        generation_mw: float | None
        if minutes != {0, 30} or len(valid_generations) != 2:
            generation_mw = None
        else:
            generation_mw = sum(valid_generations) / 2

        base = records[0]
        aggregated.append(
            NormalizedRecord(
                source=base.source,
                dataset=base.dataset,
                publish_time=max(record.publish_time for record in records),
                start_time=hour_start,
                settlement_date=base.settlement_date,
                settlement_period=None,
                fuel_type=base.fuel_type,
                generation_mw=generation_mw,
            )
        )

    aggregated.extend(passthrough)
    aggregated.sort(key=lambda record: record.start_time)
    return aggregated


def _half_hour_minutes(actuals: list[NormalizedRecord]) -> dict[datetime, set[int]]:
    """Map each UTC hour to the half-hour minutes that have a generation value."""
    minutes: dict[datetime, set[int]] = defaultdict(set)
    for actual in actuals:
        start_time = actual.start_time.astimezone(timezone.utc)
        if start_time.minute not in (0, 30):
            continue
        hour_start = start_time.replace(minute=0, second=0, microsecond=0)
        if actual.generation_mw is not None:
            minutes[hour_start].add(start_time.minute)
    return minutes


def compute_analysis(
    forecasts: list[NormalizedRecord],
    actuals: list[NormalizedRecord],
    cutoff_func: Callable[[datetime], datetime] = default_cutoff,
    fuel_type: str = "WIND",
    delivery_times: list[datetime] | None = None,
) -> dict:
    """Run the full forecast-vs-actual analysis.

    Steps:

    1. Filter actuals to the requested fuel type (default WIND).
    2. Aggregate half-hourly actuals to hourly means (WINDFOR is hourly).
    3. For each requested delivery time, select the latest forecast published
       at or before the decision cutoff.
    4. Match selected forecasts to actuals by normalized delivery interval.
    5. Calculate MAE, RMSE, bias, quantiles, and forecast-direction metrics.
    6. Return metrics plus explicit coverage counts.

    Coverage categories are counted independently, so a missing actual and a
    missing forecast can both be true for the same interval. Missing data is
    never coerced to zero.
    """
    wind_actuals = filter_fuel_type(actuals, fuel_type)
    hourly_actuals = aggregate_actuals_to_hourly(wind_actuals)
    actual_by_start = {record.start_time: record for record in hourly_actuals}
    half_hour_minutes = _half_hour_minutes(wind_actuals)

    if delivery_times is None:
        requested_times = sorted(actual_by_start)
    else:
        requested_times = sorted(set(delivery_times))

    matches = select_for_delivery_times(forecasts, requested_times, cutoff_func=cutoff_func)
    for match in matches:
        match["actual"] = actual_by_start.get(match["delivery_time"])

    valid_pairs: list[tuple[float, float]] = []
    dated_pairs: list[tuple[date, float, float]] = []
    missing_forecast = 0
    missing_actual = 0
    missing_both = 0
    invalid_forecast = 0
    invalid_actual = 0
    incomplete_actual = 0

    for match in matches:
        forecast = match["forecast"]
        actual = match["actual"]
        delivery_time = match["delivery_time"]

        if actual is None:
            missing_actual += 1
        elif actual.generation_mw is None:
            invalid_actual += 1
            if len(half_hour_minutes.get(delivery_time, set())) < 2:
                incomplete_actual += 1

        if forecast is None:
            missing_forecast += 1
        elif forecast.generation_mw is None:
            invalid_forecast += 1

        if actual is None and forecast is None:
            missing_both += 1

        if (
            actual is not None
            and forecast is not None
            and actual.generation_mw is not None
            and forecast.generation_mw is not None
        ):
            valid_pairs.append((forecast.generation_mw, actual.generation_mw))
            dated_pairs.append((delivery_time.date(), forecast.generation_mw, actual.generation_mw))

    metrics = calculate_metrics(valid_pairs)
    daily = calculate_daily_metrics(dated_pairs)
    cutoffs = [match["cutoff"] for match in matches]
    total = len(matches)
    matched = len(valid_pairs)

    return {
        "cutoff_func_name": getattr(cutoff_func, "__name__", "custom"),
        "total_delivery_intervals": total,
        "matched_pairs": matched,
        "missing_forecast": missing_forecast,
        "missing_actual": missing_actual,
        "missing_both": missing_both,
        "invalid_forecast": invalid_forecast,
        "invalid_actual": invalid_actual,
        "incomplete_actual": incomplete_actual,
        "coverage_percentage": round(100.0 * matched / total, 4) if total else None,
        "metrics": metrics,
        "daily": daily,
        "cutoff_start": min(cutoffs) if cutoffs else None,
        "cutoff_end": max(cutoffs) if cutoffs else None,
        "matches": matches,
    }


def _resolve_period_cutoff(
    date_from: date,
    cutoff: datetime | None,
    cutoff_preset: str | CutoffPreset | None,
) -> tuple[datetime | None, CutoffPreset | None, Callable[[datetime], datetime]]:
    """Validate and resolve the period cutoff configuration."""
    if cutoff is not None and cutoff_preset is not None:
        raise ValueError("provide either decision_cutoff or cutoff_preset, not both")

    if cutoff is not None:
        absolute = parse_utc(cutoff)
        first_delivery = datetime(
            date_from.year, date_from.month, date_from.day, tzinfo=timezone.utc
        )
        if absolute > first_delivery:
            raise ValueError(
                "decision_cutoff must be at or before the first delivery interval "
                f"({first_delivery.isoformat()}); use cutoff_preset for a per-delivery cutoff"
            )
        return absolute, None, lambda _delivery: absolute

    preset = parse_cutoff_preset(cutoff_preset)
    return None, preset, make_cutoff_func(preset)


def run_analysis_for_period(
    date_from: date,
    date_to: date,
    cutoff: datetime | None = None,
    cutoff_preset: str | CutoffPreset | None = None,
    fuel_type: str = "WIND",
) -> dict:
    """Fetch actuals and covering forecasts for a period and run the analysis.

    The forecast publish window is widened by two days on each side of the
    delivery period so day-ahead cutoffs can select a vintage for the earliest
    delivery intervals.
    """
    if date_from > date_to:
        raise ValueError("date_from must be on or before date_to")

    decision_cutoff, preset, cutoff_func = _resolve_period_cutoff(date_from, cutoff, cutoff_preset)
    delivery_times = expected_hourly_intervals(date_from, date_to)

    loader = DataLoader()
    actuals = loader.fetch_actuals(date_from, date_to, fuel_type=fuel_type)
    publish_from = datetime(
        date_from.year, date_from.month, date_from.day, tzinfo=timezone.utc
    ) - timedelta(days=2)
    publish_to = datetime(
        date_to.year, date_to.month, date_to.day, 23, 59, tzinfo=timezone.utc
    ) + timedelta(days=2)
    forecasts = loader.fetch_forecasts(publish_from, publish_to)

    result = compute_analysis(
        forecasts,
        actuals,
        cutoff_func=cutoff_func,
        fuel_type=fuel_type,
        delivery_times=delivery_times,
    )

    if decision_cutoff is not None:
        mode = "absolute"
        preset_value = None
        label = f"Absolute cutoff: {decision_cutoff.isoformat()}"
        description = (
            "One fixed decision timestamp applied to all delivery intervals. "
            "Only safe when it is at or before the first delivery interval."
        )
    else:
        assert preset is not None
        mode = "per_delivery"
        preset_value = preset.value
        label = cutoff_label(preset)
        description = cutoff_description(preset)

    return {
        "from_date": date_from,
        "to_date": date_to,
        "decision_cutoff": decision_cutoff,
        "cutoff_mode": mode,
        "cutoff_preset": preset_value,
        "cutoff_label": label,
        "cutoff_description": description,
        "cutoff_start": result["cutoff_start"],
        "cutoff_end": result["cutoff_end"],
        "metrics": result["metrics"],
        "daily": result["daily"],
        "coverage": {
            "total_delivery_intervals": result["total_delivery_intervals"],
            "matched_pairs": result["matched_pairs"],
            "missing_forecast": result["missing_forecast"],
            "missing_actual": result["missing_actual"],
            "missing_both": result["missing_both"],
            "invalid_forecast": result["invalid_forecast"],
            "invalid_actual": result["invalid_actual"],
            "incomplete_actual": result["incomplete_actual"],
            "coverage_percentage": result["coverage_percentage"],
        },
        "matches": result["matches"],
    }


def run_forecast_history(
    delivery_time: datetime,
    cutoff: datetime | None = None,
    cutoff_preset: str | CutoffPreset | None = None,
    loader: DataLoader | None = None,
) -> dict:
    """Select the forecast vintage for a single delivery interval.

    Returns the selected vintage plus eligible/excluded vintage lists for the
    delivery interval under the effective decision cutoff.
    """
    delivery = parse_utc(delivery_time)
    if cutoff is not None and cutoff_preset is not None:
        raise ValueError("provide either decision_cutoff or cutoff_preset, not both")

    if cutoff is not None:
        effective_cutoff = parse_utc(cutoff)
        if effective_cutoff > delivery:
            raise ValueError(
                "decision_cutoff must be at or before delivery_time; "
                "a later cutoff would evaluate a forecast published after delivery"
            )
        mode = "absolute"
        preset = None
        label = f"Absolute cutoff: {effective_cutoff.isoformat()}"
        description = "One fixed decision timestamp for this delivery interval."
    else:
        preset = parse_cutoff_preset(cutoff_preset)
        effective_cutoff = cutoff_for_preset(preset, delivery)
        mode = "per_delivery"
        label = cutoff_label(preset)
        description = cutoff_description(preset)

    owner = loader if loader is not None else DataLoader()
    publish_from = delivery - timedelta(days=3)
    publish_to = delivery + timedelta(hours=2)
    forecasts = owner.fetch_forecasts(publish_from, publish_to)

    relevant = [forecast for forecast in forecasts if forecast.start_time == delivery]
    eligible = [forecast for forecast in relevant if forecast.publish_time <= effective_cutoff]
    excluded = [forecast for forecast in relevant if forecast.publish_time > effective_cutoff]
    selected = select_latest_forecast(relevant, delivery, effective_cutoff)

    def _vintage(forecast: NormalizedRecord) -> dict:
        return {
            "publish_time": forecast.publish_time,
            "start_time": forecast.start_time,
            "generation_mw": forecast.generation_mw,
            "lead_time_hours": round(
                (delivery - forecast.publish_time).total_seconds() / 3600.0, 4
            ),
        }

    return {
        "delivery_time": delivery,
        "cutoff": effective_cutoff,
        "cutoff_mode": mode,
        "cutoff_preset": preset.value if preset is not None else None,
        "cutoff_label": label,
        "cutoff_description": description,
        "selected": _vintage(selected) if selected is not None else None,
        "eligible_vintages": [_vintage(forecast) for forecast in eligible],
        "excluded_vintages": [_vintage(forecast) for forecast in excluded],
    }


__all__ = [
    "DEFAULT_CUTOFF_PRESET",
    "aggregate_actuals_to_hourly",
    "compute_analysis",
    "expected_hourly_intervals",
    "run_analysis_for_period",
    "run_forecast_history",
]
