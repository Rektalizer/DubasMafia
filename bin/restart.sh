#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_DIR"

echo "==> Restarting bot container"
docker compose up -d bot

echo "==> Bot logs (follow mode, Ctrl+C to exit)"
docker compose logs -f bot
