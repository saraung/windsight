"""Report operational status for the local Elexon cache."""

import json
import os
from datetime import datetime, timezone
from pathlib import Path

from app.config import BACKEND_DIR, settings


def _cache_dir_display(cache_dir: Path) -> str:
    try:
        return str(cache_dir.relative_to(BACKEND_DIR))
    except ValueError:
        return "configured cache directory"


def _parse_retrieved_at(value: object) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _source_status(source: str, cache_dir: Path, now: datetime) -> dict:
    files = sorted(cache_dir.glob(f"raw_{source}_*.json"))
    latest_payload: dict | None = None
    latest_retrieved: datetime | None = None

    for path in files:
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if not isinstance(payload, dict):
            continue
        retrieved = _parse_retrieved_at(payload.get("retrieved_at_utc"))
        if retrieved is None:
            continue
        if latest_retrieved is None or retrieved > latest_retrieved:
            latest_retrieved = retrieved
            latest_payload = payload

    age_hours = None
    if latest_retrieved is not None:
        age_hours = round((now - latest_retrieved).total_seconds() / 3600.0, 2)

    return {
        "source": source,
        "cached": latest_payload is not None,
        "files": len(files),
        "last_retrieved_utc": latest_retrieved,
        "age_hours": age_hours,
        "stale": age_hours is not None and age_hours > settings.cache_ttl_hours,
        "row_count": latest_payload.get("row_count") if latest_payload else None,
        "normalized_count": latest_payload.get("normalized_count") if latest_payload else None,
    }


def get_data_status() -> dict:
    """Return cache metadata without exposing absolute filesystem paths."""
    now = datetime.now(timezone.utc)
    cache_dir = settings.data_cache_path / "cache"
    probe_dir = cache_dir if cache_dir.exists() else cache_dir.parent
    writable = probe_dir.exists() and os.access(probe_dir, os.W_OK)

    sources = {source: _source_status(source, cache_dir, now) for source in ("FUELHH", "WINDFOR")}

    return {
        "status": "ok" if writable else "degraded",
        "checked_at_utc": now,
        "cache_dir": _cache_dir_display(cache_dir),
        "cache_writable": writable,
        "cache_ttl_hours": settings.cache_ttl_hours,
        "sources": sources,
    }
