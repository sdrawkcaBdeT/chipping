# Deployment Notes

This app is intended to be built and run on the server with Docker Compose, with the `cloudflared` container routing `chip.cashbaggins.dev` to the app container over the private Compose network.

## Server Environment

Create a real `.env` on the server from `.env.production.example`.

Required values:

- `POSTGRES_PASSWORD`
- `OWNER_PIN` or `OWNER_PASSWORD`
- `JWT_SECRET`
- `CF_TUNNEL_TOKEN`
- `CORS_ORIGINS=https://chip.cashbaggins.dev`
- `COOKIE_SECURE=true`

The Compose stack does not publish the app or Postgres to host ports. Cloudflare reaches the app at `http://app:8000` from the `cloudflared` container.

## Build And Start

From the repository root on the server:

```bash
docker compose up -d --build
docker compose ps
docker compose logs -f app
docker compose logs -f cloudflared
```

The app container runs Alembic migrations before starting FastAPI.

Health check:

```bash
docker compose exec app python -c "import urllib.request; print(urllib.request.urlopen('http://127.0.0.1:8000/api/health').read().decode())"
```

Expected response:

```json
{"status":"ok","database":"ok"}
```

## Cloudflare Tunnel

Configure the public hostname:

- Hostname: `chip.cashbaggins.dev`
- Service: `http://app:8000`

The app itself does not need to know about the tunnel beyond:

```env
CORS_ORIGINS=https://chip.cashbaggins.dev
COOKIE_SECURE=true
```

When Cloudflare asks for the connector environment, choose **Docker**. Copy the tunnel token from the Docker command Cloudflare shows and put only the token value in `.env` as `CF_TUNNEL_TOKEN`.

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
