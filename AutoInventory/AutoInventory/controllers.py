"""
控制器层
实现业务逻辑和数据操作
"""
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid

from database import DatabaseManager
from models import Material, Order, OrderMaterial, StockMovement, OrderStatus, Priority, MovementType

class MaterialController:
    """物料控制器"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
    
    def create_material(self, material: Material) -> int:
        """创建新物料"""
        query = '''
            INSERT INTO materials (name, category, description, quantity, unit, min_stock, location, supplier)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        '''
        material_id = self.db.execute_insert(query, (
            material.name, material.category, material.description,
            material.quantity, material.unit, material.min_stock,
            material.location, material.supplier
        ))
        
        # 记录库存变动
        if material.quantity > 0:
            self._record_stock_movement(material_id, MovementType.IN.value, material.quantity, "初始库存")
        
        return material_id
    
    def get_material(self, material_id: int) -> Optional[Material]:
        """获取单个物料"""
        query = "SELECT * FROM materials WHERE id = ?"
        results = self.db.execute_query(query, (material_id,))
        if results:
            return Material.from_dict(results[0])
        return None
    
    def get_all_materials(self) -> List[Material]:
        """获取所有物料"""
        query = "SELECT * FROM materials ORDER BY name"
        results = self.db.execute_query(query)
        return [Material.from_dict(row) for row in results]
    
    def update_material(self, material: Material, expected_version: str = None) -> tuple[bool, str]:
        """更新物料信息，返回(成功状态, 错误信息)"""
        if not material.id:
            return False, "物料ID不能为空"
        
        # 获取当前库存和版本信息
        current_data = self.db.get_material_with_version(material.id)
        if not current_data:
            return False, "物料不存在"
        
        # 如果提供了期望版本，使用乐观锁
        if expected_version and current_data['version'] != expected_version:
            return False, "数据已被其他用户修改，请刷新后重试"
        
        # 准备更新数据
        update_data = {
            'name': material.name,
            'category': material.category,
            'description': material.description,
            'quantity': material.quantity,
            'unit': material.unit,
            'min_stock': material.min_stock,
            'location': material.location,
            'supplier': material.supplier
        }
        
        # 使用乐观锁更新
        if expected_version:
            success = self.db.update_material_with_version(material.id, update_data, expected_version)
            if not success:
                return False, "数据已被其他用户修改，请刷新后重试"
        else:
            # 传统更新方式（向后兼容）
            query = '''
                UPDATE materials 
                SET name=?, category=?, description=?, quantity=?, unit=?, 
                    min_stock=?, location=?, supplier=?, updated_at=CURRENT_TIMESTAMP
                WHERE id=?
            '''
            affected = self.db.execute_update(query, (
                material.name, material.category, material.description,
                material.quantity, material.unit, material.min_stock,
                material.location, material.supplier, material.id
            ))
            if affected == 0:
                return False, "更新失败，物料可能已被删除"
        
        # 记录库存变动
        quantity_diff = material.quantity - current_data['quantity']
        if quantity_diff != 0:
            movement_type = MovementType.IN.value if quantity_diff > 0 else MovementType.OUT.value
            self._record_stock_movement(material.id, movement_type, abs(quantity_diff), "库存调整")
        
        return True, "更新成功"
    
    def delete_material(self, material_id: int) -> bool:
        """删除物料"""
        query = "DELETE FROM materials WHERE id = ?"
        affected = self.db.execute_update(query, (material_id,))
        return affected > 0
    
    def search_materials(self, keyword: str) -> List[Material]:
        """搜索物料"""
        query = '''
            SELECT * FROM materials 
            WHERE name LIKE ? OR category LIKE ? OR description LIKE ?
            ORDER BY name
        '''
        search_term = f"%{keyword}%"
        results = self.db.execute_query(query, (search_term, search_term, search_term))
        return [Material.from_dict(row) for row in results]
    
    def get_low_stock_materials(self) -> List[Material]:
        """获取库存不足的物料"""
        query = "SELECT * FROM materials WHERE quantity <= min_stock ORDER BY quantity ASC"
        results = self.db.execute_query(query)
        return [Material.from_dict(row) for row in results]
    
    def _record_stock_movement(self, material_id: int, movement_type: str, quantity: int, notes: str):
        """记录库存变动"""
        query = '''
            INSERT INTO stock_movements (material_id, movement_type, quantity, notes)
            VALUES (?, ?, ?, ?)
        '''
        self.db.execute_insert(query, (material_id, movement_type, quantity, notes))

class OrderController:
    """订单控制器"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
    
    def create_order(self, order: Order) -> int:
        """创建新订单"""
        if not order.order_number:
            order.order_number = self._generate_order_number()
        
        query = '''
            INSERT INTO orders (order_number, requester, department, status, priority, notes)
            VALUES (?, ?, ?, ?, ?, ?)
        '''
        order_id = self.db.execute_insert(query, (
            order.order_number, order.requester, order.department,
            order.status, order.priority, order.notes
        ))
        
        # 添加订单物料
        for material_data in order.materials:
            self.add_material_to_order(order_id, material_data['material_id'], 
                                     material_data['quantity'], material_data.get('notes', ''))
        
        return order_id
    
    def get_order(self, order_id: int) -> Optional[Order]:
        """获取单个订单"""
        query = "SELECT * FROM orders WHERE id = ?"
        results = self.db.execute_query(query, (order_id,))
        if not results:
            return None
        
        order = Order.from_dict(results[0])
        order.materials = self.get_order_materials(order_id)
        return order
    
    def get_all_orders(self) -> List[Order]:
        """获取所有订单"""
        query = "SELECT * FROM orders ORDER BY created_at DESC"
        results = self.db.execute_query(query)
        orders = []
        for row in results:
            order = Order.from_dict(row)
            order.materials = self.get_order_materials(order.id)
            orders.append(order)
        return orders
    
    def update_order(self, order: Order) -> bool:
        """更新订单"""
        if not order.id:
            return False
        
        query = '''
            UPDATE orders 
            SET order_number=?, requester=?, department=?, status=?, 
                priority=?, notes=?, updated_at=CURRENT_TIMESTAMP
            WHERE id=?
        '''
        affected = self.db.execute_update(query, (
            order.order_number, order.requester, order.department,
            order.status, order.priority, order.notes, order.id
        ))
        
        return affected > 0
    
    def complete_order(self, order_id: int) -> tuple[bool, str]:
        """完成订单，返回(成功状态, 错误信息)"""
        # 首先检查订单状态
        order = self.get_order(order_id)
        if not order:
            return False, "订单不存在"
        
        if order.status == OrderStatus.COMPLETED.value:
            return False, "订单已完成"
        
        if order.status == OrderStatus.CANCELLED.value:
            return False, "订单已取消，无法完成"
        
        # 检查库存是否充足
        materials = self.get_order_materials(order_id)
        for material_data in materials:
            material_id = material_data['material_id']
            required_quantity = material_data['quantity']
            
            material = self.get_material(material_id)
            if not material:
                return False, f"物料ID {material_id} 不存在"
            
            if material.quantity < required_quantity:
                return False, f"物料 '{material.name}' 库存不足，需要 {required_quantity}，当前库存 {material.quantity}"
        
        # 使用事务完成订单和更新库存
        operations = []
        
        # 更新订单状态
        operations.append((
            "UPDATE orders SET status=?, completed_at=CURRENT_TIMESTAMP, updated_at=CURRENT_TIMESTAMP WHERE id=?",
            (OrderStatus.COMPLETED.value, order_id)
        ))
        
        # 更新库存和记录变动
        for material_data in materials:
            material_id = material_data['material_id']
            quantity = material_data['quantity']
            
            # 减少库存
            operations.append((
                "UPDATE materials SET quantity = quantity - ? WHERE id = ?",
                (quantity, material_id)
            ))
            
            # 记录库存变动
            operations.append((
                "INSERT INTO stock_movements (material_id, movement_type, quantity, reference_id, notes) VALUES (?, ?, ?, ?, ?)",
                (material_id, MovementType.OUT.value, quantity, order_id, "订单完成")
            ))
        
        try:
            self.db.execute_transaction(operations)
            return True, "订单完成成功"
        except Exception as e:
            return False, f"完成订单失败: {str(e)}"
    
    def cancel_order(self, order_id: int) -> bool:
        """取消订单"""
        query = '''
            UPDATE orders 
            SET status=?, updated_at=CURRENT_TIMESTAMP
            WHERE id=?
        '''
        affected = self.db.execute_update(query, (OrderStatus.CANCELLED.value, order_id))
        return affected > 0
    
    def add_material_to_order(self, order_id: int, material_id: int, quantity: int, notes: str = "") -> int:
        """向订单添加物料"""
        query = '''
            INSERT INTO order_materials (order_id, material_id, quantity, notes)
            VALUES (?, ?, ?, ?)
        '''
        return self.db.execute_insert(query, (order_id, material_id, quantity, notes))
    
    def remove_material_from_order(self, order_material_id: int) -> bool:
        """从订单中移除物料"""
        query = "DELETE FROM order_materials WHERE id = ?"
        affected = self.db.execute_update(query, (order_material_id,))
        return affected > 0
    
    def get_order_materials(self, order_id: int) -> List[Dict[str, Any]]:
        """获取订单中的物料列表"""
        query = '''
            SELECT om.*, m.name as material_name, m.unit, m.category
            FROM order_materials om
            JOIN materials m ON om.material_id = m.id
            WHERE om.order_id = ?
        '''
        results = self.db.execute_query(query, (order_id,))
        return results
    
    def get_orders_by_status(self, status: str) -> List[Order]:
        """根据状态获取订单"""
        query = "SELECT * FROM orders WHERE status = ? ORDER BY created_at DESC"
        results = self.db.execute_query(query, (status,))
        orders = []
        for row in results:
            order = Order.from_dict(row)
            order.materials = self.get_order_materials(order.id)
            orders.append(order)
        return orders
    
    def _generate_order_number(self) -> str:
        """生成订单号"""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        return f"ORD-{timestamp}-{unique_id}"
    

class ReportController:
    """报告控制器"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
    
    def generate_order_report(self, order_ids: List[int]) -> str:
        """生成订单HTML报告"""
        orders = []
        for order_id in order_ids:
            order = OrderController(self.db).get_order(order_id)
            if order:
                orders.append(order)
        
        if not orders:
            return "<html><body><h1>没有找到订单</h1></body></html>"
        
        html_content = self._generate_html_template(orders)
        return html_content
    
    def _generate_html_template(self, orders: List[Order]) -> str:
        """生成HTML模板"""
        html = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>库存订单报告</title>
    <style>
        body {
            font-family: 'Microsoft YaHei', Arial, sans-serif;
            margin: 20px;
            background-color: #f5f5f5;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .header {
            text-align: center;
            margin-bottom: 30px;
            padding-bottom: 20px;
            border-bottom: 2px solid #007bff;
        }
        .header h1 {
            color: #007bff;
            margin: 0;
        }
        .order {
            margin-bottom: 30px;
            border: 1px solid #ddd;
            border-radius: 8px;
            overflow: hidden;
        }
        .order-header {
            background: #007bff;
            color: white;
            padding: 15px;
            font-weight: bold;
        }
        .order-info {
            padding: 20px;
            background: #f8f9fa;
        }
        .order-info table {
            width: 100%;
            border-collapse: collapse;
        }
        .order-info td {
            padding: 8px;
            border-bottom: 1px solid #eee;
        }
        .order-info td:first-child {
            font-weight: bold;
            width: 150px;
        }
        .materials-table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 15px;
        }
        .materials-table th,
        .materials-table td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }
        .materials-table th {
            background: #007bff;
            color: white;
        }
        .materials-table tr:nth-child(even) {
            background: #f8f9fa;
        }
        .status {
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 12px;
            font-weight: bold;
        }
        .status-pending { background: #ffc107; color: #000; }
        .status-in_progress { background: #17a2b8; color: white; }
        .status-completed { background: #28a745; color: white; }
        .status-cancelled { background: #dc3545; color: white; }
        .priority {
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 12px;
            font-weight: bold;
        }
        .priority-low { background: #6c757d; color: white; }
        .priority-normal { background: #007bff; color: white; }
        .priority-high { background: #fd7e14; color: white; }
        .priority-urgent { background: #dc3545; color: white; }
        .footer {
            text-align: center;
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid #ddd;
            color: #666;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🧪 生物实验室库存订单报告</h1>
            <p>生成时间: {}</p>
        </div>
"""
        
        # 添加订单内容
        for order in orders:
            html += self._generate_order_html(order)
        
        # 添加页脚
        html += """
        <div class="footer">
            <p>此报告由库存管理系统自动生成</p>
        </div>
    </div>
</body>
</html>
""".format(datetime.now().strftime("%Y年%m月%d日 %H:%M:%S"))
        
        return html
    
    def _generate_order_html(self, order: Order) -> str:
        """生成单个订单的HTML"""
        status_class = f"status-{order.status}"
        priority_class = f"priority-{order.priority}"
        
        html = f"""
        <div class="order">
            <div class="order-header">
                订单号: {order.order_number}
            </div>
            <div class="order-info">
                <table>
                    <tr>
                        <td>申请人:</td>
                        <td>{order.requester}</td>
                        <td>部门:</td>
                        <td>{order.department}</td>
                    </tr>
                    <tr>
                        <td>状态:</td>
                        <td><span class="status {status_class}">{self._get_status_text(order.status)}</span></td>
                        <td>优先级:</td>
                        <td><span class="priority {priority_class}">{self._get_priority_text(order.priority)}</span></td>
                    </tr>
                    <tr>
                        <td>创建时间:</td>
                        <td>{order.created_at.strftime('%Y-%m-%d %H:%M:%S') if order.created_at else 'N/A'}</td>
                        <td>更新时间:</td>
                        <td>{order.updated_at.strftime('%Y-%m-%d %H:%M:%S') if order.updated_at else 'N/A'}</td>
                    </tr>
                </table>
"""
        
        if order.notes:
            html += f"""
                <p><strong>备注:</strong> {order.notes}</p>
"""
        
        if order.materials:
            html += """
                <table class="materials-table">
                    <thead>
                        <tr>
                            <th>物料名称</th>
                            <th>类别</th>
                            <th>数量</th>
                            <th>单位</th>
                            <th>备注</th>
                        </tr>
                    </thead>
                    <tbody>
"""
            for material in order.materials:
                html += f"""
                        <tr>
                            <td>{material['material_name']}</td>
                            <td>{material['category']}</td>
                            <td>{material['quantity']}</td>
                            <td>{material['unit']}</td>
                            <td>{material.get('notes', '')}</td>
                        </tr>
"""
            html += """
                    </tbody>
                </table>
"""
        
        html += """
            </div>
        </div>
"""
        return html
    
    def _get_status_text(self, status: str) -> str:
        """获取状态文本"""
        status_map = {
            'pending': '待处理',
            'in_progress': '处理中',
            'completed': '已完成',
            'cancelled': '已取消'
        }
        return status_map.get(status, status)
    
    def _get_priority_text(self, priority: str) -> str:
        """获取优先级文本"""
        priority_map = {
            'low': '低',
            'normal': '普通',
            'high': '高',
            'urgent': '紧急'
        }
        return priority_map.get(priority, priority)
