"""
Configuration management for the novelist project.

Handles loading and validation of config.yaml files.
"""

import os
from pathlib import Path
from typing import Any, Dict, Optional

import yaml

from .models import ProjectConfig


class ConfigManager:
    """
    Manages project configuration loading and access.
    
    Follows SSOT principle: config.yaml is the single source for settings.
    """
    
    DEFAULT_CONFIG_PATH = Path("config.yaml")
    
    @classmethod
    def load(cls, project_path: Optional[Path] = None) -> ProjectConfig:
        """
        Load configuration from project directory.
        
        Args:
            project_path: Path to project root. If None, uses current directory.
        
        Returns:
            ProjectConfig: Loaded and validated configuration.
        
        Raises:
            FileNotFoundError: If config.yaml doesn't exist.
        """
        if project_path is None:
            project_path = Path(".")
        
        config_path = project_path / cls.DEFAULT_CONFIG_PATH
        
        if not config_path.exists():
            raise FileNotFoundError(f"Config not found: {config_path}")
        
        with open(config_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        
        return ProjectConfig(**data)
    
    @classmethod
    def save(cls, config: ProjectConfig, project_path: Optional[Path] = None):
        """
        Save configuration to project directory.
        
        Args:
            config: Configuration to save.
            project_path: Path to project root.
        """
        if project_path is None:
            project_path = Path(".")
        
        config_path = project_path / cls.DEFAULT_CONFIG_PATH
        
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.dump(config.model_dump(), f, allow_unicode=True, sort_keys=False)
    
    @classmethod
    def create_default(cls, project_path: Path, project_name: str = "My Novel"):
        """
        Create default configuration for new project.
        
        Args:
            project_path: Path to project root.
            project_name: Name of the project.
        """
        config = ProjectConfig(
            project_name=project_name,
            provider={
                "default": "local_ollama",
                "available": {
                    "local_ollama": {
                        "type": "ollama",
                        "model": "qwen3:1.7b",
                        "base_url": "http://localhost:11434",
                        "timeout": 120
                    }
                },
                "routing": {
                    "director": "local_ollama",
                    "writer": "local_ollama",
                    "checker": "local_ollama",
                    "editor": "local_ollama",
                    "committer": "local_ollama"
                }
            },
            context={
                "budgets": {
                    "bible": 1500,
                    "characters": 1200,
                    "facts": 600,
                    "recap": 400,
                    "icl": 600
                }
            },
            swarm={
                "max_revision": 1,
                "on_persistent_failure": "ask_user"
            },
            generation={
                "default": {
                    "temperature": 0.7,
                    "max_tokens": 2000,
                    "top_p": 0.9
                }
            },
            quality={
                "meta_speech_rate_max": 0.01,
                "repetition_rate_max": 0.05,
                "fact_contradictions_max": 0,
                "character_deviations_max": 0
            }
        )
        
        cls.save(config, project_path)
    
    def get_provider_config(self, agent_name: str) -> Dict[str, Any]:
        """
        Get provider configuration for specific agent.
        
        Args:
            agent_name: Name of the agent (director, writer, etc.)
        
        Returns:
            Dict with provider settings.
        """
        config = self.load()
        
        # Get provider name for this agent
        routing = config.provider.get("routing", {})
        provider_name = routing.get(agent_name, config.provider.get("default", "local_ollama"))
        
        # Get provider details
        available = config.provider.get("available", {})
        return available.get(provider_name, {})


def get_api_key(env_var: str) -> Optional[str]:
    """
    Get API key from environment variable.
    
    Security: Never hardcode API keys. Always use environment variables
    or OS credential store.
    
    Args:
        env_var: Name of environment variable.
    
    Returns:
        API key or None if not set.
    """
    return os.environ.get(env_var)
