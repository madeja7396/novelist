# Local Distribution Release Guide

This document defines the release flow for Docker-based local distribution.

## Scope

- Target: Docker-based local bundle (`deploy/local`)
- Artifacts:
  - `novelist-local-<tag>.tar.gz`
  - `novelist-local-<tag>.tar.gz.sha256`
  - `<bundle>/SHA256SUMS`

## Versioning

- Recommended tag format: `vYYYY.MM.DD.N`
- Example: `v2026.02.06.1`

## Build Release Artifacts

```bash
./scripts/package_local_distribution.sh \
  --with-images \
  --output dist/releases \
  --tag v2026.02.06.1
```

## Verify Checksums

```bash
# Verify archive checksum
cd dist/releases
sha256sum -c novelist-local-v2026.02.06.1.tar.gz.sha256

# Verify in-bundle checksums
tar -xzf novelist-local-v2026.02.06.1.tar.gz
cd novelist-local-v2026.02.06.1
sha256sum -c SHA256SUMS
```

## Smoke Test Before Publish

```bash
just smoke-local
```

Expected:
- `/api/v1/health` returns HTTP 200
- `/api/v1/ready` returns HTTP 200
- `/api/v1/scenes` returns HTTP 200

## Publish Checklist

1. Release artifacts generated (`.tar.gz`, `.sha256`, `SHA256SUMS`).
2. `just smoke-local` passed on release candidate.
3. Release notes include:
   - release tag
   - known limitations
   - model used (`qwen3:1.7b` default)
4. Upload artifacts and checksums together.

Before commit/push, stage only public release scope:

```bash
./scripts/stage_public_push.sh
git diff --cached --name-only
```

Scope reference: `docs/public-publish.md`.

## Known Constraints

- Docker is required on end-user environment.
- Default ports: `8080`, `8081`.
- First run may download model unless `NOVELIST_PULL_MODEL=0` is used.
