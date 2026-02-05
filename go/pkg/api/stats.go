package api

import (
	"sync"
	"time"
)

// StatsStore tracks basic request statistics.
type StatsStore struct {
	mu         sync.Mutex
	startedAt  time.Time
	totalCount int64
}

// NewStatsStore creates a new StatsStore.
func NewStatsStore() *StatsStore {
	return &StatsStore{
		startedAt: time.Now(),
	}
}

// RecordRequest increments request counters.
func (s *StatsStore) RecordRequest() {
	s.mu.Lock()
	defer s.mu.Unlock()
	s.totalCount++
}

// Snapshot returns current stats snapshot.
func (s *StatsStore) Snapshot() (total int64, perMinute float64) {
	s.mu.Lock()
	defer s.mu.Unlock()
	elapsed := time.Since(s.startedAt).Minutes()
	if elapsed <= 0 {
		return s.totalCount, 0
	}
	return s.totalCount, float64(s.totalCount) / elapsed
}
