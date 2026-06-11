#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
SERVER_DIR="$ROOT/xiaozhi-esp32-server/main/xiaozhi-server"

if [[ ! -d "$SERVER_DIR" ]]; then
  echo "Run ./setup.sh first"
  exit 1
fi

cd "$SERVER_DIR"

if [[ "${1:-}" == "--full" ]]; then
  echo "Starting full stack (voice + 智控台 on :8002 + MySQL + Redis)..."
  docker compose -f docker-compose_all.yml up -d
  echo "Web console: http://$(ipconfig getifaddr en0 2>/dev/null || echo 127.0.0.1):8002"
else
  echo "Starting voice server only (Docker)..."
  docker compose up -d
fi

echo "Logs: docker logs -f xiaozhi-esp32-server"
