package agents

import (
	"context"
	"fmt"
	"strings"

	"github.com/novelist/novelist/go/pkg/models"
)

// EditorInput represents input for editor
type EditorInput struct {
	Text   string
	Issues []models.Issue
}

// EditorAgent fixes issues
type EditorAgent struct {
	*BaseAgent
}

// NewEditorAgent creates a new editor agent
func NewEditorAgent(config AgentConfig) *EditorAgent {
	return &EditorAgent{
		BaseAgent: NewBaseAgent("editor", config.Provider),
	}
}

// Execute fixes text
func (a *EditorAgent) Execute(ctx context.Context, input interface{}) (*models.GenerationResult, error) {
	in, ok := input.(*EditorInput)
	if !ok {
		return nil, fmt.Errorf("invalid input type")
	}
	
	systemPrompt := `あなたは熟練した小説編集者です。
与えられた文章の問題を修正し、品質を向上させてください。

改善の指針：
- 冗長な表現を簡潔に
- 同じ語句の過度な反復を削除
- テンポを改善
- 原作の意味・意図は保持
- 本文のみ出力（解説不要）`
	
	userPrompt := a.buildPrompt(in)
	
	params := GenerateParams{
		Temperature: 0.4,
		MaxTokens:   len(in.Text) + 500,
	}
	
	return a.Generate(ctx, systemPrompt, userPrompt, params)
}

func (a *EditorAgent) buildPrompt(input *EditorInput) string {
	var issueList strings.Builder
	for _, issue := range input.Issues {
		if issue.Severity == "error" || issue.Severity == "warning" {
			issueList.WriteString(fmt.Sprintf("- [%s] %s\n", issue.Category, issue.Description))
		}
	}
	
	return fmt.Sprintf(`## 編集対象の文章
%s

## 修正すべき問題
%s

上記の問題を修正した文章を出力してください。`,
		input.Text,
		issueList.String(),
	)
}
