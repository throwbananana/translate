#!/usr/bin/env bash
set -euo pipefail

PATCH_FILES=(
  "0001-project-hardening-readme-deps-tests-ci-repaired.patch"
)

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "Not a git repository."
  exit 1
fi

if [[ -n "$(git status --porcelain)" ]]; then
  echo "Working tree is not clean. Commit or stash your changes first."
  exit 1
fi

for patch in "${PATCH_FILES[@]}"; do
  if [[ ! -f "$patch" ]]; then
    echo "Missing patch file: $patch"
    exit 1
  fi
done

echo "Checking patch applicability..."
if git apply --check "0001-project-hardening-readme-deps-tests-ci-repaired.patch"; then
  git apply "0001-project-hardening-readme-deps-tests-ci-repaired.patch"
  echo
  echo "Patch applied successfully."
  if [[ -f requirements.txt ]]; then
    python -m pip install -r requirements.txt
  fi
  if [[ -f requirements-dev.txt ]]; then
    python -m pip install -r requirements-dev.txt
  fi
  if command -v pytest >/dev/null 2>&1; then
    pytest -q
  fi
  exit 0
fi

echo
echo "Patch does not apply cleanly."
echo "This usually means the target tree already contains these changes"
echo "or has diverged from the baseline the patch was generated from."
echo
echo "If you are running this inside throwbananana/translate main, that is expected:"
echo "the repository already contains most or all of this patch content."
exit 1
