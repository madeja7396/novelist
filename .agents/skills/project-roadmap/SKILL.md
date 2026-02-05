---
name: project-roadmap
description: Manage the novelist project development roadmap and track progress across Phase 0/1/2. Use when checking current phase status, listing next tasks, estimating remaining work, updating completed features, or planning the development schedule based on the keikaku.md design document.
---

# Project Roadmap

Track and manage development progress for the novelist project.

## Quick Start

Check current status:
```bash
python .agents/skills/project-roadmap/scripts/roadmap.py status
```

List next tasks:
```bash
python .agents/skills/project-roadmap/scripts/roadmap.py next --count 5
```

Show full roadmap:
```bash
python .agents/skills/project-roadmap/scripts/roadmap.py show
```

Mark task complete:
```bash
python .agents/skills/project-roadmap/scripts/roadmap.py complete "F1: Magic System Introduction"
```

## Phases Overview

### Phase 0: Skeleton (2-3 days)
**Goal:** Basic functional structure

**Key Deliverables:**
- Project structure (SSOT)
- Writer agent + Bible loading
- Single local provider (Qwen3-1.7B)

**Exit Criteria:**
- Can create new project
- Can generate a scene with Bible context

### Phase 1: 2-Stage & Memory (+3-5 days)
**Goal:** Director→Writer pipeline with memory

**Key Deliverables:**
- Director agent with SceneSpec output
- Memory management (Episodic/Facts/Foresc.shadowing)
- 20 regression tests

**Exit Criteria:**
- Full pipeline executes end-to-end
- Memory persists across scenes
- All 20 tests pass

### Phase 2: Swarm & Multi-Provider (+1-2 weeks)
**Goal:** Complete agent swarm with provider abstraction

**Key Deliverables:**
- Checker/Editor/Committer agents
- PAL with 2+ providers
- Provider routing by agent role
- Token/cost/speed visualization

**Exit Criteria:**
- All 5 agents functional
- Can switch providers mid-project
- Revision loop works (max 1)

## Task Commands

### Show Current Phase
```bash
python .agents/skills/project-roadmap/scripts/roadmap.py phase
```

Output:
```
Current Phase: Phase 1 (2-Stage & Memory)
Progress: 8/15 tasks completed (53%)
Estimated remaining: 2-3 days
```

### List Tasks by Phase
```bash
# All Phase 1 tasks
python .agents/skills/project-roadmap/scripts/roadmap.py tasks --phase 1

# Incomplete tasks only
python .agents/skills/project-roadmap/scripts/roadmap.py tasks --incomplete

# By category
python .agents/skills/project-roadmap/scripts/roadmap.py tasks --category agent
```

### Get Next Tasks
```bash
# Default: top 3 by priority
python .agents/skills/project-roadmap/scripts/roadmap.py next

# Custom count
python .agents/skills/project-roadmap/scripts/roadmap.py next --count 5

# Include rationale
python .agents/skills/project-roadmap/scripts/roadmap.py next --verbose
```

### Update Progress
```bash
# Mark task complete
python .agents/skills/project-roadmap/scripts/roadmap.py complete "Task name"

# Mark task in-progress
python .agents/skills/project-roadmap/scripts/roadmap.py start "Task name"

# Mark task blocked
python .agents/skills/project-roadmap/scripts/roadmap.py block "Task name" --reason "Waiting for API"

# Reset task to pending
python .agents/skills/project-roadmap/scripts/roadmap.py reset "Task name"
```

### Estimate Work
```bash
# Estimate remaining work
python .agents/skills/project-roadmap/scripts/roadmap.py estimate

Output:
Phase 0: Complete ✓
Phase 1: 7 tasks remaining (~3 days)
Phase 2: 15 tasks remaining (~10 days)
Total: ~13 days remaining
```

## Task Status File

Progress is stored in `.agents/skills/project-roadmap/progress.json`:

```json
{
  "version": "1.0",
  "updated": "2026-02-06T00:00:00Z",
  "current_phase": 1,
  "tasks": [
    {
      "id": "P0-01",
      "phase": 0,
      "name": "Project structure setup",
      "category": "infrastructure",
      "status": "completed",
      "completed_at": "2026-02-05T10:00:00Z"
    }
  ]
}
```

## Categories

Tasks are organized by category:

- **infrastructure**: Project setup, file structure, config
- **agent**: Agent implementations
- **pal**: Provider Abstraction Layer
- **memory**: Memory management
- **ui**: User interface
- **testing**: Tests and metrics
- **docs**: Documentation

## Priority Rules

When determining next tasks:

1. **Phase order**: Complete Phase 0 before Phase 1, etc.
2. **Dependencies**: Tasks with dependencies must wait for prerequisites
3. **Infrastructure first**: Core structure before features
4. **Vertical slice**: Get basic end-to-end working before polish

## Reference

For detailed task specifications, see [references/roadmap.md](references/roadmap.md)
