# Notion Backupper - Versione Modulare

Sistema modulare per il backup e conversione di contenuti Notion in formato Wiki Markdown.

## 📁 Struttura del Progetto

```
notion-backupper/
├── notion_to_wiki.py           # Script originale (monolitico)
├── notion_to_wiki_modular.py   # Script principale modulare
├── downloader.py               # Script di backup JSON semplice
├── config.json                 # Configurazione (non tracciato in git)
├── config.json.example         # Template di configurazione
├── requirements.txt            # Dipendenze Python
└── utils/                      # Moduli del sistema
    ├── __init__.py             # Esportazioni del package
    ├── config.py               # Gestione configurazione
    ├── cache.py                # Sistema di caching
    ├── notion_client.py        # Download da Notion API
    ├── markdown_converter.py   # Conversione Markdown
    ├── link_processor.py       # Gestione link interni
    └── main.py                 # Orchestrazione principale
```

## 🔧 Moduli

### `config.py`
- Caricamento configurazione da `config.json`
- Validazione parametri
- Gestione directory di output
- Gestione errori di configurazione

### `cache.py`
- Sistema di caching per API Notion
- Salvataggio/recupero dati locali
- Ottimizzazione performance

### `notion_client.py`
- Classe `NotionDownloader` per API Notion
- Download pagine, blocchi, database
- Gestione errori di rete
- Caching integrato

### `markdown_converter.py`
- Conversione blocchi Notion → Markdown
- Conversione pagine complete
- Conversione database → tabelle Markdown
- Gestione di tutti i tipi di blocco Notion

### `link_processor.py`
- Aggiornamento link interni Notion
- Conversione ID → slug/percorsi locali
- Pattern matching per link
- Post-processing dei file Markdown

### `main.py`
- Orchestrazione del processo completo
- Gestione ricorsiva delle pagine
- Coordinamento tra moduli
- Progress reporting

## 🚀 Utilizzo

### Script Modulare (Raccomandato)
```bash
python notion_to_wiki_modular.py
```

### Script Originale (Legacy)
```bash
python notion_to_wiki.py
```

## ⚙️ Configurazione

Crea `config.json` basandoti su `config.json.example`:

```json
{
    "notion_token": "secret_...",
    "root_page_id": "..."
}
```

## 📊 Output

- **`notion_wiki/`** - File Markdown strutturati
- **`_notion_cache/`** - Cache API per performance

## 🔧 Vantaggi della Versione Modulare

1. **Manutenibilità** - Codice organizzato per funzionalità
2. **Testabilità** - Ogni modulo testabile indipendentemente  
3. **Riusabilità** - Moduli utilizzabili in altri progetti
4. **Scalabilità** - Facile aggiungere nuove funzionalità
5. **Debug** - Più facile identificare e fixare problemi

## 📋 Dipendenze

- `notion-client` - API client Notion
- `requests` - HTTP requests
- `python-slugify` - Generazione slug
- `rich` - Output colorato e progress

## 🎯 Prossimi Miglioramenti

- Fix gestione relazioni database/pagine
- Miglioramento link interni
- Supporto tipi di blocco aggiuntivi
- Testing automatizzato
- Configurazione avanzata
