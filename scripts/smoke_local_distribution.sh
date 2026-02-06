#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOCAL_DIR="$ROOT_DIR/deploy/local"
PACKAGE_SCRIPT="$ROOT_DIR/scripts/package_local_distribution.sh"
COMPOSE_FILE="$LOCAL_DIR/docker-compose.yml"

MODEL_NAME="${NOVELIST_OLLAMA_MODEL:-qwen3:1.7b}"
PULL_MODEL_FOR_SMOKE="${NOVELIST_SMOKE_PULL_MODEL:-1}"
READY_TIMEOUT_SEC="${NOVELIST_SMOKE_READY_TIMEOUT_SEC:-120}"
SCENE_TIMEOUT_SEC="${NOVELIST_SMOKE_SCENE_TIMEOUT_SEC:-300}"

TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

if docker compose version >/dev/null 2>&1; then
  COMPOSE_CMD=(docker compose)
elif command -v docker-compose >/dev/null 2>&1; then
  COMPOSE_CMD=(docker-compose)
else
  echo "docker compose or docker-compose command is required." >&2
  exit 1
fi

cleanup() {
  if [ -x "$LOCAL_DIR/stop.sh" ]; then
    "$LOCAL_DIR/stop.sh" >/dev/null 2>&1 || true
  fi
}
trap cleanup EXIT

echo "[1/6] Packaging local distribution (--no-images)"
"$PACKAGE_SCRIPT" --no-images >/dev/null

echo "[2/6] Starting local distribution"
NOVELIST_PULL_MODEL=0 "$LOCAL_DIR/start.sh" >/dev/null

if [ "$PULL_MODEL_FOR_SMOKE" = "1" ]; then
  echo "[3/6] Ensuring model is available: $MODEL_NAME"
  if ! "${COMPOSE_CMD[@]}" -f "$COMPOSE_FILE" exec -T ollama ollama list | awk 'NR>1 {print $1}' | grep -Fxq "$MODEL_NAME"; then
    "${COMPOSE_CMD[@]}" -f "$COMPOSE_FILE" exec -T ollama ollama pull "$MODEL_NAME" >/dev/null
  fi
else
  echo "[3/6] Skipping model pull check (NOVELIST_SMOKE_PULL_MODEL=0)"
fi

echo "[4/6] Waiting for readiness"
READY_JSON="$TMP_DIR/ready.json"
ready_code=""
for _ in $(seq 1 "$READY_TIMEOUT_SEC"); do
  ready_code="$(curl -sS -o "$READY_JSON" -w '%{http_code}' http://127.0.0.1:8080/api/v1/ready || true)"
  if [ "$ready_code" = "200" ]; then
    break
  fi
  sleep 1
done
if [ "$ready_code" != "200" ]; then
  echo "Readiness check failed (last status: ${ready_code:-n/a})" >&2
  cat "$READY_JSON" >&2 || true
  exit 1
fi

HEALTH_JSON="$TMP_DIR/health.json"
STATS_JSON="$TMP_DIR/stats.json"
health_code="$(curl -sS -o "$HEALTH_JSON" -w '%{http_code}' http://127.0.0.1:8080/api/v1/health || true)"
stats_code="$(curl -sS -o "$STATS_JSON" -w '%{http_code}' http://127.0.0.1:8080/api/v1/stats || true)"
if [ "$health_code" != "200" ]; then
  echo "Health endpoint failed (${health_code})" >&2
  cat "$HEALTH_JSON" >&2 || true
  exit 1
fi
if [ "$stats_code" != "200" ]; then
  echo "Stats endpoint failed (${stats_code})" >&2
  cat "$STATS_JSON" >&2 || true
  exit 1
fi

WEB_HTML="$TMP_DIR/web.html"
WEB_PROXY_HEALTH="$TMP_DIR/web_proxy_health.json"
web_code="$(curl -sS -o "$WEB_HTML" -w '%{http_code}' http://127.0.0.1:8081/ || true)"
web_proxy_code="$(curl -sS -o "$WEB_PROXY_HEALTH" -w '%{http_code}' http://127.0.0.1:8081/api/v1/health || true)"
if [ "$web_code" != "200" ]; then
  echo "Web UI endpoint failed (${web_code})" >&2
  exit 1
fi
if [ "$web_proxy_code" != "200" ]; then
  echo "Web proxy health endpoint failed (${web_proxy_code})" >&2
  cat "$WEB_PROXY_HEALTH" >&2 || true
  exit 1
fi

echo "[5/6] Running scene generation smoke test"
SCENE_JSON="$TMP_DIR/scene.json"
scene_code="$(
  curl -sS -o "$SCENE_JSON" -w '%{http_code}' \
    -m "$SCENE_TIMEOUT_SEC" \
    -X POST "http://127.0.0.1:8080/api/v1/scenes" \
    -H "Content-Type: application/json" \
    -d '{"intention":"A novice mage discovers a forbidden page in an old library.","chapter":1,"scene":1,"word_count":180,"mood":"mysterious"}' \
    || true
)"
if [ "$scene_code" != "200" ]; then
  echo "Scene generation failed (${scene_code})" >&2
  cat "$SCENE_JSON" >&2 || true
  exit 1
fi

if command -v jq >/dev/null 2>&1; then
  text_chars="$(jq -r '.text | length' "$SCENE_JSON" 2>/dev/null || echo 0)"
  if [ "${text_chars:-0}" -le 0 ]; then
    stage_count="$(jq -r '.stages | length' "$SCENE_JSON" 2>/dev/null || echo 0)"
    has_spec="$(jq -r 'if (.scene_spec != null or .scenespec != null) then "1" else "0" end' "$SCENE_JSON" 2>/dev/null || echo 0)"
    if [ "${stage_count:-0}" -le 0 ] || [ "$has_spec" != "1" ]; then
      echo "Scene response missing expected payload (text/spec/stages)." >&2
      cat "$SCENE_JSON" >&2 || true
      exit 1
    fi
    echo "WARN: Scene response text was empty; scene_spec/stages were returned." >&2
  fi
fi

echo "[6/6] Stopping local distribution"
cleanup

echo "Smoke test passed."
