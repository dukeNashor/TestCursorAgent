"""
数据库基础设施
负责SQLite数据库的连接管理和基础操作
各模块的表结构由各自的repository负责初始化
"""
import sqlite3
import os
import time
import threading
import json
from typing import List, Dict, Any, Optional


def get_config_path() -> str:
    """获取配置文件路径"""
    return os.path.join(os.path.dirname(__file__), "config.json")


def load_config() -> Dict[str, Any]:
    """加载配置文件"""
    config_path = get_config_path()
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
            # 兼容旧版配置格式
            if "databases" not in config:
                old_path = config.get("database_path", "inventory.db")
                config = {
                    "databases": [{"name": "默认数据库", "path": old_path}],
                    "current_database": 0
                }
            return config
    except FileNotFoundError:
        # 如果配置文件不存在，返回默认配置
        return {
            "databases": [{"name": "默认数据库", "path": "inventory.db"}],
            "current_database": 0
        }
    except json.JSONDecodeError:
        # 如果配置文件格式错误，返回默认配置
        return {
            "databases": [{"name": "默认数据库", "path": "inventory.db"}],
            "current_database": 0
        }


def save_config(config: Dict[str, Any]):
    """保存配置文件"""
    config_path = get_config_path()
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=4)


def get_current_database_path() -> str:
    """获取当前数据库路径"""
    config = load_config()
    databases = config.get("databases", [])
    current_idx = config.get("current_database", 0)
    if databases and 0 <= current_idx < len(databases):
        return databases[current_idx].get("path", "inventory.db")
    return "inventory.db"


def get_database_list() -> List[Dict[str, str]]:
    """获取数据库列表"""
    config = load_config()
    return config.get("databases", [])


def add_database(name: str, path: str) -> bool:
    """添加数据库到配置"""
    config = load_config()
    databases = config.get("databases", [])
    # 检查路径是否已存在
    for db in databases:
        if db.get("path") == path:
            return False
    databases.append({"name": name, "path": path})
    config["databases"] = databases
    save_config(config)
    return True


def remove_database(index: int) -> bool:
    """从配置中移除数据库"""
    config = load_config()
    databases = config.get("databases", [])
    if 0 <= index < len(databases) and len(databases) > 1:
        databases.pop(index)
        config["databases"] = databases
        # 调整当前数据库索引
        if config.get("current_database", 0) >= len(databases):
            config["current_database"] = len(databases) - 1
        save_config(config)
        return True
    return False


def set_current_database(index: int) -> bool:
    """设置当前数据库"""
    config = load_config()
    databases = config.get("databases", [])
    if 0 <= index < len(databases):
        config["current_database"] = index
        save_config(config)
        return True
    return False


class DatabaseManager:
    """数据库管理器，负责数据库连接和基础操作"""
    
    def __init__(self, db_path: str = None):
        # 如果未指定路径，从配置文件读取
        if db_path is None:
            self.db_path = get_current_database_path()
        else:
            self.db_path = db_path
        
        self._lock = threading.Lock()  # 线程锁
        self.max_retries = 3  # 最大重试次数
        self.retry_delay = 0.1  # 重试延迟（秒）
        self.init_database()
    
    def switch_database(self, db_path: str):
        """切换到新的数据库"""
        self.db_path = db_path
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
                # 启用外键约束
                conn.execute("PRAGMA foreign_keys=ON")
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
        
        # 初始化物料模块的表
        from material.repository import init_material_tables
        init_material_tables(cursor)
        
        # 初始化ADC模块的表
        from adc.repository import init_adc_tables
        init_adc_tables(cursor)
        
        # 初始化ADC实验流程模块的表
        from adc_workflow.repository import init_adc_workflow_tables
        init_adc_workflow_tables(cursor)
        
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

    def with_connection(self, fn):
        """在单一连接上执行 fn(cursor)，返回 fn 的返回值。调用方负责 commit/rollback。"""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            result = fn(cursor)
            conn.commit()
            return result
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

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
