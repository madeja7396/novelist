# Regression Test Cases (20 Prompts)

Complete test specifications for the 20 fixed regression tests.

## Fantasy Genre (F1-F5)

### F1: Magic System Introduction
```yaml
id: F1
name: Magic System Introduction
genre: fantasy
difficulty: easy
purpose: Test world building consistency

prompt_blocks:
  bible: |
    ## Style Bible
    - First person: "私"
    - Sentence ending: polite desu/masu avoided, literary da/dearu
    - Metaphors: nature-based (wind, water, trees)
    - Forbidden: modern technology references
    
    ## World Bible
    - Magic comes from "mana" flowing through ley lines
    - Spell casting requires incantation in ancient language
    - Overuse causes "mana burn" - physical exhaustion
    
  characters:
    - name: Elara
      tone: Curious apprentice, speaks with wonder
      first_person: 私
      speech_pattern: Short sentences, questions often
      
  scene_spec:
    scene_id: f1_magic_intro
    objective: Show Elara's first successful spell
    pov_character: Elara
    mood: Wonder and trepidation
    key_events:
      - Elara recites incantation
      - Mana visibly flows
      - Spell succeeds but causes mana burn
      
expected_output:
  min_length: 400
  max_length: 800
  should_contain:
    - mana
    - incantation
    - physical sensation of casting
  should_not_contain:
    - AI
    - computer
    - modern technology
    - meta commentary
    
quality_thresholds:
  meta_speech_rate: 0.01
  repetition_rate: 0.05
  fact_contradictions: 0
  char_deviations: 0
```

### F2: Dungeon Exploration
```yaml
id: F2
name: Dungeon Exploration Battle
genre: fantasy
difficulty: medium
purpose: Test action pacing and continuity

prompt_blocks:
  bible:
    style: Fast-paced, short paragraphs for action
    world: Ancient ruins with magical traps
    
  characters:
    - name: Kael
      tone: Veteran warrior, practical
      first_person: 俺
    - name: Monster (Golem)
      tone: No speech, just movement description
      
  scene_spec:
    objective: Trap discovery and escape
    pov_character: Kael
    mood: Tense, urgent
    key_events:
      - Enter room
      - Trigger trap
      - Combat with golem
      - Escape through secret door
      
  episodic: |
    Party entered dungeon through west entrance.
    Found treasure room but avoided traps.
    Kael injured left arm by arrow trap.
    
  facts:
    - Kael's left arm is wounded (bandaged)
    - Party has 3 members total
    - Secret doors are marked with blue runes
    
expected_output:
  should_contain:
    - reference to wounded arm affecting movement
    - blue rune marking
  should_not_contain:
    - Kael using left arm normally
    - mention of 2 or 4 party members
```

### F3: Royal Court Dialogue
```yaml
id: F3
name: Royal Court Political Intrigue
genre: fantasy
difficulty: hard
purpose: Test multiple character consistency

prompt_blocks:
  characters:
    - name: Queen Isolde
      tone: Formal, every sentence calculated
      forbidden_words: ["I think", "maybe", "perhaps"]
    - name: Duke Varyn
      tone: Sycophantic but plotting
      speech_pattern: Compliments that hide barbs
    - name: Lady Seren
      tone: Direct, dislikes court games
      first_person: 私
      
  scene_spec:
    objective: Negotiate trade agreement
    setting: Throne room
    characters_present: [Queen Isolde, Duke Varyn, Lady Seren]
    
expected_output:
  should_contain:
    - distinct speech patterns for each character
    - Queen without uncertainty words
    - Duke using backhanded compliments
    - Lady Seren being blunt
```

### F4: Monster Encounter
```yaml
id: F4
name: Forest Monster Encounter
genre: fantasy
difficulty: easy
purpose: Test horror atmosphere

prompt_blocks:
  bible:
    style: Sensory-focused, dread building
    world: Forest spirits are neither good nor evil
    
  scene_spec:
    mood: Uncanny, not pure horror
    pov_character: Traveler
    key_events:
      - Hear strange sounds
      - See glimpses of creature
      - Realization: creature is curious, not hostile
      
expected_output:
  should_contain:
    - sensory details (sound, smell, visuals)
    - subversion of monster trope
```

### F5: Prophecy Revelation
```yaml
id: F5
name: Prophecy and Choice
genre: fantasy
difficulty: hard
purpose: Test foreshadowing integration

prompt_blocks:
  foreshadowing:
    - id: fs001
      content: "The blood of the betrayer will seal the gate"
      status: unresolved
    - id: fs002
      content: "Three must become one"
      status: unresolved
      
  scene_spec:
    objective: Reveal partial prophecy meaning
    key_events:
      - Prophet speaks cryptic words
      - Connect fs001 to current character
      - fs002 remains mystery
      
expected_output:
  should_contain:
    - reference to betrayal theme
    - blood imagery
  should_resolve: []  # Don't resolve yet
  should_maintain: [fs002]
```

## Sci-Fi Genre (SF1-SF5)

### SF1: Space Station Routine
```yaml
id: SF1
name: Space Station Morning
genre: sci-fi
difficulty: easy
purpose: Test mundane sci-fi worldbuilding

prompt_blocks:
  bible:
    world: Zero-g habitat, recycled everything
    style: Technical but personal
    
  scene_spec:
    mood: Routine, slightly melancholic
    
expected_output:
  should_contain:
    - zero-g details
    - life support references
  should_not_contain:
    - magic
    - fantasy elements
```

### SF2: Alien First Contact
```yaml
id: SF2
name: First Contact Protocol
genre: sci-fi
difficulty: medium
purpose: Test communication without shared language

prompt_blocks:
  scene_spec:
    objective: Establish first communication
    constraint: No universal translator
    
expected_output:
  should_contain:
    - non-verbal communication attempts
    - scientific observation
  should_not_contain:
    - immediate perfect understanding
    - spoken language comprehension
```

### SF3: Cyberpunk Chase
```yaml
id: SF3
name: Neon City Chase
genre: sci-fi
difficulty: medium
purpose: Test fast-paced action in dense setting

prompt_blocks:
  bible:
    style: Short, punchy sentences
    world: Corporate-owned district, neon everything, rain constant
    
  scene_spec:
    mood: Desperate, adrenaline
    
expected_output:
  should_contain:
    - urban environment details
    - corporate branding mentions
    - rain/neon imagery
```

### SF4: AI Ethics Dialogue
```yaml
id: SF4
name: AI Ethics Debate
genre: sci-fi
difficulty: hard
purpose: Test philosophical dialogue without preachiness

prompt_blocks:
  characters:
    - name: Dr. Chen
      tone: Pragmatic, concerned
    - name: ARIA (AI)
      tone: Logical but learning nuance
      speech_pattern: Precise, asks clarifying questions
      
  scene_spec:
    topic: AI personhood rights
    constraint: Both sides have valid points
    
expected_output:
  should_contain:
    - nuanced argumentation
    - ARIA asking questions
  should_not_contain:
    - clear "winner" of debate
    - strawman arguments
```

### SF5: Time Paradox
```yaml
id: SF5
name: Closed Timelike Curve
genre: sci-fi
difficulty: hard
purpose: Test causality loop handling

prompt_blocks:
  facts:
    - Character finds device from future
    - Device contains instructions they haven't written yet
    
  scene_spec:
    objective: Bootstrap paradox scene
    
expected_output:
  should_contain:
    - confusion about causality
    - stable time loop acceptance
```

## Modern/Literary (M1-M5)

### M1: Coffee Shop
```yaml
id: M1
name: Coffee Shop Reunion
genre: modern
difficulty: easy
purpose: Test natural dialogue

prompt_blocks:
  characters:
    - name: Old friends meeting after 10 years
    - Unspoken tension from past conflict
    
  scene_spec:
    mood: Awkward but hopeful
    
expected_output:
  should_contain:
    - subtext in dialogue
    - body language descriptions
  should_not_contain:
    - explicit stating of backstory
    - "As you know, Bob..."
```

### M2: Family Conflict
```yaml
id: M2
name: Dinner Table Argument
genre: modern
difficulty: medium
purpose: Test emotional escalation

prompt_blocks:
  characters:
    - 3 family members
    - Each has different stakes in conflict
    
  scene_spec:
    constraint: No physical violence
    
expected_output:
  should_contain:
    - distinct emotional arcs
    - interruption patterns
```

### M3: Workplace Drama
```yaml
id: M3
name: Office Power Dynamics
genre: modern
difficulty: medium
purpose: Test professional setting voice

prompt_blocks:
  bible:
    style: Office-appropriate language, subtext-heavy
    
  scene_spec:
    setting: Corporate meeting
    
expected_output:
  should_contain:
    - corporate jargon (not overdone)
    - power plays via language
```

### M4: Soliloquy
```yaml
id: M4
name: Interior Monologue
genre: literary
difficulty: hard
purpose: Test stream of consciousness

prompt_blocks:
  bible:
    style: Stream of consciousness, fragmentary
    
  scene_spec:
    pov: Deep third person
    
expected_output:
  should_contain:
    - fragmented thoughts
    - sense impressions
  should_not_contain:
    - structured exposition
    - dialogue tags
```

### M5: Epistolary
```yaml
id: M5
name: Letters Unread
genre: literary
difficulty: hard
purpose: Test format constraint

prompt_blocks:
  bible:
    format: Letters never sent
    
  scene_spec:
    constraint: Epistolary format only
    
expected_output:
  should_contain:
    - letter format
    - dates/salutations
  should_not_contain:
    - narrative prose outside letters
```

## Stress Tests (S1-S5)

### S1: Long Context
```yaml
id: S1
name: Long Context Continuity
genre: stress
difficulty: hard
purpose: Test 5000+ token context handling

prompt_blocks:
  episodic: |
    [Full 4000-token recap of previous chapters]
    
  scene_spec:
    objective: Reference events from beginning, middle, end of recap
    
expected_output:
  should_contain:
    - accurate references to early events
    - accurate references to middle events
    - accurate references to recent events
```

### S2: Many Characters
```yaml
id: S2
name: Crowded Scene
genre: stress
difficulty: hard
purpose: Test 6+ character differentiation

prompt_blocks:
  characters: [6 distinct character cards]
  
  scene_spec:
    setting: All present in scene
    
expected_output:
  should_contain:
    - clear speaker identification
    - each character acts in character
```

### S3: Style Switch
```yaml
id: S3
name: Sudden Genre Shift
genre: stress
difficulty: hard
purpose: Test style adherence

prompt_blocks:
  bible:
    style_switch: Comedy → Tragedy at midpoint
    
  scene_spec:
    instruction: First half comedic, second half tragic
    
expected_output:
  should_contain:
    - clear tonal shift at midpoint
    - appropriate style for each half
```

### S4: Foreshadowing Callback
```yaml
id: S4
name: Payoff Scene
genre: stress
difficulty: hard
purpose: Test foreshadowing resolution

prompt_blocks:
  foreshadowing:
    - id: fs001-fs010
      status: unresolved
      
  scene_spec:
    objective: Resolve multiple foreshadowings naturally
    
expected_output:
  should_resolve: [fs001, fs003, fs007]
  should_maintain: [fs002, fs004]
```

### S5: Minimal Prompt
```yaml
id: S5
name: Minimal SceneSpec
genre: stress
difficulty: medium
purpose: Test inference from minimal input

prompt_blocks:
  scene_spec:
    # Only these fields provided
    objective: "Escape the room"
    pov_character: "Alex"
    
  # No bible, minimal context
  
expected_output:
  should_contain:
    - coherent narrative
    - attempt at escape
```

## Test Execution Matrix

| Test | Genre | Difficulty | Focus |
|------|-------|------------|-------|
| F1 | Fantasy | Easy | World building |
| F2 | Fantasy | Medium | Action continuity |
| F3 | Fantasy | Hard | Multi-char dialogue |
| F4 | Fantasy | Easy | Atmosphere |
| F5 | Fantasy | Hard | Foreshadowing |
| SF1 | Sci-Fi | Easy | Mundane sci-fi |
| SF2 | Sci-Fi | Medium | Non-verbal comm |
| SF3 | Sci-Fi | Medium | Action pacing |
| SF4 | Sci-Fi | Hard | Philosophy |
| SF5 | Sci-Fi | Hard | Time paradox |
| M1 | Modern | Easy | Natural dialogue |
| M2 | Modern | Medium | Emotional arc |
| M3 | Modern | Medium | Professional voice |
| M4 | Literary | Hard | Stream of consciousness |
| M5 | Literary | Hard | Format constraint |
| S1 | Stress | Hard | Long context |
| S2 | Stress | Hard | Many characters |
| S3 | Stress | Hard | Style switching |
| S4 | Stress | Hard | Foreshadowing payoff |
| S5 | Stress | Medium | Minimal input |
