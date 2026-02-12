# 偶联任务 Request Schema

与 `task_template.xlsx` 对应，用于 ADC 实验流程的 request 解析、展示与投料表。  
代码实现见 `adc_workflow/request_schema.py`。

## 类型定义

| 类型 | 说明 |
|------|------|
| string | 字符串 |
| number | 数值（int/float） |
| string \| null | 可选字符串，无内容可为 null |
| bool | 布尔；展示为 是/否，支持 1/0、Y/N、是/否、true/false |
| number \| null | 可选数值 |
| list of objects | 对象数组；ADC Target Quality 的每项含「检项」「特殊要求」 |

## 字段列表（按展示顺序）

### 通用/任务标识

| 键名 | 类型 | 可选 |
|------|------|------|
| 偶联scientist | string | 否 |
| WBP Code | string | 否 |
| Reaction Scale (mg) | number | 否 |
| Product ID | string | 否 |
| Batch# | string \| null | 是 |

### mAb information

| 键名 | 类型 | 可选 |
|------|------|------|
| Protein ID | string | 否 |
| Protein batch# | string | 否 |
| Protein isotype | string \| null | 是 |
| New Carrier | bool | 是 |
| MW of antibody (Da) | number | 否 |
| MW of LC (Da) | number | 是 |
| MW of HC (Da) | number | 是 |
| Ab extinction coeff | number | 否 |
| Calculated PI value | number | 否 |
| Buffer of Antibody | string | 否 |
| Antibody concention (mg/mL) | number | 否 |

### LP information

| 键名 | 类型 | 可选 |
|------|------|------|
| Linker Payload ID | string | 否 |
| LP Batch# | string | 是 |
| NEW LP | bool | 是 |
| Payload Type | string \| null | 是 |
| LP浓度 | string | 否 |
| MW of LP (Da) | number | 否 |
| Leaving group (Da) | number \| null | 是 |
| Dissolved in | string | 否 |
| 是否预约标曲 | bool | 是 |
| Connector | string | 否 |

### Conjugation/纯化与分装

| 键名 | 类型 | 可选 |
|------|------|------|
| Conjugation buffer | string | 是 |
| Purification method | string | 否 |
| Aliqout information | string | 否 |
| Comments | string \| null | 是 |
| ID | number | 是 |
| ADC Target Quality | string | 否 |

**ADC Target Quality** 为 string 类型，内容按 JSON 存储。JSON 格式为 list，list 中元素为相同结构的 object，每个 object 有两个成员：**检项**、**特殊要求**。
