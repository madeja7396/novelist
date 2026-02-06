# Novelist Local Distribution

Local-first distribution bundle for Novelist (Docker required).

## Requirements

- Docker Engine or Docker Desktop
- Free disk space: 6GB+ recommended
- Free local ports: `8080` (API), `8081` (Web)

## Quick Start (Online)

```bash
./start.sh
./status.sh
```

This mode pulls the default model (`qwen3:1.7b`) automatically.

## Quick Start (Offline Bundle)

If this directory includes `images.tar`:

```bash
./load-images.sh
NOVELIST_PULL_MODEL=0 ./start.sh
./status.sh
```

## Stop

```bash
./stop.sh
```

## Endpoints

- API: `http://localhost:8080`
- Health: `http://localhost:8080/api/v1/health`
- Readiness: `http://localhost:8080/api/v1/ready`
- Stats: `http://localhost:8080/api/v1/stats`
- Web UI: `http://localhost:8081`

`ollama` is internal-only by default (no host `11434` bind) to avoid collisions with existing local Ollama installs.
Web app API calls go through same-origin proxy (`http://localhost:8081/api/v1/*`).

## Useful Environment Variables

- `NOVELIST_OLLAMA_MODEL=qwen3:4b` to use another model.
- `NOVELIST_PULL_MODEL=0` to skip auto model pull.
- `NOVELIST_STRICT_MODEL_PULL=1` to fail fast when model pull fails.
- `NOVELIST_MIN_FREE_MB=8192` to require more free disk at startup.

## Startup Exit Codes (`start.sh`)

- `10`: docker command missing
- `11`: docker compose missing
- `12`: docker daemon unreachable
- `13`: low disk space
- `14`: port conflict
- `15`: image build/load failure
- `16`: compose startup failure
- `17`: model pull failure (strict mode only)

## Troubleshooting

1. `ERROR: port 8080/8081 is already in use`
   - Stop the conflicting process/container, then retry `./start.sh`.
2. `ready` is false in `./status.sh`
   - Check dependency summary from `status.sh`.
   - Verify model exists with:
   - `docker compose -f docker-compose.yml exec -T ollama ollama list`
3. Model pull fails on slow/offline network
   - Retry later, or run with `NOVELIST_PULL_MODEL=0` and load model manually.

## Data Layout

- `bootstrap/project`: immutable seed files included in bundle.
- `data/`: runtime state generated on first `./start.sh` (project files, Ollama keys/models).
