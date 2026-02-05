package models

import "time"

// ProviderSection represents provider configuration.
type ProviderSection struct {
	Default   string                    `mapstructure:"default" json:"default" yaml:"default"`
	Available map[string]ProviderConfig `mapstructure:"available" json:"available" yaml:"available"`
	Routing   map[string]string         `mapstructure:"routing" json:"routing" yaml:"routing"`
}

// ProviderConfig represents a single provider definition.
type ProviderConfig struct {
	Type      string `mapstructure:"type" json:"type" yaml:"type"`
	Model     string `mapstructure:"model" json:"model" yaml:"model"`
	BaseURL   string `mapstructure:"base_url" json:"base_url" yaml:"base_url"`
	APIKeyEnv string `mapstructure:"api_key_env" json:"api_key_env" yaml:"api_key_env"`
	Timeout   int    `mapstructure:"timeout" json:"timeout" yaml:"timeout"`
}

// ProjectConfig represents project-level configuration.
type ProjectConfig struct {
	Provider ProviderSection `mapstructure:"provider" json:"provider" yaml:"provider"`
}

// SceneRequest represents API request for scene generation.
type SceneRequest struct {
	ID             string   `json:"id"`
	Intention      string   `json:"intention"`
	Chapter        int      `json:"chapter"`
	Scene          int      `json:"scene"`
	WordCount      int      `json:"word_count"`
	POVCharacter   string   `json:"pov_character"`
	Mood           string   `json:"mood"`
	RequiredEvents []string `json:"required_events"`
}

// SceneResponse represents response for scene generation.
type SceneResponse struct {
	RequestID       string      `json:"request_id"`
	Timestamp       time.Time   `json:"timestamp"`
	Stages          []StageInfo `json:"stages"`
	SceneSpec       *SceneSpec  `json:"scenespec,omitempty"`
	Issues          []Issue     `json:"issues,omitempty"`
	RevisionMade    bool        `json:"revision_made"`
	Text            string      `json:"text"`
	TotalDurationMs int64       `json:"total_duration_ms"`
}

// StageInfo represents a pipeline stage result.
type StageInfo struct {
	Agent      string `json:"agent"`
	Operation  string `json:"operation"`
	DurationMs int64  `json:"duration_ms,omitempty"`
	Tokens     int    `json:"tokens,omitempty"`
}

// Issue represents a checker finding.
type Issue struct {
	Category    string `json:"category"`
	Severity    string `json:"severity"`
	Description string `json:"description"`
}

// GenerationResult represents LLM generation output.
type GenerationResult struct {
	Text             string `json:"text"`
	PromptTokens     int    `json:"prompt_tokens"`
	CompletionTokens int    `json:"completion_tokens"`
	DurationMs       int64  `json:"duration_ms"`
}

// SceneSpec represents a structured scene design.
type SceneSpec struct {
	Scene       SceneSpecScene       `json:"scene"`
	Narrative   SceneSpecNarrative   `json:"narrative"`
	Constraints SceneSpecConstraints `json:"constraints"`
	Continuity  SceneSpecContinuity  `json:"continuity"`
}

// SceneSpecScene describes the scene metadata.
type SceneSpecScene struct {
	ID                string `json:"id"`
	Chapter           int    `json:"chapter"`
	SequenceInChapter int    `json:"sequence_in_chapter"`
	Title             string `json:"title"`
}

// SceneSpecNarrative describes narrative requirements.
type SceneSpecNarrative struct {
	Objective   string   `json:"objective"`
	Summary     string   `json:"summary"`
	KeyEvents   []string `json:"key_events"`
	Revelations []string `json:"revelations"`
	Hooks       []string `json:"hooks"`
}

// SceneSpecConstraints describes constraints for the scene.
type SceneSpecConstraints struct {
	POVCharacter string `json:"pov_character"`
	Location     string `json:"location"`
	Mood         string `json:"mood"`
}

// SceneSpecContinuity describes continuity requirements.
type SceneSpecContinuity struct {
	FactsToReinforce       []string `json:"facts_to_reinforce"`
	ForeshadowingToResolve []string `json:"foreshadowing_to_resolve"`
	ForeshadowingToPlant   []string `json:"foreshadowing_to_plant"`
}
