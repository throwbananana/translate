@echo off
setlocal

if not exist .git (
  echo Not a git repository or git is unavailable.
  exit /b 1
)

if exist translate-upgrade-series-0001-0009-fixed.mbox (
  echo Applying mailbox patch series with git am...
  git am --3way translate-upgrade-series-0001-0009-fixed.mbox
  if errorlevel 1 goto :error

  echo.
  echo Patch series applied successfully.
  echo Run these checks next:
  echo   git log --oneline -9
  echo   py -m pip install -r requirements.txt
  echo   py -m pip install -r requirements-dev.txt
  echo   py -m pytest -q
  goto :end
)

echo Missing mailbox series file: translate-upgrade-series-0001-0009-fixed.mbox
echo Falling back to the repaired single patch.

if not exist 0001-project-hardening-readme-deps-tests-ci-repaired.patch (
  echo Missing fallback patch file: 0001-project-hardening-readme-deps-tests-ci-repaired.patch
  exit /b 1
)

git apply --check 0001-project-hardening-readme-deps-tests-ci-repaired.patch
if errorlevel 1 goto :not_applicable

git apply 0001-project-hardening-readme-deps-tests-ci-repaired.patch
if errorlevel 1 goto :error

echo.
echo Repaired single patch applied successfully.
goto :end

:not_applicable
echo.
echo Fallback patch does not apply cleanly.
echo The current tree likely already contains these changes.
exit /b 1

:error
echo.
echo Patch apply failed.
echo If git am was started, run: git am --abort
exit /b 1

:end
endlocal
