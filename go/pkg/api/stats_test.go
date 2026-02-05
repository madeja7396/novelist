package api

import "testing"

func TestStatsStoreSnapshot(t *testing.T) {
	stats := NewStatsStore()
	stats.RecordRequest()
	stats.RecordRequest()

	total, perMinute := stats.Snapshot()
	if total != 2 {
		t.Fatalf("expected total 2, got %d", total)
	}
	if perMinute <= 0 {
		t.Fatalf("expected perMinute > 0, got %f", perMinute)
	}
}
