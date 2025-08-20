"""
Main module for orchestrating the download and conversion process.
"""

import os
import sys
from rich.console import Console
from slugify import slugify

from .config import OUTPUT_DIR, load_config, ensure_directories
from .notion_client import NotionDownloader
from .markdown_converter import convert_page_to_markdown, convert_database_to_markdown, convert_block_to_markdown
from .link_processor import update_all_markdown_links
from .exceptions import ConfigurationError, NotionAPIError

console = Console()


def download_page_data(downloader, page_id):
    """Download data from a Notion page without converting it."""
    page_data = downloader.download_page_data(page_id)
    if not page_data:
        return None

    blocks = downloader.download_page_blocks(page_id)
    return {"page_data": page_data, "blocks": blocks}


def download_database_data(downloader, database_id):
    """Download data from a Notion database without converting it."""
    database_data = downloader.download_database_data(database_id)
    if not database_data:
        return None

    results = downloader.download_database_query(database_id)
    
    # Also download all records as "pages" to resolve relations
    records = {}
    if results:
        for record in results:
            record_id = record["id"]
            # Also download child blocks of the record
            record_blocks = downloader.download_page_blocks(record_id)
            records[record_id] = {
                "record_data": record,
                "blocks": record_blocks
            }
    
    return {"database_data": database_data, "results": results, "records": records}


def collect_related_databases(downloader, database_id, collected_items):
    """Collect databases referenced by relation properties of a database."""
    database_data = downloader.download_database_data(database_id)
    if not database_data:
        return
    
    properties = database_data.get('properties', {})
    for prop_name, prop_data in properties.items():
        if prop_data.get('type') == 'relation':
            relation_config = prop_data.get('relation', {})
            related_db_id = relation_config.get('database_id')
            
            if related_db_id and related_db_id not in collected_items:
                # Collect the referenced database
                related_db_data = downloader.download_database_data(related_db_id)
                if related_db_data:
                    title = related_db_data.get("title", [{}])[0].get("plain_text", "Untitled Database")
                    console.print(f"  → Related database: [bold cyan]{title}[/bold cyan] ({related_db_id})")
                    item_info = {"type": "database", "id": related_db_id, "title": title}
                    collected_items[related_db_id] = item_info
                    
                    # Recursively collect databases referenced by this database
                    collect_related_databases(downloader, related_db_id, collected_items)


def collect_page_or_database_info(downloader, block_id, collected_items, parent_id=None):
    """Collect information about a page or database without downloading the content."""
    if block_id in collected_items:
        # If the element already exists but with parent_id=None and we now have a parent_id,
        # update the parent_id (case of related databases found later as children)
        existing_item = collected_items[block_id]
        if parent_id and not existing_item.get("parent_id"):
            existing_item["parent_id"] = parent_id
            console.print(f"Updated parent for [bold yellow]{existing_item['title']}[/bold yellow] -> parent: {parent_id}")
        return existing_item

    block = downloader.download_block(block_id)
    if not block:
        return None
    
    block_type = block.get("type")
    item_info = None

    if block_type == "child_page":
        title = block.get('child_page', {}).get('title', 'Untitled')
        console.print(f"Found page: [bold blue]{title}[/bold blue] ({block_id})")
        item_info = {"type": "page", "id": block_id, "title": title, "parent_id": parent_id}
    elif block_type == "child_database":
        title = block.get('child_database', {}).get('title', 'Untitled')
        console.print(f"Found database: [bold green]{title}[/bold green] ({block_id})")
        item_info = {"type": "database", "id": block_id, "title": title, "parent_id": parent_id}
        
        # Also collect databases referenced by this database
        collect_related_databases(downloader, block_id, collected_items)

    if item_info:
        collected_items[item_info["id"]] = item_info
        return item_info
    return None


def recursively_collect_items(downloader, parent_block_id, collected_items, level=0):
    """Recursively collect all items (pages and databases) without downloading content."""
    # First add the parent_block_id itself if not already present
    if parent_block_id not in collected_items:
        # For root, parent_id is None
        parent_info = collect_page_or_database_info(downloader, parent_block_id, collected_items, parent_id=None if level == 0 else None)
        if parent_info:
            collected_items[parent_info["id"]] = parent_info
    
    # Then download child blocks and process recursively
    blocks = downloader.download_page_blocks(parent_block_id)
    if not blocks:
        return
        
    for block in blocks:
        item_info = collect_page_or_database_info(downloader, block["id"], collected_items, parent_id=parent_block_id)
        if item_info:
            collected_items[item_info["id"]] = item_info
        if block.get("has_children"):
            recursively_collect_items(downloader, block["id"], collected_items, level + 1)


def build_item_path(item_id, collected_items, root_page_id=None):
    """Build the hierarchical path of an item based on its parents (excluding the item itself)."""
    # If the item is the root, return empty path
    if item_id == root_page_id:
        return ""
    
    path_parts = []
    current_id = item_id
    
    # Start from the item's parent, not the item itself
    if current_id in collected_items:
        current_item = collected_items[current_id]
        current_id = current_item.get("parent_id")
    
    # Build path by going up the hierarchy
    while current_id and current_id in collected_items:
        current_item = collected_items[current_id]
        # Don't add the root to the path
        if current_item.get("parent_id") or current_id != root_page_id:
            if current_id != root_page_id:  # Exclude root from path
                path_parts.insert(0, slugify(current_item["title"]))
        current_id = current_item.get("parent_id")
    
    return "/".join(path_parts) if path_parts else ""


def build_reverse_references(all_data, all_records):
    """Build a mapping of which records reference each record."""
    reverse_refs = {}  # record_id -> list of {source_record_id, source_database_title, source_record_title, property_name}
    
    # Go through all database records and their properties
    for source_record_id, source_record_info in all_records.items():
        source_database_id = source_record_info["database_id"]
        source_database_title = source_record_info["database_title"]
        source_record_title = source_record_info["title"]
        
        # Get the database structure to find relation properties
        if source_database_id in all_data:
            db_data = all_data[source_database_id]["data"]
            database_data = db_data["database_data"]
            properties = database_data.get('properties', {})
            
            # Get the record data to find actual relations
            records = db_data["records"]
            if source_record_id in records:
                record_entry = records[source_record_id]
                record_data = record_entry["record_data"]
                record_properties = record_data.get("properties", {})
                
                # Look for relation properties
                for prop_name, prop_data in properties.items():
                    if prop_data.get('type') == 'relation':
                        # Check if this record has values for this relation property
                        if prop_name in record_properties:
                            property_value = record_properties[prop_name]
                            relation_values = property_value.get('relation', [])
                            
                            # For each referenced record, add this as a reverse reference
                            for relation_item in relation_values:
                                target_record_id = relation_item['id']
                                
                                if target_record_id not in reverse_refs:
                                    reverse_refs[target_record_id] = []
                                
                                reverse_refs[target_record_id].append({
                                    'source_record_id': source_record_id,
                                    'source_database_title': source_database_title,
                                    'source_record_title': source_record_title,
                                    'property_name': prop_name
                                })
    
    return reverse_refs


def create_reverse_reference_table(record_id, reverse_refs, all_records, database_paths):
    """Create a markdown table for records that reference the given record."""
    if record_id not in reverse_refs:
        return ""
    
    references = reverse_refs[record_id]
    if not references:
        return ""
    
    # Group by source database
    by_database = {}
    for ref in references:
        db_title = ref['source_database_title']
        if db_title not in by_database:
            by_database[db_title] = []
        by_database[db_title].append(ref)
    
    markdown = ""
    for db_title, refs in by_database.items():
        markdown += f"\n## Referenced by {db_title}\n\n"
        markdown += "| Record | Property |\n"
        markdown += "|--------|----------|\n"
        
        for ref in refs:
            source_record_title = ref['source_record_title']
            property_name = ref['property_name']
            source_record_id = ref['source_record_id']
            
            # Find the database path for the source record
            source_database_id = None
            source_record_has_blocks = False
            for record_info in all_records.values():
                if record_info.get('title') == source_record_title and record_info.get('database_title') == db_title:
                    source_database_id = record_info.get('database_id')
                    source_record_has_blocks = bool(record_info.get('blocks'))
                    break
            
            # Get the correct database path
            if source_database_id and source_database_id in database_paths:
                source_database_path = database_paths[source_database_id]
            else:
                source_database_path = slugify(db_title)
            
            # Create link - either to individual record page or to database table
            if source_record_has_blocks:
                # Link to individual record page
                source_record_slug = slugify(source_record_title)
                record_link = f"[{source_record_title}](../{source_database_path}/{source_record_slug}.md)"
            else:
                # Link to database table (record doesn't have its own page)
                record_link = f"[{source_record_title}](../{source_database_path}.md)"
            
            markdown += f"| {record_link} | {property_name} |\n"
        
        markdown += "\n"
    
    return markdown


def main():
    """Main function for downloading Notion content."""
    try:
        # Load configuration
        notion_token, root_page_id = load_config()
        
        # Ensure directories exist
        ensure_directories()
        
        # Initialize downloader
        downloader = NotionDownloader(notion_token)
        
        # PHASE 1: Collect all items
        console.print(f"[bold cyan]PHASE 1: Collecting information from Notion...[/bold cyan]")
        collected_items = {}
        recursively_collect_items(downloader, root_page_id, collected_items)
        
        console.print(f"[bold yellow]Found {len(collected_items)} total items[/bold yellow]")
        
        # PHASE 2: Download all data
        console.print(f"[bold cyan]PHASE 2: Downloading complete data...[/bold cyan]")
        all_data = {}
        all_records = {}  # Separate dictionary for all database records
        
        for item_id, item_info in collected_items.items():
            if item_info["type"] == "page":
                console.print(f"Downloading page: [bold blue]{item_info['title']}[/bold blue]")
                page_data = download_page_data(downloader, item_id)
                if page_data:
                    all_data[item_id] = {"info": item_info, "data": page_data}
            elif item_info["type"] == "database":
                console.print(f"Downloading database: [bold green]{item_info['title']}[/bold green]")
                db_data = download_database_data(downloader, item_id)
                if db_data:
                    all_data[item_id] = {"info": item_info, "data": db_data}
                    
                    # Add all records to global dictionary for relations
                    for record_id, record_entry in db_data["records"].items():
                        record_data = record_entry["record_data"]
                        # Extract record title (concatenating all plain_text)
                        record_title = "Untitled Record"
                        properties = record_data.get("properties", {})
                        for prop_name, prop_data in properties.items():
                            if prop_data.get("type") == "title":
                                title_array = prop_data.get("title", [])
                                if title_array:
                                    # Concatenate all plain_text elements in the array
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
        
        console.print(f"[bold yellow]Collected {len(all_records)} total records from all databases[/bold yellow]")
        
        # Build reverse references
        console.print("[yellow]Building reverse references...[/yellow]")
        reverse_refs = build_reverse_references(all_data, all_records)
        console.print(f"[yellow]Found reverse references for {len(reverse_refs)} records[/yellow]")
        
        # PHASE 3: Convert to Markdown
        console.print(f"[bold cyan]PHASE 3: Converting to Markdown...[/bold cyan]")
        processed_items = {}
        
        for item_id, item_entry in all_data.items():
            item_info = item_entry["info"]
            item_data = item_entry["data"]
            
            if item_info["type"] == "page":
                console.print(f"Converting page: [bold blue]{item_info['title']}[/bold blue]")
                item_path = build_item_path(item_id, collected_items, root_page_id)
                is_root = (item_id == root_page_id)
                relative_path, title = convert_page_to_markdown(
                    item_data["page_data"], 
                    item_data["blocks"], 
                    OUTPUT_DIR,
                    item_path,
                    is_root
                )
                processed_items[item_id] = {
                    "type": "page", 
                    "id": item_id, 
                    "slug": relative_path, 
                    "title": title
                }
            elif item_info["type"] == "database":
                console.print(f"Converting database: [bold green]{item_info['title']}[/bold green]")
                item_path = build_item_path(item_id, collected_items, root_page_id)
                relative_path, title = convert_database_to_markdown(
                    item_data["database_data"], 
                    item_data["results"], 
                    all_data,
                    all_records,
                    downloader, 
                    OUTPUT_DIR,
                    item_path
                )
                processed_items[item_id] = {
                    "type": "database", 
                    "id": item_id, 
                    "slug": relative_path, 
                    "title": title
                }

        console.print(f"[bold green]Download completed. Files saved in '{OUTPUT_DIR}'[/bold green]")

        # PHASE 4: Convert database records to subpages
        console.print(f"[bold cyan]PHASE 4: Creating subpages for database records...[/bold cyan]")
        
        # Create database_id -> path mapping for correct references
        database_paths = {}
        for item_id, item_data in processed_items.items():
            if item_data["type"] == "database":
                database_paths[item_id] = item_data["slug"]
        
        for record_id, record_info in all_records.items():
            if record_info.get("blocks"):
                # Find the parent database path
                database_id = record_info["database_id"]
                database_path = database_paths.get(database_id, slugify(record_info["database_title"]))
                
                record_slug = slugify(record_info["title"])
                
                # Use the hierarchical path of the database
                if "/" in database_path:
                    # Database has a hierarchical path
                    db_dir = os.path.join(OUTPUT_DIR, database_path)
                else:
                    # Database in root
                    db_dir = os.path.join(OUTPUT_DIR, database_path)
                
                os.makedirs(db_dir, exist_ok=True)
                
                # Create the file for the record
                record_file = os.path.join(db_dir, f"{record_slug}.md")
                
                content = f"# {record_info['title']}\n\n"
                content += f"*Database record: [{record_info['database_title']}]({database_path}.md)*\n\n"
                
                # Convert blocks to markdown
                for block in record_info["blocks"]:
                    markdown_block = convert_block_to_markdown(block)
                    if markdown_block:
                        content += markdown_block + "\n\n"
                
                # Add reverse reference tables
                reverse_ref_table = create_reverse_reference_table(record_id, reverse_refs, all_records, database_paths)
                if reverse_ref_table:
                    content += reverse_ref_table
                
                with open(record_file, "w", encoding="utf-8") as f:
                    f.write(content)
                
                console.print(f"  → Subpage: [dim]{record_info['database_title']}/{record_info['title']}[/dim]")

        # Update Markdown links
        console.print("[yellow]Creating Markdown links...[/yellow]")
        update_all_markdown_links(OUTPUT_DIR, processed_items)
        console.print("[green]Markdown links updated![/green]")

    except ConfigurationError as e:
        console.print(f"[bold red]Configuration Error:[/bold red] {e}")
        sys.exit(1)
    except NotionAPIError as e:
        console.print(f"[bold red]Notion API Error:[/bold red] {e}")
        sys.exit(1)
    except Exception as e:
        console.print(f"[bold red]Unexpected Error:[/bold red] {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
