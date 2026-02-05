"""
Ollama provider implementation for local LLM inference.

Reference: docs/keikaku.md Section 4.1 - Provider Abstraction Layer
"""

import json
import time
from typing import Any, Dict, Iterator, List, Optional

import httpx

from .base import BaseProvider, ProviderCapabilities, ProviderFactory


class OllamaProvider(BaseProvider):
    """
    Provider for Ollama local LLM server.
    
    Supports any model running on Ollama (Qwen3, Llama, etc.).
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.base_url = config.get("base_url", "http://localhost:11434")
        self.api_generate = f"{self.base_url}/api/generate"
        self.api_chat = f"{self.base_url}/api/chat"
        self.api_tags = f"{self.base_url}/api/tags"
        
        # HTTP client with timeout
        self.client = httpx.Client(timeout=self.timeout)
    
    def generate(
        self,
        messages: List[Dict[str, str]],
        params: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Generate text using Ollama chat API.
        
        Args:
            messages: List of {'role': 'user'|'assistant'|'system', 'content': str}.
            params: Generation parameters.
        
        Returns:
            Generated text.
        """
        params = params or {}
        
        # Convert messages to Ollama format
        ollama_messages = self._convert_messages(messages)
        
        # Build request payload
        payload = {
            "model": self.model,
            "messages": ollama_messages,
            "stream": False,
            "options": {
                "temperature": params.get("temperature", 0.7),
                "num_predict": params.get("max_tokens", 2000),
                "top_p": params.get("top_p", 0.9),
            }
        }
        
        # Add system message if present
        system_content = self._extract_system_message(messages)
        if system_content:
            payload["system"] = system_content
        
        try:
            response = self.client.post(self.api_chat, json=payload)
            response.raise_for_status()
            
            data = response.json()
            return data.get("message", {}).get("content", "")
        
        except httpx.HTTPError as e:
            raise RuntimeError(f"Ollama API error: {e}")
    
    def generate_stream(
        self,
        messages: List[Dict[str, str]],
        params: Optional[Dict[str, Any]] = None
    ) -> Iterator[str]:
        """
        Generate text with streaming.
        
        Yields text chunks as they are generated.
        """
        params = params or {}
        
        ollama_messages = self._convert_messages(messages)
        
        payload = {
            "model": self.model,
            "messages": ollama_messages,
            "stream": True,
            "options": {
                "temperature": params.get("temperature", 0.7),
                "num_predict": params.get("max_tokens", 2000),
                "top_p": params.get("top_p", 0.9),
            }
        }
        
        try:
            with self.client.stream("POST", self.api_chat, json=payload) as response:
                response.raise_for_status()
                
                for line in response.iter_lines():
                    if line:
                        try:
                            data = json.loads(line)
                            chunk = data.get("message", {}).get("content", "")
                            if chunk:
                                yield chunk
                            
                            # Check if done
                            if data.get("done", False):
                                break
                        except json.JSONDecodeError:
                            continue
        
        except httpx.HTTPError as e:
            raise RuntimeError(f"Ollama streaming error: {e}")
    
    def capabilities(self) -> ProviderCapabilities:
        """
        Report Ollama capabilities.
        
        Note: Actual capabilities depend on the loaded model.
        """
        # Default capabilities for Qwen3-1.7B
        return ProviderCapabilities(
            ctx_len=32768,  # Qwen3-1.7B context length
            supports_tools=False,  # Ollama may support tools depending on model
            supports_json_mode=False,  # JSON mode depends on model
            supports_thinking_mode=True,
            supports_streaming=True,
        )
    
    def healthcheck(self) -> bool:
        """
        Check if Ollama server is running.
        
        Returns:
            True if server is reachable.
        """
        try:
            response = self.client.get(self.api_tags, timeout=5)
            if response.status_code == 200:
                # Check if our model is available
                data = response.json()
                models = [m.get("name", "") for m in data.get("models", [])]
                return self.model in models or any(self.model in m for m in models)
            return False
        except httpx.RequestError:
            return False
    
    def _convert_messages(self, messages: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """
        Convert standard messages to Ollama format.
        
        Ollama chat API expects: [{"role": "user"|"assistant", "content": "..."}]
        """
        converted = []
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            
            # Skip system messages (handled separately in Ollama)
            if role == "system":
                continue
            
            converted.append({
                "role": role,
                "content": content
            })
        
        return converted
    
    def _extract_system_message(self, messages: List[Dict[str, str]]) -> Optional[str]:
        """Extract system message content if present."""
        for msg in messages:
            if msg.get("role") == "system":
                return msg.get("content")
        return None
    
    def list_models(self) -> List[str]:
        """List available models on Ollama server."""
        try:
            response = self.client.get(self.api_tags)
            response.raise_for_status()
            data = response.json()
            return [m.get("name", "") for m in data.get("models", [])]
        except httpx.HTTPError:
            return []


# Register provider
ProviderFactory.register("ollama", OllamaProvider)
