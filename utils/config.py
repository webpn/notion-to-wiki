"""
Modulo per la gestione della configurazione del progetto.
"""

import json
import os
from rich.console import Console

console = Console()

# --- Configurazione ---
CONFIG_FILE = "config.json"
OUTPUT_DIR = "notion_wiki"
CACHE_DIR = "_notion_cache"
USE_CACHE = True  # Imposta a False per forzare il download da Notion


def load_config():
    """Carica la configurazione dal file JSON."""
    try:
        with open(CONFIG_FILE, "r") as f:
            config = json.load(f)
            notion_token = config.get("notion_token")
            root_page_id = config.get("root_page_id")
            
        if not notion_token or not root_page_id:
            console.print("[bold red]Errore:[/bold red] Token Notion o ID pagina radice non configurati correttamente nel file JSON.")
            exit()
            
        return notion_token, root_page_id
        
    except FileNotFoundError:
        console.print(f"[bold red]Errore:[/bold red] File di configurazione '{CONFIG_FILE}' non trovato.")
        exit()
    except json.JSONDecodeError:
        console.print(f"[bold red]Errore:[/bold red] Impossibile decodificare il file JSON '{CONFIG_FILE}'.")
        exit()
    except KeyError as e:
        console.print(f"[bold red]Errore:[/bold red] Chiave mancante nel file di configurazione: {e}")
        exit()


def ensure_directories():
    """Crea le directory necessarie se non esistono."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(CACHE_DIR, exist_ok=True)
