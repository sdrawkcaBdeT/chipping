# Deployment Notes

This app is intended to be built and run on the server with Docker Compose, with Cloudflare Tunnel routing `chip.cashbaggins.dev` to the local app port.

## Server Environment

Create a real `.env` on the server from `.env.production.example`.

Required values:

- `POSTGRES_PASSWORD`
- `OWNER_PIN` or `OWNER_PASSWORD`
- `JWT_SECRET`
- `CORS_ORIGINS=https://chip.cashbaggins.dev`
- `COOKIE_SECURE=true`

Recommended port bindings for a same-host Cloudflare Tunnel:

```env
APP_PORT=127.0.0.1:8000
POSTGRES_PORT=127.0.0.1:5432
```

These keep the app and database off public interfaces while still allowing the tunnel process on the host to reach the app.

## Build And Start

From the repository root on the server:

```bash
docker compose up -d --build
docker compose ps
docker compose logs -f app
```

The app container runs Alembic migrations before starting FastAPI.

Health check:

```bash
curl http://127.0.0.1:8000/api/health
```

Expected response:

```json
{"status":"ok","database":"ok"}
```

## Cloudflare Tunnel

Configure the public hostname:

- Hostname: `chip.cashbaggins.dev`
- Service: `http://127.0.0.1:8000`

The app itself does not need to know about the tunnel beyond:

```env
CORS_ORIGINS=https://chip.cashbaggins.dev
COOKIE_SECURE=true
```

## Backups

Create a Postgres dump:

```bash
docker compose exec -T db sh -c 'pg_dump -U "$POSTGRES_USER" "$POSTGRES_DB"' > chipping-backup.sql
```

Restore into an empty database:

```bash
cat chipping-backup.sql | docker compose exec -T db sh -c 'psql -U "$POSTGRES_USER" "$POSTGRES_DB"'
```

The Docker volume is named `chipping_postgres-data` by default.

## Updates

After pulling new code:

```bash
docker compose up -d --build
docker compose logs -f app
```

Check:

- `/api/health` returns OK
- `/` loads Observer Mode
- `/me/login` accepts the owner credential
