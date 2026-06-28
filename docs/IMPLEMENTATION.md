# Implementation Status

## Current status: V0 deployed

The app is beyond the original scaffold milestone. V0 is implemented and has been deployed through the UGREEN NAS Docker Compose project plus Cloudflare Tunnel pattern.

Production hostname:

`https://chip.cashbaggins.dev`

## Completed Milestones

1. Scaffold
   - FastAPI backend in `server/`
   - React + Vite frontend in `ui/vite-project/`
   - SQLAlchemy async database wiring
   - Alembic migrations
   - Multi-stage Dockerfile
   - Docker Compose
   - `/api/health`

2. Owner auth + manual sessions
   - Owner PIN/password login
   - Signed HTTP-only cookie
   - Owner-only write routes
   - Manual session start, stop, abandon, list, view, update, and delete
   - One active session at a time

3. Quick Log + buckets
   - `+42`, `+21`, `+10`, and custom ball counts
   - Active-session logging
   - Explicit no-active-session choices
   - Standalone quick session support
   - Bucket and partial bucket persistence

4. Target Completion 1-9
   - Sequential 1-9
   - Random 1-9
   - Miss, hit, undo
   - End bucket / retrieve
   - Stop game without stopping session
   - Stop session closes active game/bucket work

5. Observer dashboard + analytics
   - Public read-only stats endpoints
   - Overview, volume, accuracy, targets, completion, and sessions
   - Dashboard renders recent volume, completion trend, target difficulty, and session history

6. Export + prompt helper
   - Owner-only JSON export
   - Owner-only CSV export
   - Owner-only practice-summary prompt helper

7. Deployment polish
   - Compose stack runs `db`, `app`, and `cloudflared`
   - App and Postgres are not exposed on host ports
   - Cloudflare routes `chip.cashbaggins.dev` to `http://app:8000`
   - Production `.env` template documents required secrets
   - Deployment notes cover UGREEN NAS and Cloudflare setup

8. App provenance and era presentation
   - Sessions store app SHA, build version, and design version
   - Existing first-live sessions are backfilled to the first live commit
   - Public dashboard includes a compact App Evolution timeline
   - Session cards show subtle era badges
   - Session detail shows the app era, visual snapshot, and code snapshot link

## Current Acceptance Snapshot

- Observer Mode loads by default at `/`.
- Observer Mode is read-only.
- Owner can enter Me Mode with the configured credential.
- Backend rejects owner writes without auth.
- Owner can manually start and stop sessions.
- Owner can log quick buckets and partial buckets.
- Owner can run Target Completion across retrievals.
- Observer stats update after practice is logged.
- Owner export and prompt helper are protected.
- Sessions carry visible app-era provenance.
- The app runs on the NAS through Docker Compose with Postgres and Cloudflare Tunnel.

## Remaining Work

These are polish items, not blockers for V0:

- Add more practice-history drilldowns once real data exists.
- Improve trend charts after enough Target Completion runs accumulate.
- Add a tested backup/restore rehearsal against a disposable database.
- Consider owner settings for default club and distance instead of fixed frontend defaults.
