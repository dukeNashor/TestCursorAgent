"""
ADC模块 - 控制器层
实现ADC样品及规格的业务逻辑
"""
from typing import List, Optional, Dict, Any

from .models import ADC, ADCSpec
from .repository import ADCRepository


# 预设规格列表（mg）
PRESET_SPECS = [0.5, 1.0, 2.0, 5.0, 10.0]


class ADCController:
    """ADC控制器"""
    
    def __init__(self, db_manager):
        self.db = db_manager
        self.repository = ADCRepository(db_manager)
        self._adc_cache = {}  # 内存缓存：adc_id -> ADC对象
        self._all_adcs_cache = []  # 所有ADC的缓存列表
        self._cache_initialized = False
    
    def _init_cache(self):
        """初始化缓存"""
        if not self._cache_initialized:
            self._refresh_cache()
            self._cache_initialized = True
    
    def _refresh_cache(self):
        """刷新缓存"""
        # 清空缓存
        self._adc_cache.clear()
        self._all_adcs_cache.clear()
        
        # 从数据库加载所有ADC
        adc_rows = self.repository.get_all_adcs()
        
        for row in adc_rows:
            adc = ADC.from_dict(row)
            # 加载规格列表
            spec_rows = self.repository.get_specs_by_adc_id(adc.id)
            adc.specs = [ADCSpec.from_dict(spec) for spec in spec_rows]
            
            # 存入缓存
            self._adc_cache[adc.id] = adc
            self._all_adcs_cache.append(adc)
    
    # ==================== ADC CRUD ====================
    
    def create_adc(self, adc: ADC) -> int:
        """创建ADC"""
        adc_id = self.repository.create_adc(
            lot_number=adc.lot_number,
            sample_id=adc.sample_id,
            description=adc.description,
            concentration=adc.concentration,
            owner=adc.owner,
            storage_temp=adc.storage_temp,
            storage_position=adc.storage_position
        )
        
        # 添加规格
        if adc.specs:
            for spec in adc.specs:
                if isinstance(spec, ADCSpec):
                    self.repository.add_spec(adc_id, spec.spec_mg, spec.quantity)
                elif isinstance(spec, dict):
                    self.repository.add_spec(adc_id, spec['spec_mg'], spec['quantity'])
        
        # 刷新缓存
        self._refresh_cache()
        
        return adc_id
    
    def get_adc(self, adc_id: int) -> Optional[ADC]:
        """获取ADC（从缓存）"""
        self._init_cache()
        return self._adc_cache.get(adc_id)
    
    def get_adc_by_lot_number(self, lot_number: str) -> Optional[ADC]:
        """根据Lot Number获取ADC"""
        self._init_cache()
        for adc in self._all_adcs_cache:
            if adc.lot_number == lot_number:
                return adc
        return None
    
    def get_all_adcs(self) -> List[ADC]:
        """获取所有ADC（从缓存）"""
        self._init_cache()
        return self._all_adcs_cache.copy()
    
    def search_by_sample_id(self, sample_id: str) -> List[ADC]:
        """根据SampleID搜索ADC（从缓存，模糊匹配）"""
        self._init_cache()
        sample_id_lower = sample_id.lower()
        results = []
        for adc in self._all_adcs_cache:
            if sample_id_lower in adc.sample_id.lower():
                results.append(adc)
        return results
    
    def update_adc(self, adc: ADC) -> tuple:
        """更新ADC，返回(成功状态, 错误信息)"""
        if not adc.id:
            return False, "ADC ID不能为空"
        
        # 检查ADC是否存在
        existing = self.repository.get_adc_by_id(adc.id)
        if not existing:
            return False, "ADC不存在"
        
        # 检查Lot Number是否被其他记录使用
        lot_check = self.repository.get_adc_by_lot_number(adc.lot_number)
        if lot_check and lot_check['id'] != adc.id:
            return False, f"Lot Number '{adc.lot_number}' 已被其他记录使用"
        
        # 更新ADC基本信息
        success = self.repository.update_adc(
            adc_id=adc.id,
            lot_number=adc.lot_number,
            sample_id=adc.sample_id,
            description=adc.description,
            concentration=adc.concentration,
            owner=adc.owner,
            storage_temp=adc.storage_temp,
            storage_position=adc.storage_position
        )
        
        if not success:
            return False, "更新失败"
        
        # 更新规格（先删除旧的，再添加新的）
        self.repository.delete_specs_by_adc_id(adc.id)
        if adc.specs:
            for spec in adc.specs:
                if isinstance(spec, ADCSpec):
                    self.repository.add_spec(adc.id, spec.spec_mg, spec.quantity)
                elif isinstance(spec, dict):
                    self.repository.add_spec(adc.id, spec['spec_mg'], spec['quantity'])
        
        # 刷新缓存
        self._refresh_cache()
        
        return True, "更新成功"
    
    def delete_adc(self, adc_id: int) -> bool:
        """删除ADC"""
        success = self.repository.delete_adc(adc_id)
        if success:
            self._refresh_cache()
        return success
    
    # ==================== 规格管理 ====================
    
    def add_spec(self, adc_id: int, spec_mg: float, quantity: int) -> int:
        """添加规格"""
        spec_id = self.repository.add_spec(adc_id, spec_mg, quantity)
        self._refresh_cache()
        return spec_id
    
    def update_spec(self, spec_id: int, spec_mg: float, quantity: int) -> bool:
        """更新规格"""
        success = self.repository.update_spec(spec_id, spec_mg, quantity)
        if success:
            self._refresh_cache()
        return success
    
    def update_spec_quantity(self, spec_id: int, quantity: int) -> bool:
        """更新规格库存量"""
        success = self.repository.update_spec_quantity(spec_id, quantity)
        if success:
            self._refresh_cache()
        return success
    
    def delete_spec(self, spec_id: int) -> bool:
        """删除规格"""
        success = self.repository.delete_spec(spec_id)
        if success:
            self._refresh_cache()
        return success
    
    # ==================== 汇总计算 ====================
    
    def calculate_total_mg(self, adc_id: int) -> float:
        """计算ADC的总毫克数"""
        return self.repository.calculate_total_mg(adc_id)
    
    def calculate_total_vials(self, adc_id: int) -> int:
        """计算ADC的总小管数"""
        return self.repository.calculate_total_vials(adc_id)
    
    # ==================== 辅助方法 ====================
    
    def get_preset_specs(self) -> List[float]:
        """获取预设规格列表"""
        return PRESET_SPECS.copy()
    
    def refresh(self):
        """手动刷新缓存"""
        self._refresh_cache()

