"""
Module for managing and updating internal links in Markdown files.
"""

import re
import os


def update_markdown_links(filepath, processed_items):
    """Update internal Notion links in the Markdown file."""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
    except FileNotFoundError:
        print(f"Error: File not found: {filepath}")
        return
    except Exception as e:
        print(f"Error reading file {filepath}: {e}")
        return

    updated_content = content

    # Pattern to find Notion links (both full URLs and IDs)
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
        return match.group(0)  # If ID not found, leave original link

    updated_content = re.sub(notion_link_pattern, replace_notion_link, updated_content)

    # Pattern to find child_page and child_database references (ID only)
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
        print(f"Error writing updated file {filepath}: {e}")


def update_all_markdown_links(output_dir, processed_items):
    """Update links in all generated Markdown files."""
    for item_id, item_data in processed_items.items():
        if item_data["type"] == "page":
            page_path = os.path.join(output_dir, item_data["slug"], "index.md")
            update_markdown_links(page_path, processed_items)
        if item_data["type"] == "database":
            database_path = os.path.join(output_dir, f"{item_data['slug']}.md")
            update_markdown_links(database_path, processed_items)
