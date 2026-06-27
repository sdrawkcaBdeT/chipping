# Chip Tracker

Personal golf chipping tracker for `chip.cashbaggins.dev`.

This repository is currently on the **Scaffold** milestone only. The app includes a FastAPI backend, a Vite React placeholder frontend, Postgres wiring through SQLAlchemy, Alembic configuration, and Docker Compose.

## Run With Docker

```powershell
docker compose up --build
```

Then open:

- App: `http://localhost:8000`
- Health: `http://localhost:8000/api/health`

The production container serves the built React frontend from FastAPI.

## Local Backend

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r server\requirements-dev.txt
$env:DATABASE_URL = "postgresql+asyncpg://chipping:chipping@localhost:5432/chipping"
uvicorn app.main:app --app-dir server --reload
```

## Local Frontend

```powershell
cd ui\vite-project
npm install
npm run dev
```

The Vite dev server proxies `/api` requests to `http://localhost:8000`.

## Database Migrations

Alembic is configured, but there are no domain models or migrations yet.

```powershell
alembic -c alembic.ini revision --autogenerate -m "describe change"
alembic -c alembic.ini upgrade head
```

## Tests

```powershell
pytest server
cd ui\vite-project
npm run build
```

## Current Milestone Boundaries

Included:

- `/api/health`
- Postgres connectivity check from FastAPI
- Observer Mode placeholder at `/`
- Me Mode login placeholder at `/me/login`
- Docker Compose with Postgres and app container

Not included yet:

- Owner auth
- Manual sessions
- Quick Log
- Buckets
- Target Completion
- Analytics, export, prompt helper, or deployment automation
