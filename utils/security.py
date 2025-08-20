"""
Utility functions for validation and security.
"""

import re
from pathlib import Path
from typing import Optional


def is_valid_notion_id(notion_id: str) -> bool:
    """
    Valida se una stringa è un ID Notion valido.
    
    Args:
        notion_id: ID da validare
        
    Returns:
        True se l'ID è valido
    """
    if not notion_id or not isinstance(notion_id, str):
        return False
    
    # Formato con trattini: 8-4-4-4-12 caratteri
    uuid_pattern = r'^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$'
    # Formato senza trattini: 32 caratteri
    compact_pattern = r'^[a-f0-9]{32}$'
    
    return bool(re.match(uuid_pattern, notion_id) or re.match(compact_pattern, notion_id))


def sanitize_filename(filename: str) -> str:
    """
    Sanitizza un nome file per evitare path traversal.
    
    Args:
        filename: Nome file da sanitizzare
        
    Returns:
        Nome file sicuro
    """
    if not filename:
        return "untitled"
    
    # Rimuovi caratteri pericolosi
    sanitized = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '_', filename)
    
    # Evita nomi riservati su Windows
    reserved_names = {
        'CON', 'PRN', 'AUX', 'NUL',
        'COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9',
        'LPT1', 'LPT2', 'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9'
    }
    
    if sanitized.upper() in reserved_names:
        sanitized = f"_{sanitized}"
    
    # Limita la lunghezza
    return sanitized[:255]


def safe_path_join(base_path: str, *paths: str) -> Path:
    """
    Unisce percorsi in modo sicuro, prevenendo path traversal.
    
    Args:
        base_path: Percorso base
        paths: Percorsi da unire
        
    Returns:
        Percorso sicuro
        
    Raises:
        ValueError: Se il percorso risultante esce dalla directory base
    """
    base = Path(base_path).resolve()
    result = base
    
    for path in paths:
        sanitized = sanitize_filename(path)
        result = result / sanitized
    
    # Verifica che il percorso risultante sia sotto la directory base
    try:
        result.resolve().relative_to(base)
    except ValueError:
        raise ValueError(f"Percorso non sicuro rilevato: {result}")
    
    return result
