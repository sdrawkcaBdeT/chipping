# Implementation Plan

## Current milestone: Scaffold

Goal: create the initial app foundation only.

### Scope

- FastAPI backend in `server/`
- React + Vite frontend in `ui/vite-project/`
- Postgres with SQLAlchemy
- Alembic configured
- Docker Compose
- Multi-stage Dockerfile
- `.env.example`
- README
- Basic Observer Mode placeholder
- Me Mode login placeholder
- `/api/health`

### Out of scope

- Manual sessions
- Quick Log
- Target Completion
- Analytics
- Charts
- Export
- Prompt helper
- Deployment automation

### Acceptance criteria

- `docker compose up --build` starts the app.
- `/api/health` returns OK.
- FastAPI can connect to Postgres.
- React app builds.
- Visiting `/` shows an Observer Mode placeholder.
- There is a Me Mode / Log Practice button.
- Production container serves the built frontend from FastAPI.

## Milestones

1. Scaffold
2. Owner PIN auth + manual sessions
3. Quick Log + buckets/partial buckets
4. Target Completion 1-9
5. Observer dashboard + basic analytics
6. Export + LLM prompt helper
7. Deployment polish