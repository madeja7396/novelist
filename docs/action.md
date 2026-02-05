# Github action結果
## rust
Current runner version: '2.331.0'
Runner Image Provisioner
Operating System
Runner Image
GITHUB_TOKEN Permissions
Secret source: Actions
Prepare workflow directory
Prepare all required actions
Getting action download info
Error: Unable to resolve action dtolnay/rust-action, repository not foundS

## go
Run cd go && go vet ./...
Error: cmd/api/main.go:12:2: missing go.sum entry for module providing package github.com/gin-gonic/gin (imported by github.com/novelist/novelist/cmd/api); to add:
	go get github.com/novelist/novelist/cmd/api
Error: cmd/api/main.go:13:2: no required module provides package github.com/novelist/novelist/go/pkg/agents; to add it:
	go get github.com/novelist/novelist/go/pkg/agents
Error: cmd/api/main.go:14:2: no required module provides package github.com/novelist/novelist/go/pkg/api; to add it:
	go get github.com/novelist/novelist/go/pkg/api
Error: cmd/api/main.go:15:2: no required module provides package github.com/novelist/novelist/go/pkg/config; to add it:
	go get github.com/novelist/novelist/go/pkg/config
Error: cmd/api/main.go:16:2: missing go.sum entry for module providing package github.com/rs/zerolog (imported by github.com/novelist/novelist/cmd/api); to add:
	go get github.com/novelist/novelist/cmd/api
Error: pkg/agents/agent.go:8:2: no required module provides package github.com/novelist/novelist/go/pkg/models; to add it:
	go get github.com/novelist/novelist/go/pkg/models
Error: pkg/agents/agent.go:9:2: missing go.sum entry for module providing package github.com/rs/zerolog/log (imported by github.com/novelist/novelist/pkg/agents); to add:
	go get github.com/novelist/novelist/pkg/agents
Error: pkg/api/handlers.go:7:2: missing go.sum entry for module providing package github.com/google/uuid (imported by github.com/novelist/novelist/pkg/api); to add:
	go get github.com/novelist/novelist/pkg/api
Error: pkg/config/config.go:9:2: missing go.sum entry for module providing package github.com/spf13/viper (imported by github.com/novelist/novelist/pkg/config); to add:
	go get github.com/novelist/novelist/pkg/config
Error: Process completed with exit code 1.

## nix
Run nix flake check
unpacking 'github:numtide/flake-utils/11707dc2f618dd54ca8739b309ec4fc024de578b' into the Git cache...
unpacking 'github:NixOS/nixpkgs/00c21e4c93d963c50d4c0c89bfa84ed6e0694df2' into the Git cache...
unpacking 'github:oxalica/rust-overlay/42ec85352e419e601775c57256a52f6d48a39906' into the Git cache...
warning: creating lock file "/home/runner/work/novelist/novelist/flake.lock": 
• Added input 'flake-utils':
    'github:numtide/flake-utils/11707dc' (2024-11-13)
• Added input 'flake-utils/systems':
    'github:nix-systems/default/da67096' (2023-04-09)
• Added input 'nixpkgs':
    'github:NixOS/nixpkgs/00c21e4' (2026-02-04)
• Added input 'rust-overlay':
    'github:oxalica/rust-overlay/42ec853' (2026-02-05)
• Added input 'rust-overlay/nixpkgs':
    'github:NixOS/nixpkgs/18dd725' (2025-04-13)
evaluating flake...
unpacking 'github:nix-systems/default/da67096a3b9bf56a91d16901293e51ba5b49a27e?narHash=sha256-Vy1rq5AaRuLzOxct8nz4T6wlgyUR7zLU309k9mBC768%3D' into the Git cache...
checking flake output 'devShells'...
checking flake output 'apps'...
checking app 'apps.x86_64-linux.default'...
checking flake output 'formatter'...
checking derivation formatter.x86_64-linux...
derivation evaluated to /nix/store/slzhg6w6nf9a9wmsav5jbscv30nsav83-nixpkgs-fmt-1.3.0.drv
checking flake output 'packages'...
checking derivation packages.x86_64-linux.default...
checking derivation devShells.x86_64-linux.default...
error (ignored): attribute 'go_1_21' missing
error (ignored): Path 'rust/Cargo.lock' does not exist in Git repository "/home/runner/work/novelist/novelist".
error:
       … while checking flake output 'apps'
         at «github:numtide/flake-utils/11707dc»/lib.nix:43:9:
           42|       // {
           43|         ${key} = (attrs.${key} or { }) // {
             |         ^
           44|           ${system} = ret.${key};

       … while checking the app definition 'apps.x86_64-linux.default'
         at /home/runner/work/novelist/novelist/flake.nix:149:11:
          148|           };
          149|           default = self.apps.${system}.novelist-core;
             |           ^
          150|         };

       (stack trace truncated; use '--show-trace' to show the full, detailed trace)

       error: Path 'rust/Cargo.lock' does not exist in Git repository "/home/runner/work/novelist/novelist".
Error: Process completed with exit code 1.

## python
Run python tests/test_integration.py
....
----------------------------------------------------------------------
Ran 4 tests in 0.016s

OK
Traceback (most recent call last):
  File "/home/runner/work/novelist/novelist/tests/test_phase1.py", line 21, in <module>
    from rag.retriever import SimpleRetriever
  File "/home/runner/work/novelist/novelist/src/rag/retriever.py", line 10, in <module>
    import numpy as np
ModuleNotFoundError: No module named 'numpy'
Error: Process completed with exit code 1.

## quality
Run nix run nixpkgs#nixpkgs-fmt -- --check .
unpacking 'github:NixOS/nixpkgs/aa290c9891fa4ebe88f8889e59633d20cc06a5f2' into the Git cache...
these 7 paths will be fetched (9.9 MiB download, 45.0 MiB unpacked):
  /nix/store/j2kgllgds4w7na8zqv1msi0mpvpjxda8-gcc-15.2.0-lib
  /nix/store/yjmjazfwljzajwq54xlr7vfz77spzr9y-gcc-15.2.0-libgcc
  /nix/store/wb6rhpznjfczwlwx23zmdrrw74bayxw4-glibc-2.42-47
  /nix/store/d0d9wqmw5saaynfvmszsda3dmh5q82z8-libidn2-2.3.8
  /nix/store/pkphs076yz5ajnqczzj0588n6miph269-libunistring-1.4.1
  /nix/store/bhjnv6na5lzrfnrnrij1npg0zfgjp0x2-nixpkgs-fmt-1.3.0
  /nix/store/kbijm6lc9va8xann3cfyam0vczzmwkxj-xgcc-15.2.0-libgcc
copying path '/nix/store/yjmjazfwljzajwq54xlr7vfz77spzr9y-gcc-15.2.0-libgcc' from 'https://cache.nixos.org'...
copying path '/nix/store/kbijm6lc9va8xann3cfyam0vczzmwkxj-xgcc-15.2.0-libgcc' from 'https://cache.nixos.org'...
copying path '/nix/store/pkphs076yz5ajnqczzj0588n6miph269-libunistring-1.4.1' from 'https://cache.nixos.org'...
copying path '/nix/store/d0d9wqmw5saaynfvmszsda3dmh5q82z8-libidn2-2.3.8' from 'https://cache.nixos.org'...
copying path '/nix/store/wb6rhpznjfczwlwx23zmdrrw74bayxw4-glibc-2.42-47' from 'https://cache.nixos.org'...
copying path '/nix/store/j2kgllgds4w7na8zqv1msi0mpvpjxda8-gcc-15.2.0-lib' from 'https://cache.nixos.org'...
copying path '/nix/store/bhjnv6na5lzrfnrnrij1npg0zfgjp0x2-nixpkgs-fmt-1.3.0' from 'https://cache.nixos.org'...
./flake.nix
1 / 1 would have been reformatted
error: fail on changes
Error: Process completed with exit code 1.