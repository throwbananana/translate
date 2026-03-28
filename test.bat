@echo off
echo ========================================
echo   Large File Test
echo ========================================
echo.
echo Step 1: Generate test files...
py test_large_file.py
echo.
echo Step 2: Starting translator...
echo.
echo Please test:
echo   1. Load test_5k.txt (small file)
echo   2. Load test_50k.txt (large file)
echo   3. Click "Show full text" button
echo   4. Try translation
echo.
pause
py book_translator_gui.pyw
