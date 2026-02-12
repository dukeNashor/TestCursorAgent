"""
ADC实验流程模块 - 控制器层
导入 xlsx、工作流/步骤/实验结果 CRUD、权限判断、投料表数据生成
"""
import json
from typing import List, Optional, Dict, Any, Tuple

from .models import (
    AppUser,
    PurificationStepType,
    ADCWorkflow,
    ADCWorkflowStep,
    ADCExperimentResult,
    ROLE_LEADER,
)
from .repository import (
    ADCWorkflowRepository,
    parse_workbook_key_value,
    PURIFICATION_METHOD_KEY,
)
from .request_schema import ordered_request_items, coerce_request_values
from . import sp_dar8


class ADCWorkflowController:
    """ADC 实验流程控制器"""

    def __init__(self, db_manager):
        self.db = db_manager
        self.repo = ADCWorkflowRepository(db_manager)

    def get_all_users(self) -> List[AppUser]:
        rows = self.repo.get_all_users()
        return [AppUser.from_dict(r) for r in rows]

    def get_user_by_id(self, user_id: int) -> Optional[AppUser]:
        r = self.repo.get_user_by_id(user_id)
        return AppUser.from_dict(r) if r else None

    def get_all_step_types(self, active_only: bool = True) -> List[PurificationStepType]:
        rows = self.repo.get_all_step_types(active_only=active_only)
        return [PurificationStepType.from_dict(r) for r in rows]

    def get_step_type_by_name(self, name: str) -> Optional[PurificationStepType]:
        r = self.repo.get_step_type_by_name(name)
        return PurificationStepType.from_dict(r) if r else None

    def can_edit_workflow(self, workflow: ADCWorkflow, current_user_id: int, current_user_role: str) -> bool:
        """实验员只能编辑自己的，leader 可编辑全部"""
        if current_user_role == ROLE_LEADER:
            return True
        return workflow.created_by_user_id == current_user_id

    def can_delete_workflow(self, workflow: ADCWorkflow, current_user_id: int, current_user_role: str) -> bool:
        return self.can_edit_workflow(workflow, current_user_id, current_user_role)

    def can_create_workflow(self, user_id: Optional[int], current_user_role: str) -> bool:
        """实验员与 leader 均可创建偶联任务（leader 权限为实验员超集）。只要当前用户有效即允许创建。"""
        return user_id is not None

    def get_workflows_for_user(self, current_user_id: int, current_user_role: str) -> List[ADCWorkflow]:
        """实验员只看自己的，leader 看全部"""
        if current_user_role == ROLE_LEADER:
            rows = self.repo.get_all_workflows()
        else:
            rows = self.repo.get_all_workflows(created_by_user_id=current_user_id)
        out = []
        for r in rows:
            w = ADCWorkflow.from_dict(r)
            w.steps = [ADCWorkflowStep.from_dict(s) for s in self.repo.get_steps_by_workflow_id(w.id)]
            out.append(w)
        return out

    def get_workflow_by_id(self, workflow_id: int) -> Optional[ADCWorkflow]:
        r = self.repo.get_workflow_by_id(workflow_id)
        if not r:
            return None
        w = ADCWorkflow.from_dict(r)
        w.steps = [ADCWorkflowStep.from_dict(s) for s in self.repo.get_steps_by_workflow_id(w.id)]
        return w

    def import_task_xlsx(self, xlsx_path: str, created_by_user_id: int) -> Tuple[bool, str, List[int]]:
        """
        导入偶联任务 xlsx。按 sheet 键值对解析，每个 sheet 创建一条 workflow。
        返回 (成功与否, 消息, 新建的 workflow id 列表)。
        """
        try:
            import openpyxl
            wb = openpyxl.load_workbook(xlsx_path, data_only=True)
        except Exception as e:
            return False, f"打开文件失败: {e}", []

        try:
            sheets_data = parse_workbook_key_value(wb)
        finally:
            wb.close()

        if not sheets_data:
            return False, "未解析到任何有效数据（请确认文件为 B/C 或 C/D 键值对格式）", []

        created_ids = []
        for kv in sheets_data:
            sheet_name = kv.pop("_sheet_name", "")
            coerced = coerce_request_values(kv)
            raw_json = json.dumps(coerced, ensure_ascii=False)
            purification_flow = coerced.get(PURIFICATION_METHOD_KEY) or coerced.get("Purification method")
            if not isinstance(purification_flow, str):
                purification_flow = str(purification_flow).strip() if purification_flow is not None else ""
            else:
                purification_flow = purification_flow.strip()
            request_sn = coerced.get("Product ID") or sheet_name or str(len(created_ids) + 1)
            if isinstance(request_sn, (int, float)):
                request_sn = str(int(request_sn))
            else:
                request_sn = str(request_sn).strip() if request_sn else ""

            try:
                wf_id = self.repo.create_workflow(
                    request_sn=request_sn,
                    raw_request_json=raw_json,
                    purification_flow_string=purification_flow,
                    created_by_user_id=created_by_user_id,
                )
            except ValueError as e:
                return False, str(e), created_ids
            created_ids.append(wf_id)

            # 解析纯化步骤流程 "Zeba+Amicon" -> 按顺序创建 step
            if purification_flow:
                step_names = [s.strip() for s in purification_flow.split("+") if s.strip()]
                type_name_to_id = {}
                for t in self.repo.get_all_step_types(active_only=False):
                    type_name_to_id[t["name"]] = t["id"]
                for order, name in enumerate(step_names):
                    type_row = self.repo.get_step_type_by_name(name)
                    if type_row:
                        self.repo.add_workflow_step(wf_id, type_row["id"], order, "{}")

        return True, f"成功导入 {len(created_ids)} 条实验流程", created_ids

    def update_workflow_steps(self, workflow_id: int, step_type_names: List[str]) -> bool:
        """用步骤类型名称列表覆盖该 workflow 的步骤（先删后加）"""
        self.repo.delete_steps_by_workflow_id(workflow_id)
        type_name_to_id = {t["name"]: t["id"] for t in self.repo.get_all_step_types(active_only=False)}
        for order, name in enumerate(step_type_names):
            name = name.strip()
            if not name:
                continue
            tid = type_name_to_id.get(name)
            if tid is not None:
                self.repo.add_workflow_step(workflow_id, tid, order, "{}")
        return True

    def update_workflow_purification_string(self, workflow_id: int, purification_flow_string: str) -> bool:
        return self.repo.update_workflow(workflow_id, purification_flow_string=purification_flow_string)

    def delete_workflow(self, workflow_id: int) -> bool:
        return self.repo.delete_workflow(workflow_id)

    def get_feed_table_data(self, workflow_id: int) -> Optional[Dict[str, Any]]:
        """生成投料表所需数据：request 键值对 + 步骤列表（含类型名）"""
        w = self.get_workflow_by_id(workflow_id)
        if not w:
            return None
        try:
            raw = json.loads(w.raw_request_json) if w.raw_request_json else {}
        except Exception:
            raw = {}
        type_id_to_name = {t["id"]: t["name"] for t in self.repo.get_all_step_types(active_only=False)}
        steps = []
        for s in w.steps:
            steps.append({
                "order": s.step_order,
                "type_name": type_id_to_name.get(s.step_type_id, ""),
                "params": json.loads(s.params_json) if s.params_json else {},
            })
        return {
            "workflow_id": w.id,
            "request_sn": w.request_sn,
            "raw_request": raw,
            "ordered_request": ordered_request_items(raw),
            "purification_flow_string": w.purification_flow_string,
            "steps": steps,
        }

    def get_dar8_request_inputs(self, workflow_id: int) -> Optional[Dict[str, Any]]:
        """
        便捷方法：从指定 workflow 中获取 DAR8 所需的 Request 输入上下文。

        返回字典中至少包含：
        - raw_request: 原始 Request 键值对
        - dar8_request_inputs: build_dar8_inputs_from_request 的结果
        """
        w = self.get_workflow_by_id(workflow_id)
        if not w:
            return None
        try:
            raw = json.loads(w.raw_request_json) if w.raw_request_json else {}
        except Exception:
            raw = {}
        dar8_inputs = sp_dar8.build_dar8_inputs_from_request(raw)
        return {
            "workflow_id": w.id,
            "request_sn": w.request_sn,
            "raw_request": raw,
            "dar8_request_inputs": dar8_inputs,
        }

    def add_experiment_result(self, workflow_id: int, created_by_user_id: int,
                              sample_id: str = "", lot_no: str = "", conc_mg_ml: float = 0.0,
                              amount_mg: float = 0.0, yield_pct: float = 0.0, ms_dar: float = 0.0,
                              monomer_pct: float = 0.0, free_drug_pct: float = 0.0,
                              endotoxin: str = "", aliquot: str = "", purification_method: str = "") -> int:
        return self.repo.create_experiment_result(
            workflow_id=workflow_id,
            created_by_user_id=created_by_user_id,
            sample_id=sample_id,
            lot_no=lot_no,
            conc_mg_ml=conc_mg_ml,
            amount_mg=amount_mg,
            yield_pct=yield_pct,
            ms_dar=ms_dar,
            monomer_pct=monomer_pct,
            free_drug_pct=free_drug_pct,
            endotoxin=endotoxin,
            aliquot=aliquot,
            purification_method=purification_method,
        )

    def get_experiment_results(self, workflow_id: int) -> List[ADCExperimentResult]:
        rows = self.repo.get_results_by_workflow_id(workflow_id)
        return [ADCExperimentResult.from_dict(r) for r in rows]

    def update_experiment_result(self, result_id: int, **kwargs) -> bool:
        return self.repo.update_experiment_result(result_id, **kwargs)

    def delete_experiment_result(self, result_id: int) -> bool:
        return self.repo.delete_experiment_result(result_id)
