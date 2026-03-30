@echo off
setlocal

git status --porcelain >nul 2>nul
if errorlevel 1 (
  echo Not a git repository or git is unavailable.
  exit /b 1
)

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

:error
echo.
echo git am failed.
echo If needed, run: git am --abort
exit /b 1

:end
endlocal
