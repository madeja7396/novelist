# Justfile for Novelist - Task runner

# Default recipe
default:
    @just --list

# Build all components
build:
    @echo "🔨 Building Rust core..."
    cd rust && cargo build --release
    @echo "🔨 Building Go services..."
    cd go && go build ./...
    @echo "✅ Build complete"

# Build Rust only
build-rust:
    cd rust && cargo build --release

# Build Go only
build-go:
    cd go && go build ./...

# Build WebAssembly
build-wasm:
    cd rust && wasm-pack build --target web --out-dir ../web/pkg

# Run all tests
test: test-rust test-go test-python

# Run Rust tests
test-rust:
    @echo "🧪 Running Rust tests..."
    cd rust && cargo test --release

# Run Go tests
test-go:
    @echo "🧪 Running Go tests..."
    cd go && go test -race ./...

# Run Python tests (legacy)
test-python:
    @echo "🧪 Running Python tests..."
    cd /root/dev/novelist && source venv/bin/activate && python tests/test_integration.py

# Run benchmarks
bench:
    cd rust && cargo bench

# Lint all code
lint: lint-rust lint-go lint-nix

# Lint Rust
lint-rust:
    cd rust && cargo clippy -- -D warnings && cargo fmt --check

# Lint Go
lint-go:
    cd go && golangci-lint run ./...

# Lint Nix
lint-nix:
    nixpkgs-fmt --check *.nix

# Format all code
fmt:
    cd rust && cargo fmt
    cd go && gofmt -w .
    nixpkgs-fmt *.nix

# Run full development stack
dev:
    @echo "🚀 Starting development stack..."
    @echo "Rust API: http://localhost:8080"
    @echo "Go Agent: http://localhost:8081"
    concurrently \
        "cd rust && cargo run --bin novelist-server" \
        "cd go && go run ./cmd/api"

# Run CLI
run *ARGS:
    cd rust && cargo run --release -- {{ARGS}}

# Clean build artifacts
clean:
    cd rust && cargo clean
    cd go && rm -rf bin/
    rm -rf web/pkg/
    @echo "🧹 Clean complete"

# Generate documentation
docs:
    cd rust && cargo doc --no-deps --open

# Update dependencies
update:
    cd rust && cargo update
    cd go && go get -u ./...

# Security audit
audit:
    cd rust && cargo audit
    cd go && govulncheck ./...

# Run integration tests
test-integration:
    @echo "🔗 Running integration tests..."
    ./scripts/smoke_local_distribution.sh

# Create new release
release VERSION:
    @echo "📦 Creating release {{VERSION}}..."
    git tag -a v{{VERSION}} -m "Release {{VERSION}}"
    git push origin v{{VERSION}}
    @echo "✅ Release v{{VERSION}} created"

# Profile performance
profile:
    cd rust && cargo flamegraph --bench tokenizer_benchmark

# Watch for changes and rebuild
watch:
    cd rust && cargo watch -x "build --release" -x "test"

# Setup development environment
setup:
    @echo "🔧 Setting up development environment..."
    git submodule update --init --recursive
    cd rust && cargo fetch
    cd go && go mod download
    @echo "✅ Setup complete. Run 'nix develop' to enter dev shell."

# Docker build
docker:
    docker build -t novelist:latest .

# Build local distribution package
package-local *ARGS:
    ./scripts/package_local_distribution.sh {{ARGS}}

# Smoke test local distribution package/runtime
smoke-local:
    ./scripts/smoke_local_distribution.sh

# Nix build
nix-build:
    nix build .#novelist-core
    nix build .#novelist-agent

# Nix check
nix-check:
    nix flake check

# Show project stats
stats:
    @echo "📊 Project Statistics"
    @echo "====================="
    @echo "Rust files: $(find rust -name '*.rs' | wc -l)"
    @echo "Rust LOC: $(find rust -name '*.rs' -exec wc -l {} + | tail -1 | awk '{print $1}')"
    @echo "Go files: $(find go -name '*.go' | wc -l)"
    @echo "Go LOC: $(find go -name '*.go' -exec wc -l {} + | tail -1 | awk '{print $1}')"
    @echo "Python files: $(find src -name '*.py' | wc -l)"
    @echo "====================="
