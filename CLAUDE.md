# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A modular GUI-based book translation tool (Tkinter) for translating PDF, TXT, EPUB, DOCX, Markdown, and RTF files using various AI translation APIs. Features translation memory, glossary management, automatic API fallback, browser-based translation (Playwright), PDF OCR support, and online book search.

**Version:** 2.3.1

## Quick Start

```bash
# Install dependencies
py -m pip install -r requirements.txt
py -m pip install -r requirements-dev.txt

# Run the application
python book_translator_gui.pyw
# Or: start.bat
```

## Architecture

The codebase is organized into four layers:

```
book_translator_gui.pyw         # Main Tkinter GUI (entry point, ~4800 lines)
├── ui/                         # GUI component modules (Tkinter widgets)
│   ├── toc_panel.py            # Table of contents navigation
│   ├── analysis_panel.py       # Text analysis panel
│   ├── content_notebook.py     # Content notebook/tab area
│   ├── failed_segments_panel.py
│   ├── glossary_dialog.py      # Glossary editor dialog
│   ├── library_panel.py        # Online book library browser
│   └── workstation/            # Main workspace components
│       ├── action_bar.py       # Action buttons (import, translate, export)
│       ├── api_panel.py        # API configuration panel
│       ├── file_panel.py       # File selection panel
│       └── progress_panel.py   # Translation progress display
├── controllers/                # Workflow orchestration (pure Python, no Tkinter)
│   ├── gui_translation_lifecycle.py   # Translation start/finalize state
│   ├── gui_translation_session.py     # Session management
│   ├── gui_translation_workflow.py    # Full guarded translation workflow
│   ├── gui_translation_adapter.py     # Guarded run coordination
│   ├── run_guard.py            # Translation run guard/safety
│   ├── translation_run_config.py      # Run configuration
│   ├── translation_worker_orchestrator.py  # Worker orchestration
│   ├── translation_worker_runtime.py  # Worker runtime helpers
│   ├── batch_controller.py     # Batch translation controller
│   └── batch_task.py           # Batch task model
├── providers/                  # API adapter layer (isolates third-party SDKs)
│   ├── base.py                 # ProviderRequest / ProviderResponse types
│   ├── gemini_provider.py      # Gemini API adapter
│   ├── claude_provider.py      # Claude API adapter
│   ├── openai_compatible.py    # OpenAI-compatible adapter
│   ├── openai_compatible_factory.py  # Provider factory methods
│   ├── browser_automation.py   # Playwright browser-based translation
│   ├── engine_bridge.py        # Backward-compat bridge to translation_engine
│   └── errors.py               # Provider-specific error types
└── core modules:
    ├── translation_engine.py   # API orchestration and fallback logic
    ├── file_processor.py       # File reading (PDF/EPUB/DOCX/TXT/MD/RTF) + OCR
    ├── translation_memory.py   # SQLite translation cache
    ├── glossary_manager.py     # Terminology management (JSON)
    ├── config_manager.py       # Config read/write, backup, migration
    └── app_paths.py            # App data directory paths
```

**Supporting modules:** `provider_utils.py` (validation, fallback selection), `translation_review.py` (failed segment review), `cost_estimator.py`, `audio_manager.py` (text-to-speech export), `smart_glossary.py` (auto glossary extraction), `format_converter.py`, `docx_handler.py` (DOCX format preservation), `tm_editor.py` (TM editor dialog), `online_search.py` / `book_hunter.py` (Z-Library/Anna's Archive), `cloud_upload.py`, `community_manager.py`, `web_importer.py`.

### Data Flow

```
File → FileProcessor.read_file() → text
     → FileProcessor.split_text_into_segments() → segments[]
     → GUI triggers controllers/gui_translation_workflow
         → controllers orchestrate TranslationEngine + providers/
         → TranslationMemory.lookup() (cache hit? → skip API)
         → GlossaryManager.generate_prompt_injection() (inject terms)
         → Provider adapter (e.g. GeminiProvider) calls API
         → TranslationMemory.store() (cache result)
     → translated_segments[]
     → Export (plain text / DOCX / format-preserving)
```

The `controllers/` layer holds pure state/configuration logic testable without Tkinter. The `providers/` layer isolates all third-party SDK calls behind a common `ProviderRequest → ProviderResponse` interface.

## Build, Test, and Lint Commands

```bash
# Run the app
python book_translator_gui.pyw

# All tests (pytest)
pytest -q

# Unit tests only (no network/GUI)
pytest -m "not integration and not gui"

# With coverage
pytest -m "not integration and not gui" --cov=. --cov-report=xml:coverage.xml

# Single test file
pytest tests/test_translation_engine.py

# Legacy test scripts (not pytest)
python test_startup.py
python test_core_features.py
python test_actual_translation.py

# Manual tests (interactive menu)
python scripts/manual_tests/manual_translation_smoke.py

# Lint (ruff)
ruff check tests scripts/manual_tests list_models.py
```

### CI

Two GitHub Actions workflows run on push/PR:
- **`ci.yml`** (Python 3.11): unit tests with coverage + ruff lint + detect-secrets scan
- **`python-tests.yml`** (Python 3.10, 3.11): `pytest -q`

### pytest markers (from `pytest.ini`)

- `unit` — pure logic, no network or GUI
- `integration` — depends on filesystem, external services, or system components
- `gui` — involves Tkinter or window lifecycle

## File Format Support

| Format | Module | Dependencies |
|--------|--------|--------------|
| TXT | file_processor.py | None |
| PDF | file_processor.py | PyPDF2, pdfplumber, pdf2image (+ pytesseract for OCR on scanned docs) |
| EPUB | file_processor.py | ebooklib, beautifulsoup4 |
| DOCX | file_processor.py | python-docx |
| Markdown | file_processor.py | None |
| RTF | file_processor.py | None (basic support) |

## API Provider Support

| Provider | Adapter | Dependencies | Default Model |
|----------|---------|--------------|---------------|
| Gemini | providers/gemini_provider.py | google-generativeai | gemini-2.5-flash |
| OpenAI | providers/openai_compatible.py | openai | gpt-3.5-turbo |
| Claude | providers/claude_provider.py | anthropic | claude-3-haiku-20240307 |
| DeepSeek | providers/openai_compatible.py | openai | deepseek-chat |
| LM Studio | providers/openai_compatible.py | openai | qwen2.5-7b-instruct-1m |
| Custom OpenAI-compatible | providers/openai_compatible.py | openai | (user-defined) |
| Browser (Playwright) | providers/browser_automation.py | playwright | (DeepSeek/Gemini/ChatGPT web) |

### Adding a new API provider

1. Create a provider adapter in `providers/` implementing the `ProviderRequest → ProviderResponse` pattern (see `providers/base.py`)
2. Add default config in `DEFAULT_CONFIG['api_configs']` in `config_manager.py`
3. Wire up in `translation_engine.py` (add API key validation, translate method)
4. Export from `providers/__init__.py`

### Adding a new file format

1. Add format detection in `FileProcessor.SUPPORTED_FORMATS`
2. Implement `extract_{format}_text()` method in `file_processor.py`
3. Add case in `read_file()` method
4. Update `get_file_filter()` for file dialog

## Configuration Structure (v2.3.1)

Config is stored at `get_app_dir() / 'translator_config.json'` (user app data directory). Legacy config at project root is auto-migrated on first run.

```jsonc
{
  "version": "2.3.1",
  "target_language": "中文",
  "segment_size": 800,
  "preview_limit": 10000,
  "max_consecutive_failures": 3,
  "translation_delay": 0.5,
  "translation_style": "通俗小说 (Novel)",
  "concurrency": 1,
  "context_enabled": true,
  "use_translation_memory": true,
  "use_glossary": true,
  "selected_translation_api": "Gemini API",
  "selected_analysis_api": "Gemini API",
  "selected_retry_api": "本地 LM Studio",
  "api_configs": {
    "gemini":    { "api_key": "", "model": "gemini-2.5-flash", "temperature": 0.2 },
    "openai":    { "api_key": "", "model": "gpt-3.5-turbo", "base_url": "", "temperature": 0.2 },
    "claude":    { "api_key": "", "model": "claude-3-haiku-20240307", "temperature": 0.2 },
    "deepseek":  { "api_key": "", "model": "deepseek-chat", "base_url": "https://api.deepseek.com/v1", "temperature": 0.2 },
    "lm_studio": { "api_key": "lm-studio", "model": "qwen2.5-7b-instruct-1m", "base_url": "http://127.0.0.1:1234/v1", "temperature": 0.2 },
    "custom":    { "api_key": "", "model": "", "base_url": "", "temperature": 0.2 }
  },
  "custom_local_models": {},
  "browser_models": {},
  "online_search": { /* zlibrary, annas_archive credentials */ },
  "security": { "admin_password": "" },
  "ui": { "window_width": 950, "window_height": 750, "theme": "default" }
}
```

## Key Conventions

- Python 3 with 4-space indentation, UTF-8 for all file I/O
- `.pyw` for GUI apps (suppresses console on Windows)
- UI strings in Chinese; type hints in module functions; dataclasses for structured data
- SQLite for translation memory (`translation_memory.db`), JSON for glossaries and config
- Provider adapters must expose explicit timeout handling (never hang the GUI)
- Controller modules must be importable without Tkinter (no `import tkinter` at module level)
- `# pragma: allowlist secret` comments on lines with placeholder API keys for detect-secrets

## Commit Guidelines

- Sanitize `translator_config.json` before commits (remove API keys)
- Don't commit `translation_memory.db` (user data)
- Don't commit generated test files (`test_*k.txt`)
- Keep `config_backups/` and `glossaries/` out of commits

## Troubleshooting

### Module Import Errors
```bash
py -m pip install PyPDF2 pdfplumber pdf2image ebooklib beautifulsoup4 python-docx pytesseract google-generativeai openai anthropic playwright
```

### Translation Memory Issues
```python
from translation_memory import TranslationMemory
tm = TranslationMemory()
tm.cleanup(days=0, min_use_count=999999)  # Delete all records
```

### Configuration Issues
```python
from config_manager import ConfigManager
cm = ConfigManager()
cm.reset_to_defaults()
```
