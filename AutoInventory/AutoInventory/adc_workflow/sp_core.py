"""
Setup Param(SP) 核心抽象与通用工具。

用于 DAR8/DAR4/Deblocking/Thiomab 等不同 SP 类型共享：
- 字段元数据描述
- 单次计算结果结构
- 通用数值/字符串处理工具
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class SetupParamFieldMeta:
    """
    单个 SP 字段的元数据定义。

    - key: 内部唯一键名，用于代码与依赖关系。
    - display_name: UI 中展示的中文/英文名称。
    - unit: 单位字符串，如 'mL'、'mg/mL'、'°C'、'h'、'%' 等。
    - data_type: 字段类型描述，如 'float'、'string'、'enum'、'optional_float'。
    - source: 数据来源：
        - 'request'     : 来自 Request 导入
        - 'user_input'  : 实验员在 UI 中手动输入
        - 'derived'     : 由计算得到的输出
        - 'fixed'       : 固定常数
    - group: 逻辑分组，用于 UI 排序，如：
        - 'input_request'
        - 'input_user'
        - 'output_reduction'
        - 'output_conjugation'
        - 'meta'
    - is_important: 实验员需要重点关注的字段，UI 中会有更强视觉效果。
    - description: 文字描述，解释该字段含义与使用注意事项。
    - depends_on: 计算该字段时依赖的其他字段 key 列表。
    - formula_text: 人类可读的公式/计算逻辑描述。
    """

    key: str
    display_name: str
    unit: str = ""
    data_type: str = "string"
    source: str = "derived"
    group: str = "meta"
    is_important: bool = False
    description: str = ""
    depends_on: List[str] = field(default_factory=list)
    formula_text: str = ""


@dataclass
class SetupParamValue:
    """某个字段一次计算得到的值及其元数据引用。"""

    meta: SetupParamFieldMeta
    value: Any


@dataclass
class SetupParamCalculationResult:
    """
    一次 SP 计算的完整结果：
    - fields: key -> SetupParamValue
    """

    fields: Dict[str, SetupParamValue] = field(default_factory=dict)

    def set_value(self, meta: SetupParamFieldMeta, value: Any) -> None:
        self.fields[meta.key] = SetupParamValue(meta=meta, value=value)

    def get_value(self, key: str) -> Any:
        v = self.fields.get(key)
        return v.value if v is not None else None

    def get_meta(self, key: str) -> Optional[SetupParamFieldMeta]:
        v = self.fields.get(key)
        return v.meta if v is not None else None

    def items(self):
        """返回 (key, SetupParamValue) 迭代器，便于遍历。"""
        return self.fields.items()


# ---------- 通用工具函数 ----------


def parse_leading_number(text: Any) -> Optional[float]:
    """
    从字符串前缀解析出浮点数，例如：
    - '10 mM'       -> 10.0
    - ' 8.5mg/mL'   -> 8.5
    - 'N/A' / None  -> None
    """
    if text is None:
        return None
    if isinstance(text, (int, float)):
        try:
            return float(text)
        except (TypeError, ValueError):
            return None
    s = str(text).strip()
    if not s:
        return None
    num_chars = []
    dot_seen = False
    sign_seen = False
    for ch in s:
        if ch in "+-" and not sign_seen and not num_chars:
            sign_seen = True
            num_chars.append(ch)
            continue
        if ch.isdigit():
            num_chars.append(ch)
            continue
        if ch == "." and not dot_seen:
            dot_seen = True
            num_chars.append(ch)
            continue
        # 遇到第一个非数字/小数点/符号字符即停止
        break
    if not num_chars:
        return None
    try:
        return float("".join(num_chars))
    except ValueError:
        return None


def safe_div(numerator: Optional[float], denominator: Optional[float]) -> Optional[float]:
    """安全除法，任一为 None 或分母为 0 时返回 None。"""
    if numerator is None or denominator is None:
        return None
    try:
        if denominator == 0:
            return None
        return float(numerator) / float(denominator)
    except Exception:
        return None


def format_number(value: Any, digits: int = 3) -> str:
    """
    将数值格式化为字符串：
    - None -> 'N/A'
    - int/float -> 保留 digits 位小数（去掉尾随 0 与小数点）
    - 其他类型 -> str(value)
    """
    if value is None:
        return "N/A"
    if isinstance(value, (int, float)):
        fmt = "{:." + str(digits) + "f}"
        s = fmt.format(float(value))
        # 去掉尾随 0 与小数点
        if "." in s:
            s = s.rstrip("0").rstrip(".")
        return s
    return str(value)


def ensure_float(value: Any) -> Optional[float]:
    """尝试将任意类型转换为 float，失败时返回 None。"""
    if value is None:
        return None
    if isinstance(value, (int, float)):
        try:
            return float(value)
        except (TypeError, ValueError):
            return None
    try:
        return float(str(value).strip())
    except (TypeError, ValueError):
        return None

