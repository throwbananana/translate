@echo off
echo ========================================
echo   Book Translator v1.1
echo ========================================
echo.
echo Starting translator...
echo.

python book_translator_gui.pyw

if errorlevel 1 (
    echo.
    echo Failed to start!
    echo Please check:
    echo 1. Python is installed
    echo 2. Dependencies are installed
    echo.
    echo Try: pip install -r requirements.txt
    echo.
    pause
)
