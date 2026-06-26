# Upgrade Plan & Progress Tracker

> Persistent source of truth for the upgrade/refactor work. Every implementation step must update this file so progress is not lost when chat context expires.

## 0. Current branch and PR

- Repository: `throwbananana/translate`
- Working branch: `upgrade/stability-phase-1`
- Pull request: `#2` — `Refactor: add stability phase controller groundwork`
- Base branch: `main`
- Last recorded progress date: `2026-06-26`
- Last green CI-confirmed head before this update: `61916c0c6170d3bee32aa3f6a7765b6fd53f7897`
- Latest implementation commits before this tracker update:
  - `e00f4883413de51462e9706c15f6f7dd6d581636` — extend GUI wiring patch to guarded lifecycle
  - `8f5888bbfd28aa6a841ef3439105a6c15e31f436` — cover guarded lifecycle GUI wiring patch
- Test status:
  - GitHub Actions `CI` and `python-tests` passed on `61916c0c6170d3bee32aa3f6a7765b6fd53f7897`.
  - The new guarded-lifecycle patch-tool commits above still need GitHub Actions confirmation after this docs update.
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
| Overall upgrade plan | ~72% | Provider adapter wiring is mostly complete; controller-side translation orchestration, guarded GUI workflow/lifecycle/session helpers, final guarded updates, and reproducible GUI wiring patch tooling now exist. The patch tool now also generates the guarded `translate_text(...)` / config-snapshot `translate_segment(...)` rewrite, but the generated GUI diff has not yet been committed. |
| Stability phase 1 foundations | ~99% | Run config, run guard, GUI adapter, guarded GUI workflow/lifecycle/session helpers, batch controller, provider adapters, worker runtime helpers, worker orchestrator, engine provider wiring and GUI wiring patch tooling are added. Latest guarded-lifecycle patch-tool commits still need CI confirmation. |
| Provider timeout / adapter layer | ~95% | OpenAI-compatible, Gemini and Claude non-streaming engine paths are wired through adapters. Streaming path still needs separate evaluation. |
| GUI thread-safety integration | ~80% | Helper layer can snapshot config, plan resume/reset state, guard queued UI writes, compute worker-loop decisions without Tk reads, run/finalize workers through injected callbacks, finish the run after final GUI state is applied, expose one session object for GUI start/stop wiring, and now has an idempotent patch tool covering `start_translation()`, `stop_translation()`, guarded `translate_text(...)`, final-state application, and config-snapshot `translate_segment(...)`. Runtime still needs the generated patch applied/reviewed in `book_translator_gui.pyw`. |
| Batch silent/resumable flow | ~55% | `BatchTaskRecord` and `BatchController` exist; GUI batch flow is not rewired yet. |
| CI confirmation | ~90% | `61916c0c6170d3bee32aa3f6a7765b6fd53f7897` is confirmed green. New guarded-lifecycle patch-tool/docs head still needs CI confirmation. |

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

### 3.2 Provider adapter and engine integration

Completed behavior:

- Unified provider request/response/error contracts.
- Timeout coercion and adapter-level timeout handling.
- Adapter bridge for non-streaming OpenAI-compatible, Gemini and Claude paths.
- `timeout_seconds` in `APIConfig` serialization/loading.

Not completed:

- Streaming OpenAI-compatible path still uses direct SDK client logic and should be evaluated separately.
- `book_translator_gui.pyw` still needs direct file modification or local patch-tool execution before runtime uses guarded sessions.
- The generated guarded `translate_text(...)` rewrite needs review for legacy retry/cache behavior before being committed to the actual GUI file.
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
- I locally syntax-checked the updated patch tool and ran the focused patch-tool test module in a temporary copy: 6 tests passed.
- GitHub Actions `CI` and `python-tests` passed on `61916c0c6170d3bee32aa3f6a7765b6fd53f7897`; the new guarded-lifecycle patch-tool commits need CI confirmation.

Recommended focused test command:

```bash
py -m pytest tests/test_translation_run_config.py tests/test_run_guard.py tests/test_gui_translation_adapter.py tests/test_gui_translation_session.py tests/test_wire_gui_translation_session.py tests/test_translation_worker_runtime.py tests/test_translation_worker_orchestrator.py tests/test_gui_translation_workflow.py tests/test_gui_translation_lifecycle.py tests/test_batch_task.py tests/test_batch_controller.py tests/test_provider_base.py tests/test_openai_compatible_provider.py tests/test_openai_compatible_factory.py tests/test_gemini_provider.py tests/test_claude_provider.py tests/test_engine_bridge.py tests/test_translation_engine_adapter_bridge.py tests/test_translation_engine_gemini_claude_adapter_bridge.py -q
```

## 4. Remaining work backlog

### P0 — finish stability phase 1

1. Confirm CI on the guarded-lifecycle patch-tool/docs head.
2. Run `tools/wire_gui_translation_session.py` against `book_translator_gui.pyw` locally and review the generated diff.
3. Commit the reviewed generated GUI diff only after confirming:
   - `translate_text()` calls `run_guarded_gui_translation_lifecycle(...)`;
   - final state is applied via `schedule_gui_translation_final_state(...)`;
   - `translate_segment(..., config=...)` receives the config snapshot;
   - worker-owned Tk reads from `self.concurrency_var`, `self.target_language_var`, and `self.style_var` are removed.
4. Validate whether the legacy single-thread retry behavior should remain inside the guarded worker flow or become a follow-up controller helper.
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

Added `tools/wire_gui_translation_session.py` and `tests/test_wire_gui_translation_session.py`. The tool covered first-pass `book_translator_gui.pyw` wiring for imports, guarded session state initialization, `start_translation()` session creation/start-state application/thread argument passing, and `stop_translation()` cancellation.

### 2026-06-26 — guarded lifecycle patch-tool extension

Extended `tools/wire_gui_translation_session.py` so the generated GUI patch can rewrite `translate_text(self, session=None)` into a guarded workflow adapter and rewrite `translate_segment(..., config=None)` to use immutable config snapshots. Updated `tests/test_wire_gui_translation_session.py` to cover the generated guarded lifecycle and segment-config rewrite.

## 6. Mandatory update rule for future implementation

Every future implementation step MUST update this file before the response is considered complete.
