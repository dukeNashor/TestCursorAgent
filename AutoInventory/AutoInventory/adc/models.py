"""
ADC模块 - 数据模型类
定义ADC样品及规格的数据模型
"""
from dataclasses import dataclass, asdict, field
from typing import List, Optional, Dict, Any
from datetime import datetime


@dataclass
class ADCSpec:
    """ADC规格库存模型"""
    id: Optional[int] = None
    adc_id: int = 0
    spec_mg: float = 0.0           # 规格(mg)
    quantity: int = 0              # 库存量(小管数)
    created_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        data = asdict(self)
        if data.get('created_at'):
            data['created_at'] = data['created_at'].isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ADCSpec':
        """从字典创建对象"""
        if data.get('created_at') and isinstance(data['created_at'], str):
            data['created_at'] = datetime.fromisoformat(data['created_at'])
        
        spec_fields = {'id', 'adc_id', 'spec_mg', 'quantity', 'created_at'}
        filtered_data = {k: v for k, v in data.items() if k in spec_fields}
        return cls(**filtered_data)
    
    def get_total_mg(self) -> float:
        """计算该规格的总毫克数"""
        return self.spec_mg * self.quantity


@dataclass
class ADC:
    """ADC样品模型"""
    id: Optional[int] = None
    lot_number: str = ""           # Lot Number（唯一标识）
    sample_id: str = ""            # SampleID（可重复，用于筛选）
    description: str = ""          # 样品描述
    concentration: float = 0.0     # Concentration (mg/mL)
    owner: str = ""                # Owner
    storage_temp: str = ""         # Storage Temp
    storage_position: str = ""     # Storage Position
    antibody: str = ""             # Antibody
    linker_payload: str = ""       # Linker-payload
    created_at: Optional[datetime] = None   # 入库时间
    updated_at: Optional[datetime] = None   # 更新时间
    specs: List[ADCSpec] = field(default_factory=list)  # 规格列表
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        data = asdict(self)
        # 处理datetime对象
        if data.get('created_at'):
            data['created_at'] = data['created_at'].isoformat()
        if data.get('updated_at'):
            data['updated_at'] = data['updated_at'].isoformat()
        # 处理specs列表
        if data.get('specs'):
            data['specs'] = [spec if isinstance(spec, dict) else spec for spec in data['specs']]
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ADC':
        """从字典创建对象"""
        # 处理datetime字符串
        if data.get('created_at') and isinstance(data['created_at'], str):
            data['created_at'] = datetime.fromisoformat(data['created_at'])
        if data.get('updated_at') and isinstance(data['updated_at'], str):
            data['updated_at'] = datetime.fromisoformat(data['updated_at'])
        
        # 只保留ADC类定义的字段
        adc_fields = {
            'id', 'lot_number', 'sample_id', 'description', 'concentration',
            'owner', 'storage_temp', 'storage_position', 'antibody', 'linker_payload',
            'created_at', 'updated_at', 'specs'
        }
        filtered_data = {k: v for k, v in data.items() if k in adc_fields}
        
        # 确保specs字段存在
        if 'specs' not in filtered_data:
            filtered_data['specs'] = []
        
        return cls(**filtered_data)
    
    def get_total_mg(self) -> float:
        """计算所有规格的总毫克数"""
        total = 0.0
        for spec in self.specs:
            if isinstance(spec, ADCSpec):
                total += spec.get_total_mg()
            elif isinstance(spec, dict):
                total += spec.get('spec_mg', 0) * spec.get('quantity', 0)
        return total
    
    def get_total_vials(self) -> int:
        """计算所有规格的总小管数"""
        total = 0
        for spec in self.specs:
            if isinstance(spec, ADCSpec):
                total += spec.quantity
            elif isinstance(spec, dict):
                total += spec.get('quantity', 0)
        return total


# ==================== 出入库相关模型 ====================

@dataclass
class ADCMovementItem:
    """出入库明细项（规格+数量）"""
    id: Optional[int] = None
    movement_id: int = 0          # 关联的出库/入库记录ID
    spec_mg: float = 0.0          # 规格(mg)
    quantity: int = 0             # 数量(小管数)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ADCMovementItem':
        """从字典创建对象"""
        item_fields = {'id', 'movement_id', 'spec_mg', 'quantity'}
        filtered_data = {k: v for k, v in data.items() if k in item_fields}
        return cls(**filtered_data)
    
    def get_total_mg(self) -> float:
        """计算该明细的总毫克数"""
        return self.spec_mg * self.quantity


@dataclass
class ADCOutbound:
    """ADC出库记录"""
    id: Optional[int] = None
    lot_number: str = ""          # 关联的Lot Number
    requester: str = ""           # 需求人
    operator: str = ""            # 出库人
    shipping_address: str = ""    # 寄送地址
    shipping_date: Optional[datetime] = None  # 寄送日期
    notes: str = ""               # 备注
    created_at: Optional[datetime] = None     # 记录创建时间
    items: List[ADCMovementItem] = field(default_factory=list)  # 出库明细
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        data = asdict(self)
        if data.get('shipping_date'):
            data['shipping_date'] = data['shipping_date'].isoformat() if isinstance(data['shipping_date'], datetime) else data['shipping_date']
        if data.get('created_at'):
            data['created_at'] = data['created_at'].isoformat() if isinstance(data['created_at'], datetime) else data['created_at']
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ADCOutbound':
        """从字典创建对象"""
        if data.get('shipping_date') and isinstance(data['shipping_date'], str):
            try:
                data['shipping_date'] = datetime.fromisoformat(data['shipping_date'])
            except ValueError:
                data['shipping_date'] = datetime.strptime(data['shipping_date'], '%Y-%m-%d')
        if data.get('created_at') and isinstance(data['created_at'], str):
            data['created_at'] = datetime.fromisoformat(data['created_at'])
        
        outbound_fields = {
            'id', 'lot_number', 'requester', 'operator', 'shipping_address',
            'shipping_date', 'notes', 'created_at', 'items'
        }
        filtered_data = {k: v for k, v in data.items() if k in outbound_fields}
        if 'items' not in filtered_data:
            filtered_data['items'] = []
        return cls(**filtered_data)
    
    def get_total_mg(self) -> float:
        """计算出库总毫克数"""
        total = 0.0
        for item in self.items:
            if isinstance(item, ADCMovementItem):
                total += item.get_total_mg()
            elif isinstance(item, dict):
                total += item.get('spec_mg', 0) * item.get('quantity', 0)
        return total
    
    def get_total_vials(self) -> int:
        """计算出库总小管数"""
        total = 0
        for item in self.items:
            if isinstance(item, ADCMovementItem):
                total += item.quantity
            elif isinstance(item, dict):
                total += item.get('quantity', 0)
        return total


@dataclass
class ADCInbound:
    """ADC入库记录"""
    id: Optional[int] = None
    lot_number: str = ""          # 关联的Lot Number
    operator: str = ""            # 入库人
    owner: str = ""               # Owner（默认=入库人）
    storage_position: str = ""    # 存放地址
    storage_date: Optional[datetime] = None   # 存放日期
    notes: str = ""               # 备注
    created_at: Optional[datetime] = None     # 记录创建时间
    items: List[ADCMovementItem] = field(default_factory=list)  # 入库明细
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        data = asdict(self)
        if data.get('storage_date'):
            data['storage_date'] = data['storage_date'].isoformat() if isinstance(data['storage_date'], datetime) else data['storage_date']
        if data.get('created_at'):
            data['created_at'] = data['created_at'].isoformat() if isinstance(data['created_at'], datetime) else data['created_at']
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ADCInbound':
        """从字典创建对象"""
        if data.get('storage_date') and isinstance(data['storage_date'], str):
            try:
                data['storage_date'] = datetime.fromisoformat(data['storage_date'])
            except ValueError:
                data['storage_date'] = datetime.strptime(data['storage_date'], '%Y-%m-%d')
        if data.get('created_at') and isinstance(data['created_at'], str):
            data['created_at'] = datetime.fromisoformat(data['created_at'])
        
        inbound_fields = {
            'id', 'lot_number', 'operator', 'owner', 'storage_position',
            'storage_date', 'notes', 'created_at', 'items'
        }
        filtered_data = {k: v for k, v in data.items() if k in inbound_fields}
        if 'items' not in filtered_data:
            filtered_data['items'] = []
        return cls(**filtered_data)
    
    def get_total_mg(self) -> float:
        """计算入库总毫克数"""
        total = 0.0
        for item in self.items:
            if isinstance(item, ADCMovementItem):
                total += item.get_total_mg()
            elif isinstance(item, dict):
                total += item.get('spec_mg', 0) * item.get('quantity', 0)
        return total
    
    def get_total_vials(self) -> int:
        """计算入库总小管数"""
        total = 0
        for item in self.items:
            if isinstance(item, ADCMovementItem):
                total += item.quantity
            elif isinstance(item, dict):
                total += item.get('quantity', 0)
        return total

