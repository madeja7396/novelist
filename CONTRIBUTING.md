# Contributing to Novelist

Thank you for your interest in contributing to Novelist! This document provides guidelines for contributing.

## Development Setup

### Prerequisites
- [Nix](https://nixos.org/download.html) with flakes enabled
- Git

### Setup
```bash
# Clone repository
git clone https://github.com/yourusername/novelist
cd novelist

# Enter development shell
nix develop

# Verify setup
just --version
cargo --version
go version
```

## Project Structure

- `rust/` - High-performance core (tokenizer, RAG, i18n)
- `go/` - Microservices (API, agents)
- `src/` - Python legacy compatibility
- `web/` - WebAssembly UI

## Workflow

### 1. Create Branch
```bash
git checkout -b feature/your-feature-name
```

### 2. Make Changes
- Follow existing code style
- Add tests for new functionality
- Update documentation

### 3. Test
```bash
# Run all tests
just test

# Run specific tests
just test-rust
just test-go

# Run benchmarks
just bench

# Lint
just lint
```

### 4. Commit
```bash
git add .
git commit -m "feat: add amazing feature"
```

Follow [Conventional Commits](https://www.conventionalcommits.org/):
- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation
- `perf:` Performance improvement
- `refactor:` Code refactoring
- `test:` Tests
- `chore:` Maintenance

### 5. Push and PR
```bash
git push origin feature/your-feature-name
```

Create a Pull Request with:
- Clear description
- Test results
- Performance impact (if applicable)

## Code Guidelines

### Rust
- Use `cargo fmt` and `cargo clippy`
- Write doc comments (`///`)
- Add unit tests
- Use `anyhow` for errors, `thiserror` for library errors

### Go
- Use `gofmt`
- Follow standard Go conventions
- Write table-driven tests
- Use meaningful variable names

### Python (Legacy)
- Follow PEP 8
- Use type hints
- Maintain backward compatibility

## Testing

### Unit Tests
```bash
cd rust && cargo test
cd go && go test ./...
```

### Integration Tests
```bash
just test-integration
```

### Benchmarks
```bash
just bench
```

## Documentation

- Update `AGENTS.md` for architecture changes
- Update `README.md` for user-facing changes
- Add rustdoc comments for public APIs
- Update CHANGELOG.md

## Release Process

1. Update version in `Cargo.toml` and `go.mod`
2. Update `CHANGELOG.md`
3. Create git tag: `git tag -a v2.x.x -m "Release 2.x.x"`
4. Push tag: `git push origin v2.x.x`
5. CI will build and release automatically

## Questions?

- Open an issue for bugs or feature requests
- Join our Discord for discussions

Thank you for contributing! 🎉
