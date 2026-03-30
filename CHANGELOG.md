# Changelog

All notable repository-facing changes should be recorded here.

## Unreleased

### Repository hygiene and release prep
- Stop tracking the checked-in `translation_memory.db` runtime database.
- Keep compatibility for existing users by migrating a legacy repo-root `translation_memory.db` into the user runtime directory on first launch.
- Add a regression test for translation-memory migration.
- Add a release checklist so future tags and GitHub releases have a repeatable process.

## Historical notes
- Prior maintenance notes are still available in `v2.4_UPDATE_LOG.txt` and `v2.6_UPDATE_LOG.txt`.
- Older ad-hoc text summaries remain in the repository root until they are folded into this changelog.
