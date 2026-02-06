#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COMPOSE_FILE="$SCRIPT_DIR/docker-compose.yml"

if docker compose version >/dev/null 2>&1; then
  COMPOSE_CMD=(docker compose)
elif command -v docker-compose >/dev/null 2>&1; then
  COMPOSE_CMD=(docker-compose)
else
  echo "docker compose or docker-compose command is required."
  exit 1
fi

"${COMPOSE_CMD[@]}" -f "$COMPOSE_FILE" ps
echo
echo "API health:"
curl -fsS http://127.0.0.1:8080/api/v1/health || true
echo
echo "API ready:"
curl -fsS http://127.0.0.1:8080/api/v1/ready || true
echo
