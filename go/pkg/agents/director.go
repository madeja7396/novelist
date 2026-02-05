package agents

import (
	"context"
	"encoding/json"
	"fmt"

	"github.com/novelist/novelist/go/pkg/models"
)

// DirectorAgent creates SceneSpec from user intention
type DirectorAgent struct {
	*BaseAgent
}

// NewDirectorAgent creates a new director agent
func NewDirectorAgent(config AgentConfig) *DirectorAgent {
	return &DirectorAgent{
		BaseAgent: NewBaseAgent("director", config.Provider),
	}
}

// Execute generates SceneSpec
func (a *DirectorAgent) Execute(ctx context.Context, input interface{}) (*models.GenerationResult, error) {
	req, ok := input.(*models.SceneRequest)
	if !ok {
		return nil, fmt.Errorf("invalid input type")
	}
	
	systemPrompt := a.systemPrompt()
	userPrompt := a.buildPrompt(req)
	
	params := GenerateParams{
		Temperature: 0.5,
		MaxTokens:   2000,
		JSONMode:    true,
	}
	
	result, err := a.Generate(ctx, systemPrompt, userPrompt, params)
	if err != nil {
		return nil, err
	}
	
	// Validate JSON
	var spec models.SceneSpec
	if err := json.Unmarshal([]byte(result.Text), &spec); err != nil {
		// Try to extract JSON if wrapped in markdown
		extracted := extractJSON(result.Text)
		if extracted != "" {
			result.Text = extracted
		}
	}
	
	return result, nil
}

func (a *DirectorAgent) systemPrompt() string {
	return `あなたは小説の演出家（Director）です。
与えられた設定と意図から、次のシーンの詳細設計図（SceneSpec）をJSON形式で作成してください。

重要：
- 必ず有効なJSONのみを出力してください
- 世界観・キャラクター設定に矛盾がないようにしてください
- 伏線の回収や新しい伏線の設置を考慮してください

SceneSpecの構造：
{
  "scene": {
    "id": "シーンID",
    "chapter": 章番号,
    "sequence_in_chapter": シーン番号,
    "title": "シーンタイトル"
  },
  "narrative": {
    "objective": "このシーンの目的",
    "summary": "概要",
    "key_events": ["出来事1", "出来事2"],
    "revelations": ["明かされる情報"],
    "hooks": ["次へのフック"]
  },
  "constraints": {
    "pov_character": "視点キャラクター",
    "location": "場所",
    "mood": "雰囲気"
  },
  "continuity": {
    "facts_to_reinforce": ["強化する事実"],
    "foreshadowing_to_resolve": ["回収する伏線ID"],
    "foreshadowing_to_plant": ["新規伏線"]
  }
}`
}

func (a *DirectorAgent) buildPrompt(req *models.SceneRequest) string {
	return fmt.Sprintf(`## ユーザーの意図
%s

## シーン要件
- Chapter: %d
- Scene: %d
- POV Character: %s
- Mood: %s
- Word Count: %d

## 必須の出来事
%s

上記の情報に基づいて、SceneSpec JSONを作成してください。`,
		req.Intention,
		req.Chapter,
		req.Scene,
		req.POVCharacter,
		req.Mood,
		req.WordCount,
		formatStringSlice(req.RequiredEvents),
	)
}

func formatStringSlice(slice []string) string {
	if len(slice) == 0 {
		return "なし"
	}
	result := ""
	for _, s := range slice {
		result += "- " + s + "\n"
	}
	return result
}

func extractJSON(text string) string {
	// Try to find JSON block
	start := -1
	end := -1
	
	for i, c := range text {
		if c == '{' && start == -1 {
			start = i
		}
		if c == '}' && start != -1 {
			end = i + 1
		}
	}
	
	if start != -1 && end != -1 && end > start {
		return text[start:end]
	}
	
	return ""
}
