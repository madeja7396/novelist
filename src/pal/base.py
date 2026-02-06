"""
Provider Abstraction Layer (PAL) base interface.

Reference: docs/keikaku.md Section 4.1 - Provider Abstraction Layer
"""

from abc import ABC, abstractmethod
import importlib
from typing import Any, Dict, Iterator, List, Optional, Union


class ProviderCapabilities:
    """Capabilities reported by a provider."""
    
    def __init__(
        self,
        ctx_len: int = 4096,
        supports_tools: bool = False,
        supports_json_mode: bool = False,
        supports_thinking_mode: bool = False,
        supports_streaming: bool = True,
    ):
        self.ctx_len = ctx_len
        self.supports_tools = supports_tools
        self.supports_json_mode = supports_json_mode
        self.supports_thinking_mode = supports_thinking_mode
        self.supports_streaming = supports_streaming
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "ctx_len": self.ctx_len,
            "supports_tools": self.supports_tools,
            "supports_json_mode": self.supports_json_mode,
            "supports_thinking_mode": self.supports_thinking_mode,
            "supports_streaming": self.supports_streaming,
        }


class BaseProvider(ABC):
    """
    Abstract base class for LLM providers.
    
    All providers (Ollama, OpenAI, Anthropic, etc.) must implement this interface.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize provider with configuration.
        
        Args:
            config: Provider configuration from config.yaml.
        """
        self.config = config
        self.model = config.get("model", "")
        self.timeout = config.get("timeout", 120)
    
    @abstractmethod
    def generate(
        self,
        messages: List[Dict[str, str]],
        params: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Generate text from messages.
        
        Args:
            messages: List of message dicts with 'role' and 'content' keys.
            params: Optional generation parameters (temperature, max_tokens, etc.).
        
        Returns:
            Generated text string.
        """
        pass
    
    @abstractmethod
    def generate_stream(
        self,
        messages: List[Dict[str, str]],
        params: Optional[Dict[str, Any]] = None
    ) -> Iterator[str]:
        """
        Generate text with streaming.
        
        Args:
            messages: List of message dicts.
            params: Optional generation parameters.
        
        Yields:
            Chunks of generated text.
        """
        pass
    
    @abstractmethod
    def capabilities(self) -> ProviderCapabilities:
        """
        Report provider capabilities.
        
        Returns:
            ProviderCapabilities instance.
        """
        pass
    
    @abstractmethod
    def healthcheck(self) -> bool:
        """
        Check if provider is healthy and reachable.
        
        Returns:
            True if healthy, False otherwise.
        """
        pass
    
    def price_estimate(self, input_tokens: int, output_tokens: int) -> Optional[float]:
        """
        Estimate cost for generation.
        
        Args:
            input_tokens: Number of input tokens.
            output_tokens: Expected number of output tokens.
        
        Returns:
            Estimated cost in USD, or None if not applicable (local models).
        """
        return None  # Default: local models have no cost


class ProviderFactory:
    """Factory for creating provider instances."""
    
    _providers: Dict[str, type] = {}
    _builtin_modules: Dict[str, str] = {
        "ollama": "pal.ollama_provider",
        "openai": "pal.openai_provider",
        "anthropic": "pal.anthropic_provider",
    }
    
    @classmethod
    def register(cls, name: str, provider_class: type):
        """Register a provider class."""
        cls._providers[name.lower()] = provider_class

    @classmethod
    def _autoload_provider(cls, provider_type: str):
        """Lazily import built-in providers if they are not registered yet."""
        module = cls._builtin_modules.get(provider_type.lower())
        if not module:
            return
        importlib.import_module(module)
    
    @classmethod
    def create(cls, provider_type: str, config: Dict[str, Any]) -> BaseProvider:
        """
        Create provider instance.
        
        Args:
            provider_type: Type name (ollama, openai, anthropic, etc.).
            config: Provider configuration.
        
        Returns:
            BaseProvider instance.
        
        Raises:
            ValueError: If provider type is unknown.
        """
        provider_key = provider_type.lower()

        if provider_key not in cls._providers:
            cls._autoload_provider(provider_key)

        if provider_key not in cls._providers:
            raise ValueError(f"Unknown provider type: {provider_type}")
        
        return cls._providers[provider_key](config)
    
    @classmethod
    def list_providers(cls) -> List[str]:
        """List available provider types."""
        return list(cls._providers.keys())
