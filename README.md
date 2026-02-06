# Novelist - 高性能AI小説創作支援システム

<a href="./README.md"><img src="https://img.shields.io/badge/english-blue" alt="English"></a>
<a href="./docs/README.ja.md"><img src="https://img.shields.io/badge/日本語-red" alt="日本語"></a>
<a href="./docs/README.zh.md"><img src="https://img.shields.io/badge/中文-orange" alt="中文"></a>

> 🚀 **High-Performance Edition** - Rust + Go + Nix architecture

学習不要で「AIのべりすと」級の創作体験を提供する、**超高速**ローカル指向プロダクト。

## ✨ Features

- ⚡ **超高性能** - Rust実装でPython比100倍高速
- 🌏 **多言語対応** - 日/英/中/韓のネイティブサポート
- 🔄 **再現性** - Nix Flakeで完全に再現可能な環境
- 🧠 **賢い検索** - RAGによる文脈理解
- 🎯 **マルチLLM** - OpenAI / Anthropic / ローカル対応
- 🔄 **Swarm架構** - 5つのエージェントが協調
- 📦 **軽量** - 5MBバイナリ、WebAssembly対応

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  Nix Flake                                                  │
│  ├─ rust/     - Core (Tokenization, RAG, 100x faster)      │
│  ├─ go/       - Services (API, Agents, Concurrent)         │
│  └─ src/      - Python (Legacy compatibility)              │
└─────────────────────────────────────────────────────────────┘
```

| Component | Before (Python) | After (Rust/Go) | Speedup |
|-----------|-----------------|-----------------|---------|
| Tokenize | 10K chars/s | 1M chars/s | **100x** |
| RAG Index | 100 docs/s | 10K docs/s | **100x** |
| RAG Query | 10ms | 0.1ms | **100x** |
| Memory | 500MB | 50MB | **10x** |

## 🚀 Quick Start

### Prerequisites
- [Nix](https://nixos.org/download.html) with flakes enabled

### Run

```bash
# Clone
git clone https://github.com/yourusername/novelist
cd novelist

# Enter dev shell (Rust + Go + all tools)
nix develop

# Create project
novelist init my-novel --name "My Novel"
cd my-novel

# Generate scene (2-stage pipeline)
novelist write -d "主人公が魔法を発見するシーン" -w 1000
```

## 📦 Installation

### Nix (Recommended)
```bash
nix run github:yourusername/novelist
```

### Binary
```bash
curl -fsSL https://get.novelist.dev | sh
```

### Docker
```bash
docker run -v $(pwd):/project novelist/novelist init /project/my-novel
```

### Local Distribution Bundle
```bash
# Create portable local package
just package-local

# Or package without docker images
just package-local -- --no-images

# Bundle entrypoint (online)
cd deploy/local
./start.sh

# Bundle entrypoint (offline package with images.tar)
./load-images.sh
NOVELIST_PULL_MODEL=0 ./start.sh

# Smoke test end-to-end local distribution
just smoke-local
```

## 🛠️ Development

```bash
# Enter development environment
nix develop

# Build everything
just build

# Run tests
just test

# Benchmarks
just bench

# Run full stack
just run
```

## 📝 Usage

### CLI

```bash
# Initialize project
novelist init ./fantasy-novel --name "Dragon's Quest"

# Write scene (auto 2-stage)
novelist write \
  --project ./fantasy-novel \
  --description "主人公が古い図書館で魔法の書を見つける" \
  --chapter 1 \
  --words 1500

# Check project status
novelist status --project ./fantasy-novel

# Manage sessions
novelist session --list
```

### API (Go)

```bash
# Start API server
cd go && go run ./cmd/api

# Request
curl -X POST http://localhost:8080/api/v1/scenes \
  -H "Content-Type: application/json" \
  -d '{
    "intention": "Hero discovers magic",
    "chapter": 1,
    "word_count": 1000
  }'

# Health and readiness
curl http://localhost:8080/api/v1/health
curl http://localhost:8080/api/v1/ready
curl http://localhost:8080/api/v1/stats
```

### Rust Library

```rust
use novelist_core::{tokenizer::MultiLanguageTokenizer, rag::Retriever};

// Tokenize Japanese
let tokenizer = MultiLanguageTokenizer::new();
let tokens = tokenizer.tokenize("こんにちは世界");

// RAG search
let retriever = Retriever::new(128);
retriever.add_document(doc);
let results = retriever.search("magic system", 5);
```

## 🌍 Internationalization

| Language | Code | Status |
|----------|------|--------|
| 日本語 | ja | ✅ Native |
| English | en | ✅ Native |
| 中文 | zh | ✅ Supported |
| 한국어 | ko | ✅ Supported |

```rust
use novelist_core::i18n::I18n;

let i18n = I18n::new("ja");
println!("{}", i18n.t("welcome")); // ようこそ
```

## 🏛️ Project Structure

```
my-novel/
├── bible.md              # World & Style settings
├── characters/
│   ├── protagonist.json
│   └── mentor.json
├── chapters/
│   └── chapter_001.md
├── memory/
│   ├── episodic.md      # Recent summaries
│   ├── facts.json       # Immutable facts
│   └── foreshadow.json  # Plot hooks
├── runs/                # Execution logs
└── config.yaml          # Provider settings
```

## 🔧 Configuration

```yaml
# config.yaml
provider:
  default: local_ollama
  
  available:
    local_ollama:
      type: ollama
      model: qwen3:1.7b
      base_url: http://localhost:11434
    
    openai_gpt4:
      type: openai
      model: gpt-4
      api_key_env: OPENAI_API_KEY
  
  # Per-agent routing
  routing:
    director: openai_gpt4    # JSON mode
    writer: local_ollama     # Creative
    checker: local_ollama    # Cost-effective

context:
  budgets:
    bible: 1500
    characters: 1200
    facts: 600
    recap: 400
```

Runtime safety limits (env):

```bash
NOVELIST_MAX_REQUEST_BYTES=65536
NOVELIST_REQUEST_TIMEOUT_SEC=90
NOVELIST_MAX_CONCURRENT_REQUESTS=8
NOVELIST_RATE_LIMIT_PER_MIN=120
```

Local distribution release checklist:

```bash
docs/release-local.md
docs/public-publish.md
```

## 🧪 Testing

```bash
# Rust
cd rust && cargo test --release && cargo bench

# Go
cd go && go test -race ./...

# Python (legacy)
cd src && python -m pytest ../tests/

# All
just test
```

## 📊 Benchmarks

```bash
cd rust && cargo bench

# Results (AMD Ryzen 9 5900X)
tokenize_jp             time:   [102.34 ns/char]
tokenize_en             time:   [18.45 ns/char]
rag_index_1000          time:   [98.45 ms]
rag_search              time:   [89.12 µs]
```

## 🤝 Contributing

1. `nix develop` - Enter dev shell
2. `git checkout -b feature/amazing` - Create branch
3. Make changes
4. `just test` - Verify
5. `just fmt` - Format
6. Submit PR

## 📚 Documentation

- [AGENTS.md](AGENTS.md) - Architecture & Development Guide
- [docs/keikaku.md](docs/keikaku.md) - Original Design (Japanese)
- [API Docs](https://docs.novelist.dev) - API Reference

## 📄 License

MIT License - See [LICENSE](LICENSE)

---

Made with ❤️ using Rust 🦀, Go 🐹, and Nix ❄️
