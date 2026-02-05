# Novelist Project Roadmap

Detailed task specifications based on `docs/keikaku.md`.

## Phase 0: Skeleton (2-3 days)

**Goal:** Basic functional structure that can generate a scene.

### P0-01: Project Structure Setup
- **Category**: infrastructure
- **Dependencies**: None
- **Description**: Create SSOT directory structure
- **Deliverables**:
  - `bible.md` template
  - `characters/` directory
  - `chapters/` directory
  - `memory/` directory with episodic.md, facts.json, foreshadow.json
  - `runs/` directory
  - `config.yaml` template

### P0-02: Bible Parser
- **Category**: infrastructure
- **Dependencies**: P0-01
- **Description**: Parse bible.md into structured format
- **Deliverables**:
  - Parser for Style Bible section
  - Parser for World Bible section
  - Validation of required fields

### P0-03: Character Loader
- **Category**: infrastructure
- **Dependencies**: P0-01
- **Description**: Load and validate character JSON files
- **Deliverables**:
  - JSON schema validation
  - Character card formatter for prompts

### P0-04: Local Provider (Ollama)
- **Category**: pal
- **Dependencies**: None
- **Description**: Implement Ollama provider
- **Deliverables**:
  - `generate(messages, params)` method
  - `capabilities()` method
  - `healthcheck()` method
  - Support for Qwen3-1.7B

### P0-05: Writer Agent (Basic)
- **Category**: agent
- **Dependencies**: P0-02, P0-03, P0-04
- **Description**: Single-turn scene generation
- **Deliverables**:
  - Accepts: Bible + Characters + Scene description
  - Outputs: Generated prose
  - Basic prompt template

### P0-06: CLI Interface
- **Category**: ui
- **Dependencies**: P0-05
- **Description**: Command-line interface for generation
- **Deliverables**:
  - `novelist generate` command
  - Project initialization command
  - Basic output formatting

### P0-07: Integration Test
- **Category**: testing
- **Dependencies**: P0-06
- **Description**: End-to-end test of basic flow
- **Deliverables**:
  - Can create project
  - Can generate scene
  - Output saved to chapters/

---

## Phase 1: 2-Stage & Memory (+3-5 days)

**Goal:** Director→Writer pipeline with memory management.

### P1-01: SceneSpec Schema
- **Category**: infrastructure
- **Dependencies**: None
- **Description**: Define SceneSpec JSON schema
- **Deliverables**:
  - JSON Schema for SceneSpec
  - Validation function
  - Example SceneSpecs

### P1-02: Director Agent
- **Category**: agent
- **Dependencies**: P1-01
- **Description**: Generate SceneSpec from context
- **Deliverables**:
  - Accepts: Bible + Characters + Facts + Episodic + Foreshadowing
  - Outputs: SceneSpec JSON
  - Handles long context

### P1-03: Memory: Episodic
- **Category**: memory
- **Dependencies**: None
- **Description**: Manage episodic memory (recap)
- **Deliverables**:
  - `memory/episodic.md` format
  - Recap generator (summarize scenes)
  - Recap retriever (get last N scenes)

### P1-04: Memory: Facts
- **Category**: memory
- **Dependencies**: None
- **Description**: Manage immutable facts
- **Deliverables**:
  - `memory/facts.json` format
  - Fact extractor (from scenes)
  - Fact validator

### P1-05: Memory: Foreshadowing
- **Category**: memory
- **Dependencies**: None
- **Description**: Manage foreshadowing tracking
- **Deliverables**:
  - `memory/foreshadow.json` format
  - Foreshadowing extractor
  - Status tracking (unresolved/resolved/abandoned)

### P1-06: Writer Agent (SceneSpec)
- **Category**: agent
- **Dependencies**: P1-02
- **Description**: Enhanced Writer using SceneSpec
- **Deliverables**:
  - Accepts: SceneSpec + all context blocks
  - Follows SceneSpec constraints
  - Outputs structured prose

### P1-07: Prompt Assembler
- **Category**: infrastructure
- **Dependencies**: P1-03, P1-04, P1-05, P1-06
- **Description**: Assemble Prompt Program blocks
- **Deliverables**:
  - Assemble in correct order
  - Respect context budgets
  - ICL example injection

### P1-08: 2-Stage Pipeline
- **Category**: infrastructure
- **Dependencies**: P1-02, P1-07
- **Description**: Connect Director → Writer
- **Deliverables**:
  - Director output feeds Writer
  - Error handling
  - Logging

### P1-09: Committer Agent (Basic)
- **Category**: agent
- **Dependencies**: P1-03, P1-04, P1-05
- **Description**: Update memory after generation
- **Deliverables**:
  - Update episodic.md
  - Extract and add facts
  - Update foreshadowing status

### P1-10: Regression Test Suite
- **Category**: testing
- **Dependencies**: P1-08
- **Description**: 20 fixed prompt tests
- **Deliverables**:
  - F1-F5: Fantasy tests
  - SF1-SF5: Sci-Fi tests
  - M1-M5: Modern/Literary tests
  - S1-S5: Stress tests

### P1-11: Metrics Calculator
- **Category**: testing
- **Dependencies**: P1-10
- **Description**: Calculate quality metrics
- **Deliverables**:
  - Meta-speech rate
  - Repetition rate
  - Fact contradiction detection
  - Character deviation detection

### P1-12: Test Runner
- **Category**: testing
- **Dependencies**: P1-10, P1-11
- **Description**: Automated test execution
- **Deliverables**:
  - Run all 20 tests
  - Generate report
  - Version comparison

### P1-13: ICL Examples
- **Category**: infrastructure
- **Dependencies**: None
- **Description**: Create in-context learning examples
- **Deliverables**:
  - Bad→Good examples (×3 per genre)
  - Tone examples per character type
  - Narrative tempo examples

### P1-14: Web UI (Basic)
- **Category**: ui
- **Dependencies**: P1-08
- **Description**: Simple web interface
- **Deliverables**:
  - Left: Project tree
  - Center: Editor
  - Right: Controls
  - Basic generation flow

### P1-15: Phase 1 Integration
- **Category**: testing
- **Dependencies**: P1-08, P1-09, P1-14
- **Description**: Full pipeline test
- **Deliverables**:
  - End-to-end workflow
  - All 20 tests pass
  - Memory persists correctly

---

## Phase 2: Swarm & Multi-Provider (+1-2 weeks)

**Goal:** Complete agent swarm with provider abstraction and routing.

### P2-01: PAL Interface Definition
- **Category**: pal
- **Dependencies**: None
- **Description**: Formalize Provider Abstraction Layer
- **Deliverables**:
  - Interface specification
  - Capabilities schema
  - Error handling standard

### P2-02: Cloud Provider (OpenAI)
- **Category**: pal
- **Dependencies**: P2-01
- **Description**: OpenAI API provider
- **Deliverables**:
  - OpenAI-compatible `generate()`
  - Proper system message handling
  - JSON mode support

### P2-03: Cloud Provider (Anthropic)
- **Category**: pal
- **Dependencies**: P2-01
- **Description**: Anthropic Claude provider
- **Deliverables**:
  - Claude-compatible `generate()`
  - Thinking mode support
  - Proper message formatting

### P2-04: Provider Routing
- **Category**: pal
- **Dependencies**: P2-02, P2-03
- **Description**: Route agents to different providers
- **Deliverables**:
  - Configurable per-agent routing
  - Capability-based routing
  - Fallback handling

### P2-05: ContinuityChecker Agent
- **Category**: agent
- **Dependencies**: P2-01
- **Description**: Detect inconsistencies
- **Deliverables**:
  - Accepts: Text + Facts + Characters
  - Outputs: Issue list (not corrected text)
  - Checks: facts, tone, POV, setting

### P2-06: StyleEditor Agent
- **Category**: agent
- **Dependencies**: P2-01
- **Description**: Improve prose quality
- **Deliverables**:
  - Accepts: Text with issues
  - Outputs: Improved text or diff
  - Fixes: redundancy, repetition, tempo

### P2-07: Committer Agent (Full)
- **Category**: agent
- **Dependencies**: P2-05, P2-06
- **Description**: Complete committer with validation
- **Deliverables**:
  - Validate text before commit
  - Generate memory updates
  - Log execution to runs/

### P2-08: Revision Loop
- **Category**: infrastructure
- **Dependencies**: P2-05, P2-06
- **Description**: Checker → Editor → validation
- **Deliverables**:
  - Max 1 revision enforced
  - Failure reason on persistent issues
  - User choice for resolution

### P2-09: Token/Cost Tracking
- **Category**: infrastructure
- **Dependencies**: P2-04
- **Description**: Track usage per request
- **Deliverables**:
  - Token counting
  - Cost estimation
  - Per-agent breakdown

### P2-10: Execution Log
- **Category**: infrastructure
- **Dependencies**: None
- **Description**: Detailed run logging
- **Deliverables**:
  - `runs/*.jsonl` format
  - Prompt/response logging
  - Token/cost per step
  - Error tracking

### P2-11: Web UI (Enhanced)
- **Category**: ui
- **Dependencies**: P1-14, P2-09, P2-10
- **Description**: Full UI with monitoring
- **Deliverables**:
  - Provider switcher
  - Token/cost display
  - Execution log viewer
  - Agent status display

### P2-12: Security Implementation
- **Category**: infrastructure
- **Dependencies**: P2-02, P2-03
- **Description**: Secure credential handling
- **Deliverables**:
  - OS credential store integration
  - API key encryption
  - Transmission scope indicator

### P2-13: Export/Import
- **Category**: infrastructure
- **Dependencies**: None
- **Description**: Project portability
- **Deliverables**:
  - Export project to archive
  - Import project from archive
  - Git-friendly format

### P2-14: Performance Optimization
- **Category**: infrastructure
- **Dependencies**: P2-08
- **Description**: Optimize for speed
- **Deliverables**:
  - Context caching
  - Parallel where possible
  - Streaming responses

### P2-15: Phase 2 Integration
- **Category**: testing
- **Dependencies**: P2-07, P2-08, P2-11
- **Description**: Full swarm test
- **Deliverables**:
  - All 5 agents functional
  - Provider switching works
  - Revision loop functional
  - Performance acceptable

---

## Dependencies Graph

```
Phase 0:
  P0-01 → P0-02 → P0-05
        → P0-03 ↗
  P0-04 → P0-05 → P0-06 → P0-07

Phase 1:
  P1-01 → P1-02 → P1-08 → P1-15
  P1-03 → P1-07 ↗    ↘
  P1-04 → P1-07 → P1-09 ↗
  P1-05 → P1-07 ↗
  P1-06 → P1-08
  P1-13 → P1-07
  P1-08 → P1-14
  P1-10 → P1-11 → P1-12

Phase 2:
  P2-01 → P2-02 → P2-04 → P2-09 → P2-11
        → P2-03 ↗
  P2-01 → P2-05 → P2-08 → P2-15
  P2-01 → P2-06 ↗    ↘
  P2-07 → P2-15 ↗
  P2-10 → P2-11
  P2-12 (parallel)
  P2-13 (parallel)
  P2-14 (parallel)
```

## Estimation Rules

- **Infrastructure**: 0.5-1 day per task
- **Agent**: 1-2 days per task
- **PAL/Provider**: 1 day per provider
- **Memory**: 1-2 days per component
- **UI**: 2-3 days per major component
- **Testing**: 0.5-1 day per task
- **Integration**: 1-2 days per phase

Buffer: 20% for unexpected issues
