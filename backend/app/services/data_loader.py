"""Bounded historical retrieval and local caching for Elexon datasets."""

import json
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

from app.config import settings
from app.schemas.records import NormalizedRecord
from app.services.data_validation import normalize_raw_row
from app.services.elexon_client import ElexonClient, ElexonError
from app.utils.datetime_utils import to_utc_iso


class DataLoaderError(ElexonError):
    """Raised when data loading or caching fails."""


class DataLoader:
    """Retrieve Elexon records for a bounded historical window and cache them.

    Cache files live under ``<cache_dir>/cache/raw_<source>_<key>.json`` and
    store the raw API rows plus retrieval metadata so the source request does
    not have to be repeated while the cache is valid.
    """

    def __init__(
        self,
        client: ElexonClient | None = None,
        cache_dir: Path | None = None,
    ) -> None:
        self._ec = client or ElexonClient(settings.elexon_base_url, settings.elexon_timeout_seconds)
        self.cache_dir = cache_dir or settings.data_cache_path / "cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    # -- public API -----------------------------------------------------

    def fetch_actuals(
        self,
        date_from: date,
        date_to: date,
        fuel_type: str = "WIND",
        force_refresh: bool = False,
    ) -> list[NormalizedRecord]:
        """Fetch FUELHH actuals for an inclusive settlement-date range."""
        key = f"{fuel_type}_{date_from.isoformat()}_to_{date_to.isoformat()}"
        if not force_refresh:
            cached = self._load_cache("FUELHH", key)
            if cached is not None:
                return cached

        params = {
            "settlementDateFrom": date_from.isoformat(),
            "settlementDateTo": date_to.isoformat(),
            "fuelType": fuel_type,
        }
        with self._ec as ec:
            rows = ec.get_dataset_stream("FUELHH", params)
        records = [normalize_raw_row(row, "FUELHH") for row in rows]
        records = [record for record in records if record is not None]
        self._save_cache("FUELHH", key, params, rows, records)
        return records

    def fetch_forecasts(
        self,
        publish_from: datetime,
        publish_to: datetime,
        force_refresh: bool = False,
    ) -> list[NormalizedRecord]:
        """Fetch WINDFOR publications for an inclusive publish-time window."""
        key = f"{to_utc_iso(publish_from)}_to_{to_utc_iso(publish_to)}"
        if not force_refresh:
            cached = self._load_cache("WINDFOR", key)
            if cached is not None:
                return cached

        params = {
            "publishDateTimeFrom": to_utc_iso(publish_from),
            "publishDateTimeTo": to_utc_iso(publish_to),
        }
        with self._ec as ec:
            rows = ec.get_dataset_stream("WINDFOR", params)
        records = [normalize_raw_row(row, "WINDFOR") for row in rows]
        records = [record for record in records if record is not None]
        self._save_cache("WINDFOR", key, params, rows, records)
        return records

    # -- cache ----------------------------------------------------------

    def _cache_path(self, source: str, key: str) -> Path:
        safe_key = "".join(c if c.isalnum() or c in "-_." else "_" for c in key)
        return self.cache_dir / f"raw_{source}_{safe_key}.json"

    def _load_cache(self, source: str, key: str) -> list[NormalizedRecord] | None:
        path = self._cache_path(source, key)
        if not path.exists():
            return None
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return None
        rows = payload.get("data")
        if not isinstance(rows, list):
            return None
        records = [normalize_raw_row(row, source) for row in rows]
        return [record for record in records if record is not None]

    def _save_cache(
        self,
        source: str,
        key: str,
        params: dict[str, Any],
        raw_rows: list[dict[str, Any]],
        records: list[NormalizedRecord],
    ) -> None:
        path = self._cache_path(source, key)
        payload: dict[str, Any] = {
            "source": source,
            "retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
            "time_range": key,
            "params": params,
            "row_count": len(raw_rows),
            "normalized_count": len(records),
            "data": raw_rows,
        }
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
