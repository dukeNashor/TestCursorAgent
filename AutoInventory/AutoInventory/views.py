"""
视图层
使用tkinter构建用户界面
"""
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
from typing import List, Optional, Dict, Any
import webbrowser
import os
import io
from datetime import datetime
from PIL import Image, ImageTk, ImageDraw, ImageFont

from models import Material, Order, OrderStatus, Priority
from controllers import MaterialController, OrderController, ReportController
from database import load_config

class EmojiPicker:
    """Emoji选择器"""
    
    def __init__(self, parent):
        self.parent = parent
        self.result = None
        
    def show(self):
        """显示emoji选择器"""
        dialog = tk.Toplevel(self.parent)
        dialog.title("选择Emoji")
        dialog.geometry("400x300")
        dialog.transient(self.parent)
        dialog.grab_set()
        
        # 常用emoji列表
        emojis = [
            "🧪", "🔬", "⚗️", "🧬", "🦠", "💊", "💉", "🧫", "🔍", "📊",
            "📈", "📉", "⚠️", "✅", "❌", "🔴", "🟡", "🟢", "🔵", "⚪",
            "📝", "📋", "📌", "🔗", "💡", "🔧", "⚙️", "🔩", "📦", "📋",
            "🏷️", "📅", "⏰", "📍", "🎯", "💯", "⭐", "🔥", "💎", "🌟"
        ]
        
        # 创建emoji按钮网格
        frame = ttk.Frame(dialog)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        row, col = 0, 0
        for emoji in emojis:
            btn = tk.Button(frame, text=emoji, font=("Arial", 16), width=3, height=1,
                           command=lambda e=emoji: self._select_emoji(dialog, e))
            btn.grid(row=row, column=col, padx=2, pady=2)
            col += 1
            if col >= 10:
                col = 0
                row += 1
        
        # 等待用户选择
        dialog.wait_window()
        return self.result
    
    def _select_emoji(self, dialog, emoji):
        """选择emoji"""
        self.result = emoji
        dialog.destroy()

class MaterialDialog:
    """物料编辑对话框"""
    
    def __init__(self, parent, material: Optional[Material] = None, material_controller=None):
        self.parent = parent
        self.material = material
        self.material_controller = material_controller
        self.result = None
        self.image_paths = []  # 存储图片路径
        
        # 如果有现有物料且有图片，初始化图片列表
        # 由于图片现在存储在数据库中，编辑时需要临时保存为文件路径以便在界面上显示
        if material and material.images:
            # 图片现在是二进制数据，我们需要为编辑对话框创建临时文件
            self.image_paths = []  # 编辑模式下先清空，用户需要重新添加图片
        
    def show(self):
        """显示对话框"""
        dialog = tk.Toplevel(self.parent)
        dialog.title("编辑物料" if self.material else "添加物料")
        dialog.geometry("600x700")
        dialog.transient(self.parent)
        dialog.grab_set()
        
        # 图片列表已经在__init__中初始化
        
        # 创建表单
        main_frame = ttk.Frame(dialog)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # 物料名称
        ttk.Label(main_frame, text="物料名称 *:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.name_var = tk.StringVar(value=self.material.name if self.material else "")
        ttk.Entry(main_frame, textvariable=self.name_var, width=40).grid(row=0, column=1, pady=5, sticky=tk.W)
        
        # 类别
        ttk.Label(main_frame, text="类别 *:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.category_var = tk.StringVar(value=self.material.category if self.material else "")
        category_combo = ttk.Combobox(main_frame, textvariable=self.category_var, width=37)
        category_combo['values'] = ("试剂", "耗材", "设备", "工具", "其他")
        category_combo.grid(row=1, column=1, pady=5, sticky=tk.W)
        
        # 数量
        ttk.Label(main_frame, text="数量 *:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.quantity_var = tk.StringVar(value=str(self.material.quantity) if self.material else "0")
        ttk.Entry(main_frame, textvariable=self.quantity_var, width=40).grid(row=2, column=1, pady=5, sticky=tk.W)
        
        # 单位
        ttk.Label(main_frame, text="单位 *:").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.unit_var = tk.StringVar(value=self.material.unit if self.material else "")
        unit_combo = ttk.Combobox(main_frame, textvariable=self.unit_var, width=37)
        unit_combo['values'] = ("个", "瓶", "盒", "包", "升", "毫升", "克", "千克", "米", "厘米")
        unit_combo.grid(row=3, column=1, pady=5, sticky=tk.W)
        
        # 最低库存
        ttk.Label(main_frame, text="最低库存:").grid(row=4, column=0, sticky=tk.W, pady=5)
        self.min_stock_var = tk.StringVar(value=str(self.material.min_stock) if self.material else "0")
        ttk.Entry(main_frame, textvariable=self.min_stock_var, width=40).grid(row=4, column=1, pady=5, sticky=tk.W)
        
        # 存放位置
        ttk.Label(main_frame, text="存放位置:").grid(row=5, column=0, sticky=tk.W, pady=5)
        self.location_var = tk.StringVar(value=self.material.location if self.material else "")
        ttk.Entry(main_frame, textvariable=self.location_var, width=40).grid(row=5, column=1, pady=5, sticky=tk.W)
        
        # 供应商
        ttk.Label(main_frame, text="供应商:").grid(row=6, column=0, sticky=tk.W, pady=5)
        self.supplier_var = tk.StringVar(value=self.material.supplier if self.material else "")
        ttk.Entry(main_frame, textvariable=self.supplier_var, width=40).grid(row=6, column=1, pady=5, sticky=tk.W)
        
        # 描述（富文本）
        ttk.Label(main_frame, text="描述:").grid(row=7, column=0, sticky=tk.NW, pady=5)
        
        # 描述输入区域
        desc_frame = ttk.Frame(main_frame)
        desc_frame.grid(row=7, column=1, pady=5, sticky=tk.W)
        
        self.desc_text = scrolledtext.ScrolledText(desc_frame, width=40, height=8, wrap=tk.WORD)
        self.desc_text.pack(side=tk.LEFT)
        
        # Emoji按钮
        emoji_btn = ttk.Button(desc_frame, text="😀", command=self._insert_emoji)
        emoji_btn.pack(side=tk.RIGHT, padx=(5, 0))
        
        # 设置描述内容
        if self.material and self.material.description:
            self.desc_text.insert(tk.END, self.material.description)
        
        # 图片管理区域
        ttk.Label(main_frame, text="图片:").grid(row=8, column=0, sticky=tk.NW, pady=5)
        
        images_frame = ttk.Frame(main_frame)
        images_frame.grid(row=8, column=1, pady=5, sticky=tk.W)
        
        # 图片列表
        self.images_listbox = tk.Listbox(images_frame, width=40, height=5)
        self.images_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # 更新图片列表显示
        self._update_images_listbox()
        
        # 图片操作按钮
        image_btn_frame = ttk.Frame(images_frame)
        image_btn_frame.pack(side=tk.RIGHT, padx=(5, 0))
        
        ttk.Button(image_btn_frame, text="添加", command=self._add_image).pack(pady=2)
        ttk.Button(image_btn_frame, text="删除", command=self._remove_image).pack(pady=2)
        ttk.Button(image_btn_frame, text="查看", command=self._view_image).pack(pady=2)
        
        # 按钮区域
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=9, column=0, columnspan=2, pady=20)
        
        ttk.Button(button_frame, text="保存", command=lambda: self._save(dialog)).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="取消", command=dialog.destroy).pack(side=tk.LEFT, padx=5)
        
        # 等待用户操作
        dialog.wait_window()
        return self.result
    
    def _insert_emoji(self):
        """插入emoji"""
        emoji_picker = EmojiPicker(self.parent)
        emoji = emoji_picker.show()
        if emoji:
            self.desc_text.insert(tk.INSERT, emoji)
    
    def _update_images_listbox(self):
        """更新图片列表显示"""
        self.images_listbox.delete(0, tk.END)
        for path in self.image_paths:
            filename = os.path.basename(path)
            self.images_listbox.insert(tk.END, filename)
    
    def _add_image(self):
        """添加图片"""
        filename = filedialog.askopenfilename(
            title="选择图片",
            filetypes=[
                ("图片文件", "*.jpg *.jpeg *.png *.gif *.bmp"),
                ("所有文件", "*.*")
            ]
        )
        if filename:
            self.image_paths.append(filename)
            self._update_images_listbox()
    
    def _remove_image(self):
        """删除选中的图片"""
        selection = self.images_listbox.curselection()
        if not selection:
            messagebox.showwarning("警告", "请选择要删除的图片")
            return
        
        if messagebox.askyesno("确认", "确定要删除选中的图片吗？"):
            index = selection[0]
            del self.image_paths[index]
            self._update_images_listbox()
    
    def _view_image(self):
        """查看选中的图片"""
        selection = self.images_listbox.curselection()
        if not selection:
            messagebox.showwarning("警告", "请选择要查看的图片")
            return
        
        index = selection[0]
        image_path = self.image_paths[index]
        
        # 创建图片查看窗口
        view_window = tk.Toplevel(self.parent)
        view_window.title("查看图片")
        view_window.geometry("800x600")
        
        try:
            from PIL import Image, ImageTk
            # 加载图片
            if os.path.exists(image_path):
                img = Image.open(image_path)
            else:
                messagebox.showerror("错误", "图片文件不存在")
                view_window.destroy()
                return
            # 缩放图片以适应窗口
            img.thumbnail((700, 500), Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(img)
            
            # 显示图片
            label = tk.Label(view_window, image=photo)
            label.image = photo  # 保持引用
            label.pack(padx=10, pady=10)
            
            # 显示图片路径
            path_label = tk.Label(view_window, text=image_path, wraplength=700)
            path_label.pack(pady=5)
            
        except Exception as e:
            messagebox.showerror("错误", f"无法显示图片: {str(e)}")
            view_window.destroy()
    
    def _save(self, dialog):
        """保存物料"""
        try:
            # 验证必填字段
            if not self.name_var.get().strip():
                messagebox.showerror("错误", "请输入物料名称")
                return
            
            if not self.category_var.get().strip():
                messagebox.showerror("错误", "请选择类别")
                return
            
            if not self.unit_var.get().strip():
                messagebox.showerror("错误", "请输入单位")
                return
            
            # 验证数量
            try:
                quantity = int(self.quantity_var.get())
                min_stock = int(self.min_stock_var.get())
            except ValueError:
                messagebox.showerror("错误", "数量和最低库存必须是数字")
                return
            
            # 读取图片文件为二进制数据
            image_data_list = []
            for image_path in self.image_paths:
                if os.path.exists(image_path):
                    with open(image_path, 'rb') as f:
                        image_bytes = f.read()
                    image_data_list.append(image_bytes)
            
            # 创建物料对象
            material = Material(
                id=self.material.id if self.material else None,
                name=self.name_var.get().strip(),
                category=self.category_var.get().strip(),
                description=self.desc_text.get(1.0, tk.END).strip(),
                quantity=quantity,
                unit=self.unit_var.get().strip(),
                min_stock=min_stock,
                location=self.location_var.get().strip(),
                supplier=self.supplier_var.get().strip(),
                images=image_data_list
            )
            
            self.result = material
            dialog.destroy()
            
        except Exception as e:
            messagebox.showerror("错误", f"保存失败: {str(e)}")

class OrderDialog:
    """订单编辑对话框"""
    
    def __init__(self, parent, order: Optional[Order] = None, material_controller: MaterialController = None):
        self.parent = parent
        self.order = order
        self.material_controller = material_controller
        self.result = None
        self.materials = []
        
    def show(self):
        """显示对话框"""
        dialog = tk.Toplevel(self.parent)
        dialog.title("编辑订单" if self.order else "创建订单")
        dialog.geometry("800x700")
        dialog.transient(self.parent)
        dialog.grab_set()
        
        # 创建主框架
        main_frame = ttk.Frame(dialog)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # 订单基本信息
        info_frame = ttk.LabelFrame(main_frame, text="订单信息")
        info_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 申请人
        ttk.Label(info_frame, text="申请人 *:").grid(row=0, column=0, sticky=tk.W, pady=5, padx=10)
        self.requester_var = tk.StringVar(value=self.order.requester if self.order else "")
        ttk.Entry(info_frame, textvariable=self.requester_var, width=30).grid(row=0, column=1, pady=5, padx=10)
        
        # 部门
        ttk.Label(info_frame, text="部门:").grid(row=0, column=2, sticky=tk.W, pady=5, padx=10)
        self.department_var = tk.StringVar(value=self.order.department if self.order else "")
        ttk.Entry(info_frame, textvariable=self.department_var, width=30).grid(row=0, column=3, pady=5, padx=10)
        
        # 优先级
        ttk.Label(info_frame, text="优先级:").grid(row=1, column=0, sticky=tk.W, pady=5, padx=10)
        self.priority_var = tk.StringVar(value=self.order.priority if self.order else Priority.NORMAL.value)
        priority_combo = ttk.Combobox(info_frame, textvariable=self.priority_var, width=27)
        priority_combo['values'] = [p.value for p in Priority]
        priority_combo.grid(row=1, column=1, pady=5, padx=10)
        
        # 状态
        ttk.Label(info_frame, text="状态:").grid(row=1, column=2, sticky=tk.W, pady=5, padx=10)
        self.status_var = tk.StringVar(value=self.order.status if self.order else OrderStatus.PENDING.value)
        status_combo = ttk.Combobox(info_frame, textvariable=self.status_var, width=27)
        status_combo['values'] = [s.value for s in OrderStatus]
        status_combo.grid(row=1, column=3, pady=5, padx=10)
        
        # 备注
        ttk.Label(info_frame, text="备注:").grid(row=2, column=0, sticky=tk.NW, pady=5, padx=10)
        self.notes_text = scrolledtext.ScrolledText(info_frame, width=70, height=3, wrap=tk.WORD)
        self.notes_text.grid(row=2, column=1, columnspan=3, pady=5, padx=10, sticky=tk.W)
        
        if self.order and self.order.notes:
            self.notes_text.insert(tk.END, self.order.notes)
        
        # 物料列表
        materials_frame = ttk.LabelFrame(main_frame, text="物料列表")
        materials_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # 物料表格
        columns = ("物料名称", "类别", "数量", "单位", "备注")
        self.materials_tree = ttk.Treeview(materials_frame, columns=columns, show="headings", height=8)
        
        for col in columns:
            self.materials_tree.heading(col, text=col)
            self.materials_tree.column(col, width=120)
        
        # 滚动条
        scrollbar = ttk.Scrollbar(materials_frame, orient=tk.VERTICAL, command=self.materials_tree.yview)
        self.materials_tree.configure(yscrollcommand=scrollbar.set)
        
        self.materials_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(10, 0), pady=10)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=10)
        
        # 物料操作按钮
        material_btn_frame = ttk.Frame(materials_frame)
        material_btn_frame.pack(side=tk.RIGHT, padx=10, pady=10)
        
        ttk.Button(material_btn_frame, text="添加物料", command=self._add_material).pack(pady=2)
        ttk.Button(material_btn_frame, text="编辑物料", command=self._edit_material).pack(pady=2)
        ttk.Button(material_btn_frame, text="删除物料", command=self._remove_material).pack(pady=2)
        
        # 加载现有物料
        if self.order and self.order.materials:
            for material_data in self.order.materials:
                self._add_material_to_tree(material_data)
        
        # 按钮区域
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(pady=10)
        
        ttk.Button(button_frame, text="保存", command=lambda: self._save(dialog)).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="取消", command=dialog.destroy).pack(side=tk.LEFT, padx=5)
        
        # 等待用户操作
        dialog.wait_window()
        return self.result
    
    def _add_material(self):
        """添加物料到订单"""
        if not self.material_controller:
            messagebox.showerror("错误", "物料控制器未初始化")
            return
        
        # 选择物料对话框
        materials = self.material_controller.get_all_materials()
        if not materials:
            messagebox.showwarning("警告", "没有可用的物料")
            return
        
        # 创建物料选择对话框
        select_dialog = tk.Toplevel(self.parent)
        select_dialog.title("选择物料")
        select_dialog.geometry("600x400")
        select_dialog.transient(self.parent)
        select_dialog.grab_set()
        
        # 物料列表
        frame = ttk.Frame(select_dialog)
        frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        ttk.Label(frame, text="选择物料:").pack(anchor=tk.W)
        
        # 物料表格
        columns = ("ID", "名称", "类别", "库存", "单位")
        tree = ttk.Treeview(frame, columns=columns, show="headings", height=10)
        
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=100)
        
        for material in materials:
            tree.insert("", tk.END, values=(
                material.id, material.name, material.category,
                material.quantity, material.unit
            ))
        
        tree.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # 数量输入
        quantity_frame = ttk.Frame(frame)
        quantity_frame.pack(fill=tk.X, pady=10)
        
        ttk.Label(quantity_frame, text="数量:").pack(side=tk.LEFT)
        quantity_var = tk.StringVar(value="1")
        ttk.Entry(quantity_frame, textvariable=quantity_var, width=10).pack(side=tk.LEFT, padx=5)
        
        # 备注输入
        ttk.Label(quantity_frame, text="备注:").pack(side=tk.LEFT, padx=(20, 0))
        notes_var = tk.StringVar()
        ttk.Entry(quantity_frame, textvariable=notes_var, width=30).pack(side=tk.LEFT, padx=5)
        
        # 按钮
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(pady=10)
        
        def add_selected():
            selection = tree.selection()
            if not selection:
                messagebox.showwarning("警告", "请选择物料")
                return
            
            try:
                quantity = int(quantity_var.get())
                if quantity <= 0:
                    messagebox.showerror("错误", "数量必须大于0")
                    return
            except ValueError:
                messagebox.showerror("错误", "请输入有效的数量")
                return
            
            item = tree.item(selection[0])
            material_id = item['values'][0]
            material_name = item['values'][1]
            category = item['values'][2]
            unit = item['values'][4]
            
            material_data = {
                'material_id': material_id,
                'material_name': material_name,
                'category': category,
                'quantity': quantity,
                'unit': unit,
                'notes': notes_var.get()
            }
            
            self._add_material_to_tree(material_data)
            select_dialog.destroy()
        
        ttk.Button(btn_frame, text="添加", command=add_selected).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="取消", command=select_dialog.destroy).pack(side=tk.LEFT, padx=5)
    
    def _add_material_to_tree(self, material_data):
        """添加物料到树形控件"""
        self.materials_tree.insert("", tk.END, values=(
            material_data['material_name'],
            material_data['category'],
            material_data['quantity'],
            material_data['unit'],
            material_data.get('notes', '')
        ))
        self.materials.append(material_data)
    
    def _edit_material(self):
        """编辑选中的物料"""
        selection = self.materials_tree.selection()
        if not selection:
            messagebox.showwarning("警告", "请选择要编辑的物料")
            return
        
        # 这里可以实现编辑功能
        messagebox.showinfo("提示", "编辑功能待实现")
    
    def _remove_material(self):
        """删除选中的物料"""
        selection = self.materials_tree.selection()
        if not selection:
            messagebox.showwarning("警告", "请选择要删除的物料")
            return
        
        if messagebox.askyesno("确认", "确定要删除选中的物料吗？"):
            item = self.materials_tree.item(selection[0])
            index = self.materials_tree.index(selection[0])
            self.materials_tree.delete(selection[0])
            del self.materials[index]
    
    def _save(self, dialog):
        """保存订单"""
        try:
            # 验证必填字段
            if not self.requester_var.get().strip():
                messagebox.showerror("错误", "请输入申请人")
                return
            
            if not self.materials:
                messagebox.showerror("错误", "请至少添加一个物料")
                return
            
            # 创建订单对象
            order = Order(
                id=self.order.id if self.order else None,
                order_number=self.order.order_number if self.order else "",
                requester=self.requester_var.get().strip(),
                department=self.department_var.get().strip(),
                status=self.status_var.get(),
                priority=self.priority_var.get(),
                notes=self.notes_text.get(1.0, tk.END).strip(),
                materials=self.materials
            )
            
            self.result = order
            dialog.destroy()
            
        except Exception as e:
            messagebox.showerror("错误", f"保存失败: {str(e)}")

class MainWindow:
    """主窗口"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("生物实验室库存管理系统")
        self.root.geometry("1200x800")
        
        # 初始化数据库和控制器
        from database import DatabaseManager
        self.db_manager = DatabaseManager()
        self.material_controller = MaterialController(self.db_manager)
        self.order_controller = OrderController(self.db_manager, self.material_controller)
        self.report_controller = ReportController(self.db_manager)
        
        self.setup_ui()
        self.refresh_data()
    
    def setup_ui(self):
        """设置用户界面"""
        # 创建菜单栏
        self.create_menu()
        
        # 创建主框架
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 创建标签页
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill=tk.BOTH, expand=True)
        
        # 物料管理标签页
        self.material_frame = ttk.Frame(notebook)
        notebook.add(self.material_frame, text="物料管理")
        self.setup_material_tab()
        
        # 订单管理标签页
        self.order_frame = ttk.Frame(notebook)
        notebook.add(self.order_frame, text="订单管理")
        self.setup_order_tab()
        
        # 报告生成标签页
        self.report_frame = ttk.Frame(notebook)
        notebook.add(self.report_frame, text="报告生成")
        self.setup_report_tab()
        
        # 状态栏
        self.setup_status_bar()
    
    def create_menu(self):
        """创建菜单栏"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # 文件菜单
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="文件", menu=file_menu)
        file_menu.add_command(label="退出", command=self.root.quit)
        
        # 帮助菜单
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="帮助", menu=help_menu)
        help_menu.add_command(label="关于", command=self.show_about)
    
    def setup_material_tab(self):
        """设置物料管理标签页"""
        # 工具栏
        toolbar = ttk.Frame(self.material_frame)
        toolbar.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(toolbar, text="添加物料", command=self.add_material).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(toolbar, text="编辑物料", command=self.edit_material).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(toolbar, text="删除物料", command=self.delete_material).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(toolbar, text="刷新", command=self.refresh_materials).pack(side=tk.LEFT, padx=(0, 5))
        
        # 搜索框
        ttk.Label(toolbar, text="搜索:").pack(side=tk.LEFT, padx=(20, 5))
        self.material_search_var = tk.StringVar()
        search_entry = ttk.Entry(toolbar, textvariable=self.material_search_var, width=20)
        search_entry.pack(side=tk.LEFT, padx=(0, 5))
        search_entry.bind('<KeyRelease>', self.search_materials)
        
        # 创建水平分割框架
        paned_window = ttk.PanedWindow(self.material_frame, orient=tk.HORIZONTAL)
        paned_window.pack(fill=tk.BOTH, expand=True)
        
        # 左侧物料列表区域
        list_frame = ttk.Frame(paned_window)
        paned_window.add(list_frame, weight=2)
        
        # 物料显示区域 - 使用Canvas实现卡片式布局
        canvas_frame = ttk.Frame(list_frame)
        canvas_frame.pack(fill=tk.BOTH, expand=True)
        
        # 创建Canvas和滚动条
        self.material_canvas = tk.Canvas(canvas_frame, bg="#f5f5f5")
        material_scrollbar = ttk.Scrollbar(canvas_frame, orient=tk.VERTICAL, command=self.material_canvas.yview)
        self.material_scrollable_frame = ttk.Frame(self.material_canvas)
        
        self.material_scrollable_frame.bind(
            "<Configure>",
            lambda e: self.material_canvas.configure(scrollregion=self.material_canvas.bbox("all"))
        )
        
        self.material_canvas.create_window((0, 0), window=self.material_scrollable_frame, anchor="nw")
        self.material_canvas.configure(yscrollcommand=material_scrollbar.set)
        
        self.material_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        material_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 绑定鼠标滚轮
        self.material_canvas.bind_all("<MouseWheel>", self._on_material_canvas_scroll)
        
        # 存储物料卡片引用
        self.material_cards = []
        self.selected_material_id = None  # 当前选中的物料ID
        
        # 右侧详情面板
        detail_frame = ttk.Frame(paned_window)
        paned_window.add(detail_frame, weight=1)
        self.setup_material_detail_panel(detail_frame)
    
    def setup_material_detail_panel(self, parent):
        """设置物料详情面板"""
        # 标题
        title_label = tk.Label(parent, text="物料详情", font=("Microsoft YaHei", 14, "bold"), bg="white")
        title_label.pack(pady=10)
        
        # 详情内容框架
        self.detail_content = tk.Frame(parent, bg="white")
        self.detail_content.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 存储不同物料的详情面板
        self.detail_panels = {}  # material_id -> panel widget
        
        # 初始显示提示
        self.detail_placeholder = tk.Label(
            self.detail_content,
            text="请点击左侧物料卡片查看详情",
            font=("Arial", 12),
            bg="white",
            fg="#6c757d"
        )
        self.detail_placeholder.pack(expand=True)
    
    def setup_order_tab(self):
        """设置订单管理标签页"""
        # 工具栏
        toolbar = ttk.Frame(self.order_frame)
        toolbar.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(toolbar, text="创建订单", command=self.create_order).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(toolbar, text="编辑订单", command=self.edit_order).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(toolbar, text="完成订单", command=self.complete_order).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(toolbar, text="取消订单", command=self.cancel_order).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(toolbar, text="刷新", command=self.refresh_orders).pack(side=tk.LEFT, padx=(0, 5))
        
        # 状态筛选
        ttk.Label(toolbar, text="状态:").pack(side=tk.LEFT, padx=(20, 5))
        self.order_status_var = tk.StringVar(value="all")
        status_combo = ttk.Combobox(toolbar, textvariable=self.order_status_var, width=15)
        status_combo['values'] = ("all", "pending", "in_progress", "completed", "cancelled")
        status_combo.pack(side=tk.LEFT, padx=(0, 5))
        status_combo.bind('<<ComboboxSelected>>', self.filter_orders)
        
        # 订单表格
        columns = ("ID", "订单号", "申请人", "部门", "状态", "优先级", "创建时间")
        self.order_tree = ttk.Treeview(self.order_frame, columns=columns, show="headings", height=20)
        
        for col in columns:
            self.order_tree.heading(col, text=col)
            self.order_tree.column(col, width=120)
        
        # 滚动条
        order_scrollbar = ttk.Scrollbar(self.order_frame, orient=tk.VERTICAL, command=self.order_tree.yview)
        self.order_tree.configure(yscrollcommand=order_scrollbar.set)
        
        self.order_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        order_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    def setup_report_tab(self):
        """设置报告生成标签页"""
        # 说明文本
        info_frame = ttk.LabelFrame(self.report_frame, text="报告生成说明")
        info_frame.pack(fill=tk.X, pady=(0, 10))
        
        info_text = """
选择要生成报告的订单，系统将自动生成包含订单详细信息的HTML报告。
报告包含订单基本信息、物料清单等内容，适合打印或分享。
        """
        ttk.Label(info_frame, text=info_text, justify=tk.LEFT).pack(padx=10, pady=10)
        
        # 订单选择
        selection_frame = ttk.LabelFrame(self.report_frame, text="选择订单")
        selection_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # 订单列表
        columns = ("ID", "订单号", "申请人", "部门", "状态", "优先级", "创建时间")
        self.report_order_tree = ttk.Treeview(selection_frame, columns=columns, show="headings", height=15)
        
        for col in columns:
            self.report_order_tree.heading(col, text=col)
            self.report_order_tree.column(col, width=120)
        
        # 多选
        self.report_order_tree.configure(selectmode=tk.EXTENDED)
        
        # 滚动条
        report_scrollbar = ttk.Scrollbar(selection_frame, orient=tk.VERTICAL, command=self.report_order_tree.yview)
        self.report_order_tree.configure(yscrollcommand=report_scrollbar.set)
        
        self.report_order_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(10, 0), pady=10)
        report_scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=10)
        
        # 按钮
        button_frame = ttk.Frame(self.report_frame)
        button_frame.pack(pady=10)
        
        ttk.Button(button_frame, text="生成报告", command=self.generate_report).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="刷新订单列表", command=self.refresh_report_orders).pack(side=tk.LEFT, padx=5)
    
    def setup_status_bar(self):
        """设置状态栏"""
        self.status_frame = ttk.Frame(self.root)
        self.status_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=5, pady=2)
        
        # 状态信息
        self.status_var = tk.StringVar()
        self.status_var.set("就绪 - 支持多用户并发访问")
        status_label = ttk.Label(self.status_frame, textvariable=self.status_var, relief=tk.SUNKEN)
        status_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # 配置文件路径显示
        config = load_config()
        config_path = os.path.join(os.path.dirname(__file__), "config.json")
        config_display = f"📄 配置: {os.path.basename(config_path)} | "
        if config.get("database_path"):
            config_display += f"数据库: {config['database_path']}"
        else:
            config_display += "数据库: inventory.db"
        
        self.config_label = ttk.Label(self.status_frame, text=config_display, relief=tk.SUNKEN, font=("Arial", 8))
        self.config_label.pack(side=tk.RIGHT, padx=(5, 0))
        
        # 连接状态指示器
        self.connection_status = ttk.Label(self.status_frame, text="🟢 数据库连接正常", relief=tk.SUNKEN)
        self.connection_status.pack(side=tk.RIGHT, padx=(5, 0))
        
        # 定期检查数据库连接状态
        self.check_connection_status()
    
    def check_connection_status(self):
        """检查数据库连接状态"""
        try:
            # 尝试执行一个简单的查询
            self.material_controller.get_all_materials()
            self.connection_status.config(text="🟢 数据库连接正常")
        except Exception as e:
            self.connection_status.config(text="🔴 数据库连接异常")
        
        # 每5秒检查一次
        self.root.after(5000, self.check_connection_status)
    
    def update_status(self, message: str):
        """更新状态栏信息"""
        self.status_var.set(message)
        # 3秒后恢复默认状态
        self.root.after(3000, lambda: self.status_var.set("就绪 - 支持多用户并发访问"))
    
    def add_material(self):
        """添加物料"""
        dialog = MaterialDialog(self.root, material_controller=self.material_controller)
        material = dialog.show()
        if material:
            try:
                # 读取图片文件为二进制数据
                if material.images:
                    image_data_list = []
                    for image_path in material.images:
                        if os.path.exists(image_path):
                            with open(image_path, 'rb') as f:
                                image_bytes = f.read()
                            image_data_list.append(image_bytes)
                    material.images = image_data_list
                
                material_id = self.material_controller.create_material(material)
                messagebox.showinfo("成功", "物料添加成功")
                self.refresh_materials()
            except Exception as e:
                messagebox.showerror("错误", f"添加失败: {str(e)}")
    
    def edit_material(self):
        """编辑物料"""
        messagebox.showinfo("提示", "请双击物料卡片进行编辑")
    
    def _edit_material_by_id(self, material_id: int):
        """根据ID编辑物料"""
        # 获取物料信息，包含版本号
        material_data = self.material_controller.db.get_material_with_version(material_id)
        if not material_data:
            messagebox.showerror("错误", "物料不存在")
            return
        
        material = Material.from_dict(material_data)
        # 加载图片列表（从数据库获取二进制数据）
        images = self.material_controller.db.get_material_images(material_id)
        material.images = [img['image_data'] for img in images]  # 使用 image_data 而不是 image_path
        
        dialog = MaterialDialog(self.root, material, self.material_controller)
        updated_material = dialog.show()
        
        if updated_material:
            # 显示处理中提示
            self.show_processing_dialog("正在更新物料...")
            
            try:
                # 读取新添加的图片文件为二进制数据
                if updated_material.images:
                    image_data_list = []
                    for image_data in updated_material.images:
                        if isinstance(image_data, str):
                            # 文件路径，读取文件
                            if os.path.exists(image_data):
                                with open(image_data, 'rb') as f:
                                    image_bytes = f.read()
                                image_data_list.append(image_bytes)
                        else:
                            # 已经是二进制数据，直接使用
                            image_data_list.append(image_data)
                    updated_material.images = image_data_list
                
                success, message = self.material_controller.update_material(
                    updated_material, material_data['version']
                )
                self.hide_processing_dialog()
                
                if success:
                    messagebox.showinfo("成功", message)
                    self.update_status("物料更新成功")
                    self.refresh_materials()
                else:
                    # 如果是并发冲突，提供刷新选项
                    if "已被其他用户修改" in message:
                        self.update_status("检测到数据冲突")
                        if messagebox.askyesno("数据冲突", f"{message}\n\n是否刷新数据后重试？"):
                            self.refresh_materials()
                            self.edit_material()  # 递归重试
                    else:
                        messagebox.showerror("错误", message)
            except Exception as e:
                self.hide_processing_dialog()
                messagebox.showerror("错误", f"更新失败: {str(e)}")
    
    def delete_material(self):
        """删除物料"""
        if not self.selected_material_id:
            messagebox.showwarning("警告", "请先选择一个物料")
            return
        
        if messagebox.askyesno("确认", "确定要删除选中的物料吗？"):
            try:
                self.material_controller.delete_material(self.selected_material_id)
                messagebox.showinfo("成功", "物料删除成功")
                self.selected_material_id = None
                self.refresh_materials()
                # 清空详情面板
                for widget in self.detail_content.winfo_children():
                    widget.destroy()
                self.detail_placeholder = tk.Label(
                    self.detail_content,
                    text="请点击左侧物料卡片查看详情",
                    font=("Arial", 12),
                    bg="white",
                    fg="#6c757d"
                )
                self.detail_placeholder.pack(expand=True)
            except Exception as e:
                messagebox.showerror("错误", f"删除失败: {str(e)}")
    
    def _delete_material_by_id(self, material_id: int):
        """根据ID删除物料"""
        if messagebox.askyesno("确认", "确定要删除这个物料吗？"):
            try:
                self.material_controller.delete_material(material_id)
                messagebox.showinfo("成功", "物料删除成功")
                self.selected_material_id = None
                self.refresh_materials()
                # 清空详情面板
                for widget in self.detail_content.winfo_children():
                    widget.destroy()
                self.detail_placeholder = tk.Label(
                    self.detail_content,
                    text="请点击左侧物料卡片查看详情",
                    font=("Arial", 12),
                    bg="white",
                    fg="#6c757d"
                )
                self.detail_placeholder.pack(expand=True)
            except Exception as e:
                messagebox.showerror("错误", f"删除失败: {str(e)}")
    
    def create_order(self):
        """创建订单"""
        dialog = OrderDialog(self.root, material_controller=self.material_controller)
        order = dialog.show()
        if order:
            try:
                self.order_controller.create_order(order)
                messagebox.showinfo("成功", "订单创建成功")
                self.refresh_orders()
            except Exception as e:
                messagebox.showerror("错误", f"创建失败: {str(e)}")
    
    def edit_order(self):
        """编辑订单"""
        selection = self.order_tree.selection()
        if not selection:
            messagebox.showwarning("警告", "请选择要编辑的订单")
            return
        
        item = self.order_tree.item(selection[0])
        order_id = item['values'][0]
        order = self.order_controller.get_order(order_id)
        
        if order:
            dialog = OrderDialog(self.root, order, self.material_controller)
            updated_order = dialog.show()
            if updated_order:
                try:
                    self.order_controller.update_order(updated_order)
                    messagebox.showinfo("成功", "订单更新成功")
                    self.refresh_orders()
                except Exception as e:
                    messagebox.showerror("错误", f"更新失败: {str(e)}")
    
    def complete_order(self):
        """完成订单"""
        selection = self.order_tree.selection()
        if not selection:
            messagebox.showwarning("警告", "请选择要完成的订单")
            return
        
        item = self.order_tree.item(selection[0])
        order_id = item['values'][0]
        order_number = item['values'][1]
        
        # 显示详细确认对话框
        if messagebox.askyesno("确认完成订单", 
                              f"确定要完成订单 {order_number} 吗？\n\n"
                              f"此操作将：\n"
                              f"• 更新订单状态为已完成\n"
                              f"• 减少相关物料的库存\n"
                              f"• 记录库存变动历史\n\n"
                              f"此操作不可撤销！"):
            
            # 显示处理中提示
            self.show_processing_dialog("正在完成订单...")
            
            try:
                success, message = self.order_controller.complete_order(order_id)
                self.hide_processing_dialog()
                
                if success:
                    messagebox.showinfo("成功", message)
                    self.update_status("订单完成成功，库存已更新")
                    self.refresh_orders()
                    self.refresh_materials()  # 同时刷新物料列表
                else:
                    # 如果是库存不足，提供详细错误信息
                    if "库存不足" in message:
                        self.update_status("订单完成失败：库存不足")
                        messagebox.showerror("库存不足", message + "\n\n请检查库存后重试。")
                    else:
                        self.update_status("订单完成失败")
                        messagebox.showerror("完成失败", message)
            except Exception as e:
                self.hide_processing_dialog()
                messagebox.showerror("错误", f"完成失败: {str(e)}")
    
    def cancel_order(self):
        """取消订单"""
        selection = self.order_tree.selection()
        if not selection:
            messagebox.showwarning("警告", "请选择要取消的订单")
            return
        
        if messagebox.askyesno("确认", "确定要取消选中的订单吗？"):
            item = self.order_tree.item(selection[0])
            order_id = item['values'][0]
            try:
                self.order_controller.cancel_order(order_id)
                messagebox.showinfo("成功", "订单已取消")
                self.refresh_orders()
            except Exception as e:
                messagebox.showerror("错误", f"取消失败: {str(e)}")
    
    def generate_report(self):
        """生成报告"""
        selection = self.report_order_tree.selection()
        if not selection:
            messagebox.showwarning("警告", "请选择要生成报告的订单")
            return
        
        order_ids = []
        for item in selection:
            order_id = self.report_order_tree.item(item)['values'][0]
            order_ids.append(order_id)
        
        try:
            html_content = self.report_controller.generate_order_report(order_ids)
            
            # 保存文件
            filename = filedialog.asksaveasfilename(
                defaultextension=".html",
                filetypes=[("HTML文件", "*.html"), ("所有文件", "*.*")],
                title="保存报告"
            )
            
            if filename:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(html_content)
                
                messagebox.showinfo("成功", f"报告已保存到: {filename}")
                
                # 询问是否打开文件
                if messagebox.askyesno("打开文件", "是否要打开生成的报告？"):
                    webbrowser.open(filename)
        
        except Exception as e:
            messagebox.showerror("错误", f"生成报告失败: {str(e)}")
    
    def search_materials(self, event=None):
        """搜索物料"""
        keyword = self.material_search_var.get()
        if keyword:
            materials = self.material_controller.search_materials(keyword)
        else:
            materials = self.material_controller.get_all_materials()
        
        self.update_material_tree(materials)
    
    def filter_orders(self, event=None):
        """筛选订单"""
        status = self.order_status_var.get()
        if status == "all":
            orders = self.order_controller.get_all_orders()
        else:
            orders = self.order_controller.get_orders_by_status(status)
        
        self.update_order_tree(orders)
    
    def refresh_data(self):
        """刷新所有数据"""
        self.refresh_materials()
        self.refresh_orders()
        self.refresh_report_orders()
    
    def refresh_materials(self):
        """刷新物料列表"""
        materials = self.material_controller.get_all_materials()
        self.update_material_tree(materials)
    
    def refresh_orders(self):
        """刷新订单列表"""
        orders = self.order_controller.get_all_orders()
        self.update_order_tree(orders)
    
    def refresh_report_orders(self):
        """刷新报告页面的订单列表"""
        orders = self.order_controller.get_all_orders()
        self.update_report_order_tree(orders)
    
    def _on_material_canvas_scroll(self, event):
        """处理Canvas滚动"""
        self.material_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
    
    def update_material_tree(self, materials):
        """更新物料树形控件 - 使用卡片式布局"""
        # 清空现有卡片
        for card in self.material_cards:
            card.destroy()
        self.material_cards = []
        
        # 清空详情面板缓存
        self.detail_panels.clear()
        
        # 重置选中状态
        self.selected_material_id = None
        
        # 显示placeholder
        if hasattr(self, 'detail_placeholder'):
            self.detail_placeholder.pack(expand=True)
        
        # 为每个物料创建卡片
        for material in materials:
            card = self._create_material_card(material)
            self.material_cards.append(card)
    
    def _create_material_card(self, material: Material) -> tk.Frame:
        """创建物料卡片"""
        # 主卡片框架
        card = tk.Frame(self.material_scrollable_frame, bg="white", relief=tk.RAISED, bd=2)
        card.pack(fill=tk.X, padx=10, pady=8)
        
        # 左侧图片区域
        image_frame = tk.Frame(card, bg="white", width=150)
        image_frame.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=10)
        
        # 加载并显示图片（从二进制数据）
        if material.images and len(material.images) > 0:
            try:
                # 获取第一张图片的二进制数据
                img_bytes = material.images[0]
                if isinstance(img_bytes, bytes):
                    # 将二进制数据转换为PIL Image
                    img = Image.open(io.BytesIO(img_bytes))
                    img.thumbnail((120, 120), Image.Resampling.LANCZOS)
                    photo = ImageTk.PhotoImage(img)
                    
                    img_label = tk.Label(image_frame, image=photo, bg="white")
                    img_label.image = photo  # 保持引用
                    img_label.pack(pady=5)
                    
                    # 如果有多张图片，显示数量标签
                    if len(material.images) > 1:
                        count_label = tk.Label(
                            image_frame, 
                            text=f"+{len(material.images)-1}", 
                            bg="#007bff", 
                            fg="white",
                            font=("Arial", 10, "bold")
                        )
                        count_label.pack(pady=2)
                else:
                    # 如果还是字符串路径（兼容旧数据）
                    if os.path.exists(img_bytes):
                        img = Image.open(img_bytes)
                        img.thumbnail((120, 120), Image.Resampling.LANCZOS)
                        photo = ImageTk.PhotoImage(img)
                        
                        img_label = tk.Label(image_frame, image=photo, bg="white")
                        img_label.image = photo
                        img_label.pack(pady=5)
                    else:
                        raise Exception("图片数据格式错误")
            except Exception as e:
                # 图片加载失败，显示占位符
                placeholder = tk.Label(
                    image_frame, 
                    text="📷\n加载失败", 
                    bg="#e9ecef", 
                    fg="#6c757d",
                    font=("Arial", 12),
                    width=15,
                    height=8
                )
                placeholder.pack(pady=5)
        else:
            # 没有图片，显示占位符
            placeholder = tk.Label(
                image_frame, 
                text="📷\n无图片", 
                bg="#e9ecef", 
                fg="#6c757d",
                font=("Arial", 14),
                width=15,
                height=8
            )
            placeholder.pack(pady=5)
        
        # 右侧信息区域
        info_frame = tk.Frame(card, bg="white")
        info_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 标题区域
        title_frame = tk.Frame(info_frame, bg="white")
        title_frame.pack(fill=tk.X, pady=(0, 5))
        
        # 物料名称（大号粗体）
        name_label = tk.Label(
            title_frame, 
            text=material.name, 
            font=("Microsoft YaHei", 16, "bold"),
            bg="white",
            fg="#212529"
        )
        name_label.pack(side=tk.LEFT)
        
        # ID标签
        id_label = tk.Label(
            title_frame,
            text=f"ID: {material.id}",
            font=("Arial", 9),
            bg="#e9ecef",
            fg="#6c757d",
            padx=8,
            pady=2
        )
        id_label.pack(side=tk.RIGHT)
        
        # 类别标签
        category_colors = {
            "试剂": "#28a745",
            "耗材": "#17a2b8",
            "设备": "#ffc107",
            "工具": "#fd7e14",
            "其他": "#6c757d"
        }
        category_color = category_colors.get(material.category, "#6c757d")
        category_label = tk.Label(
            info_frame,
            text=material.category,
            font=("Arial", 10, "bold"),
            bg=category_color,
            fg="white",
            padx=10,
            pady=3
        )
        category_label.pack(anchor=tk.W, pady=5)
        
        # 信息网格
        grid_frame = tk.Frame(info_frame, bg="white")
        grid_frame.pack(fill=tk.X, pady=5)
        
        # 数量信息
        quantity_frame = tk.Frame(grid_frame, bg="white")
        quantity_frame.grid(row=0, column=0, sticky=tk.W, padx=(0, 20), pady=2)
        
        tk.Label(quantity_frame, text="数量:", font=("Arial", 9), bg="white", fg="#6c757d").pack(side=tk.LEFT)
        quantity_value = tk.Label(
            quantity_frame, 
            text=f"{material.quantity} {material.unit}", 
            font=("Arial", 10, "bold"),
            bg="white",
            fg="#212529"
        )
        quantity_value.pack(side=tk.LEFT, padx=5)
        
        # 最低库存
        min_stock_frame = tk.Frame(grid_frame, bg="white")
        min_stock_frame.grid(row=0, column=1, sticky=tk.W, padx=(0, 20), pady=2)
        
        tk.Label(min_stock_frame, text="最低库存:", font=("Arial", 9), bg="white", fg="#6c757d").pack(side=tk.LEFT)
        min_stock_value = tk.Label(
            min_stock_frame,
            text=str(material.min_stock),
            font=("Arial", 10, "bold"),
            bg="white",
            fg="#dc3545" if material.quantity <= material.min_stock else "#212529"
        )
        min_stock_value.pack(side=tk.LEFT, padx=5)
        
        # 存放位置
        if material.location:
            location_frame = tk.Frame(grid_frame, bg="white")
            location_frame.grid(row=1, column=0, sticky=tk.W, padx=(0, 20), pady=2)
            
            tk.Label(location_frame, text="📍", font=("Arial", 10), bg="white").pack(side=tk.LEFT)
            tk.Label(location_frame, text=material.location, font=("Arial", 9), bg="white", fg="#6c757d").pack(side=tk.LEFT, padx=5)
        
        # 供应商
        if material.supplier:
            supplier_frame = tk.Frame(grid_frame, bg="white")
            supplier_frame.grid(row=1, column=1, sticky=tk.W, padx=(0, 20), pady=2)
            
            tk.Label(supplier_frame, text="🏢", font=("Arial", 10), bg="white").pack(side=tk.LEFT)
            tk.Label(supplier_frame, text=material.supplier, font=("Arial", 9), bg="white", fg="#6c757d").pack(side=tk.LEFT, padx=5)
        
        # 绑定点击事件用于选中和显示详情
        def on_card_click(event):
            self._select_material_card(material.id, card)
        
        def on_card_double_click(event):
            self._edit_material_by_id(material.id)
        
        card.bind("<Button-1>", on_card_click)
        card.bind("<Double-Button-1>", on_card_double_click)
        for widget in card.winfo_children():
            widget.bind("<Button-1>", on_card_click)
            widget.bind("<Double-Button-1>", on_card_double_click)
        
        return card
    
    def _select_material_card(self, material_id: int, card_widget):
        """选中物料卡片"""
        # 取消之前选中的卡片
        if self.selected_material_id:
            for card in self.material_cards:
                card.config(relief=tk.RAISED, bd=2, highlightbackground="white", highlightthickness=0)
        
        # 高亮当前选中的卡片（立即响应）
        card_widget.config(relief=tk.SOLID, bd=3, highlightbackground="#28a745", highlightthickness=2)
        self.selected_material_id = material_id
        
        # 直接显示详情（现在从缓存读取，速度很快）
        self._show_material_detail(material_id)
    
    def _show_material_detail(self, material_id: int):
        """显示物料详情"""
        # 隐藏placeholder
        if hasattr(self, 'detail_placeholder'):
            self.detail_placeholder.pack_forget()
        
        # 如果已经有缓存的面板，直接显示
        if material_id in self.detail_panels:
            # 隐藏所有面板
            for mid, panel in self.detail_panels.items():
                panel.pack_forget()
            # 显示当前面板
            self.detail_panels[material_id].pack(fill=tk.BOTH, expand=True)
            return
        
        # 从缓存获取物料信息（速度很快）
        material = self.material_controller.get_material(material_id)
        
        if not material:
            error_label = tk.Label(
                self.detail_content,
                text="物料不存在",
                font=("Arial", 12),
                bg="white",
                fg="#dc3545"
            )
            error_label.pack(expand=True)
            return
        
        # 创建新的详情面板并缓存
        panel = self._create_detail_panel(material)
        self.detail_panels[material_id] = panel
        panel.pack(fill=tk.BOTH, expand=True)
    
    def _create_detail_panel(self, material: Material) -> tk.Frame:
        """创建详情面板"""
        panel = tk.Frame(self.detail_content, bg="white")
        
        # 创建滚动区域
        canvas = tk.Canvas(panel, bg="white")
        scrollbar = ttk.Scrollbar(panel, orient=tk.VERTICAL, command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg="white")
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 物料名称
        name_label = tk.Label(
            scrollable_frame,
            text=material.name,
            font=("Microsoft YaHei", 18, "bold"),
            bg="white",
            fg="#212529"
        )
        name_label.pack(pady=10)
        
        # 类别
        category_colors = {
            "试剂": "#28a745",
            "耗材": "#17a2b8",
            "设备": "#ffc107",
            "工具": "#fd7e14",
            "其他": "#6c757d"
        }
        category_color = category_colors.get(material.category, "#6c757d")
        category_label = tk.Label(
            scrollable_frame,
            text=material.category,
            font=("Arial", 12, "bold"),
            bg=category_color,
            fg="white",
            padx=15,
            pady=5
        )
        category_label.pack(pady=5)
        
        # 分隔线
        separator = tk.Frame(scrollable_frame, height=2, bg="#dee2e6")
        separator.pack(fill=tk.X, pady=15)
        
        # 详细信息
        info_section = tk.LabelFrame(scrollable_frame, text="基本信息", font=("Arial", 10, "bold"), bg="white")
        info_section.pack(fill=tk.X, padx=10, pady=5)
        
        # ID
        tk.Label(info_section, text=f"ID: {material.id}", font=("Arial", 9), bg="white", fg="#6c757d").pack(anchor=tk.W, pady=3)
        
        # 数量
        tk.Label(info_section, text=f"数量: {material.quantity} {material.unit}", font=("Arial", 10, "bold"), bg="white").pack(anchor=tk.W, pady=3)
        
        # 最低库存
        min_stock_color = "#dc3545" if material.quantity <= material.min_stock else "#6c757d"
        tk.Label(info_section, text=f"最低库存: {material.min_stock}", font=("Arial", 10), bg="white", fg=min_stock_color).pack(anchor=tk.W, pady=3)
        
        # 存放位置
        if material.location:
            tk.Label(info_section, text=f"📍 位置: {material.location}", font=("Arial", 9), bg="white", fg="#6c757d").pack(anchor=tk.W, pady=3)
        
        # 供应商
        if material.supplier:
            tk.Label(info_section, text=f"🏢 供应商: {material.supplier}", font=("Arial", 9), bg="white", fg="#6c757d").pack(anchor=tk.W, pady=3)
        
        # 描述
        if material.description:
            desc_section = tk.LabelFrame(scrollable_frame, text="描述", font=("Arial", 10, "bold"), bg="white")
            desc_section.pack(fill=tk.X, padx=10, pady=5)
            
            desc_text = tk.Text(desc_section, height=6, wrap=tk.WORD, font=("Arial", 9), bg="#f8f9fa", fg="#212529")
            desc_text.insert(tk.END, material.description)
            desc_text.config(state=tk.DISABLED)
            desc_text.pack(fill=tk.X, padx=5, pady=5)
        
        # 图片（延迟加载以提高性能）
        if material.images and len(material.images) > 0:
            img_section = tk.LabelFrame(scrollable_frame, text="图片", font=("Arial", 10, "bold"), bg="white")
            img_section.pack(fill=tk.X, padx=10, pady=5)
            
            # 限制显示的图片数量
            max_images = 3
            for idx, img_bytes in enumerate(material.images[:max_images]):
                if isinstance(img_bytes, bytes):
                    try:
                        img = Image.open(io.BytesIO(img_bytes))
                        img.thumbnail((200, 200), Image.Resampling.LANCZOS)
                        photo = ImageTk.PhotoImage(img)
                        
                        img_label = tk.Label(img_section, image=photo, bg="white")
                        img_label.image = photo
                        img_label.pack(pady=5)
                    except Exception as e:
                        pass
            
            # 如果还有更多图片，显示提示
            if len(material.images) > max_images:
                tk.Label(img_section, text=f"...还有 {len(material.images) - max_images} 张图片", 
                        font=("Arial", 9), bg="white", fg="#6c757d").pack(pady=5)
        
        # 按钮区域
        button_frame = tk.Frame(scrollable_frame, bg="white")
        button_frame.pack(fill=tk.X, padx=10, pady=15)
        
        ttk.Button(button_frame, text="编辑物料", command=lambda: self._edit_material_by_id(material.id)).pack(fill=tk.X, pady=3)
        ttk.Button(button_frame, text="删除物料", command=lambda: self._delete_material_by_id(material.id)).pack(fill=tk.X, pady=3)
        
        return panel
    
    def update_order_tree(self, orders):
        """更新订单树形控件"""
        # 清空现有数据
        for item in self.order_tree.get_children():
            self.order_tree.delete(item)
        
        # 添加新数据
        for order in orders:
            created_at = order.created_at.strftime('%Y-%m-%d %H:%M') if order.created_at else 'N/A'
            self.order_tree.insert("", tk.END, values=(
                order.id, order.order_number, order.requester,
                order.department, order.status, order.priority, created_at
            ))
    
    def update_report_order_tree(self, orders):
        """更新报告页面的订单树形控件"""
        # 清空现有数据
        for item in self.report_order_tree.get_children():
            self.report_order_tree.delete(item)
        
        # 添加新数据
        for order in orders:
            created_at = order.created_at.strftime('%Y-%m-%d %H:%M') if order.created_at else 'N/A'
            self.report_order_tree.insert("", tk.END, values=(
                order.id, order.order_number, order.requester,
                order.department, order.status, order.priority, created_at
            ))
    
    def show_processing_dialog(self, message: str):
        """显示处理中对话框"""
        self.processing_dialog = tk.Toplevel(self.root)
        self.processing_dialog.title("处理中")
        self.processing_dialog.geometry("300x100")
        self.processing_dialog.transient(self.root)
        self.processing_dialog.grab_set()
        
        # 居中显示
        self.processing_dialog.geometry("+%d+%d" % (
            self.root.winfo_rootx() + 50,
            self.root.winfo_rooty() + 50
        ))
        
        # 禁用关闭按钮
        self.processing_dialog.protocol("WM_DELETE_WINDOW", lambda: None)
        
        frame = ttk.Frame(self.processing_dialog)
        frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        ttk.Label(frame, text=message, font=("Arial", 10)).pack(pady=10)
        
        # 进度条
        self.progress = ttk.Progressbar(frame, mode='indeterminate')
        self.progress.pack(fill=tk.X, pady=5)
        self.progress.start()
        
        # 强制更新界面
        self.processing_dialog.update()
    
    def hide_processing_dialog(self):
        """隐藏处理中对话框"""
        if hasattr(self, 'processing_dialog') and self.processing_dialog:
            self.progress.stop()
            self.processing_dialog.destroy()
            self.processing_dialog = None
    
    def show_about(self):
        """显示关于对话框"""
        messagebox.showinfo("关于", 
            "生物实验室库存管理系统 v1.1\n\n"
            "功能特点:\n"
            "• 物料管理（增删改查）\n"
            "• 订单管理（创建、修改、完成）\n"
            "• HTML报告生成\n"
            "• 富文本描述支持\n"
            "• 库存变动记录\n"
            "• 多用户并发支持\n"
            "• 乐观锁防冲突\n\n"
            "使用SQLite数据库存储数据\n"
            "支持多用户同时访问"
        )
    
    def run(self):
        """运行应用程序"""
        self.root.mainloop()
