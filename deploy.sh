#!/usr/bin/env bash
set -euo pipefail

NAS_SHARE="/z/chipping"
NAS_HOST="CashBaggins@192.168.100.241"
NAS_PROJECT="/volume1/python_projects/chipping"
NAS_COMPOSE_FILE="docker-compose.yaml"

cd "$NAS_SHARE"
git fetch origin
git reset --hard origin/main

# UGREEN's Docker app points at docker-compose.yaml, while the repo tracks
# docker-compose.yml. Keep the NAS-facing copy in sync on every deploy.
cp docker-compose.yml "$NAS_COMPOSE_FILE"

ssh -t "$NAS_HOST" "cd $NAS_PROJECT && sudo docker compose --env-file .env -f $NAS_COMPOSE_FILE up -d --build"
