package agents

import (
	"fmt"

	"github.com/novelist/novelist/pkg/models"
)

var defaultAgentList = []string{
	"director",
	"writer",
	"checker",
	"editor",
	"committer",
}

// BuildAgentConfigs builds agent configs from provider configuration.
func BuildAgentConfigs(provider models.ProviderSection) (map[string]AgentConfig, error) {
	configs := make(map[string]AgentConfig)
	defaultProvider := provider.Default

	for _, agentName := range defaultAgentList {
		providerName := provider.Routing[agentName]
		if providerName == "" {
			providerName = defaultProvider
		}

		providerConfig, ok := provider.Available[providerName]
		if !ok || providerName == "" {
			providerConfig = models.ProviderConfig{Type: "mock"}
		}

		if providerConfig.Type == "" {
			return nil, fmt.Errorf("provider type missing for %s", providerName)
		}

		providerInstance, err := CreateProvider(providerConfig)
		if err != nil {
			return nil, err
		}

		configs[agentName] = AgentConfig{
			Provider: providerInstance,
		}
	}

	return configs, nil
}
