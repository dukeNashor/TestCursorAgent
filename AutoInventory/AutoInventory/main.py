"""
生物实验室库存管理系统
主程序入口
"""
import sys
import os
from views import MainWindow

def main():
    """主函数"""
    try:
        # 创建并运行主窗口
        app = MainWindow()
        app.run()
    except Exception as e:
        print(f"程序启动失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
