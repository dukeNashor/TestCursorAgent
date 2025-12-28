"""
使用 PyInstaller 将应用打包为单文件 exe
使用方法：python build_exe.py
"""
import os
import sys
import subprocess
import shutil


def main():
    # 获取脚本所在目录和项目根目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_dir = os.path.dirname(script_dir)
    
    print(f"项目目录: {project_dir}")
    
    # 切换到项目目录
    os.chdir(project_dir)
    
    # 检查 PyInstaller 是否已安装
    try:
        import PyInstaller
        print(f"PyInstaller 版本: {PyInstaller.__version__}")
    except ImportError:
        print("PyInstaller 未安装，正在安装...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
        print("PyInstaller 安装完成")
    
    # 主程序入口
    main_script = os.path.join(project_dir, "main.py")
    
    if not os.path.exists(main_script):
        print(f"错误: 找不到主程序 {main_script}")
        sys.exit(1)
    
    # 输出目录
    dist_dir = os.path.join(project_dir, "dist")
    build_dir = os.path.join(project_dir, "build")
    
    # 应用名称
    app_name = "ADC库存管理系统"
    
    # PyInstaller 参数
    pyinstaller_args = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",                    # 打包为单文件
        "--windowed",                   # 无控制台窗口 (GUI应用)
        "--noconfirm",                  # 覆盖已存在的输出
        f"--name={app_name}",           # 输出文件名
        f"--distpath={dist_dir}",       # 输出目录
        f"--workpath={build_dir}",      # 临时工作目录
        "--clean",                      # 清理临时文件
        # 添加模块
        "--hidden-import=PyQt5",
        "--hidden-import=PyQt5.QtWidgets",
        "--hidden-import=PyQt5.QtCore",
        "--hidden-import=PyQt5.QtGui",
        "--hidden-import=sqlite3",
        "--hidden-import=material",
        "--hidden-import=material.models",
        "--hidden-import=material.repository",
        "--hidden-import=material.controller",
        "--hidden-import=adc",
        "--hidden-import=adc.models",
        "--hidden-import=adc.repository",
        "--hidden-import=adc.controller",
        # 添加数据文件（如有需要）
        # f"--add-data={os.path.join(project_dir, 'config.json')};.",
        main_script
    ]
    
    print("\n开始打包...")
    print(f"命令: {' '.join(pyinstaller_args)}")
    print("-" * 50)
    
    try:
        result = subprocess.run(pyinstaller_args, check=True)
        print("-" * 50)
        print(f"\n✅ 打包成功!")
        print(f"输出文件: {os.path.join(dist_dir, app_name + '.exe')}")
        
        # 清理 build 目录和 .spec 文件
        if os.path.exists(build_dir):
            shutil.rmtree(build_dir)
            print("已清理 build 目录")
        
        spec_file = os.path.join(project_dir, f"{app_name}.spec")
        if os.path.exists(spec_file):
            os.remove(spec_file)
            print("已清理 .spec 文件")
            
    except subprocess.CalledProcessError as e:
        print(f"\n❌ 打包失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

