"""
数据库模型和连接管理
负责SQLite数据库的初始化和表结构管理
"""
import sqlite3
import os
import time
import threading
from datetime import datetime
from typing import List, Dict, Any, Optional

class DatabaseManager:
    """数据库管理器，负责数据库连接和表管理"""
    
    def __init__(self, db_path: str = "inventory.db"):
        self.db_path = db_path
        self._lock = threading.Lock()  # 线程锁
        self.max_retries = 3  # 最大重试次数
        self.retry_delay = 0.1  # 重试延迟（秒）
        self.init_database()
    
    def get_connection(self) -> sqlite3.Connection:
        """获取数据库连接，支持重试机制"""
        for attempt in range(self.max_retries):
            try:
                conn = sqlite3.connect(self.db_path, timeout=10.0)  # 10秒超时
                conn.row_factory = sqlite3.Row
                # 启用WAL模式提高并发性能
                conn.execute("PRAGMA journal_mode=WAL")
                conn.execute("PRAGMA synchronous=NORMAL")
                conn.execute("PRAGMA cache_size=10000")
                return conn
            except sqlite3.OperationalError as e:
                if "database is locked" in str(e) and attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay * (attempt + 1))  # 递增延迟
                    continue
                raise
    
    def init_database(self):
        """初始化数据库表结构"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
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
                movement_type TEXT NOT NULL, -- 'in', 'out', 'adjustment'
                quantity INTEGER NOT NULL,
                reference_id INTEGER, -- 关联订单ID或其他参考
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (material_id) REFERENCES materials (id) ON DELETE CASCADE
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def execute_query(self, query: str, params: tuple = ()) -> List[Dict[str, Any]]:
        """执行查询并返回结果"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(query, params)
        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return results
    
    def execute_update(self, query: str, params: tuple = ()) -> int:
        """执行更新操作并返回影响的行数"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(query, params)
        conn.commit()
        affected_rows = cursor.rowcount
        conn.close()
        return affected_rows
    
    def execute_insert(self, query: str, params: tuple = ()) -> int:
        """执行插入操作并返回新插入行的ID"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(query, params)
        conn.commit()
        new_id = cursor.lastrowid
        conn.close()
        return new_id
    
    def execute_transaction(self, operations: List[tuple]) -> bool:
        """执行事务操作，确保原子性"""
        with self._lock:  # 使用锁确保事务的原子性
            conn = None
            try:
                conn = self.get_connection()
                cursor = conn.cursor()
                
                for query, params in operations:
                    cursor.execute(query, params)
                
                conn.commit()
                return True
            except Exception as e:
                if conn:
                    conn.rollback()
                raise e
            finally:
                if conn:
                    conn.close()
    
    def get_material_with_version(self, material_id: int) -> Optional[Dict[str, Any]]:
        """获取物料信息，包含版本号用于乐观锁"""
        query = "SELECT *, updated_at as version FROM materials WHERE id = ?"
        results = self.execute_query(query, (material_id,))
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
        affected = self.execute_update(query, params)
        return affected > 0
