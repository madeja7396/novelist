package config

import (
	"fmt"
	"os"
	"path/filepath"

	"github.com/novelist/novelist/go/pkg/models"
	"github.com/spf13/viper"
)

// Config represents application configuration
type Config struct {
	Server   ServerConfig            `mapstructure:"server"`
	Project  string                  `mapstructure:"project"`
	Provider models.ProviderSection  `mapstructure:"provider"`
}

// ServerConfig represents server configuration
type ServerConfig struct {
	HTTPPort string `mapstructure:"http_port"`
	GRPCPort string `mapstructure:"grpc_port"`
	Host     string `mapstructure:"host"`
}

// Load loads configuration from file
func Load(configPath string) (*Config, error) {
	v := viper.New()
	
	// Set defaults
	v.SetDefault("server.http_port", "8080")
	v.SetDefault("server.grpc_port", "50051")
	v.SetDefault("server.host", "0.0.0.0")
	
	// Read from file if provided
	if configPath != "" {
		v.SetConfigFile(configPath)
		if err := v.ReadInConfig(); err != nil {
			return nil, fmt.Errorf("failed to read config: %w", err)
		}
	}
	
	// Environment variables
	v.AutomaticEnv()
	v.SetEnvPrefix("NOVELIST")
	
	var cfg Config
	if err := v.Unmarshal(&cfg); err != nil {
		return nil, fmt.Errorf("failed to unmarshal config: %w", err)
	}
	
	return &cfg, nil
}

// LoadProjectConfig loads project-specific config
func LoadProjectConfig(projectPath string) (*models.ProjectConfig, error) {
	configFile := filepath.Join(projectPath, "config.yaml")
	
	data, err := os.ReadFile(configFile)
	if err != nil {
		return nil, fmt.Errorf("failed to read project config: %w", err)
	}
	
	v := viper.New()
	v.SetConfigType("yaml")
	
	if err := v.ReadConfig(data); err != nil {
		return nil, fmt.Errorf("failed to parse config: %w", err)
	}
	
	var cfg models.ProjectConfig
	if err := v.Unmarshal(&cfg); err != nil {
		return nil, fmt.Errorf("failed to unmarshal: %w", err)
	}
	
	return &cfg, nil
}
