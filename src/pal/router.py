"""
Provider Router - Route agents to appropriate providers.

Reference: docs/keikaku.md Section 4.2 - Capability-Based Routing
"""

import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from core.config_manager import ConfigManager
from pal.base import BaseProvider, ProviderFactory


class ProviderRouter:
    """
    Routes agent requests to appropriate providers based on capabilities.
    
    Allows different agents to use different models/providers:
    - Director: JSON output capable
    - Writer: Creative writing capable
    - Checker: Precise, can use cheaper model
    """
    
    def __init__(self, project_path: Path):
        self.project_path = Path(project_path)
        self.config = ConfigManager.load(project_path)
        
        # Cache of provider instances
        self._providers: Dict[str, BaseProvider] = {}
        
        # Default provider
        self.default_provider = self.config.provider.get("default", "local_ollama")
        
        # Routing configuration
        self.routing = self.config.provider.get("routing", {})
    
    def get_provider(self, agent_type: str) -> BaseProvider:
        """
        Get provider for specific agent type.
        
        Args:
            agent_type: 'director', 'writer', 'checker', 'editor', 'committer'
        
        Returns:
            Provider instance
        """
        # Check cache
        if agent_type in self._providers:
            return self._providers[agent_type]
        
        # Determine which provider to use
        provider_name = self.routing.get(agent_type, self.default_provider)
        
        # Get provider config
        available = self.config.provider.get("available", {})
        provider_config = available.get(provider_name, {})
        
        if not provider_config:
            raise ValueError(f"Provider '{provider_name}' not configured")
        
        # Create provider instance
        provider_type = provider_config.get("type", "ollama")
        provider = ProviderFactory.create(provider_type, provider_config)
        
        # Cache
        self._providers[agent_type] = provider
        
        return provider
    
    def route_by_capability(self, required_capabilities: List[str]) -> BaseProvider:
        """
        Route based on required capabilities.
        
        Args:
            required_capabilities: List of required capability names
        
        Returns:
            Provider that meets requirements
        """
        available = self.config.provider.get("available", {})
        
        for provider_name, config in available.items():
            # Create temporary provider to check capabilities
            provider_type = config.get("type", "ollama")
            
            try:
                provider = ProviderFactory.create(provider_type, config)
                caps = provider.capabilities()
                
                # Check if all required capabilities are met
                meets_requirements = True
                for cap in required_capabilities:
                    if cap == "json_mode" and not caps.supports_json_mode:
                        meets_requirements = False
                        break
                    if cap == "tools" and not caps.supports_tools:
                        meets_requirements = False
                        break
                    if cap == "thinking" and not caps.supports_thinking_mode:
                        meets_requirements = False
                        break
                
                if meets_requirements:
                    return provider
            
            except Exception:
                continue
        
        # Fall back to default
        return self.get_provider("default")
    
    def get_all_providers(self) -> Dict[str, Dict]:
        """
        Get all available providers with their capabilities.
        
        Returns:
            Dict mapping provider name to capabilities dict
        """
        available = self.config.provider.get("available", {})
        result = {}
        
        for name, config in available.items():
            try:
                provider_type = config.get("type", "ollama")
                provider = ProviderFactory.create(provider_type, config)
                caps = provider.capabilities()
                
                result[name] = {
                    "type": provider_type,
                    "model": config.get("model", "unknown"),
                    "capabilities": caps.to_dict(),
                    "healthy": provider.healthcheck(),
                }
            except Exception as e:
                result[name] = {
                    "type": config.get("type", "unknown"),
                    "error": str(e),
                }
        
        return result
    
    def healthcheck_all(self) -> Dict[str, bool]:
        """Check health of all providers."""
        available = self.config.provider.get("available", {})
        results = {}
        
        for name, config in available.items():
            try:
                provider_type = config.get("type", "ollama")
                provider = ProviderFactory.create(provider_type, config)
                results[name] = provider.healthcheck()
            except Exception:
                results[name] = False
        
        return results


class CostTracker:
    """
    Track token usage and costs across providers.
    """
    
    def __init__(self, project_path: Path):
        self.project_path = Path(project_path)
        self.usage_log: List[Dict] = []
    
    def log_usage(
        self,
        agent: str,
        provider: str,
        model: str,
        input_tokens: int,
        output_tokens: int,
        cost: Optional[float] = None,
        duration_ms: int = 0,
    ):
        """
        Log token usage.
        
        Args:
            agent: Agent name
            provider: Provider name
            model: Model name
            input_tokens: Input token count
            output_tokens: Output token count
            cost: Cost in USD (optional, calculated if not provided)
            duration_ms: Request duration
        """
        entry = {
            "timestamp": time.time(),
            "agent": agent,
            "provider": provider,
            "model": model,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": input_tokens + output_tokens,
            "cost_usd": cost,
            "duration_ms": duration_ms,
        }
        
        self.usage_log.append(entry)
    
    def get_summary(self) -> Dict:
        """Get usage summary."""
        if not self.usage_log:
            return {"total_requests": 0, "total_cost": 0, "total_tokens": 0}
        
        total_cost = sum(e.get("cost_usd", 0) or 0 for e in self.usage_log)
        total_tokens = sum(e.get("total_tokens", 0) for e in self.usage_log)
        
        # By agent
        by_agent: Dict[str, Dict] = {}
        for entry in self.usage_log:
            agent = entry["agent"]
            if agent not in by_agent:
                by_agent[agent] = {"requests": 0, "tokens": 0, "cost": 0}
            by_agent[agent]["requests"] += 1
            by_agent[agent]["tokens"] += entry.get("total_tokens", 0)
            by_agent[agent]["cost"] += entry.get("cost_usd", 0) or 0
        
        # By provider
        by_provider: Dict[str, Dict] = {}
        for entry in self.usage_log:
            prov = entry["provider"]
            if prov not in by_provider:
                by_provider[prov] = {"requests": 0, "tokens": 0, "cost": 0}
            by_provider[prov]["requests"] += 1
            by_provider[prov]["tokens"] += entry.get("total_tokens", 0)
            by_provider[prov]["cost"] += entry.get("cost_usd", 0) or 0
        
        return {
            "total_requests": len(self.usage_log),
            "total_cost": round(total_cost, 4),
            "total_tokens": total_tokens,
            "by_agent": by_agent,
            "by_provider": by_provider,
        }
    
    def print_summary(self):
        """Print usage summary."""
        summary = self.get_summary()
        
        print("=" * 60)
        print("Usage Summary")
        print("=" * 60)
        print(f"Total Requests: {summary['total_requests']}")
        print(f"Total Tokens: {summary['total_tokens']:,}")
        print(f"Total Cost: ${summary['total_cost']:.4f}")
        print()
        
        if summary['by_agent']:
            print("By Agent:")
            for agent, data in summary['by_agent'].items():
                print(f"  {agent:12s}: {data['requests']:3d} req, "
                      f"{data['tokens']:6,} tok, ${data['cost']:.4f}")
            print()
        
        if summary['by_provider']:
            print("By Provider:")
            for prov, data in summary['by_provider'].items():
                print(f"  {prov:12s}: {data['requests']:3d} req, "
                      f"{data['tokens']:6,} tok, ${data['cost']:.4f}")


class TokenEstimator:
    """Estimate token counts for text."""
    
    @staticmethod
    def estimate(text: str) -> int:
        """
        Rough token estimation.
        
        English: ~4 chars per token
        Japanese: ~1.5 chars per token
        """
        if not text:
            return 0
        
        # Count different character types
        ascii_chars = sum(1 for c in text if ord(c) < 128)
        non_ascii_chars = len(text) - ascii_chars
        
        # Estimate
        ascii_tokens = ascii_chars / 4
        non_ascii_tokens = non_ascii_chars / 1.5
        
        return int(ascii_tokens + non_ascii_tokens)
    
    @staticmethod
    def estimate_messages(messages: List[Dict[str, str]]) -> int:
        """Estimate tokens for message list."""
        total = 0
        for msg in messages:
            total += TokenEstimator.estimate(msg.get("content", ""))
            # Add overhead per message
            total += 4
        return total
