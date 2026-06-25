# Stability Phase 1 Checklist

## Landed in this branch

- [x] Create `controllers/` as a GUI-free orchestration layer.
- [x] Add immutable `TranslationRunConfig` for background translation runs.
- [x] Centralize style prompt mapping for translation runs.
- [x] Add defensive coercion for GUI-sourced numeric values.
- [x] Add unit tests for run config behavior.
- [x] Add `TranslationRunGuard` to reject stale worker writes after stop/cancel.
- [x] Add unit tests for run guard behavior.
- [x] Add GUI-facing adapter helpers to read Tk-style values on the GUI thread, start guarded runs, and skip stale worker UI updates.
- [x] Add unit tests for GUI translation adapter helpers.
- [x] Add `BatchTaskRecord` and normalized batch task statuses.
- [x] Add `BatchController` to normalize queues, select next runnable tasks, update task statuses, cancel pending tasks and serialize back to legacy dicts.
- [x] Add unit tests for legacy batch queue normalization, batch state transitions and silent-loading decisions.
- [x] Add `providers/` adapter package with structured provider request/response/error types.
- [x] Add OpenAI-compatible provider adapter with explicit client/request timeout handling.
- [x] Add factory helpers to convert existing APIConfig/custom-local-model settings into OpenAI-compatible adapters.
- [x] Add engine bridge helpers that preserve the current `(translated_text, model)` return shape while delegating to adapters.
- [x] Replace `translation_engine.py` OpenAI / DeepSeek / LM Studio / custom-local non-streaming methods with calls to the engine bridge.
- [x] Add `timeout_seconds` to APIConfig, API config serialization and config loading.
- [x] Add unit tests for provider timeout coercion, adapter calls, factory defaults, engine bridge behavior and TranslationEngine bridge integration.
- [x] Add upgrade roadmap documentation.

## Next implementation steps

- [ ] Wire `start_guarded_translation_run(...)` into `BookTranslatorGUI.start_translation()`.
- [ ] Pass the config snapshot into `translate_text()` and `translate_segment()`.
- [ ] Stop reading Tk variables from background worker code.
- [ ] Use `guarded_gui_update(...)` or `should_apply_gui_update(...)` before every worker UI write-back.
- [ ] Adopt `BatchController` in GUI batch queue loading/saving and `process_next_batch_file()`.
- [ ] Make `load_file_content(..., silent=True)` the default for batch processing.
- [ ] Add Gemini and Claude provider adapters with timeout/error mapping.
