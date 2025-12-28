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
            antibody TEXT DEFAULT '',
            linker_payload TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 为现有表添加新列（如果不存在）
    try:
        cursor.execute('ALTER TABLE adc ADD COLUMN antibody TEXT DEFAULT ""')
    except:
        pass  # 列已存在
    try:
        cursor.execute('ALTER TABLE adc ADD COLUMN linker_payload TEXT DEFAULT ""')
    except:
        pass  # 列已存在
    
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
    
    # ==================== 出入库相关表 ====================
    
    # 创建出库记录表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS adc_outbound (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lot_number TEXT NOT NULL,
            requester TEXT NOT NULL,
            operator TEXT NOT NULL,
            shipping_address TEXT,
            shipping_date TIMESTAMP,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 创建出库明细表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS adc_outbound_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            outbound_id INTEGER NOT NULL,
            spec_mg REAL NOT NULL,
            quantity INTEGER NOT NULL,
            FOREIGN KEY (outbound_id) REFERENCES adc_outbound (id) ON DELETE CASCADE
        )
    ''')
    
    # 创建入库记录表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS adc_inbound (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lot_number TEXT NOT NULL,
            operator TEXT NOT NULL,
            owner TEXT,
            storage_position TEXT,
            storage_date TIMESTAMP,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 创建入库明细表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS adc_inbound_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            inbound_id INTEGER NOT NULL,
            spec_mg REAL NOT NULL,
            quantity INTEGER NOT NULL,
            FOREIGN KEY (inbound_id) REFERENCES adc_inbound (id) ON DELETE CASCADE
        )
    ''')
    
    # 为出入库记录的lot_number创建索引
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_adc_outbound_lot ON adc_outbound (lot_number)
    ''')
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_adc_inbound_lot ON adc_inbound (lot_number)
    ''')


class ADCRepository:
    """ADC数据仓库"""
    
    def __init__(self, db_manager):
        self.db = db_manager
    
    # ==================== ADC CRUD ====================
    
    def create_adc(self, lot_number: str, sample_id: str, description: str = "",
                   concentration: float = 0.0, owner: str = "", 
                   storage_temp: str = "", storage_position: str = "",
                   antibody: str = "", linker_payload: str = "") -> int:
        """创建ADC记录"""
        query = '''
            INSERT INTO adc (lot_number, sample_id, description, concentration, 
                           owner, storage_temp, storage_position, antibody, linker_payload)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        '''
        return self.db.execute_insert(query, (
            lot_number, sample_id, description, concentration,
            owner, storage_temp, storage_position, antibody, linker_payload
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
                   storage_temp: str, storage_position: str,
                   antibody: str = "", linker_payload: str = "") -> bool:
        """更新ADC记录"""
        query = '''
            UPDATE adc 
            SET lot_number=?, sample_id=?, description=?, concentration=?,
                owner=?, storage_temp=?, storage_position=?, antibody=?, linker_payload=?,
                updated_at=CURRENT_TIMESTAMP
            WHERE id=?
        '''
        affected = self.db.execute_update(query, (
            lot_number, sample_id, description, concentration,
            owner, storage_temp, storage_position, antibody, linker_payload, adc_id
        ))
        return affected > 0
    
    def search_by_antibody(self, antibody: str) -> List[Dict[str, Any]]:
        """根据Antibody搜索ADC"""
        query = "SELECT * FROM adc WHERE antibody LIKE ? ORDER BY created_at DESC"
        return self.db.execute_query(query, (f"%{antibody}%",))
    
    def search_by_linker_payload(self, linker_payload: str) -> List[Dict[str, Any]]:
        """根据Linker-payload搜索ADC"""
        query = "SELECT * FROM adc WHERE linker_payload LIKE ? ORDER BY created_at DESC"
        return self.db.execute_query(query, (f"%{linker_payload}%",))
    
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
    
    # ==================== 出库记录 CRUD ====================
    
    def create_outbound(self, lot_number: str, requester: str, operator: str,
                       shipping_address: str, shipping_date: str, notes: str = "") -> int:
        """创建出库记录"""
        query = '''
            INSERT INTO adc_outbound (lot_number, requester, operator, shipping_address, shipping_date, notes)
            VALUES (?, ?, ?, ?, ?, ?)
        '''
        return self.db.execute_insert(query, (
            lot_number, requester, operator, shipping_address, shipping_date, notes
        ))
    
    def add_outbound_item(self, outbound_id: int, spec_mg: float, quantity: int) -> int:
        """添加出库明细"""
        query = '''
            INSERT INTO adc_outbound_items (outbound_id, spec_mg, quantity)
            VALUES (?, ?, ?)
        '''
        return self.db.execute_insert(query, (outbound_id, spec_mg, quantity))
    
    def get_outbound_by_id(self, outbound_id: int) -> Optional[Dict[str, Any]]:
        """根据ID获取出库记录"""
        query = "SELECT * FROM adc_outbound WHERE id = ?"
        results = self.db.execute_query(query, (outbound_id,))
        return results[0] if results else None
    
    def get_outbound_items(self, outbound_id: int) -> List[Dict[str, Any]]:
        """获取出库明细"""
        query = "SELECT * FROM adc_outbound_items WHERE outbound_id = ? ORDER BY spec_mg"
        return self.db.execute_query(query, (outbound_id,))
    
    def get_all_outbounds(self) -> List[Dict[str, Any]]:
        """获取所有出库记录"""
        query = "SELECT * FROM adc_outbound ORDER BY created_at DESC"
        return self.db.execute_query(query)
    
    def search_outbounds_by_lot_number(self, lot_number: str) -> List[Dict[str, Any]]:
        """根据LotNumber搜索出库记录"""
        query = "SELECT * FROM adc_outbound WHERE lot_number LIKE ? ORDER BY created_at DESC"
        return self.db.execute_query(query, (f"%{lot_number}%",))
    
    def delete_outbound(self, outbound_id: int) -> bool:
        """删除出库记录"""
        query = "DELETE FROM adc_outbound WHERE id = ?"
        affected = self.db.execute_update(query, (outbound_id,))
        return affected > 0
    
    # ==================== 入库记录 CRUD ====================
    
    def create_inbound(self, lot_number: str, operator: str, owner: str,
                      storage_position: str, storage_date: str, notes: str = "") -> int:
        """创建入库记录"""
        query = '''
            INSERT INTO adc_inbound (lot_number, operator, owner, storage_position, storage_date, notes)
            VALUES (?, ?, ?, ?, ?, ?)
        '''
        return self.db.execute_insert(query, (
            lot_number, operator, owner, storage_position, storage_date, notes
        ))
    
    def add_inbound_item(self, inbound_id: int, spec_mg: float, quantity: int) -> int:
        """添加入库明细"""
        query = '''
            INSERT INTO adc_inbound_items (inbound_id, spec_mg, quantity)
            VALUES (?, ?, ?)
        '''
        return self.db.execute_insert(query, (inbound_id, spec_mg, quantity))
    
    def get_inbound_by_id(self, inbound_id: int) -> Optional[Dict[str, Any]]:
        """根据ID获取入库记录"""
        query = "SELECT * FROM adc_inbound WHERE id = ?"
        results = self.db.execute_query(query, (inbound_id,))
        return results[0] if results else None
    
    def get_inbound_items(self, inbound_id: int) -> List[Dict[str, Any]]:
        """获取入库明细"""
        query = "SELECT * FROM adc_inbound_items WHERE inbound_id = ? ORDER BY spec_mg"
        return self.db.execute_query(query, (inbound_id,))
    
    def get_all_inbounds(self) -> List[Dict[str, Any]]:
        """获取所有入库记录"""
        query = "SELECT * FROM adc_inbound ORDER BY created_at DESC"
        return self.db.execute_query(query)
    
    def search_inbounds_by_lot_number(self, lot_number: str) -> List[Dict[str, Any]]:
        """根据LotNumber搜索入库记录"""
        query = "SELECT * FROM adc_inbound WHERE lot_number LIKE ? ORDER BY created_at DESC"
        return self.db.execute_query(query, (f"%{lot_number}%",))
    
    def delete_inbound(self, inbound_id: int) -> bool:
        """删除入库记录"""
        query = "DELETE FROM adc_inbound WHERE id = ?"
        affected = self.db.execute_update(query, (inbound_id,))
        return affected > 0
    
    # ==================== 库存更新 ====================
    
    def get_spec_by_adc_and_mg(self, adc_id: int, spec_mg: float) -> Optional[Dict[str, Any]]:
        """根据ADC ID和规格获取规格记录"""
        query = "SELECT * FROM adc_specs WHERE adc_id = ? AND spec_mg = ?"
        results = self.db.execute_query(query, (adc_id, spec_mg))
        return results[0] if results else None
    
    def increase_spec_quantity(self, spec_id: int, delta: int) -> bool:
        """增加规格库存量"""
        query = "UPDATE adc_specs SET quantity = quantity + ? WHERE id = ?"
        affected = self.db.execute_update(query, (delta, spec_id))
        return affected > 0
    
    def decrease_spec_quantity(self, spec_id: int, delta: int) -> bool:
        """减少规格库存量"""
        query = "UPDATE adc_specs SET quantity = quantity - ? WHERE id = ? AND quantity >= ?"
        affected = self.db.execute_update(query, (delta, spec_id, delta))
        return affected > 0

