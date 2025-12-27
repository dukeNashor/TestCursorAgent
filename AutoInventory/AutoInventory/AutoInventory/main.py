"""
生物实验室库存管理系统
主程序入口
"""
import sys
import os

def main():
    """主函数"""
    try:
        # 检查是否有PyQt5，如果有则使用PyQt版本
        try:
            from PyQt5.QtWidgets import QApplication
            from views_pyqt import MainWindow
            
            app = QApplication(sys.argv)
            window = MainWindow()
            window.show()
            sys.exit(app.exec_())
        except ImportError:
            # 如果没有PyQt5，使用tkinter版本
            from views import MainWindow
            app = MainWindow()
            app.run()
    except Exception as e:
        print(f"程序启动失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
