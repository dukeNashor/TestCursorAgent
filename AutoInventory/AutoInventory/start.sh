#!/bin/bash
echo "启动生物实验室库存管理系统..."
echo
python3 main.py
if [ $? -ne 0 ]; then
    echo
    echo "错误：无法启动程序"
    echo "请确保已安装Python 3.7或更高版本"
    echo
    read -p "按回车键继续..."
fi
