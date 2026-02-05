package agents

import (
	"context"
	"encoding/json"
	"fmt"

	"github.com/novelist/novelist/go/pkg/models"
)

// CheckerInput represents input for checker
type CheckerInput struct {
	Text         string
	Chapter      int
	Scene        int
	POVCharacter string
}

// CheckerAgent checks for issues
type CheckerAgent struct {
	*BaseAgent
}

// NewCheckerAgent creates a new checker agent
func NewCheckerAgent(config AgentConfig) *CheckerAgent {
	return &CheckerAgent{
		BaseAgent: NewBaseAgent("checker", config.Provider),
	}
}

// Check checks text for issues
func (a *CheckerAgent) Check(ctx context.Context, input *CheckerInput) ([]models.Issue, error) {
	systemPrompt := `あなたは小説の設定・矛盾チェッカーです。
文章を客観的に分析し、問題点をJSON形式で出力してください。`
	
	userPrompt := fmt.Sprintf(`チェック対象の文章:
%s

以下の点をチェックし、問題があればJSON配列で出力：
1. 設定矛盾（世界観、技術水準）
2. キャラクター逸脱（口調、価値観）
3. 視点違反
4. 事実矛盾

問題がなければ空配列 [] を返してください。

出力形式:
[
  {
    "category": "fact|character|world|pov",
    "severity": "error|warning|info",
    "description": "問題の説明"
  }
]`,
		input.Text[:min(len(input.Text), 2000)],
	)
	
	params := GenerateParams{
		Temperature: 0.2,
		MaxTokens:   1000,
	}
	
	result, err := a.Generate(ctx, systemPrompt, userPrompt, params)
	if err != nil {
		return nil, err
	}
	
	// Parse issues
	var issues []models.Issue
	jsonStr := extractJSON(result.Text)
	if jsonStr == "" {
		jsonStr = result.Text
	}
	
	if err := json.Unmarshal([]byte(jsonStr), &issues); err != nil {
		// No issues found or parse error
		return []models.Issue{}, nil
	}
	
	return issues, nil
}

func min(a, b int) int {
	if a < b {
		return a
	}
	return b
}
