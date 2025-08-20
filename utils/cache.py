"""
Module for managing the caching system.
"""

import os
import json
import time
from pathlib import Path
from typing import Any, Optional
from datetime import datetime, timedelta
from .config import CACHE_DIR, USE_CACHE
from .exceptions import CacheError


def _get_cache_path(filename: str) -> Path:
    """Get the full path of the cache file."""
    return Path(CACHE_DIR) / filename


def _is_cache_valid(cache_path: Path, max_age_hours: int = 24) -> bool:
    """Check if the cache is still valid."""
    if not cache_path.exists():
        return False
    
    cache_age = datetime.now() - datetime.fromtimestamp(cache_path.stat().st_mtime)
    return cache_age < timedelta(hours=max_age_hours)


def get_cached_data(filename: str, max_age_hours: int = 24) -> Optional[Any]:
    """
    Retrieve data from local cache if present and valid.
    
    Args:
        filename: Cache file name
        max_age_hours: Maximum cache age in hours
        
    Returns:
        Data from cache or None if invalid/non-existent
    """
    if not USE_CACHE:
        return None
        
    cache_path = _get_cache_path(filename)
    
    if not _is_cache_valid(cache_path, max_age_hours):
        return None
    
    try:
        with open(cache_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        # Corrupted cache, delete it
        cache_path.unlink(missing_ok=True)
        return None


def save_cached_data(filename: str, data: Any) -> None:
    """
    Save data to local cache.
    
    Args:
        filename: Cache file name
        data: Data to save
        
    Raises:
        CacheError: If saving fails
    """
    try:
        cache_path = _get_cache_path(filename)
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(cache_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except (OSError, TypeError) as e:
        raise CacheError(f"Error saving cache {filename}: {e}")


def clear_cache(pattern: str = "*") -> int:
    """
    Clear cache files matching the pattern.
    
    Args:
        pattern: Pattern for files to delete (default: all)
        
    Returns:
        Number of files deleted
    """
    cache_dir = Path(CACHE_DIR)
    if not cache_dir.exists():
        return 0
    
    count = 0
    for cache_file in cache_dir.glob(pattern):
        if cache_file.is_file():
            cache_file.unlink()
            count += 1
    
    return count
