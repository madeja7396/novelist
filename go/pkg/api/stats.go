package api

import (
	"sort"
	"sync"
	"time"
)

// StatsStore tracks basic request statistics.
type StatsStore struct {
	mu           sync.Mutex
	startedAt    time.Time
	totalCount   int64
	inFlight     int64
	statusCounts map[int]int64
	latencies    []time.Duration
	latencyCap   int
}

// StatsSnapshot contains immutable stats values for API responses.
type StatsSnapshot struct {
	StartedAt         time.Time     `json:"started_at"`
	RequestsTotal     int64         `json:"requests_total"`
	RequestsPerMinute float64       `json:"requests_per_minute"`
	InFlight          int64         `json:"in_flight"`
	StatusCounts      map[int]int64 `json:"status_counts"`
	LatencyMsP50      float64       `json:"latency_ms_p50"`
	LatencyMsP95      float64       `json:"latency_ms_p95"`
}

// NewStatsStore creates a new StatsStore.
func NewStatsStore() *StatsStore {
	return &StatsStore{
		startedAt:    time.Now(),
		statusCounts: make(map[int]int64),
		latencyCap:   4096,
	}
}

// BeginRequest marks request start.
func (s *StatsStore) BeginRequest() {
	s.mu.Lock()
	defer s.mu.Unlock()
	s.inFlight++
}

// EndRequest records request completion.
func (s *StatsStore) EndRequest(statusCode int, latency time.Duration) {
	s.mu.Lock()
	defer s.mu.Unlock()
	if s.inFlight > 0 {
		s.inFlight--
	}
	s.totalCount++
	s.statusCounts[statusCode]++

	if latency < 0 {
		latency = 0
	}
	if len(s.latencies) >= s.latencyCap {
		copy(s.latencies, s.latencies[1:])
		s.latencies[len(s.latencies)-1] = latency
	} else {
		s.latencies = append(s.latencies, latency)
	}
}

// Snapshot returns current stats snapshot.
func (s *StatsStore) Snapshot() StatsSnapshot {
	s.mu.Lock()
	defer s.mu.Unlock()

	elapsed := time.Since(s.startedAt).Minutes()
	perMinute := 0.0
	if elapsed > 0 {
		perMinute = float64(s.totalCount) / elapsed
	}

	status := make(map[int]int64, len(s.statusCounts))
	for code, count := range s.statusCounts {
		status[code] = count
	}

	return StatsSnapshot{
		StartedAt:         s.startedAt,
		RequestsTotal:     s.totalCount,
		RequestsPerMinute: perMinute,
		InFlight:          s.inFlight,
		StatusCounts:      status,
		LatencyMsP50:      durationPercentileMs(s.latencies, 0.50),
		LatencyMsP95:      durationPercentileMs(s.latencies, 0.95),
	}
}

func durationPercentileMs(values []time.Duration, percentile float64) float64 {
	if len(values) == 0 {
		return 0
	}
	if percentile < 0 {
		percentile = 0
	}
	if percentile > 1 {
		percentile = 1
	}

	tmp := make([]time.Duration, len(values))
	copy(tmp, values)
	sort.Slice(tmp, func(i, j int) bool {
		return tmp[i] < tmp[j]
	})

	index := int(float64(len(tmp)-1) * percentile)
	return float64(tmp[index].Milliseconds())
}
