# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A modular GUI-based book translation tool (Tkinter) for translating PDF, TXT, EPUB, DOCX, and Markdown files using various AI translation APIs. Features translation memory, glossary management, and automatic API fallback.

**Version:** 2.1
**Architecture:** Modular design with separate components for file processing, translation engine, configuration, and memory management.

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run the application
python book_translator_gui.pyw
# Or use the batch launcher
start.bat
```

## Module Architecture

```
translate/
├── book_translator_gui.pyw    # Main GUI application (Tkinter)
├── file_processor.py          # File reading and text segmentation
├── translation_engine.py      # Translation API orchestration
├── translation_memory.py      # SQLite-based translation cache
├── glossary_manager.py        # Terminology management
├── config_manager.py          # Configuration with backup/migration
├── translator_config.json     # User configuration (auto-generated)
├── translation_memory.db      # Translation cache database
├── glossaries/                # Glossary files (JSON)
└── config_backups/            # Configuration backups
```

### Module Descriptions

| Module | Responsibility |
|--------|----------------|
| `file_processor.py` | Reads TXT/PDF/EPUB/DOCX/MD/RTF, auto-detects encoding, segments text |
| `translation_engine.py` | Manages API calls (Gemini/OpenAI/Claude/DeepSeek/LM Studio), handles fallback |
| `translation_memory.py` | SQLite cache for translations, avoids duplicate API calls |
| `glossary_manager.py` | Terminology tables, injects terms into translation prompts |
| `config_manager.py` | Configuration read/write, version migration, backup management |

### Data Flow

```
File → FileProcessor.read_file() → text
     → FileProcessor.split_text_into_segments() → segments[]
     → BookTranslatorGUI.translate_segment()
         → TranslationMemory.lookup() (cache hit? return cached)
         → GlossaryManager.generate_prompt_injection() (inject terminology)
         → API call (Gemini/OpenAI/LM Studio/etc.)
         → TranslationMemory.store() (save for future)
     → translated_segments[]
     → Export
```

**Note:** The main GUI (`book_translator_gui.pyw`) now directly integrates `TranslationMemory` and `GlossaryManager`. The standalone `translation_engine.py` module provides an alternative programmatic interface for batch translation tasks.

## File Format Support

| Format | Module | Dependencies |
|--------|--------|--------------|
| TXT | file_processor.py | None (built-in) |
| PDF | file_processor.py | PyPDF2 |
| EPUB | file_processor.py | ebooklib, beautifulsoup4 |
| DOCX | file_processor.py | python-docx |
| Markdown | file_processor.py | None (built-in) |
| RTF | file_processor.py | None (basic support) |

## API Provider Support

| Provider | Module | Dependencies | Default Model |
|----------|--------|--------------|---------------|
| Gemini | translation_engine.py | google-generativeai | gemini-2.5-flash |
| OpenAI | translation_engine.py | openai | gpt-3.5-turbo |
| Claude | translation_engine.py | anthropic | claude-3-haiku |
| DeepSeek | translation_engine.py | openai | deepseek-chat |
| LM Studio | translation_engine.py | openai | (local model) |
| Custom | translation_engine.py | requests | (user-defined) |

## Testing

```bash
# Run all tests
run_all_tests.bat

# Individual test scripts
python test_startup.py           # Basic app initialization
python test_core_features.py     # Core functionality checks
python test_large_file.py        # Generates test files (1k-500k chars)
python test_autosave.py          # Config backup/restore
python test_actual_translation.py # Live API test (consumes tokens)

# Test individual modules
python translation_memory.py     # Translation memory self-test
python glossary_manager.py       # Glossary manager self-test
python file_processor.py         # File processor self-test
python translation_engine.py     # Translation engine self-test
python config_manager.py         # Config manager self-test
```

## Configuration Structure (v2.1)

```json
{
  "version": "2.1",
  "target_language": "中文",
  "segment_size": 800,
  "use_translation_memory": true,
  "use_glossary": true,
  "api_configs": {
    "gemini": { "api_key": "", "model": "gemini-2.5-flash" },
    "openai": { "api_key": "", "model": "gpt-3.5-turbo", "base_url": "" },
    "claude": { "api_key": "", "model": "claude-3-haiku-20240307" },
    "deepseek": { "api_key": "", "model": "deepseek-chat", "base_url": "https://api.deepseek.com/v1" },
    "lm_studio": { "api_key": "lm-studio", "model": "qwen2.5-7b-instruct-1m", "base_url": "http://127.0.0.1:1234/v1" },
    "custom": { "api_key": "", "model": "", "base_url": "" }
  },
  "custom_local_models": {}
}
```

## Common Modifications

### Adding a New File Format

1. Add format detection in `FileProcessor.SUPPORTED_FORMATS`
2. Implement `extract_{format}_text()` method in `file_processor.py`
3. Add case in `read_file()` method
4. Update `get_file_filter()` for file dialog

### Adding a New API Provider

1. Add to `APIProvider` enum in `translation_engine.py`
2. Add default config in `DEFAULT_CONFIG['api_configs']` in `config_manager.py`
3. Implement `_translate_with_{provider}()` in `TranslationEngine`
4. Update `get_available_providers()` and `_do_translate()`

### Using Translation Memory

```python
from translation_memory import get_translation_memory

tm = get_translation_memory()

# Lookup
cached = tm.lookup("Hello", "中文")

# Store
tm.store("Hello", "你好", "中文", api_provider="gemini")

# Similar lookup
similar = tm.lookup_similar("Hello world", "中文", threshold=0.8)

# Statistics
stats = tm.get_stats()
```

### Using Glossary Manager

```python
from glossary_manager import get_glossary_manager

gm = get_glossary_manager()

# Create and add terms
gm.create_glossary("tech", "Technical terms")
gm.load_glossary("tech")
gm.add_term("tech", "API", "应用程序接口")

# Generate prompt injection
prompt = gm.generate_prompt_injection("This API uses...")
# Returns: "请在翻译时使用以下术语：\n- \"API\" → \"应用程序接口\"\n\n"
```

### Using Translation Engine

```python
from translation_engine import TranslationEngine, APIConfig, APIProvider

engine = TranslationEngine()
engine.add_api_config('gemini', APIConfig(
    provider=APIProvider.GEMINI,
    api_key='your-key',
    model='gemini-2.5-flash'
))

# Single translation
result = engine.translate("Hello", "中文", provider="gemini")

# Batch translation
results = engine.translate_batch(
    ["Hello", "World"],
    "中文",
    on_progress=lambda cur, total: print(f"{cur}/{total}")
)

# Streaming translation
for chunk in engine.translate_stream("Hello", "中文"):
    print(chunk, end="", flush=True)
```

## Key Conventions

### Code Style
- Python 3 with 4-space indentation
- UTF-8 for all file I/O
- UI strings in Chinese
- Type hints in module functions
- Dataclasses for structured data

### File Naming
- `.pyw` for GUI apps (suppresses console on Windows)
- `test_*.py` for test scripts
- `*_manager.py` for management modules
- `*_engine.py` for processing engines

### Database
- SQLite for translation memory (`translation_memory.db`)
- JSON for glossaries (`glossaries/*.json`)
- JSON for configuration (`translator_config.json`)

## Troubleshooting

### Module Import Errors
```bash
# Install missing dependencies
pip install PyPDF2 ebooklib beautifulsoup4 python-docx google-generativeai openai
```

### Translation Memory Issues
```python
# Reset translation memory
from translation_memory import TranslationMemory
tm = TranslationMemory()
tm.cleanup(days=0, min_use_count=999999)  # Delete all records
```

### Configuration Issues
```python
# Reset to defaults
from config_manager import ConfigManager
cm = ConfigManager()
cm.reset_to_defaults()
```

## Commit Guidelines

- Sanitize `translator_config.json` before commits (remove API keys)
- Don't commit `translation_memory.db` (user data)
- Don't commit generated test files (`test_*k.txt`)
- Keep `config_backups/` and `glossaries/` out of commits

## Writer Tool (Subdirectory)

A separate writing assistant application in `writer tool/` with mind mapping, script editing, and AI integration. Has its own CLAUDE.md.

```bash
python "writer tool/start_app.py"
```
