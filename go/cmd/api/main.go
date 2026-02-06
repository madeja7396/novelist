package main

import (
	"context"
	"net/http"
	"os"
	"os/signal"
	"strconv"
	"syscall"
	"time"

	"github.com/gin-gonic/gin"
	"github.com/novelist/novelist/pkg/agents"
	"github.com/novelist/novelist/pkg/api"
	"github.com/novelist/novelist/pkg/config"
	"github.com/rs/zerolog"
)

func main() {
	// Setup logger
	zerolog.TimeFieldFormat = zerolog.TimeFormatUnix
	logger := zerolog.New(os.Stdout).With().Timestamp().Logger()

	// Load config
	cfg, err := config.Load("")
	if err != nil {
		logger.Fatal().Err(err).Msg("Failed to load config")
	}

	// Setup Gin
	gin.SetMode(gin.ReleaseMode)
	r := gin.New()
	if err := r.SetTrustedProxies(nil); err != nil {
		logger.Warn().Err(err).Msg("Failed to set trusted proxies")
	}

	// Setup swarm
	agentConfigs, err := agents.BuildAgentConfigs(cfg.Provider)
	if err != nil {
		logger.Fatal().Err(err).Msg("Failed to initialize providers")
	}
	swarm := agents.NewSwarm(agentConfigs)

	// Runtime limits
	maxRequestBytes := int64(envInt("NOVELIST_MAX_REQUEST_BYTES", 64*1024))
	requestTimeout := time.Duration(envInt("NOVELIST_REQUEST_TIMEOUT_SEC", 90)) * time.Second
	maxConcurrent := envInt("NOVELIST_MAX_CONCURRENT_REQUESTS", 8)
	rateLimitPerMinute := envInt("NOVELIST_RATE_LIMIT_PER_MIN", 30)

	statsStore := api.NewStatsStore()

	r.Use(gin.Recovery())
	r.Use(api.RequestIDMiddleware())
	r.Use(api.StatsMiddleware(statsStore))
	r.Use(loggerMiddleware(&logger))

	rateLimiter := api.NewIPRateLimiter(rateLimitPerMinute, time.Minute)
	concurrencyLimiter := api.NewConcurrencyLimiter(maxConcurrent)

	// Setup handlers
	handler := api.NewHandler(swarm, &logger, statsStore)

	// Routes
	apiGroup := r.Group("/api/v1")
	{
		apiGroup.POST(
			"/scenes",
			api.BodyLimitMiddleware(maxRequestBytes),
			rateLimiter.Middleware(),
			concurrencyLimiter.Middleware(),
			api.TimeoutMiddleware(requestTimeout),
			handler.GenerateScene,
		)
		apiGroup.GET("/health", handler.Health)
		apiGroup.GET("/ready", handler.Ready)
		apiGroup.GET("/stats", handler.Stats)
	}

	// Create server
	srv := &http.Server{
		Addr:    cfg.Server.Host + ":" + cfg.Server.HTTPPort,
		Handler: r,
	}

	// Graceful shutdown
	go func() {
		if err := srv.ListenAndServe(); err != nil && err != http.ErrServerClosed {
			logger.Fatal().Err(err).Msg("Failed to start server")
		}
	}()

	logger.Info().
		Str("host", cfg.Server.Host).
		Str("port", cfg.Server.HTTPPort).
		Int("rate_limit_per_min", rateLimitPerMinute).
		Int("max_concurrent_requests", maxConcurrent).
		Int64("max_request_bytes", maxRequestBytes).
		Dur("request_timeout", requestTimeout).
		Msg("Server started")

	// Wait for interrupt
	quit := make(chan os.Signal, 1)
	signal.Notify(quit, syscall.SIGINT, syscall.SIGTERM)
	<-quit

	logger.Info().Msg("Shutting down server...")

	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()

	if err := srv.Shutdown(ctx); err != nil {
		logger.Fatal().Err(err).Msg("Server forced to shutdown")
	}

	logger.Info().Msg("Server exited")
}

func loggerMiddleware(logger *zerolog.Logger) gin.HandlerFunc {
	return func(c *gin.Context) {
		start := time.Now()
		path := c.Request.URL.Path
		raw := c.Request.URL.RawQuery

		c.Next()

		latency := time.Since(start)
		clientIP := c.ClientIP()
		method := c.Request.Method
		statusCode := c.Writer.Status()
		userAgent := c.Request.UserAgent()
		requestID := c.GetHeader("X-Request-ID")
		if requestID == "" {
			if fromCtx, ok := c.Get("request_id"); ok {
				if v, ok := fromCtx.(string); ok {
					requestID = v
				}
			}
		}

		if raw != "" {
			path = path + "?" + raw
		}

		logger.Info().
			Str("request_id", requestID).
			Str("client_ip", clientIP).
			Str("user_agent", userAgent).
			Str("method", method).
			Str("path", path).
			Int("status", statusCode).
			Dur("latency", latency).
			Msg("Request")
	}
}

func envInt(key string, fallback int) int {
	raw := os.Getenv(key)
	if raw == "" {
		return fallback
	}
	parsed, err := strconv.Atoi(raw)
	if err != nil {
		return fallback
	}
	return parsed
}
