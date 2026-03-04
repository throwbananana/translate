@echo off
echo ========================================
echo   Book Translator v1.3 - Test Suite
echo ========================================
echo.
echo Running complete test suite...
echo.
pause

echo.
echo ========================================
echo Step 1/3: Generate test files
echo ========================================
python test_large_file.py
if errorlevel 1 goto error

echo.
echo ========================================
echo Step 2/3: Test core features
echo ========================================
python test_core_features.py
if errorlevel 1 goto error

echo.
echo ========================================
echo Step 3/3: Test translation
echo ========================================
python test_actual_translation.py
if errorlevel 1 goto error

echo.
echo ========================================
echo   All Tests Passed!
echo ========================================
echo.
echo Generated files:
echo   - Test data: test_1k.txt ~ test_500k.txt
echo   - Translation: sample_book_translation_test.txt
echo   - Translation: test_50k_translation_test.txt
echo   - Report: test_report.md
echo.
echo Next steps:
echo   1. Check test_report.md for details
echo   2. Run book_translator_gui.pyw to use the app
echo.
goto end

:error
echo.
echo ========================================
echo   Test Failed!
echo ========================================
echo.
echo Please check the error message above.
echo.

:end
pause
