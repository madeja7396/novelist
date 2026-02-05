package main

import (
	"context"
	"log"
	"net/http"
	"os"
	"os/signal"
	"syscall"
	"time"

	"github.com/gin-gonic/gin"
	"github.com/novelist/novelist/go/pkg/agents"
	"github.com/novelist/novelist/go/pkg/api"
	"github.com/novelist/novelist/go/pkg/config"
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
	r.Use(gin.Recovery())
	r.Use(loggerMiddleware(&logger))

	// Setup swarm
	agentConfigs, err := agents.BuildAgentConfigs(cfg.Provider)
	if err != nil {
		logger.Fatal().Err(err).Msg("Failed to initialize providers")
	}
	swarm := agents.NewSwarm(agentConfigs)

	// Setup handlers
	handler := api.NewHandler(swarm, &logger)

	// Routes
	api := r.Group("/api/v1")
	{
		api.POST("/scenes", handler.GenerateScene)
		api.GET("/health", handler.Health)
		api.GET("/stats", handler.Stats)
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

		if raw != "" {
			path = path + "?" + raw
		}

		logger.Info().
			Str("client_ip", clientIP).
			Str("method", method).
			Str("path", path).
			Int("status", statusCode).
			Dur("latency", latency).
			Msg("Request")
	}
}
