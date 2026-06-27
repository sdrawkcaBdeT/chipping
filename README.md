# Chip Tracker

Personal golf chipping tracker for `chip.cashbaggins.dev`.

This repository includes the V0 app: owner PIN auth, manual practice sessions, Quick Log, buckets/partial buckets, Target Completion 1-9, observer stats, export, a prompt helper, and the NAS/Cloudflare deployment pattern. The app includes a FastAPI backend, a Vite React frontend, Postgres wiring through SQLAlchemy, Alembic migrations, and Docker Compose.

Current implementation status is tracked in `docs/IMPLEMENTATION.md`. The working roadmap is in `docs/ROADMAP.md`. Deployment notes are in `docs/DEPLOYMENT.md`.

## Run With Docker

```powershell
docker compose --env-file .env up -d --build
```

Then open:

- App: `https://chip.cashbaggins.dev` after Cloudflare Tunnel is connected
- Health: `/api/health`

The production container applies Alembic migrations and serves the built React frontend from FastAPI. The Compose stack includes a `cloudflared` container and does not publish app or database ports to the host.

For the server/Cloudflare handoff, copy `.env.production.example` to `.env` on the server and follow `docs/DEPLOYMENT.md`.

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
- `APP_GIT_SHA`, `APP_BUILD_VERSION`, and `DESIGN_VERSION` for session provenance

## Database Migrations

Alembic migrations cover sessions, buckets, and Target Completion.

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

## Implemented V0 Surface

Included:

- `/api/health`
- Postgres connectivity check from FastAPI
- Observer Mode dashboard at `/`
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
- Docker Compose with Postgres, app, and Cloudflare Tunnel containers

Operational follow-ups:

- Automated server provisioning is not included.
- Backups should be rehearsed against a disposable database before relying on them.
