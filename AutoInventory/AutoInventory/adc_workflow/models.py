"""
ADC实验流程模块 - 数据模型
定义用户、纯化步骤类型、工作流、工作流步骤、实验结果
"""
from dataclasses import dataclass, asdict, field
from typing import List, Optional, Dict, Any
from datetime import datetime


# 角色枚举
ROLE_EXPERIMENTER = "实验员"
ROLE_LEADER = "leader"


@dataclass
class AppUser:
    """应用用户（实验员/leader）"""
    id: Optional[int] = None
    username: str = ""
    role: str = ROLE_EXPERIMENTER
    created_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        if data.get("created_at"):
            data["created_at"] = data["created_at"].isoformat()
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AppUser":
        if data.get("created_at") and isinstance(data["created_at"], str):
            data["created_at"] = datetime.fromisoformat(data["created_at"])
        fields = {"id", "username", "role", "created_at"}
        filtered = {k: v for k, v in data.items() if k in fields}
        return cls(**filtered)

    def is_leader(self) -> bool:
        return self.role == ROLE_LEADER


@dataclass
class PurificationStepType:
    """纯化步骤类型（Zeba/Amicon/G25 等）"""
    id: Optional[int] = None
    name: str = ""
    display_order: int = 0
    is_active: bool = True
    param_schema: str = ""  # JSON
    schema_version: int = 1
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        for key in ("created_at", "updated_at"):
            if data.get(key):
                data[key] = data[key].isoformat()
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PurificationStepType":
        for key in ("created_at", "updated_at"):
            if data.get(key) and isinstance(data[key], str):
                data[key] = datetime.fromisoformat(data[key])
        fields = {
            "id", "name", "display_order", "is_active",
            "param_schema", "schema_version", "created_at", "updated_at",
        }
        filtered = {k: v for k, v in data.items() if k in fields}
        return cls(**filtered)


@dataclass
class ADCWorkflowStep:
    """单次工作流中的纯化步骤实例"""
    id: Optional[int] = None
    workflow_id: int = 0
    step_type_id: int = 0
    step_order: int = 0
    params_json: str = ""  # 该步骤参数 + Estimated recovery 等
    created_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        if data.get("created_at"):
            data["created_at"] = data["created_at"].isoformat()
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ADCWorkflowStep":
        if data.get("created_at") and isinstance(data["created_at"], str):
            data["created_at"] = datetime.fromisoformat(data["created_at"])
        fields = {"id", "workflow_id", "step_type_id", "step_order", "params_json", "created_at"}
        filtered = {k: v for k, v in data.items() if k in fields}
        return cls(**filtered)


@dataclass
class ADCWorkflow:
    """ADC实验流程（单次 Request + 步骤）"""
    id: Optional[int] = None
    request_sn: str = ""
    raw_request_json: str = ""
    purification_flow_string: str = ""
    created_by_user_id: int = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    steps: List[ADCWorkflowStep] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        for key in ("created_at", "updated_at"):
            if data.get(key):
                data[key] = data[key].isoformat()
        if data.get("steps"):
            data["steps"] = [
                s if isinstance(s, dict) else s.to_dict() for s in data["steps"]
            ]
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ADCWorkflow":
        for key in ("created_at", "updated_at"):
            if data.get(key) and isinstance(data[key], str):
                data[key] = datetime.fromisoformat(data[key])
        if data.get("steps"):
            data["steps"] = [
                ADCWorkflowStep.from_dict(s) if isinstance(s, dict) else s
                for s in data["steps"]
            ]
        fields = {
            "id", "request_sn", "raw_request_json", "purification_flow_string",
            "created_by_user_id", "created_at", "updated_at", "steps",
        }
        filtered = {k: v for k, v in data.items() if k in fields}
        if "steps" not in filtered:
            filtered["steps"] = []
        return cls(**filtered)


@dataclass
class ADCExperimentResult:
    """实验结果（单条）"""
    id: Optional[int] = None
    workflow_id: int = 0
    sample_id: str = ""
    lot_no: str = ""
    conc_mg_ml: float = 0.0
    amount_mg: float = 0.0
    yield_pct: float = 0.0
    ms_dar: float = 0.0
    monomer_pct: float = 0.0
    free_drug_pct: float = 0.0
    endotoxin: str = ""
    aliquot: str = ""
    purification_method: str = ""
    created_at: Optional[datetime] = None
    created_by_user_id: int = 0

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        if data.get("created_at"):
            data["created_at"] = data["created_at"].isoformat()
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ADCExperimentResult":
        if data.get("created_at") and isinstance(data["created_at"], str):
            data["created_at"] = datetime.fromisoformat(data["created_at"])
        fields = {
            "id", "workflow_id", "sample_id", "lot_no", "conc_mg_ml", "amount_mg",
            "yield_pct", "ms_dar", "monomer_pct", "free_drug_pct", "endotoxin",
            "aliquot", "purification_method", "created_at", "created_by_user_id",
        }
        filtered = {k: v for k, v in data.items() if k in fields}
        return cls(**filtered)
