# Stability Phase 1 Checklist

## Landed in this branch

- [x] Create `controllers/` as a GUI-free orchestration layer.
- [x] Add immutable `TranslationRunConfig` for background translation runs.
- [x] Centralize style prompt mapping for translation runs.
- [x] Add defensive coercion for GUI-sourced numeric values.
- [x] Add unit tests for run config behavior.
- [x] Add `TranslationRunGuard` to reject stale worker writes after stop/cancel.
- [x] Add unit tests for run guard behavior.
- [x] Add `BatchTaskRecord` and normalized batch task statuses.
- [x] Add unit tests for legacy batch queue normalization and state transitions.
- [x] Add `providers/` adapter package with structured provider request/response/error types.
- [x] Add OpenAI-compatible provider adapter with explicit client/request timeout handling.
- [x] Add unit tests for provider timeout coercion and OpenAI-compatible adapter calls.
- [x] Add upgrade roadmap documentation.

## Next implementation steps

- [ ] Wire `TranslationRunConfig` into `BookTranslatorGUI.start_translation()`.
- [ ] Pass the config snapshot into `translate_text()` and `translate_segment()`.
- [ ] Stop reading Tk variables from background worker code.
- [ ] Instantiate `TranslationRunGuard` in the GUI and check it before every UI write-back.
- [ ] Route OpenAI / DeepSeek / LM Studio / custom calls through `OpenAICompatibleProvider`.
- [ ] Add Gemini and Claude provider adapters with timeout/error mapping.
- [ ] Make batch file loading silent.
- [ ] Normalize persisted `batch_tasks.json` through `BatchTaskRecord`.
