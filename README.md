# translate patch series (mailbox-style)

This directory contains mailbox-style wrappers around the earlier unified diffs.
They are meant to be easier to review and to convert into real commits later.

## What these files are

- `0000-cover-letter.patch`: series overview
- `0001`..`0004`: one patch-message per logical change

## Important limitation

These patches were generated from prepared diff files, not exported from a real
Git commit history. The `From <sha>` values are synthetic content hashes used to
make the files look and behave more like `git format-patch` output.

## Apply options

### If you only want the file changes

```bash
git apply 0001-secure-config-and-ignore-runtime-data.patch
```

Use `git apply --check <patch>` first if you want to verify applicability.

### If you want to turn them into commits later

These mailbox-style files are best treated as review artifacts first. The most
reliable path is:

1. apply the original plain diffs or these mailbox diffs on a topic branch
2. inspect and test the result
3. create real commits with `git commit`
4. export them again with `git format-patch`

## Suggested order

1. `0001` security and ignore rules
2. `0002` runtime path and translation-memory relocation
3. `0003` DOCX stabilization
4. `0004` parallel batch hardening
