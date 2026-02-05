package agents

import (
	"context"
	"fmt"

	"github.com/novelist/novelist/go/pkg/models"
)

// WriterInput represents input for writer
type WriterInput struct {
	SceneSpec    *models.SceneSpec
	WordCount    int
	POVCharacter string
}

// WriterAgent generates prose
type WriterAgent struct {
	*BaseAgent
}

// NewWriterAgent creates a new writer agent
func NewWriterAgent(config AgentConfig) *WriterAgent {
	return &WriterAgent{
		BaseAgent: NewBaseAgent("writer", config.Provider),
	}
}

// Execute generates prose
func (a *WriterAgent) Execute(ctx context.Context, input interface{}) (*models.GenerationResult, error) {
	in, ok := input.(*WriterInput)
	if !ok {
		return nil, fmt.Errorf("invalid input type")
	}
	
	systemPrompt := `あなたはプロの小説家です。
与えられた設計図に従って、小説の本文を書いてください。

重要な制約：
- 本文のみを出力してください
- メタ的な言及（「この物語では」「読者の皆さん」）は禁止
- 与えられた文体・世界観に厳密に従う
- キャラクターの口調・禁則事項を遵守

自然な小説の文章を出力してください。`
	
	userPrompt := a.buildPrompt(in)
	
	params := GenerateParams{
		Temperature: 0.8,
		MaxTokens:   in.WordCount * 2,
	}
	
	return a.Generate(ctx, systemPrompt, userPrompt, params)
}

func (a *WriterAgent) buildPrompt(input *WriterInput) string {
	ss := input.SceneSpec
	
	prompt := fmt.Sprintf(`## Scene Design
目的: %s
概要: %s
必須の出来事: %v
雰囲気: %s
場所: %s

## Requirements
- 視点: %s
- 目標文字数: %d文字程度

上記の設計に従って、シーンの本文を書いてください。`,
		ss.Narrative.Objective,
		ss.Narrative.Summary,
		ss.Narrative.KeyEvents,
		ss.Constraints.Mood,
		ss.Constraints.Location,
		input.POVCharacter,
		input.WordCount,
	)
	
	return prompt
}
