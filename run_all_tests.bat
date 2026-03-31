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
py test_large_file.py
if errorlevel 1 goto error

echo.
echo ========================================
echo Step 2/3: Test core features
echo ========================================
py test_core_features.py
if errorlevel 1 goto error

echo.
echo ========================================
echo Step 3/3: Test translation ^(requires GEMINI_API_KEY^)
echo ========================================
if "%GEMINI_API_KEY%"=="" (
echo Missing GEMINI_API_KEY. Please set your own key before running translation tests.
goto error
)
py test_actual_translation.py
if errorlevel 1 goto error

echo.
echo ========================================
echo   All Tests Passed!
echo ========================================
echo.
echo Generated files:
echo   - Test data: test_1k.txt ~ test_500k.txt
echo   - Translation: manual_outputs\sample_book_翻译测试.txt
echo   - Translation: manual_outputs\test_50k_翻译测试.txt
echo.
echo Next steps:
echo   1. Check manual_outputs for translation outputs
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
