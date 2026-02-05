package models

import (
	"time"

	"github.com/google/uuid"
)

// SceneSpec represents the director's scene design
type SceneSpec struct {
	Scene struct {
		ID               string `json:"id"`
		Chapter          int    `json:"chapter"`
		SequenceInChapter int   `json:"sequence_in_chapter"`
		Title            string `json:"title"`
	} `json:"scene"`
	
	Narrative struct {
		Objective    string   `json:"objective"`
		Summary      string   `json:"summary"`
		KeyEvents    []string `json:"key_events"`
		Revelations  []string `json:"revelations"`
		Hooks        []string `json:"hooks"`
	} `json:"narrative"`
	
	Constraints struct {
		POVCharacter        string   `json:"pov_character"`
		Location            string   `json:"location"`
		Mood                string   `json:"mood"`
		CharactersPresent   []string `json:"characters_present"`
	} `json:"constraints"`
	
	Continuity struct {
		FactsToReinforce        []string `json:"facts_to_reinforce"`
		ForeshadowingToResolve  []string `json:"foreshadowing_to_resolve"`
		ForeshadowingToPlant    []string `json:"foreshadowing_to_plant"`
	} `json:"continuity"`
	
	Style struct {
		Pacing         string `json:"pacing"`
		DialogueRatio  string `json:"dialogue_ratio"`
	} `json:"style"`
}

// GenerationResult represents a generation result from any agent
type GenerationResult struct {
	Text             string        `json:"text"`
	PromptTokens     int           `json:"prompt_tokens"`
	CompletionTokens int           `json:"completion_tokens"`
	Model            string        `json:"model"`
	Provider         string        `json:"provider"`
	DurationMs       int64         `json:"duration_ms"`
	Timestamp        time.Time     `json:"timestamp"`
}

// NewGenerationResult creates a new generation result
func NewGenerationResult(text string) *GenerationResult {
	return &GenerationResult{
		Text:      text,
		Timestamp: time.Now(),
	}
}

// SceneRequest represents a request to generate a scene
type SceneRequest struct {
	ID              string   `json:"id" binding:"required"`
	Intention       string   `json:"intention" binding:"required"`
	Chapter         int      `json:"chapter"`
	Scene           int      `json:"scene"`
	POVCharacter    string   `json:"pov_character"`
	WordCount       int      `json:"word_count"`
	RequiredEvents  []string `json:"required_events"`
	Mood            string   `json:"mood"`
}

// NewSceneRequest creates a new scene request with defaults
func NewSceneRequest() *SceneRequest {
	return &SceneRequest{
		ID:         uuid.New().String(),
		Chapter:    1,
		Scene:      1,
		WordCount:  1000,
	}
}

// SceneResponse represents the response from scene generation
type SceneResponse struct {
	RequestID       string           `json:"request_id"`
	SceneSpec       *SceneSpec       `json:"scene_spec"`
	Text            string           `json:"text"`
	Issues          []Issue          `json:"issues,omitempty"`
	RevisionMade    bool             `json:"revision_made"`
	Stages          []StageInfo      `json:"stages"`
	TotalDurationMs int64            `json:"total_duration_ms"`
	Timestamp       time.Time        `json:"timestamp"`
}

// StageInfo represents information about a pipeline stage
type StageInfo struct {
	Agent      string `json:"agent"`
	Operation  string `json:"operation"`
	DurationMs int64  `json:"duration_ms"`
	Tokens     int    `json:"tokens,omitempty"`
}

// Issue represents a detected issue
type Issue struct {
	Category    string `json:"category"`
	Severity    string `json:"severity"`
	Description string `json:"description"`
	Location    string `json:"location,omitempty"`
	Suggestion  string `json:"suggestion,omitempty"`
}

// Character represents a character in the story
type Character struct {
	ID          string            `json:"id"`
	Name        CharacterName     `json:"name"`
	Language    CharacterLanguage `json:"language"`
	Personality CharacterPersonality `json:"personality"`
}

// CharacterName represents character naming
type CharacterName struct {
	Full    string   `json:"full"`
	Short   string   `json:"short"`
	Aliases []string `json:"aliases"`
}

// CharacterLanguage represents character speech patterns
type CharacterLanguage struct {
	FirstPerson     string   `json:"first_person"`
	Tone            string   `json:"tone"`
	SpeechPattern   string   `json:"speech_pattern"`
	ForbiddenWords  []string `json:"forbidden_words"`
}

// CharacterPersonality represents character traits
type CharacterPersonality struct {
	Values       []string `json:"values"`
	Motivations  []string `json:"motivations"`
	Fears        []string `json:"fears"`
}

// Document represents a RAG document
type Document struct {
	ID       string            `json:"id"`
	Content  string            `json:"content"`
	Source   string            `json:"source"`
	DocType  string            `json:"doc_type"`
	Metadata map[string]string `json:"metadata"`
}

// SearchResult represents a RAG search result
type SearchResult struct {
	Document Document `json:"document"`
	Score    float64  `json:"score"`
	Rank     int      `json:"rank"`
}

// ProviderConfig represents LLM provider configuration
type ProviderConfig struct {
	Type        string            `json:"type"`
	Model       string            `json:"model"`
	BaseURL     string            `json:"base_url,omitempty"`
	APIKey      string            `json:"api_key,omitempty"`
	APIKeyEnv   string            `json:"api_key_env,omitempty"`
	Timeout     int               `json:"timeout"`
	ExtraParams map[string]string `json:"extra_params,omitempty"`
}

// ProjectConfig represents project configuration
type ProjectConfig struct {
	Version   string                    `json:"version"`
	Name      string                    `json:"project_name"`
	Provider  ProviderSection           `json:"provider"`
	Context   ContextSection            `json:"context"`
	Swarm     SwarmSection              `json:"swarm"`
}

// ProviderSection represents provider configuration section
type ProviderSection struct {
	Default   string                    `json:"default"`
	Available map[string]ProviderConfig `json:"available"`
	Routing   map[string]string         `json:"routing"`
}

// ContextSection represents context configuration
type ContextSection struct {
	Budgets map[string]int `json:"budgets"`
}

// SwarmSection represents swarm configuration
type SwarmSection struct {
	MaxRevision        int    `json:"max_revision"`
	OnPersistentFailure string `json:"on_persistent_failure"`
}
