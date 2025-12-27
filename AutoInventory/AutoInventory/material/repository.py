"""
物料模块 - 数据库操作层
负责物料相关表的数据库操作
"""
from typing import List, Dict, Any, Optional


def init_material_tables(cursor):
    """初始化物料相关表结构"""
    # 创建物料表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS materials (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            category TEXT NOT NULL,
            description TEXT,
            quantity INTEGER NOT NULL DEFAULT 0,
            unit TEXT NOT NULL,
            min_stock INTEGER DEFAULT 0,
            location TEXT,
            supplier TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 创建订单表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_number TEXT UNIQUE NOT NULL,
            requester TEXT NOT NULL,
            department TEXT,
            status TEXT NOT NULL DEFAULT 'pending',
            priority TEXT DEFAULT 'normal',
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completed_at TIMESTAMP
        )
    ''')
    
    # 创建订单物料关联表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS order_materials (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL,
            material_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL,
            notes TEXT,
            FOREIGN KEY (order_id) REFERENCES orders (id) ON DELETE CASCADE,
            FOREIGN KEY (material_id) REFERENCES materials (id) ON DELETE CASCADE
        )
    ''')
    
    # 创建库存变动记录表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS stock_movements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            material_id INTEGER NOT NULL,
            movement_type TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            reference_id INTEGER,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (material_id) REFERENCES materials (id) ON DELETE CASCADE
        )
    ''')
    
    # 迁移并创建物料图片表
    _migrate_material_images_table(cursor)


def _migrate_material_images_table(cursor):
    """迁移 material_images 表结构"""
    try:
        # 检查表是否存在
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='material_images'")
        table_exists = cursor.fetchone()
        
        if table_exists:
            # 检查是否有 image_path 列（旧结构）
            cursor.execute("PRAGMA table_info(material_images)")
            columns = [row[1] for row in cursor.fetchall()]
            
            if 'image_path' in columns and 'image_data' not in columns:
                # 需要迁移：删除旧表并创建新表
                print("检测到旧版本表结构，正在迁移...")
                cursor.execute("DROP TABLE IF EXISTS material_images")
                
        # 创建新表结构
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS material_images (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                material_id INTEGER NOT NULL,
                image_data BLOB NOT NULL,
                image_type TEXT,
                display_order INTEGER DEFAULT 0,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (material_id) REFERENCES materials (id) ON DELETE CASCADE
            )
        ''')
    except Exception as e:
        print(f"迁移表结构时出错: {e}")
        # 如果迁移失败，尝试直接创建新表
        cursor.execute("DROP TABLE IF EXISTS material_images")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS material_images (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                material_id INTEGER NOT NULL,
                image_data BLOB NOT NULL,
                image_type TEXT,
                display_order INTEGER DEFAULT 0,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (material_id) REFERENCES materials (id) ON DELETE CASCADE
            )
        ''')


class MaterialRepository:
    """物料数据仓库"""
    
    def __init__(self, db_manager):
        self.db = db_manager
    
    def get_material_with_version(self, material_id: int) -> Optional[Dict[str, Any]]:
        """获取物料信息，包含版本号用于乐观锁"""
        query = "SELECT *, updated_at as version FROM materials WHERE id = ?"
        results = self.db.execute_query(query, (material_id,))
        return results[0] if results else None
    
    def update_material_with_version(self, material_id: int, data: dict, expected_version: str) -> bool:
        """使用乐观锁更新物料信息"""
        query = '''
            UPDATE materials 
            SET name=?, category=?, description=?, quantity=?, unit=?, 
                min_stock=?, location=?, supplier=?, updated_at=CURRENT_TIMESTAMP
            WHERE id=? AND updated_at=?
        '''
        params = (
            data['name'], data['category'], data['description'],
            data['quantity'], data['unit'], data['min_stock'],
            data['location'], data['supplier'], material_id, expected_version
        )
        affected = self.db.execute_update(query, params)
        return affected > 0
    
    def add_material_image(self, material_id: int, image_data: bytes, image_type: str, 
                          display_order: int = 0, notes: str = "") -> int:
        """添加物料图片（存储二进制数据）"""
        query = '''
            INSERT INTO material_images (material_id, image_data, image_type, display_order, notes)
            VALUES (?, ?, ?, ?, ?)
        '''
        return self.db.execute_insert(query, (material_id, image_data, image_type, display_order, notes))
    
    def get_material_images(self, material_id: int) -> List[Dict[str, Any]]:
        """获取物料的图片列表（返回二进制数据）"""
        query = '''
            SELECT id, material_id, image_data, image_type, display_order, notes, created_at
            FROM material_images 
            WHERE material_id = ? 
            ORDER BY display_order, created_at
        '''
        return self.db.execute_query(query, (material_id,))
    
    def delete_material_image(self, image_id: int) -> bool:
        """删除物料图片"""
        query = "DELETE FROM material_images WHERE id = ?"
        affected = self.db.execute_update(query, (image_id,))
        return affected > 0
    
    def delete_material_images(self, material_id: int) -> bool:
        """删除物料的所有图片"""
        query = "DELETE FROM material_images WHERE material_id = ?"
        affected = self.db.execute_update(query, (material_id,))
        return affected > 0

