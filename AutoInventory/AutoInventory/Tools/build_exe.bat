@echo off
chcp 65001 >nul
echo ========================================
echo   ADC库存管理系统 - 打包工具
echo ========================================
echo.

cd /d "%~dp0"
python build_exe.py

echo.
pause

