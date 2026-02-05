---
name: design-compliance-checker
description: Verify that the novelist project implementation complies with the design specification (keikaku.md). Use when checking SSOT file structure, PAL interface implementation, Agent configurations, data schemas, or validating that code changes follow the architectural decisions documented in the design.
---

# Design Compliance Checker

Check that the implementation follows the design specification in `docs/keikaku.md`.

## Quick Start

Run a full compliance check:
```bash
python .agents/skills/design-compliance-checker/scripts/check_compliance.py --all
```

Check specific areas:
```bash
# Check SSOT file structure only
python .agents/skills/design-compliance-checker/scripts/check_compliance.py --ssot

# Check PAL implementation only
python .agents/skills/design-compliance-checker/scripts/check_compliance.py --pal

# Check Agent configuration
python .agents/skills/design-compliance-checker/scripts/check_compliance.py --agents
```

## What to Check

### 1. SSOT File Structure (Section 3)

Verify that the project follows the Single Source of Truth structure:

```
Project/
├── bible.md              # World setting rules
├── characters/*.json     # Character cards
├── chapters/*.md         # Main text
├── memory/
│   ├── episodic.md       # Recent summaries
│   ├── facts.json        # Immutable facts
│   └── foreshadow.json   # Foreshadowing list
├── runs/*.jsonl          # Execution logs
└── config.yaml           # Provider routing & settings
```

**Critical requirements:**
- `bible.md` must exist and contain: Style Bible, World Bible
- `characters/` directory with `.json` files containing: tone, values, relationships, forbidden words
- `chapters/` directory with `.md` files
- `memory/` directory with episodic.md, facts.json, foreshadow.json

### 2. PAL Interface (Section 4.1)

Verify the Provider Abstraction Layer implements:

```python
# Required methods
generate(messages, params) -> text | stream
capabilities() -> {ctx_len, tools, json_mode, thinking_mode, ...}
price_estimate(tokens) -> cost  # optional
healthcheck()
```

**Capabilities to declare:**
- `ctx_len`: Context length limit
- `tools`: Tool calling support
- `json_mode`: JSON output reliability
- `thinking_mode`: Thinking/thought process toggle

### 3. Agent Configuration (Section 6.1)

Verify the 5 MVP agents exist with proper roles:

| Agent | Role | Output Format | Key Requirements |
|-------|------|---------------|------------------|
| Director | Generate SceneSpec | Structured text/JSON | Uses Bible, Facts, Episodic, Foreshadowing |
| Writer | Generate main text | Prose only (no meta-thoughts) | Follows Style Bible, Character Cards |
| ContinuityChecker | Detect inconsistencies | Issue list | Checks facts, tone, POV, setting deviations |
| StyleEditor | Improve prose | Diff/patch | Fixes redundancy, repetition, tempo |
| Committer | Update Memory | Diff updates | Updates Episodic/Facts/Foreshadowing |

### 4. Data Schemas

#### Character Card (characters/*.json)
```json
{
  "name": "string",
  "tone": "string (speech pattern)",
  "values": ["string"],
  "relationships": {"char_name": "description"},
  "forbidden_words": ["string"],
  "first_person": "string",
  "speech_pattern": "string"
}
```

#### SceneSpec (Director output)
```json
{
  "scene_id": "string",
  "chapter": "number",
  "objective": "string (scene purpose)",
  "constraints": ["string"],
  "foreshadowing": ["foreshadow_id"],
  "pov_character": "string",
  "mood": "string",
  "key_events": ["string"]
}
```

#### Facts (memory/facts.json)
```json
{
  "facts": [
    {"id": "f001", "content": "string", "category": "immutable", "source": "chapter_1"}
  ]
}
```

#### Foreshadowing (memory/foreshadow.json)
```json
{
  "foreshadowings": [
    {"id": "fs001", "content": "string", "status": "unresolved|resolved", "related_chapters": ["c1"]}
  ]
}
```

### 5. Prompt Program Structure (Section 5.1)

Verify prompts are constructed in this order:
1. Style Bible (文体規約)
2. World Bible (世界観)
3. Character Cards
4. Facts (確定事実)
5. Episodic Recap (直近要約)
6. SceneSpec (設計図)
7. ICL Examples (マイクロ例×3)

### 6. Context Budgets (Section 10)

Verify config.yaml respects these defaults:
- `bible`: 1500 tokens
- `characters`: 1200 tokens
- `facts`: 600 tokens
- `recap`: 400 tokens
- `icl`: 600 tokens

## Reference

For detailed checklists, see [references/checklist.md](references/checklist.md)
