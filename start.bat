@echo off
setlocal

echo ========================================
echo Book Translator v2.3.1
echo ========================================
echo.
echo Starting translator...
echo.

where py >nul 2>nul
if errorlevel 1 (
  echo Python Launcher ^(py^) was not found.
  echo Please install Python from https://www.python.org/downloads/windows/
  echo and make sure the Python Launcher is enabled.
  echo.
  pause
  exit /b 1
)

py book_translator_gui.pyw
if errorlevel 1 (
  echo.
  echo Failed to start. Try: py -m pip install -r requirements.txt
  pause
)
