package api

import (
	"context"
	"errors"
	"net/http"
	"strings"
	"time"
	"unicode/utf8"

	"github.com/gin-gonic/gin"
	"github.com/google/uuid"
	"github.com/novelist/novelist/pkg/agents"
	"github.com/novelist/novelist/pkg/models"
	"github.com/rs/zerolog"
)

// Handler represents API handlers
type Handler struct {
	swarm  *agents.Swarm
	logger *zerolog.Logger
	stats  *StatsStore
}

// NewHandler creates a new handler
func NewHandler(swarm *agents.Swarm, logger *zerolog.Logger, stats *StatsStore) *Handler {
	if stats == nil {
		stats = NewStatsStore()
	}
	return &Handler{
		swarm:  swarm,
		logger: logger,
		stats:  stats,
	}
}

// GenerateScene handles scene generation requests
func (h *Handler) GenerateScene(c *gin.Context) {
	var req models.SceneRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		statusCode := http.StatusBadRequest
		errorCode := "invalid_request"
		if strings.Contains(err.Error(), "http: request body too large") {
			statusCode = http.StatusRequestEntityTooLarge
			errorCode = "payload_too_large"
		}
		c.JSON(statusCode, gin.H{
			"error": err.Error(),
			"code":  errorCode,
		})
		return
	}

	if err := validateSceneRequest(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{
			"error": err.Error(),
			"code":  "invalid_request",
		})
		return
	}

	// Generate ID if not provided
	if req.ID == "" {
		if fromCtx, ok := c.Get("request_id"); ok {
			if requestID, ok := fromCtx.(string); ok && requestID != "" {
				req.ID = requestID
			}
		}
		if req.ID == "" {
			req.ID = uuid.New().String()
		}
	}

	// Set defaults
	if req.Chapter == 0 {
		req.Chapter = 1
	}
	if req.Scene == 0 {
		req.Scene = 1
	}
	if req.WordCount == 0 {
		req.WordCount = 1000
	}

	h.logger.Info().
		Str("request_id", req.ID).
		Int("chapter", req.Chapter).
		Int("scene", req.Scene).
		Msg("Generating scene")

	// Generate
	resp, err := h.swarm.GenerateScene(c, &req)
	if err != nil {
		h.logger.Error().Err(err).Msg("Scene generation failed")

		statusCode := http.StatusInternalServerError
		errorCode := "generation_failed"
		if errors.Is(err, context.DeadlineExceeded) || errors.Is(c.Request.Context().Err(), context.DeadlineExceeded) {
			statusCode = http.StatusRequestTimeout
			errorCode = "request_timeout"
		}
		c.JSON(statusCode, gin.H{
			"error": err.Error(),
			"code":  errorCode,
		})
		return
	}

	c.JSON(http.StatusOK, resp)
}

// Health handles health check
func (h *Handler) Health(c *gin.Context) {
	ctx, cancel := context.WithTimeout(c.Request.Context(), 2*time.Second)
	defer cancel()

	dependencies := h.swarm.ProviderHealth(ctx)
	healthy := true
	for _, dep := range dependencies {
		if !dep.Healthy {
			healthy = false
			break
		}
	}

	status := "healthy"
	if !healthy {
		status = "degraded"
	}

	c.JSON(http.StatusOK, gin.H{
		"status":       status,
		"version":      "2.0.0",
		"dependencies": dependencies,
	})
}

// Ready handles readiness check.
func (h *Handler) Ready(c *gin.Context) {
	ctx, cancel := context.WithTimeout(c.Request.Context(), 2*time.Second)
	defer cancel()

	dependencies := h.swarm.ProviderHealth(ctx)
	ready := true
	for _, dep := range dependencies {
		if !dep.Healthy {
			ready = false
			break
		}
	}

	statusCode := http.StatusOK
	status := "ready"
	if !ready {
		statusCode = http.StatusServiceUnavailable
		status = "not_ready"
	}

	c.JSON(statusCode, gin.H{
		"status":       status,
		"ready":        ready,
		"dependencies": dependencies,
	})
}

// Stats handles stats request
func (h *Handler) Stats(c *gin.Context) {
	c.JSON(http.StatusOK, h.stats.Snapshot())
}

func validateSceneRequest(req *models.SceneRequest) error {
	req.Intention = strings.TrimSpace(req.Intention)
	req.POVCharacter = strings.TrimSpace(req.POVCharacter)
	req.Mood = strings.TrimSpace(req.Mood)

	if req.Intention == "" {
		return errors.New("intention is required")
	}
	if utf8.RuneCountInString(req.Intention) > 4000 {
		return errors.New("intention must be 4000 characters or less")
	}

	if req.WordCount < 0 {
		return errors.New("word_count must be positive")
	}
	if req.WordCount > 5000 {
		return errors.New("word_count must be 5000 or less")
	}

	if req.Chapter < 0 {
		return errors.New("chapter must be positive")
	}
	if req.Scene < 0 {
		return errors.New("scene must be positive")
	}

	if len(req.RequiredEvents) > 20 {
		return errors.New("required_events must be 20 items or less")
	}
	for _, event := range req.RequiredEvents {
		if utf8.RuneCountInString(strings.TrimSpace(event)) > 300 {
			return errors.New("each required_event must be 300 characters or less")
		}
	}
	return nil
}
