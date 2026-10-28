# Elexon API test fixtures

These files are **verbatim samples of live Elexon BMRS API responses**, saved for
deterministic backend tests. They are not synthetic data and must not be used as
production/dashboard data.

- Source: Elexon BMRS API v1 — <https://data.elexon.co.uk/bmrs/api/v1>
- OpenAPI document: <https://data.elexon.co.uk/swagger/v1/swagger.json>
- Retrieved: **2026-10-28T05:08:03Z**

Each JSON file wraps the API rows in a small metadata object:

```json
{
  "fixture": "...",
  "note": "...",
  "source": "...",
  "endpoint": "...",
  "request_url": "...",
  "retrieved_at_utc": "...",
  "record_count": 0,
  "data": []
}
```

## Files

| File | Records | What it contains |
|---|---|---|
| `fuelhh_wind_2026-01-01.json` | 48 | Every half-hourly `FUELHH` row with `fuelType=WIND` for 2026-01-01. |
| `windfor_publication_2026-01-01T0230Z.json` | 73 | One complete `WINDFOR` publication (`publishTime=2026-01-01T02:30:00Z`), 73 hourly rows. |
| `windfor_vintages_2026-01-15T1200Z.json` | 24 | All forecast vintages for delivery hour `startTime=2026-01-15T12:00:00Z`, filtered from the 2026-01-13 → 2026-01-16 publication window. |

## Verified field notes

`FUELHH` rows:

- `generation`: integer **MW**, average over the 30-minute settlement period.
- `startTime`: interval start, UTC (`Z`).
- `settlementDate` / `settlementPeriod`: GB settlement convention. In January,
  GMT = UTC, so period 1 starts at `00:00Z`.

`WINDFOR` rows (dataset/stream shape):

- `generation`: integer **MW**, hourly wind forecast.
- `publishTime`: forecast issue time, UTC (`Z`).
- `startTime`: delivery hour start, UTC (`Z`).
- The `/datasets/WINDFOR` endpoint has **no delivery-time filter**; only
  `publishDateTimeFrom`/`publishDateTimeTo` are supported. Without them it
  returns only the latest publication.

## Reproduce the fixtures

```bash
curl "https://data.elexon.co.uk/bmrs/api/v1/datasets/FUELHH/stream?settlementDateFrom=2026-01-01&settlementDateTo=2026-01-01&fuelType=WIND"

curl "https://data.elexon.co.uk/bmrs/api/v1/datasets/WINDFOR/stream?publishDateTimeFrom=2026-01-01T02:30Z&publishDateTimeTo=2026-01-01T02:30Z"

curl "https://data.elexon.co.uk/bmrs/api/v1/datasets/WINDFOR/stream?publishDateTimeFrom=2026-01-13T00:00Z&publishDateTimeTo=2026-01-16T00:00Z"
# then keep only rows with startTime == "2026-01-15T12:00:00Z"
```

The live API is authoritative. If Elexon revises historical values, these
fixtures remain the snapshot used by tests; update them deliberately and record
the retrieval date.
