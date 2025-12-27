"""
ADC模块 - 数据库操作层
负责ADC相关表的数据库操作
"""
from typing import List, Dict, Any, Optional


def init_adc_tables(cursor):
    """初始化ADC相关表结构"""
    # 创建ADC主表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS adc (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lot_number TEXT UNIQUE NOT NULL,
            sample_id TEXT NOT NULL,
            description TEXT,
            concentration REAL DEFAULT 0.0,
            owner TEXT,
            storage_temp TEXT,
            storage_position TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 创建ADC规格库存表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS adc_specs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            adc_id INTEGER NOT NULL,
            spec_mg REAL NOT NULL,
            quantity INTEGER NOT NULL DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (adc_id) REFERENCES adc (id) ON DELETE CASCADE
        )
    ''')
    
    # 为sample_id创建索引以加速查询
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_adc_sample_id ON adc (sample_id)
    ''')


class ADCRepository:
    """ADC数据仓库"""
    
    def __init__(self, db_manager):
        self.db = db_manager
    
    # ==================== ADC CRUD ====================
    
    def create_adc(self, lot_number: str, sample_id: str, description: str = "",
                   concentration: float = 0.0, owner: str = "", 
                   storage_temp: str = "", storage_position: str = "") -> int:
        """创建ADC记录"""
        query = '''
            INSERT INTO adc (lot_number, sample_id, description, concentration, 
                           owner, storage_temp, storage_position)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        '''
        return self.db.execute_insert(query, (
            lot_number, sample_id, description, concentration,
            owner, storage_temp, storage_position
        ))
    
    def get_adc_by_id(self, adc_id: int) -> Optional[Dict[str, Any]]:
        """根据ID获取ADC"""
        query = "SELECT * FROM adc WHERE id = ?"
        results = self.db.execute_query(query, (adc_id,))
        return results[0] if results else None
    
    def get_adc_by_lot_number(self, lot_number: str) -> Optional[Dict[str, Any]]:
        """根据Lot Number获取ADC"""
        query = "SELECT * FROM adc WHERE lot_number = ?"
        results = self.db.execute_query(query, (lot_number,))
        return results[0] if results else None
    
    def get_all_adcs(self) -> List[Dict[str, Any]]:
        """获取所有ADC"""
        query = "SELECT * FROM adc ORDER BY created_at DESC"
        return self.db.execute_query(query)
    
    def search_by_sample_id(self, sample_id: str) -> List[Dict[str, Any]]:
        """根据SampleID搜索ADC（模糊匹配）"""
        query = "SELECT * FROM adc WHERE sample_id LIKE ? ORDER BY created_at DESC"
        return self.db.execute_query(query, (f"%{sample_id}%",))
    
    def update_adc(self, adc_id: int, lot_number: str, sample_id: str, 
                   description: str, concentration: float, owner: str,
                   storage_temp: str, storage_position: str) -> bool:
        """更新ADC记录"""
        query = '''
            UPDATE adc 
            SET lot_number=?, sample_id=?, description=?, concentration=?,
                owner=?, storage_temp=?, storage_position=?, updated_at=CURRENT_TIMESTAMP
            WHERE id=?
        '''
        affected = self.db.execute_update(query, (
            lot_number, sample_id, description, concentration,
            owner, storage_temp, storage_position, adc_id
        ))
        return affected > 0
    
    def delete_adc(self, adc_id: int) -> bool:
        """删除ADC记录（会级联删除相关规格）"""
        query = "DELETE FROM adc WHERE id = ?"
        affected = self.db.execute_update(query, (adc_id,))
        return affected > 0
    
    # ==================== ADC Specs CRUD ====================
    
    def add_spec(self, adc_id: int, spec_mg: float, quantity: int) -> int:
        """添加规格"""
        query = '''
            INSERT INTO adc_specs (adc_id, spec_mg, quantity)
            VALUES (?, ?, ?)
        '''
        return self.db.execute_insert(query, (adc_id, spec_mg, quantity))
    
    def get_specs_by_adc_id(self, adc_id: int) -> List[Dict[str, Any]]:
        """获取ADC的所有规格"""
        query = "SELECT * FROM adc_specs WHERE adc_id = ? ORDER BY spec_mg"
        return self.db.execute_query(query, (adc_id,))
    
    def get_spec_by_id(self, spec_id: int) -> Optional[Dict[str, Any]]:
        """根据ID获取规格"""
        query = "SELECT * FROM adc_specs WHERE id = ?"
        results = self.db.execute_query(query, (spec_id,))
        return results[0] if results else None
    
    def update_spec(self, spec_id: int, spec_mg: float, quantity: int) -> bool:
        """更新规格"""
        query = "UPDATE adc_specs SET spec_mg=?, quantity=? WHERE id=?"
        affected = self.db.execute_update(query, (spec_mg, quantity, spec_id))
        return affected > 0
    
    def update_spec_quantity(self, spec_id: int, quantity: int) -> bool:
        """更新规格库存量"""
        query = "UPDATE adc_specs SET quantity=? WHERE id=?"
        affected = self.db.execute_update(query, (quantity, spec_id))
        return affected > 0
    
    def delete_spec(self, spec_id: int) -> bool:
        """删除规格"""
        query = "DELETE FROM adc_specs WHERE id = ?"
        affected = self.db.execute_update(query, (spec_id,))
        return affected > 0
    
    def delete_specs_by_adc_id(self, adc_id: int) -> bool:
        """删除ADC的所有规格"""
        query = "DELETE FROM adc_specs WHERE adc_id = ?"
        affected = self.db.execute_update(query, (adc_id,))
        return affected >= 0  # 可能没有规格，返回True
    
    # ==================== 汇总计算 ====================
    
    def calculate_total_mg(self, adc_id: int) -> float:
        """计算ADC的总毫克数"""
        query = "SELECT SUM(spec_mg * quantity) as total FROM adc_specs WHERE adc_id = ?"
        results = self.db.execute_query(query, (adc_id,))
        if results and results[0]['total']:
            return float(results[0]['total'])
        return 0.0
    
    def calculate_total_vials(self, adc_id: int) -> int:
        """计算ADC的总小管数"""
        query = "SELECT SUM(quantity) as total FROM adc_specs WHERE adc_id = ?"
        results = self.db.execute_query(query, (adc_id,))
        if results and results[0]['total']:
            return int(results[0]['total'])
        return 0

