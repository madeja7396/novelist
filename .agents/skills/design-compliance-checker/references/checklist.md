# Design Compliance Checklist

Complete checklist based on `docs/keikaku.md`.

## SSOT Structure Checklist

### File Structure
- [ ] `bible.md` exists
- [ ] `characters/` directory exists
- [ ] `chapters/` directory exists
- [ ] `memory/` directory exists
- [ ] `memory/episodic.md` exists
- [ ] `memory/facts.json` exists
- [ ] `memory/foreshadow.json` exists
- [ ] `runs/` directory exists
- [ ] `config.yaml` exists

### bible.md Contents
- [ ] Contains Style Bible section (文体規約)
- [ ] Contains World Bible section (世界観)
- [ ] Style Bible includes: first person, sentence endings, metaphors, forbidden words, line break rules
- [ ] World Bible includes: world setting, tech level, glossary, prohibitions

### Character Files
- [ ] All .json files in characters/ are valid JSON
- [ ] Each character has: name, tone, values, relationships
- [ ] Each character has: forbidden_words, first_person, speech_pattern

## PAL Interface Checklist

### Required Methods
- [ ] `generate(messages, params)` implemented
- [ ] `capabilities()` implemented
- [ ] `healthcheck()` implemented

### Capabilities Object
- [ ] Returns ctx_len
- [ ] Returns tools (boolean or array)
- [ ] Returns json_mode (boolean)
- [ ] Returns thinking_mode (boolean or config)

### Provider Handling
- [ ] System message handling for APIs that don't support it
- [ ] JSON mode abstraction
- [ ] Tool calling abstraction
- [ ] Context length enforcement

## Agent Configuration Checklist

### Director Agent
- [ ] Accepts: Bible, Characters, Facts, Episodic, Foreshadowing
- [ ] Outputs: SceneSpec (structured)
- [ ] Uses long-context capable model
- [ ] Outputs valid JSON when requested

### Writer Agent
- [ ] Accepts: SceneSpec + all context blocks
- [ ] Outputs: Prose only (no meta commentary)
- [ ] Follows Style Bible strictly
- [ ] Respects Character Cards

### ContinuityChecker Agent
- [ ] Accepts: generated text + Facts + Character Cards
- [ ] Outputs: List of issues (not corrected text)
- [ ] Checks: factual contradictions
- [ ] Checks: character tone deviations
- [ ] Checks: POV consistency
- [ ] Checks: setting deviations

### StyleEditor Agent
- [ ] Accepts: text with issues
- [ ] Outputs: improved text or diff
- [ ] Fixes: redundancy
- [ ] Fixes: repetition
- [ ] Fixes: tempo issues
- [ ] Fixes: line break rules

### Committer Agent
- [ ] Accepts: new text + current Memory
- [ ] Updates: episodic.md (recap)
- [ ] Updates: facts.json (new immutable facts)
- [ ] Updates: foreshadow.json (status changes)
- [ ] Logs: execution to runs/*.jsonl

## Data Schema Checklist

### Character Card Schema
```json
{
  "name": "required string",
  "tone": "required string",
  "values": ["required array of strings"],
  "relationships": {"required object": "values"},
  "forbidden_words": ["required array"],
  "first_person": "required string",
  "speech_pattern": "required string"
}
```

### SceneSpec Schema
```json
{
  "scene_id": "required string",
  "chapter": "required number",
  "objective": "required string",
  "constraints": ["array of strings"],
  "foreshadowing": ["array of foreshadow_ids"],
  "pov_character": "required string",
  "mood": "required string",
  "key_events": ["array of strings"]
}
```

### Facts Schema
```json
{
  "facts": [
    {
      "id": "required string (f###)",
      "content": "required string",
      "category": "enum: immutable|variable",
      "source": "required string (chapter_ref)"
    }
  ]
}
```

### Foreshadowing Schema
```json
{
  "foreshadowings": [
    {
      "id": "required string (fs###)",
      "content": "required string",
      "status": "enum: unresolved|resolved|abandoned",
      "related_chapters": ["array of chapter refs"],
      "resolution_chapter": "optional string"
    }
  ]
}
```

## Prompt Program Checklist

### Block Order
- [ ] 1. Style Bible
- [ ] 2. World Bible
- [ ] 3. Character Cards
- [ ] 4. Facts
- [ ] 5. Episodic Recap
- [ ] 6. SceneSpec
- [ ] 7. ICL Examples

### ICL Examples
- [ ] 3 micro examples minimum
- [ ] Bad→Good examples for style
- [ ] Tone examples for each character
- [ ] Narrative tempo examples

## Config.yaml Checklist

### Provider Section
- [ ] `provider.default` specified
- [ ] `provider.routing` maps agents to providers

### Context Budgets
- [ ] `context.budgets.bible` (default: 1500)
- [ ] `context.budgets.characters` (default: 1200)
- [ ] `context.budgets.facts` (default: 600)
- [ ] `context.budgets.recap` (default: 400)
- [ ] `context.budgets.icl` (default: 600)

### Swarm Settings
- [ ] `swarm.max_revision` (default: 1)

### Logging
- [ ] `logging.save_prompts` (boolean)
- [ ] `logging.save_outputs` (boolean)

## Loop & Safety Checklist

### Revision Loop
- [ ] Max 1 revision enforced
- [ ] Failure reason returned if still failing
- [ ] User choice required for additional attempts

### Safety
- [ ] Local storage is default
- [ ] Cloud usage shows transmission scope in UI
- [ ] API keys stored in OS credential store
