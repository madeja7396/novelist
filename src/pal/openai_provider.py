"""
OpenAI provider implementation.

Supports GPT-4, GPT-3.5, and compatible APIs.
"""

import time
from typing import Any, Dict, Iterator, List, Optional

import httpx

from pal.base import BaseProvider, ProviderCapabilities, ProviderFactory


class OpenAIProvider(BaseProvider):
    """
    Provider for OpenAI API.
    
    Supports GPT-4, GPT-3.5-turbo, and compatible endpoints.
    """
    
    DEFAULT_BASE_URL = "https://api.openai.com/v1"
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.base_url = config.get("base_url", self.DEFAULT_BASE_URL)
        self.api_key = config.get("api_key") or self._get_api_key(config)
        
        if not self.api_key:
            raise ValueError("OpenAI API key not provided. Set OPENAI_API_KEY env var or api_key in config.")
        
        # HTTP client
        self.client = httpx.Client(
            base_url=self.base_url,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            timeout=self.timeout,
        )
        
        # Pricing per 1K tokens (as of 2024)
        self.pricing = {
            "gpt-4": {"input": 0.03, "output": 0.06},
            "gpt-4-turbo": {"input": 0.01, "output": 0.03},
            "gpt-3.5-turbo": {"input": 0.0005, "output": 0.0015},
        }
    
    def _get_api_key(self, config: Dict[str, Any]) -> Optional[str]:
        """Get API key from environment or config."""
        import os
        env_var = config.get("api_key_env", "OPENAI_API_KEY")
        return os.environ.get(env_var)
    
    def generate(
        self,
        messages: List[Dict[str, str]],
        params: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Generate text using OpenAI chat completion API.
        """
        params = params or {}
        
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": params.get("temperature", 0.7),
            "max_tokens": params.get("max_tokens", 2000),
            "top_p": params.get("top_p", 0.9),
            "stream": False,
        }
        
        # Add JSON mode if requested
        if params.get("json_mode"):
            payload["response_format"] = {"type": "json_object"}
        
        try:
            response = self.client.post("/chat/completions", json=payload)
            response.raise_for_status()
            
            data = response.json()
            return data["choices"][0]["message"]["content"]
        
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                raise RuntimeError("Invalid OpenAI API key")
            elif e.response.status_code == 429:
                raise RuntimeError("OpenAI rate limit exceeded")
            raise RuntimeError(f"OpenAI API error: {e}")
    
    def generate_stream(
        self,
        messages: List[Dict[str, str]],
        params: Optional[Dict[str, Any]] = None
    ) -> Iterator[str]:
        """
        Generate text with streaming.
        """
        params = params or {}
        
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": params.get("temperature", 0.7),
            "max_tokens": params.get("max_tokens", 2000),
            "stream": True,
        }
        
        try:
            with self.client.stream("POST", "/chat/completions", json=payload) as response:
                response.raise_for_status()
                
                for line in response.iter_lines():
                    if line and line.startswith("data: "):
                        data_str = line[6:]  # Remove "data: " prefix
                        
                        if data_str == "[DONE]":
                            break
                        
                        try:
                            import json
                            data = json.loads(data_str)
                            delta = data["choices"][0].get("delta", {})
                            content = delta.get("content", "")
                            if content:
                                yield content
                        except (json.JSONDecodeError, KeyError):
                            continue
        
        except httpx.HTTPError as e:
            raise RuntimeError(f"OpenAI streaming error: {e}")
    
    def capabilities(self) -> ProviderCapabilities:
        """Report OpenAI capabilities."""
        ctx_len = 128000 if "gpt-4-turbo" in self.model else (
            8192 if "gpt-4" in self.model else 16385
        )
        
        return ProviderCapabilities(
            ctx_len=ctx_len,
            supports_tools=True,
            supports_json_mode=True,
            supports_thinking_mode=False,
            supports_streaming=True,
        )
    
    def healthcheck(self) -> bool:
        """Check if API is accessible."""
        try:
            response = self.client.get("/models", timeout=10)
            return response.status_code == 200
        except httpx.RequestError:
            return False
    
    def price_estimate(self, input_tokens: int, output_tokens: int) -> float:
        """
        Estimate cost for generation.
        
        Returns cost in USD.
        """
        model_pricing = self.pricing.get(self.model, self.pricing.get("gpt-3.5-turbo"))
        
        input_cost = (input_tokens / 1000) * model_pricing["input"]
        output_cost = (output_tokens / 1000) * model_pricing["output"]
        
        return round(input_cost + output_cost, 4)


# Register provider
ProviderFactory.register("openai", OpenAIProvider)
