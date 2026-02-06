package agents

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"os"
	"strings"
	"time"

	"github.com/novelist/novelist/pkg/models"
)

const defaultOpenAIBaseURL = "https://api.openai.com/v1"

type openAIProvider struct {
	model      string
	baseURL    string
	apiKey     string
	client     *http.Client
	chatPath   string
	modelsPath string
}

type openAIRequest struct {
	Model          string    `json:"model"`
	Messages       []Message `json:"messages"`
	Temperature    float64   `json:"temperature,omitempty"`
	MaxTokens      int       `json:"max_tokens,omitempty"`
	TopP           float64   `json:"top_p,omitempty"`
	ResponseFormat any       `json:"response_format,omitempty"`
}

type openAIResponse struct {
	Choices []struct {
		Message struct {
			Content string `json:"content"`
		} `json:"message"`
	} `json:"choices"`
	Usage struct {
		PromptTokens     int `json:"prompt_tokens"`
		CompletionTokens int `json:"completion_tokens"`
	} `json:"usage"`
	Error *struct {
		Message string `json:"message"`
	} `json:"error,omitempty"`
}

func init() {
	RegisterProviderFactory("openai", NewOpenAIProvider)
}

// NewOpenAIProvider creates a provider backed by OpenAI-compatible API.
func NewOpenAIProvider(config models.ProviderConfig) (Provider, error) {
	if strings.TrimSpace(config.Model) == "" {
		return nil, fmt.Errorf("openai provider requires model")
	}

	baseURL := strings.TrimRight(strings.TrimSpace(config.BaseURL), "/")
	if baseURL == "" {
		baseURL = defaultOpenAIBaseURL
	}

	apiKeyEnv := strings.TrimSpace(config.APIKeyEnv)
	if apiKeyEnv == "" {
		apiKeyEnv = "OPENAI_API_KEY"
	}
	apiKey := strings.TrimSpace(os.Getenv(apiKeyEnv))
	if apiKey == "" {
		return nil, fmt.Errorf("openai API key is missing in env %s", apiKeyEnv)
	}

	timeout := time.Duration(config.Timeout) * time.Second
	if timeout <= 0 {
		timeout = 60 * time.Second
	}

	chatPath, modelsPath := openAIPaths(baseURL)

	return &openAIProvider{
		model:      config.Model,
		baseURL:    baseURL,
		apiKey:     apiKey,
		client:     &http.Client{Timeout: timeout},
		chatPath:   chatPath,
		modelsPath: modelsPath,
	}, nil
}

func (p *openAIProvider) Name() string {
	return "openai"
}

func (p *openAIProvider) Generate(ctx context.Context, messages []Message, params GenerateParams) (*models.GenerationResult, error) {
	payload := openAIRequest{
		Model:       p.model,
		Messages:    messages,
		Temperature: params.Temperature,
		MaxTokens:   params.MaxTokens,
		TopP:        params.TopP,
	}
	if params.JSONMode {
		payload.ResponseFormat = map[string]string{"type": "json_object"}
	}

	body, err := json.Marshal(payload)
	if err != nil {
		return nil, fmt.Errorf("failed to marshal openai request: %w", err)
	}

	req, err := http.NewRequestWithContext(ctx, http.MethodPost, p.baseURL+p.chatPath, bytes.NewReader(body))
	if err != nil {
		return nil, fmt.Errorf("failed to build openai request: %w", err)
	}
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Authorization", "Bearer "+p.apiKey)

	resp, err := p.client.Do(req)
	if err != nil {
		return nil, fmt.Errorf("openai request failed: %w", err)
	}
	defer resp.Body.Close()

	raw, err := io.ReadAll(io.LimitReader(resp.Body, 2*1024*1024))
	if err != nil {
		return nil, fmt.Errorf("failed reading openai response: %w", err)
	}

	var out openAIResponse
	if err := json.Unmarshal(raw, &out); err != nil {
		return nil, fmt.Errorf("failed to decode openai response: %w", err)
	}

	if resp.StatusCode >= http.StatusBadRequest {
		msg := strings.TrimSpace(string(raw))
		if out.Error != nil && out.Error.Message != "" {
			msg = out.Error.Message
		}
		return nil, fmt.Errorf("openai returned %d: %s", resp.StatusCode, msg)
	}

	if len(out.Choices) == 0 {
		return nil, fmt.Errorf("openai response missing choices")
	}

	text := strings.TrimSpace(out.Choices[0].Message.Content)
	promptTokens := out.Usage.PromptTokens
	completionTokens := out.Usage.CompletionTokens
	if promptTokens <= 0 {
		promptTokens = estimateTokensFromMessages(messages)
	}
	if completionTokens <= 0 {
		completionTokens = estimateTokensFromText(text)
	}

	return &models.GenerationResult{
		Text:             text,
		PromptTokens:     promptTokens,
		CompletionTokens: completionTokens,
	}, nil
}

func (p *openAIProvider) Capabilities() ProviderCapabilities {
	ctxLen := 16385
	if strings.Contains(p.model, "gpt-4") {
		ctxLen = 8192
	}
	if strings.Contains(p.model, "gpt-4o") || strings.Contains(p.model, "gpt-4.1") {
		ctxLen = 128000
	}

	return ProviderCapabilities{
		CtxLen:            ctxLen,
		SupportsTools:     true,
		SupportsJSONMode:  true,
		SupportsThinking:  false,
		SupportsStreaming: false,
	}
}

func (p *openAIProvider) HealthCheck(ctx context.Context) error {
	req, err := http.NewRequestWithContext(ctx, http.MethodGet, p.baseURL+p.modelsPath, nil)
	if err != nil {
		return err
	}
	req.Header.Set("Authorization", "Bearer "+p.apiKey)

	resp, err := p.client.Do(req)
	if err != nil {
		return err
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		raw, _ := io.ReadAll(io.LimitReader(resp.Body, 2048))
		return fmt.Errorf("status %d: %s", resp.StatusCode, strings.TrimSpace(string(raw)))
	}
	return nil
}

func openAIPaths(baseURL string) (chatPath string, modelsPath string) {
	if strings.HasSuffix(baseURL, "/v1") {
		return "/chat/completions", "/models"
	}
	return "/v1/chat/completions", "/v1/models"
}
