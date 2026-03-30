@echo off
setlocal enabledelayedexpansion

git apply --check 0001-project-hardening-readme-deps-tests-ci.patch || goto :error
git apply --check 0002-runtime-bugfixes-resume-autofill-batch.patch || goto :error
git apply --check 0003-modularization-prep-extract-pure-helper-functions.patch || goto :error
git apply --check 0004-modularization-extract-api-selection-and-dispatch.patch || goto :error
git apply --check 0005-modularization-extract-analysis-api-implementations.patch || goto :error
git apply --check 0006-modularization-extract-runtime-state-persistence.patch || goto :error
git apply --check 0007-modularization-extract-export-helpers.patch || goto :error
git apply --check 0008-modularization-extract-library-ui-helpers.patch || goto :error
git apply --check 0009-modularization-extract-ui-view-helpers.patch || goto :error

git apply 0001-project-hardening-readme-deps-tests-ci.patch || goto :error
git apply 0002-runtime-bugfixes-resume-autofill-batch.patch || goto :error
git apply 0003-modularization-prep-extract-pure-helper-functions.patch || goto :error
git apply 0004-modularization-extract-api-selection-and-dispatch.patch || goto :error
git apply 0005-modularization-extract-analysis-api-implementations.patch || goto :error
git apply 0006-modularization-extract-runtime-state-persistence.patch || goto :error
git apply 0007-modularization-extract-export-helpers.patch || goto :error
git apply 0008-modularization-extract-library-ui-helpers.patch || goto :error
git apply 0009-modularization-extract-ui-view-helpers.patch || goto :error

py -m pip install -r requirements.txt
py -m pip install -r requirements-dev.txt
py -m pytest -q

echo.
echo All patches applied successfully.
goto :end

:error
echo.
echo Patch apply failed.
exit /b 1

:end
endlocal
