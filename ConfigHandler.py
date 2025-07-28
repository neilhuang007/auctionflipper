#!/usr/bin/env python3
"""
Configuration Handler for AuctionFlipper

Handles configuration loading from config.json and environment variables.
"""

import json
import os
import logging
from typing import Dict, Any, Optional

DEFAULT_CONFIG = {
    "hypixel_api_key": None,
    "mongodb_url": "mongodb://localhost:27017",
    "database_name": "skyblock",
    "evaluation_service": {
        "url": "http://localhost:3000",
        "timeout": 10
    },
    "performance": {
        "max_concurrent_pages": 12,
        "cache_ttl_seconds": 300,
        "connection_pool_size": 200
    }
}

_config: Optional[Dict[str, Any]] = None

def load_config() -> Dict[str, Any]:
    """Load configuration from config.json and environment variables."""
    global _config
    
    if _config is not None:
        return _config
    
    config = DEFAULT_CONFIG.copy()
    
    # Try to load from config.json
    config_file = "config.json"
    if os.path.exists(config_file):
        try:
            with open(config_file, 'r') as f:
                file_config = json.load(f)
                config.update(file_config)
            print(f"✅ Loaded configuration from {config_file}")
        except Exception as e:
            print(f"⚠️  Error loading {config_file}: {e}")
    else:
        print(f"ℹ️  {config_file} not found, using defaults")
    
    # Override with environment variables if they exist
    env_overrides = {
        "HYPIXEL_API_KEY": ["hypixel_api_key"],
        "MONGODB_URL": ["mongodb_url"],
        "DATABASE_NAME": ["database_name"],
        "EVALUATION_SERVICE_URL": ["evaluation_service", "url"],
        "EVALUATION_SERVICE_TIMEOUT": ["evaluation_service", "timeout"],
        "MAX_CONCURRENT_PAGES": ["performance", "max_concurrent_pages"],
        "CACHE_TTL_SECONDS": ["performance", "cache_ttl_seconds"],
        "CONNECTION_POOL_SIZE": ["performance", "connection_pool_size"]
    }
    
    for env_var, config_path in env_overrides.items():
        env_value = os.getenv(env_var)
        if env_value:
            # Navigate to the nested config location
            current = config
            for key in config_path[:-1]:
                if key not in current:
                    current[key] = {}
                current = current[key]
            
            # Convert to appropriate type
            final_key = config_path[-1]
            if final_key in ["timeout", "max_concurrent_pages", "cache_ttl_seconds", "connection_pool_size"]:
                try:
                    current[final_key] = int(env_value)
                except ValueError:
                    print(f"⚠️  Invalid integer value for {env_var}: {env_value}")
            else:
                current[final_key] = env_value
            
            print(f"✅ Environment override: {env_var} = {env_value}")
    
    # Validate configuration
    if not config["hypixel_api_key"] or config["hypixel_api_key"] == "your-hypixel-api-key-here":
        print("⚠️  No Hypixel API key configured. Using public endpoints (may have rate limits)")
        print("   Set HYPIXEL_API_KEY environment variable or update config.json")
    
    _config = config
    return config

def get_config() -> Dict[str, Any]:
    """Get the current configuration."""
    if _config is None:
        return load_config()
    return _config

def get_hypixel_api_key() -> Optional[str]:
    """Get the Hypixel API key if configured."""
    config = get_config()
    api_key = config.get("hypixel_api_key")
    if api_key and api_key != "your-hypixel-api-key-here":
        return api_key
    return None

def get_api_url(endpoint: str) -> str:
    """Get API URL with API key parameter if available."""
    api_key = get_hypixel_api_key()
    if api_key:
        separator = "&" if "?" in endpoint else "?"
        return f"{endpoint}{separator}key={api_key}"
    return endpoint

def get_mongodb_url() -> str:
    """Get MongoDB connection URL."""
    return get_config()["mongodb_url"]

def get_database_name() -> str:
    """Get database name."""
    return get_config()["database_name"]

def get_evaluation_service_config() -> Dict[str, Any]:
    """Get evaluation service configuration."""
    return get_config()["evaluation_service"]

def get_performance_config() -> Dict[str, Any]:
    """Get performance configuration."""
    return get_config()["performance"]

# Initialize configuration on import
load_config()