package api

import (
	"testing"
	"time"
)

func TestStatsStoreSnapshot(t *testing.T) {
	stats := NewStatsStore()
	stats.BeginRequest()
	stats.EndRequest(200, 10*time.Millisecond)
	stats.BeginRequest()
	stats.EndRequest(429, 30*time.Millisecond)

	snapshot := stats.Snapshot()
	if snapshot.RequestsTotal != 2 {
		t.Fatalf("expected total 2, got %d", snapshot.RequestsTotal)
	}
	if snapshot.RequestsPerMinute <= 0 {
		t.Fatalf("expected perMinute > 0, got %f", snapshot.RequestsPerMinute)
	}
	if snapshot.StatusCounts[200] != 1 {
		t.Fatalf("expected 200 count 1, got %d", snapshot.StatusCounts[200])
	}
	if snapshot.StatusCounts[429] != 1 {
		t.Fatalf("expected 429 count 1, got %d", snapshot.StatusCounts[429])
	}
	if snapshot.LatencyMsP95 <= 0 {
		t.Fatalf("expected latency p95 > 0, got %f", snapshot.LatencyMsP95)
	}
}
