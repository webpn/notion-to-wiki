"""
Module for downloading content from Notion via API.
"""

import requests
from notion_client import Client
from rich.console import Console
from .cache import get_cached_data, save_cached_data

console = Console()


class NotionDownloader:
    """Class for managing downloads of content from Notion."""
    
    def __init__(self, notion_token):
        """Initialize the Notion client."""
        self.notion = Client(auth=notion_token)
    
    def download_block(self, block_id):
        """Download a Notion block and convert it to Markdown."""
        cache_filename = f"block_{block_id}.json"
        cached_data = get_cached_data(cache_filename)
        if cached_data is not None:
            return cached_data
        else:
            try:
                block = self.notion.blocks.retrieve(block_id)
                save_cached_data(cache_filename, block)
                return block
            except requests.exceptions.RequestException as e:
                console.print(f"[bold red]Network error downloading block {block_id}:[/bold red] {e}")
                return None
            except Exception as e:
                console.print(f"[bold red]Unexpected error downloading block {block_id}:[/bold red] {e}")
                return None

    def download_page_data(self, page_id):
        """Download data from a Notion page."""
        cache_filename = f"page_{page_id}.json"
        cached_data = get_cached_data(cache_filename)
        if cached_data is not None:
            return cached_data
        else:
            try:
                page = self.notion.pages.retrieve(page_id)
                save_cached_data(cache_filename, page)
                return page
            except requests.exceptions.RequestException as e:
                console.print(f"[bold red]Network error downloading page {page_id}:[/bold red] {e}")
                return None
            except Exception as e:
                console.print(f"[bold red]Unexpected error downloading page {page_id}:[/bold red] {e}")
                return None

    def download_page_blocks(self, page_id):
        """Download blocks from a Notion page (with caching)."""
        cache_filename = f"page_blocks_{page_id}.json"
        cached_data = get_cached_data(cache_filename)
        if cached_data is not None:
            return cached_data
        else:
            try:
                blocks = self.notion.blocks.children.list(block_id=page_id).get("results")
                save_cached_data(cache_filename, blocks)
                return blocks
            except requests.exceptions.RequestException as e:
                console.print(f"[bold red]Network error downloading page blocks {page_id}:[/bold red] {e}")
                return None
            except Exception as e:
                console.print(f"[bold red]Unexpected error downloading page blocks {page_id}:[/bold red] {e}")
                return None

    def download_database_data(self, database_id):
        """Download data from a Notion database."""
        cache_filename = f"database_{database_id}.json"
        cached_data = get_cached_data(cache_filename)
        if cached_data is not None:
            return cached_data
        else:
            try:
                database = self.notion.databases.retrieve(database_id)
                save_cached_data(cache_filename, database)
                return database
            except requests.exceptions.RequestException as e:
                console.print(f"[bold red]Network error downloading database {database_id}:[/bold red] {e}")
                return None
            except Exception as e:
                console.print(f"[bold red]Unexpected error downloading database {database_id}:[/bold red] {e}")
                return None

    def download_database_query(self, database_id):
        """Download results from a Notion database query (with caching)."""
        cache_filename = f"database_query_{database_id}.json"
        cached_data = get_cached_data(cache_filename)
        if cached_data is not None:
            return cached_data
        else:
            try:
                results = self.notion.databases.query(database_id=database_id).get("results")
                save_cached_data(cache_filename, results)
                return results
            except requests.exceptions.RequestException as e:
                console.print(f"[bold red]Network error querying database {database_id}:[/bold red] {e}")
                return None
            except Exception as e:
                console.print(f"[bold red]Unexpected error querying database {database_id}:[/bold red] {e}")
                return None

    def download_related_page_data(self, page_id):
        """Download data from a Notion page (with caching) for relations."""
        cache_filename = f"related_page_{page_id}.json"
        cached_data = get_cached_data(cache_filename)
        if cached_data is not None:
            return cached_data
        else:
            try:
                page = self.notion.pages.retrieve(page_id)
                save_cached_data(cache_filename, page)
                return page
            except requests.exceptions.RequestException as e:
                print(f"Network error downloading related page {page_id}: {e}")
                return None
            except Exception as e:
                print(f"Unexpected error downloading related page {page_id}: {e}")
                return None

    def download_related_database_data(self, database_id):
        """Download data from a Notion database (with caching) for relations."""
        cache_filename = f"related_database_{database_id}.json"
        cached_data = get_cached_data(cache_filename)
        if cached_data is not None:
            return cached_data
        else:
            try:
                database = self.notion.databases.retrieve(database_id)
                save_cached_data(cache_filename, database)
                return database
            except requests.exceptions.RequestException as e:
                print(f"Network error downloading related database {database_id}: {e}")
                return None
            except Exception as e:
                print(f"Unexpected error downloading related database {database_id}: {e}")
                return None
