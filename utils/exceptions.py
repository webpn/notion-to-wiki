"""
Custom exceptions for the Notion backup system.
"""


class NotionBackupError(Exception):
    """Base exception for Notion backup operations."""
    pass


class NotionAPIError(NotionBackupError):
    """Raised when Notion API calls fail."""
    pass


class ConfigurationError(NotionBackupError):
    """Raised when configuration is invalid or missing."""
    pass


class CacheError(NotionBackupError):
    """Raised when cache operations fail."""
    pass


class ConversionError(NotionBackupError):
    """Raised when content conversion fails."""
    pass
