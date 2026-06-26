# Stability Phase 1 Checklist

> Persistent progress source: [`docs/upgrade-progress.md`](upgrade-progress.md).  
> Every future implementation step must update `docs/upgrade-progress.md` together with this checklist.

## Landed in this branch

- [x] Create `controllers/` as a GUI-free orchestration layer.
- [x] Add immutable `TranslationRunConfig` for background translation runs.
- [x] Centralize style prompt mapping for translation runs.
- [x] Add defensive coercion for GUI-sourced numeric values.
- [x] Add unit tests for run config behavior.
- [x] Add `TranslationRunGuard` to reject stale worker writes after stop/cancel.
- [x] Add unit tests for run guard behavior.
- [x] Add GUI-facing adapter helpers to read Tk-style values on the GUI thread, start guarded runs, and skip stale worker UI updates.
- [x] Add `schedule_guarded_gui_update(...)` for Tk `root.after(...)` callbacks so queued UI writes re-check the active run at execution time.
- [x] Add `guarded_final_gui_update(...)` and `schedule_guarded_final_gui_update(...)` so final accepted GUI state finishes the active run exactly once.
- [x] Add `GuiTranslationSession` plus helpers to start/cancel guarded GUI sessions and schedule final-state application.
- [x] Add first-pass GUI wiring patch tool for guarded imports, session state initialization and stop cancellation in `book_translator_gui.pyw`.
- [x] Extend GUI wiring patch tool to route `start_translation()` resume/reset planning through `start_gui_translation_session(...)`, apply `session.start_state`, and pass the session into the translation thread.
- [x] Extend GUI wiring patch tool to generate guarded `translate_text(self, session=None)` lifecycle wiring through `run_guarded_gui_translation_lifecycle(...)`.
- [x] Extend GUI wiring patch tool to generate final-state application through `schedule_gui_translation_final_state(...)`.
- [x] Extend GUI wiring patch tool to generate `translate_segment(..., config=None)` so guarded workers use config snapshots instead of Tk variable reads for target language/style.
- [x] Add pure `translation_worker_runtime` helpers for resume clamping, worker count, context selection, segment-slot extension, progress and translated-text snapshots.
- [x] Add `translation_worker_orchestrator` to run the serial/concurrent translation worker loop through injected callbacks without tkinter dependencies.
- [x] Add `gui_translation_workflow` to compose the run guard, guarded scheduler and worker orchestrator into one GUI-facing adapter.
- [x] Add `run_guarded_gui_translation_lifecycle(...)` to run the guarded worker and return finalized GUI state in one helper.
- [x] Add `gui_translation_lifecycle` to plan resume/reset start state and finalize worker results into legacy GUI state fields.
- [x] Add unit tests for GUI translation adapter helpers, including scheduled stale callback rejection and final guarded update behavior.
- [x] Add unit tests for GUI translation session behavior: config snapshots, resume/reset planning, cancellation and final-state scheduling.
- [x] Add unit tests for GUI wiring patch tool behavior, start-session rewrite, guarded lifecycle rewrite, segment-config rewrite and idempotency.
- [x] Add unit tests for worker runtime helper behavior before GUI rewiring.
- [x] Add unit tests for worker orchestrator behavior: serial context, parallel no-context, resume, failure pause, cancellation stop, progress and snapshots.
- [x] Add unit tests for guarded GUI workflow behavior: normal scheduled updates, queued update skip after cancel, stale-run refusal, and guarded lifecycle finalization.
- [x] Add unit tests for GUI translation lifecycle behavior: resume/reset decisions, success/failure finalization, and stopped/paused completion blocking.
- [x] Add `BatchTaskRecord` and normalized batch task statuses.
- [x] Add `BatchController` to normalize queues, select next runnable tasks, update statuses, cancel pending tasks and serialize back to legacy dicts.
- [x] Add unit tests for legacy batch queue normalization, batch state transitions and silent-loading decisions.
- [x] Add `providers/` adapter package with structured provider request/response/error types.
- [x] Add OpenAI-compatible provider adapter with explicit client/request timeout handling.
- [x] Add Gemini and Claude provider adapters with timeout/error mapping.
- [x] Add factory helpers to convert existing APIConfig/custom-local-model settings into OpenAI-compatible adapters.
- [x] Add engine bridge helpers that preserve the current `(translated_text, model)` return shape while delegating to adapters.
- [x] Replace `translation_engine.py` OpenAI / DeepSeek / LM Studio / custom-local non-streaming methods with calls to the engine bridge.
- [x] Route Gemini and Claude `translation_engine.py` methods through their provider adapters.
- [x] Add `timeout_seconds` to APIConfig, API config serialization and config loading.
- [x] Add unit tests for provider timeout coercion, adapter calls, factory defaults, Gemini/Claude timeout mapping, engine bridge behavior and TranslationEngine bridge integration.
- [x] Add upgrade roadmap documentation.
- [x] Add persistent upgrade/progress tracker at `docs/upgrade-progress.md`.
- [x] Reduce detect-secrets false positives by replacing static fake credential values in tests.
- [x] Remove tracked patch mbox artifacts that could trigger secret scans.
- [x] Remove tracked historical GUI fix scripts, patch bundle scripts and GUI backup artifact.
- [x] Remove tracked runtime config, config backup and legacy autosave artifacts.
- [x] Confirm CI and `python-tests` are green after the secrets scan repair.
- [x] Confirm CI and `python-tests` are green after the guarded GUI workflow commits.
- [x] Confirm CI and `python-tests` are green after the GUI lifecycle helper commits.
- [x] Confirm CI and `python-tests` are green after the guarded lifecycle workflow/docs head.
- [x] Confirm CI and `python-tests` are green after the guarded final update/docs head.
- [x] Confirm CI and `python-tests` are green after the GUI translation session helper commits.
- [x] Confirm CI and `python-tests` are green after the first-pass GUI wiring patch-tool commits.
- [x] Confirm CI and `python-tests` are green on `61916c0c6170d3bee32aa3f6a7765b6fd53f7897`.

## Next implementation steps

- [ ] Confirm CI on the guarded-lifecycle patch-tool/docs head.
- [ ] Run `tools/wire_gui_translation_session.py` against `book_translator_gui.pyw` and review the generated diff.
- [ ] Commit the reviewed generated `book_translator_gui.pyw` diff.
- [ ] Validate whether legacy single-thread retry should be preserved inside the guarded worker flow or moved into a follow-up controller helper.
- [ ] Replace any remaining run-owned direct `root.after(...)` writes with guarded workflow events or guarded helpers.
- [ ] Adopt `BatchController` in GUI batch queue loading/saving and `process_next_batch_file()`.
- [ ] Make `load_file_content(..., silent=True)` the default for batch processing.
- [ ] Evaluate whether `_stream_openai_compatible(...)` should be adapted or kept as direct SDK logic for now.
