# Chip Tracker

Personal golf chipping tracker for `chip.cashbaggins.dev`.

This repository currently includes the scaffold, owner PIN auth, manual practice sessions, Quick Log, buckets/partial buckets, Target Completion 1-9, observer stats, export, and a prompt helper. The app includes a FastAPI backend, a Vite React frontend, Postgres wiring through SQLAlchemy, Alembic migrations, and Docker Compose.

Deployment polish is not implemented yet.

## Run With Docker

```powershell
docker compose up --build
```

Then open:

- App: `http://localhost:8000`
- Health: `http://localhost:8000/api/health`

The production container applies Alembic migrations and serves the built React frontend from FastAPI.

## Local Backend

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r server\requirements-dev.txt
$env:DATABASE_URL = "postgresql+asyncpg://chipping:chipping@localhost:5432/chipping"
$env:OWNER_PIN = "change-me"
$env:JWT_SECRET = "replace-with-a-long-random-secret"
alembic -c alembic.ini upgrade head
uvicorn app.main:app --app-dir server --reload
```

## Local Frontend

```powershell
cd ui\vite-project
npm install
npm run dev
```

The Vite dev server proxies `/api` requests to `http://localhost:8000`.

## Owner Mode

Observer Mode is the default at `/`. Owner controls are available from `/me/login` after entering the configured PIN or password.

Required owner auth environment variables:

- `OWNER_PIN` or `OWNER_PASSWORD`
- `JWT_SECRET`

Optional:

- `SESSION_DAYS`, default `30`
- `COOKIE_SECURE`, default `false`

## Database Migrations

Alembic is configured with the initial `practice_sessions` migration.

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
- Me Mode login at `/me/login`
- Signed HTTP-only owner cookie
- Owner-protected manual session routes
- Start, stop, abandon, list, view, update, and delete sessions
- One active session at a time
- Quick Log for `+42`, `+21`, `+10`, and custom ball counts
- Explicit no-active-session Quick Log behavior: start session and log, or standalone quick session
- Bucket/partial bucket persistence and session bucket listing
- Target Completion sequential 1-9 and random 1-9
- Miss, hit, undo, retrieve/end bucket, and stop game controls
- Target Completion can span multiple buckets without ending the session
- Public read-only observer stats
- Owner CSV and JSON export
- Owner prompt helper
- Docker Compose with Postgres and app container

Not included yet:

- Deployment automation and production server/Cloudflare-specific polish
