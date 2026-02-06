#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COMPOSE_FILE="$SCRIPT_DIR/docker-compose.yml"
TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

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

HEALTH_JSON="$TMP_DIR/health.json"
READY_JSON="$TMP_DIR/ready.json"

health_code="$(curl -sS -o "$HEALTH_JSON" -w '%{http_code}' http://127.0.0.1:8080/api/v1/health || true)"
ready_code="$(curl -sS -o "$READY_JSON" -w '%{http_code}' http://127.0.0.1:8080/api/v1/ready || true)"

echo "API health (${health_code}):"
cat "$HEALTH_JSON" 2>/dev/null || true
echo
echo "API ready (${ready_code}):"
cat "$READY_JSON" 2>/dev/null || true
echo

summarize_unhealthy() {
  local source_json="$1"
  if ! command -v jq >/dev/null 2>&1; then
    return
  fi
  jq -r '
    .dependencies // {} | to_entries[]
    | select(.value.healthy == false)
    | "- \(.key): \(.value.error // "unhealthy")"
  ' "$source_json" 2>/dev/null || true
}

if [ "$ready_code" != "200" ] || [ "$health_code" != "200" ]; then
  echo "Dependency summary:"
  summary="$(summarize_unhealthy "$READY_JSON")"
  if [ -z "$summary" ]; then
    summary="$(summarize_unhealthy "$HEALTH_JSON")"
  fi
  if [ -n "$summary" ]; then
    echo "$summary"
  else
    echo "- unable to summarize dependency errors (install jq for structured output)"
  fi
fi
