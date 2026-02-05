"""
Anthropic provider implementation.

Supports Claude 3 models (Opus, Sonnet, Haiku).
"""

import time
from typing import Any, Dict, Iterator, List, Optional

import httpx

from pal.base import BaseProvider, ProviderCapabilities, ProviderFactory


class AnthropicProvider(BaseProvider):
    """
    Provider for Anthropic Claude API.
    
    Supports Claude 3 Opus, Sonnet, and Haiku.
    """
    
    DEFAULT_BASE_URL = "https://api.anthropic.com"
    API_VERSION = "2023-06-01"
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.base_url = config.get("base_url", self.DEFAULT_BASE_URL)
        self.api_key = config.get("api_key") or self._get_api_key(config)
        
        if not self.api_key:
            raise ValueError("Anthropic API key not provided. Set ANTHROPIC_API_KEY env var or api_key in config.")
        
        # HTTP client
        self.client = httpx.Client(
            base_url=self.base_url,
            headers={
                "x-api-key": self.api_key,
                "anthropic-version": self.API_VERSION,
                "Content-Type": "application/json",
            },
            timeout=self.timeout,
        )
        
        # Pricing per 1K tokens (as of 2024)
        self.pricing = {
            "claude-3-opus-20240229": {"input": 0.015, "output": 0.075},
            "claude-3-sonnet-20240229": {"input": 0.003, "output": 0.015},
            "claude-3-haiku-20240307": {"input": 0.00025, "output": 0.00125},
        }
    
    def _get_api_key(self, config: Dict[str, Any]) -> Optional[str]:
        """Get API key from environment or config."""
        import os
        env_var = config.get("api_key_env", "ANTHROPIC_API_KEY")
        return os.environ.get(env_var)
    
    def _convert_messages(self, messages: List[Dict[str, str]]) -> tuple:
        """
        Convert to Anthropic format.
        
        Anthropic uses 'system' as a top-level param and 'user'/'assistant' messages.
        """
        system_msg = None
        anthropic_messages = []
        
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            
            if role == "system":
                system_msg = content
            elif role in ("user", "assistant"):
                anthropic_messages.append({
                    "role": role,
                    "content": content
                })
        
        return system_msg, anthropic_messages
    
    def generate(
        self,
        messages: List[Dict[str, str]],
        params: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Generate text using Anthropic messages API.
        """
        params = params or {}
        
        system_msg, anthropic_messages = self._convert_messages(messages)
        
        payload = {
            "model": self.model,
            "messages": anthropic_messages,
            "max_tokens": params.get("max_tokens", 2000),
            "temperature": params.get("temperature", 0.7),
            "top_p": params.get("top_p", 0.9),
        }
        
        if system_msg:
            payload["system"] = system_msg
        
        # Thinking mode (if enabled in params)
        if params.get("thinking"):
            payload["thinking"] = {
                "type": "enabled",
                "budget_tokens": params.get("thinking_budget", 2000)
            }
        
        try:
            response = self.client.post("/v1/messages", json=payload)
            response.raise_for_status()
            
            data = response.json()
            
            # Handle text content blocks
            for block in data.get("content", []):
                if block.get("type") == "text":
                    return block.get("text", "")
            
            return ""
        
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                raise RuntimeError("Invalid Anthropic API key")
            raise RuntimeError(f"Anthropic API error: {e}")
    
    def generate_stream(
        self,
        messages: List[Dict[str, str]],
        params: Optional[Dict[str, Any]] = None
    ) -> Iterator[str]:
        """
        Generate text with streaming.
        """
        params = params or {}
        
        system_msg, anthropic_messages = self._convert_messages(messages)
        
        payload = {
            "model": self.model,
            "messages": anthropic_messages,
            "max_tokens": params.get("max_tokens", 2000),
            "temperature": params.get("temperature", 0.7),
            "stream": True,
        }
        
        if system_msg:
            payload["system"] = system_msg
        
        try:
            with self.client.stream("POST", "/v1/messages", json=payload) as response:
                response.raise_for_status()
                
                for line in response.iter_lines():
                    if line.startswith("data: "):
                        data_str = line[6:]
                        
                        if data_str == "[DONE]":
                            break
                        
                        try:
                            import json
                            data = json.loads(data_str)
                            
                            if data.get("type") == "content_block_delta":
                                delta = data.get("delta", {})
                                if delta.get("type") == "text_delta":
                                    yield delta.get("text", "")
                        
                        except (json.JSONDecodeError, KeyError):
                            continue
        
        except httpx.HTTPError as e:
            raise RuntimeError(f"Anthropic streaming error: {e}")
    
    def capabilities(self) -> ProviderCapabilities:
        """Report Anthropic capabilities."""
        ctx_len = 200000  # All Claude 3 models support 200K
        
        return ProviderCapabilities(
            ctx_len=ctx_len,
            supports_tools=True,
            supports_json_mode=False,  # Claude doesn't have native JSON mode yet
            supports_thinking_mode=True,
            supports_streaming=True,
        )
    
    def healthcheck(self) -> bool:
        """Check if API is accessible."""
        try:
            # Anthropic doesn't have a simple models endpoint
            # Use a minimal request to check auth
            response = self.client.get("/v1/models", timeout=10)
            return response.status_code in (200, 404)  # 404 means endpoint doesn't exist but auth worked
        except httpx.RequestError:
            return False
    
    def price_estimate(self, input_tokens: int, output_tokens: int) -> float:
        """
        Estimate cost for generation.
        
        Returns cost in USD.
        """
        model_pricing = self.pricing.get(self.model, self.pricing.get("claude-3-sonnet-20240229"))
        
        input_cost = (input_tokens / 1000) * model_pricing["input"]
        output_cost = (output_tokens / 1000) * model_pricing["output"]
        
        return round(input_cost + output_cost, 4)


# Register provider
ProviderFactory.register("anthropic", AnthropicProvider)
