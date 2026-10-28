# WindSight

WindSight is a React dashboard and FastAPI service for evaluating UK wind
generation forecasts against historical metered output from Elexon BMRS.

The analysis answers a practical question: **how reliable was the forecast that
was actually available before delivery?** For every hourly delivery interval it
selects the latest WINDFOR vintage published at or before a configurable
decision cutoff, matches it to FUELHH wind actuals, and reports accuracy,
coverage, and forecast-direction metrics.

## Live demo

| Service | URL |
| --- | --- |
| Dashboard | <https://windsight-mu.vercel.app/> |
| Backend API | <https://windsight-lpuk.onrender.com> |
| API health | <https://windsight-lpuk.onrender.com/api/health> |
| Repository | <https://github.com/saraung/windsight> |

The frontend is deployed on Vercel and the backend on Render. The backend runs
outside Docker in production; Docker Compose is the local reproduction path.
Render free instances can take up to a minute to wake and do not provide a
durable local cache, so the first request after a restart may be slower.

## What it does

- Retrieves January 2026 wind actuals and forecast vintages from the public
  Elexon BMRS API.
- Preserves both forecast `publishTime` and delivery `startTime`.
- Supports per-delivery decision cutoffs:
  - day-ahead 12:00 UTC (default)
  - day-ahead 00:00 UTC
  - 24, 12, 2, or 1 hours before delivery
  - a single absolute cutoff, allowed only when it is at or before the first
    delivery interval
- Selects the latest eligible vintage for each delivery hour and never
  substitutes a later forecast.
- Aggregates half-hourly FUELHH actuals to hourly means only when both
  half-hours are present and valid.
- Reports matched pairs, missing forecasts, missing actuals, missing-both
  intervals, invalid records, incomplete half-hour actuals, and coverage.
- Calculates MAE, RMSE, bias, over/underforecast frequency, and signed-error
  P10/P50/P90.
- Exposes the selected vintage and eligible/excluded publications for any
  delivery hour.
- Shows source/cache status from the backend instead of assuming connectivity.

## Important data limitation

WINDFOR is a **total wind** forecast, while FUELHH `WIND` is
**transmission-metered** wind output. They are the two datasets in the
assignment scope, but they are not identical quantities. Embedded/onshore
generation can make FUELHH lower than WINDFOR, so part of the measured bias and
MAE is a measurement-scope difference, not forecast error.

The app therefore makes the mismatch visible and should be read as a
directional, decision-time comparison rather than an exact settlement or
procurement calculation. Demand, thermal generation, imbalance prices, and
total extra procurement are outside the scope of this project.

## Architecture

```text
Browser
  │
  ├── React + TypeScript + Vite + Tailwind CSS
  │     ├── shared period/cutoff controls
  │     ├── overview and decision interpretation
  │     ├── forecast-vs-actual timeline
  │     ├── forecast-vintage history
  │     └── backend cache/status banner
  │
  └── FastAPI backend
        ├── /api/overview
        ├── /api/accuracy
        ├── /api/timeseries
        ├── /api/forecast-history
        ├── /api/data-status
        └── /api/health
              │
              ├── bounded Elexon retrieval + retry/backoff
              ├── local raw cache with TTL metadata
              ├── forecast selection by publish cutoff
              ├── hourly actual aggregation
              └── coverage + accuracy metrics
```

Forecast selection, matching, and metric calculations live in the service layer
and are independent of HTTP handlers. API responses are typed with Pydantic on
the backend and mirrored in TypeScript on the frontend.

## Repository structure

```text
windsight/
├── backend/
│   ├── Dockerfile
│   ├── pyproject.toml
│   ├── uv.lock
│   ├── app/
│   │   ├── api/          # FastAPI route handlers
│   │   ├── schemas/      # Pydantic response models
│   │   ├── services/     # Elexon, loading, selection, metrics, status
│   │   └── utils/
│   └── tests/
├── frontend/
│   ├── Dockerfile
│   ├── nginx.conf        # static serving + /api reverse proxy
│   └── src/
│       ├── components/
│       ├── config/
│       ├── hooks/
│       ├── pages/
│       └── services/
├── docker-compose.yml
└── README.md
```

## Run locally with Docker

Requirements:

- Docker Engine
- Docker Compose v2
- Network access to the public Elexon API

No `.env` file is required for this workflow. Compose supplies non-secret
runtime configuration, and the frontend is built to use the same-origin `/api`
path.

```bash
git clone https://github.com/saraung/windsight.git
cd windsight
docker compose up --build
```

Open <http://localhost:5173>. The frontend container serves the production
build and reverse-proxies `/api` to FastAPI.

| Service | URL |
| --- | --- |
| Dashboard | <http://localhost:5173> |
| Backend API | <http://localhost:8000> |
| API health | <http://localhost:8000/api/health> |
| API docs | <http://localhost:8000/docs> |

Downloaded Elexon responses are stored in the named `windsight-cache` volume
and survive container restarts. Remove the volume for a clean refresh:

```bash
docker compose down -v
```

Stop the app with `Ctrl+C`, or:

```bash
docker compose down
```

If ports `5173` or `8000` are already in use, stop the process using the port
or change the published host port in `docker-compose.yml`.

## Manual development without Docker

Backend:

```bash
cd backend
cp .env.example .env
uv sync
uv run uvicorn app.main:app --reload
```

Frontend:

```bash
cd frontend
cp .env.example .env
npm ci
npm run dev
```

For the Vite development server, set:

```env
VITE_API_BASE_URL=http://localhost:8000/api
```

The local `.env` files are ignored by Git and are not needed for Docker.

## Configuration

Backend variables (see `backend/.env.example`):

| Variable | Default | Purpose |
| --- | --- | --- |
| `APP_ENV` | `development` | Runtime environment label |
| `DEBUG` | `true` | Debug flag |
| `ELEXON_BASE_URL` | `https://data.elexon.co.uk/bmrs/api/v1` | Elexon API root |
| `ELEXON_TIMEOUT_SECONDS` | `30` | HTTP timeout |
| `ELEXON_MAX_RETRIES` | `2` | Retries for transient failures |
| `ELEXON_RETRY_BACKOFF_SECONDS` | `0.5` | Exponential backoff base |
| `CORS_ORIGINS` | local Vite origins | Comma-separated allowed origins |
| `DATA_CACHE_DIR` | `app/data` | Cache root relative to the backend directory |
| `CACHE_TTL_HOURS` | `24` | Raw cache freshness threshold |

Frontend variable:

| Variable | Purpose |
| --- | --- |
| `VITE_API_BASE_URL` | Backend API root, including `/api` |

Production CORS must include the deployed frontend origin. No credentials or
secrets are required by the current application.

## API

| Endpoint | Purpose |
| --- | --- |
| `GET /api/health` | Service status |
| `GET /api/data-status` | Cache/source freshness metadata |
| `GET /api/overview?from=2026-01-01&to=2026-01-31` | Headline metrics and daily breakdown |
| `GET /api/accuracy?from=...&to=...` | Accuracy metrics and coverage |
| `GET /api/timeseries?from=...&to=...` | Forecast/actual points with error and lead time |
| `GET /api/forecast-history?delivery_time=2026-01-15T12:00Z` | Selected, eligible, and excluded vintages |

Period endpoints accept either `cutoff_preset=day_ahead_noon` (default) or
`decision_cutoff=<ISO-8601 UTC>`. Absolute cutoffs later than the first delivery
interval return HTTP 422. Naive timestamps are rejected. Upstream Elexon
failures return HTTP 502 rather than fabricated or empty data.

## Methodology

1. Fetch FUELHH actuals for the settlement-date range and WINDFOR publications
   from two days before the first delivery through two days after the last.
2. Normalize timestamps to UTC. Missing or invalid generation values remain
   missing; they are never replaced with zero.
3. Filter actuals to `fuelType == "WIND"`.
4. Aggregate each half-hourly hour to a mean only when both `:00` and `:30`
   records exist and both generation values are valid.
5. For each expected hourly delivery interval, compute the cutoff. Choose the
   latest forecast with `publish_time <= cutoff`; ties break deterministically.
6. Match selected forecasts to actuals by exact normalized delivery timestamp.
7. Calculate metrics over valid pairs only. Forecast error is
   `forecast_mw - actual_mw`; positive bias means overforecasting.
8. Return explicit coverage counts so excluded data remains visible.

The default D-1 12:00 UTC cutoff is an assumption, not a claimed market
gate-closure time. Change it in the UI or API to test other decision rules.

## Verification

Backend:

```bash
cd backend
uv run pytest -q
uv run ruff check app tests
uv run ruff format --check app tests
```

Frontend:

```bash
cd frontend
npm run build
npm run lint
```

At the time of writing:

- Backend: 70 tests passing; Ruff check and format check clean.
- Frontend: production build passes; oxlint is clean.

## Deployment notes

- Frontend: Vercel project using `npm run build` and `dist/` output.
- Backend: Render Python service running Uvicorn.
- Production backend CORS includes the Vercel origin.
- The frontend reads `VITE_API_BASE_URL` at build time; set it in the Vercel
  project environment to the Render backend URL plus `/api`.
- Docker is used for local reproduction, not as the production runtime.

## Limitations

- WINDFOR and FUELHH do not measure the same wind scope; absolute error and bias
  include a measurement gap.
- The analysis evaluates forecast accuracy, not trading profitability,
  imbalance prices, demand, or total thermal procurement.
- January 2026 is the assignment period; the UI defaults to it but the API can
  evaluate other bounded periods.
- Render free-tier cold starts and ephemeral storage can cause slower first
  requests and re-downloads.
- Elexon data availability and retention are controlled by the upstream service.

## AI tools

ChatGPT and DeepSeek were used during development for research, implementation
support, test writing, and documentation. All production data is fetched from
Elexon at request time; the app does not fabricate metrics or use fixture data in
the deployed dashboard. The final methodology, verification, and submission
decisions remain the author's responsibility.
