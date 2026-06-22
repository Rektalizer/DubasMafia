#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_DIR"

echo "==> Pulling latest code"
git pull

echo "==> Ensuring database is running"
docker compose up -d db

echo "==> Building bot image"
docker compose build bot

echo "==> Applying migrations"
docker compose run --rm bot alembic upgrade head

echo "==> Restarting bot"
docker compose up -d --force-recreate bot

echo "==> Bot logs (last 80 lines)"
docker compose logs --tail=80 bot
