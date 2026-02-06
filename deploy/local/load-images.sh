#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
IMAGE_ARCHIVE="$SCRIPT_DIR/images.tar"

if ! command -v docker >/dev/null 2>&1; then
  echo "docker command is required."
  exit 1
fi

if [ ! -f "$IMAGE_ARCHIVE" ]; then
  echo "images.tar not found at: $IMAGE_ARCHIVE"
  echo "If you are using source checkout, run deploy/local/start.sh instead."
  exit 1
fi

docker load -i "$IMAGE_ARCHIVE"
echo "Images loaded successfully."
