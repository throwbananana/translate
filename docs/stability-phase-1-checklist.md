# Stability Phase 1 Checklist

## Landed in this branch

- [x] Create `controllers/` as a GUI-free orchestration layer.
- [x] Add immutable `TranslationRunConfig` for background translation runs.
- [x] Centralize style prompt mapping for translation runs.
- [x] Add defensive coercion for GUI-sourced numeric values.
- [x] Add unit tests for run config behavior.
- [x] Add upgrade roadmap documentation.

## Next implementation steps

- [ ] Wire `TranslationRunConfig` into `BookTranslatorGUI.start_translation()`.
- [ ] Pass the config snapshot into `translate_text()` and `translate_segment()`.
- [ ] Stop reading Tk variables from background worker code.
- [ ] Add a per-run id so stopped translations cannot write late results into the UI.
- [ ] Add provider timeout handling.
- [ ] Make batch file loading silent.
