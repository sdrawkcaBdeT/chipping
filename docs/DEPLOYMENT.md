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

## UGREEN NAS Docker App

The deployed pattern is one UGREEN Docker project named `chipping`, pointed at the repository folder:

```text
../python_projects/chipping
```

That folder should contain:

```text
docker-compose.yml
.env
Dockerfile
server/
ui/
```

Create the Docker project from `docker-compose.yml`. The project should build/start these containers together:

- `chipping-db-1`
- `chipping-app-1`
- `chipping-cloudflared-1`

The UGREEN UI may show a build/deploy step before the containers are actually running. Cloudflare will not show the connector as online until `cloudflared` has started and checked in.

Expected harmless build warning:

```text
current commit information was not captured by the build ... git was not found
```

## Deploy Script

The local deploy script mirrors the BID workflow:

```bash
./deploy.sh
```

It runs from the local machine, updates the NAS-mounted repo at `/z/chipping` from GitHub `main`, copies the tracked `docker-compose.yml` to `docker-compose.yaml` for the UGREEN Docker project, then SSHes into the NAS to rebuild/start the Compose stack.

The script also writes the current deploy commit into the NAS `.env`:

```env
APP_GIT_SHA=<full commit sha>
APP_BUILD_VERSION=<short commit sha>
DESIGN_VERSION=v4-practice-net-map
```

New practice sessions snapshot those values so public session detail pages can link to the code that was live when the session was recorded.

## Build And Start With CLI

If managing the stack over SSH instead of the UGREEN Docker UI, run from the repository root on the server:

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

Setup order:

1. Create the tunnel in Cloudflare Zero Trust.
2. Choose **Docker** for the connector environment.
3. Copy only the token value from the Docker command Cloudflare shows.
4. Put that value in the server `.env` as `CF_TUNNEL_TOKEN`.
5. Start/deploy the UGREEN Docker project.
6. Wait for the tunnel connector to show online in Cloudflare.
7. Add the published application/public hostname route.

Configure the published application/public hostname route:

- Hostname: `chip.cashbaggins.dev`
- Service: `http://app:8000`

The app itself does not need to know about the tunnel beyond:

```env
CORS_ORIGINS=https://chip.cashbaggins.dev
COOKIE_SECURE=true
```

When Cloudflare asks for the connector environment, choose **Docker**. Copy the tunnel token from the Docker command Cloudflare shows and put only the token value in `.env` as `CF_TUNNEL_TOKEN`.

Do not run Cloudflare's raw `docker run ...` command separately for this app. The `cloudflared` service is already part of `docker-compose.yml`.

## Post-Deploy Smoke Test

After the connector is online:

- Open `https://chip.cashbaggins.dev/api/health`.
- Open `https://chip.cashbaggins.dev`.
- Enter Me Mode from `Log Practice`.
- Start a session.
- Quick-log a small bucket or partial bucket.
- Stop the session.
- Return to Observer Mode and confirm the public stats changed.

If Cloudflare is still waiting for a connector, check the `cloudflared` container logs first. If `cloudflared` is waiting on the app, check the `app` container logs and health state.

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
