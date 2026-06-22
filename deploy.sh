#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"

echo "Pulling latest code..."
git pull

echo "Rebuilding containers..."
docker compose build bot

echo "Restarting bot..."
docker compose up -d bot

echo "Showing recent bot logs..."
docker compose logs --tail=50 bot
