#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
IMAGE_ARCHIVE="$SCRIPT_DIR/images.tar"
CHECKSUM_FILE="$SCRIPT_DIR/SHA256SUMS"

if ! command -v docker >/dev/null 2>&1; then
  echo "docker command is required."
  exit 1
fi

if [ ! -f "$IMAGE_ARCHIVE" ]; then
  echo "images.tar not found at: $IMAGE_ARCHIVE"
  echo "If you are using source checkout, run deploy/local/start.sh instead."
  exit 1
fi

if [ -f "$CHECKSUM_FILE" ]; then
  if command -v sha256sum >/dev/null 2>&1; then
    echo "Verifying images.tar checksum..."
    (cd "$SCRIPT_DIR" && grep "  images.tar\$" "$CHECKSUM_FILE" | sha256sum -c -)
  elif command -v shasum >/dev/null 2>&1; then
    echo "Verifying images.tar checksum..."
    expected="$(grep "  images.tar\$" "$CHECKSUM_FILE" | awk '{print $1}')"
    actual="$(shasum -a 256 "$IMAGE_ARCHIVE" | awk '{print $1}')"
    if [ "$expected" != "$actual" ]; then
      echo "Checksum mismatch for images.tar" >&2
      exit 1
    fi
  fi
fi

docker load -i "$IMAGE_ARCHIVE"
echo "Images loaded successfully."
