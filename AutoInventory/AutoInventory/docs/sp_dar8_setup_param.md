### Request 输入字段

- **名称**：Antibody concention (mg/mL)
  - 内部 key：`antibody_conc_mg_ml`
  - 单位：mg/mL
  - 类型：float
  - 数据来源：request
  - 说明：Request 中的 Antibody concention (mg/mL)。
  - 依赖字段：无（原始输入或固定值）

- **名称**：Dissolved in
  - 内部 key：`dissolved_in`
  - 类型：string
  - 数据来源：request
  - 说明：Request 中的 Dissolved in 字段，用于表示有机溶剂类型。
  - 依赖字段：无（原始输入或固定值）

- **名称**：ID
  - 内部 key：`request_id`
  - 类型：string
  - 数据来源：request
  - 依赖字段：无（原始输入或固定值）

- **名称**：LP浓度（原始）
  - 内部 key：`lp_conc_str`
  - 类型：string
  - 数据来源：request
  - 说明：Request 中的 LP浓度 字符串，例如 '10 mM'。
  - 依赖字段：无（原始输入或固定值）

- **名称**：LP浓度（数值, mM）
  - 内部 key：`lp_conc_mM`
  - 单位：mM
  - 类型：float
  - 数据来源：derived
  - 说明：从 LP浓度 字符串解析出的数值（只取前导数字部分），单位 mM；无法解析为 None。
  - 依赖字段：`lp_conc_str`
  - 计算逻辑：lp_conc_mM = 从 LP浓度 字符串前导部分解析出的数值，例如 '10 mM' -> 10.0。

- **名称**：MW of antibody (Da)
  - 内部 key：`mw_antibody_da`
  - 单位：Da
  - 类型：float
  - 数据来源：request
  - 依赖字段：无（原始输入或固定值）

- **名称**：Reaction Scale (mg)
  - 内部 key：`reaction_scale_mg`
  - 单位：mg
  - 类型：float
  - 数据来源：request
  - 说明：Request 中的 Reaction Scale (mg)。
  - 依赖字段：无（原始输入或固定值）

- **名称**：WBP Code
  - 内部 key：`wbp_code`
  - 类型：string
  - 数据来源：request
  - 依赖字段：无（原始输入或固定值）

### 用户输入字段

- **名称**：Add additional LP (输入)
  - 内部 key：`add_additional_lp`
  - 类型：optional_float
  - 数据来源：user_input
  - 说明：可选输入：额外 LP 量；数值含义依据实验员约定。
  - 依赖字段：无（原始输入或固定值）

- **名称**：Add additional TCEP (eq, 输入)
  - 内部 key：`add_additional_tcep_eq`
  - 单位：eq
  - 类型：optional_float
  - 数据来源：user_input
  - 说明：可选输入：额外 TCEP 当量；仅在用户勾选时生效。
  - 依赖字段：无（原始输入或固定值）

- **名称**：Additional reaction time (h, 输入)
  - 内部 key：`additional_reaction_time_h`
  - 单位：h
  - 类型：optional_float
  - 数据来源：user_input
  - 说明：可选输入：额外反应时间（小时）。
  - 依赖字段：无（原始输入或固定值）

- **名称**：Conjugation organic solvent ratio (%)
  - 内部 key：`conj_org_ratio_percent`
  - 单位：%
  - 类型：float
  - 数据来源：user_input
  - 说明：用户输入的有机溶剂体积分数（百分比形式，0–100）。内部计算时将其转换为 ratio_fraction = conj_org_ratio_percent / 100.0。
  - 依赖字段：无（原始输入或固定值）
  - 计算逻辑：ratio_fraction = 用户输入的百分比 / 100.0，例如 20 (%) -> 0.20。

- **名称**：Reaction status
  - 内部 key：`reaction_status`
  - 类型：enum
  - 数据来源：user_input
  - 说明：实验员主观判断填写，取值为 clear/cloudy/precipitate。
  - 依赖字段：无（原始输入或固定值）

- **名称**：TCEP stock (mM)
  - 内部 key：`tcep_stock_mM`
  - 单位：mM
  - 类型：float
  - 数据来源：user_input
  - 说明：用户输入的 TCEP stock 浓度 (mM)，默认 8.0。
  - 依赖字段：无（原始输入或固定值）

- **名称**：TCEP 当量
  - 内部 key：`tcep_eq`
  - 单位：eq
  - 类型：float
  - 数据来源：user_input
  - 说明：用户输入的 TCEP 当量，默认 8.0。
  - 依赖字段：无（原始输入或固定值）

- **名称**：x LP/Ab
  - 内部 key：`x_lp_per_ab`
  - 类型：float
  - 数据来源：user_input
  - 说明：用户输入的 x LP/Ab，当量比，默认 12.0。
  - 依赖字段：无（原始输入或固定值）

### Antibody Reduction Set Up 输出字段

- **名称**：Add 200mM EDTA (mL)
  - 内部 key：`add_edta_ml`
  - 单位：mL
  - 类型：float
  - 数据来源：derived
  - 重要性：实验员重点关注
  - 说明：200 mM EDTA 加入体积，实验员重点关注。
  - 依赖字段：`add_antibody_ml`, `add_tcep_ml`, `add_buffer_ml`
  - 计算逻辑：Add 200mM EDTA (mL) = 0.01 * (Add antibody (mL) + Add TCEP(mL) + Add buffer (mL))。

- **名称**：Add antibody (mL)
  - 内部 key：`add_antibody_ml`
  - 单位：mL
  - 类型：float
  - 数据来源：derived
  - 重要性：实验员重点关注
  - 说明：抗体加入体积，实验员重点关注。
  - 依赖字段：`reaction_scale_mg`, `antibody_conc_mg_ml`
  - 计算逻辑：Add antibody (mL) = Reaction Scale (mg) / Antibody concention (mg/mL)。

- **名称**：Add buffer to adjust Ab conc. (mL)
  - 内部 key：`add_buffer_ml`
  - 单位：mL
  - 类型：float
  - 数据来源：derived
  - 重要性：实验员重点关注
  - 说明：用于在抗体浓度较高时稀释至目标浓度的 buffer 体积。假设文档中的 Total volume 即 Reduction Total volume。
  - 依赖字段：`antibody_conc_mg_ml`, `reduction_total_volume_ml`, `add_antibody_ml`, `add_tcep_ml`
  - 计算逻辑：若 Antibody concention >= 11.5：Add buffer (mL) = Reduction Total volume(mL) - Add antibody (mL) - Add TCEP(mL) - Reduction Total volume(mL) * 0.01；否则为 0.0。

- **名称**：Add additional TCEP (mL)
  - 内部 key：`add_additional_tcep_ml`
  - 单位：mL
  - 类型：optional_float
  - 数据来源：derived
  - 说明：若用户输入了额外 TCEP 当量，则据此计算额外加入的 TCEP 体积；否则为 None。
  - 依赖字段：`reaction_scale_mg`, `mw_antibody_da`, `add_additional_tcep_eq`, `tcep_stock_mM`
  - 计算逻辑：当且仅当存在 Add additional TCEP(eq)：Add additional TCEP (mL) = Reaction Scale (mg) / MW of antibody(Da) * Add additional TCEP(eq) / TCEP stock(mM) * 1000。

- **名称**：Add TCEP (mL)
  - 内部 key：`add_tcep_ml`
  - 单位：mL
  - 类型：float
  - 数据来源：derived
  - 重要性：实验员重点关注
  - 说明：TCEP 加入体积，实验员重点关注。
  - 依赖字段：`reaction_scale_mg`, `mw_antibody_da`, `tcep_eq`, `tcep_stock_mM`
  - 计算逻辑：Add TCEP (mL) = Reaction Scale (mg) / MW of antibody(Da) * TCEP eq / TCEP stock(mM) * 1000。

- **名称**：Reduction Reaction temperature (°C)
  - 内部 key：`reduction_reaction_temperature_c`
  - 单位：°C
  - 类型：float
  - 数据来源：fixed
  - 说明：Reduction 反应温度，固定为 22°C。
  - 依赖字段：无（原始输入或固定值）
  - 计算逻辑：固定值：22°C。

- **名称**：Reduction Reaction time (h)
  - 内部 key：`reduction_reaction_time_h`
  - 单位：h
  - 类型：float
  - 数据来源：fixed
  - 说明：Reduction 反应时间，固定为 18h。
  - 依赖字段：无（原始输入或固定值）
  - 计算逻辑：固定值：18h。

- **名称**：Reduction Total volume (mL)
  - 内部 key：`reduction_total_volume_ml`
  - 单位：mL
  - 类型：float
  - 数据来源：derived
  - 说明：Reduction 反应总体积。
  - 依赖字段：`reaction_scale_mg`, `mab_conc_reduction_mg_ml`
  - 计算逻辑：Reduction Total volume (mL) = Reaction Scale (mg) / mAb conc. in reaction (mg/mL)。

- **名称**：mAb conc. in reaction (mg/mL)
  - 内部 key：`mab_conc_reduction_mg_ml`
  - 单位：mg/mL
  - 类型：float
  - 数据来源：derived
  - 说明：Reduction 反应体系中的 mAb 浓度。根据需求方确认：若 Antibody concention < 11.5，则 mAb conc. in reaction = Add antibody + Add 200mM EDTA + Add TCEP (单位 mL，量纲存在约定性)；否则 mAb conc. in reaction = 10.0。
  - 依赖字段：`antibody_conc_mg_ml`, `add_antibody_ml`, `add_edta_ml`, `add_tcep_ml`
  - 计算逻辑：若 Antibody concention (mg/mL) < 11.5：mAb conc. in reaction = Add antibody (mL) + Add 200mM EDTA(mL) + Add TCEP(mL)；否则 mAb conc. in reaction = 10.0。

### Antibody Conjugation Set Up 输出字段

- **名称**：Add additional LP (输出)
  - 内部 key：`add_additional_lp_out`
  - 类型：optional_float
  - 数据来源：derived
  - 说明：输出字段，当且仅当用户输入了 Add additional LP 时，拷贝其值。
  - 依赖字段：`add_additional_lp`
  - 计算逻辑：Add additional LP (输出) = 输入的 Add additional LP；否则为 None。

- **名称**：Additional reaction time (h, 输出)
  - 内部 key：`additional_reaction_time_h_out`
  - 单位：h
  - 类型：optional_float
  - 数据来源：derived
  - 说明：输出字段，当且仅当用户输入了 Additional reaction time 时，拷贝其值。
  - 依赖字段：`additional_reaction_time_h`
  - 计算逻辑：Additional reaction time (输出) = 输入的 Additional reaction time；否则为 None。

- **名称**：Conjugation Concentration (mg/mL)
  - 内部 key：`conj_conc_mg_ml`
  - 单位：mg/mL
  - 类型：float
  - 数据来源：derived
  - 说明：Conjugation 体系中的 mAb 浓度。
  - 依赖字段：`reaction_scale_mg`, `conj_total_volume_ml`
  - 计算逻辑：Conjugation Concentration (mg/mL) = Reaction Scale (mg) / Conjugation Total volume(mL)。

- **名称**：Conjugation Reaction temperature (°C)
  - 内部 key：`conj_reaction_temperature_c`
  - 单位：°C
  - 类型：float
  - 数据来源：fixed
  - 说明：Conjugation 反应温度，固定 22°C。
  - 依赖字段：无（原始输入或固定值）
  - 计算逻辑：固定值：22°C。

- **名称**：Conjugation Reaction time (h)
  - 内部 key：`conj_reaction_time_h`
  - 单位：h
  - 类型：float
  - 数据来源：fixed
  - 说明：Conjugation 反应时间，固定 18h。
  - 依赖字段：无（原始输入或固定值）
  - 计算逻辑：固定值：18h。

- **名称**：Conjugation Total volume (mL)
  - 内部 key：`conj_total_volume_ml`
  - 单位：mL
  - 类型：float
  - 数据来源：derived
  - 说明：Conjugation 反应总体系体积。ratio_fraction = conj_org_ratio_percent / 100.0，Conjugation Total volume = Reduction Total volume / (1 - ratio_fraction)。
  - 依赖字段：`reduction_total_volume_ml`, `conj_org_ratio_percent`
  - 计算逻辑：Conjugation Total volume(mL) = Reduction Total volume(mL) / (1.0 - ratio_fraction)，其中 ratio_fraction = Conjugation organic solvent ratio(%) / 100.0。

- **名称**：Add organic solvent to reaction (mL)
  - 内部 key：`add_org_solvent_ml`
  - 单位：mL
  - 类型：float
  - 数据来源：derived
  - 说明：向反应体系中额外加入的有机溶剂体积。
  - 依赖字段：`conj_total_volume_ml`, `conj_org_ratio_percent`, `add_lp_stock_ml`
  - 计算逻辑：Add organic solvent (mL) = Conjugation Total volume(mL) * ratio_fraction - Add stock LP solution(mL)，其中 ratio_fraction = ratio_percent / 100.0。

- **名称**：Add stock LP solution (mL)
  - 内部 key：`add_lp_stock_ml`
  - 单位：mL
  - 类型：float
  - 数据来源：derived
  - 说明：LP stock 溶液加入体积，依赖于 LP 浓度数值；若无法解析 LP 浓度则为 None。
  - 依赖字段：`reaction_scale_mg`, `mw_antibody_da`, `x_lp_per_ab`, `lp_conc_mM`
  - 计算逻辑：Add stock LP solution (mL) = Reaction Scale (mg) / MW of antibody(Da) * x LP/Ab / LP浓度(mM) * 1000。

- **名称**：Conjugation organic solvent ratio (%)
  - 内部 key：`conj_org_ratio_percent_out`
  - 单位：%
  - 类型：float
  - 数据来源：derived
  - 说明：输出字段，拷贝自用户输入的有机溶剂体积分数 (% )。
  - 依赖字段：`conj_org_ratio_percent`
  - 计算逻辑：直接等于用户输入的 Conjugation organic solvent ratio (%)。

- **名称**：unit of Conjugation organic solvent ratio
  - 内部 key：`conj_org_ratio_unit`
  - 类型：string
  - 数据来源：derived
  - 说明：有机溶剂比率的单位/溶剂类型，拷贝自 Request 的 Dissolved in。
  - 依赖字段：`dissolved_in`
  - 计算逻辑：unit = Request 中的 Dissolved in。

- **名称**：x LP/Ab (输出)
  - 内部 key：`x_lp_per_ab_out`
  - 类型：float
  - 数据来源：derived
  - 说明：输出字段，直接拷贝用户输入的 x LP/Ab。
  - 依赖字段：`x_lp_per_ab`
  - 计算逻辑：x LP/Ab (输出) = 用户输入的 x LP/Ab。

### 元数据字段

- **名称**：Batch#
  - 内部 key：`batch_no`
  - 类型：string
  - 数据来源：derived
  - 说明：批号，格式为 WBP Code-YYmmddID，其中 YYmmdd 为当前日期。
  - 依赖字段：`wbp_code`, `request_id`
  - 计算逻辑：Batch# = WBP Code + '-' + 当前日期(YYmmdd) + ID。

