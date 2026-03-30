# Release checklist

Use this checklist before creating a Git tag and a GitHub Release.

## 1. Repository hygiene
- Ensure runtime files are not tracked: `translator_config.json`, `translation_memory.db`, `translation_cache.json`, `batch_tasks.json`, `config_backups/`.
- Verify the app still migrates any legacy repo-root config/database into the user runtime directory.
- Confirm the repository homepage README is the product README, not a patch wrapper.

## 2. Validation
- Run the local test entrypoint.
- Run the translation-memory migration regression test.
- Smoke test at least one provider configuration and one OCR-disabled path.

## 3. Versioning
- Update version constants if behavior changed.
- Add an entry to `CHANGELOG.md`.
- Summarize noteworthy breaking changes, migration steps, and dependency changes.

## 4. GitHub release
- Create a signed tag when possible.
- Create a GitHub Release from that tag.
- Include release notes, migration notes, and any known limitations.
- Attach binaries or packaged artifacts only if they were built from the tagged commit.

## 5. Post-release follow-up
- Verify the release page renders correctly.
- Open a follow-up issue for any deferred cleanup.
- Keep the next development changes under the `Unreleased` section in `CHANGELOG.md`.
