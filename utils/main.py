"""
Modulo principale per l'orchestrazione del processo di download e conversione.
"""

import os
from rich.console import Console
from slugify import slugify

from .config import OUTPUT_DIR, load_config, ensure_directories
from .notion_client import NotionDownloader
from .markdown_converter import convert_page_to_markdown, convert_database_to_markdown
from .link_processor import update_all_markdown_links

console = Console()


def download_page(downloader, page_id, output_dir):
    """Scarica una pagina Notion e i suoi blocchi."""
    page_data = downloader.download_page_data(page_id)
    if not page_data:
        return None, None

    blocks = downloader.download_page_blocks(page_id)
    return convert_page_to_markdown(page_data, blocks, output_dir)


def download_database(downloader, database_id, output_dir):
    """Scarica un database Notion come tabella Markdown."""
    database_data = downloader.download_database_data(database_id)
    if not database_data:
        return None, None

    results = downloader.download_database_query(database_id)
    return convert_database_to_markdown(database_data, results, downloader, output_dir)


def process_page_or_database(downloader, block_id, output_dir, processed_items):
    """Processa una pagina o un database, scaricandone il contenuto."""
    if block_id in processed_items:
        console.print(f"Blocco [bold yellow]{block_id}[/bold yellow] già processato.")
        return processed_items[block_id]  # Restituisci le informazioni già presenti

    block = downloader.download_block(block_id)
    if not block:
        return None
    block_type = block.get("type")
    item_info = None

    if block_type == "child_page":
        page_id = block["id"]
        title = block.get('child_page', {}).get('title', 'Untitled')
        console.print(f"Trovata pagina: [bold blue]{title}[/bold blue] ({page_id})")
        slug, _ = download_page(downloader, page_id, output_dir)
        item_info = {"type": "page", "id": page_id, "slug": slug, "title": title}
    elif block_type == "child_database":
        database_id = block["id"]
        title = block.get('child_database', {}).get('title', 'Untitled')
        console.print(f"Trovato database: [bold green]{title}[/bold green] ({database_id})")
        slug, _ = download_database(downloader, database_id, output_dir)
        item_info = {"type": "database", "id": database_id, "slug": slug, "title": title}

    if item_info:
        processed_items[item_info["id"]] = item_info  # Memorizza l'elemento processato
        return item_info
    return None


def recursively_process_blocks(downloader, parent_block_id, current_output_dir, processed_items, level=0):
    """Processa ricorsivamente tutti i blocchi di una pagina."""
    blocks = downloader.download_page_blocks(parent_block_id)
    if not blocks:
        return
        
    for block in blocks:
        item_info = process_page_or_database(downloader, block["id"], current_output_dir, processed_items)
        if item_info:
            processed_items[item_info["id"]] = item_info
        if block.get("has_children"):
            recursively_process_blocks(downloader, block["id"], current_output_dir, processed_items, level + 1)


def main():
    """Funzione principale per scaricare i contenuti di Notion."""
    # Carica configurazione
    notion_token, root_page_id = load_config()
    
    # Assicura che le directory esistano
    ensure_directories()
    
    # Inizializza downloader
    downloader = NotionDownloader(notion_token)
    
    # Inizializza strutture dati
    processed_items = {}

    console.print(f"[bold magenta]Inizio download da Notion...[/bold magenta]")
    recursively_process_blocks(downloader, root_page_id, OUTPUT_DIR, processed_items)
    console.print(f"[bold green]Download completato. File salvati in '{OUTPUT_DIR}'[/bold green]")

    # Aggiorna i link Markdown
    console.print("[yellow]Creazione dei link Markdown...[/yellow]")
    update_all_markdown_links(OUTPUT_DIR, processed_items)
    console.print("[green]Link Markdown aggiornati![/green]")


if __name__ == "__main__":
    main()
