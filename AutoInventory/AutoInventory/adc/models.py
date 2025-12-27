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
            'owner', 'storage_temp', 'storage_position', 'created_at', 'updated_at', 'specs'
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

