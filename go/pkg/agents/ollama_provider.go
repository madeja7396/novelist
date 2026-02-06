package agents

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"strings"
	"time"

	"github.com/novelist/novelist/pkg/models"
)

const defaultOllamaBaseURL = "http://localhost:11434"

type ollamaProvider struct {
	model   string
	baseURL string
	client  *http.Client
}

type ollamaChatRequest struct {
	Model    string                 `json:"model"`
	Messages []Message              `json:"messages"`
	Stream   bool                   `json:"stream"`
	Format   string                 `json:"format,omitempty"`
	Options  map[string]interface{} `json:"options,omitempty"`
}

type ollamaChatResponse struct {
	Message struct {
		Content string `json:"content"`
	} `json:"message"`
	PromptEvalCount int    `json:"prompt_eval_count"`
	EvalCount       int    `json:"eval_count"`
	Error           string `json:"error"`
}

func init() {
	RegisterProviderFactory("ollama", NewOllamaProvider)
}

// NewOllamaProvider creates a provider backed by Ollama HTTP API.
func NewOllamaProvider(config models.ProviderConfig) (Provider, error) {
	if strings.TrimSpace(config.Model) == "" {
		return nil, fmt.Errorf("ollama provider requires model")
	}

	baseURL := strings.TrimRight(strings.TrimSpace(config.BaseURL), "/")
	if baseURL == "" {
		baseURL = defaultOllamaBaseURL
	}

	timeout := time.Duration(config.Timeout) * time.Second
	if timeout <= 0 {
		timeout = 120 * time.Second
	}

	return &ollamaProvider{
		model:   config.Model,
		baseURL: baseURL,
		client:  &http.Client{Timeout: timeout},
	}, nil
}

func (p *ollamaProvider) Name() string {
	return "ollama"
}

func (p *ollamaProvider) Generate(ctx context.Context, messages []Message, params GenerateParams) (*models.GenerationResult, error) {
	reqPayload := ollamaChatRequest{
		Model:    p.model,
		Messages: messages,
		Stream:   false,
		Options: map[string]interface{}{
			"temperature": params.Temperature,
			"num_predict": params.MaxTokens,
			"top_p":       params.TopP,
		},
	}
	if params.JSONMode {
		reqPayload.Format = "json"
	}

	body, err := json.Marshal(reqPayload)
	if err != nil {
		return nil, fmt.Errorf("failed to marshal ollama request: %w", err)
	}

	req, err := http.NewRequestWithContext(ctx, http.MethodPost, p.baseURL+"/api/chat", bytes.NewReader(body))
	if err != nil {
		return nil, fmt.Errorf("failed to build ollama request: %w", err)
	}
	req.Header.Set("Content-Type", "application/json")

	resp, err := p.client.Do(req)
	if err != nil {
		return nil, fmt.Errorf("ollama request failed: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode >= http.StatusBadRequest {
		raw, _ := io.ReadAll(io.LimitReader(resp.Body, 4096))
		return nil, fmt.Errorf("ollama returned %d: %s", resp.StatusCode, strings.TrimSpace(string(raw)))
	}

	var out ollamaChatResponse
	if err := json.NewDecoder(resp.Body).Decode(&out); err != nil {
		return nil, fmt.Errorf("failed to decode ollama response: %w", err)
	}
	if out.Error != "" {
		return nil, fmt.Errorf("ollama error: %s", out.Error)
	}

	promptTokens := out.PromptEvalCount
	completionTokens := out.EvalCount
	if promptTokens <= 0 {
		promptTokens = estimateTokensFromMessages(messages)
	}
	if completionTokens <= 0 {
		completionTokens = estimateTokensFromText(out.Message.Content)
	}

	return &models.GenerationResult{
		Text:             strings.TrimSpace(out.Message.Content),
		PromptTokens:     promptTokens,
		CompletionTokens: completionTokens,
	}, nil
}

func (p *ollamaProvider) Capabilities() ProviderCapabilities {
	return ProviderCapabilities{
		CtxLen:            32768,
		SupportsTools:     false,
		SupportsJSONMode:  true,
		SupportsThinking:  true,
		SupportsStreaming: false,
	}
}

func (p *ollamaProvider) HealthCheck(ctx context.Context) error {
	req, err := http.NewRequestWithContext(ctx, http.MethodGet, p.baseURL+"/api/tags", nil)
	if err != nil {
		return err
	}

	resp, err := p.client.Do(req)
	if err != nil {
		return err
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return fmt.Errorf("status %d", resp.StatusCode)
	}
	return nil
}

func estimateTokensFromMessages(messages []Message) int {
	total := 0
	for _, msg := range messages {
		total += estimateTokensFromText(msg.Content)
	}
	if total <= 0 {
		return 1
	}
	return total
}

func estimateTokensFromText(text string) int {
	if text == "" {
		return 1
	}
	chars := len([]rune(text))
	estimated := chars / 4
	if estimated <= 0 {
		return 1
	}
	return estimated
}
