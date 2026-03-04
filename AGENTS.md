# Repository Guidelines

## Project Structure & Modules
- `book_translator_gui.pyw`: Tkinter GUI orchestrating text loading, segmentation, API calls, and autosave/backup of `translator_config.json`.
- `translator_config.json` + `config_backups/`: store API keys/models; backups keep the latest three; keep real keys out of commits.
- `test_*.py` and companion `.bat` files: scripted checks for large-file handling, core logic, startup, autosave, and live translation; `test_large_file.py` builds fixtures used by other tests.
- Sample inputs: `sample_book.txt` and generated `test_*k.txt`; outputs like `*_翻译测试.txt` and `test_report.md` land in the repo root.
- Docs and changelog: Chinese quick-start/usage guides and `v1.1更新说明.txt`; update them when behavior or defaults change.

## Setup, Build, and Run
- Install dependencies: `pip install -r requirements.txt` (includes google-generativeai; PyPDF2/ebooklib add PDF/EPUB support).
- Launch the app: `python book_translator_gui.pyw` or double-click `start.bat`.
- Generate fixtures: `python test_large_file.py` (creates 1k–500k text files for preview/segment testing).
- Run the full suite: `run_all_tests.bat` (generates fixtures, runs core logic checks, then translation smoke tests).
- Targeted checks: `python test_core_features.py`, `python test_startup.py`, `python test_autosave.py`; `python test_actual_translation.py` hits Gemini and consumes tokens—use your own key.

## Coding Style & Naming
- Python 3 with 4-space indentation; use UTF-8 for all file I/O.
- Keep UI strings/logs in Chinese; function and variable names in lower_snake_case; GUI widget vars follow `*_var`/`*_label` patterns already used.
- Reuse shared helpers (segmentation, backup logic) instead of duplicating; prefer `pathlib` and context-managed file handles.
- Never hardcode secrets; read them from config, and mask keys when printing or logging.

## Testing Guidelines
- Tests are script-driven (no pytest); expect console output plus generated artifacts in the repo root.
- Before merging, at minimum run `python test_startup.py` and `python test_core_features.py`; for API changes, also run `python test_actual_translation.py` with your own key.
- Validate large-file mode by opening `test_50k.txt` in the GUI and confirming preview toggles; ensure backups rotate to ≤3 files in `config_backups/`.

## Commit & Pull Requests
- Git history is not bundled here; use concise, imperative commits (Conventional style welcome, e.g., `fix: handle preview toggle`).
- PRs should describe scope, list commands/tests run, note any API key handling, and attach screenshots/gifs for UI-visible changes (before/after preferred).
- Keep `translator_config.json` sanitized before pushing; do not commit real API keys or oversized generated outputs.
