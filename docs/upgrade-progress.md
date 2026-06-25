# Upgrade Plan & Progress Tracker

> This file is the persistent source of truth for the upgrade/refactor work.  
> Every implementation step MUST update this file in the same PR/commit series so progress is not lost when chat context expires.

## 0. Current branch and PR

- Repository: `throwbananana/translate`
- Working branch: `upgrade/stability-phase-1`
- Pull request: `#2` — `Refactor: add stability phase controller groundwork`
- Base branch: `main`
- Last recorded progress date: `2026-06-25`
- Test status: **not run in this environment yet**
- Merge guidance: use **Squash merge** because this branch contains many process commits.

## 1. Upgrade objective

The project is already feature-rich, but the main risks are runtime stability and maintainability:

1. `book_translator_gui.pyw` still owns too much workflow orchestration.
2. Background workers can still read Tk variables directly.
3. Stopped/cancelled translations can still produce late UI writes until the GUI is rewired.
4. Batch processing can still block on message boxes until `silent=True` is wired into GUI loading.
5. Provider timeout handling was inconsistent across OpenAI-compatible, Gemini and Claude paths.
6. Batch task persistence needs normalized status/error/output tracking.
7. Tests need to be run and CI verified before merge.

The upgrade goal is to make the app safer to run for long translations and easier to maintain by moving state and provider logic into small testable modules before changing the large GUI file.

## 2. Progress summary

Approximate status after the latest recorded implementation:

| Area | Progress | Notes |
|---|---:|---|
| Overall upgrade plan | ~47% | Core foundations are in place, but GUI rewiring is still pending. |
| Stability phase 1 foundations | ~90% | Run config, run guard, GUI adapter, batch controller, provider adapters are added. |
| Provider timeout / adapter layer | ~85% | OpenAI-compatible engine path is wired; Gemini/Claude adapters exist but are not wired into `translation_engine.py` yet. |
| GUI thread-safety integration | ~35% | Helper layer exists; `book_translator_gui.pyw` is not rewired yet. |
| Batch silent/resumable flow | ~55% | `BatchTaskRecord` and `BatchController` exist; GUI batch flow is not rewired yet. |
| Tests / CI confirmation | 0% | Tests have been added but not run in this environment. |

## 3. Completed work

### 3.1 Controller foundation

Added `controllers/` as a GUI-free orchestration/helper layer.

Completed files:

- `controllers/__init__.py`
- `controllers/README.md`
- `controllers/translation_run_config.py`
- `controllers/run_guard.py`
- `controllers/gui_translation_adapter.py`
- `controllers/batch_task.py`
- `controllers/batch_controller.py`

Completed behavior:

- Immutable `TranslationRunConfig` for background translation runs.
- Defensive coercion of GUI/Tk-derived values.
- Centralized translation style prompt mapping.
- `TranslationRunGuard` for rejecting stale worker results after stop/cancel.
- GUI-facing adapter helpers:
  - read Tk-style values on the GUI thread,
  - start guarded translation runs,
  - decide whether a worker result can still update UI,
  - cancel the active guarded run.
- `BatchTaskRecord` for normalized task state.
- `BatchController` for queue normalization, next-task selection, status updates, cancellation, snapshot counts and serialization.
- `should_load_batch_file_silently(...)` helper for future `load_file_content(..., silent=True)` wiring.

### 3.2 Provider adapter foundation

Added `providers/` adapter layer.

Completed files:

- `providers/__init__.py`
- `providers/base.py`
- `providers/errors.py`
- `providers/openai_compatible.py`
- `providers/openai_compatible_factory.py`
- `providers/engine_bridge.py`
- `providers/gemini_provider.py`
- `providers/claude_provider.py`

Completed behavior:

- Unified `ProviderRequest` and `ProviderResponse` data structures.
- Unified provider error classes, including `ProviderTimeoutError`.
- Timeout coercion through `coerce_timeout_seconds(...)`.
- OpenAI-compatible adapter with explicit client/request timeout handling.
- Factory helpers for OpenAI, DeepSeek, LM Studio and custom local models.
- Engine bridge helpers that preserve the current `(translated_text, model)` return shape.
- Gemini adapter with timeout request options and timeout error mapping.
- Claude adapter with client-level timeout and request-level timeout fallback compatibility.

### 3.3 `translation_engine.py` integration

Completed:

- Added `timeout_seconds` to `APIConfig`.
- Added timeout serialization in `_serialize_api_configs()`.
- Added timeout loading in `create_engine_with_config(...)`.
- Added timeout storage for custom local model registration.
- Routed non-streaming OpenAI / DeepSeek / LM Studio / custom-local calls through the OpenAI-compatible adapter bridge.
- Updated custom API requests to use `config.timeout_seconds` instead of a fixed timeout.

Not completed:

- Gemini and Claude methods in `translation_engine.py` still need to be routed through `GeminiProvider` / `ClaudeProvider`.
- Streaming OpenAI-compatible path still uses direct SDK client logic and should be evaluated separately.

### 3.4 Tests added

Added focused unit tests:

- `tests/test_translation_run_config.py`
- `tests/test_run_guard.py`
- `tests/test_gui_translation_adapter.py`
- `tests/test_batch_task.py`
- `tests/test_batch_controller.py`
- `tests/test_provider_base.py`
- `tests/test_openai_compatible_provider.py`
- `tests/test_openai_compatible_factory.py`
- `tests/test_gemini_provider.py`
- `tests/test_claude_provider.py`
- `tests/test_engine_bridge.py`
- `tests/test_translation_engine_adapter_bridge.py`

Recommended focused test command:

```bash
py -m pytest tests/test_translation_run_config.py tests/test_run_guard.py tests/test_gui_translation_adapter.py tests/test_batch_task.py tests/test_batch_controller.py tests/test_provider_base.py tests/test_openai_compatible_provider.py tests/test_openai_compatible_factory.py tests/test_gemini_provider.py tests/test_claude_provider.py tests/test_engine_bridge.py tests/test_translation_engine_adapter_bridge.py -q
```

## 4. Remaining work backlog

### P0 — finish stability phase 1

1. Rewire `book_translator_gui.pyw` translation start/stop path:
   - initialize `self.translation_run_guard = TranslationRunGuard()` or use adapter helper;
   - call `start_guarded_translation_run(...)` inside `start_translation()`;
   - pass the guarded run/config snapshot into `translate_text()`;
   - pass config into `translate_segment()`;
   - stop background worker reads of `self.concurrency_var`, `self.target_language_var`, `self.style_var`.

2. Guard worker UI writes:
   - before every background-worker result writes to widgets, use `should_apply_gui_update(...)` or `guarded_gui_update(...)`;
   - `stop_translation()` should call `cancel_guarded_translation_run(...)`.

3. Rewire GUI batch processing:
   - normalize persisted queue through `BatchController`;
   - use controller status transitions in `process_next_batch_file()`;
   - add `load_file_content(filepath, silent=False)`;
   - call `load_file_content(..., silent=True)` during batch processing.

4. Route Gemini / Claude engine methods through adapters:
   - `_translate_with_gemini(...)` -> `GeminiProvider`;
   - `_translate_with_claude(...)` -> `ClaudeProvider`;
   - preserve existing tuple return shape and quality/memory behavior.

5. Run focused tests and then full tests.

### P1 — controller extraction after P0

1. Extract `TranslationController` or equivalent to own background translation coordination.
2. Extract `WorkspaceController` for file loading / resume / content state.
3. Extract `BatchController` usage fully out of GUI event handlers.
4. Add regression tests for cancellation, stale result skipping and batch resume behavior.

### P2 — repository hygiene and release readiness

1. Clean tracked historical artifacts such as `.mbox`, `.bak`, and patch bundle files if still present.
2. Add or confirm `LICENSE`.
3. Run full test suite and CI.
4. Squash merge the PR.

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

Status after this implementation:

- Overall upgrade plan: ~47%.
- Stability phase 1 foundations: ~90%.
- Provider timeout / adapter layer: ~85%.
- GUI thread-safety integration: ~35%.
- Batch silent/resumable flow: ~55%.
- Tests/CI: not run yet.

## 6. Mandatory update rule for future implementation

Every future implementation step MUST update this file before the response is considered complete.

When adding code, update at least these sections:

1. `Progress summary` — adjust percentages and short notes.
2. `Completed work` — add or refine completed items.
3. `Remaining work backlog` — remove completed tasks or add newly discovered tasks.
4. `Implementation log` — add a dated entry with:
   - files changed,
   - behavior changed,
   - tests added/run,
   - known risks or follow-up.

Suggested log template:

```markdown
### YYYY-MM-DD — short title

Changed files:

- `path/to/file.py`
- `tests/test_x.py`

Completed:

- ...

Tests:

- Run: `...`
- Result: pass/fail/not run

Remaining / risks:

- ...
```
