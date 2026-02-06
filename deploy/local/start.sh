#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
COMPOSE_FILE="$SCRIPT_DIR/docker-compose.yml"
LOCAL_IMAGE="novelist-local:latest"
MIN_FREE_MB="${NOVELIST_MIN_FREE_MB:-6144}"

# Exit codes for automation / CI triage.
EXIT_NO_DOCKER=10
EXIT_NO_COMPOSE=11
EXIT_DOCKER_DAEMON=12
EXIT_LOW_DISK=13
EXIT_PORT_CONFLICT=14
EXIT_IMAGE_BUILD=15
EXIT_COMPOSE_UP=16
EXIT_MODEL_PULL=17

die() {
  local code="$1"
  local message="$2"
  echo "ERROR: ${message}" >&2
  exit "$code"
}

warn() {
  local message="$1"
  echo "WARN: ${message}" >&2
}

check_disk_space() {
  local available_kb min_kb
  available_kb="$(df -Pk "$SCRIPT_DIR" | awk 'NR==2 {print $4}')"
  min_kb=$((MIN_FREE_MB * 1024))

  if [ -z "$available_kb" ] || [ "$available_kb" -lt "$min_kb" ]; then
    die "$EXIT_LOW_DISK" "at least ${MIN_FREE_MB}MB free disk is required (set NOVELIST_MIN_FREE_MB to override)."
  fi
}

port_in_use() {
  local port="$1"
  if command -v ss >/dev/null 2>&1; then
    ss -H -ltn "sport = :${port}" 2>/dev/null | grep -q .
    return
  fi
  if command -v lsof >/dev/null 2>&1; then
    lsof -iTCP:"${port}" -sTCP:LISTEN >/dev/null 2>&1
    return
  fi
  if command -v netstat >/dev/null 2>&1; then
    netstat -ltn 2>/dev/null | awk '{print $4}' | grep -Eq "[:.]${port}\$"
    return
  fi
  warn "unable to check local port conflicts (ss/lsof/netstat not found)."
  return 1
}

check_required_ports() {
  local port
  for port in 8080 8081; do
    if port_in_use "$port"; then
      die "$EXIT_PORT_CONFLICT" "port ${port} is already in use. Stop the conflicting process and retry."
    fi
  done
}

stack_already_running() {
  "${COMPOSE_CMD[@]}" -f "$COMPOSE_FILE" ps --status running --services 2>/dev/null \
    | grep -Eq '^(api|web|ollama)$'
}

if ! command -v docker >/dev/null 2>&1; then
  die "$EXIT_NO_DOCKER" "docker command is required."
fi

if ! docker info >/dev/null 2>&1; then
  die "$EXIT_DOCKER_DAEMON" "docker daemon is not reachable. Start Docker and retry."
fi

if docker compose version >/dev/null 2>&1; then
  COMPOSE_CMD=(docker compose)
elif command -v docker-compose >/dev/null 2>&1; then
  COMPOSE_CMD=(docker-compose)
else
  die "$EXIT_NO_COMPOSE" "docker compose or docker-compose command is required."
fi

check_disk_space
if ! stack_already_running; then
  check_required_ports
fi

mkdir -p "$SCRIPT_DIR/data"
mkdir -p "$SCRIPT_DIR/data/ollama"

if [ ! -f "$SCRIPT_DIR/data/project/config.yaml" ]; then
  mkdir -p "$SCRIPT_DIR/data/project"
  cp -R "$SCRIPT_DIR/bootstrap/project/." "$SCRIPT_DIR/data/project/"
  echo "Initialized project data at deploy/local/data/project"
fi

if ! docker image inspect "$LOCAL_IMAGE" >/dev/null 2>&1; then
  if [ -f "$ROOT_DIR/Dockerfile" ]; then
    echo "Building ${LOCAL_IMAGE} image..."
    if ! docker build -t "$LOCAL_IMAGE" "$ROOT_DIR"; then
      die "$EXIT_IMAGE_BUILD" "failed to build ${LOCAL_IMAGE} image."
    fi
  else
    die "$EXIT_IMAGE_BUILD" "${LOCAL_IMAGE} image not found. Run ./load-images.sh first."
  fi
fi

if ! "${COMPOSE_CMD[@]}" -f "$COMPOSE_FILE" up -d; then
  die "$EXIT_COMPOSE_UP" "failed to start docker compose services."
fi

MODEL_NAME="${NOVELIST_OLLAMA_MODEL:-qwen3:1.7b}"
if [ "${NOVELIST_PULL_MODEL:-1}" = "1" ]; then
  echo "Pulling Ollama model: ${MODEL_NAME}"
  if ! "${COMPOSE_CMD[@]}" -f "$COMPOSE_FILE" exec -T ollama ollama pull "$MODEL_NAME"; then
    if [ "${NOVELIST_STRICT_MODEL_PULL:-0}" = "1" ]; then
      die "$EXIT_MODEL_PULL" "model pull failed for ${MODEL_NAME}."
    fi
    warn "model pull failed for ${MODEL_NAME}. Start completed; pull the model manually later."
  fi
fi

echo
echo "Local distribution started:"
echo "  API: http://localhost:8080"
echo "  Health: http://localhost:8080/api/v1/health"
echo "  Ready: http://localhost:8080/api/v1/ready"
echo "  Web: http://localhost:8081"
