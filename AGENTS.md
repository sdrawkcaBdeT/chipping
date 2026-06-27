# AGENTS.md

## Project

This repo is the personal golf chipping tracker for chip.cashbaggins.dev.

Read `docs/SPEC.md` before implementing product behavior.

## Stack

- FastAPI backend in `server/`
- React + Vite frontend in `ui/vite-project/`
- Postgres with SQLAlchemy and Alembic
- Docker Compose deployment
- Mobile-first UI

## Working rules

- Do not implement the whole spec in one giant pass unless explicitly asked.
- Work in small, reviewable milestones.
- Keep Observer Mode read-only by default.
- Keep Me Mode owner-only.
- Manual session start/stop is mandatory.
- Quick Log must stay extremely low-friction.
- Target Completion 1-9 is the flagship structured game.
- Do not add Google Forms import.
- Prefer simple, boring implementation over clever abstractions.
- Add or update tests for backend behavior when changing models/routes.
- After changes, report:
  - what changed
  - how to run it
  - what tests were run
  - what remains