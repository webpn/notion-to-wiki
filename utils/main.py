"""
Modulo principale per l'orchestrazione del processo di download e conversione.
"""

import os
from rich.console import Console
from slugify import slugify

from .config import OUTPUT_DIR, load_config, ensure_directories
from .notion_client import NotionDownloader
from .markdown_converter import convert_page_to_markdown, convert_database_to_markdown, convert_block_to_markdown
from .link_processor import update_all_markdown_links

console = Console()


def download_page_data(downloader, page_id):
    """Scarica i dati di una pagina Notion senza convertirli."""
    page_data = downloader.download_page_data(page_id)
    if not page_data:
        return None

    blocks = downloader.download_page_blocks(page_id)
    return {"page_data": page_data, "blocks": blocks}


def download_database_data(downloader, database_id):
    """Scarica i dati di un database Notion senza convertirli."""
    database_data = downloader.download_database_data(database_id)
    if not database_data:
        return None

    results = downloader.download_database_query(database_id)
    
    # Scarica anche tutti i record come "pagine" per risolvere le relazioni
    records = {}
    if results:
        for record in results:
            record_id = record["id"]
            # Scarica anche i blocchi figli del record
            record_blocks = downloader.download_page_blocks(record_id)
            records[record_id] = {
                "record_data": record,
                "blocks": record_blocks
            }
    
    return {"database_data": database_data, "results": results, "records": records}


def collect_related_databases(downloader, database_id, collected_items):
    """Raccoglie i database referenziati dalle proprietà relation di un database."""
    database_data = downloader.download_database_data(database_id)
    if not database_data:
        return
    
    properties = database_data.get('properties', {})
    for prop_name, prop_data in properties.items():
        if prop_data.get('type') == 'relation':
            relation_config = prop_data.get('relation', {})
            related_db_id = relation_config.get('database_id')
            
            if related_db_id and related_db_id not in collected_items:
                # Raccoglie il database referenziato
                related_db_data = downloader.download_database_data(related_db_id)
                if related_db_data:
                    title = related_db_data.get("title", [{}])[0].get("plain_text", "Untitled Database")
                    console.print(f"  → Database correlato: [bold cyan]{title}[/bold cyan] ({related_db_id})")
                    item_info = {"type": "database", "id": related_db_id, "title": title}
                    collected_items[related_db_id] = item_info
                    
                    # Ricorsivamente raccoglie anche i database referenziati da questo database
                    collect_related_databases(downloader, related_db_id, collected_items)


def collect_page_or_database_info(downloader, block_id, collected_items):
    """Raccoglie informazioni su una pagina o un database senza scaricare i contenuti."""
    if block_id in collected_items:
        console.print(f"Blocco [bold yellow]{block_id}[/bold yellow] già raccolto.")
        return collected_items[block_id]

    block = downloader.download_block(block_id)
    if not block:
        return None
    
    block_type = block.get("type")
    item_info = None

    if block_type == "child_page":
        title = block.get('child_page', {}).get('title', 'Untitled')
        console.print(f"Trovata pagina: [bold blue]{title}[/bold blue] ({block_id})")
        item_info = {"type": "page", "id": block_id, "title": title}
    elif block_type == "child_database":
        title = block.get('child_database', {}).get('title', 'Untitled')
        console.print(f"Trovato database: [bold green]{title}[/bold green] ({block_id})")
        item_info = {"type": "database", "id": block_id, "title": title}
        
        # Raccoglie anche i database referenziati da questo database
        collect_related_databases(downloader, block_id, collected_items)

    if item_info:
        collected_items[item_info["id"]] = item_info
        return item_info
    return None
    """Raccoglie informazioni su una pagina o un database senza scaricare i contenuti."""
    if block_id in collected_items:
        console.print(f"Blocco [bold yellow]{block_id}[/bold yellow] già raccolto.")
        return collected_items[block_id]

    block = downloader.download_block(block_id)
    if not block:
        return None
    
    block_type = block.get("type")
    item_info = None

    if block_type == "child_page":
        title = block.get('child_page', {}).get('title', 'Untitled')
        console.print(f"Trovata pagina: [bold blue]{title}[/bold blue] ({block_id})")
        item_info = {"type": "page", "id": block_id, "title": title}
    elif block_type == "child_database":
        title = block.get('child_database', {}).get('title', 'Untitled')
        console.print(f"Trovato database: [bold green]{title}[/bold green] ({block_id})")
        item_info = {"type": "database", "id": block_id, "title": title}

    if item_info:
        collected_items[item_info["id"]] = item_info
        return item_info
    return None


def recursively_collect_items(downloader, parent_block_id, collected_items, level=0):
    """Raccoglie ricorsivamente tutti gli elementi (pagine e database) senza scaricare i contenuti."""
    blocks = downloader.download_page_blocks(parent_block_id)
    if not blocks:
        return
        
    for block in blocks:
        item_info = collect_page_or_database_info(downloader, block["id"], collected_items)
        if item_info:
            collected_items[item_info["id"]] = item_info
        if block.get("has_children"):
            recursively_collect_items(downloader, block["id"], collected_items, level + 1)


def main():
    """Funzione principale per scaricare i contenuti di Notion."""
    # Carica configurazione
    notion_token, root_page_id = load_config()
    
    # Assicura che le directory esistano
    ensure_directories()
    
    # Inizializza downloader
    downloader = NotionDownloader(notion_token)
    
    # FASE 1: Raccolta di tutti gli elementi
    console.print(f"[bold cyan]FASE 1: Raccolta informazioni da Notion...[/bold cyan]")
    collected_items = {}
    recursively_collect_items(downloader, root_page_id, collected_items)
    
    console.print(f"[bold yellow]Trovati {len(collected_items)} elementi totali[/bold yellow]")
    
    # FASE 2: Download di tutti i dati
    console.print(f"[bold cyan]FASE 2: Download dati completi...[/bold cyan]")
    all_data = {}
    all_records = {}  # Dizionario separato per tutti i record dei database
    
    for item_id, item_info in collected_items.items():
        if item_info["type"] == "page":
            console.print(f"Scaricando pagina: [bold blue]{item_info['title']}[/bold blue]")
            page_data = download_page_data(downloader, item_id)
            if page_data:
                all_data[item_id] = {"info": item_info, "data": page_data}
        elif item_info["type"] == "database":
            console.print(f"Scaricando database: [bold green]{item_info['title']}[/bold green]")
            db_data = download_database_data(downloader, item_id)
            if db_data:
                all_data[item_id] = {"info": item_info, "data": db_data}
                
                # Aggiungi tutti i record al dizionario globale per le relazioni
                for record_id, record_entry in db_data["records"].items():
                    record_data = record_entry["record_data"]
                    # Estrai il titolo del record (concatenando tutti i plain_text)
                    record_title = "Untitled Record"
                    properties = record_data.get("properties", {})
                    for prop_name, prop_data in properties.items():
                        if prop_data.get("type") == "title":
                            title_array = prop_data.get("title", [])
                            if title_array:
                                # Concatena tutti i plain_text degli elementi nell'array
                                record_title = "".join([item.get("plain_text", "") for item in title_array])
                                if not record_title.strip():
                                    record_title = "Untitled Record"
                                break
                    
                    all_records[record_id] = {
                        "title": record_title,
                        "database_title": item_info['title'],
                        "database_id": item_id,
                        "blocks": record_entry["blocks"]
                    }
                    console.print(f"  → Record: [dim]{record_title}[/dim]")
    
    console.print(f"[bold yellow]Raccolti {len(all_records)} record totali da tutti i database[/bold yellow]")
    
    # FASE 3: Conversione in Markdown
    console.print(f"[bold cyan]FASE 3: Conversione in Markdown...[/bold cyan]")
    processed_items = {}
    
    for item_id, item_entry in all_data.items():
        item_info = item_entry["info"]
        item_data = item_entry["data"]
        
        if item_info["type"] == "page":
            console.print(f"Convertendo pagina: [bold blue]{item_info['title']}[/bold blue]")
            slug, title = convert_page_to_markdown(
                item_data["page_data"], 
                item_data["blocks"], 
                OUTPUT_DIR
            )
            processed_items[item_id] = {
                "type": "page", 
                "id": item_id, 
                "slug": slug, 
                "title": title
            }
        elif item_info["type"] == "database":
            console.print(f"Convertendo database: [bold green]{item_info['title']}[/bold green]")
            slug, title = convert_database_to_markdown(
                item_data["database_data"], 
                item_data["results"], 
                all_data,
                all_records,
                downloader, 
                OUTPUT_DIR
            )
            processed_items[item_id] = {
                "type": "database", 
                "id": item_id, 
                "slug": slug, 
                "title": title
            }

    console.print(f"[bold green]Download completato. File salvati in '{OUTPUT_DIR}'[/bold green]")

    # FASE 4: Conversione dei record dei database in sottopagine
    console.print(f"[bold cyan]FASE 4: Creazione sottopagine per record database...[/bold cyan]")
    for record_id, record_info in all_records.items():
        if record_info.get("blocks"):
            # Crea una sottopagina per ogni record con contenuto
            database_slug = slugify(record_info["database_title"])
            record_slug = slugify(record_info["title"])
            
            # Crea la directory del database se non esiste
            db_dir = os.path.join(OUTPUT_DIR, database_slug)
            os.makedirs(db_dir, exist_ok=True)
            
            # Crea il file per il record
            record_file = os.path.join(db_dir, f"{record_slug}.md")
            
            content = f"# {record_info['title']}\n\n"
            content += f"*Record del database: [{record_info['database_title']}]({database_slug}.md)*\n\n"
            
            # Converti i blocchi in markdown
            for block in record_info["blocks"]:
                markdown_block = convert_block_to_markdown(block)
                if markdown_block:
                    content += markdown_block + "\n\n"
            
            with open(record_file, "w", encoding="utf-8") as f:
                f.write(content)
            
            console.print(f"  → Sottopagina: [dim]{record_info['database_title']}/{record_info['title']}[/dim]")

    # Aggiorna i link Markdown
    console.print("[yellow]Creazione dei link Markdown...[/yellow]")
    update_all_markdown_links(OUTPUT_DIR, processed_items)
    console.print("[green]Link Markdown aggiornati![/green]")


if __name__ == "__main__":
    main()
