"""Configuration loader for NOVA."""

import os
import yaml
from pathlib import Path
from typing import Any, Dict
from dotenv import load_dotenv


class ConfigSection:
    """Base class for configuration sections."""
    
    def __init__(self, data: Dict[str, Any]):
        for key, value in data.items():
            if isinstance(value, dict):
                setattr(self, key, ConfigSection(value))
            else:
                setattr(self, key, value)
    
    def __getattr__(self, name: str) -> Any:
        """Return None for missing attributes instead of raising error."""
        return None


class Config:
    """Main configuration class that loads from config.yaml."""
    
    _instance = None
    
    def __new__(cls):
        """Singleton pattern to ensure only one config instance."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """Initialize configuration from config.yaml."""
        if self._initialized:
            return
        
        # Load environment variables from .env file
        load_dotenv()
        
        # Get config file path
        config_path = Path(__file__).parent.parent / 'config.yaml'
        
        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
        
        # Load YAML configuration
        with open(config_path, 'r') as f:
            config_data = yaml.safe_load(f)
        
        # Process environment variable substitutions
        config_data = self._substitute_env_vars(config_data)
        
        # Create configuration sections
        for section_name, section_data in config_data.items():
            setattr(self, section_name, ConfigSection(section_data))
        
        self._initialized = True
    
    def _substitute_env_vars(self, data: Any) -> Any:
        """Recursively substitute ${VAR_NAME} with environment variables."""
        if isinstance(data, dict):
            return {k: self._substitute_env_vars(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._substitute_env_vars(item) for item in data]
        elif isinstance(data, str) and data.startswith('${') and data.endswith('}'):
            env_var = data[2:-1]
            return os.getenv(env_var, data)
        return data
    
    def get(self, path: str, default: Any = None) -> Any:
        """
        Get configuration value using dot notation.
        
        Args:
            path: Dot-separated path (e.g., 'api.llm_model')
            default: Default value if path not found
        
        Returns:
            Configuration value or default
        """
        parts = path.split('.')
        value = self
        
        for part in parts:
            value = getattr(value, part, None)
            if value is None:
                return default
        
        return value


# Convenience function to get config instance
def get_config() -> Config:
    """Get the singleton configuration instance."""
    return Config()
