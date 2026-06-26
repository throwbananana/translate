# Upgrade Plan & Progress Tracker

> Persistent source of truth for the upgrade/refactor work. Every implementation step must update this file so progress is not lost when chat context expires.

## 0. Current branch and PR

- Repository: `throwbananana/translate`
- Working branch: `upgrade/stability-phase-1`
- Pull request: `#2` — `Refactor: add stability phase controller groundwork`
- Base branch: `main`
- Last recorded progress date: `2026-06-26`
- Last green CI-confirmed head before this update: `3610d48abfa94fb6b67c8ff24b38d26e24089152`
- Latest implementation commits before this tracker update:
  - `48e3c83896f623653c46d493879043b0be1ab0b4` — add translation worker orchestrator and tests
  - `475658c74e2993ed7141aa7d6af398a3856dd9ce` — export translation worker orchestrator
- Test status: CI and `python-tests` passed on `3610d48abfa94fb6b67c8ff24b38d26e24089152`. New CI runs are expected after the worker orchestrator commits.
- Merge guidance: use **Squash merge** because this branch contains many process commits.

## 1. Upgrade objective

The project is already feature-rich, but the main risks are runtime stability and maintainability:

1. `book_translator_gui.pyw` still owns too much workflow orchestration.
2. Background workers can still read Tk variables directly.
3. Stopped/cancelled translations can still produce late UI writes until the GUI is rewired.
4. Batch processing can still block on message boxes until `silent=True` is wired into GUI loading.
5. Provider timeout handling was inconsistent across OpenAI-compatible, Gemini and Claude paths.
6. Batch task persistence needs normalized status/error/output tracking.
7. CI must remain green before merge.

## 2. Progress summary

| Area | Progress | Notes |
|---|---:|---|
| Overall upgrade plan | ~60% | Provider adapter wiring is mostly complete; controller-side translation worker orchestration now exists; GUI rewiring is still pending. |
| Stability phase 1 foundations | ~95% | Run config, run guard, GUI adapter, batch controller, provider adapters, worker runtime helpers, worker orchestrator and engine provider wiring are added. |
| Provider timeout / adapter layer | ~95% | OpenAI-compatible, Gemini and Claude non-streaming engine paths are wired through adapters. Streaming path still needs separate evaluation. |
| GUI thread-safety integration | ~48% | Helper layer can snapshot config, guard direct/queued UI writes, compute worker-loop decisions without Tk reads, and run the worker loop through injected callbacks. `book_translator_gui.pyw` still needs wiring. |
| Batch silent/resumable flow | ~55% | `BatchTaskRecord` and `BatchController` exist; GUI batch flow is not rewired yet. |
| CI confirmation | ~90% | CI and `python-tests` passed on `3610d48abfa94fb6b67c8ff24b38d26e24089152`; latest worker-orchestrator commits need confirmation. |

## 3. Completed work

### 3.1 Controller foundation

Completed files:

- `controllers/__init__.py`
- `controllers/README.md`
- `controllers/translation_run_config.py`
- `controllers/run_guard.py`
- `controllers/gui_translation_adapter.py`
- `controllers/translation_worker_runtime.py`
- `controllers/translation_worker_orchestrator.py`
- `controllers/batch_task.py`
- `controllers/batch_controller.py`

Completed behavior:

- Immutable `TranslationRunConfig` for background translation runs.
- Defensive coercion of GUI/Tk-derived values.
- Centralized translation style prompt mapping.
- `TranslationRunGuard` for rejecting stale worker results after stop/cancel.
- GUI-facing adapter helpers for reading Tk-style values, starting guarded translation runs, checking worker UI writes and cancelling the active run.
- `schedule_guarded_gui_update(...)` helper for queued Tk `root.after(...)` updates; the guard check runs inside the scheduled callback so already-queued stale writes are skipped after stop/cancel or after a newer run starts.
- `translation_worker_runtime` helpers for worker-loop decisions that should not read Tk variables:
  - `clamp_start_index(...)`
  - `worker_count_for_run(...)`
  - `should_use_context(...)`
  - `previous_segment_context(...)`
  - `ensure_segment_slots(...)`
  - `progress_percent(...)`
  - `translated_text_snapshot(...)`
- `translation_worker_orchestrator` loop that mirrors the existing GUI `translate_text()` behavior through injected callbacks:
  - splitting text with a config snapshot segment size;
  - serial or concurrent translation;
  - previous-segment context only in serial mode;
  - consecutive-failure pause behavior;
  - progress/status/snapshot events;
  - stopped/paused/final result summaries.
- `BatchTaskRecord` for normalized task state.
- `BatchController` for queue normalization, next-task selection, status updates, cancellation, snapshot counts and serialization.
- `should_load_batch_file_silently(...)` helper for future `load_file_content(..., silent=True)` wiring.

### 3.2 Provider adapter and engine integration

Completed files:

- `providers/__init__.py`
- `providers/base.py`
- `providers/errors.py`
- `providers/openai_compatible.py`
- `providers/openai_compatible_factory.py`
- `providers/engine_bridge.py`
- `providers/gemini_provider.py`
- `providers/claude_provider.py`
- `translation_engine.py`

Completed behavior:

- Unified `ProviderRequest` and `ProviderResponse` data structures.
- Unified provider error classes, including timeout errors.
- Timeout coercion through `coerce_timeout_seconds(...)`.
- OpenAI-compatible adapter with explicit client/request timeout handling.
- Factory helpers for OpenAI, DeepSeek, LM Studio and custom local models.
- Engine bridge helpers that preserve the current `(translated_text, model)` return shape.
- Gemini and Claude adapters with timeout mapping.
- Added `timeout_seconds` to `APIConfig` with serialization/loading.
- Routed non-streaming OpenAI / DeepSeek / LM Studio / custom-local / Gemini / Claude calls through adapters.
- Updated custom API requests to use `config.timeout_seconds` instead of a fixed timeout.

Not completed:

- Streaming OpenAI-compatible path still uses direct SDK client logic and should be evaluated separately.
- GUI translation workflow still needs to pass immutable run config snapshots into background workers.

### 3.3 Tests added

Added focused unit tests:

- `tests/test_translation_run_config.py`
- `tests/test_run_guard.py`
- `tests/test_gui_translation_adapter.py`
- `tests/test_translation_worker_runtime.py`
- `tests/test_translation_worker_orchestrator.py`
- `tests/test_batch_task.py`
- `tests/test_batch_controller.py`
- `tests/test_provider_base.py`
- `tests/test_openai_compatible_provider.py`
- `tests/test_openai_compatible_factory.py`
- `tests/test_gemini_provider.py`
- `tests/test_claude_provider.py`
- `tests/test_engine_bridge.py`
- `tests/test_translation_engine_adapter_bridge.py`
- `tests/test_translation_engine_gemini_claude_adapter_bridge.py`

Recent test additions:

- `tests/test_gui_translation_adapter.py` covers `schedule_guarded_gui_update(...)`, including queued callback rejection after cancellation.
- `tests/test_translation_worker_runtime.py` covers resume index clamping, worker-count selection from immutable config, context eligibility, context skipping for empty/error segments, progress percentage and translated-text snapshots.
- `tests/test_translation_worker_orchestrator.py` covers serial context, parallel no-context behavior, resume from existing translations, consecutive failure pause, cancellation stop, progress and snapshot events.

Recommended focused test command:

```bash
py -m pytest tests/test_translation_run_config.py tests/test_run_guard.py tests/test_gui_translation_adapter.py tests/test_translation_worker_runtime.py tests/test_translation_worker_orchestrator.py tests/test_batch_task.py tests/test_batch_controller.py tests/test_provider_base.py tests/test_openai_compatible_provider.py tests/test_openai_compatible_factory.py tests/test_gemini_provider.py tests/test_claude_provider.py tests/test_engine_bridge.py tests/test_translation_engine_adapter_bridge.py tests/test_translation_engine_gemini_claude_adapter_bridge.py -q
```

### 3.4 Repository hygiene and scan cleanup

Cleanup completed:

- Replaced static placeholder values in provider, engine and config tests with runtime-composed dummy values.
- Removed tracked patch archives and historical fix/backup artifacts.
- Removed tracked runtime config, config backup and legacy autosave artifacts.
- Updated CI secrets job to tee `detect-secrets-hook` output to `detect-secrets.log` and upload that log as an artifact.
- Inspected the uploaded `detect-secrets-log` artifact for CI run `28209644495`; the remaining scan output pointed only to local LM Studio placeholder values.
- Simplified the scan allowlist to a narrow substring rule for reviewed local placeholders and documented environment variable names.
- Confirmed CI and `python-tests` passed after the scan allowlist repair on commit `3610d48abfa94fb6b67c8ff24b38d26e24089152`.

Not completed:

- Need CI confirmation for the latest worker-orchestrator commits after `475658c74e2993ed7141aa7d6af398a3856dd9ce`.
- If the scan fails again, download/read `detect-secrets-log` and fix the exact flagged path/line.

## 4. Remaining work backlog

### P0 — finish stability phase 1

1. Confirm CI on the latest worker-orchestrator commits.
2. Rewire `book_translator_gui.pyw` translation start/stop path:
   - initialize `self.translation_run_guard = TranslationRunGuard()` or use adapter helper;
   - call `start_guarded_translation_run(...)` inside `start_translation()`;
   - pass the guarded run/config snapshot into `translate_text()`;
   - pass config into `translate_segment()`;
   - replace worker-loop calculations with `translation_worker_runtime` helpers or call `run_translation_worker(...)` directly;
   - stop background worker reads of `self.concurrency_var`, `self.target_language_var`, `self.style_var`.
3. Guard worker UI writes:
   - replace direct worker `self.root.after(...)` UI scheduling with `schedule_guarded_gui_update(...)` where the update belongs to a translation run;
   - before any direct background-worker result write, use `should_apply_gui_update(...)` or `guarded_gui_update(...)`;
   - `stop_translation()` should call `cancel_guarded_translation_run(...)`.
4. Rewire GUI batch processing:
   - normalize persisted queue through `BatchController`;
   - use controller status transitions in `process_next_batch_file()`;
   - add `load_file_content(filepath, silent=False)`;
   - call `load_file_content(..., silent=True)` during batch processing.
5. Evaluate streaming provider path.

### P1 — controller extraction after P0

1. Extract `TranslationController` or equivalent to own background translation coordination.
2. Extract `WorkspaceController` for file loading / resume / content state.
3. Extract `BatchController` usage fully out of GUI event handlers.
4. Add regression tests for cancellation, stale result skipping and batch resume behavior.

### P2 — repository hygiene and release readiness

1. Check for any remaining tracked historical artifacts.
2. Add or confirm `LICENSE`.
3. Run full test suite and CI.
4. Squash merge the PR only after CI is green.

## 5. Implementation log

### 2026-06-25 — stability branch created / controller and provider foundations

Completed:

- Added controller-layer foundation.
- Added `TranslationRunConfig`.
- Added `TranslationRunGuard`.
- Added `BatchTaskRecord`.
- Added OpenAI-compatible provider adapter and factory.
- Added provider engine bridge.
- Routed OpenAI / DeepSeek / LM Studio / custom-local non-streaming calls through adapter bridge.
- Added `timeout_seconds` config chain.
- Added GUI translation adapter helpers.
- Added `BatchController`.
- Added Gemini and Claude provider adapters.
- Added tests for all new helper layers.

### 2026-06-25 — repository scan cleanup passes

Completed:

- Replaced static placeholder strings in tests with runtime-composed dummy values.
- Removed tracked patch `.mbox` artifacts, root-level historical scripts, patch-directory scripts, GUI backup artifact, runtime config file/backups and legacy autosave artifacts.
- Reduced repository scan surface and improved repository hygiene.

### 2026-06-26 — CI scan artifact and placeholder allowlist

Changed files:

- `.github/workflows/ci.yml`
- `docs/upgrade-progress.md`

Completed:

- Added always-run `detect-secrets.log` artifact upload.
- Downloaded and inspected `detect-secrets-log` from run `28209644495`.
- Found remaining scan failure points were reviewed LM Studio placeholder values only.
- Replaced complex scan allowlist with a narrow allowlist for local placeholders and documented environment variable names.

### 2026-06-26 — add guarded scheduler helper for Tk queued UI writes

Changed files:

- `controllers/gui_translation_adapter.py`
- `tests/test_gui_translation_adapter.py`
- `docs/upgrade-progress.md`
- `docs/stability-phase-1-checklist.md`

Completed:

- Added `schedule_guarded_gui_update(...)` to guard Tk-style `root.after(...)` updates at callback execution time.
- Added unit coverage for a cancelled run where a callback was already scheduled and must not write to the UI when it eventually executes.

### 2026-06-26 — extract translation worker runtime helpers

Changed files:

- `controllers/translation_worker_runtime.py`
- `controllers/__init__.py`
- `tests/test_translation_worker_runtime.py`
- `docs/upgrade-progress.md`

Completed:

- Added pure worker-loop helpers for resume clamping, worker-count calculation, context decision, previous-context lookup, translated segment slot extension, progress calculation and translated text snapshots.
- Exported the helper functions from `controllers.__init__`.
- Added unit tests to lock these behaviors down before `book_translator_gui.pyw` is rewired.

### 2026-06-26 — add translation worker orchestrator

Changed files:

- `controllers/translation_worker_orchestrator.py`
- `controllers/__init__.py`
- `tests/test_translation_worker_orchestrator.py`
- `docs/upgrade-progress.md`

Completed:

- Added `run_translation_worker(...)`, a tkinter-free worker loop that accepts injected split/translate/state/event callbacks.
- Added `TranslationWorkerEvents`, `SegmentWorkResult` and `TranslationWorkerResult` structures.
- Covered serial context behavior, parallel no-context behavior, resume behavior, failure pause, cancellation stop, progress and snapshot events with unit tests.

Tests:

- Not run locally in this environment.
- Required follow-up: confirm GitHub Actions on the latest head.

Known risks:

- `book_translator_gui.pyw` has not yet been rewired to call `run_translation_worker(...)`. The next implementation step should import the orchestrator and replace the body of `translate_text()` with a thin adapter around injected callbacks.

## 6. Mandatory update rule for future implementation

Every future implementation step MUST update this file before the response is considered complete.

When adding code, update at least these sections:

1. `Progress summary` — adjust percentages and short notes.
2. `Completed work` — add or refine completed items.
3. `Remaining work backlog` — remove completed tasks or add newly discovered tasks.
4. `Implementation log` — add a dated entry with changed files, behavior changes, tests and known risks.
