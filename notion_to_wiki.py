import os
import json
import requests
import re

from notion_client import Client
from slugify import slugify
from rich.console import Console
from rich.progress import track

# --- Configurazione ---
CONFIG_FILE = "config.json"
OUTPUT_DIR = "notion_wiki"
CACHE_DIR = "_notion_cache"
USE_CACHE = True  # Imposta a False per forzare il download da Notion

console = Console()

# Carica la configurazione dal file JSON
try:
    with open(CONFIG_FILE, "r") as f:
        config = json.load(f)
        NOTION_TOKEN = config.get("notion_token")
        ROOT_PAGE_ID = config.get("root_page_id")
except FileNotFoundError:
    console.print(f"[bold red]Errore:[/bold red] File di configurazione '{CONFIG_FILE}' non trovato.")
    exit()
except json.JSONDecodeError:
    console.print(f"[bold red]Errore:[/bold red] Impossibile decodificare il file JSON '{CONFIG_FILE}'.")
    exit()
except KeyError as e:
    console.print(f"[bold red]Errore:[/bold red] Chiave mancante nel file di configurazione: {e}")
    exit()

if not NOTION_TOKEN or not ROOT_PAGE_ID:
    console.print("[bold red]Errore:[/bold red] Token Notion o ID pagina radice non configurati correttamente nel file JSON.")
    exit()

notion = Client(auth=NOTION_TOKEN)

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

def download_block(block_id):
    """Scarica un blocco Notion e lo converte in Markdown."""
    cache_filename = f"block_{block_id}.json"
    cached_data = get_cached_data(cache_filename)
    if cached_data:
        return cached_data
    else:
        try:
            block = notion.blocks.retrieve(block_id)
            save_cached_data(cache_filename, block)
            return block
        except requests.exceptions.RequestException as e:
            console.print(f"[bold red]Errore di rete durante il download del blocco {block_id}:[/bold red] {e}")
            return None
        except Exception as e:
            console.print(f"[bold red]Errore imprevisto durante il download del blocco {block_id}:[/bold red] {e}")
            return None

def download_page_data(page_id):
    """Scarica i dati di una pagina Notion."""
    cache_filename = f"page_{page_id}.json"
    cached_data = get_cached_data(cache_filename)
    if cached_data:
        return cached_data
    else:
        try:
            page = notion.pages.retrieve(page_id)
            save_cached_data(cache_filename, page)
            return page
        except requests.exceptions.RequestException as e:
            console.print(f"[bold red]Errore di rete durante il download della pagina {page_id}:[/bold red] {e}")
            return None
        except Exception as e:
            console.print(f"[bold red]Errore imprevisto durante il download della pagina {page_id}:[/bold red] {e}")
            return None

def download_page_blocks(page_id):
    """Scarica i blocchi di una pagina Notion (con caching)."""
    cache_filename = f"page_blocks_{page_id}.json"
    cached_data = get_cached_data(cache_filename)
    if cached_data:
        return cached_data
    else:
        try:
            blocks = notion.blocks.children.list(block_id=page_id).get("results")
            save_cached_data(cache_filename, blocks)
            return blocks
        except requests.exceptions.RequestException as e:
            console.print(f"[bold red]Errore di rete durante il download dei blocchi della pagina {page_id}:[/bold red] {e}")
            return None
        except Exception as e:
            console.print(f"[bold red]Errore imprevisto durante il download dei blocchi della pagina {page_id}:[/bold red] {e}")
            return None

def download_database_data(database_id):
    """Scarica i dati di un database Notion ."""
    cache_filename = f"database_{database_id}.json"
    cached_data = get_cached_data(cache_filename)
    if cached_data:
        return cached_data
    else:
        try:
            database = notion.databases.retrieve(database_id)
            save_cached_data(cache_filename, database)
            return database
        except requests.exceptions.RequestException as e:
            console.print(f"[bold red]Errore di rete durante il download del database {database_id}:[/bold red] {e}")
            return None
        except Exception as e:
            console.print(f"[bold red]Errore imprevisto durante il download del database {database_id}:[/bold red] {e}")
            return None

def download_database_query(database_id):
    """Scarica i risultati di una query del database Notion (con caching)."""
    cache_filename = f"database_query_{database_id}.json"
    cached_data = get_cached_data(cache_filename)
    if cached_data:
        return cached_data
    else:
        try:
            results = notion.databases.query(database_id=database_id).get("results")
            save_cached_data(cache_filename, results)
            return results
        except requests.exceptions.RequestException as e:
            console.print(f"[bold red]Errore di rete durante la query del database {database_id}:[/bold red] {e}")
            return None
        except Exception as e:
            console.print(f"[bold red]Errore imprevisto durante la query del database {database_id}:[/bold red] {e}")
            return None

def download_page(page_id, output_dir):
    """Scarica una pagina Notion e i suoi blocchi."""
    page_data = download_page_data(page_id)
    if not page_data:
        return None, None
    title = page_data.get("properties", {}).get("title", {}).get("title", [{}])[0].get("plain_text", "Untitled")
    slug = slugify(title)
    page_dir = os.path.join(output_dir, slug)
    os.makedirs(page_dir, exist_ok=True)
    output_file = os.path.join(page_dir, "index.md")

    blocks = download_page_blocks(page_id)
    if not blocks:
        return slug, title

    all_markdown_content = f"# {title}\n\n"
    for block in blocks: # track(blocks, description=f"Scaricando blocchi di '{title}'"):
        markdown_block = convert_block_to_markdown(block)
        if markdown_block:
            all_markdown_content += markdown_block + "\n\n"

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(all_markdown_content)
    return slug, title

def download_related_page_data(page_id):
    """Scarica i dati di una pagina Notion (con caching) per le relazioni."""
    cache_filename = f"related_page_{page_id}.json"
    cached_data = get_cached_data(cache_filename)
    if cached_data:
        return cached_data
    else:
        try:
            page = notion.pages.retrieve(page_id)
            save_cached_data(cache_filename, page)
            return page
        except requests.exceptions.RequestException as e:
            print(f"Errore di rete durante il download della pagina correlata {page_id}: {e}")
            return None
        except Exception as e:
            print(f"Errore imprevisto durante il download della pagina correlata {page_id}: {e}")
            return None

def download_related_database_data(database_id):
    """Scarica i dati di un database Notion (con caching) per le relazioni."""
    cache_filename = f"related_database_{database_id}.json"
    cached_data = get_cached_data(cache_filename)
    if cached_data:
        return cached_data
    else:
        try:
            database = notion.databases.retrieve(database_id)
            save_cached_data(cache_filename, database)
            return database
        except requests.exceptions.RequestException as e:
            print(f"Errore di rete durante il download del database correlato {database_id}: {e}")
            return None
        except Exception as e:
            print(f"Errore imprevisto durante il download del database correlato {database_id}: {e}")
            return None

def download_database(database_id, output_dir):
    """Scarica un database Notion come tabella Markdown."""
    database_data = download_database_data(database_id)
    if not database_data:
        return None, None
    title = database_data.get("title", [{}])[0].get("plain_text", "Untitled Database")
    slug = slugify(title)
    output_file = os.path.join(output_dir, f"{slug}.md")

    results = download_database_query(database_id)
    markdown_table = f"# {title}\n\n"
    if results:
        # Estrai i nomi delle colonne dall'oggetto database_data['properties']
        columns = list(database_data['properties'].keys())
        markdown_table += "| " + " | ".join(columns) + " |\n"
        markdown_table += "| " + " | ".join(['---'] * len(columns)) + " |\n"

        for row in results:
            row_values = []
            for column in columns:
                property_value = row['properties'].get(column)
                if property_value:
                    data_type = property_value.get("type")

                    if data_type == 'title':
                        value = property_value.get('title', [])
                        row_values.append(value[0]['plain_text'] if value else '')
                    elif data_type == 'rich_text':
                        value = property_value.get('rich_text', [])
                        row_values.append("".join([text['plain_text'] for text in value]))
                    elif data_type == 'number':
                        row_values.append(str(property_value.get('number', '')))
                    elif data_type == 'select':
                        value = property_value.get('select')
                        row_values.append(value['name'] if value else '')
                    elif data_type == 'multi_select':
                        value = property_value.get('multi_select', [])
                        row_values.append(", ".join([item['name'] for item in value]))
                    elif data_type == 'date':
                        value = property_value.get('date')
                        row_values.append(value['start'] if value else '')
                    elif data_type == 'relation':
                        related_names = []
                        relation_values = property_value.get('relation', [])
                        for relation_item in relation_values:
                            related_id = relation_item['id']
                            related_page_data = download_related_page_data(related_id)
                            if related_page_data:
                                related_title_prop = related_page_data.get("properties", {}).get("title")
                                if related_title_prop and related_title_prop.get("type") == "title":
                                    related_title = related_title_prop.get("title", [{}])[0].get("plain_text", "Untitled")
                                    related_names.append(f"[{related_title}]({slugify(related_title)}/index.md)")
                                    continue # Passa alla prossima relazione

                            related_database_data = download_related_database_data(related_id)
                            if related_database_data:
                                related_db_title_prop = related_database_data.get("title", [{}])[0].get("plain_text", "Untitled Database")
                                related_names.append(f"[{related_db_title_prop}]({slugify(related_db_title_prop)}.md)")
                                continue # Passa alla prossima relazione

                            related_names.append(f"[ID non trovato: {related_id}]")
                            print(f"Errore nel recupero della relazione {related_id}")

                        row_values.append(", ".join(related_names))
                    elif data_type == 'checkbox':
                        row_values.append('X' if property_value.get('checkbox', False) else '')
                    elif data_type == 'url':
                        row_values.append(property_value.get('url', ''))
                    elif data_type == 'email':
                        row_values.append(property_value.get('email', ''))
                    elif data_type == 'phone_number':
                        row_values.append(property_value.get('phone_number', ''))
                    elif data_type == 'created_time':
                        row_values.append(property_value.get('created_time', ''))
                    elif data_type == 'last_edited_time':
                        row_values.append(property_value.get('last_edited_time', ''))
                    elif data_type == 'created_by':
                        value = property_value.get('created_by')
                        row_values.append(value['name'] if value else '')
                    elif data_type == 'last_edited_by':
                        value = property_value.get('last_edited_by')
                        row_values.append(value['name'] if value else '')
                    else:
                        data_type = list(property_value.keys())[0]
                        value = property_value.get(data_type)
                        row_values.append(str(value) if value is not None else '')
                else:
                    row_values.append('')
            markdown_table += "| " + " | ".join(row_values) + " |\n"

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(markdown_table)
    return slug, title


def convert_block_to_markdown(block):
    """Converte un singolo blocco Notion in Markdown."""
    block_type = block.get("type")
    if not block_type:
        return ""
    markdown = ""
    if block_type == "paragraph":
        markdown = "".join(text["plain_text"] for text in block["paragraph"].get("rich_text", []))
    elif block_type == "heading_1":
        markdown = "# " + "".join(text["plain_text"] for text in block["heading_1"].get("rich_text", []))
    elif block_type == "heading_2":
        markdown = "## " + "".join(text["plain_text"] for text in block["heading_2"].get("rich_text", []))
    elif block_type == "heading_3":
        markdown = "### " + "".join(text["plain_text"] for text in block["heading_3"].get("rich_text", []))
    elif block_type == "bulleted_list_item":
        markdown = "* " + "".join(text["plain_text"] for text in block["bulleted_list_item"].get("rich_text", []))
    elif block_type == "numbered_list_item":
        markdown = "1. " + "".join(text["plain_text"] for text in block["numbered_list_item"].get("rich_text", []))
    elif block_type == "quote":
        markdown = "> " + "".join(text["plain_text"] for text in block["quote"].get("rich_text", []))
    elif block_type == "code":
        language = block["code"].get("language", "")
        code_text = "".join(text["plain_text"] for text in block["code"].get("rich_text", []))
        markdown = f"```{language}\n{code_text}\n```"
    elif block_type == "divider":
        markdown = "---"
    elif block_type == "image":
        image_url = block["image"].get("file", {}).get("url") or block["image"].get("external", {}).get("url", "")
        caption = "".join(text["plain_text"] for text in block["image"].get("caption", []))
        markdown = f"![{caption}]({image_url})"
    elif block_type == "callout":
        emoji = block["callout"].get("icon", {}).get("emoji", "")
        text = "".join(text["plain_text"] for text in block["callout"].get("rich_text", []))
        markdown = f"> {emoji} {text}"
    elif block_type == "bookmark":
        url = block["bookmark"].get("url", "")
        caption = "".join(text["plain_text"] for text in block["bookmark"].get("caption", []))
        markdown = f"[{caption}]({url})" if caption else f"[{url}]({url})"
    elif block_type == "equation":
        expression = block["equation"].get("expression", "")
        markdown = rf'<span class="math-block">\n{expression}\n</span>'
    elif block_type == "file":
        file_url = block["file"].get("file", {}).get("url") or block["file"].get("external", {}).get("url", "")
        caption = "".join(text["plain_text"] for text in block["file"].get("caption", []))
        markdown = f"[{caption}]({file_url})" if caption else f"[Allegato]({file_url})"
    elif block_type == "child_page":
        title = block["child_page"]["title"]
        slug = slugify(title)
        markdown = f"[{title}]({slug}/index.md)"
    elif block_type == "child_database":
        title = block["child_database"]["title"]
        slug = slugify(title)
        markdown = f"[{title}]({slug}.md)"
    elif block_type == "relation":
        # Potrebbe essere necessario un approccio più complesso per i link a pagine correlate
        markdown = "[Relazione]"
    # ... (Aggiungi altri tipi di blocco se necessario) ...
    return markdown

def process_page_or_database(block_id, output_dir, processed_items):
    """Processa una pagina o un database, scaricandone il contenuto."""
    if block_id in processed_items:
        console.print(f"Blocco [bold yellow]{block_id}[/bold yellow] già processato.")
        return processed_items[block_id]  # Restituisci le informazioni già presenti

    block = download_block(block_id)
    if not block:
        return None
    block_type = block.get("type")
    item_info = None

    if block_type == "child_page":
        page_id = block["id"]
        title = block.get('child_page', {}).get('title', 'Untitled')
        console.print(f"Trovata pagina: [bold blue]{title}[/bold blue] ({page_id})")
        slug, _ = download_page(page_id, output_dir)
        item_info = {"type": "page", "id": page_id, "slug": slug, "title": title}
    elif block_type == "child_database":
        database_id = block["id"]
        title = block.get('child_database', {}).get('title', 'Untitled')
        console.print(f"Trovato database: [bold green]{title}[/bold green] ({database_id})")
        slug, _ = download_database(database_id, output_dir)
        item_info = {"type": "database", "id": database_id, "slug": slug, "title": title}

    if item_info:
        processed_items[item_info["id"]] = item_info  # Memorizza l'elemento processato
        return item_info
    return None

def update_markdown_links(filepath, processed_items):
    """Aggiorna i link interni di Notion nel file Markdown."""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
    except FileNotFoundError:
        print(f"Errore: File non trovato: {filepath}")
        return
    except Exception as e:
        print(f"Errore durante la lettura del file {filepath}: {e}")
        return

    updated_content = content

    # Pattern per trovare i link di Notion (sia URL completi che ID)
    notion_link_pattern = r"\[(.*?)\]\((?:https:\/\/www\.notion\.so\/([a-f0-9]{32})|([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}))\)"

    def replace_notion_link(match):
        link_text = match.group(1)
        notion_id_url = match.group(2)
        notion_id_dash = match.group(3)
        target_id = notion_id_url or notion_id_dash.replace('-', '') if notion_id_dash else notion_id_url

        if target_id and target_id in processed_items:
            target_item = processed_items[target_id]
            if target_item["type"] == "page":
                return f"[{link_text}]({target_item['slug']}/index.md)"
            elif target_item["type"] == "database":
                return f"[{link_text}]({target_item['slug']}.md)"
        return match.group(0)  # Se l'ID non è trovato, lascia il link originale

    updated_content = re.sub(notion_link_pattern, replace_notion_link, updated_content)

    # Pattern per trovare riferimenti a child_page e child_database (solo ID)
    child_block_pattern = r"\[(.*?)\]\(([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})\)"

    def replace_child_block_link(match):
        link_text = match.group(1)
        target_id_dash = match.group(2)
        target_id = target_id_dash.replace('-', '')

        if target_id and target_id in processed_items:
            target_item = processed_items[target_id]
            if target_item["type"] == "page":
                return f"[{link_text}]({target_item['slug']}/index.md)"
            elif target_item["type"] == "database":
                return f"[{link_text}]({target_item['slug']}.md)"
        return match.group(0)

    updated_content = re.sub(child_block_pattern, replace_child_block_link, updated_content)

    try:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(updated_content)
    except Exception as e:
        print(f"Errore durante la scrittura del file aggiornato {filepath}: {e}")

def main():
    """Funzione principale per scaricare i contenuti di Notion."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(CACHE_DIR, exist_ok=True)
    processed_items = {}

    def recursively_process_blocks(parent_block_id, current_output_dir, processed_items, level=0):
        blocks = download_page_blocks(parent_block_id)
        for block in blocks: #track(blocks, description=f"Scansionando livello {level}"):
            item_info = process_page_or_database(block["id"], current_output_dir, processed_items) # <--- Ora lo passiamo
            if item_info:
                processed_items[item_info["id"]] = item_info
            if block["has_children"]:
                recursively_process_blocks(block["id"], current_output_dir, processed_items, level + 1)

    console.print(f"[bold magenta]Inizio download da Notion...[/bold magenta]")
    recursively_process_blocks(ROOT_PAGE_ID, OUTPUT_DIR, processed_items) # <--- Aggiunto 'processed_items'
    console.print(f"[bold green]Download completato. File salvati in '{OUTPUT_DIR}'[/bold green]")

    # --- Creazione dei link (migliorata) ---
    console.print("[yellow]Creazione dei link Markdown...[/yellow]")
    for item_id, item_data in processed_items.items():
        if item_data["type"] == "page":
            page_path = os.path.join(OUTPUT_DIR, item_data["slug"], "index.md")
            update_markdown_links(page_path, processed_items)
        if item_data["type"] == "database":
            database_path = os.path.join(OUTPUT_DIR, f"{item_data['slug']}.md")
            update_markdown_links(database_path, processed_items)

    # --- Creazione dei link (da implementare) ---
    console.print("[yellow]Creazione dei link Markdown... (da implementare)[/yellow]")
    # Questa parte richiederà di scorrere i file Markdown scaricati
    # e sostituire i riferimenti interni di Notion con link Markdown basati sugli slug.

if __name__ == "__main__":
    main()