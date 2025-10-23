@echo off
echo 启动生物实验室库存管理系统...
echo.
python main.py
if errorlevel 1 (
    echo.
    echo 错误：无法启动程序
    echo 请确保已安装Python 3.7或更高版本
    echo.
    pause
)
