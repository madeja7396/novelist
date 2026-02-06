package api

import (
	"testing"
	"time"
)

func TestIPRateLimiterAllow(t *testing.T) {
	limiter := NewIPRateLimiter(2, time.Minute)
	now := time.Unix(1000, 0)

	allowed, remaining, _ := limiter.Allow("127.0.0.1", now)
	if !allowed || remaining != 1 {
		t.Fatalf("expected first request allowed with remaining 1, got allowed=%v remaining=%d", allowed, remaining)
	}

	allowed, remaining, _ = limiter.Allow("127.0.0.1", now.Add(10*time.Second))
	if !allowed || remaining != 0 {
		t.Fatalf("expected second request allowed with remaining 0, got allowed=%v remaining=%d", allowed, remaining)
	}

	allowed, remaining, _ = limiter.Allow("127.0.0.1", now.Add(20*time.Second))
	if allowed || remaining != 0 {
		t.Fatalf("expected third request denied with remaining 0, got allowed=%v remaining=%d", allowed, remaining)
	}

	allowed, remaining, _ = limiter.Allow("127.0.0.1", now.Add(61*time.Second))
	if !allowed || remaining != 1 {
		t.Fatalf("expected request after reset to be allowed with remaining 1, got allowed=%v remaining=%d", allowed, remaining)
	}
}
