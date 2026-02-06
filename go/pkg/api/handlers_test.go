package api

import (
	"strings"
	"testing"

	"github.com/novelist/novelist/pkg/models"
)

func TestValidateSceneRequest(t *testing.T) {
	valid := &models.SceneRequest{
		Intention: "Hero discovers hidden magic.",
		WordCount: 1200,
	}
	if err := validateSceneRequest(valid); err != nil {
		t.Fatalf("expected valid request, got error: %v", err)
	}

	tooLong := &models.SceneRequest{
		Intention: strings.Repeat("x", 4001),
	}
	if err := validateSceneRequest(tooLong); err == nil {
		t.Fatal("expected error for overly long intention")
	}

	tooManyEvents := &models.SceneRequest{
		Intention:      "test",
		RequiredEvents: make([]string, 21),
	}
	if err := validateSceneRequest(tooManyEvents); err == nil {
		t.Fatal("expected error for too many required events")
	}
}
