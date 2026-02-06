# Public Publish Scope

This document defines which files/directories should be included in a public push for local distribution releases.

## Include in Push

- `deploy/local/`
  - `docker-compose.yml`
  - `start.sh`, `stop.sh`, `status.sh`, `load-images.sh`
  - `web/index.html`, `web/nginx.conf`
  - `README.md`
  - `bootstrap/project/*`
  - `data/.gitignore`
- `scripts/package_local_distribution.sh`
- `scripts/smoke_local_distribution.sh`
- `docs/release-local.md`
- `README.md`
- `justfile`

## Exclude from Push

- Runtime artifacts and generated outputs:
  - `dist/`
  - `deploy/local/data/ollama/*`
  - `deploy/local/data/project/*` (except tracked seed placeholders)
- Local logs and temporary files.
- Internal progress/meta files not needed for public release context:
  - `.agents/skills/project-roadmap/progress.json`
  - `docs/action.md` (internal progress memo)

## Recommended Staging Flow

Use the helper script:

```bash
./scripts/stage_public_push.sh
```

Then verify:

```bash
git diff --cached --name-only
```

Expected staged set should stay within the include list above.

## Pre-Push Validation

```bash
./scripts/smoke_local_distribution.sh
./scripts/package_local_distribution.sh --no-images --tag vYYYY.MM.DD.N --output dist/releases
```

For full release:

```bash
./scripts/package_local_distribution.sh --with-images --tag vYYYY.MM.DD.N --output dist/releases
```
