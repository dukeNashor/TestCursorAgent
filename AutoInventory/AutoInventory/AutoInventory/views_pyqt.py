"""
视图层 - PyQt版本
使用PyQt构建用户界面，保持缓存机制确保流畅性能
"""
import sys
import os
import io
from typing import List, Optional, Dict, Any
from datetime import datetime

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QLineEdit, QTextEdit, QComboBox, QScrollArea,
    QListWidget, QListWidgetItem, QFrame, QSplitter, QMessageBox, QFileDialog,
    QDialog, QDialogButtonBox, QSpinBox, QGroupBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QTabWidget, QProgressBar
)
from PyQt5.QtCore import Qt, QSize, pyqtSignal, QThread, QTimer
from PyQt5.QtGui import QPixmap, QFont, QColor, QImage

from models import Material, Order, OrderStatus, Priority
from controllers import MaterialController, OrderController, ReportController
from database import load_config

class EmojiPicker(QDialog):
    """Emoji选择器"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("选择Emoji")
        self.setFixedSize(400, 300)
        self.result = None
        
        # 常用emoji列表
        emojis = [
            "🧪", "🔬", "⚗️", "🧬", "🦠", "💊", "💉", "🧫", "🔍", "📊",
            "📈", "📉", "⚠️", "✅", "❌", "🔴", "🟡", "🟢", "🔵", "⚪",
            "📝", "📋", "📌", "🔗", "💡", "🔧", "⚙️", "🔩", "📦", "📋",
            "🏷️", "📅", "⏰", "📍", "🎯", "💯", "⭐", "🔥", "💎", "🌟"
        ]
        
        layout = QGridLayout()
        self.setLayout(layout)
        
        row, col = 0, 0
        for emoji in emojis:
            btn = QPushButton(emoji)
            btn.setFixedSize(40, 40)
            btn.setFont(QFont("Arial", 16))
            btn.clicked.connect(lambda checked, e=emoji: self._select_emoji(e))
            layout.addWidget(btn, row, col)
            col += 1
            if col >= 10:
                col = 0
                row += 1
    
    def _select_emoji(self, emoji):
        self.result = emoji
        self.accept()

class MaterialDialog(QDialog):
    """物料编辑对话框"""
    
    def __init__(self, parent=None, material: Optional[Material] = None, material_controller=None):
        super().__init__(parent)
        self.material = material
        self.material_controller = material_controller
        self.result = None
        self.image_paths = []
        
        self.setWindowTitle("编辑物料" if material else "添加物料")
        self.setFixedSize(600, 700)
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        scroll_layout = QVBoxLayout()
        content.setLayout(scroll_layout)
        
        # 物料名称
        scroll_layout.addWidget(QLabel("物料名称 *:"))
        self.name_edit = QLineEdit(self.material.name if self.material else "")
        scroll_layout.addWidget(self.name_edit)
        
        # 类别
        scroll_layout.addWidget(QLabel("类别 *:"))
        self.category_combo = QComboBox()
        self.category_combo.addItems(["试剂", "耗材", "设备", "工具", "其他"])
        if self.material:
            self.category_combo.setCurrentText(self.material.category)
        scroll_layout.addWidget(self.category_combo)
        
        # 数量
        scroll_layout.addWidget(QLabel("数量 *:"))
        self.quantity_edit = QSpinBox()
        self.quantity_edit.setMaximum(999999)
        self.quantity_edit.setValue(self.material.quantity if self.material else 0)
        scroll_layout.addWidget(self.quantity_edit)
        
        # 单位
        scroll_layout.addWidget(QLabel("单位 *:"))
        self.unit_combo = QComboBox()
        self.unit_combo.addItems(["个", "瓶", "盒", "包", "升", "毫升", "克", "千克", "米", "厘米"])
        if self.material:
            self.unit_combo.setCurrentText(self.material.unit)
        scroll_layout.addWidget(self.unit_combo)
        
        # 最低库存
        scroll_layout.addWidget(QLabel("最低库存:"))
        self.min_stock_edit = QSpinBox()
        self.min_stock_edit.setMaximum(999999)
        self.min_stock_edit.setValue(self.material.min_stock if self.material else 0)
        scroll_layout.addWidget(self.min_stock_edit)
        
        # 存放位置
        scroll_layout.addWidget(QLabel("存放位置:"))
        self.location_edit = QLineEdit(self.material.location if self.material else "")
        scroll_layout.addWidget(self.location_edit)
        
        # 供应商
        scroll_layout.addWidget(QLabel("供应商:"))
        self.supplier_edit = QLineEdit(self.material.supplier if self.material else "")
        scroll_layout.addWidget(self.supplier_edit)
        
        # 描述
        scroll_layout.addWidget(QLabel("描述:"))
        desc_layout = QHBoxLayout()
        self.desc_text = QTextEdit()
        self.desc_text.setMaximumHeight(100)
        if self.material and self.material.description:
            self.desc_text.setPlainText(self.material.description)
        desc_layout.addWidget(self.desc_text)
        
        emoji_btn = QPushButton("😀")
        emoji_btn.clicked.connect(self._insert_emoji)
        desc_layout.addWidget(emoji_btn)
        scroll_layout.addLayout(desc_layout)
        
        # 图片管理
        scroll_layout.addWidget(QLabel("图片:"))
        img_layout = QHBoxLayout()
        self.image_list = QListWidget()
        self.image_list.setMaximumHeight(100)
        img_layout.addWidget(self.image_list)
        
        img_btn_layout = QVBoxLayout()
        add_btn = QPushButton("添加")
        add_btn.clicked.connect(self._add_image)
        remove_btn = QPushButton("删除")
        remove_btn.clicked.connect(self._remove_image)
        view_btn = QPushButton("查看")
        view_btn.clicked.connect(self._view_image)
        
        img_btn_layout.addWidget(add_btn)
        img_btn_layout.addWidget(remove_btn)
        img_btn_layout.addWidget(view_btn)
        img_layout.addLayout(img_btn_layout)
        scroll_layout.addLayout(img_layout)
        
        scroll.setWidget(content)
        layout.addWidget(scroll)
        
        # 按钮
        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._save)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
    
    def _insert_emoji(self):
        emoji_picker = EmojiPicker(self)
        if emoji_picker.exec_() == QDialog.Accepted:
            emoji = emoji_picker.result
            if emoji:
                self.desc_text.insertPlainText(emoji)
    
    def _add_image(self):
        filename, _ = QFileDialog.getOpenFileName(
            self, "选择图片", "", "图片文件 (*.jpg *.jpeg *.png *.gif *.bmp)"
        )
        if filename:
            self.image_paths.append(filename)
            self.image_list.addItem(os.path.basename(filename))
    
    def _remove_image(self):
        current_item = self.image_list.currentItem()
        if current_item:
            index = self.image_list.row(current_item)
            self.image_list.takeItem(index)
            del self.image_paths[index]
    
    def _view_image(self):
        current_item = self.image_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "警告", "请选择要查看的图片")
            return
        
        index = self.image_list.row(current_item)
        image_path = self.image_paths[index]
        
        dialog = QDialog(self)
        dialog.setWindowTitle("查看图片")
        dialog.setFixedSize(800, 600)
        layout = QVBoxLayout()
        
        pixmap = QPixmap(image_path)
        label = QLabel()
        label.setPixmap(pixmap.scaled(700, 500, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        label.setAlignment(Qt.AlignCenter)
        layout.addWidget(label)
        
        path_label = QLabel(image_path)
        path_label.setWordWrap(True)
        layout.addWidget(path_label)
        
        dialog.setLayout(layout)
        dialog.exec_()
    
    def _save(self):
        if not self.name_edit.text().strip():
            QMessageBox.critical(self, "错误", "请输入物料名称")
            return
        
        if not self.category_combo.currentText():
            QMessageBox.critical(self, "错误", "请选择类别")
            return
        
        if not self.unit_combo.currentText():
            QMessageBox.critical(self, "错误", "请输入单位")
            return
        
        # 读取图片文件为二进制数据
        image_data_list = []
        for image_path in self.image_paths:
            if os.path.exists(image_path):
                with open(image_path, 'rb') as f:
                    image_bytes = f.read()
                image_data_list.append(image_bytes)
        
        material = Material(
            id=self.material.id if self.material else None,
            name=self.name_edit.text().strip(),
            category=self.category_combo.currentText(),
            description=self.desc_text.toPlainText().strip(),
            quantity=self.quantity_edit.value(),
            unit=self.unit_combo.currentText(),
            min_stock=self.min_stock_edit.value(),
            location=self.location_edit.text().strip(),
            supplier=self.supplier_edit.text().strip(),
            images=image_data_list
        )
        
        self.result = material
        self.accept()

class OrderDialog(QDialog):
    """订单编辑对话框"""
    
    def __init__(self, parent=None, order: Optional[Order] = None, material_controller: MaterialController = None):
        super().__init__(parent)
        self.order = order
        self.material_controller = material_controller
        self.result = None
        self.materials = []
        
        self.setWindowTitle("编辑订单" if order else "创建订单")
        self.setFixedSize(800, 700)
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # 订单信息
        info_group = QGroupBox("订单信息")
        info_layout = QGridLayout()
        
        info_layout.addWidget(QLabel("申请人 *:"), 0, 0)
        self.requester_edit = QLineEdit(self.order.requester if self.order else "")
        info_layout.addWidget(self.requester_edit, 0, 1)
        
        info_layout.addWidget(QLabel("部门:"), 0, 2)
        self.department_edit = QLineEdit(self.order.department if self.order else "")
        info_layout.addWidget(self.department_edit, 0, 3)
        
        info_layout.addWidget(QLabel("优先级:"), 1, 0)
        self.priority_combo = QComboBox()
        self.priority_combo.addItems([p.value for p in Priority])
        if self.order:
            self.priority_combo.setCurrentText(self.order.priority)
        info_layout.addWidget(self.priority_combo, 1, 1)
        
        info_layout.addWidget(QLabel("状态:"), 1, 2)
        self.status_combo = QComboBox()
        self.status_combo.addItems([s.value for s in OrderStatus])
        if self.order:
            self.status_combo.setCurrentText(self.order.status)
        info_layout.addWidget(self.status_combo, 1, 3)
        
        info_layout.addWidget(QLabel("备注:"), 2, 0)
        self.notes_text = QTextEdit()
        self.notes_text.setMaximumHeight(80)
        if self.order and self.order.notes:
            self.notes_text.setPlainText(self.order.notes)
        info_layout.addWidget(self.notes_text, 2, 1, 1, 3)
        
        info_group.setLayout(info_layout)
        layout.addWidget(info_group)
        
        # 物料列表
        materials_group = QGroupBox("物料列表")
        materials_layout = QVBoxLayout()
        
        self.materials_table = QTableWidget()
        self.materials_table.setColumnCount(5)
        self.materials_table.setHorizontalHeaderLabels(["物料名称", "类别", "数量", "单位", "备注"])
        self.materials_table.horizontalHeader().setStretchLastSection(True)
        materials_layout.addWidget(self.materials_table)
        
        btn_layout = QHBoxLayout()
        add_btn = QPushButton("添加物料")
        add_btn.clicked.connect(self._add_material)
        edit_btn = QPushButton("编辑物料")
        edit_btn.clicked.connect(self._edit_material)
        remove_btn = QPushButton("删除物料")
        remove_btn.clicked.connect(self._remove_material)
        
        btn_layout.addWidget(add_btn)
        btn_layout.addWidget(edit_btn)
        btn_layout.addWidget(remove_btn)
        materials_layout.addLayout(btn_layout)
        
        materials_group.setLayout(materials_layout)
        layout.addWidget(materials_group)
        
        # 按钮
        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._save)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
    
    def _add_material(self):
        # 简化的物料添加逻辑
        pass
    
    def _edit_material(self):
        pass
    
    def _remove_material(self):
        pass
    
    def _save(self):
        if not self.requester_edit.text().strip():
            QMessageBox.critical(self, "错误", "请输入申请人")
            return
        
        order = Order(
            id=self.order.id if self.order else None,
            order_number=self.order.order_number if self.order else "",
            requester=self.requester_edit.text().strip(),
            department=self.department_edit.text().strip(),
            status=self.status_combo.currentText(),
            priority=self.priority_combo.currentText(),
            notes=self.notes_text.toPlainText().strip(),
            materials=self.materials
        )
        
        self.result = order
        self.accept()

class MaterialCard(QFrame):
    """物料卡片"""
    
    clicked = pyqtSignal(int)  # material_id
    
    def __init__(self, material: Material, parent=None):
        super().__init__(parent)
        self.material = material
        self.setFrameStyle(QFrame.Box)
        self.setLineWidth(2)
        self.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 5px;
            }
        """)
        self.setup_ui()
    
    def setup_ui(self):
        layout = QHBoxLayout()
        self.setLayout(layout)
        
        # 左侧图片
        img_label = QLabel()
        if self.material.images and len(self.material.images) > 0:
            try:
                img_bytes = self.material.images[0]
                if isinstance(img_bytes, bytes):
                    img = QImage.fromData(img_bytes)
                    pixmap = QPixmap.fromImage(img)
                    img_label.setPixmap(pixmap.scaled(120, 120, Qt.KeepAspectRatio, Qt.SmoothTransformation))
                img_label.setAlignment(Qt.AlignCenter)
            except:
                img_label.setText("📷\n无图片")
                img_label.setAlignment(Qt.AlignCenter)
        else:
            img_label.setText("📷\n无图片")
            img_label.setAlignment(Qt.AlignCenter)
        
        img_label.setFixedSize(150, 150)
        layout.addWidget(img_label)
        
        # 右侧信息
        info_layout = QVBoxLayout()
        
        # 标题
        title_layout = QHBoxLayout()
        name_label = QLabel(self.material.name)
        name_label.setFont(QFont("Microsoft YaHei", 16, QFont.Bold))
        title_layout.addWidget(name_label)
        
        id_label = QLabel(f"ID: {self.material.id}")
        id_label.setStyleSheet("background-color: #e9ecef; padding: 5px; border-radius: 3px;")
        title_layout.addWidget(id_label)
        info_layout.addLayout(title_layout)
        
        # 类别
        category_colors = {
            "试剂": "#28a745",
            "耗材": "#17a2b8",
            "设备": "#ffc107",
            "工具": "#fd7e14",
            "其他": "#6c757d"
        }
        category_color = category_colors.get(self.material.category, "#6c757d")
        category_label = QLabel(self.material.category)
        category_label.setStyleSheet(f"background-color: {category_color}; color: white; padding: 5px; border-radius: 3px;")
        category_label.setFixedWidth(80)
        info_layout.addWidget(category_label)
        
        # 信息
        info_text = f"数量: {self.material.quantity} {self.material.unit}"
        if self.material.quantity <= self.material.min_stock:
            info_text += f" ⚠️ 库存不足"
        info_label = QLabel(info_text)
        info_layout.addWidget(info_label)
        
        if self.material.location:
            location_label = QLabel(f"📍 {self.material.location}")
            info_layout.addWidget(location_label)
        
        if self.material.supplier:
            supplier_label = QLabel(f"🏢 {self.material.supplier}")
            info_layout.addWidget(supplier_label)
        
        layout.addLayout(info_layout)
        
        # 鼠标点击事件
        self.mousePressEvent = self._on_click
    
    def _on_click(self, event):
        self.clicked.emit(self.material.id)
    
    def set_selected(self, selected: bool):
        """设置选中状态"""
        if selected:
            self.setStyleSheet("""
                QFrame {
                    background-color: white;
                    border: 3px solid #28a745;
                    border-radius: 5px;
                }
            """)
        else:
            self.setStyleSheet("""
                QFrame {
                    background-color: white;
                    border-radius: 5px;
                }
            """)

class MaterialDetailPanel(QWidget):
    """物料详情面板"""
    
    edit_requested = pyqtSignal(int)  # material_id
    delete_requested = pyqtSignal(int)  # material_id
    
    def __init__(self, material: Material, parent=None):
        super().__init__(parent)
        self.material = material
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        scroll_layout = QVBoxLayout()
        content.setLayout(scroll_layout)
        
        # 物料名称
        name_label = QLabel(self.material.name)
        name_label.setFont(QFont("Microsoft YaHei", 18, QFont.Bold))
        name_label.setAlignment(Qt.AlignCenter)
        scroll_layout.addWidget(name_label)
        
        # 类别
        category_colors = {
            "试剂": "#28a745",
            "耗材": "#17a2b8",
            "设备": "#ffc107",
            "工具": "#fd7e14",
            "其他": "#6c757d"
        }
        category_color = category_colors.get(self.material.category, "#6c757d")
        category_label = QLabel(self.material.category)
        category_label.setStyleSheet(f"background-color: {category_color}; color: white; padding: 10px; border-radius: 5px;")
        category_label.setAlignment(Qt.AlignCenter)
        scroll_layout.addWidget(category_label)
        
        # 基本信息
        info_group = QGroupBox("基本信息")
        info_layout = QVBoxLayout()
        info_layout.addWidget(QLabel(f"ID: {self.material.id}"))
        info_layout.addWidget(QLabel(f"数量: {self.material.quantity} {self.material.unit}"))
        
        min_stock_text = f"最低库存: {self.material.min_stock}"
        if self.material.quantity <= self.material.min_stock:
            min_stock_label = QLabel(min_stock_text)
            min_stock_label.setStyleSheet("color: #dc3545;")
            info_layout.addWidget(min_stock_label)
        else:
            info_layout.addWidget(QLabel(min_stock_text))
        
        if self.material.location:
            info_layout.addWidget(QLabel(f"📍 位置: {self.material.location}"))
        if self.material.supplier:
            info_layout.addWidget(QLabel(f"🏢 供应商: {self.material.supplier}"))
        
        info_group.setLayout(info_layout)
        scroll_layout.addWidget(info_group)
        
        # 描述
        if self.material.description:
            desc_group = QGroupBox("描述")
            desc_layout = QVBoxLayout()
            desc_text = QTextEdit()
            desc_text.setPlainText(self.material.description)
            desc_text.setReadOnly(True)
            desc_text.setMaximumHeight(100)
            desc_layout.addWidget(desc_text)
            desc_group.setLayout(desc_layout)
            scroll_layout.addWidget(desc_group)
        
        # 图片
        if self.material.images and len(self.material.images) > 0:
            img_group = QGroupBox("图片")
            img_layout = QVBoxLayout()
            
            max_images = 3
            for idx, img_bytes in enumerate(self.material.images[:max_images]):
                if isinstance(img_bytes, bytes):
                    try:
                        img = QImage.fromData(img_bytes)
                        pixmap = QPixmap.fromImage(img)
                        label = QLabel()
                        label.setPixmap(pixmap.scaled(200, 200, Qt.KeepAspectRatio, Qt.SmoothTransformation))
                        label.setAlignment(Qt.AlignCenter)
                        img_layout.addWidget(label)
                    except:
                        pass
            
            if len(self.material.images) > max_images:
                img_layout.addWidget(QLabel(f"...还有 {len(self.material.images) - max_images} 张图片"))
            
            img_group.setLayout(img_layout)
            scroll_layout.addWidget(img_group)
        
        scroll_layout.addStretch()
        
        scroll.setWidget(content)
        layout.addWidget(scroll)
        
        # 按钮
        btn_layout = QVBoxLayout()
        edit_btn = QPushButton("编辑物料")
        edit_btn.clicked.connect(lambda: self.edit_requested.emit(self.material.id))
        delete_btn = QPushButton("删除物料")
        delete_btn.clicked.connect(lambda: self.delete_requested.emit(self.material.id))
        
        btn_layout.addWidget(edit_btn)
        btn_layout.addWidget(delete_btn)
        layout.addLayout(btn_layout)

class MainWindow(QMainWindow):
    """主窗口"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("生物实验室库存管理系统")
        self.setGeometry(100, 100, 1400, 900)
        
        # 初始化数据库和控制器
        from database import DatabaseManager
        self.db_manager = DatabaseManager()
        self.material_controller = MaterialController(self.db_manager)
        self.order_controller = OrderController(self.db_manager, self.material_controller)
        self.report_controller = ReportController(self.db_manager)
        
        # 存储卡片和详情面板
        self.material_cards = {}
        self.detail_panels = {}
        self.selected_material_id = None
        
        self.setup_ui()
        self.refresh_data()
    
    def setup_ui(self):
        """设置用户界面"""
        # 创建中心部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)
        
        # 创建标签页
        tabs = QTabWidget()
        main_layout.addWidget(tabs)
        
        # 物料管理标签页
        material_tab = QWidget()
        self.setup_material_tab(material_tab)
        tabs.addTab(material_tab, "物料管理")
        
        # 订单管理标签页
        order_tab = QWidget()
        self.setup_order_tab(order_tab)
        tabs.addTab(order_tab, "订单管理")
        
        # 报告生成标签页
        report_tab = QWidget()
        self.setup_report_tab(report_tab)
        tabs.addTab(report_tab, "报告生成")
        
        # 状态栏
        self.statusBar().showMessage("就绪 - 支持多用户并发访问")
        
        # 配置信息
        config = load_config()
        config_path = os.path.join(os.path.dirname(__file__), "config.json")
        config_display = f"📄 配置: {os.path.basename(config_path)} | "
        if config.get("database_path"):
            config_display += f"数据库: {config['database_path']}"
        else:
            config_display += "数据库: inventory.db"
        self.statusBar().addPermanentWidget(QLabel(config_display))
    
    def setup_material_tab(self, parent):
        """设置物料管理标签页"""
        layout = QVBoxLayout()
        parent.setLayout(layout)
        
        # 工具栏
        toolbar = QHBoxLayout()
        
        add_btn = QPushButton("添加物料")
        add_btn.clicked.connect(self.add_material)
        toolbar.addWidget(add_btn)
        
        edit_btn = QPushButton("编辑物料")
        edit_btn.clicked.connect(self.edit_material)
        toolbar.addWidget(edit_btn)
        
        delete_btn = QPushButton("删除物料")
        delete_btn.clicked.connect(self.delete_material)
        toolbar.addWidget(delete_btn)
        
        refresh_btn = QPushButton("刷新")
        refresh_btn.clicked.connect(self.refresh_materials)
        toolbar.addWidget(refresh_btn)
        
        toolbar.addWidget(QLabel("搜索:"))
        self.material_search_edit = QLineEdit()
        self.material_search_edit.textChanged.connect(self.search_materials)
        toolbar.addWidget(self.material_search_edit)
        
        toolbar.addStretch()
        layout.addLayout(toolbar)
        
        # 创建分割器
        splitter = QSplitter(Qt.Horizontal)
        
        # 左侧物料列表
        list_widget = QWidget()
        list_layout = QVBoxLayout()
        list_widget.setLayout(list_layout)
        
        self.material_scroll = QScrollArea()
        self.material_scroll.setWidgetResizable(True)
        self.material_scroll.setWidget(QWidget())
        list_layout.addWidget(self.material_scroll)
        
        splitter.addWidget(list_widget)
        splitter.setStretchFactor(0, 2)
        
        # 右侧详情面板
        self.detail_widget = QWidget()
        self.detail_layout = QVBoxLayout()
        self.detail_widget.setLayout(self.detail_layout)
        
        self.detail_placeholder = QLabel("请点击左侧物料卡片查看详情")
        self.detail_placeholder.setAlignment(Qt.AlignCenter)
        self.detail_layout.addWidget(self.detail_placeholder)
        
        splitter.addWidget(self.detail_widget)
        splitter.setStretchFactor(1, 1)
        
        layout.addWidget(splitter)
    
    def setup_order_tab(self, parent):
        """设置订单管理标签页"""
        layout = QVBoxLayout()
        parent.setLayout(layout)
        
        # 工具栏
        toolbar = QHBoxLayout()
        
        create_btn = QPushButton("创建订单")
        create_btn.clicked.connect(self.create_order)
        toolbar.addWidget(create_btn)
        
        edit_btn = QPushButton("编辑订单")
        edit_btn.clicked.connect(self.edit_order)
        toolbar.addWidget(edit_btn)
        
        complete_btn = QPushButton("完成订单")
        complete_btn.clicked.connect(self.complete_order)
        toolbar.addWidget(complete_btn)
        
        cancel_btn = QPushButton("取消订单")
        cancel_btn.clicked.connect(self.cancel_order)
        toolbar.addWidget(cancel_btn)
        
        refresh_btn = QPushButton("刷新")
        refresh_btn.clicked.connect(self.refresh_orders)
        toolbar.addWidget(refresh_btn)
        
        toolbar.addWidget(QLabel("状态:"))
        self.order_status_combo = QComboBox()
        self.order_status_combo.addItems(["all", "pending", "in_progress", "completed", "cancelled"])
        self.order_status_combo.currentTextChanged.connect(self.filter_orders)
        toolbar.addWidget(self.order_status_combo)
        
        toolbar.addStretch()
        layout.addLayout(toolbar)
        
        # 订单表格
        self.order_table = QTableWidget()
        self.order_table.setColumnCount(7)
        self.order_table.setHorizontalHeaderLabels(["ID", "订单号", "申请人", "部门", "状态", "优先级", "创建时间"])
        self.order_table.horizontalHeader().setStretchLastSection(True)
        self.order_table.setSelectionBehavior(QTableWidget.SelectRows)
        layout.addWidget(self.order_table)
    
    def setup_report_tab(self, parent):
        """设置报告生成标签页"""
        layout = QVBoxLayout()
        parent.setLayout(layout)
        
        info_label = QLabel("选择要生成报告的订单，系统将自动生成包含订单详细信息的HTML报告。")
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        self.report_table = QTableWidget()
        self.report_table.setColumnCount(7)
        self.report_table.setHorizontalHeaderLabels(["ID", "订单号", "申请人", "部门", "状态", "优先级", "创建时间"])
        self.report_table.setSelectionMode(QTableWidget.ExtendedSelection)
        self.report_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.report_table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.report_table)
        
        btn_layout = QHBoxLayout()
        generate_btn = QPushButton("生成报告")
        generate_btn.clicked.connect(self.generate_report)
        btn_layout.addWidget(generate_btn)
        
        refresh_btn = QPushButton("刷新订单列表")
        refresh_btn.clicked.connect(self.refresh_report_orders)
        btn_layout.addWidget(refresh_btn)
        
        layout.addLayout(btn_layout)
    
    def refresh_data(self):
        """刷新所有数据"""
        self.refresh_materials()
        self.refresh_orders()
        self.refresh_report_orders()
    
    def refresh_materials(self):
        """刷新物料列表"""
        materials = self.material_controller.get_all_materials()
        self.update_material_cards(materials)
    
    def update_material_cards(self, materials: List[Material]):
        """更新物料卡片"""
        # 清空现有卡片
        for card in self.material_cards.values():
            card.deleteLater()
        self.material_cards.clear()
        
        # 清空详情面板缓存
        for panel in self.detail_panels.values():
            panel.deleteLater()
        self.detail_panels.clear()
        
        self.selected_material_id = None
        
        # 创建新卡片
        container = QWidget()
        layout = QVBoxLayout()
        container.setLayout(layout)
        
        for material in materials:
            card = MaterialCard(material)
            card.clicked.connect(self._on_card_clicked)
            layout.addWidget(card)
            self.material_cards[material.id] = card
        
        layout.addStretch()
        
        self.material_scroll.setWidget(container)
        
        # 显示placeholder
        self.detail_placeholder.show()
    
    def _on_card_clicked(self, material_id: int):
        """卡片点击事件"""
        # 取消之前选中的卡片
        if self.selected_material_id:
            if self.selected_material_id in self.material_cards:
                self.material_cards[self.selected_material_id].set_selected(False)
        
        # 选中当前卡片
        if material_id in self.material_cards:
            self.material_cards[material_id].set_selected(True)
        self.selected_material_id = material_id
        
        # 显示详情（从缓存）
        self._show_material_detail(material_id)
    
    def _show_material_detail(self, material_id: int):
        """显示物料详情"""
        # 隐藏placeholder
        self.detail_placeholder.hide()
        
        # 如果已经有缓存的面板，直接显示
        if material_id in self.detail_panels:
            # 隐藏所有面板
            for mid, panel in self.detail_panels.items():
                panel.hide()
            # 显示当前面板
            self.detail_panels[material_id].show()
            return
        
        # 从缓存获取物料信息
        material = self.material_controller.get_material(material_id)
        if not material:
            return
        
        # 创建新的详情面板并缓存
        panel = MaterialDetailPanel(material, self.detail_widget)
        panel.edit_requested.connect(self.edit_material_by_id)
        panel.delete_requested.connect(self.delete_material_by_id)
        self.detail_panels[material_id] = panel
        self.detail_layout.addWidget(panel)
    
    def add_material(self):
        """添加物料"""
        dialog = MaterialDialog(self, material_controller=self.material_controller)
        if dialog.exec_() == QDialog.Accepted:
            material = dialog.result
            if material:
                try:
                    material_id = self.material_controller.create_material(material)
                    QMessageBox.information(self, "成功", "物料添加成功")
                    self.refresh_materials()
                except Exception as e:
                    QMessageBox.critical(self, "错误", f"添加失败: {str(e)}")
    
    def edit_material(self):
        """编辑物料"""
        if not self.selected_material_id:
            QMessageBox.warning(self, "警告", "请先选择一个物料")
            return
        
        self.edit_material_by_id(self.selected_material_id)
    
    def edit_material_by_id(self, material_id: int):
        """根据ID编辑物料"""
        material = self.material_controller.get_material(material_id)
        if not material:
            QMessageBox.critical(self, "错误", "物料不存在")
            return
        
        dialog = MaterialDialog(self, material, self.material_controller)
        if dialog.exec_() == QDialog.Accepted:
            updated_material = dialog.result
            if updated_material:
                try:
                    success, message = self.material_controller.update_material(updated_material)
                    if success:
                        QMessageBox.information(self, "成功", message)
                        self.refresh_materials()
                    else:
                        QMessageBox.critical(self, "错误", message)
                except Exception as e:
                    QMessageBox.critical(self, "错误", f"更新失败: {str(e)}")
    
    def delete_material(self):
        """删除物料"""
        if not self.selected_material_id:
            QMessageBox.warning(self, "警告", "请先选择一个物料")
            return
        
        self.delete_material_by_id(self.selected_material_id)
    
    def delete_material_by_id(self, material_id: int):
        """根据ID删除物料"""
        if QMessageBox.question(self, "确认", "确定要删除这个物料吗？") == QMessageBox.Yes:
            try:
                self.material_controller.delete_material(material_id)
                QMessageBox.information(self, "成功", "物料删除成功")
                self.refresh_materials()
            except Exception as e:
                QMessageBox.critical(self, "错误", f"删除失败: {str(e)}")
    
    def search_materials(self):
        """搜索物料"""
        keyword = self.material_search_edit.text()
        if keyword:
            materials = self.material_controller.search_materials(keyword)
        else:
            materials = self.material_controller.get_all_materials()
        
        self.update_material_cards(materials)
    
    def refresh_orders(self):
        """刷新订单列表"""
        orders = self.order_controller.get_all_orders()
        self.order_table.setRowCount(len(orders))
        
        for row, order in enumerate(orders):
            self.order_table.setItem(row, 0, QTableWidgetItem(str(order.id)))
            self.order_table.setItem(row, 1, QTableWidgetItem(order.order_number))
            self.order_table.setItem(row, 2, QTableWidgetItem(order.requester))
            self.order_table.setItem(row, 3, QTableWidgetItem(order.department or ""))
            self.order_table.setItem(row, 4, QTableWidgetItem(order.status))
            self.order_table.setItem(row, 5, QTableWidgetItem(order.priority))
            created_at = order.created_at.strftime('%Y-%m-%d %H:%M') if order.created_at else 'N/A'
            self.order_table.setItem(row, 6, QTableWidgetItem(created_at))
    
    def refresh_report_orders(self):
        """刷新报告页面的订单列表"""
        orders = self.order_controller.get_all_orders()
        self.report_table.setRowCount(len(orders))
        
        for row, order in enumerate(orders):
            self.report_table.setItem(row, 0, QTableWidgetItem(str(order.id)))
            self.report_table.setItem(row, 1, QTableWidgetItem(order.order_number))
            self.report_table.setItem(row, 2, QTableWidgetItem(order.requester))
            self.report_table.setItem(row, 3, QTableWidgetItem(order.department or ""))
            self.report_table.setItem(row, 4, QTableWidgetItem(order.status))
            self.report_table.setItem(row, 5, QTableWidgetItem(order.priority))
            created_at = order.created_at.strftime('%Y-%m-%d %H:%M') if order.created_at else 'N/A'
            self.report_table.setItem(row, 6, QTableWidgetItem(created_at))
    
    def create_order(self):
        """创建订单"""
        dialog = OrderDialog(self, material_controller=self.material_controller)
        if dialog.exec_() == QDialog.Accepted:
            order = dialog.result
            if order:
                try:
                    self.order_controller.create_order(order)
                    QMessageBox.information(self, "成功", "订单创建成功")
                    self.refresh_orders()
                except Exception as e:
                    QMessageBox.critical(self, "错误", f"创建失败: {str(e)}")
    
    def edit_order(self):
        """编辑订单"""
        current_row = self.order_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "警告", "请选择要编辑的订单")
            return
        
        order_id = int(self.order_table.item(current_row, 0).text())
        order = self.order_controller.get_order(order_id)
        
        if order:
            dialog = OrderDialog(self, order, self.material_controller)
            if dialog.exec_() == QDialog.Accepted:
                updated_order = dialog.result
                if updated_order:
                    try:
                        self.order_controller.update_order(updated_order)
                        QMessageBox.information(self, "成功", "订单更新成功")
                        self.refresh_orders()
                    except Exception as e:
                        QMessageBox.critical(self, "错误", f"更新失败: {str(e)}")
    
    def complete_order(self):
        """完成订单"""
        current_row = self.order_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "警告", "请选择要完成的订单")
            return
        
        order_id = int(self.order_table.item(current_row, 0).text())
        order_number = self.order_table.item(current_row, 1).text()
        
        if QMessageBox.question(self, "确认完成订单", 
                              f"确定要完成订单 {order_number} 吗？\n\n"
                              f"此操作将：\n"
                              f"• 更新订单状态为已完成\n"
                              f"• 减少相关物料的库存\n"
                              f"• 记录库存变动历史\n\n"
                              f"此操作不可撤销！") == QMessageBox.Yes:
            try:
                success, message = self.order_controller.complete_order(order_id)
                if success:
                    QMessageBox.information(self, "成功", message)
                    self.refresh_orders()
                    self.refresh_materials()
                else:
                    QMessageBox.critical(self, "错误", message)
            except Exception as e:
                QMessageBox.critical(self, "错误", f"完成失败: {str(e)}")
    
    def cancel_order(self):
        """取消订单"""
        current_row = self.order_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "警告", "请选择要取消的订单")
            return
        
        if QMessageBox.question(self, "确认", "确定要取消选中的订单吗？") == QMessageBox.Yes:
            order_id = int(self.order_table.item(current_row, 0).text())
            try:
                self.order_controller.cancel_order(order_id)
                QMessageBox.information(self, "成功", "订单已取消")
                self.refresh_orders()
            except Exception as e:
                QMessageBox.critical(self, "错误", f"取消失败: {str(e)}")
    
    def filter_orders(self):
        """筛选订单"""
        status = self.order_status_combo.currentText()
        if status == "all":
            orders = self.order_controller.get_all_orders()
        else:
            orders = self.order_controller.get_orders_by_status(status)
        
        self.order_table.setRowCount(len(orders))
        for row, order in enumerate(orders):
            self.order_table.setItem(row, 0, QTableWidgetItem(str(order.id)))
            self.order_table.setItem(row, 1, QTableWidgetItem(order.order_number))
            self.order_table.setItem(row, 2, QTableWidgetItem(order.requester))
            self.order_table.setItem(row, 3, QTableWidgetItem(order.department or ""))
            self.order_table.setItem(row, 4, QTableWidgetItem(order.status))
            self.order_table.setItem(row, 5, QTableWidgetItem(order.priority))
            created_at = order.created_at.strftime('%Y-%m-%d %H:%M') if order.created_at else 'N/A'
            self.order_table.setItem(row, 6, QTableWidgetItem(created_at))
    
    def generate_report(self):
        """生成订单报告"""
        # 获取选中的行
        selected_ranges = self.report_table.selectedRanges()
        if not selected_ranges:
            QMessageBox.warning(self, "警告", "请选择要生成报告的订单")
            return
        
        # 获取选中的订单ID
        order_ids = set()
        for range_item in selected_ranges:
            top_row = range_item.topRow()
            bottom_row = range_item.bottomRow()
            for row in range(top_row, bottom_row + 1):
                if self.report_table.item(row, 0):
                    order_id = int(self.report_table.item(row, 0).text())
                    order_ids.add(order_id)
        
        if not order_ids:
            QMessageBox.warning(self, "警告", "请选择要生成报告的订单")
            return
        
        # 生成报告
        try:
            html_content = self.report_controller.generate_order_report(list(order_ids))
            
            # 保存文件
            filename, _ = QFileDialog.getSaveFileName(
                self, "保存报告", "order_report.html", "HTML文件 (*.html)"
            )
            
            if filename:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(html_content)
                QMessageBox.information(self, "成功", f"报告已保存到: {filename}")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"生成报告失败: {str(e)}")

def main():
    """主函数"""
    app = QApplication(sys.argv)
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()

