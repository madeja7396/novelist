package agents

import (
	"context"
	"fmt"
	"math/rand"
	"os"
	"strings"
	"sync"
	"time"

	"github.com/novelist/novelist/go/pkg/models"
)

// ProviderRegistry stores provider factories by type.
var ProviderRegistry = struct {
	sync.RWMutex
	factories map[string]ProviderFactory
}{
	factories: make(map[string]ProviderFactory),
}

// ProviderFactory builds providers from config.
type ProviderFactory func(config models.ProviderConfig) (Provider, error)

// RegisterProviderFactory registers a provider factory for a provider type.
func RegisterProviderFactory(providerType string, factory ProviderFactory) {
	ProviderRegistry.Lock()
	defer ProviderRegistry.Unlock()
	ProviderRegistry.factories[strings.ToLower(providerType)] = factory
}

// CreateProvider creates a provider from config.
func CreateProvider(config models.ProviderConfig) (Provider, error) {
	ProviderRegistry.RLock()
	factory, ok := ProviderRegistry.factories[strings.ToLower(config.Type)]
	ProviderRegistry.RUnlock()
	if !ok {
		return nil, fmt.Errorf("provider type not registered: %s", config.Type)
	}
	return factory(config)
}

func init() {
	RegisterProviderFactory("mock", NewMockProvider)
}

// MockProvider is a deterministic provider for tests and fallback usage.
type MockProvider struct {
	rand *rand.Rand
}

// NewMockProvider creates a mock provider.
func NewMockProvider(config models.ProviderConfig) (Provider, error) {
	seed := time.Now().UnixNano()
	if envSeed := os.Getenv("NOVELIST_MOCK_SEED"); envSeed != "" {
		if parsed, err := time.Parse(time.RFC3339Nano, envSeed); err == nil {
			seed = parsed.UnixNano()
		}
	}
	return &MockProvider{rand: rand.New(rand.NewSource(seed))}, nil
}

// Generate returns a canned response based on params.
func (p *MockProvider) Generate(ctx context.Context, messages []Message, params GenerateParams) (*models.GenerationResult, error) {
	select {
	case <-ctx.Done():
		return nil, ctx.Err()
	default:
	}

	text := "Mock response."
	if params.JSONMode {
		text = `{"scene":{"id":"mock","chapter":1,"sequence_in_chapter":1,"title":"Mock Scene"},` +
			`"narrative":{"objective":"Mock objective","summary":"Mock summary","key_events":[],"revelations":[],"hooks":[]},` +
			`"constraints":{"pov_character":"", "location":"", "mood":""},` +
			`"continuity":{"facts_to_reinforce":[],"foreshadowing_to_resolve":[],"foreshadowing_to_plant":[]}}`
	}

	return &models.GenerationResult{
		Text:             text,
		PromptTokens:     50 + p.rand.Intn(25),
		CompletionTokens: 100 + p.rand.Intn(50),
	}, nil
}

// Capabilities returns mock provider capabilities.
func (p *MockProvider) Capabilities() ProviderCapabilities {
	return ProviderCapabilities{
		CtxLen:            8192,
		SupportsTools:     false,
		SupportsJSONMode:  true,
		SupportsThinking:  false,
		SupportsStreaming: false,
	}
}
