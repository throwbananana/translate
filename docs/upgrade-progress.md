# Upgrade Plan & Progress Tracker

> Persistent source of truth for the upgrade/refactor work. Every implementation step must update this file so progress is not lost when chat context expires.

## 0. Current branch and PR

- Repository: `throwbananana/translate`
- Working branch: `upgrade/stability-phase-1`
- Pull request: `#2` — `Refactor: add stability phase controller groundwork`
- Base branch: `main`
- Last recorded progress date: `2026-07-02`
- Last green CI-confirmed head before this update: `61916c0c6170d3bee32aa3f6a7765b6fd53f7897`
- Latest implementation state before this tracker update:
  - `2adb4dcae3b5983dc512f72c9f77565a2558b04c` — latest remote branch head before the generated GUI wiring was applied locally
  - This update applies the generated guarded-session wiring to `book_translator_gui.pyw`
- Test status:
  - GitHub Actions `CI` and `python-tests` passed on `61916c0c6170d3bee32aa3f6a7765b6fd53f7897`.
  - Local validation after applying the generated GUI wiring passed on 2026-07-02:
    - `python tools/wire_gui_translation_session.py --check book_translator_gui.pyw`
    - focused controller/provider/GUI wiring pytest command listed below
    - `python -m pytest -q`
    - `python test_startup.py`
    - `python test_core_features.py`
  - GitHub Actions confirmation is still required on the pushed generated-GUI-wiring head before merging.
- Merge guidance: use **Squash merge** because this branch contains many process commits.

## 1. Upgrade objective

The project is feature-rich, but the main risks are runtime stability and maintainability:

1. `book_translator_gui.pyw` still owns too much workflow orchestration.
2. Background workers can still read Tk variables directly until the generated GUI patch is applied.
3. Stopped/cancelled translations can still produce late UI writes until the actual GUI file is rewired.
4. Batch processing can still block on message boxes until `silent=True` is wired into GUI loading.
5. Provider timeout handling was inconsistent across OpenAI-compatible, Gemini and Claude paths.
6. Batch task persistence needs normalized status/error/output tracking.
7. CI must remain green before merge.

## 2. Progress summary

| Area | Progress | Notes |
|---|---:|---|
| Overall upgrade plan | ~78% | Provider adapter wiring is mostly complete; controller-side translation orchestration, guarded GUI workflow/lifecycle/session helpers, final guarded updates, reproducible GUI wiring patch tooling, and the generated `book_translator_gui.pyw` guarded-session diff now exist locally. |
| Stability phase 1 foundations | ~100% | Run config, run guard, GUI adapter, guarded GUI workflow/lifecycle/session helpers, batch controller, provider adapters, worker runtime helpers, worker orchestrator, engine provider wiring, GUI wiring patch tooling, and the generated GUI wiring diff are in place. Generated-GUI-wiring head still needs GitHub Actions confirmation before merge. |
| Provider timeout / adapter layer | ~95% | OpenAI-compatible, Gemini and Claude non-streaming engine paths are wired through adapters. Streaming path still needs separate evaluation. |
| GUI thread-safety integration | ~90% | `book_translator_gui.pyw` now creates guarded translation sessions, passes the session into the worker thread, routes `translate_text(...)` through `run_guarded_gui_translation_lifecycle(...)`, applies final state through `schedule_gui_translation_final_state(...)`, and calls `translate_segment(..., config=...)` from guarded workers so target language/style/memory/glossary settings come from an immutable snapshot. |
| Batch silent/resumable flow | ~55% | `BatchTaskRecord` and `BatchController` exist; GUI batch flow is not rewired yet. |
| CI confirmation | ~90% | `61916c0c6170d3bee32aa3f6a7765b6fd53f7897` is confirmed green. The generated-GUI-wiring head still needs GitHub Actions confirmation before merge. |

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
- `tools/wire_gui_translation_session.py` now applies idempotent GUI wiring locally:
  - insert or upgrade controller imports;
  - initialize `self.translation_run_guard` and `self.current_translation_session`;
  - replace `start_translation()` resume/reset planning with `start_gui_translation_session(...)`;
  - apply `session.start_state` to legacy fields;
  - pass `session` into the translation thread;
  - cancel the active guarded session from `stop_translation()`;
  - rewrite `translate_text(self, session=None)` into a thin adapter around `run_guarded_gui_translation_lifecycle(...)`;
  - apply `GuiTranslationFinishState` through `schedule_gui_translation_final_state(...)`;
  - rewrite `translate_segment(..., config=None)` so guarded workers use immutable config snapshots instead of reading `target_language_var` / `style_var` from the background thread.
- The generated guarded-session wiring has now been applied to `book_translator_gui.pyw`:
  - `start_translation()` creates and stores a `GuiTranslationSession`;
  - `stop_translation()` cancels the active guarded run;
  - the worker thread receives the session as an argument;
  - `translate_text(self, session=None)` delegates to the guarded lifecycle adapter;
  - final GUI state is applied through `_apply_guarded_translation_finish_state(...)`;
  - guarded worker calls use `translate_segment(..., config=session.config)`.

### 3.2 Provider adapter and engine integration

Completed behavior:

- Unified provider request/response/error contracts.
- Timeout coercion and adapter-level timeout handling.
- Adapter bridge for non-streaming OpenAI-compatible, Gemini and Claude paths.
- `timeout_seconds` in `APIConfig` serialization/loading.

Not completed:

- Streaming OpenAI-compatible path still uses direct SDK client logic and should be evaluated separately.
- The generated guarded `translate_text(...)` rewrite still needs follow-up review for whether legacy single-thread retry behavior should be reintroduced in the guarded worker flow.
- Batch processing still needs GUI rewiring through `BatchController`.

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

- `tests/test_wire_gui_translation_session.py` now covers import insertion/upgrades, guarded state initialization, stop cancellation, `start_translation()` session wiring, guarded lifecycle `translate_text(...)` generation, final-state scheduling, `translate_segment(..., config=None)` snapshot use, removal of old resume/thread blocks, idempotency and missing-anchor failure.
- The generated GUI wiring was applied to the real `book_translator_gui.pyw`, then verified with the patch-tool idempotency check, the focused controller/provider/GUI wiring pytest command, full pytest, startup script and core-feature script.
- GitHub Actions `CI` and `python-tests` passed on `61916c0c6170d3bee32aa3f6a7765b6fd53f7897`; the generated-GUI-wiring head needs CI confirmation after push.

Recommended focused test command:

```bash
py -m pytest tests/test_translation_run_config.py tests/test_run_guard.py tests/test_gui_translation_adapter.py tests/test_gui_translation_session.py tests/test_wire_gui_translation_session.py tests/test_translation_worker_runtime.py tests/test_translation_worker_orchestrator.py tests/test_gui_translation_workflow.py tests/test_gui_translation_lifecycle.py tests/test_batch_task.py tests/test_batch_controller.py tests/test_provider_base.py tests/test_openai_compatible_provider.py tests/test_openai_compatible_factory.py tests/test_gemini_provider.py tests/test_claude_provider.py tests/test_engine_bridge.py tests/test_translation_engine_adapter_bridge.py tests/test_translation_engine_gemini_claude_adapter_bridge.py -q
```

## 4. Remaining work backlog

### P0 — finish stability phase 1

1. Confirm GitHub Actions on the generated-GUI-wiring head before merging.
2. Validate whether the legacy single-thread retry behavior should remain inside the guarded worker flow or become a follow-up controller helper.
3. Rewire GUI batch processing through `BatchController` and `load_file_content(..., silent=True)`.
4. Evaluate streaming provider path.

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

Added `tools/wire_gui_translation_session.py` and `tests/test_wire_gui_translation_session.py`. The tool covered first-pass `book_translator_gui.pyw` wiring for imports, guarded session state initialization, `start_translation()` session creation/start-state application/thread argument passing, and `stop_translation()` cancellation.

### 2026-06-26 — guarded lifecycle patch-tool extension

Extended `tools/wire_gui_translation_session.py` so the generated GUI patch can rewrite `translate_text(self, session=None)` into a guarded workflow adapter and rewrite `translate_segment(..., config=None)` to use immutable config snapshots. Updated `tests/test_wire_gui_translation_session.py` to cover the generated guarded lifecycle and segment-config rewrite.

### 2026-07-02 — generated guarded GUI wiring applied

Ran `tools/wire_gui_translation_session.py book_translator_gui.pyw` and reviewed the generated diff. `book_translator_gui.pyw` now uses guarded translation sessions for start/stop, worker lifecycle, final-state application and immutable config-snapshot translation calls. Local validation passed with the patch-tool idempotency check, focused controller/provider/GUI wiring pytest command, full pytest, `test_startup.py` and `test_core_features.py`.

## 6. Mandatory update rule for future implementation

Every future implementation step MUST update this file before the response is considered complete.
