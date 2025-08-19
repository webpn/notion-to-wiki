"""
Modulo per la gestione del sistema di caching.
"""

import os
import json
from .config import CACHE_DIR, USE_CACHE


def get_cached_data(filename):
    """Recupera i dati dal cache locale se presenti."""
    cache_path = os.path.join(CACHE_DIR, filename)
    if USE_CACHE and os.path.exists(cache_path):
        with open(cache_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return None


def save_cached_data(filename, data):
    """Salva i dati nel cache locale."""
    os.makedirs(CACHE_DIR, exist_ok=True)
    cache_path = os.path.join(CACHE_DIR, filename)
    with open(cache_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
