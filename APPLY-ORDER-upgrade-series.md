# Upgrade patch series apply order

This note is meant to be used with the proposed `0005`–`0019` patch series.

## Why this order

The upstream README describes its own mailbox-style files as review artifacts,
and recommends this workflow:

1. apply on a topic branch
2. inspect and test the result
3. create real commits with `git commit`
4. export again with `git format-patch`

It also gives an explicit ordered application model for the earlier `0001`–`0004`
series, so this follow-up keeps the same idea: small logical steps, checked in
sequence.

## Recommended branch

```bash
git checkout -b chore/upgrade-series
```

## Apply commands

For each patch:

```bash
git apply --check <patch>
git apply <patch>
```

## Order

### Phase A — foundation and low-risk hardening

1. `0005-unify-runtime-data-paths.patch`
2. `0006-stabilize-docx-handler.patch`
3. `0007-harden-test-suite.patch`

Validate here before continuing:

```bash
python -m py_compile config_manager.py translation_memory.py docx_handler.py
python test_core_features.py
python test_full_workflow.py
```

### Phase B — config and engine/runtime convergence

4. `0008-extract-runtime-state-store.patch`
5. `0009-centralize-config-runtime-profile.patch`
6. `0010-centralize-translation-runtime-profile.patch`
7. `0011-centralize-engine-runtime-sync.patch`

Validate here:

```bash
python -m py_compile book_translator_gui.pyw config_manager.py translation_engine.py runtime_state.py
```

Then manually verify:
- GUI starts
- config still loads/saves
- cache and batch-task files are created under the user runtime dir

### Phase C — batch execution extraction

8. `0012-extract-batch-translation-executor.patch`

Validate here:

```bash
python -m py_compile book_translator_gui.pyw batch_translation_executor.py
```

Then manually verify:
- single-thread translation still works
- concurrent translation still works
- pause/stop behavior still works
- checkpointing still works

### Phase D — failed-segment workflow extraction

9.  `0013-extract-failed-segment-manager.patch`
10. `0014-extract-retry-failed-segment-service.patch`
11. `0015-extract-failed-segment-panel.patch`
12. `0016-extract-retry-api-resolver.patch`
13. `0017-extract-failed-segment-actions.patch`
14. `0018-extract-failed-segment-controller.patch`
15. `0019-extract-failed-segment-feature.patch`

Validate here:

```bash
python -m py_compile \
  book_translator_gui.pyw \
  failed_segment_manager.py \
  retry_failed_segment_service.py \
  failed_segment_panel.py \
  retry_api_resolver.py \
  failed_segment_actions.py \
  failed_segment_controller.py \
  failed_segment_feature.py
```

Then manually verify:
- failed list populates
- selecting a failed segment updates detail text
- retry API selection behaves correctly
- retry action updates the list and cache
- manual translation save updates the list and cache

## Practical advice

- Commit after each phase, not only at the very end.
- If a patch in Phase D conflicts, stop and resolve before continuing; these
  patches intentionally build on each other.
- `0018` and `0019` are the least standalone patches in the series and are best
  treated as continuation patches on top of the earlier failed-segment work.

## Example commit checkpoints

```bash
git commit -am "chore: harden runtime paths, docx export, and tests"
git commit -am "refactor: centralize runtime/config/engine sync"
git commit -am "refactor: extract batch translation executor"
git commit -am "refactor: extract failed segment workflow"
```
