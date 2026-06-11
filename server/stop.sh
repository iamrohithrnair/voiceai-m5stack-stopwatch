#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
SERVER_DIR="$ROOT/xiaozhi-esp32-server/main/xiaozhi-server"
cd "$SERVER_DIR"
docker compose -f docker-compose_all.yml down 2>/dev/null || true
docker compose down 2>/dev/null || true
echo "Stopped."
