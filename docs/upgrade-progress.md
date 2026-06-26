# Upgrade Plan & Progress Tracker

> Persistent source of truth for the upgrade/refactor work. Every implementation step must update this file so progress is not lost when chat context expires.

## 0. Current branch and PR

- Repository: `throwbananana/translate`
- Working branch: `upgrade/stability-phase-1`
- Pull request: `#2` — `Refactor: add stability phase controller groundwork`
- Base branch: `main`
- Last recorded progress date: `2026-06-26`
- Last green CI-confirmed head before this update: `32f889024cf7c5fb77258ff58c6b45b2d8e3ee4f`
- Latest implementation commits before this tracker update:
  - `1598320e154a8e8dab15d2799b6db693a45cdaf0` — add guarded GUI translation workflow adapter and tests
  - `db1d5079f21952f5f3505fb67d082a4d3b55e62a` — export guarded GUI translation workflow adapter
  - `188506b2ef32fd0fcfff83d5e9e5ce8ee15249f3` — record guarded GUI workflow adapter in progress docs
  - `978839ebf9de79cda74d46c98c5943a4e44ee62f` — include guarded GUI workflow in checklist
  - `8f233ad5329bbc63d7c6f979bac8871d33389278` — fix guarded GUI workflow test cancellation API
  - `32f889024cf7c5fb77258ff58c6b45b2d8e3ee4f` — record latest green guarded workflow CI status
  - `437980550980c68baba6e254c9bb15e1e5b709c1` — record latest guarded workflow CI status in progress docs
  - `101b0521f2021b7a6f34b856750c00c70a892598` — mark guarded workflow CI confirmed in checklist and PR body
  - `d178fb2c546dd40020576f1984a8135ece3f780c` — add pure GUI translation lifecycle helpers
  - `d1bfbee970dc42cc409e287baf83d3463c6364e5` — export GUI translation lifecycle helpers
  - `1371aa144b77d7b983c0a676a6dc627d1fcbd085` — add lifecycle helper tests
  - `b3d8c7fb7b05fe67b1f433af93da99647cf751ed` — adjust lifecycle tests to avoid false incomplete-success cases
- Test status: CI and `python-tests` passed on `32f889024cf7c5fb77258ff58c6b45b2d8e3ee4f`. The latest lifecycle-helper head `b3d8c7fb7b05fe67b1f433af93da99647cf751ed` has no status result yet from the connector status query, so it still needs CI confirmation.
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
| Overall upgrade plan | ~64% | Provider adapter wiring is mostly complete; controller-side translation worker orchestration, guarded GUI workflow adapter, and GUI lifecycle state helpers exist. Direct `book_translator_gui.pyw` wiring is still pending. |
| Stability phase 1 foundations | ~98% | Run config, run guard, GUI adapter, guarded GUI workflow adapter, GUI lifecycle helpers, batch controller, provider adapters, worker runtime helpers, worker orchestrator and engine provider wiring are added. Latest lifecycle helper head still needs CI confirmation. |
| Provider timeout / adapter layer | ~95% | OpenAI-compatible, Gemini and Claude non-streaming engine paths are wired through adapters. Streaming path still needs separate evaluation. |
| GUI thread-safety integration | ~57% | Helper layer can snapshot config, guard direct/queued UI writes, compute worker-loop decisions without Tk reads, run the worker loop through injected callbacks, expose a GUI-facing guarded workflow entry, and now plan/finalize GUI run state without widgets. `book_translator_gui.pyw` still needs wiring. |
| Batch silent/resumable flow | ~55% | `BatchTaskRecord` and `BatchController` exist; GUI batch flow is not rewired yet. |
| CI confirmation | ~88% | Last confirmed green head is `32f889024cf7c5fb77258ff58c6b45b2d8e3ee4f`; latest lifecycle-helper head `b3d8c7fb7b05fe67b1f433af93da99647cf751ed` still needs CI confirmation. |

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
- `controllers/gui_translation_lifecycle.py`
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
- `gui_translation_lifecycle` helpers that plan legacy GUI start state, decide whether to resume/reset segment state, and finalize worker results into translated text, failed-segment records, progress/status, completion-hook decisions and cache-clearing decisions.
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
- `book_translator_gui.pyw` still needs to pass immutable run config snapshots into background workers.

### 3.3 Tests added

Added focused unit tests:

- `tests/test_translation_run_config.py`
- `tests/test_run_guard.py`
- `tests/test_gui_translation_adapter.py`
- `tests/test_translation_worker_runtime.py`
- `tests/test_translation_worker_orchestrator.py`
- `tests/test_gui_translation_workflow.py`
- `tests/test_gui_translation_lifecycle.py`
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
- `tests/test_gui_translation_lifecycle.py` covers resume/reset start-state decisions, success finalization, failed-segment derivation, stopped-run completion blocking and paused-run completion blocking.
- `8f233ad5329bbc63d7c6f979bac8871d33389278` fixes the guarded workflow cancellation test to use the real `TranslationRunGuard.cancel_current()` API.
- CI and `python-tests` passed on `32f889024cf7c5fb77258ff58c6b45b2d8e3ee4f` after the guarded workflow adapter and cancellation-test fix.
- Latest lifecycle-helper head `b3d8c7fb7b05fe67b1f433af93da99647cf751ed` still needs CI confirmation.

Recommended focused test command:

```bash
py -m pytest tests/test_translation_run_config.py tests/test_run_guard.py tests/test_gui_translation_adapter.py tests/test_translation_worker_runtime.py tests/test_translation_worker_orchestrator.py tests/test_gui_translation_workflow.py tests/test_gui_translation_lifecycle.py tests/test_batch_task.py tests/test_batch_controller.py tests/test_provider_base.py tests/test_openai_compatible_provider.py tests/test_openai_compatible_factory.py tests/test_gemini_provider.py tests/test_claude_provider.py tests/test_engine_bridge.py tests/test_translation_engine_adapter_bridge.py tests/test_translation_engine_gemini_claude_adapter_bridge.py -q
```

## 4. Remaining work backlog

### P0 — finish stability phase 1

1. Confirm CI on latest lifecycle-helper head `b3d8c7fb7b05fe67b1f433af93da99647cf751ed`.
2. Rewire `book_translator_gui.pyw` translation start/stop path:
   - initialize `self.translation_run_guard = TranslationRunGuard()` or use adapter helper;
   - call `start_guarded_translation_run(...)` inside `start_translation()`;
   - use `plan_gui_translation_start(...)` for resume/reset state;
   - pass the guarded run/config snapshot into `translate_text()`;
   - pass config into `translate_segment()`;
   - replace the body of `translate_text()` with a thin adapter around `run_guarded_gui_translation_worker(...)`;
   - use `finalize_gui_translation_result(...)` to apply worker results;
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

### 2026-06-26 — confirm guarded workflow CI

Confirmed that both `CI` and `python-tests` completed successfully on head `32f889024cf7c5fb77258ff58c6b45b2d8e3ee4f`. This clears the previous checklist blocker and makes the next safe step the direct `book_translator_gui.pyw` guarded-run wiring.

### 2026-06-26 — add GUI translation lifecycle helpers

Added `controllers/gui_translation_lifecycle.py` plus `tests/test_gui_translation_lifecycle.py`. The helper layer now supports pure planning of resume/reset start state and finalization of `TranslationWorkerResult` into legacy GUI state fields, reducing the remaining `book_translator_gui.pyw` wiring surface.

## 6. Mandatory update rule for future implementation

Every future implementation step MUST update this file before the response is considered complete.