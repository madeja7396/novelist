{
  description = "Novelist - High-performance AI novel writing assistant";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    rust-overlay.url = "github:oxalica/rust-overlay";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, rust-overlay, flake-utils, ... }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        overlays = [ (import rust-overlay) ];
        pkgs = import nixpkgs {
          inherit system overlays;
        };
        
        # Rust toolchain
        rustToolchain = pkgs.rust-bin.stable.latest.default.override {
          extensions = [ "rust-src" "rust-analyzer" "clippy" "rustfmt" ];
          targets = [ 
            "x86_64-unknown-linux-gnu"
            "wasm32-unknown-unknown"
          ];
        };
        
        # Go toolchain
        goToolchain = pkgs.go_1_21;
        
        # Python for legacy compatibility
        pythonEnv = pkgs.python312.withPackages (ps: with ps; [
          pydantic
          pyyaml
          httpx
          numpy
        ]);
        
        # System dependencies
        nativeBuildInputs = with pkgs; [
          # Rust
          rustToolchain
          cargo-watch
          cargo-audit
          cargo-tarpaulin
          
          # Go
          goToolchain
          gopls
          golangci-lint
          
          # Python (for hybrid)
          pythonEnv
          
          # Build tools
          pkg-config
          cmake
          protobuf
          
          # Nix tools
          nixpkgs-fmt
          nil
          
          # Dev tools
          just
          jq
          fd
          ripgrep
        ];
        
        buildInputs = with pkgs; [
          openssl
          sqlite
        ];
        
      in
      {
        # Development shell
        devShells.default = pkgs.mkShell {
          inherit nativeBuildInputs buildInputs;
          
          shellHook = ''
            echo "🚀 Novelist Development Environment"
            echo ""
            echo "Available tools:"
            echo "  rustc $(rustc --version)"
            echo "  go $(go version)"
            echo "  python $(python --version)"
            echo ""
            echo "Project structure:"
            echo "  ./rust/     - Rust core (high-performance components)"
            echo "  ./go/       - Go services (API, agents)"
            echo "  ./src/      - Python (legacy compatibility)"
            echo "  ./web/      - WebAssembly UI"
            echo ""
            
            # Set up environment
            export RUST_BACKTRACE=1
            export RUST_LOG=debug
            export GOPATH="$PWD/.go"
            export PATH="$GOPATH/bin:$PATH"
            
            # Create local directories
            mkdir -p .go/bin .go/pkg
          '';
        };
        
        # Packages
        packages = {
          # Rust core library
          novelist-core = pkgs.rustPlatform.buildRustPackage {
            pname = "novelist-core";
            version = "0.2.0";
            src = ./rust;
            cargoLock = {
              lockFile = ./rust/Cargo.lock;
            };
            nativeBuildInputs = nativeBuildInputs;
            buildInputs = buildInputs;
          };
          
          # Go agent service
          novelist-agent = pkgs.buildGoModule {
            pname = "novelist-agent";
            version = "0.2.0";
            src = ./go;
            vendorHash = null; # Use go.mod
          };
          
          # Full package
          default = pkgs.symlinkJoin {
            name = "novelist";
            paths = [ 
              self.packages.${system}.novelist-core
              self.packages.${system}.novelist-agent
            ];
          };
        };
        
        # Apps
        apps = {
          novelist-core = {
            type = "app";
            program = "${self.packages.${system}.novelist-core}/bin/novelist-core";
          };
          novelist-agent = {
            type = "app";
            program = "${self.packages.${system}.novelist-agent}/bin/novelist-agent";
          };
          default = self.apps.${system}.novelist-core;
        };
        
        # Formatter
        formatter = pkgs.nixpkgs-fmt;
      });
}
