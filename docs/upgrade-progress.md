# Upgrade Plan & Progress Tracker

> Persistent source of truth for the upgrade/refactor work. Every implementation step must update this file so progress is not lost when chat context expires.

## 0. Current branch and PR

- Repository: `throwbananana/translate`
- Working branch: `upgrade/stability-phase-1`
- Pull request: `#2` — `Refactor: add stability phase controller groundwork`
- Base branch: `main`
- Last recorded progress date: `2026-06-26`
- Last green CI-confirmed head before this update: `313e79527a9f186ae0702a0cd65f869a30506165`
- Latest implementation commits before this tracker update:
  - `3b6bfc22dfd8512cba5cae1616f417d1c34a98b3` — add GUI translation session checklist item
  - `5659607376aeb2707d1b567f1f09086a80990913` — add GUI translation wiring patch tool
  - `4251ffa9c779572923d5321db17d5ce471180b77` — cover GUI translation wiring patch tool in tests
  - `7c8287f68e746bc1b74c4ed650f2d9b420c2d067` — record GUI wiring patch tool progress
  - `313e79527a9f186ae0702a0cd65f869a30506165` — add GUI wiring patch tool checklist item
  - `78e9849a99b2f2fd9f5d8f6b8da71e754613e151` — extend GUI wiring patch to start session
  - `ec7f93bfca05c325b92c1f2ca45bc6182c7e2077` — cover start session GUI wiring patch
- Test status: CI and `python-tests` passed on `313e79527a9f186ae0702a0cd65f869a30506165`, confirming the first-pass GUI wiring patch-tool/docs head. The latest start-session patch-tool code head `ec7f93bfca05c325b92c1f2ca45bc6182c7e2077` still needs CI confirmation.
- Merge guidance: use **Squash merge** because this branch contains many process commits.

## 1. Upgrade objective

The project is feature-rich, but the main risks are runtime stability and maintainability:

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
| Overall upgrade plan | ~70% | Provider adapter wiring is mostly complete; controller-side translation worker orchestration, guarded GUI workflow/lifecycle/session helpers, final guarded updates, and reproducible GUI wiring patch tooling now exist. Direct runtime replacement in `book_translator_gui.pyw` is still pending. |
| Stability phase 1 foundations | ~99% | Run config, run guard, GUI adapter, guarded GUI workflow/lifecycle/session helpers, batch controller, provider adapters, worker runtime helpers, worker orchestrator, engine provider wiring and GUI wiring patch tooling are added. Latest start-session patch head still needs CI confirmation. |
| Provider timeout / adapter layer | ~95% | OpenAI-compatible, Gemini and Claude non-streaming engine paths are wired through adapters. Streaming path still needs separate evaluation. |
| GUI thread-safety integration | ~70% | Helper layer can snapshot config, plan resume/reset state, guard direct/queued UI writes, compute worker-loop decisions without Tk reads, run/finalize workers through injected callbacks, finish the run after final GUI state is applied, expose one session object for GUI start/stop wiring, and now has an idempotent patch tool covering imports, guarded state initialization, stop cancellation, and `start_translation()` session creation/thread argument wiring. |
| Batch silent/resumable flow | ~55% | `BatchTaskRecord` and `BatchController` exist; GUI batch flow is not rewired yet. |
| CI confirmation | ~90% | Last confirmed green head is `313e79527a9f186ae0702a0cd65f869a30506165`; latest start-session patch head `ec7f93bfca05c325b92c1f2ca45bc6182c7e2077` still needs CI confirmation. |

## 3. Completed work

### 3.1 Controller and GUI wiring foundation

Completed files include:

- `controllers/__init__.py`
- `controllers/translation_run_config.py`
- `controllers/run_guard.py`
- `controllers/gui_translation_adapter.py`
- `controllers/gui_translation_session.py`
- `controllers/translation_worker_runtime.py`
- `controllers/translation_worker_orchestrator.py`
- `controllers/gui_translation_workflow.py`
- `controllers/gui_translation_lifecycle.py`
- `controllers/batch_task.py`
- `controllers/batch_controller.py`
- `tools/wire_gui_translation_session.py`

Completed behavior:

- Immutable `TranslationRunConfig` snapshots for background translation runs.
- Defensive coercion of GUI/Tk-derived values.
- Centralized translation style prompt mapping.
- `TranslationRunGuard` for rejecting stale worker results after stop/cancel.
- GUI-facing helpers for reading Tk-style values, starting/cancelling guarded runs, checking worker UI writes, and scheduling guarded Tk `root.after(...)` updates.
- `guarded_final_gui_update(...)` and `schedule_guarded_final_gui_update(...)`, so final GUI state can be accepted and then finish the active run exactly once.
- `GuiTranslationSession` plus `start_gui_translation_session(...)`, `cancel_gui_translation_session(...)`, and `schedule_gui_translation_final_state(...)`.
- `translation_worker_runtime` helpers for resume clamping, worker count, context decisions, progress calculation and translated text snapshots.
- `translation_worker_orchestrator` for serial/concurrent translation worker loops through injected callbacks.
- `run_guarded_gui_translation_lifecycle(...)`, which runs the guarded worker and returns a finalized `GuiTranslationFinishState`.
- `gui_translation_lifecycle` helpers that plan legacy GUI start state and finalize worker results into legacy GUI state fields.
- `BatchTaskRecord` and `BatchController` for normalized batch queue state.
- `tools/wire_gui_translation_session.py` now applies idempotent first-pass GUI wiring locally:
  - insert controller imports;
  - initialize `self.translation_run_guard` and `self.current_translation_session`;
  - replace `start_translation()` resume/reset planning with `start_gui_translation_session(...)`;
  - apply `session.start_state` to legacy fields;
  - pass `session` into the translation thread;
  - cancel the active guarded session from `stop_translation()`.

### 3.2 Provider adapter and engine integration

Completed behavior:

- Unified provider request/response/error contracts.
- Timeout coercion and adapter-level timeout handling.
- Adapter bridge for non-streaming OpenAI-compatible, Gemini and Claude paths.
- `timeout_seconds` in `APIConfig` serialization/loading.

Not completed:

- Streaming OpenAI-compatible path still uses direct SDK client logic and should be evaluated separately.
- `book_translator_gui.pyw` still needs direct file modification or local patch-tool execution before runtime uses guarded sessions.
- `translate_text()` still needs to become a thin adapter around `run_guarded_gui_translation_lifecycle(...)`.
- `translate_segment()` still needs a config parameter to avoid background Tk variable reads.

### 3.3 Tests added

Focused unit tests now include:

- `tests/test_translation_run_config.py`
- `tests/test_run_guard.py`
- `tests/test_gui_translation_adapter.py`
- `tests/test_gui_translation_session.py`
- `tests/test_wire_gui_translation_session.py`
- `tests/test_translation_worker_runtime.py`
- `tests/test_translation_worker_orchestrator.py`
- `tests/test_gui_translation_workflow.py`
- `tests/test_gui_translation_lifecycle.py`
- `tests/test_batch_task.py`
- `tests/test_batch_controller.py`
- provider and engine bridge tests

Recent test additions/fixes:

- `tests/test_wire_gui_translation_session.py` now covers import insertion, guarded state initialization, stop cancellation, `start_translation()` session wiring, removal of old resume/thread blocks, legacy import upgrade, idempotency and missing-anchor failure.
- CI and `python-tests` passed on `313e79527a9f186ae0702a0cd65f869a30506165`, confirming the first-pass GUI wiring patch-tool/docs head.
- Latest start-session patch-tool head `ec7f93bfca05c325b92c1f2ca45bc6182c7e2077` still needs CI confirmation.

Recommended focused test command:

```bash
py -m pytest tests/test_translation_run_config.py tests/test_run_guard.py tests/test_gui_translation_adapter.py tests/test_gui_translation_session.py tests/test_wire_gui_translation_session.py tests/test_translation_worker_runtime.py tests/test_translation_worker_orchestrator.py tests/test_gui_translation_workflow.py tests/test_gui_translation_lifecycle.py tests/test_batch_task.py tests/test_batch_controller.py tests/test_provider_base.py tests/test_openai_compatible_provider.py tests/test_openai_compatible_factory.py tests/test_gemini_provider.py tests/test_claude_provider.py tests/test_engine_bridge.py tests/test_translation_engine_adapter_bridge.py tests/test_translation_engine_gemini_claude_adapter_bridge.py -q
```

## 4. Remaining work backlog

### P0 — finish stability phase 1

1. Confirm CI on latest start-session patch-tool head `ec7f93bfca05c325b92c1f2ca45bc6182c7e2077`.
2. Apply or further extend `tools/wire_gui_translation_session.py` against `book_translator_gui.pyw`.
3. Rewire `book_translator_gui.pyw` worker path:
   - replace `BookTranslatorGUI.translate_text()` body with a thin adapter around `run_guarded_gui_translation_lifecycle(...)`;
   - apply the returned `GuiTranslationFinishState` via `schedule_gui_translation_final_state(...)`;
   - pass the config snapshot into `translate_segment()`;
   - stop background worker reads of `self.concurrency_var`, `self.target_language_var`, `self.style_var`.
4. Guard worker UI writes through guarded workflow events.
5. Rewire GUI batch processing through `BatchController` and `load_file_content(..., silent=True)`.
6. Evaluate streaming provider path.

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

### 2026-06-26 — guarded GUI workflow/lifecycle/session foundation

Added run config, run guard, GUI adapter helpers, worker runtime helpers, worker orchestrator, guarded GUI workflow, GUI lifecycle finalization helpers, final guarded GUI update helpers and GUI translation session helpers.

### 2026-06-26 — GUI wiring patch tooling

Added `tools/wire_gui_translation_session.py` and `tests/test_wire_gui_translation_session.py`. The tool now covers first-pass `book_translator_gui.pyw` wiring for imports, guarded session state initialization, `start_translation()` session creation/start-state application/thread argument passing, and `stop_translation()` cancellation.

## 6. Mandatory update rule for future implementation

Every future implementation step MUST update this file before the response is considered complete.