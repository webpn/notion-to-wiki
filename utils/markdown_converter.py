"""
Modulo per la conversione dei contenuti Notion in formato Markdown.
"""

import os
import requests
from slugify import slugify


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


def convert_page_to_markdown(page_data, blocks, output_dir):
    """Converte una pagina Notion completa in file Markdown."""
    title = page_data.get("properties", {}).get("title", {}).get("title", [{}])[0].get("plain_text", "Untitled")
    slug = slugify(title)
    page_dir = os.path.join(output_dir, slug)
    os.makedirs(page_dir, exist_ok=True)
    output_file = os.path.join(page_dir, "index.md")

    if not blocks:
        return slug, title

    all_markdown_content = f"# {title}\n\n"
    for block in blocks:
        markdown_block = convert_block_to_markdown(block)
        if markdown_block:
            all_markdown_content += markdown_block + "\n\n"

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(all_markdown_content)
    return slug, title


def convert_database_to_markdown(database_data, results, all_data, all_records, downloader, output_dir):
    """Converte un database Notion in tabella Markdown usando tutti i dati già scaricati."""
    title = database_data.get("title", [{}])[0].get("plain_text", "Untitled Database")
    slug = slugify(title)
    output_file = os.path.join(output_dir, f"{slug}.md")

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
                            
                            # Prima controlla se è un database o pagina già scaricato
                            if related_id in all_data:
                                related_entry = all_data[related_id]
                                related_info = related_entry["info"]
                                related_title = related_info["title"]
                                
                                if related_info["type"] == "page":
                                    related_names.append(f"[{related_title}]({slugify(related_title)}/index.md)")
                                elif related_info["type"] == "database":
                                    related_names.append(f"[{related_title}]({slugify(related_title)}.md)")
                            # Controlla se è un record di un database
                            elif related_id in all_records:
                                record_info = all_records[related_id]
                                related_names.append(f"[{record_info['title']}]")
                            else:
                                # Fallback con ID parziale
                                related_names.append(f"[ID: {related_id[:8]}...]")

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
