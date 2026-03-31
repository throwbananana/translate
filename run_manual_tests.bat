@echo off
setlocal

echo ============================================
echo 手工测试入口
echo ============================================
echo.
echo 1. 启动检查
echo 2. 翻译烟雾测试
echo 3. 完整工作流
echo 4. 实际翻译样例文件
echo.

set /p CHOICE=请选择 [1-4]:

if "%CHOICE%"=="1" py scripts\manual_tests\manual_startup_check.py
if "%CHOICE%"=="2" py scripts\manual_tests\manual_translation_smoke.py
if "%CHOICE%"=="3" py scripts\manual_tests\manual_full_workflow.py
if "%CHOICE%"=="4" py scripts\manual_tests\manual_actual_translation.py

endlocal
