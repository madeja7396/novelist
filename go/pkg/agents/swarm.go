package agents

import (
	"context"
	"fmt"
	"time"

	"github.com/novelist/novelist/go/pkg/models"
	"github.com/rs/zerolog/log"
)

// Swarm orchestrates multiple agents
type Swarm struct {
	director  *DirectorAgent
	writer    *WriterAgent
	checker   *CheckerAgent
	editor    *EditorAgent
	committer *CommitterAgent
	
	maxRevision int
}

// NewSwarm creates a new agent swarm
func NewSwarm(configs map[string]AgentConfig) *Swarm {
	return &Swarm{
		director:    NewDirectorAgent(configs["director"]),
		writer:      NewWriterAgent(configs["writer"]),
		checker:     NewCheckerAgent(configs["checker"]),
		editor:      NewEditorAgent(configs["editor"]),
		committer:   NewCommitterAgent(configs["committer"]),
		maxRevision: 1, // Max 1 revision as per spec
	}
}

// GenerateScene runs the full pipeline
func (s *Swarm) GenerateScene(ctx context.Context, req *models.SceneRequest) (*models.SceneResponse, error) {
	start := time.Now()
	
	response := &models.SceneResponse{
		RequestID: req.ID,
		Timestamp: time.Now(),
		Stages:    []models.StageInfo{},
	}
	
	// Stage 1: Director
	log.Info().Str("stage", "director").Msg("Starting scene design")
	
	directorResult, err := s.director.Execute(ctx, req)
	if err != nil {
		return nil, fmt.Errorf("director failed: %w", err)
	}
	
	response.Stages = append(response.Stages, models.StageInfo{
		Agent:      "director",
		Operation:  "design_scene",
		DurationMs: directorResult.DurationMs,
		Tokens:     directorResult.PromptTokens + directorResult.CompletionTokens,
	})
	
	// Parse SceneSpec
	sceneSpec, err := parseSceneSpec(directorResult.Text)
	if err != nil {
		log.Warn().Err(err).Msg("Failed to parse SceneSpec, using raw")
		sceneSpec = &models.SceneSpec{}
	}
	response.SceneSpec = sceneSpec
	
	// Stage 2: Writer
	log.Info().Str("stage", "writer").Msg("Generating prose")
	
	writerInput := &WriterInput{
		SceneSpec:   sceneSpec,
		WordCount:   req.WordCount,
		POVCharacter: req.POVCharacter,
	}
	
	writerResult, err := s.writer.Execute(ctx, writerInput)
	if err != nil {
		return nil, fmt.Errorf("writer failed: %w", err)
	}
	
	response.Stages = append(response.Stages, models.StageInfo{
		Agent:      "writer",
		Operation:  "generate_prose",
		DurationMs: writerResult.DurationMs,
		Tokens:     writerResult.PromptTokens + writerResult.CompletionTokens,
	})
	
	text := writerResult.Text
	
	// Stage 3: Checker
	log.Info().Str("stage", "checker").Msg("Validating content")
	
	checkerInput := &CheckerInput{
		Text:         text,
		Chapter:      req.Chapter,
		Scene:        req.Scene,
		POVCharacter: req.POVCharacter,
	}
	
	issues, err := s.checker.Check(ctx, checkerInput)
	if err != nil {
		log.Warn().Err(err).Msg("Checker encountered error, continuing")
	}
	
	response.Issues = issues
	response.Stages = append(response.Stages, models.StageInfo{
		Agent:     "checker",
		Operation: "validate",
	})
	
	// Stage 4: Editor (if issues found and maxRevision > 0)
	if len(issues) > 0 {
		log.Info().
			Int("issues", len(issues)).
			Msg("Issues found, running editor")
		
		editorInput := &EditorInput{
			Text:   text,
			Issues: issues,
		}
		
		editorResult, err := s.editor.Execute(ctx, editorInput)
		if err != nil {
			log.Warn().Err(err).Msg("Editor failed, using original text")
		} else {
			text = editorResult.Text
			response.RevisionMade = true
			response.Stages = append(response.Stages, models.StageInfo{
				Agent:      "editor",
				Operation:  "fix_issues",
				DurationMs: editorResult.DurationMs,
			})
		}
	}
	
	response.Text = text
	
	// Stage 5: Committer (async)
	log.Info().Str("stage", "committer").Msg("Updating memory")
	
	go func() {
		committerInput := &CommitterInput{
			Text:      text,
			Chapter:   req.Chapter,
			Scene:     req.Scene,
			SceneSpec: sceneSpec,
		}
		
		if err := s.committer.Commit(context.Background(), committerInput); err != nil {
			log.Error().Err(err).Msg("Committer failed")
		}
	}()
	
	response.TotalDurationMs = time.Since(start).Milliseconds()
	
	log.Info().
		Int64("duration_ms", response.TotalDurationMs).
		Int("issues", len(issues)).
		Bool("revision", response.RevisionMade).
		Msg("Scene generation complete")
	
	return response, nil
}

func parseSceneSpec(text string) (*models.SceneSpec, error) {
	// Try to extract JSON first
	jsonStr := extractJSON(text)
	if jsonStr == "" {
		jsonStr = text
	}
	
	var spec models.SceneSpec
	if err := json.Unmarshal([]byte(jsonStr), &spec); err != nil {
		return nil, err
	}
	
	return &spec, nil
}
