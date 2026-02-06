#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
COMPOSE_FILE="$SCRIPT_DIR/docker-compose.yml"

if ! command -v docker >/dev/null 2>&1; then
  echo "docker command is required."
  exit 1
fi

if docker compose version >/dev/null 2>&1; then
  COMPOSE_CMD=(docker compose)
elif command -v docker-compose >/dev/null 2>&1; then
  COMPOSE_CMD=(docker-compose)
else
  echo "docker compose or docker-compose command is required."
  exit 1
fi

mkdir -p "$SCRIPT_DIR/data"
mkdir -p "$SCRIPT_DIR/data/ollama"

if [ ! -f "$SCRIPT_DIR/data/project/config.yaml" ]; then
  mkdir -p "$SCRIPT_DIR/data/project"
  cp -R "$SCRIPT_DIR/bootstrap/project/." "$SCRIPT_DIR/data/project/"
  echo "Initialized project data at deploy/local/data/project"
fi

if ! docker image inspect novelist-local:latest >/dev/null 2>&1; then
  if [ -f "$ROOT_DIR/Dockerfile" ]; then
    echo "Building novelist-local:latest image..."
    docker build -t novelist-local:latest "$ROOT_DIR"
  else
    echo "novelist-local:latest image not found. Run ./load-images.sh first."
    exit 1
  fi
fi

"${COMPOSE_CMD[@]}" -f "$COMPOSE_FILE" up -d

MODEL_NAME="${NOVELIST_OLLAMA_MODEL:-qwen3:1.7b}"
if [ "${NOVELIST_PULL_MODEL:-1}" = "1" ]; then
  echo "Pulling Ollama model: ${MODEL_NAME}"
  if ! "${COMPOSE_CMD[@]}" -f "$COMPOSE_FILE" exec -T ollama ollama pull "$MODEL_NAME"; then
    echo "Model pull failed. Start completed; pull the model manually later."
  fi
fi

echo
echo "Local distribution started:"
echo "  API: http://localhost:8080"
echo "  Health: http://localhost:8080/api/v1/health"
echo "  Ready: http://localhost:8080/api/v1/ready"
echo "  Web: http://localhost:8081"
