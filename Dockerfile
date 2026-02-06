# Multi-stage build for Novelist

# Stage 1: Rust builder
FROM rust:1.85-slim AS rust-builder

WORKDIR /build
RUN apt-get update && apt-get install -y \
    pkg-config \
    libssl-dev \
    cmake \
    && rm -rf /var/lib/apt/lists/*

COPY rust/Cargo.toml rust/Cargo.lock ./
COPY rust/src ./src
COPY rust/benches ./benches
RUN cargo build --release

# Stage 2: Go builder
FROM golang:1.21-alpine AS go-builder

WORKDIR /build
RUN apk add --no-cache git

COPY go/go.mod go/go.sum ./
RUN go mod download

COPY go/ ./
RUN CGO_ENABLED=0 GOOS=linux go build -a -installsuffix cgo -o novelist-api ./cmd/api
RUN CGO_ENABLED=0 GOOS=linux go build -a -installsuffix cgo -o novelist-agent ./cmd/agent

# Stage 3: Python (legacy) - optional
FROM python:3.12-slim AS python-base

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/
COPY templates/ ./templates/

# Stage 4: Final image
FROM debian:bookworm-slim

RUN apt-get update && apt-get install -y \
    ca-certificates \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy binaries
COPY --from=rust-builder /build/target/release/libnovelist_core.so /usr/lib/
COPY --from=go-builder /build/novelist-api /usr/local/bin/
COPY --from=go-builder /build/novelist-agent /usr/local/bin/
COPY --from=python-base /app /app/python

# Copy entrypoint
COPY docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

# Create non-root user
RUN useradd -m -u 1000 novelist
USER novelist

# Expose ports
EXPOSE 8080 50051

ENTRYPOINT ["docker-entrypoint.sh"]
CMD ["api"]
