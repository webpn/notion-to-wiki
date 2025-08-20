"""
Modulo per la gestione e l'aggiornamento dei link interni nei file Markdown.
"""

import re
import os


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
                return f"[{link_text}]({target_item['slug']}.md)"
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
                return f"[{link_text}]({target_item['slug']}.md)"
            elif target_item["type"] == "database":
                return f"[{link_text}]({target_item['slug']}.md)"
        return match.group(0)

    updated_content = re.sub(child_block_pattern, replace_child_block_link, updated_content)

    try:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(updated_content)
    except Exception as e:
        print(f"Errore durante la scrittura del file aggiornato {filepath}: {e}")


def update_all_markdown_links(output_dir, processed_items):
    """Aggiorna i link in tutti i file Markdown generati."""
    for item_id, item_data in processed_items.items():
        if item_data["type"] == "page":
            page_path = os.path.join(output_dir, f"{item_data['slug']}.md")
            update_markdown_links(page_path, processed_items)
        if item_data["type"] == "database":
            database_path = os.path.join(output_dir, f"{item_data['slug']}.md")
            update_markdown_links(database_path, processed_items)
