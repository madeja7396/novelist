package agents

import (
	"testing"

	"github.com/novelist/novelist/go/pkg/models"
)

func TestBuildAgentConfigsFallsBackToMock(t *testing.T) {
	configs, err := BuildAgentConfigs(models.ProviderSection{})
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}

	for _, name := range defaultAgentList {
		cfg, ok := configs[name]
		if !ok {
			t.Fatalf("missing agent config for %s", name)
		}
		if cfg.Provider == nil {
			t.Fatalf("provider not set for %s", name)
		}
		if _, ok := cfg.Provider.(*MockProvider); !ok {
			t.Fatalf("expected mock provider for %s", name)
		}
	}
}

func TestBuildAgentConfigsErrorsOnMissingType(t *testing.T) {
	section := models.ProviderSection{
		Available: map[string]models.ProviderConfig{
			"broken": {},
		},
		Routing: map[string]string{
			"director": "broken",
		},
	}

	_, err := BuildAgentConfigs(section)
	if err == nil {
		t.Fatal("expected error for missing provider type")
	}
}
