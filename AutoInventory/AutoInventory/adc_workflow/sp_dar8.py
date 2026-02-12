"""
DAR8 类型 Setup Param(SP) 字段定义与计算逻辑。

该模块基于 Request 信息与用户输入，计算 DAR8 相关的各类体积/浓度参数，
并提供元数据用于：
- UI 两列表格展示（名称 + 数值）
- 点击单元格后高亮依赖字段与展示计算过程
- 自动生成文档说明
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

from .sp_core import (
    SetupParamFieldMeta,
    SetupParamCalculationResult,
    parse_leading_number,
    safe_div,
    ensure_float,
)


# ---------- 字段元数据定义 ----------


def _f(
    key: str,
    display_name: str,
    unit: str = "",
    data_type: str = "string",
    source: str = "derived",
    group: str = "meta",
    is_important: bool = False,
    description: str = "",
    depends_on: Optional[List[str]] = None,
    formula_text: str = "",
) -> SetupParamFieldMeta:
    return SetupParamFieldMeta(
        key=key,
        display_name=display_name,
        unit=unit,
        data_type=data_type,
        source=source,
        group=group,
        is_important=is_important,
        description=description,
        depends_on=depends_on or [],
        formula_text=formula_text,
    )


# group 常量，便于 UI 排序
GROUP_INPUT_REQUEST = "input_request"
GROUP_INPUT_USER = "input_user"
GROUP_OUTPUT_REDUCTION = "output_reduction"
GROUP_OUTPUT_CONJUGATION = "output_conjugation"
GROUP_META = "meta"


# 所有字段元数据列表
DAR8_FIELDS: List[SetupParamFieldMeta] = [
    # ----- 来自 Request 的输入 -----
    _f(
        key="antibody_conc_mg_ml",
        display_name="Antibody concention (mg/mL)",
        unit="mg/mL",
        data_type="float",
        source="request",
        group=GROUP_INPUT_REQUEST,
        description="Request 中的 Antibody concention (mg/mL)。",
    ),
    _f(
        key="reaction_scale_mg",
        display_name="Reaction Scale (mg)",
        unit="mg",
        data_type="float",
        source="request",
        group=GROUP_INPUT_REQUEST,
        description="Request 中的 Reaction Scale (mg)。",
    ),
    _f(
        key="mw_antibody_da",
        display_name="MW of antibody (Da)",
        unit="Da",
        data_type="float",
        source="request",
        group=GROUP_INPUT_REQUEST,
        description="Request 中的 MW of antibody (Da)。",
    ),
    _f(
        key="dissolved_in",
        display_name="Dissolved in",
        unit="",
        data_type="string",
        source="request",
        group=GROUP_INPUT_REQUEST,
        description="Request 中的 Dissolved in 字段，用于表示有机溶剂类型。",
    ),
    _f(
        key="lp_conc_str",
        display_name="LP浓度（原始）",
        unit="",
        data_type="string",
        source="request",
        group=GROUP_INPUT_REQUEST,
        description="Request 中的 LP浓度 字符串，例如 '10 mM'。",
    ),
    _f(
        key="lp_conc_mM",
        display_name="LP浓度（数值, mM）",
        unit="mM",
        data_type="float",
        source="derived",
        group=GROUP_INPUT_REQUEST,
        depends_on=["lp_conc_str"],
        description="从 LP浓度 字符串解析出的数值（只取前导数字部分），单位 mM；无法解析为 None。",
        formula_text="lp_conc_mM = 从 LP浓度 字符串前导部分解析出的数值，例如 '10 mM' -> 10.0。",
    ),
    _f(
        key="wbp_code",
        display_name="WBP Code",
        unit="",
        data_type="string",
        source="request",
        group=GROUP_INPUT_REQUEST,
    ),
    _f(
        key="request_id",
        display_name="ID",
        unit="",
        data_type="string",
        source="request",
        group=GROUP_INPUT_REQUEST,
    ),
    # ----- 用户输入 -----
    _f(
        key="tcep_eq",
        display_name="TCEP 当量",
        unit="eq",
        data_type="float",
        source="user_input",
        group=GROUP_INPUT_USER,
        description="用户输入的 TCEP 当量，默认 8.0。",
    ),
    _f(
        key="tcep_stock_mM",
        display_name="TCEP stock (mM)",
        unit="mM",
        data_type="float",
        source="user_input",
        group=GROUP_INPUT_USER,
        description="用户输入的 TCEP stock 浓度 (mM)，默认 8.0。",
    ),
    _f(
        key="conj_org_ratio_percent",
        display_name="Conjugation organic solvent ratio (%)",
        unit="%",
        data_type="float",
        source="user_input",
        group=GROUP_INPUT_USER,
        description=(
            "用户输入的有机溶剂体积分数（百分比形式，0–100）。"
            "内部计算时将其转换为 ratio_fraction = conj_org_ratio_percent / 100.0。"
        ),
        formula_text="ratio_fraction = 用户输入的百分比 / 100.0，例如 20 (%) -> 0.20。",
    ),
    _f(
        key="x_lp_per_ab",
        display_name="x LP/Ab",
        unit="",
        data_type="float",
        source="user_input",
        group=GROUP_INPUT_USER,
        description="用户输入的 x LP/Ab，当量比，默认 12.0。",
    ),
    _f(
        key="add_additional_tcep_eq",
        display_name="Add additional TCEP (eq, 输入)",
        unit="eq",
        data_type="optional_float",
        source="user_input",
        group=GROUP_INPUT_USER,
        description="可选输入：额外 TCEP 当量；仅在用户勾选时生效。",
    ),
    _f(
        key="add_additional_lp",
        display_name="Add additional LP (输入)",
        unit="",
        data_type="optional_float",
        source="user_input",
        group=GROUP_INPUT_USER,
        description="可选输入：额外 LP 量；数值含义依据实验员约定。",
    ),
    _f(
        key="additional_reaction_time_h",
        display_name="Additional reaction time (h, 输入)",
        unit="h",
        data_type="optional_float",
        source="user_input",
        group=GROUP_INPUT_USER,
        description="可选输入：额外反应时间（小时）。",
    ),
    _f(
        key="reaction_status",
        display_name="Reaction status",
        unit="",
        data_type="enum",
        source="user_input",
        group=GROUP_INPUT_USER,
        description="实验员主观判断填写，取值为 clear/cloudy/precipitate。",
    ),
    # ----- 输出：重点关注 -----
    _f(
        key="add_antibody_ml",
        display_name="Add antibody (mL)",
        unit="mL",
        data_type="float",
        source="derived",
        group=GROUP_OUTPUT_REDUCTION,
        is_important=True,
        depends_on=["reaction_scale_mg", "antibody_conc_mg_ml"],
        description="抗体加入体积，实验员重点关注。",
        formula_text="Add antibody (mL) = Reaction Scale (mg) / Antibody concention (mg/mL)。",
    ),
    _f(
        key="add_tcep_ml",
        display_name="Add TCEP (mL)",
        unit="mL",
        data_type="float",
        source="derived",
        group=GROUP_OUTPUT_REDUCTION,
        is_important=True,
        depends_on=["reaction_scale_mg", "mw_antibody_da", "tcep_eq", "tcep_stock_mM"],
        description="TCEP 加入体积，实验员重点关注。",
        formula_text=(
            "Add TCEP (mL) = Reaction Scale (mg) / MW of antibody(Da) "
            "* TCEP eq / TCEP stock(mM) * 1000。"
        ),
    ),
    _f(
        key="add_buffer_ml",
        display_name="Add buffer to adjust Ab conc. (mL)",
        unit="mL",
        data_type="float",
        source="derived",
        group=GROUP_OUTPUT_REDUCTION,
        is_important=True,
        depends_on=[
            "antibody_conc_mg_ml",
            "reduction_total_volume_ml",
            "add_antibody_ml",
            "add_tcep_ml",
        ],
        description=(
            "用于在抗体浓度较高时稀释至目标浓度的 buffer 体积。"
            "假设文档中的 Total volume 即 Reduction Total volume。"
        ),
        formula_text=(
            "若 Antibody concention >= 11.5："
            "Add buffer (mL) = Reduction Total volume(mL) - Add antibody (mL) "
            "- Add TCEP(mL) - Reduction Total volume(mL) * 0.01；"
            "否则为 0.0。"
        ),
    ),
    _f(
        key="add_edta_ml",
        display_name="Add 200mM EDTA (mL)",
        unit="mL",
        data_type="float",
        source="derived",
        group=GROUP_OUTPUT_REDUCTION,
        is_important=True,
        depends_on=["add_antibody_ml", "add_tcep_ml", "add_buffer_ml"],
        description="200 mM EDTA 加入体积，实验员重点关注。",
        formula_text=(
            "Add 200mM EDTA (mL) = 0.01 * (Add antibody (mL) + Add TCEP(mL) + Add buffer (mL))。"
        ),
    ),
    # ----- 输出：普通展示（含 Reduction 部分） -----
    _f(
        key="batch_no",
        display_name="Batch#",
        unit="",
        data_type="string",
        source="derived",
        group=GROUP_META,
        depends_on=["wbp_code", "request_id"],
        description="批号，格式为 WBP Code-YYmmddID，其中 YYmmdd 为当前日期。",
        formula_text="Batch# = WBP Code + '-' + 当前日期(YYmmdd) + ID。",
    ),
    _f(
        key="mab_conc_reduction_mg_ml",
        display_name="mAb conc. in reaction (mg/mL)",
        unit="mg/mL",
        data_type="float",
        source="derived",
        group=GROUP_OUTPUT_REDUCTION,
        depends_on=[
            "antibody_conc_mg_ml",
            "add_antibody_ml",
            "add_edta_ml",
            "add_tcep_ml",
        ],
        description=(
            "Reduction 反应体系中的 mAb 浓度。"
            "根据需求方确认：若 Antibody concention < 11.5，"
            "则 mAb conc. in reaction = Add antibody + Add 200mM EDTA + Add TCEP (单位 mL，量纲存在约定性)；"
            "否则 mAb conc. in reaction = 10.0。"
        ),
        formula_text=(
            "若 Antibody concention (mg/mL) < 11.5："
            "mAb conc. in reaction = Add antibody (mL) + Add 200mM EDTA(mL) + Add TCEP(mL)；"
            "否则 mAb conc. in reaction = 10.0。"
        ),
    ),
    _f(
        key="reduction_total_volume_ml",
        display_name="Reduction Total volume (mL)",
        unit="mL",
        data_type="float",
        source="derived",
        group=GROUP_OUTPUT_REDUCTION,
        depends_on=["reaction_scale_mg", "mab_conc_reduction_mg_ml"],
        description="Reduction 反应总体积。",
        formula_text=(
            "Reduction Total volume (mL) = Reaction Scale (mg) / mAb conc. in reaction (mg/mL)。"
        ),
    ),
    _f(
        key="reduction_reaction_temperature_c",
        display_name="Reduction Reaction temperature (°C)",
        unit="°C",
        data_type="float",
        source="fixed",
        group=GROUP_OUTPUT_REDUCTION,
        description="Reduction 反应温度，固定为 22°C。",
        formula_text="固定值：22°C。",
    ),
    _f(
        key="reduction_reaction_time_h",
        display_name="Reduction Reaction time (h)",
        unit="h",
        data_type="float",
        source="fixed",
        group=GROUP_OUTPUT_REDUCTION,
        description="Reduction 反应时间，固定为 18h。",
        formula_text="固定值：18h。",
    ),
    _f(
        key="add_additional_tcep_ml",
        display_name="Add additional TCEP (mL)",
        unit="mL",
        data_type="optional_float",
        source="derived",
        group=GROUP_OUTPUT_REDUCTION,
        depends_on=["reaction_scale_mg", "mw_antibody_da", "add_additional_tcep_eq", "tcep_stock_mM"],
        description="若用户输入了额外 TCEP 当量，则据此计算额外加入的 TCEP 体积；否则为 None。",
        formula_text=(
            "当且仅当存在 Add additional TCEP(eq)："
            "Add additional TCEP (mL) = Reaction Scale (mg) / MW of antibody(Da) "
            "* Add additional TCEP(eq) / TCEP stock(mM) * 1000。"
        ),
    ),
    # ----- 输出：Conjugation 部分 -----
    _f(
        key="conj_org_ratio_percent_out",
        display_name="Conjugation organic solvent ratio (%)",
        unit="%",
        data_type="float",
        source="derived",
        group=GROUP_OUTPUT_CONJUGATION,
        depends_on=["conj_org_ratio_percent"],
        description="输出字段，拷贝自用户输入的有机溶剂体积分数 (% )。",
        formula_text="直接等于用户输入的 Conjugation organic solvent ratio (%)。",
    ),
    _f(
        key="conj_org_ratio_unit",
        display_name="unit of Conjugation organic solvent ratio",
        unit="",
        data_type="string",
        source="derived",
        group=GROUP_OUTPUT_CONJUGATION,
        depends_on=["dissolved_in"],
        description="有机溶剂比率的单位/溶剂类型，拷贝自 Request 的 Dissolved in。",
        formula_text="unit = Request 中的 Dissolved in。",
    ),
    _f(
        key="x_lp_per_ab_out",
        display_name="x LP/Ab (输出)",
        unit="",
        data_type="float",
        source="derived",
        group=GROUP_OUTPUT_CONJUGATION,
        depends_on=["x_lp_per_ab"],
        description="输出字段，直接拷贝用户输入的 x LP/Ab。",
        formula_text="x LP/Ab (输出) = 用户输入的 x LP/Ab。",
    ),
    _f(
        key="conj_total_volume_ml",
        display_name="Conjugation Total volume (mL)",
        unit="mL",
        data_type="float",
        source="derived",
        group=GROUP_OUTPUT_CONJUGATION,
        depends_on=["reduction_total_volume_ml", "conj_org_ratio_percent"],
        description=(
            "Conjugation 反应总体系体积。"
            "ratio_fraction = conj_org_ratio_percent / 100.0，"
            "Conjugation Total volume = Reduction Total volume / (1 - ratio_fraction)。"
        ),
        formula_text=(
            "Conjugation Total volume(mL) = Reduction Total volume(mL) / (1.0 - ratio_fraction)，"
            "其中 ratio_fraction = Conjugation organic solvent ratio(%) / 100.0。"
        ),
    ),
    _f(
        key="add_lp_stock_ml",
        display_name="Add stock LP solution (mL)",
        unit="mL",
        data_type="float",
        source="derived",
        group=GROUP_OUTPUT_CONJUGATION,
        depends_on=["reaction_scale_mg", "mw_antibody_da", "x_lp_per_ab", "lp_conc_mM"],
        description="LP stock 溶液加入体积，依赖于 LP 浓度数值；若无法解析 LP 浓度则为 None。",
        formula_text=(
            "Add stock LP solution (mL) = Reaction Scale (mg) / MW of antibody(Da) "
            "* x LP/Ab / LP浓度(mM) * 1000。"
        ),
    ),
    _f(
        key="add_org_solvent_ml",
        display_name="Add organic solvent to reaction (mL)",
        unit="mL",
        data_type="float",
        source="derived",
        group=GROUP_OUTPUT_CONJUGATION,
        depends_on=["conj_total_volume_ml", "conj_org_ratio_percent", "add_lp_stock_ml"],
        description="向反应体系中额外加入的有机溶剂体积。",
        formula_text=(
            "Add organic solvent (mL) = Conjugation Total volume(mL) * ratio_fraction "
            "- Add stock LP solution(mL)，其中 ratio_fraction = ratio_percent / 100.0。"
        ),
    ),
    _f(
        key="conj_conc_mg_ml",
        display_name="Conjugation Concentration (mg/mL)",
        unit="mg/mL",
        data_type="float",
        source="derived",
        group=GROUP_OUTPUT_CONJUGATION,
        depends_on=["reaction_scale_mg", "conj_total_volume_ml"],
        description="Conjugation 体系中的 mAb 浓度。",
        formula_text="Conjugation Concentration (mg/mL) = Reaction Scale (mg) / Conjugation Total volume(mL)。",
    ),
    _f(
        key="conj_reaction_temperature_c",
        display_name="Conjugation Reaction temperature (°C)",
        unit="°C",
        data_type="float",
        source="fixed",
        group=GROUP_OUTPUT_CONJUGATION,
        description="Conjugation 反应温度，固定 22°C。",
        formula_text="固定值：22°C。",
    ),
    _f(
        key="conj_reaction_time_h",
        display_name="Conjugation Reaction time (h)",
        unit="h",
        data_type="float",
        source="fixed",
        group=GROUP_OUTPUT_CONJUGATION,
        description="Conjugation 反应时间，固定 18h。",
        formula_text="固定值：18h。",
    ),
    _f(
        key="add_additional_lp_out",
        display_name="Add additional LP (输出)",
        unit="",
        data_type="optional_float",
        source="derived",
        group=GROUP_OUTPUT_CONJUGATION,
        depends_on=["add_additional_lp"],
        description="输出字段，当且仅当用户输入了 Add additional LP 时，拷贝其值。",
        formula_text="Add additional LP (输出) = 输入的 Add additional LP；否则为 None。",
    ),
    _f(
        key="additional_reaction_time_h_out",
        display_name="Additional reaction time (h, 输出)",
        unit="h",
        data_type="optional_float",
        source="derived",
        group=GROUP_OUTPUT_CONJUGATION,
        depends_on=["additional_reaction_time_h"],
        description="输出字段，当且仅当用户输入了 Additional reaction time 时，拷贝其值。",
        formula_text="Additional reaction time (输出) = 输入的 Additional reaction time；否则为 None。",
    ),
]


_DAR8_META_BY_KEY: Dict[str, SetupParamFieldMeta] = {f.key: f for f in DAR8_FIELDS}


def get_dar8_field_meta_dict() -> Dict[str, SetupParamFieldMeta]:
    """返回 key -> meta 的映射，用于 UI 与文档生成。"""
    return _DAR8_META_BY_KEY


# ---------- 从 Request 提取 DAR8 相关输入 ----------


def build_dar8_inputs_from_request(raw_request: Dict[str, Any]) -> Dict[str, Any]:
    """
    从 Request 原始 dict 中抽取 DAR8 所需字段，并做基础类型转换。

    仅负责提取与简单解析，不做数值计算。
    """
    result: Dict[str, Any] = {}
    # 直接映射
    result["antibody_conc_mg_ml"] = ensure_float(
        raw_request.get("Antibody concention (mg/mL)")
    )
    result["reaction_scale_mg"] = ensure_float(raw_request.get("Reaction Scale (mg)"))
    result["mw_antibody_da"] = ensure_float(raw_request.get("MW of antibody (Da)"))
    result["dissolved_in"] = raw_request.get("Dissolved in") or ""
    lp_raw = raw_request.get("LP浓度")
    result["lp_conc_str"] = "" if lp_raw is None else str(lp_raw)
    result["lp_conc_mM"] = parse_leading_number(lp_raw)
    result["wbp_code"] = raw_request.get("WBP Code") or ""
    req_id = raw_request.get("ID")
    if req_id is None:
        result["request_id"] = ""
    else:
        # 保持与 UI 一致：数字转为无小数的字符串，其余直接 str()
        if isinstance(req_id, (int, float)):
            result["request_id"] = str(int(req_id))
        else:
            result["request_id"] = str(req_id).strip()
    return result


# ---------- DAR8 计算主函数 ----------


def calculate_dar8_sp(
    raw_request: Dict[str, Any],
    user_inputs: Dict[str, Any],
) -> SetupParamCalculationResult:
    """
    执行 DAR8 SP 计算。

    参数：
    - raw_request: Request 原始键值对（从 workflow.raw_request_json 解析）。
    - user_inputs: 用户在 UI 中填写的 DAR8 相关输入字典。
    返回：
    - SetupParamCalculationResult，包含所有 DAR8_FIELDS 对应的值。
    """
    meta = _DAR8_META_BY_KEY
    result = SetupParamCalculationResult()

    # 1. 基础输入：Request -> ctx
    ctx: Dict[str, Any] = build_dar8_inputs_from_request(raw_request)

    # 2. 用户输入合并（带默认值）
    tcep_eq = ensure_float(user_inputs.get("tcep_eq", 8.0)) or 8.0
    tcep_stock_mM = ensure_float(user_inputs.get("tcep_stock_mM", 8.0)) or 8.0
    conj_org_ratio_percent = ensure_float(
        user_inputs.get("conj_org_ratio_percent", 0.0)
    ) or 0.0
    x_lp_per_ab = ensure_float(user_inputs.get("x_lp_per_ab", 12.0)) or 12.0
    add_additional_tcep_eq = ensure_float(user_inputs.get("add_additional_tcep_eq"))
    add_additional_lp = ensure_float(user_inputs.get("add_additional_lp"))
    additional_reaction_time_h = ensure_float(
        user_inputs.get("additional_reaction_time_h")
    )
    reaction_status = user_inputs.get("reaction_status") or ""

    ctx.update(
        dict(
            tcep_eq=tcep_eq,
            tcep_stock_mM=tcep_stock_mM,
            conj_org_ratio_percent=conj_org_ratio_percent,
            x_lp_per_ab=x_lp_per_ab,
            add_additional_tcep_eq=add_additional_tcep_eq,
            add_additional_lp=add_additional_lp,
            additional_reaction_time_h=additional_reaction_time_h,
            reaction_status=reaction_status,
        )
    )

    # 将所有 ctx 值先写入结果（便于 UI 显示输入字段）
    for key, value in ctx.items():
        if key in meta:
            result.set_value(meta[key], value)

    # ratio_fraction = conj_org_ratio_percent / 100.0
    ratio_fraction = None
    if conj_org_ratio_percent is not None:
        ratio_fraction = conj_org_ratio_percent / 100.0
    ctx["ratio_fraction"] = ratio_fraction

    # ---------- 核心计算 ----------
    rs = ctx.get("reaction_scale_mg")
    ab_conc = ctx.get("antibody_conc_mg_ml")
    mw_ab = ctx.get("mw_antibody_da")
    lp_conc_mM = ctx.get("lp_conc_mM")

    # Add antibody (mL)
    add_antibody_ml = safe_div(rs, ab_conc)
    result.set_value(meta["add_antibody_ml"], add_antibody_ml)

    # Add TCEP (mL)
    add_tcep_ml = None
    if rs is not None and mw_ab and tcep_eq and tcep_stock_mM:
        try:
            add_tcep_ml = float(rs) / float(mw_ab) * float(tcep_eq) / float(
                tcep_stock_mM
            ) * 1000.0
        except Exception:
            add_tcep_ml = None
    result.set_value(meta["add_tcep_ml"], add_tcep_ml)

    # mAb conc. in reaction (mg/mL)
    mab_conc_reduction = None
    if ab_conc is None:
        mab_conc_reduction = None
    else:
        try:
            if ab_conc < 11.5:
                if (
                    add_antibody_ml is not None
                    and add_tcep_ml is not None
                    # Add EDTA 依赖 Add buffer，后面会算，此处先占位 None
                ):
                    # 此处先不依赖 EDTA，自洽计算流程中会在写入结果时再更新
                    # 为保持与文档一致，仍按加和体积逻辑，只在后续补上 EDTA。
                    pass
            else:
                mab_conc_reduction = 10.0
        except Exception:
            mab_conc_reduction = None
    # 先写入占位，后面在知道 Add EDTA 后再更新
    result.set_value(meta["mab_conc_reduction_mg_ml"], mab_conc_reduction)

    # Reduction Total volume (mL)
    reduction_total_volume_ml = safe_div(rs, mab_conc_reduction)
    result.set_value(meta["reduction_total_volume_ml"], reduction_total_volume_ml)

    # Add buffer to adjust Ab conc. (mL)
    add_buffer_ml: Optional[float]
    if ab_conc is None:
        add_buffer_ml = None
    else:
        if ab_conc < 11.5:
            add_buffer_ml = 0.0
        else:
            if (
                reduction_total_volume_ml is not None
                and add_antibody_ml is not None
                and add_tcep_ml is not None
            ):
                try:
                    add_buffer_ml = (
                        reduction_total_volume_ml
                        - add_antibody_ml
                        - add_tcep_ml
                        - reduction_total_volume_ml * 0.01
                    )
                except Exception:
                    add_buffer_ml = None
            else:
                add_buffer_ml = None
    result.set_value(meta["add_buffer_ml"], add_buffer_ml)

    # Add 200mM EDTA (mL)
    add_edta_ml = None
    if (
        add_antibody_ml is not None
        and add_tcep_ml is not None
        and add_buffer_ml is not None
    ):
        try:
            add_edta_ml = 0.01 * (
                float(add_antibody_ml) + float(add_tcep_ml) + float(add_buffer_ml)
            )
        except Exception:
            add_edta_ml = None
    result.set_value(meta["add_edta_ml"], add_edta_ml)

    # 现在补全 mAb conc. in reaction 在 ab_conc < 11.5 情形下的值
    if ab_conc is not None and ab_conc < 11.5:
        if (
            add_antibody_ml is not None
            and add_edta_ml is not None
            and add_tcep_ml is not None
        ):
            try:
                mab_conc_reduction = (
                    float(add_antibody_ml)
                    + float(add_edta_ml)
                    + float(add_tcep_ml)
                )
            except Exception:
                pass
        result.set_value(meta["mab_conc_reduction_mg_ml"], mab_conc_reduction)
        # 同时更新 Reduction Total volume
        reduction_total_volume_ml = safe_div(rs, mab_conc_reduction)
        result.set_value(meta["reduction_total_volume_ml"], reduction_total_volume_ml)

    # 固定温度与时间（Reduction）
    result.set_value(meta["reduction_reaction_temperature_c"], 22.0)
    result.set_value(meta["reduction_reaction_time_h"], 18.0)

    # Add additional TCEP (mL) 输出
    add_additional_tcep_ml = None
    if add_additional_tcep_eq is not None and rs is not None and mw_ab and tcep_stock_mM:
        try:
            add_additional_tcep_ml = (
                float(rs)
                / float(mw_ab)
                * float(add_additional_tcep_eq)
                / float(tcep_stock_mM)
                * 1000.0
            )
        except Exception:
            add_additional_tcep_ml = None
    result.set_value(meta["add_additional_tcep_ml"], add_additional_tcep_ml)

    # Batch#
    wbp_code = ctx.get("wbp_code", "") or ""
    req_id_str = ctx.get("request_id", "") or ""
    today = datetime.now().strftime("%y%m%d")
    batch_no = ""
    if wbp_code or req_id_str:
        batch_no = f"{wbp_code}-{today}{req_id_str}"
    result.set_value(meta["batch_no"], batch_no)

    # ---------- Conjugation 部分 ----------
    # 输出 ratio 与 unit/xLP
    result.set_value(meta["conj_org_ratio_percent_out"], conj_org_ratio_percent)
    result.set_value(meta["conj_org_ratio_unit"], ctx.get("dissolved_in", ""))
    result.set_value(meta["x_lp_per_ab_out"], x_lp_per_ab)

    # Conjugation Total volume (mL)
    conj_total_volume_ml = None
    if reduction_total_volume_ml is not None and ratio_fraction is not None:
        try:
            denom = 1.0 - float(ratio_fraction)
            if denom != 0.0:
                conj_total_volume_ml = float(reduction_total_volume_ml) / denom
        except Exception:
            conj_total_volume_ml = None
    result.set_value(meta["conj_total_volume_ml"], conj_total_volume_ml)

    # Add stock LP solution (mL)
    add_lp_stock_ml = None
    if rs is not None and mw_ab and x_lp_per_ab and lp_conc_mM:
        try:
            add_lp_stock_ml = (
                float(rs)
                / float(mw_ab)
                * float(x_lp_per_ab)
                / float(lp_conc_mM)
                * 1000.0
            )
        except Exception:
            add_lp_stock_ml = None
    result.set_value(meta["add_lp_stock_ml"], add_lp_stock_ml)

    # Add organic solvent to reaction (mL)
    add_org_solvent_ml = None
    if conj_total_volume_ml is not None and ratio_fraction is not None:
        try:
            add_org_solvent_ml = (
                float(conj_total_volume_ml) * float(ratio_fraction)
            )
            if add_lp_stock_ml is not None:
                add_org_solvent_ml -= float(add_lp_stock_ml)
        except Exception:
            add_org_solvent_ml = None
    result.set_value(meta["add_org_solvent_ml"], add_org_solvent_ml)

    # Conjugation Concentration (mg/mL)
    conj_conc_mg_ml = safe_div(rs, conj_total_volume_ml)
    result.set_value(meta["conj_conc_mg_ml"], conj_conc_mg_ml)

    # 固定温度与时间（Conjugation）
    result.set_value(meta["conj_reaction_temperature_c"], 22.0)
    result.set_value(meta["conj_reaction_time_h"], 18.0)

    # Optional 输出：额外 LP 与额外反应时间
    result.set_value(meta["add_additional_lp_out"], add_additional_lp)
    result.set_value(
        meta["additional_reaction_time_h_out"], additional_reaction_time_h
    )

    # Reaction status 作为用户输入字段已在 ctx->result 中写入

    return result


# ---------- 文档渲染 ----------


def render_dar8_doc_markdown() -> str:
    """
    将 DAR8_FIELDS 渲染为 markdown 文本，记录：
    - 字段名称 / 内部 key
    - 单位 / 类型 / 数据来源
    - 所属分组
    - 依赖字段
    - 公式描述
    """
    group_titles = {
        GROUP_INPUT_REQUEST: "Request 输入字段",
        GROUP_INPUT_USER: "用户输入字段",
        GROUP_OUTPUT_REDUCTION: "Antibody Reduction Set Up 输出字段",
        GROUP_OUTPUT_CONJUGATION: "Antibody Conjugation Set Up 输出字段",
        GROUP_META: "元数据字段",
    }

    # 按 group 排序，再按 display_name 排序
    ordered = sorted(
        DAR8_FIELDS, key=lambda f: (f.group, f.display_name.lower())
    )

    lines: List[str] = []
    current_group = None
    for fmeta in ordered:
        if fmeta.group != current_group:
            current_group = fmeta.group
            title = group_titles.get(current_group, current_group or "")
            if lines:
                lines.append("")
            lines.append(f"### {title}")
            lines.append("")
        lines.append(f"- **名称**：{fmeta.display_name}")
        lines.append(f"  - 内部 key：`{fmeta.key}`")
        if fmeta.unit:
            lines.append(f"  - 单位：{fmeta.unit}")
        lines.append(f"  - 类型：{fmeta.data_type}")
        lines.append(f"  - 数据来源：{fmeta.source}")
        if fmeta.is_important:
            lines.append(f"  - 重要性：实验员重点关注")
        if fmeta.description:
            lines.append(f"  - 说明：{fmeta.description}")
        if fmeta.depends_on:
            deps = ", ".join(f"`{k}`" for k in fmeta.depends_on)
            lines.append(f"  - 依赖字段：{deps}")
        else:
            lines.append("  - 依赖字段：无（原始输入或固定值）")
        if fmeta.formula_text:
            lines.append(f"  - 计算逻辑：{fmeta.formula_text}")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def write_dar8_doc_markdown(path: str) -> None:
    """将 DAR8 字段说明文档写入指定路径。"""
    content = render_dar8_doc_markdown()
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


if __name__ == "__main__":
    # 调试入口：直接运行本文件即可在默认位置生成文档
    default_path = "docs/sp_dar8_setup_param.md"
    write_dar8_doc_markdown(default_path)
    print(f"DAR8 SP 文档已生成到: {default_path}")

