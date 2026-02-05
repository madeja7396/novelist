package api

import (
	"net/http"

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
func NewHandler(swarm *agents.Swarm, logger *zerolog.Logger) *Handler {
	return &Handler{
		swarm:  swarm,
		logger: logger,
		stats:  NewStatsStore(),
	}
}

// GenerateScene handles scene generation requests
func (h *Handler) GenerateScene(c *gin.Context) {
	var req models.SceneRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{
			"error": err.Error(),
		})
		return
	}

	h.stats.RecordRequest()

	// Generate ID if not provided
	if req.ID == "" {
		req.ID = uuid.New().String()
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
		c.JSON(http.StatusInternalServerError, gin.H{
			"error": err.Error(),
		})
		return
	}

	c.JSON(http.StatusOK, resp)
}

// Health handles health check
func (h *Handler) Health(c *gin.Context) {
	c.JSON(http.StatusOK, gin.H{
		"status":  "healthy",
		"version": "2.0.0",
	})
}

// Stats handles stats request
func (h *Handler) Stats(c *gin.Context) {
	total, perMinute := h.stats.Snapshot()
	c.JSON(http.StatusOK, gin.H{
		"requests_total":      total,
		"requests_per_minute": perMinute,
	})
}
