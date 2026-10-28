# WindSight

WindSight is a React dashboard and FastAPI service for reviewing UK wind
generation forecasts against historical actuals from Elexon. Forecast vintage
selection and accuracy calculations are performed by the backend.

## Run with Docker: one command for reviewers

Requirements:

- Docker Engine
- Docker Compose v2
- Network access to the public Elexon API

No `.env` file is required for the Docker workflow. Compose supplies the
non-secret runtime configuration, and the frontend is built to use the
same-origin `/api` path.

After cloning, run this from the repository root:

```bash
git clone <repository-url>
cd windsight
docker compose up --build
```

Open <http://localhost:5173>. The frontend container serves the built React
application and reverse-proxies `/api` requests to the FastAPI container, so
the browser does not need to know the internal Compose service name.

The backend is also available directly at <http://localhost:8000>, with health
status at <http://localhost:8000/api/health>. The default ports are:

| Service | URL |
| --- | --- |
| Frontend dashboard | <http://localhost:5173> |
| Backend API | <http://localhost:8000> |
| Backend health | <http://localhost:8000/api/health> |

The backend uses the live Elexon API. Downloaded source responses are stored in
the named `windsight-cache` volume and survive container restarts. Remove that
volume when a clean data refresh is required:

```bash
docker compose down -v
```

Stop the application with `Ctrl+C`, or run:

```bash
docker compose down
```

If ports `5173` or `8000` are already in use, stop the process using the port
or change the published host port in `docker-compose.yml` before starting.

No local `.env` files, credentials, virtual environments, `node_modules`, or
private development documentation are copied into the images.

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
│   │   ├── services/     # Elexon, loading, selection, and metrics logic
│   │   └── utils/
│   └── tests/
├── frontend/
│   ├── Dockerfile
│   ├── nginx.conf        # Static serving and /api reverse proxy
│   └── src/
│       ├── pages/
│       └── services/
├── docker-compose.yml
└── README.md
```

## Manual local development without Docker

This mode is separate from the one-command Docker workflow. If running the
services directly on the host, create the local environment files from the
provided examples:

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

These `.env` files are ignored by Git and are not needed by reviewers using
Docker Compose.

## Verification

```bash
cd backend && uv run pytest -q
cd frontend && npm run build && npm run lint
```

## Deployment readiness

The repository is ready for platform selection and deployment configuration:

- Docker Compose runs the frontend and backend together locally.
- The frontend uses a same-origin `/api` path, while Nginx routes API calls to
  the backend container.
- Backend and frontend production images build successfully.
- The backend uses the live Elexon API and a persistent Docker cache volume.
- No application secrets are required by the current local Docker setup.

Public hosting has not been selected or configured yet. Production deployment
environment variables, hosting-specific configuration, deployment URLs, and
production CORS settings should be added after choosing the hosting platform.

Before publishing, verify that the public repository contains no real `.env`
files, credentials, virtual environments, dependency directories, generated
build output, or the private `docs/PRD.md` document. The repository currently
keeps those paths ignored; only `.env.example` templates are intended to be
tracked.