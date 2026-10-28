"""Orchestration for matched series and accuracy summaries.

Combines forecast selection, matching to actuals, and metric calculation.
Keeps forecast selection and metric math independent of HTTP endpoint code.
"""

from collections import defaultdict
from collections.abc import Callable
from datetime import date, datetime, timedelta, timezone

from app.schemas.records import NormalizedRecord
from app.services.accuracy_calculator import calculate_metrics
from app.services.data_loader import DataLoader
from app.services.data_validation import filter_fuel_type
from app.services.forecast_selection import default_cutoff, select_all, select_latest_forecast


def aggregate_actuals_to_hourly(
    actuals: list[NormalizedRecord],
) -> list[NormalizedRecord]:
    """Aggregate half-hourly FUELHH actuals to hourly means.

    WINDFOR forecasts are hourly. To match by delivery interval, each
    delivery hour's actual is the mean of its two half-hourly FUELHH records.
    Records without an hourly-aligned ``start_time`` (minute != 0 or 30) are
    passed through unchanged.
    """
    by_hour: dict[datetime, list[NormalizedRecord]] = defaultdict(list)
    passthrough: list[NormalizedRecord] = []

    for a in actuals:
        st = a.start_time.astimezone(timezone.utc)
        if st.minute in (0, 30):
            hour_start = st.replace(minute=0, second=0, microsecond=0)
            by_hour[hour_start].append(a)
        else:
            passthrough.append(a)

    aggregated: list[NormalizedRecord] = []
    for hour_start, records in sorted(by_hour.items()):
        valid_gens = [r.generation_mw for r in records if r.generation_mw is not None]
        if not valid_gens:
            generation_mw: float | None = None
        else:
            generation_mw = sum(valid_gens) / len(valid_gens)
        # Build a synthetic hourly record from the first half-hour's metadata.
        base = records[0]
        aggregated.append(
            NormalizedRecord(
                source=base.source,
                dataset=base.dataset,
                publish_time=max(r.publish_time for r in records),
                start_time=hour_start,
                settlement_date=base.settlement_date,
                settlement_period=None,
                fuel_type=base.fuel_type,
                generation_mw=generation_mw,
            )
        )

    aggregated.extend(passthrough)
    aggregated.sort(key=lambda r: r.start_time)
    return aggregated


def compute_analysis(
    forecasts: list[NormalizedRecord],
    actuals: list[NormalizedRecord],
    cutoff_func: Callable[[datetime], datetime] = default_cutoff,
    fuel_type: str = "WIND",
) -> dict:
    """Run the full forecast-vs-actual analysis.

    Steps:

    1. Filter actuals to the requested fuel type (default WIND).
    2. Aggregate half-hourly actuals to hourly means (WINDFOR is hourly).
    3. For each hourly delivery time, select the latest forecast published at
       or before the decision cutoff.
    4. Match selected forecasts to actuals by normalized delivery interval.
    5. Calculate MAE, RMSE, bias, overforecast percentage over valid pairs.
    6. Return metrics plus coverage counts.

    Missing forecasts and missing actuals are counted separately and never
    coerced to zero.
    """
    wind_actuals = filter_fuel_type(actuals, fuel_type)
    hourly_actuals = aggregate_actuals_to_hourly(wind_actuals)

    matches = select_all(forecasts, hourly_actuals, cutoff_func=cutoff_func)

    valid_pairs: list[tuple[float, float]] = []
    missing_forecast = 0
    missing_actual = 0
    invalid_actual = 0
    invalid_forecast = 0

    for m in matches:
        fc = m["forecast"]
        act = m["actual"]

        if fc is None:
            missing_forecast += 1
            continue
        if act is None:
            missing_actual += 1
            continue

        if fc.generation_mw is None:
            invalid_forecast += 1
            continue
        if act.generation_mw is None:
            invalid_actual += 1
            continue

        valid_pairs.append((fc.generation_mw, act.generation_mw))

    metrics = calculate_metrics(valid_pairs)

    return {
        "cutoff_func_name": cutoff_func.__name__,
        "total_delivery_intervals": len(hourly_actuals),
        "matched_pairs": len(valid_pairs),
        "missing_forecast": missing_forecast,
        "missing_actual": missing_actual,
        "invalid_forecast": invalid_forecast,
        "invalid_actual": invalid_actual,
        "metrics": metrics,
        "matches": matches,
    }


def run_analysis_for_period(
    date_from: date,
    date_to: date,
    cutoff: datetime | None = None,
    fuel_type: str = "WIND",
) -> dict:
    """Fetch actuals and covering forecasts for a period and run the analysis.

    The forecast publish window is widened by two days on each side of the
    delivery period so day-ahead cutoffs (default D-1 12:00 UTC) can select a
    vintage for the earliest delivery intervals.
    """
    if date_from > date_to:
        raise ValueError("date_from must be on or before date_to")

    loader = DataLoader()
    actuals = loader.fetch_actuals(date_from, date_to, fuel_type=fuel_type)
    publish_from = datetime(
        date_from.year, date_from.month, date_from.day, tzinfo=timezone.utc
    ) - timedelta(days=2)
    publish_to = datetime(
        date_to.year, date_to.month, date_to.day, 23, 59, tzinfo=timezone.utc
    ) + timedelta(days=2)
    forecasts = loader.fetch_forecasts(publish_from, publish_to)

    cutoff_func = (lambda _: cutoff) if cutoff is not None else default_cutoff
    result = compute_analysis(forecasts, actuals, cutoff_func=cutoff_func, fuel_type=fuel_type)

    return {
        "from_date": date_from,
        "to_date": date_to,
        "decision_cutoff": cutoff,
        "metrics": result["metrics"],
        "coverage": {
            "total_delivery_intervals": result["total_delivery_intervals"],
            "matched_pairs": result["matched_pairs"],
            "missing_forecast": result["missing_forecast"],
            "missing_actual": result["missing_actual"],
            "invalid_forecast": result["invalid_forecast"],
            "invalid_actual": result["invalid_actual"],
        },
        "matches": result["matches"],
    }


def run_forecast_history(
    delivery_time: datetime,
    cutoff: datetime | None = None,
    loader: DataLoader | None = None,
) -> dict:
    """Select the forecast vintage for a single delivery interval.

    Returns the selected vintage plus eligible/excluded vintage lists for the
    delivery interval under the effective decision cutoff.
    """
    effective_cutoff = cutoff if cutoff is not None else default_cutoff(delivery_time)
    owner = loader if loader is not None else DataLoader()
    publish_from = delivery_time - timedelta(days=2)
    publish_to = delivery_time + timedelta(hours=2)
    forecasts = owner.fetch_forecasts(publish_from, publish_to)

    relevant = [f for f in forecasts if f.start_time == delivery_time]
    eligible = [f for f in relevant if f.publish_time <= effective_cutoff]
    excluded = [f for f in relevant if f.publish_time > effective_cutoff]
    selected = select_latest_forecast(relevant, delivery_time, effective_cutoff)

    def _vintage(f: NormalizedRecord) -> dict:
        return {
            "publish_time": f.publish_time,
            "start_time": f.start_time,
            "generation_mw": f.generation_mw,
        }

    return {
        "delivery_time": delivery_time,
        "cutoff": effective_cutoff,
        "selected": _vintage(selected) if selected is not None else None,
        "eligible_vintages": [_vintage(f) for f in eligible],
        "excluded_vintages": [_vintage(f) for f in excluded],
    }
