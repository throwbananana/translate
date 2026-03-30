#!/usr/bin/env bash
set -euo pipefail

git apply --check 0001-project-hardening-readme-deps-tests-ci.patch
git apply --check 0002-runtime-bugfixes-resume-autofill-batch.patch
git apply --check 0003-modularization-prep-extract-pure-helper-functions.patch
git apply --check 0004-modularization-extract-api-selection-and-dispatch.patch
git apply --check 0005-modularization-extract-analysis-api-implementations.patch
git apply --check 0006-modularization-extract-runtime-state-persistence.patch
git apply --check 0007-modularization-extract-export-helpers.patch
git apply --check 0008-modularization-extract-library-ui-helpers.patch
git apply --check 0009-modularization-extract-ui-view-helpers.patch

git apply 0001-project-hardening-readme-deps-tests-ci.patch
git apply 0002-runtime-bugfixes-resume-autofill-batch.patch
git apply 0003-modularization-prep-extract-pure-helper-functions.patch
git apply 0004-modularization-extract-api-selection-and-dispatch.patch
git apply 0005-modularization-extract-analysis-api-implementations.patch
git apply 0006-modularization-extract-runtime-state-persistence.patch
git apply 0007-modularization-extract-export-helpers.patch
git apply 0008-modularization-extract-library-ui-helpers.patch
git apply 0009-modularization-extract-ui-view-helpers.patch

python -m pip install -r requirements.txt
python -m pip install -r requirements-dev.txt
pytest -q
