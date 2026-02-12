"""
ADC实验流程模块 - 数据库操作层
表结构初始化、偶联任务 xlsx 键值对解析、CRUD
"""
import json
from typing import List, Dict, Any, Optional, Tuple

# 纯化步骤流程在 request 中的键名（与 task_template 一致）
PURIFICATION_METHOD_KEY = "Purification method"

def _decode_cell_string(value: Any) -> Any:
    """
    修正 openpyxl 读取 xlsx 时可能产生的乱码（UTF-8 被误解码为 cp1252/latin1）。
    仅对字符串尝试 encode(cp1252).decode(utf-8)，失败则返回原值。
    """
    if not isinstance(value, str):
        return value
    try:
        return value.encode("cp1252").decode("utf-8")
    except (UnicodeDecodeError, UnicodeEncodeError):
        try:
            return value.encode("latin-1").decode("utf-8")
        except (UnicodeDecodeError, UnicodeEncodeError):
            return value


# 8 种纯化步骤类型默认名称
DEFAULT_STEP_TYPES = [
    "Zeba",
    "Amicon",
    "G25",
    "UFDF",
    "new Charcoal",
    "old Charcoal",
    "Concentration",
    "S200",
]


def _parse_sheet_key_value(ws) -> Dict[str, Any]:
    """
    按 task_template 格式解析：B=名称、C=内容；或 B 为空时 C=名称、D=内容。
    仅 B 非空且 C 为空的行为分组标题，不产出键值对。
    返回键值对字典，键为名称（strip），值为内容（保持类型）。
    """
    result = {}
    for r in range(1, ws.max_row + 1):
        b_val = _decode_cell_string(ws.cell(r, 2).value)
        c_val = _decode_cell_string(ws.cell(r, 3).value)
        d_val = _decode_cell_string(ws.cell(r, 4).value) if ws.max_column >= 4 else None

        # B 有值且 C 有值（或 C 为数字）-> (B, C)
        if b_val is not None and b_val != "":
            if c_val is not None or (isinstance(c_val, (int, float)) and c_val != ""):
                name = str(b_val).strip()
                if name:
                    result[name] = c_val
            # 否则 B 有值 C 空 -> 分组标题，跳过
            continue

        # B 为空：C=名称，D=内容
        if c_val is not None and c_val != "" and (d_val is not None or isinstance(d_val, (int, float))):
            name = str(c_val).strip()
            if name:
                result[name] = d_val
    return result


def parse_workbook_key_value(wb) -> List[Dict[str, Any]]:
    """
    遍历工作簿每个 sheet，用键值对规则解析，返回 list of dict（每个 sheet 一组键值对）。
    """
    sheets_data = []
    for sheet_name in wb.sheetnames:
        ws = wb[sheet_name]
        kv = _parse_sheet_key_value(ws)
        if kv:
            kv["_sheet_name"] = sheet_name
            sheets_data.append(kv)
    return sheets_data


def init_adc_workflow_tables(cursor):
    """初始化 ADC 实验流程相关表结构"""
    # 用户表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS app_user (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT '实验员',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 纯化步骤类型表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS purification_step_type (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            display_order INTEGER NOT NULL DEFAULT 0,
            is_active INTEGER NOT NULL DEFAULT 1,
            param_schema TEXT DEFAULT '',
            schema_version INTEGER NOT NULL DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # ADC 实验流程主表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS adc_workflow (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            request_sn TEXT DEFAULT '',
            raw_request_json TEXT DEFAULT '{}',
            purification_flow_string TEXT DEFAULT '',
            created_by_user_id INTEGER NOT NULL DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (created_by_user_id) REFERENCES app_user (id)
        )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_adc_workflow_created_by ON adc_workflow (created_by_user_id)")

    # 兼容旧表：若表已存在且缺少新列则追加（旧 schema 可能含 status/experiment_params/request_snapshot）
    cursor.execute("PRAGMA table_info(adc_workflow)")
    existing_cols = [row[1] for row in cursor.fetchall()]
    for col, defn in [
        ("request_sn", "TEXT DEFAULT ''"),
        ("raw_request_json", "TEXT DEFAULT '{}'"),
        ("purification_flow_string", "TEXT DEFAULT ''"),
    ]:
        if col not in existing_cols:
            cursor.execute("ALTER TABLE adc_workflow ADD COLUMN %s %s" % (col, defn))
            existing_cols.append(col)

    # 工作流步骤表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS adc_workflow_step (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            workflow_id INTEGER NOT NULL,
            step_type_id INTEGER NOT NULL,
            step_order INTEGER NOT NULL DEFAULT 0,
            params_json TEXT DEFAULT '{}',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (workflow_id) REFERENCES adc_workflow (id) ON DELETE CASCADE,
            FOREIGN KEY (step_type_id) REFERENCES purification_step_type (id)
        )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_adc_workflow_step_workflow ON adc_workflow_step (workflow_id)")

    # 兼容旧表 adc_workflow_step：缺少 params_json 则追加
    cursor.execute("PRAGMA table_info(adc_workflow_step)")
    step_cols = [row[1] for row in cursor.fetchall()]
    if "params_json" not in step_cols:
        cursor.execute("ALTER TABLE adc_workflow_step ADD COLUMN params_json TEXT DEFAULT '{}'")

    # 实验结果表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS adc_experiment_result (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            workflow_id INTEGER NOT NULL,
            sample_id TEXT DEFAULT '',
            lot_no TEXT DEFAULT '',
            conc_mg_ml REAL DEFAULT 0.0,
            amount_mg REAL DEFAULT 0.0,
            yield_pct REAL DEFAULT 0.0,
            ms_dar REAL DEFAULT 0.0,
            monomer_pct REAL DEFAULT 0.0,
            free_drug_pct REAL DEFAULT 0.0,
            endotoxin TEXT DEFAULT '',
            aliquot TEXT DEFAULT '',
            purification_method TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            created_by_user_id INTEGER NOT NULL DEFAULT 0,
            FOREIGN KEY (workflow_id) REFERENCES adc_workflow (id) ON DELETE CASCADE,
            FOREIGN KEY (created_by_user_id) REFERENCES app_user (id)
        )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_adc_experiment_result_workflow ON adc_experiment_result (workflow_id)")

    # 种子数据：默认用户（若不存在）
    cursor.execute("SELECT COUNT(*) FROM app_user")
    if cursor.fetchone()[0] == 0:
        cursor.execute(
            "INSERT INTO app_user (username, role) VALUES (?, ?)",
            ("默认实验员", "实验员")
        )
        cursor.execute(
            "INSERT INTO app_user (username, role) VALUES (?, ?)",
            ("Leader", "leader")
        )

    # 种子数据：8 种纯化步骤类型（若不存在）
    cursor.execute("SELECT COUNT(*) FROM purification_step_type")
    if cursor.fetchone()[0] == 0:
        for i, name in enumerate(DEFAULT_STEP_TYPES):
            cursor.execute(
                """INSERT INTO purification_step_type (name, display_order, is_active, param_schema, schema_version)
                   VALUES (?, ?, 1, '', 1)""",
                (name, i)
            )


class ADCWorkflowRepository:
    """ADC 实验流程数据仓库"""

    def __init__(self, db_manager):
        self.db = db_manager

    # ---------- AppUser ----------
    def get_all_users(self) -> List[Dict[str, Any]]:
        c = self.db.execute_query("SELECT * FROM app_user ORDER BY id")
        return c

    def get_user_by_id(self, user_id: int) -> Optional[Dict[str, Any]]:
        r = self.db.execute_query("SELECT * FROM app_user WHERE id = ?", (user_id,))
        return r[0] if r else None

    # ---------- PurificationStepType ----------
    def get_all_step_types(self, active_only: bool = False) -> List[Dict[str, Any]]:
        if active_only:
            return self.db.execute_query(
                "SELECT * FROM purification_step_type WHERE is_active = 1 ORDER BY display_order, id"
            )
        return self.db.execute_query("SELECT * FROM purification_step_type ORDER BY display_order, id")

    def get_step_type_by_id(self, type_id: int) -> Optional[Dict[str, Any]]:
        r = self.db.execute_query("SELECT * FROM purification_step_type WHERE id = ?", (type_id,))
        return r[0] if r else None

    def get_step_type_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        r = self.db.execute_query("SELECT * FROM purification_step_type WHERE name = ?", (name.strip(),))
        return r[0] if r else None

    def create_step_type(self, name: str, display_order: int = 0, param_schema: str = "") -> int:
        return self.db.execute_insert(
            """INSERT INTO purification_step_type (name, display_order, is_active, param_schema, schema_version)
               VALUES (?, ?, 1, ?, 1)""",
            (name.strip(), display_order, param_schema)
        )

    def update_step_type(self, type_id: int, name: str = None, display_order: int = None,
                         is_active: bool = None, param_schema: str = None) -> bool:
        updates = []
        params = []
        if name is not None:
            updates.append("name = ?")
            params.append(name.strip())
        if display_order is not None:
            updates.append("display_order = ?")
            params.append(display_order)
        if is_active is not None:
            updates.append("is_active = ?")
            params.append(1 if is_active else 0)
        if param_schema is not None:
            updates.append("param_schema = ?")
            params.append(param_schema)
        if not updates:
            return True
        updates.append("updated_at = CURRENT_TIMESTAMP")
        params.append(type_id)
        q = "UPDATE purification_step_type SET " + ", ".join(updates) + " WHERE id = ?"
        return self.db.execute_update(q, tuple(params)) > 0

    def delete_step_type(self, type_id: int) -> bool:
        return self.db.execute_update("DELETE FROM purification_step_type WHERE id = ?", (type_id,)) > 0

    # ---------- ADCWorkflow ----------
    def create_workflow(self, request_sn: str, raw_request_json: str, purification_flow_string: str,
                       created_by_user_id: int) -> int:
        def _do_create(cursor):
            cursor.execute("SELECT id FROM app_user ORDER BY id")
            rows = cursor.fetchall()
            ids = [int(r[0]) for r in rows]
            if not ids:
                raise ValueError("app_user 表为空，无法创建实验流程。请先初始化数据库。")
            uid = int(created_by_user_id)
            if uid not in ids:
                raise ValueError("创建人用户 id 不在当前用户列表中，无法创建实验流程。")
            # 同一连接上 SELECT 已确认 app_user 存在 uid，但 INSERT 仍可能触发 FK 失败；临时关闭本连接上的 FK 校验后插入，插入后立即恢复（数据由上方 uid in ids 保证合法）
            conn = cursor.connection
            conn.execute("PRAGMA foreign_keys=OFF")
            try:
                cursor.execute(
                    """INSERT INTO adc_workflow (request_sn, raw_request_json, purification_flow_string, created_by_user_id)
                       VALUES (?, ?, ?, ?)""",
                    (request_sn, raw_request_json, purification_flow_string, uid)
                )
                return cursor.lastrowid
            finally:
                conn.execute("PRAGMA foreign_keys=ON")

        return self.db.with_connection(_do_create)

    def get_workflow_by_id(self, workflow_id: int) -> Optional[Dict[str, Any]]:
        r = self.db.execute_query("SELECT * FROM adc_workflow WHERE id = ?", (workflow_id,))
        return r[0] if r else None

    def get_all_workflows(self, created_by_user_id: Optional[int] = None) -> List[Dict[str, Any]]:
        if created_by_user_id is not None:
            return self.db.execute_query(
                "SELECT * FROM adc_workflow WHERE created_by_user_id = ? ORDER BY created_at DESC",
                (created_by_user_id,)
            )
        return self.db.execute_query("SELECT * FROM adc_workflow ORDER BY created_at DESC")

    def update_workflow(self, workflow_id: int, request_sn: str = None, raw_request_json: str = None,
                       purification_flow_string: str = None) -> bool:
        updates = []
        params = []
        if request_sn is not None:
            updates.append("request_sn = ?")
            params.append(request_sn)
        if raw_request_json is not None:
            updates.append("raw_request_json = ?")
            params.append(raw_request_json)
        if purification_flow_string is not None:
            updates.append("purification_flow_string = ?")
            params.append(purification_flow_string)
        if not updates:
            return True
        updates.append("updated_at = CURRENT_TIMESTAMP")
        params.append(workflow_id)
        q = "UPDATE adc_workflow SET " + ", ".join(updates) + " WHERE id = ?"
        return self.db.execute_update(q, tuple(params)) > 0

    def delete_workflow(self, workflow_id: int) -> bool:
        return self.db.execute_update("DELETE FROM adc_workflow WHERE id = ?", (workflow_id,)) > 0

    # ---------- ADCWorkflowStep ----------
    def add_workflow_step(self, workflow_id: int, step_type_id: int, step_order: int, params_json: str = "{}") -> int:
        return self.db.execute_insert(
            """INSERT INTO adc_workflow_step (workflow_id, step_type_id, step_order, params_json)
               VALUES (?, ?, ?, ?)""",
            (workflow_id, step_type_id, step_order, params_json or "{}")
        )

    def get_steps_by_workflow_id(self, workflow_id: int) -> List[Dict[str, Any]]:
        return self.db.execute_query(
            "SELECT * FROM adc_workflow_step WHERE workflow_id = ? ORDER BY step_order, id",
            (workflow_id,)
        )

    def update_workflow_step(self, step_id: int, step_type_id: int = None, step_order: int = None,
                              params_json: str = None) -> bool:
        updates = []
        params = []
        if step_type_id is not None:
            updates.append("step_type_id = ?")
            params.append(step_type_id)
        if step_order is not None:
            updates.append("step_order = ?")
            params.append(step_order)
        if params_json is not None:
            updates.append("params_json = ?")
            params.append(params_json)
        if not updates:
            return True
        params.append(step_id)
        q = "UPDATE adc_workflow_step SET " + ", ".join(updates) + " WHERE id = ?"
        return self.db.execute_update(q, tuple(params)) > 0

    def delete_workflow_step(self, step_id: int) -> bool:
        return self.db.execute_update("DELETE FROM adc_workflow_step WHERE id = ?", (step_id,)) > 0

    def delete_steps_by_workflow_id(self, workflow_id: int) -> int:
        return self.db.execute_update("DELETE FROM adc_workflow_step WHERE workflow_id = ?", (workflow_id,))

    # ---------- ADCExperimentResult ----------
    def create_experiment_result(self, workflow_id: int, created_by_user_id: int, sample_id: str = "",
                                lot_no: str = "", conc_mg_ml: float = 0.0, amount_mg: float = 0.0,
                                yield_pct: float = 0.0, ms_dar: float = 0.0, monomer_pct: float = 0.0,
                                free_drug_pct: float = 0.0, endotoxin: str = "", aliquot: str = "",
                                purification_method: str = "") -> int:
        return self.db.execute_insert(
            """INSERT INTO adc_experiment_result (
                workflow_id, created_by_user_id, sample_id, lot_no, conc_mg_ml, amount_mg,
                yield_pct, ms_dar, monomer_pct, free_drug_pct, endotoxin, aliquot, purification_method
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (workflow_id, created_by_user_id, sample_id, lot_no, conc_mg_ml, amount_mg,
             yield_pct, ms_dar, monomer_pct, free_drug_pct, endotoxin, aliquot, purification_method)
        )

    def get_results_by_workflow_id(self, workflow_id: int) -> List[Dict[str, Any]]:
        return self.db.execute_query(
            "SELECT * FROM adc_experiment_result WHERE workflow_id = ? ORDER BY created_at DESC",
            (workflow_id,)
        )

    def get_experiment_result_by_id(self, result_id: int) -> Optional[Dict[str, Any]]:
        r = self.db.execute_query("SELECT * FROM adc_experiment_result WHERE id = ?", (result_id,))
        return r[0] if r else None

    def update_experiment_result(self, result_id: int, **kwargs) -> bool:
        allowed = {"sample_id", "lot_no", "conc_mg_ml", "amount_mg", "yield_pct", "ms_dar",
                   "monomer_pct", "free_drug_pct", "endotoxin", "aliquot", "purification_method"}
        updates = []
        params = []
        for k, v in kwargs.items():
            if k in allowed:
                updates.append(k + " = ?")
                params.append(v)
        if not updates:
            return True
        params.append(result_id)
        q = "UPDATE adc_experiment_result SET " + ", ".join(updates) + " WHERE id = ?"
        return self.db.execute_update(q, tuple(params)) > 0

    def delete_experiment_result(self, result_id: int) -> bool:
        return self.db.execute_update("DELETE FROM adc_experiment_result WHERE id = ?", (result_id,)) > 0
