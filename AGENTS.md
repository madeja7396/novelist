# AGENTS.md - Novelist Project

This document provides essential context for AI agents working on the novelist project.

## Project Overview

A high-performance, local-first AI novel writing assistant with multi-language support (Japanese, English, Chinese, Korean).

### Architecture v2.0 (Nix + Rust + Go)

```
┌─────────────────────────────────────────────────────────────────┐
│                         Novelist v2.0                           │
├─────────────────────────────────────────────────────────────────┤
│  Nix Flake                                                      │
│  ├── Rust Core (High-performance components)                    │
│  │   ├── tokenizer/     - Multi-language tokenization           │
│  │   ├── rag/           - Vector similarity search              │
│  │   └── i18n/          - Internationalization                  │
│  ├── Go Services        (API, Agent orchestration)              │
│  │   ├── api/           - REST/gRPC API                         │
│  │   └── agents/        - Agent swarm management                │
│  └── Python (Legacy)    - Compatibility layer                   │
└─────────────────────────────────────────────────────────────────┘
```

### Core Philosophy

- **High Performance**: Rust for compute-intensive tasks (10-100x faster than Python)
- **Scalability**: Go for concurrent agent orchestration
- **Reproducibility**: Nix for deterministic builds
- **Multi-language**: Native support for CJK languages
- **Lightweight**: WebAssembly for browser deployment

## Quick Start (Nix)

```bash
# Enter development shell
nix develop

# Build Rust core
cd rust && cargo build --release

# Build Go services
cd go && go build ./...

# Run full stack
just run
```

## Technology Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| Build System | Nix Flake | Reproducible builds, dev environment |
| Core Library | Rust | Tokenization, RAG, vector ops |
| API Services | Go | Agent orchestration, HTTP API |
| Legacy | Python | Backward compatibility |
| UI (Future) | Rust + WebAssembly | Browser-based interface |

## Project Structure

```
novelist/
├── flake.nix              # Nix configuration
├── justfile               # Task runner
├── rust/                  # Rust core library
│   ├── src/
│   │   ├── tokenizer/    # Multi-language tokenization
│   │   ├── rag/          # Vector similarity search
│   │   ├── i18n/         # Internationalization
│   │   └── models/       # Data models
│   ├── benches/          # Performance benchmarks
│   └── tests/            # Unit tests
├── go/                    # Go microservices
│   ├── cmd/
│   │   ├── api/          # API server
│   │   └── agent/        # Agent worker
│   └── pkg/
│       ├── agents/       # Agent implementations
│       └── api/          # API handlers
├── src/                   # Python (legacy)
├── web/                   # WebAssembly UI (future)
├── templates/             # SSOT document templates
└── docs/                  # Documentation
```

## Multi-Language Tokenization

Rust-based tokenizer with optimized performance:

| Language | Method | Speed (chars/sec) |
|----------|--------|-------------------|
| Japanese | Lindera (MeCab) | ~1M |
| English | Unicode segmentation | ~5M |
| Chinese | Character-based | ~3M |
| Korean | Jamo composition | ~2M |

```rust
use novelist_core::tokenizer::MultiLanguageTokenizer;

let tokenizer = MultiLanguageTokenizer::new();
let tokens = tokenizer.tokenize("こんにちは世界");
let lang = MultiLanguageTokenizer::detect_language(text);
```

## High-Performance RAG

Rust implementation with SIMD optimizations:

```rust
use novelist_core::rag::{Retriever, Document, DocType};

let retriever = Retriever::new(128);  // 128-dim embeddings
retriever.add_document(Document {
    id: "doc1".into(),
    content: "Magic comes from ley lines".into(),
    source: "bible.md".into(),
    doc_type: DocType::Bible,
    ..Default::default()
});

let results = retriever.search("magic system", 5);
```

**Performance**: ~10,000 docs/sec indexing, <1ms query time

## Agent Swarm (Go)

Go-based agent orchestration with goroutines:

```go
import "github.com/novelist/novelist/go/pkg/agents"

swarm := agents.NewSwarm(config)
result := swarm.GenerateScene(ctx, agents.SceneRequest{
    Intention: "Hero discovers magic",
    Chapter:   1,
    Scene:     1,
})
```

### Pipeline
1. **Director** → SceneSpec (JSON)
2. **Writer** → Prose
3. **Checker** → Issues (parallel validation)
4. **Editor** → Fixed prose (if issues)
5. **Committer** → Memory update

**Max 1 revision** to prevent loops.

## Internationalization (i18n)

Supported languages:
- 🇯🇵 Japanese (ja)
- 🇺🇸 English (en)
- 🇨🇳 Chinese (zh)
- 🇰🇷 Korean (ko)

```rust
use novelist_core::i18n::I18n;

let i18n = I18n::new("ja");
println!("{}", i18n.t("welcome"));
```

## Provider Routing

Capability-based routing:

```yaml
# config.yaml
provider:
  routing:
    director:  openai_gpt4      # JSON mode capable
    writer:    anthropic_claude # Creative writing
    checker:   local_ollama     # Cost-effective
    editor:    local_ollama     # Fast iteration
```

## Development Tasks (Just)

```bash
just build      # Build all components
just test       # Run all tests
just bench      # Run benchmarks
just lint       # Run linters
just run        # Start full stack
just clean      # Clean build artifacts
```

## Building

### Rust Core
```bash
cd rust
cargo build --release          # Optimized build
cargo test                      # Run tests
cargo bench                     # Benchmarks
wasm-pack build --target web   # WebAssembly
```

### Go Services
```bash
cd go
go build ./cmd/api            # API server
go build ./cmd/agent          # Agent worker
go test ./...                  # Run tests
```

### Full System
```bash
nix build                    # Build all packages
nix run .#novelist-core      # Run Rust binary
nix run .#novelist-agent     # Run Go binary
```

## Testing

### Rust
```bash
cd rust
cargo test --release
cargo bench  # Criterion benchmarks
```

### Go
```bash
cd go
go test -race ./...
go test -bench=. ./...
```

### Integration
```bash
just test-integration
```

## Performance Benchmarks

| Operation | Python | Rust | Speedup |
|-----------|--------|------|---------|
| Tokenize (JP) | 10K/s | 1M/s | **100x** |
| RAG Index | 100/s | 10K/s | **100x** |
| RAG Search | 10ms | 0.1ms | **100x** |
| Memory Usage | 500MB | 50MB | **10x** |
| Binary Size | - | 5MB | - |

## Deployment

### Native
```bash
nix build .#novelist
./result/bin/novelist-core
```

### Docker
```bash
docker build -t novelist .
docker run -p 8080:8080 novelist
```

### WebAssembly
```bash
cd rust
wasm-pack build --target web
# Use in browser
```

## Migration from v1.0 (Python)

v1.0 Python code remains in `src/` for compatibility.

```python
# Legacy Python API (still works)
from novelist import SimplePipeline

pipeline = SimplePipeline("./my_novel")
text = pipeline.write_scene("Scene description")
```

New projects should use Rust/Go APIs for better performance.

## Environment Variables

```bash
# API Keys
export OPENAI_API_KEY="sk-..."
export ANTHROPIC_API_KEY="sk-ant-..."

# Paths
export NOVELIST_PROJECT="/path/to/project"

# Rust
export RUST_LOG=debug
export RUST_BACKTRACE=1

# Go
export NOVELIST_HTTP_PORT=8080
export NOVELIST_GRPC_PORT=50051
```

## Contributing

1. Enter Nix shell: `nix develop`
2. Make changes
3. Run tests: `just test`
4. Format code: `just fmt`
5. Submit PR

## References

- [Rust Book](https://doc.rust-lang.org/book/)
- [Go Documentation](https://golang.org/doc/)
- [Nix Manual](https://nixos.org/manual/nix/stable/)
- [Original Design](docs/keikaku.md) (Japanese)

## License

MIT License - See LICENSE file
