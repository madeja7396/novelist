package api

import (
	"context"
	"net/http"
	"strconv"
	"sync"
	"time"

	"github.com/gin-gonic/gin"
	"github.com/google/uuid"
)

// RequestIDMiddleware ensures each request has an ID.
func RequestIDMiddleware() gin.HandlerFunc {
	return func(c *gin.Context) {
		requestID := c.GetHeader("X-Request-ID")
		if requestID == "" {
			requestID = uuid.NewString()
		}
		c.Set("request_id", requestID)
		c.Writer.Header().Set("X-Request-ID", requestID)
		c.Next()
	}
}

// StatsMiddleware records request metrics.
func StatsMiddleware(stats *StatsStore) gin.HandlerFunc {
	return func(c *gin.Context) {
		if stats == nil {
			c.Next()
			return
		}
		start := time.Now()
		stats.BeginRequest()
		c.Next()
		stats.EndRequest(c.Writer.Status(), time.Since(start))
	}
}

// BodyLimitMiddleware caps request payload size in bytes.
func BodyLimitMiddleware(maxBytes int64) gin.HandlerFunc {
	return func(c *gin.Context) {
		if maxBytes > 0 {
			c.Request.Body = http.MaxBytesReader(c.Writer, c.Request.Body, maxBytes)
		}
		c.Next()
	}
}

// TimeoutMiddleware attaches deadline to request context.
func TimeoutMiddleware(timeout time.Duration) gin.HandlerFunc {
	return func(c *gin.Context) {
		if timeout <= 0 {
			c.Next()
			return
		}

		ctx, cancel := context.WithTimeout(c.Request.Context(), timeout)
		defer cancel()
		c.Request = c.Request.WithContext(ctx)
		c.Next()

		if ctx.Err() == context.DeadlineExceeded && !c.Writer.Written() {
			c.AbortWithStatusJSON(http.StatusRequestTimeout, gin.H{
				"error": "request timeout",
				"code":  "request_timeout",
			})
		}
	}
}

// ConcurrencyLimiter bounds in-flight generation requests.
type ConcurrencyLimiter struct {
	sem chan struct{}
}

// NewConcurrencyLimiter creates a limiter with max slots.
func NewConcurrencyLimiter(maxInFlight int) *ConcurrencyLimiter {
	if maxInFlight <= 0 {
		maxInFlight = 8
	}
	return &ConcurrencyLimiter{
		sem: make(chan struct{}, maxInFlight),
	}
}

// Middleware returns gin middleware for concurrency limiting.
func (l *ConcurrencyLimiter) Middleware() gin.HandlerFunc {
	return func(c *gin.Context) {
		select {
		case l.sem <- struct{}{}:
			defer func() { <-l.sem }()
			c.Next()
		default:
			c.AbortWithStatusJSON(http.StatusTooManyRequests, gin.H{
				"error": "too many in-flight requests",
				"code":  "too_many_requests",
			})
		}
	}
}

type rateWindow struct {
	count   int
	resetAt time.Time
}

// IPRateLimiter applies a fixed-window limit by client IP.
type IPRateLimiter struct {
	mu      sync.Mutex
	limit   int
	window  time.Duration
	clients map[string]rateWindow
}

// NewIPRateLimiter creates a new per-IP limiter.
func NewIPRateLimiter(limit int, window time.Duration) *IPRateLimiter {
	if limit <= 0 {
		limit = 30
	}
	if window <= 0 {
		window = time.Minute
	}
	return &IPRateLimiter{
		limit:   limit,
		window:  window,
		clients: make(map[string]rateWindow),
	}
}

// Middleware returns gin middleware for per-IP rate limiting.
func (l *IPRateLimiter) Middleware() gin.HandlerFunc {
	return func(c *gin.Context) {
		allowed, remaining, resetUnix := l.Allow(c.ClientIP(), time.Now())
		c.Writer.Header().Set("X-RateLimit-Limit", strconv.Itoa(l.limit))
		c.Writer.Header().Set("X-RateLimit-Remaining", strconv.Itoa(remaining))
		c.Writer.Header().Set("X-RateLimit-Reset", strconv.FormatInt(resetUnix, 10))

		if !allowed {
			c.AbortWithStatusJSON(http.StatusTooManyRequests, gin.H{
				"error": "rate limit exceeded",
				"code":  "rate_limit_exceeded",
			})
			return
		}
		c.Next()
	}
}

// Allow records one request and returns current allowance.
func (l *IPRateLimiter) Allow(clientIP string, now time.Time) (allowed bool, remaining int, resetUnix int64) {
	l.mu.Lock()
	defer l.mu.Unlock()

	state, ok := l.clients[clientIP]
	if !ok || now.After(state.resetAt) {
		state = rateWindow{
			count:   0,
			resetAt: now.Add(l.window),
		}
	}

	if state.count >= l.limit {
		l.clients[clientIP] = state
		return false, 0, state.resetAt.Unix()
	}

	state.count++
	l.clients[clientIP] = state

	remaining = l.limit - state.count
	if remaining < 0 {
		remaining = 0
	}
	return true, remaining, state.resetAt.Unix()
}
