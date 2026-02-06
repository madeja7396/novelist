#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

git add \
  README.md \
  justfile \
  docs/release-local.md \
  docs/public-publish.md \
  deploy/local \
  scripts/package_local_distribution.sh \
  scripts/smoke_local_distribution.sh

echo "Staged files for public push:"
git diff --cached --name-only
