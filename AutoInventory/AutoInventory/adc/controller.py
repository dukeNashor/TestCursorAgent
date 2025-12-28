"""
ADC模块 - 控制器层
实现ADC样品及规格的业务逻辑
"""
from typing import List, Optional, Dict, Any
from datetime import datetime

from .models import ADC, ADCSpec, ADCOutbound, ADCInbound, ADCMovementItem
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
            storage_position=adc.storage_position,
            antibody=adc.antibody,
            linker_payload=adc.linker_payload
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
    
    def search_by_antibody(self, antibody: str) -> List[ADC]:
        """根据Antibody搜索ADC（从缓存，模糊匹配）"""
        self._init_cache()
        antibody_lower = antibody.lower()
        results = []
        for adc in self._all_adcs_cache:
            if antibody_lower in adc.antibody.lower():
                results.append(adc)
        return results
    
    def search_by_linker_payload(self, linker_payload: str) -> List[ADC]:
        """根据Linker-payload搜索ADC（从缓存，模糊匹配）"""
        self._init_cache()
        linker_payload_lower = linker_payload.lower()
        results = []
        for adc in self._all_adcs_cache:
            if linker_payload_lower in adc.linker_payload.lower():
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
            storage_position=adc.storage_position,
            antibody=adc.antibody,
            linker_payload=adc.linker_payload
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
    
    # ==================== 出库管理 ====================
    
    def create_outbound(self, outbound: ADCOutbound) -> tuple:
        """
        创建出库记录并减少库存
        返回 (成功状态, 消息或出库ID)
        """
        # 检查ADC是否存在
        adc = self.get_adc_by_lot_number(outbound.lot_number)
        if not adc:
            return False, f"Lot Number '{outbound.lot_number}' 不存在"
        
        # 检查库存是否充足
        for item in outbound.items:
            spec_mg = item.spec_mg if isinstance(item, ADCMovementItem) else item['spec_mg']
            quantity = item.quantity if isinstance(item, ADCMovementItem) else item['quantity']
            
            # 查找对应规格
            spec_found = None
            for spec in adc.specs:
                if isinstance(spec, ADCSpec) and abs(spec.spec_mg - spec_mg) < 0.001:
                    spec_found = spec
                    break
                elif isinstance(spec, dict) and abs(spec.get('spec_mg', 0) - spec_mg) < 0.001:
                    spec_found = spec
                    break
            
            if not spec_found:
                return False, f"规格 {spec_mg}mg 不存在"
            
            current_qty = spec_found.quantity if isinstance(spec_found, ADCSpec) else spec_found.get('quantity', 0)
            if current_qty < quantity:
                return False, f"规格 {spec_mg}mg 库存不足，当前库存 {current_qty}，需要 {quantity}"
        
        # 创建出库记录（使用当前时间作为精确时间戳）
        shipping_date_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
        
        outbound_id = self.repository.create_outbound(
            lot_number=outbound.lot_number,
            requester=outbound.requester,
            operator=outbound.operator,
            shipping_address=outbound.shipping_address,
            shipping_date=shipping_date_str,
            notes=outbound.notes
        )
        
        # 添加出库明细并减少库存
        for item in outbound.items:
            spec_mg = item.spec_mg if isinstance(item, ADCMovementItem) else item['spec_mg']
            quantity = item.quantity if isinstance(item, ADCMovementItem) else item['quantity']
            
            # 添加明细记录
            self.repository.add_outbound_item(outbound_id, spec_mg, quantity)
            
            # 减少库存
            spec_record = self.repository.get_spec_by_adc_and_mg(adc.id, spec_mg)
            if spec_record:
                self.repository.decrease_spec_quantity(spec_record['id'], quantity)
        
        # 刷新缓存
        self._refresh_cache()
        
        return True, outbound_id
    
    def get_all_outbounds(self) -> List[ADCOutbound]:
        """获取所有出库记录"""
        outbound_rows = self.repository.get_all_outbounds()
        outbounds = []
        for row in outbound_rows:
            outbound = ADCOutbound.from_dict(row)
            # 加载明细
            item_rows = self.repository.get_outbound_items(outbound.id)
            outbound.items = [ADCMovementItem.from_dict(item) for item in item_rows]
            outbounds.append(outbound)
        return outbounds
    
    def search_outbounds_by_lot_number(self, lot_number: str) -> List[ADCOutbound]:
        """根据LotNumber搜索出库记录"""
        outbound_rows = self.repository.search_outbounds_by_lot_number(lot_number)
        outbounds = []
        for row in outbound_rows:
            outbound = ADCOutbound.from_dict(row)
            item_rows = self.repository.get_outbound_items(outbound.id)
            outbound.items = [ADCMovementItem.from_dict(item) for item in item_rows]
            outbounds.append(outbound)
        return outbounds
    
    # ==================== 入库管理 ====================
    
    def create_inbound(self, inbound: ADCInbound) -> tuple:
        """
        创建入库记录并增加库存
        返回 (成功状态, 消息或入库ID)
        """
        # 检查ADC是否存在
        adc = self.get_adc_by_lot_number(inbound.lot_number)
        if not adc:
            return False, f"Lot Number '{inbound.lot_number}' 不存在"
        
        # 创建入库记录（使用当前时间作为精确时间戳）
        storage_date_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
        
        inbound_id = self.repository.create_inbound(
            lot_number=inbound.lot_number,
            operator=inbound.operator,
            owner=inbound.owner,
            storage_position=inbound.storage_position,
            storage_date=storage_date_str,
            notes=inbound.notes
        )
        
        # 添加入库明细并增加库存
        for item in inbound.items:
            spec_mg = item.spec_mg if isinstance(item, ADCMovementItem) else item['spec_mg']
            quantity = item.quantity if isinstance(item, ADCMovementItem) else item['quantity']
            
            # 添加明细记录
            self.repository.add_inbound_item(inbound_id, spec_mg, quantity)
            
            # 查找规格，如果不存在则新建
            spec_record = self.repository.get_spec_by_adc_and_mg(adc.id, spec_mg)
            if spec_record:
                # 增加库存
                self.repository.increase_spec_quantity(spec_record['id'], quantity)
            else:
                # 新建规格
                self.repository.add_spec(adc.id, spec_mg, quantity)
        
        # 刷新缓存
        self._refresh_cache()
        
        return True, inbound_id
    
    def get_all_inbounds(self) -> List[ADCInbound]:
        """获取所有入库记录"""
        inbound_rows = self.repository.get_all_inbounds()
        inbounds = []
        for row in inbound_rows:
            inbound = ADCInbound.from_dict(row)
            # 加载明细
            item_rows = self.repository.get_inbound_items(inbound.id)
            inbound.items = [ADCMovementItem.from_dict(item) for item in item_rows]
            inbounds.append(inbound)
        return inbounds
    
    def search_inbounds_by_lot_number(self, lot_number: str) -> List[ADCInbound]:
        """根据LotNumber搜索入库记录"""
        inbound_rows = self.repository.search_inbounds_by_lot_number(lot_number)
        inbounds = []
        for row in inbound_rows:
            inbound = ADCInbound.from_dict(row)
            item_rows = self.repository.get_inbound_items(inbound.id)
            inbound.items = [ADCMovementItem.from_dict(item) for item in item_rows]
            inbounds.append(inbound)
        return inbounds
    
    # ==================== 混合查询 ====================
    
    def get_all_movements(self) -> List[Dict]:
        """获取所有出入库记录（混合列表，按时间倒序）"""
        movements = []
        
        # 获取所有出库记录
        for outbound in self.get_all_outbounds():
            movements.append({
                'type': 'outbound',
                'record': outbound,
                'lot_number': outbound.lot_number,
                'operator': outbound.operator,
                'date': outbound.shipping_date,
                'created_at': outbound.created_at,
                'items': outbound.items
            })
        
        # 获取所有入库记录
        for inbound in self.get_all_inbounds():
            movements.append({
                'type': 'inbound',
                'record': inbound,
                'lot_number': inbound.lot_number,
                'operator': inbound.operator,
                'date': inbound.storage_date,
                'created_at': inbound.created_at,
                'items': inbound.items
            })
        
        # 按创建时间倒序排序
        movements.sort(key=lambda x: x['created_at'] or '', reverse=True)
        
        return movements
    
    def search_movements_by_lot_number(self, lot_number: str) -> List[Dict]:
        """根据LotNumber搜索出入库记录"""
        movements = []
        
        for outbound in self.search_outbounds_by_lot_number(lot_number):
            movements.append({
                'type': 'outbound',
                'record': outbound,
                'lot_number': outbound.lot_number,
                'operator': outbound.operator,
                'date': outbound.shipping_date,
                'created_at': outbound.created_at,
                'items': outbound.items
            })
        
        for inbound in self.search_inbounds_by_lot_number(lot_number):
            movements.append({
                'type': 'inbound',
                'record': inbound,
                'lot_number': inbound.lot_number,
                'operator': inbound.operator,
                'date': inbound.storage_date,
                'created_at': inbound.created_at,
                'items': inbound.items
            })
        
        movements.sort(key=lambda x: x['created_at'] or '', reverse=True)
        
        return movements

