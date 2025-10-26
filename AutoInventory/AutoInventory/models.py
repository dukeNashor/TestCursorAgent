"""
数据模型类
定义物料、订单等业务对象的模型
"""
from dataclasses import dataclass, asdict
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

class OrderStatus(Enum):
    """订单状态枚举"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class Priority(Enum):
    """优先级枚举"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"

class MovementType(Enum):
    """库存变动类型"""
    IN = "in"
    OUT = "out"
    ADJUSTMENT = "adjustment"

@dataclass
class Material:
    """物料模型"""
    id: Optional[int] = None
    name: str = ""
    category: str = ""
    description: str = ""
    quantity: int = 0
    unit: str = ""
    min_stock: int = 0
    location: str = ""
    supplier: str = ""
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    images: List[str] = None  # 图片路径列表
    
    def __post_init__(self):
        if self.images is None:
            self.images = []
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        data = asdict(self)
        # 处理datetime对象
        if data.get('created_at'):
            data['created_at'] = data['created_at'].isoformat()
        if data.get('updated_at'):
            data['updated_at'] = data['updated_at'].isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Material':
        """从字典创建对象"""
        # 处理datetime字符串
        if data.get('created_at'):
            data['created_at'] = datetime.fromisoformat(data['created_at'])
        if data.get('updated_at'):
            data['updated_at'] = datetime.fromisoformat(data['updated_at'])
        
        # 只保留Material类定义的字段，过滤掉其他字段（如version）
        material_fields = {
            'id', 'name', 'category', 'description', 'quantity', 
            'unit', 'min_stock', 'location', 'supplier', 
            'created_at', 'updated_at', 'images'
        }
        filtered_data = {k: v for k, v in data.items() if k in material_fields}
        # 确保images字段存在
        if 'images' not in filtered_data:
            filtered_data['images'] = []
        return cls(**filtered_data)

@dataclass
class Order:
    """订单模型"""
    id: Optional[int] = None
    order_number: str = ""
    requester: str = ""
    department: str = ""
    status: str = OrderStatus.PENDING.value
    priority: str = Priority.NORMAL.value
    notes: str = ""
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    materials: List[Dict[str, Any]] = None  # 订单中的物料列表
    
    def __post_init__(self):
        if self.materials is None:
            self.materials = []
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        data = asdict(self)
        # 处理datetime对象
        for field in ['created_at', 'updated_at', 'completed_at']:
            if data.get(field):
                data[field] = data[field].isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Order':
        """从字典创建对象"""
        # 处理datetime字符串
        for field in ['created_at', 'updated_at', 'completed_at']:
            if data.get(field):
                data[field] = datetime.fromisoformat(data[field])
        
        # 只保留Order类定义的字段，过滤掉其他字段
        order_fields = {
            'id', 'order_number', 'requester', 'department', 'status',
            'priority', 'notes', 'created_at', 'updated_at', 'completed_at',
            'materials'
        }
        filtered_data = {k: v for k, v in data.items() if k in order_fields}
        return cls(**filtered_data)

@dataclass
class OrderMaterial:
    """订单物料关联模型"""
    id: Optional[int] = None
    order_id: int = 0
    material_id: int = 0
    quantity: int = 0
    notes: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'OrderMaterial':
        """从字典创建对象"""
        return cls(**data)

@dataclass
class StockMovement:
    """库存变动记录模型"""
    id: Optional[int] = None
    material_id: int = 0
    movement_type: str = MovementType.ADJUSTMENT.value
    quantity: int = 0
    reference_id: Optional[int] = None
    notes: str = ""
    created_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        data = asdict(self)
        if data.get('created_at'):
            data['created_at'] = data['created_at'].isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'StockMovement':
        """从字典创建对象"""
        if data.get('created_at'):
            data['created_at'] = datetime.fromisoformat(data['created_at'])
        return cls(**data)
