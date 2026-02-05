---
name: novelist-tester
description: Run regression tests and quality metrics for the novelist project. Use when executing the 20 fixed prompt regression tests, calculating quality metrics (meta-speech rate, repetition rate, fact contradictions, character deviations), validating scene generation quality, or comparing outputs between versions.
---

# Novelist Tester

Run regression tests and calculate quality metrics for generated scenes.

## Quick Start

Run all tests:
```bash
python .agents/skills/novelist-tester/scripts/run_tests.py --all
```

Run specific test category:
```bash
# Genre tests (Fantasy, Sci-Fi, Modern, etc.)
python .agents/skills/novelist-tester/scripts/run_tests.py --genre fantasy

# Quality metrics only
python .agents/skills/novelist-tester/scripts/run_tests.py --metrics

# Compare with previous version
python .agents/skills/novelist-tester/scripts/run_tests.py --compare runs/previous.jsonl
```

Calculate metrics for a generated file:
```bash
python .agents/skills/novelist-tester/scripts/metrics.py chapters/chapter_01.md
```

## Test Categories

### 1. Regression Tests (20 Fixed Prompts)

The 20 regression tests cover different genres and scenarios:

**Fantasy (5 tests)**
- F1: Magic system introduction scene
- F2: Dungeon exploration battle
- F3: Royal court dialogue
- F4: Monster encounter
- F5: Prophecy revelation

**Sci-Fi (5 tests)**
- SF1: Space station routine
- SF2: Alien first contact
- SF3: Cyberpunk city chase
- SF4: AI ethics dialogue
- SF5: Time paradox scene

**Modern/Literary (5 tests)**
- M1: Coffee shop conversation
- M2: Family conflict
- M3: Workplace drama
- M4: Soliloquy/monologue
- M5: Epistolary format

**Stress Tests (5 tests)**
- S1: Long context continuity (5000+ tokens)
- S2: Multiple character dialogue (6+ chars)
- S3: Style switching (comedy→tragedy)
- S4: Complex foreshadowing callback
- S5: Minimal prompt (only SceneSpec)

### 2. Quality Metrics

#### Meta-Speech Rate（メタ発言率）
Detect meta-commentary that breaks immersion:
- "この物語では..."
- "読者の皆さん..."
- "次の章で..."
- "AIとして..."

**Target:** < 1% of sentences

#### Repetition Rate（反復率）
Detect n-gram repetition:
- 3-gram repeats within 500 tokens
- Sentence start patterns
- Word frequency anomalies

**Target:** < 5% repetition

#### Fact Contradiction Count（事実矛盾数）
Compare generated text against `memory/facts.json`:
- Character attributes
- World setting details
- Timeline consistency

**Target:** 0 contradictions

#### Character Deviation Count（キャラ逸脱数）
Check against `characters/*.json`:
- First-person pronoun usage
- Speech pattern violations
- Forbidden word usage
- Value/action inconsistency

**Target:** 0 deviations

### 3. Output Format Tests

Verify Agent outputs match expected formats:

**Director:** Valid SceneSpec JSON
**Writer:** Prose only (no JSON, no meta-thoughts)
**Checker:** Issue list format
**Editor:** Diff format or corrected text
**Committer:** Memory update diff

## Test Execution

### Test Structure

Each test case:
```yaml
id: "F1"
name: "Magic system introduction"
genre: "fantasy"
prompt_blocks:
  bible: "..."
  characters: [...]
  scene_spec: {...}
expected:
  min_length: 500
  max_length: 2000
  contains: ["magic", "mana"]
  not_contains: ["AI", "computer"]
metrics:
  meta_speech_rate: 0.01
  repetition_rate: 0.05
```

### Running Tests

```bash
# Run single test
python .agents/skills/novelist-tester/scripts/run_tests.py --test F1

# Run by genre
python .agents/skills/novelist-tester/scripts/run_tests.py --genre fantasy

# Run with specific provider
python .agents/skills/novelist-tester/scripts/run_tests.py --all --provider local_ollama

# Save results
python .agents/skills/novelist-tester/scripts/run_tests.py --all --output results/$(date +%Y%m%d).json
```

### Test Results Format

```json
{
  "timestamp": "2026-02-06T00:00:00Z",
  "version": "git-commit-hash",
  "provider": "local_ollama",
  "summary": {
    "total": 20,
    "passed": 18,
    "failed": 2,
    "warnings": 1
  },
  "results": [
    {
      "id": "F1",
      "status": "passed",
      "metrics": {
        "meta_speech_rate": 0.005,
        "repetition_rate": 0.03,
        "fact_contradictions": 0,
        "char_deviations": 0
      },
      "duration_ms": 2500
    }
  ]
}
```

## Version Comparison

Compare outputs between versions:

```bash
# Compare current with previous run
python .agents/skills/novelist-tester/scripts/run_tests.py --compare runs/20260205.json

# Generate diff report
python .agents/skills/novelist-tester/scripts/compare.py runs/20260205.json runs/20260206.json
```

Comparison metrics:
- Pass/fail delta
- Quality metric trends
- Regression detection
- Improvement highlights

## Reference

For detailed test case specifications, see [references/test_cases.md](references/test_cases.md)
