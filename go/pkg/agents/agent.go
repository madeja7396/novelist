package agents

import (
	"context"
	"fmt"
	"time"

	"github.com/novelist/novelist/pkg/models"
	"github.com/rs/zerolog/log"
)

// Agent is the interface for all agents
type Agent interface {
	Name() string
	Execute(ctx context.Context, input interface{}) (*models.GenerationResult, error)
}

// BaseAgent provides common functionality
type BaseAgent struct {
	name     string
	provider Provider
}

// Name returns the agent name
func (a *BaseAgent) Name() string {
	return a.name
}

// Provider interface for LLM providers
type Provider interface {
	Generate(ctx context.Context, messages []Message, params GenerateParams) (*models.GenerationResult, error)
	Capabilities() ProviderCapabilities
	HealthCheck(ctx context.Context) error
	Name() string
}

// Message represents a chat message
type Message struct {
	Role    string `json:"role"`
	Content string `json:"content"`
}

// GenerateParams represents generation parameters
type GenerateParams struct {
	Temperature float64 `json:"temperature"`
	MaxTokens   int     `json:"max_tokens"`
	TopP        float64 `json:"top_p"`
	JSONMode    bool    `json:"json_mode"`
}

// ProviderCapabilities represents provider capabilities
type ProviderCapabilities struct {
	CtxLen            int  `json:"ctx_len"`
	SupportsTools     bool `json:"supports_tools"`
	SupportsJSONMode  bool `json:"supports_json_mode"`
	SupportsThinking  bool `json:"supports_thinking_mode"`
	SupportsStreaming bool `json:"supports_streaming"`
}

// Generate executes generation with the provider
func (a *BaseAgent) Generate(ctx context.Context, systemPrompt, userPrompt string, params GenerateParams) (*models.GenerationResult, error) {
	start := time.Now()

	messages := []Message{
		{Role: "system", Content: systemPrompt},
		{Role: "user", Content: userPrompt},
	}

	result, err := a.provider.Generate(ctx, messages, params)
	if err != nil {
		log.Error().
			Str("agent", a.name).
			Err(err).
			Msg("Generation failed")
		return nil, fmt.Errorf("%s generation failed: %w", a.name, err)
	}

	result.DurationMs = time.Since(start).Milliseconds()

	log.Debug().
		Str("agent", a.name).
		Int64("duration_ms", result.DurationMs).
		Int("tokens", result.PromptTokens+result.CompletionTokens).
		Msg("Generation complete")

	return result, nil
}

// HealthCheck checks provider reachability.
func (a *BaseAgent) HealthCheck(ctx context.Context) error {
	if a.provider == nil {
		return fmt.Errorf("%s provider is not configured", a.name)
	}
	return a.provider.HealthCheck(ctx)
}

// ProviderName returns underlying provider name.
func (a *BaseAgent) ProviderName() string {
	if a.provider == nil {
		return "unknown"
	}
	return a.provider.Name()
}

// AgentConfig represents agent configuration
type AgentConfig struct {
	Provider    Provider
	Temperature float64
	MaxTokens   int
}

// NewBaseAgent creates a new base agent
func NewBaseAgent(name string, provider Provider) *BaseAgent {
	return &BaseAgent{
		name:     name,
		provider: provider,
	}
}
