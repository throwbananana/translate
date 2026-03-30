@echo off
setlocal

if not exist .git (
  echo Not a git repository.
  exit /b 1
)

if not exist 0001-project-hardening-readme-deps-tests-ci-repaired.patch (
  echo Missing patch file: 0001-project-hardening-readme-deps-tests-ci-repaired.patch
  exit /b 1
)

git apply --check 0001-project-hardening-readme-deps-tests-ci-repaired.patch
if errorlevel 1 goto :not_applicable

git apply 0001-project-hardening-readme-deps-tests-ci-repaired.patch
if errorlevel 1 goto :error

if exist requirements.txt py -m pip install -r requirements.txt
if exist requirements-dev.txt py -m pip install -r requirements-dev.txt
py -m pytest -q

echo.
echo Patch applied successfully.
goto :end

:not_applicable
echo.
echo Patch does not apply cleanly.
echo The current tree likely already contains these changes.
exit /b 1

:error
echo.
echo Patch apply failed.
exit /b 1

:end
endlocal
