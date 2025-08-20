"""
Module for managing project configuration.
"""

import json
import os
import sys
from pathlib import Path
from typing import Tuple, Optional
from rich.console import Console
from .exceptions import ConfigurationError

console = Console()

# --- Configuration ---
CONFIG_FILE = os.getenv("NOTION_CONFIG_FILE", "config.json")
OUTPUT_DIR = os.getenv("NOTION_OUTPUT_DIR", "notion_wiki")
CACHE_DIR = os.getenv("NOTION_CACHE_DIR", "_notion_cache")
USE_CACHE = os.getenv("NOTION_USE_CACHE", "true").lower() in ("true", "1", "yes")


def load_config() -> Tuple[str, str]:
    """
    Load configuration from JSON file or environment variables.
    
    Returns:
        Tuple[str, str]: (notion_token, root_page_id)
        
    Raises:
        ConfigurationError: If configuration is invalid or missing
    """
    # Try environment variables first
    notion_token = os.getenv("NOTION_TOKEN")
    root_page_id = os.getenv("NOTION_ROOT_PAGE_ID")
    
    if notion_token and root_page_id:
        return notion_token, root_page_id
    
    # Fallback to configuration file
    config_path = Path(CONFIG_FILE)
    
    if not config_path.exists():
        raise ConfigurationError(
            f"Configuration file '{CONFIG_FILE}' not found and environment "
            "variables NOTION_TOKEN/NOTION_ROOT_PAGE_ID not set."
        )
    
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
            
        notion_token = config.get("notion_token") or notion_token
        root_page_id = config.get("root_page_id") or root_page_id
        
        if not notion_token or not root_page_id:
            raise ConfigurationError(
                "Notion token or root page ID not configured correctly."
            )
            
        return notion_token, root_page_id
        
    except json.JSONDecodeError as e:
        raise ConfigurationError(f"Error parsing JSON file: {e}")
    except Exception as e:
        raise ConfigurationError(f"Error loading configuration: {e}")


def ensure_directories() -> None:
    """Create necessary directories if they don't exist."""
    try:
        Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)
        Path(CACHE_DIR).mkdir(parents=True, exist_ok=True)
    except OSError as e:
        raise ConfigurationError(f"Unable to create directories: {e}")
