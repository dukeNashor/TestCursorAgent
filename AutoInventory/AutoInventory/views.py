"""
视图层
使用tkinter构建用户界面
"""
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
from typing import List, Optional, Dict, Any
import webbrowser
import os
from datetime import datetime

from models import Material, Order, OrderStatus, Priority
from controllers import MaterialController, OrderController, ReportController

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
    
    def __init__(self, parent, material: Optional[Material] = None):
        self.parent = parent
        self.material = material
        self.result = None
        
    def show(self):
        """显示对话框"""
        dialog = tk.Toplevel(self.parent)
        dialog.title("编辑物料" if self.material else "添加物料")
        dialog.geometry("500x600")
        dialog.transient(self.parent)
        dialog.grab_set()
        
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
        
        # 按钮区域
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=8, column=0, columnspan=2, pady=20)
        
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
                supplier=self.supplier_var.get().strip()
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
        self.order_controller = OrderController(self.db_manager)
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
        
        # 物料表格
        columns = ("ID", "名称", "类别", "数量", "单位", "最低库存", "位置", "供应商")
        self.material_tree = ttk.Treeview(self.material_frame, columns=columns, show="headings", height=20)
        
        for col in columns:
            self.material_tree.heading(col, text=col)
            self.material_tree.column(col, width=120)
        
        # 滚动条
        material_scrollbar = ttk.Scrollbar(self.material_frame, orient=tk.VERTICAL, command=self.material_tree.yview)
        self.material_tree.configure(yscrollcommand=material_scrollbar.set)
        
        self.material_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        material_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
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
        dialog = MaterialDialog(self.root)
        material = dialog.show()
        if material:
            try:
                self.material_controller.create_material(material)
                messagebox.showinfo("成功", "物料添加成功")
                self.refresh_materials()
            except Exception as e:
                messagebox.showerror("错误", f"添加失败: {str(e)}")
    
    def edit_material(self):
        """编辑物料"""
        selection = self.material_tree.selection()
        if not selection:
            messagebox.showwarning("警告", "请选择要编辑的物料")
            return
        
        item = self.material_tree.item(selection[0])
        material_id = item['values'][0]
        
        # 获取物料信息，包含版本号
        material_data = self.material_controller.db.get_material_with_version(material_id)
        if not material_data:
            messagebox.showerror("错误", "物料不存在")
            return
        
        material = Material.from_dict(material_data)
        dialog = MaterialDialog(self.root, material)
        updated_material = dialog.show()
        
        if updated_material:
            # 显示处理中提示
            self.show_processing_dialog("正在更新物料...")
            
            try:
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
        selection = self.material_tree.selection()
        if not selection:
            messagebox.showwarning("警告", "请选择要删除的物料")
            return
        
        if messagebox.askyesno("确认", "确定要删除选中的物料吗？"):
            item = self.material_tree.item(selection[0])
            material_id = item['values'][0]
            try:
                self.material_controller.delete_material(material_id)
                messagebox.showinfo("成功", "物料删除成功")
                self.refresh_materials()
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
    
    def update_material_tree(self, materials):
        """更新物料树形控件"""
        # 清空现有数据
        for item in self.material_tree.get_children():
            self.material_tree.delete(item)
        
        # 添加新数据
        for material in materials:
            self.material_tree.insert("", tk.END, values=(
                material.id, material.name, material.category,
                material.quantity, material.unit, material.min_stock,
                material.location, material.supplier
            ))
    
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
