### 背景与目标

本模块在原有偶联任务 Request 信息与纯化步骤之间，引入了一层新的中间抽象：**Setup Param（SP）**。  
当前实现了 **DAR8** 类型的 SP，用于在导入偶联任务后，根据 Request 信息与实验员手动输入，计算出一系列与 DAR8 相关的投料参数，并以可视化方式展示与解释计算过程。

本说明文档用于记录：

- 数据流与主要模块结构；
- DAR8 SP 中各类数据的来源与类型分层；
- 计算逻辑与容错策略（公式整体概览，详细字段级公式见 `sp_dar8_setup_param.md`）；
- PyQt 界面交互设计：填写-展示流程、点击高亮及计算说明；
- 将来扩展到 DAR4 / Deblocking / Thiomab 的思路。

---

### 模块与文件结构

- `adc_workflow/sp_core.py`
  - 定义 SP 核心抽象与通用工具：
    - `SetupParamFieldMeta`：字段元数据（名称、类型、来源、分组、依赖、公式说明等）。
    - `SetupParamCalculationResult`：一次计算结果的 key → value 容器。
    - 工具函数：
      - `parse_leading_number(text)`: 从字符串前导部分提取数值（如 `"10 mM"` → `10.0`）。
      - `safe_div(numerator, denominator)`: 安全除法，处理 `None` 与除零。
      - `format_number(value, digits)`: 统一数值展示格式。
      - `ensure_float(value)`: 宽松地将任意输入转换为 `float`。

- `adc_workflow/sp_dar8.py`
  - DAR8 专用字段与计算逻辑：
    - `DAR8_FIELDS: List[SetupParamFieldMeta]`：
      - 覆盖 Request 输入、用户输入、Reduction 输出、Conjugation 输出及元数据字段。
      - 每个字段定义其：
        - `key`、`display_name`、`unit`、`data_type`（float/string/enum/optional_float 等）；
        - `source`（`request` / `user_input` / `derived` / `fixed`）；
        - `group`（如 `input_request`、`input_user`、`output_reduction`、`output_conjugation`、`meta`）；
        - `depends_on`（依赖字段列表）；
        - `formula_text`（人类可读公式说明）。
    - `build_dar8_inputs_from_request(raw_request) -> Dict[str, Any]`：
      - 从 Request 原始字典中抽取 DAR8 所需字段，并做基础解析/类型转换（如从 `"LP浓度"` 字符串解析出数值 `lp_conc_mM`）。
    - `calculate_dar8_sp(raw_request, user_inputs) -> SetupParamCalculationResult`：
      - 合并 Request 与用户输入，执行 DAR8 SP 全部数值计算，并返回包含所有字段值的结果对象。
    - 文档生成：
      - `render_dar8_doc_markdown() -> str`：基于 `DAR8_FIELDS` 渲染出字段级说明。
      - `write_dar8_doc_markdown(path)`：写出 markdown 文档，当前产物为 `docs/sp_dar8_setup_param.md`。

- `adc_workflow/controller.py`
  - `ADCWorkflowController.get_dar8_request_inputs(workflow_id)`：
    - 便捷 helper，从 workflow 中解出 `raw_request`，并调用 `build_dar8_inputs_from_request` 得到 DAR8 相关输入上下文。
    - 当前 PyQt 界面直接在 `_workflow_show_feed_table` 中操作 `raw_request`，但后续如需在其它位置使用 DAR8 SP，可通过该 helper 复用逻辑。

- `views_pyqt.py`
  - `MainWindow._workflow_show_feed_table(self)`：
    - 通过“生成投料表”按钮打开 DAR8 SP 交互式对话框，集成了：
      - Request 详细信息展示；
      - SP 类型选择；
      - DAR8 输入表单；
      - 两列 SP 结果表格；
      - 点击单元格后的依赖高亮与计算过程说明。

---

### 数据分层与来源

DAR8 SP 中的数据大致分为四类：

1. **Request 输入字段（source = `request` / `derived`，group = `input_request`）**
   - 直接来自导入的偶联任务 Request，例如：
     - `antibody_conc_mg_ml` ← `"Antibody concention (mg/mL)"`；
     - `reaction_scale_mg` ← `"Reaction Scale (mg)"`；
     - `mw_antibody_da` ← `"MW of antibody (Da)"`；
     - `dissolved_in` ← `"Dissolved in"`；
     - `lp_conc_str` ← `"LP浓度"` 原始字符串；
     - `wbp_code` ← `"WBP Code"`；
     - `request_id` ← `"ID"`。
   - 以及由 Request 解析出的派生输入：
     - `lp_conc_mM`：由 `lp_conc_str` 前导数字解析出的 LP 浓度数值（单位 mM）。

2. **用户输入字段（source = `user_input`，group = `input_user`）**
   - 实验员在 UI 中手动填写的参数，例如：
     - `tcep_eq`（TCEP 当量，默认 `8.0`）；
     - `tcep_stock_mM`（TCEP stock 浓度，默认 `8.0`）；
     - `conj_org_ratio_percent`（Conjugation organic solvent ratio (%)，输入 0–100%，内部换算为 0–1 小数）；
     - `x_lp_per_ab`（x LP/Ab，当量比，默认 `12.0`）；
     - 可选输入：
       - `add_additional_tcep_eq`（额外 TCEP 当量）；
       - `add_additional_lp`（额外 LP）；
       - `additional_reaction_time_h`（额外反应时间）；
     - `reaction_status`（clear / cloudy / precipitate，实验员主观判断）。

3. **计算输出字段（source = `derived`，group = `output_reduction` / `output_conjugation`）**
   - 根据 Request 输入与用户输入，通过给定公式计算得到的中间量与结果：
     - Reduction 部分：
       - `add_antibody_ml`，`add_tcep_ml`，`add_buffer_ml`，`add_edta_ml`；
       - `mab_conc_reduction_mg_ml`，`reduction_total_volume_ml`；
       - `add_additional_tcep_ml`（仅当存在额外 TCEP 输入时有值）。
     - Conjugation 部分：
       - `conj_org_ratio_percent_out`，`conj_org_ratio_unit`，`x_lp_per_ab_out`；
       - `conj_total_volume_ml`，`add_lp_stock_ml`，`add_org_solvent_ml`；
       - `conj_conc_mg_ml`；
       - `add_additional_lp_out`，`additional_reaction_time_h_out`。

4. **固定字段与元数据（source = `fixed` / `derived`，group = `output_*` / `meta`）**
   - 固定值：
     - `reduction_reaction_temperature_c` = 22°C，`reduction_reaction_time_h` = 18h；
     - `conj_reaction_temperature_c` = 22°C，`conj_reaction_time_h` = 18h。
   - 元数据：
     - `batch_no`：`WBP Code-YYmmddID`（YYmmdd 用当前日期），方便实验批号管理。

详细的字段列表、依赖关系与字段级公式请参见：  
`docs/sp_dar8_setup_param.md`（由 `sp_dar8.render_dar8_doc_markdown()` 自动生成）。

---

### 计算逻辑概览（DAR8）

以下为 DAR8 计算的大致流程（省略异常/None 处理细节）：

1. **输入解析与默认值补全**
   - 使用 `build_dar8_inputs_from_request(raw_request)` 将 Request 的原始键值对转换为内部键（如 `antibody_conc_mg_ml`）。
   - 用户输入字典 `user_inputs` 指定 / 覆盖：
     - `tcep_eq`、`tcep_stock_mM`、`conj_org_ratio_percent`、`x_lp_per_ab`；
     - 以及可选的 `add_additional_tcep_eq`、`add_additional_lp`、`additional_reaction_time_h`、`reaction_status`。
   - 内部计算使用：
     - `ratio_fraction = conj_org_ratio_percent / 100.0`。

2. **基础体积计算（Reduction 部分）**
   - `add_antibody_ml = Reaction Scale (mg) / Antibody concention (mg/mL)`。
   - `add_tcep_ml = Reaction Scale (mg) / MW of antibody(Da) * TCEP eq / TCEP stock(mM) * 1000`。

3. **mAb 浓度与 Reduction 总体积**
   - 根据你确认的逻辑：
     - 若 `Antibody concention < 11.5`：
       - `mab_conc_reduction_mg_ml = Add antibody (mL) + Add 200mM EDTA (mL) + Add TCEP (mL)`（约定量纲），
         其中 `Add 200mM EDTA` 稍后通过 `0.01 * (Add antibody + Add TCEP + Add buffer)` 计算后再回填；
     - 否则：
       - `mab_conc_reduction_mg_ml = 10.0`。
   - `reduction_total_volume_ml = Reaction Scale (mg) / mAb conc. in reaction (mg/mL)`。

4. **Buffer 与 EDTA**
   - `Add buffer to adjust Ab conc.`：  
     - 若 `Antibody concention < 11.5`：`0.0`；  
     - 否则：  
       `Add buffer = Reduction Total volume - Add antibody - Add TCEP - Reduction Total volume * 0.01`  
       （将原文中的 `Total volume` 视为 `Reduction Total volume`）。
   - `Add 200mM EDTA = 0.01 * (Add antibody + Add TCEP + Add buffer)`。
   - 在 `Antibody concention < 11.5` 情形下，使用计算出的 `Add EDTA` 补全 `mab_conc_reduction_mg_ml`。

5. **额外 TCEP**
   - 若存在 `add_additional_tcep_eq`：
     - `add_additional_tcep_ml = Reaction Scale / MW of antibody * add_additional_tcep_eq / TCEP stock * 1000`。

6. **Conjugation 部分**
   - `conj_total_volume_ml = Reduction Total volume / (1 - ratio_fraction)`。
   - `add_lp_stock_ml = Reaction Scale / MW of antibody * x LP/Ab / LP浓度(mM) * 1000`（需 LP 浓度数值有效）。  
   - `add_org_solvent_ml = Conjugation Total volume * ratio_fraction - Add stock LP solution`。  
   - `conj_conc_mg_ml = Reaction Scale / Conjugation Total volume`。  
   - 输出字段 `conj_org_ratio_percent_out`、`conj_org_ratio_unit`、`x_lp_per_ab_out` 直接拷贝相应输入。
   - 若存在 `add_additional_lp`、`additional_reaction_time_h`，则对应输出字段直接复制输入值。

所有计算过程中，若任一关键上游参数缺失或无法转换为数值，相关结果字段会设为 `None`，并在 UI 中以 `N/A` 展示。

---

### PyQt 界面与交互设计

入口：  
在 ADC 实验流程 tab 中选中某条 workflow 后，点击右侧的“生成投料表”按钮，会打开一个 `QDialog`，由 `MainWindow._workflow_show_feed_table` 构建界面。

#### 布局结构（自上而下 / 自左而右）

1. **顶部摘要行**
   - 显示关键信息：
     - `Request SN`、`WBP Code`、`Product ID`。

2. **中部三列布局（`QHBoxLayout`）**

   - **左列：Request 详细信息**
     - `QTableWidget`，4 列：
       - `字段名`、`类型`、`必填/可选`、`值`。
     - 数据来源：
       - 调用 `ordered_request_items_for_display(raw_request)`，与 ADC 实验流程 tab 中的 Request 表一致。
     - 显示风格：
       - 文字居中。
       - 值为 `"null"` 时使用灰色斜体字体，提示该字段在 Request 中为空。

   - **中列：SP 类型选择 + DAR8 输入**
     - SP 类型：
       - `QComboBox`，选项：`DAR8`、`DAR4`、`Deblocking`、`Thiomab`。  
       - 目前仅实现 DAR8；其他类型时中列控件与右列结果表整体置灰，并在说明区提示“当前仅支持 DAR8 类型的 Setup Param 计算”。
     - DAR8 输入区（`QGroupBox("DAR8 Setup Param 输入") + QGridLayout`）：
       - 数值输入（`QDoubleSpinBox`）：
         - `TCEP 当量`（默认 8.0）；
         - `TCEP stock (mM)`（默认 8.0）；
         - `Conjugation organic solvent ratio (%)`（范围 0–100，步长 1，默认 0）；
         - `x LP/Ab`（默认 12.0）。
       - 可选输入（`QCheckBox + QDoubleSpinBox`）：
         - `Add additional TCEP (eq)`；
         - `Add additional LP`；
         - `Additional reaction time (h)`；
         - 勾选时启用数值输入，否则视为 `None`。
       - `Reaction status`：
         - `QComboBox`，选项：`""`、`clear`、`cloudy`、`precipitate`。
       - “重新计算 DAR8 参数”按钮：
         - 点击后收集所有当前值，构造 `user_inputs` 并调用 `sp_dar8.calculate_dar8_sp(raw_request, user_inputs)`。
         - 刷新右侧结果表和说明文本。
       - 窗口打开时会自动执行一次计算，以 Request + 默认输入生成初始结果。

   - **右列：SP 结果表 + 计算说明**
     - 结果表（`QTableWidget`）：
       - 两列：“名称”“数值”，行顺序按 `group + display_name` 排序。
       - 第一列展示字段名（带单位），并在 `Qt.UserRole` 中存储内部 `field_key`，方便后续查 meta。
       - 数值列：
         - 对 `float` / `optional_float` 字段，使用 `format_number` 格式化，`None` 显示为 `N/A`；
         - 其他类型按字符串展示。
       - 对 `is_important=True` 的字段（如 `Add antibody`、`Add buffer`、`Add 200mM EDTA`、`Add TCEP`）使用淡黄色背景，增强可视化提示。
     - 计算说明区域：
       - `QTextEdit` 只读，用于在点击结果表单元格后展示计算过程。

3. **底部按钮行**
   - `QDialogButtonBox(QDialogButtonBox.Close)`，用于关闭对话框。

#### 单元格点击：依赖高亮与计算过程说明

1. **文字说明生成**
   - 结果表连接 `cellClicked(row, column)` 信号：
     - 根据被点击行第一列的 `UserRole` 取得 `field_key`；
     - 从 `dar8_meta` 与当前的 `SetupParamCalculationResult` 中获取对应字段元数据与值；
     - 在说明区按以下格式输出：
       - 字段名称 + 单位；
       - 当前值；
       - 数据来源（request / user_input / derived / fixed）；
       - 字段说明文本（`description`）；
       - 公式描述（`formula_text`）；
       - 若存在 `depends_on`：
         - 分行列出每个依赖字段的名称、单位与当前值，方便理解计算链路；
       - 若无 `depends_on`：
         - 明确说明“该字段为原始输入或固定值，无上游依赖”。

2. **依赖高亮策略**
   - 在每次点击时：
     - 先将整个结果表背景重置为白色，再重新为所有 `is_important` 字段行恢复淡黄色背景；
     - 对当前选中字段所在行设置淡绿色背景，表示“当前关注字段”；
     - 对 `depends_on` 中的每个字段所在行设置淡蓝色背景，表示“参与当前字段计算的上游字段”。
   - 这样实验员可以非常直观地看到**一个参数是由哪些其它值推导而来**。

---

### 与现有功能的关系与扩展

- 与原有 Request 展示的关系：
  - ADC 实验流程 tab 中已有 Request 详细信息表格，`_workflow_show_feed_table` 的左列在逻辑与样式上复用同一套数据源（`ordered_request_items_for_display`），确保体验一致。
- 与纯化步骤列表的关系：
  - 当前 SP 抽象独立于纯化步骤类型（如 Zeba/Amicon/G25 等），位于 Request 与步骤之间，用于生成更“实验员友好”的投料参数。
  - 后续如需将 SP 参数持久化到数据库，可在 `adc_workflow_step.params_json` 中增加对 SP 结果的引用。

#### 扩展到 DAR4 / Deblocking / Thiomab 的建议

1. 在 `sp_core.py` 之上，为每种 SP 类型新建类似 `sp_dar8.py` 的模块（如 `sp_dar4.py`），定义各自的：
   - `*_FIELDS` 元数据列表；
   - `build_*_inputs_from_request` 与 `calculate_*_sp`。
2. 在 `sp_core.py` 或单独的工厂模块中提供：
   - `get_sp_definition(sp_type: str)`：返回对应的 `FIELDS` 与计算入口。
3. 在 `views_pyqt.py` 中：
   - 将 DAR8 特有逻辑抽象为按 `sp_type` 分派：
     - `sp_type = sp_type_combo.currentText()`；
     - 根据 `sp_type` 切换不同的输入区与计算入口；
     - 结果表与说明区可以复用当前的单元格点击与高亮逻辑（依赖于 `depends_on` 与 `formula_text` 元数据）。

通过以上设计，DAR8 SP 的实现不仅满足当前实验需求，同时也为后续扩展到其它 SP 类型提供了统一的接口与清晰的结构基础。

