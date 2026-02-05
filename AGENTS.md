# AGENTS.md - Novelist Project

This document provides essential context for AI agents working on the novelist project.

## Project Overview

A local-first AI novel writing assistant that provides "AI Novelist"-level creative writing experience **without fine-tuning**. It uses In-Context Learning (ICL), Context Engineering, and Agent Swarm architecture.

### Core Philosophy

- **No Training Required**: No DAPT/SFT/LoRA weight updates
- **Inference-Time Architecture**: Quality through ICL, rules, memory, and inspection/correction loops
- **Local-First**: Default to local inference (Qwen3-1.7B), optional cloud provider fallback
- **Human-in-the-Loop**: Writer is human-led, AI-assisted (not fully autonomous)

## Project Structure

```
novelist/
├── AGENTS.md                 # This file - agent context
├── docs/
│   └── keikaku.md           # Design specification (Japanese)
├── .agents/skills/          # Kimi skills for this project
│   ├── design-compliance-checker/  # Verify keikaku.md compliance
│   ├── novelist-tester/           # Run regression tests
│   └── project-roadmap/           # Track Phase 0/1/2 progress
├── templates/               # SSOT document templates
│   ├── bible.md.template
│   ├── character.json.template
│   └── config.yaml.template
└── src/                     # Implementation (to be created)
    ├── agents/             # Director, Writer, Checker, Editor, Committer
    ├── pal/                # Provider Abstraction Layer
    ├── memory/             # Episodic, Facts, Foreshadowing
    └── ui/                 # Web interface
```

## Single Source of Truth (SSOT)

Every novel project follows this structure:

```
Project/
├── bible.md              # World setting + Style rules
├── characters/
│   ├── protagonist.json
│   └── supporting.json
├── chapters/
│   ├── chapter_01.md
│   └── chapter_02.md
├── memory/
│   ├── episodic.md      # Recent summaries (variable)
│   ├── facts.json       # Immutable facts (append-only)
│   └── foreshadow.json  # Foreshadowing tracking
├── runs/                # Execution logs
└── config.yaml          # Provider routing, budgets
```

See `templates/` for detailed format specifications.

## Agent Swarm Architecture (5 Agents)

### 1. Director
- **Input**: Bible, Characters, Facts, Episodic, Foreshadowing
- **Output**: SceneSpec (JSON)
- **Requirements**: Long context, structured output
- **Model**: Capable of JSON generation

### 2. Writer
- **Input**: SceneSpec + all context blocks
- **Output**: Prose only (NO meta-thoughts, NO JSON)
- **Requirements**: Creative writing, style adherence
- **Model**: Creative writing capable

### 3. ContinuityChecker
- **Input**: Generated text + Facts + Characters
- **Output**: List of issues (NOT corrected text)
- **Checks**: Fact contradictions, tone deviations, POV consistency, setting violations
- **Model**: Analytical, detail-oriented

### 4. StyleEditor
- **Input**: Text with issues
- **Output**: Improved text or diff
- **Fixes**: Redundancy, repetition, tempo, line breaks
- **Model**: Good at prose refinement

### 5. Committer
- **Input**: Approved text + current Memory
- **Output**: Memory updates (Episodic/Facts/Foreshadowing)
- **Actions**: Update memory, save chapter, log execution
- **Model**: Structured extraction

## Provider Abstraction Layer (PAL)

All providers implement:

```python
generate(messages: List[Dict], params: Dict) -> Union[str, Iterator[str]]
capabilities() -> Dict  # {ctx_len, tools, json_mode, thinking_mode, ...}
healthcheck() -> bool
# Optional: price_estimate(tokens) -> float
```

### Supported Providers
- **local_ollama**: Qwen3-1.7B (default)
- **openai**: GPT-4, GPT-3.5
- **anthropic**: Claude

### Capability-Based Routing

Configure per-agent provider in `config.yaml`:
```yaml
provider:
  default: local_ollama
  routing:
    director: local_ollama      # Needs JSON
    writer: local_ollama        # Needs creativity
    checker: openai            # Can use cloud for accuracy
    editor: local_ollama
    committer: local_ollama
```

## Prompt Program Structure

Every generation assembles these blocks in order:

1. **Style Bible**: First person, sentence endings, metaphors, forbidden words
2. **World Bible**: Setting, tech level, glossary, prohibitions
3. **Character Cards**: Tone, values, relationships, forbidden words
4. **Facts**: Immutable facts (short, append-only)
5. **Episodic Recap**: Recent summaries (200-400 chars, overwritten)
6. **SceneSpec**: Current scene design (10-20 lines)
7. **ICL Examples**: 3 micro examples (bad→good, tone, tempo)

Context Budgets (default):
- bible: 1500 tokens
- characters: 1200 tokens
- facts: 600 tokens
- recap: 400 tokens
- icl: 600 tokens

## Development Roadmap

### Phase 0: Skeleton (2-3 days)
- [ ] SSOT structure
- [ ] Basic Writer + Bible loading
- [ ] Single local provider
- **Exit**: Can generate a scene

### Phase 1: 2-Stage & Memory (+3-5 days)
- [ ] Director → Writer pipeline
- [ ] Memory management (Episodic/Facts/Foreshadowing)
- [ ] 20 regression tests
- **Exit**: Full pipeline, memory persists

### Phase 2: Swarm & Multi-Provider (+1-2 weeks)
- [ ] Checker/Editor/Committer
- [ ] PAL with 2+ providers
- [ ] Provider routing
- [ ] Token/cost visualization
- **Exit**: All 5 agents, provider switching

See `.agents/skills/project-roadmap/` for detailed task tracking.

## Quality Metrics

### Automatic Metrics
- **Meta-speech rate**: < 1% (detects "この物語は...", "読者の皆さん...")
- **Repetition rate**: < 5% (n-gram detection)
- **Fact contradictions**: 0 (against facts.json)
- **Character deviations**: 0 (tone, pronoun, forbidden words)

### Regression Testing
20 fixed prompts covering:
- F1-F5: Fantasy scenarios
- SF1-SF5: Sci-fi scenarios
- M1-M5: Modern/literary
- S1-S5: Stress tests

Run with: `python .agents/skills/novelist-tester/scripts/run_tests.py --all`

## Safety & Constraints

### Revision Loop
- **MAX 1 revision** (prevent infinite loops)
- If still failing: Return failure reason + user choice

### Context Compression Strategy
- Facts: Keep minimal (don't let it bloat)
- Episodic: Only last N scenes (overwrite older)
- Foreshadowing: ID-based tracking with status

### Security
- Local storage default
- Cloud usage shows transmission scope
- API keys in OS credential store

## Key Design Decisions

1. **No Full Autonomy**: Human is the writer, AI assists
2. **No Infinite Context**: Compression through summaries and fact extraction
3. **No Media (Phase 1)**: Text-only initially
4. **File-Based SSOT**: Git-friendly, portable, inspectable

## Useful Commands

```bash
# Check design compliance
python .agents/skills/design-compliance-checker/scripts/check_compliance.py --all

# Run regression tests
python .agents/skills/novelist-tester/scripts/run_tests.py --all

# Check roadmap progress
python .agents/skills/project-roadmap/scripts/roadmap.py status

# List next tasks
python .agents/skills/project-roadmap/scripts/roadmap.py next
```

## References

- **Design Spec**: `docs/keikaku.md` (Japanese)
- **Skills**: `.agents/skills/*/SKILL.md`
- **Templates**: `templates/`

## Contributing

When modifying:
1. Update `docs/keikaku.md` if design changes
2. Update `.agents/skills/` if process changes
3. Run compliance check: `design-compliance-checker`
4. Update this AGENTS.md if architecture changes
