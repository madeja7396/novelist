package main

import (
	"context"
	"net/http"
	"os"
	"os/signal"
	"strconv"
	"syscall"
	"time"

	"github.com/rs/zerolog"
)

func main() {
	zerolog.TimeFieldFormat = zerolog.TimeFormatUnix
	logger := zerolog.New(os.Stdout).With().Timestamp().Logger()

	apiURL := env("NOVELIST_API_URL", "http://localhost:8080")
	heartbeatSec := envInt("NOVELIST_AGENT_HEARTBEAT_SEC", 30)
	interval := time.Duration(heartbeatSec) * time.Second

	client := &http.Client{Timeout: 5 * time.Second}
	ticker := time.NewTicker(interval)
	defer ticker.Stop()

	logger.Info().
		Str("api_url", apiURL).
		Dur("heartbeat_interval", interval).
		Msg("Agent worker started")

	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()

	go func() {
		for {
			select {
			case <-ctx.Done():
				return
			case <-ticker.C:
				req, err := http.NewRequestWithContext(ctx, http.MethodGet, apiURL+"/api/v1/health", nil)
				if err != nil {
					logger.Warn().Err(err).Msg("failed to build health request")
					continue
				}

				resp, err := client.Do(req)
				if err != nil {
					logger.Warn().Err(err).Msg("api health probe failed")
					continue
				}
				_ = resp.Body.Close()

				if resp.StatusCode >= 400 {
					logger.Warn().Int("status", resp.StatusCode).Msg("api unhealthy")
					continue
				}

				logger.Debug().Int("status", resp.StatusCode).Msg("api healthy")
			}
		}
	}()

	quit := make(chan os.Signal, 1)
	signal.Notify(quit, syscall.SIGINT, syscall.SIGTERM)
	<-quit

	logger.Info().Msg("Agent worker shutting down")
	cancel()
}

func env(key, fallback string) string {
	value := os.Getenv(key)
	if value == "" {
		return fallback
	}
	return value
}

func envInt(key string, fallback int) int {
	value := os.Getenv(key)
	if value == "" {
		return fallback
	}
	parsed, err := strconv.Atoi(value)
	if err != nil {
		return fallback
	}
	return parsed
}
