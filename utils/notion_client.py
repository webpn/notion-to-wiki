"""
Modulo per il download dei contenuti da Notion tramite API.
"""

import requests
from notion_client import Client
from rich.console import Console
from .cache import get_cached_data, save_cached_data

console = Console()


class NotionDownloader:
    """Classe per gestire il download di contenuti da Notion."""
    
    def __init__(self, notion_token):
        """Inizializza il client Notion."""
        self.notion = Client(auth=notion_token)
    
    def download_block(self, block_id):
        """Scarica un blocco Notion e lo converte in Markdown."""
        cache_filename = f"block_{block_id}.json"
        cached_data = get_cached_data(cache_filename)
        if cached_data:
            return cached_data
        else:
            try:
                block = self.notion.blocks.retrieve(block_id)
                save_cached_data(cache_filename, block)
                return block
            except requests.exceptions.RequestException as e:
                console.print(f"[bold red]Errore di rete durante il download del blocco {block_id}:[/bold red] {e}")
                return None
            except Exception as e:
                console.print(f"[bold red]Errore imprevisto durante il download del blocco {block_id}:[/bold red] {e}")
                return None

    def download_page_data(self, page_id):
        """Scarica i dati di una pagina Notion."""
        cache_filename = f"page_{page_id}.json"
        cached_data = get_cached_data(cache_filename)
        if cached_data:
            return cached_data
        else:
            try:
                page = self.notion.pages.retrieve(page_id)
                save_cached_data(cache_filename, page)
                return page
            except requests.exceptions.RequestException as e:
                console.print(f"[bold red]Errore di rete durante il download della pagina {page_id}:[/bold red] {e}")
                return None
            except Exception as e:
                console.print(f"[bold red]Errore imprevisto durante il download della pagina {page_id}:[/bold red] {e}")
                return None

    def download_page_blocks(self, page_id):
        """Scarica i blocchi di una pagina Notion (con caching)."""
        cache_filename = f"page_blocks_{page_id}.json"
        cached_data = get_cached_data(cache_filename)
        if cached_data:
            return cached_data
        else:
            try:
                blocks = self.notion.blocks.children.list(block_id=page_id).get("results")
                save_cached_data(cache_filename, blocks)
                return blocks
            except requests.exceptions.RequestException as e:
                console.print(f"[bold red]Errore di rete durante il download dei blocchi della pagina {page_id}:[/bold red] {e}")
                return None
            except Exception as e:
                console.print(f"[bold red]Errore imprevisto durante il download dei blocchi della pagina {page_id}:[/bold red] {e}")
                return None

    def download_database_data(self, database_id):
        """Scarica i dati di un database Notion."""
        cache_filename = f"database_{database_id}.json"
        cached_data = get_cached_data(cache_filename)
        if cached_data:
            return cached_data
        else:
            try:
                database = self.notion.databases.retrieve(database_id)
                save_cached_data(cache_filename, database)
                return database
            except requests.exceptions.RequestException as e:
                console.print(f"[bold red]Errore di rete durante il download del database {database_id}:[/bold red] {e}")
                return None
            except Exception as e:
                console.print(f"[bold red]Errore imprevisto durante il download del database {database_id}:[/bold red] {e}")
                return None

    def download_database_query(self, database_id):
        """Scarica i risultati di una query del database Notion (con caching)."""
        cache_filename = f"database_query_{database_id}.json"
        cached_data = get_cached_data(cache_filename)
        if cached_data:
            return cached_data
        else:
            try:
                results = self.notion.databases.query(database_id=database_id).get("results")
                save_cached_data(cache_filename, results)
                return results
            except requests.exceptions.RequestException as e:
                console.print(f"[bold red]Errore di rete durante la query del database {database_id}:[/bold red] {e}")
                return None
            except Exception as e:
                console.print(f"[bold red]Errore imprevisto durante la query del database {database_id}:[/bold red] {e}")
                return None

    def download_related_page_data(self, page_id):
        """Scarica i dati di una pagina Notion (con caching) per le relazioni."""
        cache_filename = f"related_page_{page_id}.json"
        cached_data = get_cached_data(cache_filename)
        if cached_data:
            return cached_data
        else:
            try:
                page = self.notion.pages.retrieve(page_id)
                save_cached_data(cache_filename, page)
                return page
            except requests.exceptions.RequestException as e:
                print(f"Errore di rete durante il download della pagina correlata {page_id}: {e}")
                return None
            except Exception as e:
                print(f"Errore imprevisto durante il download della pagina correlata {page_id}: {e}")
                return None

    def download_related_database_data(self, database_id):
        """Scarica i dati di un database Notion (con caching) per le relazioni."""
        cache_filename = f"related_database_{database_id}.json"
        cached_data = get_cached_data(cache_filename)
        if cached_data:
            return cached_data
        else:
            try:
                database = self.notion.databases.retrieve(database_id)
                save_cached_data(cache_filename, database)
                return database
            except requests.exceptions.RequestException as e:
                print(f"Errore di rete durante il download del database correlato {database_id}: {e}")
                return None
            except Exception as e:
                print(f"Errore imprevisto durante il download del database correlato {database_id}: {e}")
                return None
