# Notion to Wiki

A Python script that exports your Notion workspace to a local wiki in Markdown format.

## What it does

This script connects to your Notion workspace and downloads all pages and databases, converting them into a structured collection of Markdown files. It preserves the hierarchical structure of your Notion workspace and converts internal links to work in the local wiki format.

**Features:**
- Downloads all pages and sub-pages recursively
- Converts databases to Markdown tables with individual record pages
- Maintains internal link relationships
- Creates a hierarchical folder structure
- Supports all common Notion block types (text, headers, lists, tables, images, etc.)
- Includes caching for improved performance

## Requirements

- Python 3.9+
- A Notion integration token
- The ID of your root Notion page

## Installation

1. Clone this repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Configuration

1. Create a `config.json` file by copying the example:
   ```bash
   cp config.json.example config.json
   ```

2. Edit `config.json` with your settings:
   ```json
   {
     "notion_token": "secret_your_notion_integration_token_here",
     "root_page_id": "your-root-page-id-here"
   }
   ```

### Getting your Notion token

1. Go to [Notion Developers](https://developers.notion.com/)
2. Click "Create new integration"
3. Give it a name and select your workspace
4. Copy the "Internal Integration Token" (starts with `secret_`)
5. Share your root page with the integration (click Share → Add people → select your integration)

### Getting your root page ID

From any Notion page URL like:
```
https://www.notion.so/workspace/Page-Title-abc123def456...
```

The page ID is the part after the last dash: `abc123def456...`

You can also use the full UUID format with dashes.

## Usage

Run the script:
```bash
python run.py
```

The script will:
1. Connect to Notion and collect all pages/databases
2. Download the content 
3. Convert everything to Markdown
4. Create subpages for database records
5. Update internal links

Output will be saved in the `notion_wiki/` directory.

## Output Structure

```
notion_wiki/
├── index.md                    # Your root page
├── page-name/
│   ├── index.md               # Page content
│   └── sub-page.md            # Sub-pages
├── database-name.md           # Database as table
├── database-name/             # Database records
│   ├── record-1.md
│   └── record-2.md
└── ...
```

## Dependencies

- `notion-client` - Official Notion API client
- `requests` - HTTP requests
- `python-slugify` - URL-safe filenames
- `rich` - Beautiful console output
