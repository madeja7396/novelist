# Novelist Local Distribution

This directory contains a local-only distribution package for Novelist.

## Purpose

- Run Novelist locally with Docker.
- No cloud dependency is required for generation (Ollama-based).
- Can be shared as a portable bundle.

## Quick Start

1. Start the local stack:

```bash
./start.sh
```

2. Check status:

```bash
./status.sh
```

3. Stop:

```bash
./stop.sh
```

## Endpoints

- API: `http://localhost:8080`
- Health: `http://localhost:8080/api/v1/health`
- Readiness: `http://localhost:8080/api/v1/ready`
- Stats: `http://localhost:8080/api/v1/stats`
- Web UI: `http://localhost:8081`

`ollama` service is internal-only by default (no host `11434` bind) to avoid port conflicts with existing local Ollama installations.

## Optional: Load packaged images

If this directory was delivered with `images.tar`, load it first:

```bash
./load-images.sh
```

## Model

Default model is `qwen3:1.7b`.

Override model:

```bash
NOVELIST_OLLAMA_MODEL=qwen3:4b ./start.sh
```

Skip automatic model pull:

```bash
NOVELIST_PULL_MODEL=0 ./start.sh
```

## Data Layout

- `bootstrap/project`: immutable seed files distributed with the package.
- `data/`: runtime state (project working files, Ollama keys/models) generated on first `./start.sh`.
