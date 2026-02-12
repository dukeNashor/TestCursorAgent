"""
偶联任务 Request 的规范 schema
与 data/task_template.xlsx 对应，用于展示顺序与类型。
"""
import json
from typing import List, Dict, Any, Optional

# 类型常量
TYPE_STRING = "string"
TYPE_NUMBER = "number"
TYPE_OPTIONAL_STRING = "string | null"
TYPE_BOOL = "bool"
TYPE_NUMBER_OPTIONAL = "number | null"
# ADC Target Quality: list of objects with members "检项", "特殊要求"
TYPE_LIST_OBJECTS = "list of objects"

# 分组
SECTION_COMMON = "通用/任务标识"
SECTION_MAB = "mAb information"
SECTION_LP = "LP information"
SECTION_CONJUGATION = "Conjugation/纯化与分装"

# 字段定义: (key, type, section, optional)
# 键名与 task_template.xlsx 中一致
REQUEST_FIELDS: List[Dict[str, Any]] = [
    {"key": "偶联scientist", "type": TYPE_STRING, "section": SECTION_COMMON, "optional": False},
    {"key": "WBP Code", "type": TYPE_STRING, "section": SECTION_COMMON, "optional": False},
    {"key": "Reaction Scale (mg)", "type": TYPE_NUMBER, "section": SECTION_COMMON, "optional": False},
    {"key": "Product ID", "type": TYPE_STRING, "section": SECTION_COMMON, "optional": False},
    {"key": "Batch#", "type": TYPE_OPTIONAL_STRING, "section": SECTION_COMMON, "optional": True},
    {"key": "Protein ID", "type": TYPE_STRING, "section": SECTION_MAB, "optional": False},
    {"key": "Protein batch#", "type": TYPE_STRING, "section": SECTION_MAB, "optional": False},
    {"key": "Protein isotype", "type": TYPE_OPTIONAL_STRING, "section": SECTION_MAB, "optional": True},
    {"key": "New Carrier", "type": TYPE_BOOL, "section": SECTION_MAB, "optional": True},
    {"key": "MW of antibody (Da)", "type": TYPE_NUMBER, "section": SECTION_MAB, "optional": False},
    {"key": "MW of LC (Da)", "type": TYPE_NUMBER, "section": SECTION_MAB, "optional": True},
    {"key": "MW of HC (Da)", "type": TYPE_NUMBER, "section": SECTION_MAB, "optional": True},
    {"key": "Ab extinction coeff", "type": TYPE_NUMBER, "section": SECTION_MAB, "optional": False},
    {"key": "Calculated PI value", "type": TYPE_NUMBER, "section": SECTION_MAB, "optional": False},
    {"key": "Buffer of Antibody", "type": TYPE_STRING, "section": SECTION_MAB, "optional": False},
    {"key": "Antibody concention (mg/mL)", "type": TYPE_NUMBER, "section": SECTION_MAB, "optional": False},
    {"key": "Linker Payload ID", "type": TYPE_STRING, "section": SECTION_LP, "optional": False},
    {"key": "LP Batch#", "type": TYPE_STRING, "section": SECTION_LP, "optional": True},
    {"key": "NEW LP", "type": TYPE_BOOL, "section": SECTION_LP, "optional": True},
    {"key": "Payload Type", "type": TYPE_OPTIONAL_STRING, "section": SECTION_LP, "optional": True},
    {"key": "LP浓度", "type": TYPE_STRING, "section": SECTION_LP, "optional": False},
    {"key": "MW of LP (Da)", "type": TYPE_NUMBER, "section": SECTION_LP, "optional": False},
    {"key": "Leaving group (Da)", "type": TYPE_NUMBER_OPTIONAL, "section": SECTION_LP, "optional": True},
    {"key": "Dissolved in", "type": TYPE_STRING, "section": SECTION_LP, "optional": False},
    {"key": "是否预约标曲", "type": TYPE_BOOL, "section": SECTION_LP, "optional": True},
    {"key": "Connector", "type": TYPE_STRING, "section": SECTION_LP, "optional": False},
    {"key": "Conjugation buffer", "type": TYPE_STRING, "section": SECTION_CONJUGATION, "optional": True},
    {"key": "Purification method", "type": TYPE_STRING, "section": SECTION_CONJUGATION, "optional": False},
    {"key": "Aliqout information", "type": TYPE_STRING, "section": SECTION_CONJUGATION, "optional": False},
    {"key": "Comments", "type": TYPE_OPTIONAL_STRING, "section": SECTION_CONJUGATION, "optional": True},
    {"key": "ID", "type": TYPE_NUMBER, "section": SECTION_CONJUGATION, "optional": True},
    {"key": "ADC Target Quality", "type": TYPE_STRING, "section": SECTION_CONJUGATION, "optional": False},
]

# ADC Target Quality 列表中每个 object 的成员
ADC_TARGET_QUALITY_ITEM_KEYS = ("检项", "特殊要求")

def get_key_to_optional() -> Dict[str, bool]:
    """返回 规范键名 -> optional 的映射。"""
    return {f["key"]: f.get("optional", False) for f in REQUEST_FIELDS}


def _coerce_bool(value: Any) -> bool:
    """将单元格值转为 bool。"""
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    s = str(value).strip().upper()
    if s in ("1", "Y", "YES", "TRUE", "是"):
        return True
    if s in ("0", "N", "NO", "FALSE", "否", ""):
        return False
    return False


def _coerce_number(value: Any) -> Optional[float]:
    """将单元格值转为 number（int/float），无法解析时返回 None。"""
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return value
    s = str(value).strip().upper()
    if s in ("", "NA", "N/A"):
        return None
    try:
        if "." in s or "e" in s.lower():
            return float(s)
        return int(s)
    except ValueError:
        return None


def _coerce_value(value: Any, field_type: str, optional: bool) -> Any:
    """按 schema 类型将原始值转换为存储/展示用类型。"""
    empty = value is None or (isinstance(value, str) and value.strip() == "")
    if empty:
        return None if optional else ("" if field_type in (TYPE_STRING, TYPE_OPTIONAL_STRING) else None)
    if field_type == TYPE_BOOL:
        return _coerce_bool(value)
    if field_type in (TYPE_NUMBER, TYPE_NUMBER_OPTIONAL):
        n = _coerce_number(value)
        return n if n is not None else (None if optional else value)
    if field_type == TYPE_LIST_OBJECTS:
        if isinstance(value, list):
            return value
        if isinstance(value, str):
            try:
                parsed = json.loads(value)
                return parsed if isinstance(parsed, list) else value
            except Exception:
                pass
        return value
    return value


def coerce_request_values(kv: Dict[str, Any]) -> Dict[str, Any]:
    """
    将解析出的 request 键值对按 schema 规范化：
    - 键统一为规范键名（别名映射）
    - 值按 REQUEST_FIELDS 类型做转换（bool/number/list of objects）
    用于导入 xlsx 后写入 raw_request_json 前。
    """
    key_to_type = get_key_to_type()
    key_to_optional = get_key_to_optional()
    result = {}
    for raw_key, value in kv.items():
        if raw_key == "_sheet_name":
            result["_sheet_name"] = value
            continue
        canonical = raw_key.strip()
        ft = key_to_type.get(canonical, TYPE_STRING)
        optional = key_to_optional.get(canonical, True)
        result[canonical] = _coerce_value(value, ft, optional)
        if canonical == "ADC Target Quality" and isinstance(result[canonical], list):
            result[canonical] = json.dumps(result[canonical], ensure_ascii=False)
    return result


def _raw_value_for_key(raw: Dict[str, Any], key: str) -> tuple:
    """从 raw 中取键对应的值。返回 (value, raw_key_used)，若不存在则 (None, None)。"""
    if key in raw:
        return (raw[key], key)
    return (None, None)


def get_display_order_keys() -> List[str]:
    """按 REQUEST_FIELDS 顺序返回规范键名列表，用于展示与投料表。"""
    return [f["key"] for f in REQUEST_FIELDS]


def format_value_for_display(value: Any, field_type: str) -> str:
    """按类型格式化用于展示（数字、bool、list of objects 等）。"""
    if value is None:
        return ""
    if isinstance(value, list):
        return json.dumps(value, ensure_ascii=False)
    if field_type == TYPE_NUMBER or field_type == TYPE_NUMBER_OPTIONAL:
        if isinstance(value, (int, float)):
            return str(int(value)) if value == int(value) else str(value)
        return str(value)
    if field_type == TYPE_BOOL:
        if isinstance(value, bool):
            return "是" if value else "否"
        s = str(value).strip().upper()
        if s in ("1", "Y", "YES", "TRUE", "是"):
            return "是"
        if s in ("0", "N", "NO", "FALSE", "否"):
            return "否"
        return str(value).strip()
    if field_type == TYPE_LIST_OBJECTS:
        if isinstance(value, list):
            parts = []
            for item in value:
                if isinstance(item, dict):
                    a = item.get("检项", "")
                    b = item.get("特殊要求", "")
                    parts.append("%s: %s" % (a, b))
                else:
                    parts.append(str(item))
            return " | ".join(parts) if parts else ""
        if isinstance(value, str):
            try:
                parsed = json.loads(value)
                if isinstance(parsed, list):
                    return format_value_for_display(parsed, TYPE_LIST_OBJECTS)
            except Exception:
                pass
        return str(value).strip()
    return str(value).strip()


def get_key_to_type() -> Dict[str, str]:
    """返回 规范键名 -> type 的映射。"""
    return {f["key"]: f["type"] for f in REQUEST_FIELDS}


def ordered_request_items(raw: Dict[str, Any]) -> List[tuple]:
    """
    按 REQUEST_FIELDS 顺序返回 (key, display_value) 列表；raw 中多出的键排在最后。
    """
    key_to_type = get_key_to_type()
    ordered = []
    shown_raw_keys = set()
    for key in get_display_order_keys():
        val, raw_key = _raw_value_for_key(raw, key)
        if val is not None:
            if raw_key:
                shown_raw_keys.add(raw_key)
            ft = key_to_type.get(key, TYPE_STRING)
            ordered.append((key, format_value_for_display(val, ft)))
    for key, val in raw.items():
        if key in ("_sheet_name",) or key in shown_raw_keys:
            continue
        if key.strip() in get_display_order_keys():
            continue
        ordered.append((key, format_value_for_display(val, TYPE_STRING)))
    return ordered


def ordered_request_items_for_display(raw: Dict[str, Any]) -> List[tuple]:
    """
    按 REQUEST_FIELDS 顺序返回 (字段名, 类型, 必填/可选, 展示值) 列表，用于 UI 表格展示。
    包含值为 None 的项，展示为 "null"；raw 中多出的键排在最后。
    """
    key_to_type = get_key_to_type()
    key_to_optional = get_key_to_optional()
    ordered: List[tuple] = []
    shown_raw_keys = set()
    for key in get_display_order_keys():
        val, raw_key = _raw_value_for_key(raw, key)
        if raw_key:
            shown_raw_keys.add(raw_key)
        ft = key_to_type.get(key, TYPE_STRING)
        optional_label = "可选" if key_to_optional.get(key, True) else "必填"
        if val is None:
            display_value = "null"
        else:
            display_value = format_value_for_display(val, ft)
        ordered.append((key, ft, optional_label, display_value))
    for key, val in raw.items():
        if key in ("_sheet_name",) or key in shown_raw_keys:
            continue
        if key.strip() in get_display_order_keys():
            continue
        display_value = "null" if val is None else format_value_for_display(val, TYPE_STRING)
        ordered.append((key, TYPE_STRING, "可选", display_value))
    return ordered
