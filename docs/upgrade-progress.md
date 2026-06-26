# Upgrade Plan & Progress Tracker

> Persistent source of truth for the upgrade/refactor work. Every implementation step must update this file so progress is not lost when chat context expires.

## 0. Current branch and PR

- Repository: `throwbananana/translate`
- Working branch: `upgrade/stability-phase-1`
- Pull request: `#2` — `Refactor: add stability phase controller groundwork`
- Base branch: `main`
- Last recorded progress date: `2026-06-26`
- Last green CI-confirmed head before this update: `8036710c74e01429cb78c43f9675d430bd801e1a`
- Latest implementation commits before this tracker update:
  - `1598320e154a8e8dab15d2799b6db693a45cdaf0` — add guarded GUI translation workflow adapter and tests
  - `db1d5079f21952f5f3505fb67d082a4d3b55e62a` — export guarded GUI translation workflow adapter
  - `188506b2ef32fd0fcfff83d5e9e5ce8ee15249f3` — record guarded GUI workflow adapter in progress docs
  - `978839ebf9de79cda74d46c98c5943a4e44ee62f` — include guarded GUI workflow in checklist
  - `8f233ad5329bbc63d7c6f979bac8871d33389278` — fix guarded GUI workflow test cancellation API
- Test status: CI and `python-tests` passed on `8036710c74e01429cb78c43f9675d430bd801e1a`. On `978839ebf9de79cda74d46c98c5943a4e44ee62f`, CI passed but `python-tests` failed because the new test used a non-existent `cancel_run(...)` API. Commit `8f233ad5329bbc63d7c6f979bac8871d33389278` fixes the test to call `cancel_current()`; new CI runs are in progress.
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
| Overall upgrade plan | ~62% | Provider adapter wiring is mostly complete; controller-side translation worker orchestration and guarded GUI workflow adapter now exist; GUI main-file wiring is still pending. |
| Stability phase 1 foundations | ~96% | Run config, run guard, GUI adapter, guarded GUI workflow adapter, batch controller, provider adapters, worker runtime helpers, worker orchestrator and engine provider wiring are added. |
| Provider timeout / adapter layer | ~95% | OpenAI-compatible, Gemini and Claude non-streaming engine paths are wired through adapters. Streaming path still needs separate evaluation. |
| GUI thread-safety integration | ~53% | Helper layer can snapshot config, guard direct/queued UI writes, compute worker-loop decisions without Tk reads, run the worker loop through injected callbacks, and expose a GUI-facing guarded workflow entry. `book_translator_gui.pyw` still needs wiring. |
| Batch silent/resumable flow | ~55% | `BatchTaskRecord` and `BatchController` exist; GUI batch flow is not rewired yet. |
| CI confirmation | ~88% | Last fully green head is `8036710c74e01429cb78c43f9675d430bd801e1a`; latest test-fix commit is waiting for CI confirmation. |

## 3. Completed work

### 3.1 Controller foundation

Completed files:

- `controllers/__init__.py`
- `controllers/translation_run_config.py`
- `controllers/run_guard.py`
- `controllers/gui_translation_adapter.py`
- `controllers/translation_worker_runtime.py`
- `controllers/translation_worker_orchestrator.py`
- `controllers/gui_translation_workflow.py`
- `controllers/batch_task.py`
- `controllers/batch_controller.py`

Completed behavior:

- Immutable `TranslationRunConfig` for background translation runs.
- Defensive coercion of GUI/Tk-derived values.
- Centralized translation style prompt mapping.
- `TranslationRunGuard` for rejecting stale worker results after stop/cancel.
- GUI-facing adapter helpers for reading Tk-style values, starting guarded translation runs, checking worker UI writes and cancelling the active run.
- `schedule_guarded_gui_update(...)` for queued Tk `root.after(...)` updates.
- `translation_worker_runtime` helpers for resume clamping, worker count, context decisions, progress calculation and translated text snapshots.
- `translation_worker_orchestrator` for the serial/concurrent translation worker loop through injected callbacks.
- `gui_translation_workflow` adapter that composes `TranslationRunGuard`, `schedule_guarded_gui_update(...)`, and `run_translation_worker(...)` into one GUI-facing entry point.
- `BatchTaskRecord` and `BatchController` for normalized batch queue state.

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

- Unified provider request/response/error contracts.
- Timeout coercion and adapter-level timeout handling.
- Adapter bridge for non-streaming OpenAI-compatible, Gemini and Claude paths.
- `timeout_seconds` in `APIConfig` serialization/loading.

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
- `tests/test_gui_translation_workflow.py`
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

Recent test additions/fixes:

- `tests/test_gui_translation_adapter.py` covers scheduled stale callback rejection.
- `tests/test_translation_worker_runtime.py` covers runtime helper behavior.
- `tests/test_translation_worker_orchestrator.py` covers serial context, parallel no-context behavior, resume, failure pause, cancellation stop, progress and snapshot events.
- `tests/test_gui_translation_workflow.py` covers guarded GUI workflow scheduling, queued update skip after cancellation, and stale-run refusal.
- `8f233ad5329bbc63d7c6f979bac8871d33389278` fixes the guarded workflow cancellation test to use the real `TranslationRunGuard.cancel_current()` API.

Recommended focused test command:

```bash
py -m pytest tests/test_translation_run_config.py tests/test_run_guard.py tests/test_gui_translation_adapter.py tests/test_translation_worker_runtime.py tests/test_translation_worker_orchestrator.py tests/test_gui_translation_workflow.py tests/test_batch_task.py tests/test_batch_controller.py tests/test_provider_base.py tests/test_openai_compatible_provider.py tests/test_openai_compatible_factory.py tests/test_gemini_provider.py tests/test_claude_provider.py tests/test_engine_bridge.py tests/test_translation_engine_adapter_bridge.py tests/test_translation_engine_gemini_claude_adapter_bridge.py -q
```

## 4. Remaining work backlog

### P0 — finish stability phase 1

1. Confirm CI on `8f233ad5329bbc63d7c6f979bac8871d33389278`.
2. Rewire `book_translator_gui.pyw` translation start/stop path:
   - initialize `self.translation_run_guard = TranslationRunGuard()` or use adapter helper;
   - call `start_guarded_translation_run(...)` inside `start_translation()`;
   - pass the guarded run/config snapshot into `translate_text()`;
   - pass config into `translate_segment()`;
   - replace the body of `translate_text()` with a thin adapter around `run_guarded_gui_translation_worker(...)`;
   - stop background worker reads of `self.concurrency_var`, `self.target_language_var`, `self.style_var`.
3. Guard worker UI writes through guarded workflow events.
4. Rewire GUI batch processing through `BatchController` and `load_file_content(..., silent=True)`.
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

Completed controller foundation, provider adapters, provider engine bridge, timeout config chain, GUI adapter helpers, batch controller and initial tests.

### 2026-06-25 — repository scan cleanup passes

Removed tracked patch/archive/runtime artifacts and replaced static placeholder strings in tests with runtime-composed dummy values.

### 2026-06-26 — CI scan artifact and placeholder allowlist

Added `detect-secrets.log` artifact upload, inspected scan output, and narrowed the allowlist to reviewed local placeholders/environment variable names.

### 2026-06-26 — add guarded scheduler helper for Tk queued UI writes

Added `schedule_guarded_gui_update(...)` and unit coverage for already-queued stale callback rejection.

### 2026-06-26 — extract translation worker runtime helpers

Added pure worker-loop helper functions and tests.

### 2026-06-26 — add translation worker orchestrator

Added `run_translation_worker(...)`, `TranslationWorkerEvents`, `SegmentWorkResult`, `TranslationWorkerResult` and tests.

### 2026-06-26 — add guarded GUI translation workflow adapter

Added `GuiTranslationWorkerCallbacks`, `build_guarded_translation_events(...)`, `run_guarded_gui_translation_worker(...)` and tests.

### 2026-06-26 — fix guarded GUI workflow cancellation test

Changed `tests/test_gui_translation_workflow.py` to call `TranslationRunGuard.cancel_current()` instead of the non-existent `cancel_run(...)` method.

## 6. Mandatory update rule for future implementation

Every future implementation step MUST update this file before the response is considered complete.
