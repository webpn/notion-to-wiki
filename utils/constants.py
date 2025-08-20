"""
Constants and configuration values for the Notion backup system.
"""

# Database column orders for specific types
TRACCIAMENTI_COLUMNS = ["Schermata", "Evento di navigazione", "AA Events"]

# Supported block types for conversion
SUPPORTED_BLOCK_TYPES = {
    "paragraph", "heading_1", "heading_2", "heading_3",
    "bulleted_list_item", "numbered_list_item", "quote",
    "code", "divider", "image", "callout", "bookmark",
    "equation", "file", "child_page", "child_database"
}

# Cache settings
DEFAULT_CACHE_AGE_HOURS = 24
MAX_RETRIES = 3
RETRY_DELAY_SECONDS = 1

# Markdown formatting
MARKDOWN_TABLE_SEPARATOR = "---"
