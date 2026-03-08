
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

import pandas as pd
import matplotlib as mpl
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.ticker import PercentFormatter
from openpyxl import load_workbook
from openpyxl.utils.datetime import from_excel
from PyQt6.QtCore import QDate, Qt
from PyQt6.QtGui import QColor, QFont, QPalette
from PyQt6.QtWidgets import (
    QApplication,
    QComboBox,
    QDateEdit,
    QFileDialog,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

APP_TITLE = "实验室生产数据统计看板 (PyQt6)"

# 源表固定字段位置（A=1, AI=35）
COL_COUPLING_A = 0
COL_WBP_C = 2
COL_PRODUCT_D = 3
COL_RESEARCHER_E = 4
COL_START_AF = 31
COL_END_AG = 32
COL_SCORE_AI = 34


@dataclass
class FilterState:
    start_date: date
    end_date: date
    date_basis: str  # completion_priority / completion_date / start_date
    researcher: str
    wbp_code: str
    product_id: str
    saturation_threshold: int


class LabKPIDashboard(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.df_raw = pd.DataFrame()
        self.df_working = pd.DataFrame()
        self.chart_payloads: dict[str, Any] = {}

        self.setWindowTitle(APP_TITLE)
        self.resize(1520, 920)
        self._apply_palette()
        self._apply_stylesheet()
        self._configure_matplotlib_font()

        self._build_ui()
        self._auto_pick_default_file()

    @staticmethod
    def _configure_matplotlib_font() -> None:
        mpl.rcParams["font.sans-serif"] = [
            "Microsoft YaHei",
            "SimHei",
            "Segoe UI",
            "Arial Unicode MS",
            "DejaVu Sans",
        ]
        mpl.rcParams["axes.unicode_minus"] = False

    def _apply_palette(self) -> None:
        palette = QPalette()
        palette.setColor(QPalette.ColorRole.Window, QColor("#F3F7FF"))
        palette.setColor(QPalette.ColorRole.Base, QColor("#FFFFFF"))
        palette.setColor(QPalette.ColorRole.AlternateBase, QColor("#EFF6FF"))
        palette.setColor(QPalette.ColorRole.Text, QColor("#133047"))
        palette.setColor(QPalette.ColorRole.ButtonText, QColor("#133047"))
        palette.setColor(QPalette.ColorRole.Highlight, QColor("#0EA5E9"))
        palette.setColor(QPalette.ColorRole.HighlightedText, QColor("#FFFFFF"))
        self.setPalette(palette)

    def _apply_stylesheet(self) -> None:
        self.setStyleSheet(
            """
            QWidget {
                font-family: 'Segoe UI', 'Microsoft YaHei UI', sans-serif;
                font-size: 13px;
                color: #16324f;
                background: #f4f8ff;
            }
            QMainWindow {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #f7fbff, stop:0.55 #edf5ff, stop:1 #e7f3ff);
            }
            QLabel#heroTitle {
                font-size: 30px;
                font-weight: 700;
                letter-spacing: 1px;
                color: #0f2f4a;
            }
            QLabel#heroSub {
                color: #476b89;
                font-size: 13px;
            }
            QLabel#chartTitle {
                font-size: 16px;
                font-weight: 700;
                color: #14466c;
                padding: 0 0 4px 0;
            }
            QFrame#card, QGroupBox {
                background: rgba(255, 255, 255, 0.94);
                border: 1px solid #d4e7fb;
                border-radius: 14px;
            }
            QGroupBox {
                margin-top: 10px;
                padding-top: 12px;
                font-weight: 600;
                color: #1a4668;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 6px;
            }
            QLineEdit, QComboBox, QDateEdit, QSpinBox {
                border: 1px solid #bfdcf8;
                border-radius: 8px;
                padding: 6px 10px;
                background: #ffffff;
                min-height: 30px;
            }
            QLineEdit:focus, QComboBox:focus, QDateEdit:focus, QSpinBox:focus {
                border: 2px solid #2ea6ff;
            }
            QPushButton {
                border: 0;
                border-radius: 10px;
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #06b6d4, stop:1 #3b82f6);
                color: white;
                font-weight: 600;
                padding: 8px 14px;
                min-height: 34px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #0891b2, stop:1 #2563eb);
            }
            QPushButton:pressed {
                background: #1d4ed8;
            }
            QTabWidget::pane {
                border: 1px solid #d4e7fb;
                border-radius: 12px;
                background: rgba(255, 255, 255, 0.95);
                top: -1px;
            }
            QTabBar::tab {
                background: #e8f3ff;
                border: 1px solid #cde4fb;
                border-bottom: none;
                border-top-left-radius: 10px;
                border-top-right-radius: 10px;
                padding: 8px 14px;
                margin-right: 4px;
                color: #2b5a80;
                font-weight: 600;
            }
            QTabBar::tab:selected {
                background: #ffffff;
                color: #0d4266;
                border-color: #9fd0fa;
            }
            QTableWidget {
                background: white;
                border: 1px solid #d4e7fb;
                border-radius: 10px;
                gridline-color: #e5f0fb;
                selection-background-color: #d8efff;
                selection-color: #113350;
                alternate-background-color: #f6fbff;
            }
            QHeaderView::section {
                background: #e9f4ff;
                border: none;
                border-right: 1px solid #d8ebfd;
                border-bottom: 1px solid #d8ebfd;
                padding: 7px;
                color: #1f4d73;
                font-weight: 700;
            }
            QLabel#periodBadge {
                background: #e9f7ff;
                border: 1px solid #bfe6fb;
                border-radius: 8px;
                padding: 5px 10px;
                color: #155e7a;
                font-weight: 600;
            }
            """
        )

    def _build_ui(self) -> None:
        root = QWidget()
        root_layout = QVBoxLayout(root)
        root_layout.setContentsMargins(20, 16, 20, 16)
        root_layout.setSpacing(14)

        hero = QFrame()
        hero.setObjectName("card")
        hero_layout = QVBoxLayout(hero)
        hero_layout.setContentsMargins(20, 16, 20, 16)
        hero_layout.setSpacing(2)

        title = QLabel("Lab Productivity Navigator")
        title.setObjectName("heroTitle")
        subtitle = QLabel(
            "外链读取 xlsx（不改动原表 A~AI），按指定起止日期分析在研负载、积分、FTE 与人效。"
        )
        subtitle.setObjectName("heroSub")
        hero_layout.addWidget(title)
        hero_layout.addWidget(subtitle)

        root_layout.addWidget(hero)

        control = QFrame()
        control.setObjectName("card")
        control_layout = QVBoxLayout(control)
        control_layout.setContentsMargins(14, 14, 14, 14)
        control_layout.setSpacing(10)

        file_group = QGroupBox("数据源")
        file_grid = QGridLayout(file_group)
        file_grid.setHorizontalSpacing(10)
        file_grid.setVerticalSpacing(8)

        self.file_path_edit = QLineEdit()
        self.file_path_edit.setPlaceholderText("选择生产数据统计 xlsx 文件")
        self.file_path_edit.setReadOnly(True)

        self.sheet_combo = QComboBox()
        self.sheet_combo.setMinimumWidth(180)

        browse_btn = QPushButton("选择文件")
        browse_btn.clicked.connect(self._choose_file)

        load_btn = QPushButton("加载数据")
        load_btn.clicked.connect(self._load_data)

        file_grid.addWidget(QLabel("Excel 路径"), 0, 0)
        file_grid.addWidget(self.file_path_edit, 0, 1, 1, 5)
        file_grid.addWidget(browse_btn, 0, 6)
        file_grid.addWidget(QLabel("Sheet"), 1, 0)
        file_grid.addWidget(self.sheet_combo, 1, 1)
        file_grid.addWidget(load_btn, 1, 2)

        filter_group = QGroupBox("筛选器")
        filter_grid = QGridLayout(filter_group)
        filter_grid.setHorizontalSpacing(12)
        filter_grid.setVerticalSpacing(8)

        self.period_quick_combo = QComboBox()
        self.period_quick_combo.addItems(["本周", "本月"])
        apply_quick_btn = QPushButton("套用快捷时间")
        apply_quick_btn.clicked.connect(self._apply_quick_period)

        self.start_date_edit = QDateEdit()
        self.start_date_edit.setCalendarPopup(True)
        self.start_date_edit.setDisplayFormat("yyyy-MM-dd")

        self.end_date_edit = QDateEdit()
        self.end_date_edit.setCalendarPopup(True)
        self.end_date_edit.setDisplayFormat("yyyy-MM-dd")

        self.date_basis_combo = QComboBox()
        self.date_basis_combo.addItem("完成优先", userData="completion_priority")
        self.date_basis_combo.addItem("完成日期", userData="completion_date")
        self.date_basis_combo.addItem("起始日期", userData="start_date")

        self.saturation_spin = QSpinBox()
        self.saturation_spin.setRange(1, 200)
        self.saturation_spin.setValue(8)

        self.researcher_combo = QComboBox()
        self.researcher_combo.addItem("全部")

        self.wbp_edit = QLineEdit()
        self.wbp_edit.setPlaceholderText("精确匹配，例如 WBP-001")

        self.product_edit = QLineEdit()
        self.product_edit.setPlaceholderText("精确匹配，例如 PID-123")

        self.period_badge = QLabel("时间段: -")
        self.period_badge.setObjectName("periodBadge")

        apply_btn = QPushButton("应用筛选并刷新")
        apply_btn.clicked.connect(self._refresh_all_tabs)

        self.start_date_edit.dateChanged.connect(self._update_period_badge)
        self.end_date_edit.dateChanged.connect(self._update_period_badge)

        filter_grid.addWidget(QLabel("快捷时间"), 0, 0)
        filter_grid.addWidget(self.period_quick_combo, 0, 1)
        filter_grid.addWidget(apply_quick_btn, 0, 2)
        filter_grid.addWidget(QLabel("起始日期"), 0, 3)
        filter_grid.addWidget(self.start_date_edit, 0, 4)
        filter_grid.addWidget(QLabel("结束日期"), 0, 5)
        filter_grid.addWidget(self.end_date_edit, 0, 6)

        filter_grid.addWidget(QLabel("统计日期口径"), 1, 0)
        filter_grid.addWidget(self.date_basis_combo, 1, 1)
        filter_grid.addWidget(QLabel("在研饱和阈值"), 1, 2)
        filter_grid.addWidget(self.saturation_spin, 1, 3)
        filter_grid.addWidget(QLabel("实验员筛选"), 1, 4)
        filter_grid.addWidget(self.researcher_combo, 1, 5)
        filter_grid.addWidget(self.period_badge, 1, 6)

        filter_grid.addWidget(QLabel("WBP Code"), 2, 0)
        filter_grid.addWidget(self.wbp_edit, 2, 1)
        filter_grid.addWidget(QLabel("Product ID"), 2, 2)
        filter_grid.addWidget(self.product_edit, 2, 3)
        filter_grid.addWidget(apply_btn, 2, 6)

        control_layout.addWidget(file_group)
        control_layout.addWidget(filter_group)
        root_layout.addWidget(control)

        content_row = QHBoxLayout()
        content_row.setSpacing(12)

        self.tab_widget = QTabWidget()
        self.tab_widget.currentChanged.connect(self._refresh_chart_for_current_tab)
        content_row.addWidget(self.tab_widget, 3)

        chart_card = QFrame()
        chart_card.setObjectName("card")
        chart_layout = QVBoxLayout(chart_card)
        chart_layout.setContentsMargins(12, 12, 12, 12)
        chart_layout.setSpacing(8)

        self.chart_title_label = QLabel("图表视图")
        self.chart_title_label.setObjectName("chartTitle")
        chart_layout.addWidget(self.chart_title_label)

        self.figure = Figure(figsize=(6, 5), dpi=100)
        self.chart_canvas = FigureCanvas(self.figure)
        self.chart_ax = self.figure.add_subplot(111)
        chart_layout.addWidget(self.chart_canvas, 1)

        content_row.addWidget(chart_card, 2)
        root_layout.addLayout(content_row, 1)

        self.detail_table = self._add_table_tab(
            "0. 筛选明细",
            "按当前筛选条件列出相关条目，便于核查。",
        )
        self.wip_table = self._add_table_tab(
            "1. 在研负载",
            "每个实验员未完成分子数（Unique C|D）以及是否可接收新任务。",
        )
        self.score_table = self._add_table_tab(
            "2. 实验员积分",
            "按选定时间段 + 可选筛选条件，统计实验员积分。",
        )
        self.type_table = self._add_table_tab(
            "3. 偶联类型积分",
            "按时间段统计全体记录中 IC Complete 与 Other 的积分与占比。",
        )
        self.fte_overview_table = self._add_table_tab(
            "4. FTE总览",
            "FTE = IC Complete积分 / 时间段总积分（支持实验员筛选）。",
        )
        self.fte_person_table = self._add_table_tab(
            "5. 按实验员FTE",
            "给定时间段按实验员列出 FTE，并求 FTE 总值。",
        )
        self.efficiency_table = self._add_table_tab(
            "6. 人效",
            "人效 = 时间段内 Unique(C|D)数量 / (第5页 FTE总值)。",
        )

        self.setCentralWidget(root)

        self._apply_quick_period(init_only=True)
        self._update_period_badge()
        self._draw_empty_chart("加载并筛选数据后显示图表")

    def _add_table_tab(self, tab_name: str, note: str) -> QTableWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        note_label = QLabel(note)
        note_label.setStyleSheet("color:#47708f; font-size:12px;")
        layout.addWidget(note_label)

        table = QTableWidget()
        table.setAlternatingRowColors(True)
        table.setSortingEnabled(False)
        table.verticalHeader().setVisible(False)
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(table, 1)

        self.tab_widget.addTab(tab, tab_name)
        return table

    def _auto_pick_default_file(self) -> None:
        cwd = Path.cwd()
        candidates = [p for p in cwd.glob("*.xlsx") if not p.name.startswith("~$")]
        if not candidates:
            return
        target = sorted(candidates, key=lambda x: x.name)[0]
        self.file_path_edit.setText(str(target))
        self._load_sheet_names(target)

    def _choose_file(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择生产数据统计文件",
            str(Path.cwd()),
            "Excel Files (*.xlsx *.xlsm)",
        )
        if not file_path:
            return
        self.file_path_edit.setText(file_path)
        self._load_sheet_names(Path(file_path))

    def _load_sheet_names(self, path: Path) -> None:
        self.sheet_combo.clear()
        try:
            wb = load_workbook(path, read_only=True, data_only=True)
            self.sheet_combo.addItems(list(wb.sheetnames))
            wb.close()
        except Exception as exc:  # pragma: no cover - GUI message path
            QMessageBox.critical(self, "读取失败", f"无法读取 Excel Sheet 列表:\n{exc}")

    def _load_data(self) -> None:
        file_path = self.file_path_edit.text().strip()
        if not file_path:
            QMessageBox.warning(self, "缺少文件", "请先选择 xlsx 文件。")
            return

        sheet_name = self.sheet_combo.currentText().strip()
        if not sheet_name:
            QMessageBox.warning(self, "缺少 Sheet", "请选择数据所在 Sheet。")
            return

        path = Path(file_path)
        if not path.exists():
            QMessageBox.warning(self, "文件不存在", "所选 Excel 文件不存在。")
            return

        try:
            self.df_raw = self._read_source_sheet(path, sheet_name)
        except Exception as exc:  # pragma: no cover - GUI message path
            QMessageBox.critical(self, "加载失败", f"解析数据失败:\n{exc}")
            return

        if self.df_raw.empty:
            QMessageBox.information(self, "无数据", "第4行起未检测到实验记录。")
            return

        self._rebuild_researcher_filter_options()
        self._refresh_all_tabs()

    def _read_source_sheet(self, file_path: Path, sheet_name: str) -> pd.DataFrame:
        wb = load_workbook(file_path, read_only=True, data_only=True)
        try:
            if sheet_name not in wb.sheetnames:
                raise ValueError(f"Sheet 不存在: {sheet_name}")

            ws = wb[sheet_name]
            rows: list[dict[str, Any]] = []
            epoch = wb.epoch

            for row in ws.iter_rows(min_row=4, max_col=35, values_only=True):
                coupling_raw = row[COL_COUPLING_A]
                wbp_raw = row[COL_WBP_C]
                product_raw = row[COL_PRODUCT_D]
                researcher_raw = row[COL_RESEARCHER_E]
                start_raw = row[COL_START_AF]
                end_raw = row[COL_END_AG]
                score_raw = row[COL_SCORE_AI]

                if self._all_empty(
                    coupling_raw,
                    wbp_raw,
                    product_raw,
                    researcher_raw,
                    start_raw,
                    end_raw,
                    score_raw,
                ):
                    continue

                coupling_type = self._norm_text(coupling_raw)
                wbp_code = self._norm_text(wbp_raw)
                product_id = self._norm_text(product_raw)
                researcher = self._norm_text(researcher_raw)
                start_date = self._to_date(start_raw, epoch)
                end_date = self._to_date(end_raw, epoch)
                score = self._to_float(score_raw)

                if not researcher:
                    continue

                is_ic = coupling_type.casefold() == "ic complete"
                cd_key = f"{wbp_code}|{product_id}" if (wbp_code or product_id) else ""

                rows.append(
                    {
                        "coupling_type": coupling_type,
                        "coupling_group": "IC Complete" if is_ic else "Other",
                        "wbp_code": wbp_code,
                        "product_id": product_id,
                        "researcher": researcher,
                        "start_date": start_date,
                        "end_date": end_date,
                        "score": score,
                        "cd_key": cd_key,
                    }
                )
        finally:
            wb.close()

        df = pd.DataFrame(rows)
        if df.empty:
            return df

        df["start_date"] = pd.to_datetime(df["start_date"], errors="coerce")
        df["end_date"] = pd.to_datetime(df["end_date"], errors="coerce")
        df["score"] = pd.to_numeric(df["score"], errors="coerce").fillna(0.0)
        return df

    @staticmethod
    def _all_empty(*values: Any) -> bool:
        for v in values:
            if isinstance(v, str) and v.strip() != "":
                return False
            if v not in (None, ""):
                return False
        return True

    @staticmethod
    def _norm_text(value: Any) -> str:
        if value is None:
            return ""
        return str(value).strip()

    @staticmethod
    def _to_float(value: Any) -> float:
        if value is None or value == "":
            return 0.0
        if isinstance(value, (int, float)):
            return float(value)
        text = str(value).strip().replace(",", "")
        try:
            return float(text)
        except ValueError:
            return 0.0

    @staticmethod
    def _to_date(value: Any, epoch: datetime) -> date | None:
        if value is None or value == "":
            return None
        if isinstance(value, datetime):
            return value.date()
        if isinstance(value, date):
            return value
        if isinstance(value, (int, float)):
            try:
                converted = from_excel(value, epoch=epoch)
                if isinstance(converted, datetime):
                    return converted.date()
                if isinstance(converted, date):
                    return converted
            except Exception:
                return None

        parsed = pd.to_datetime(str(value).strip(), errors="coerce")
        if pd.isna(parsed):
            return None
        return parsed.date()

    def _rebuild_researcher_filter_options(self) -> None:
        cur = self.researcher_combo.currentText().strip() or "全部"
        names = sorted(x for x in self.df_raw["researcher"].dropna().unique().tolist() if x)

        self.researcher_combo.blockSignals(True)
        self.researcher_combo.clear()
        self.researcher_combo.addItem("全部")
        self.researcher_combo.addItems(names)

        idx = self.researcher_combo.findText(cur)
        self.researcher_combo.setCurrentIndex(idx if idx >= 0 else 0)
        self.researcher_combo.blockSignals(False)

    def _current_filters(self) -> FilterState:
        researcher = self.researcher_combo.currentText().strip()
        if researcher == "全部":
            researcher = ""

        return FilterState(
            start_date=self.start_date_edit.date().toPyDate(),
            end_date=self.end_date_edit.date().toPyDate(),
            date_basis=self.date_basis_combo.currentData(),
            researcher=researcher,
            wbp_code=self.wbp_edit.text().strip(),
            product_id=self.product_edit.text().strip(),
            saturation_threshold=int(self.saturation_spin.value()),
        )

    @staticmethod
    def _period_range(period_type: str, anchor: date) -> tuple[date, date]:
        if period_type == "week":
            start = anchor - timedelta(days=anchor.weekday())
            end = start + timedelta(days=6)
            return start, end

        month_start = anchor.replace(day=1)
        if month_start.month == 12:
            next_month = month_start.replace(year=month_start.year + 1, month=1, day=1)
        else:
            next_month = month_start.replace(month=month_start.month + 1, day=1)
        return month_start, next_month - timedelta(days=1)

    def _apply_quick_period(self, init_only: bool = False) -> None:
        quick_type = self.period_quick_combo.currentText().strip()
        period_type = "week" if quick_type == "本周" else "month"
        start, end = self._period_range(period_type, date.today())

        self.start_date_edit.blockSignals(True)
        self.end_date_edit.blockSignals(True)
        self.start_date_edit.setDate(QDate(start.year, start.month, start.day))
        self.end_date_edit.setDate(QDate(end.year, end.month, end.day))
        self.start_date_edit.blockSignals(False)
        self.end_date_edit.blockSignals(False)

        self._update_period_badge()

        if not init_only and not self.df_raw.empty:
            self._refresh_all_tabs()

    def _update_period_badge(self) -> None:
        start = self.start_date_edit.date().toPyDate()
        end = self.end_date_edit.date().toPyDate()
        self.period_badge.setText(f"时间段: {start:%Y-%m-%d} ~ {end:%Y-%m-%d}")

    def _prepare_df_with_stat_date(self, fs: FilterState) -> pd.DataFrame:
        if self.df_raw.empty:
            return pd.DataFrame()

        df = self.df_raw.copy()

        if fs.date_basis == "completion_date":
            df["stat_date"] = df["end_date"]
        elif fs.date_basis == "start_date":
            df["stat_date"] = df["start_date"]
        else:
            df["stat_date"] = df["end_date"].where(df["end_date"].notna(), df["start_date"])

        return df

    def _filter_common(
        self,
        df: pd.DataFrame,
        fs: FilterState,
        *,
        apply_period: bool,
        apply_researcher: bool,
    ) -> pd.DataFrame:
        if df.empty:
            return df

        out = df.copy()
        if apply_period:
            start_ts = pd.Timestamp(fs.start_date)
            end_ts = pd.Timestamp(fs.end_date)
            out = out[(out["stat_date"] >= start_ts) & (out["stat_date"] <= end_ts)]

        if apply_researcher and fs.researcher:
            out = out[out["researcher"] == fs.researcher]

        if fs.wbp_code:
            out = out[out["wbp_code"] == fs.wbp_code]

        if fs.product_id:
            out = out[out["product_id"] == fs.product_id]

        return out

    def _refresh_all_tabs(self) -> None:
        if self.df_raw.empty:
            QMessageBox.information(self, "提示", "请先加载数据文件。")
            return

        fs = self._current_filters()
        if fs.start_date > fs.end_date:
            QMessageBox.warning(self, "时间段错误", "起始日期不能晚于结束日期。")
            return

        df = self._prepare_df_with_stat_date(fs)
        self.df_working = df

        detail_df = self._fill_detail_tab(df, fs)
        wip_df = self._fill_wip_tab(df, fs)
        score_df = self._fill_score_tab(df, fs)
        type_df = self._fill_type_tab(df, fs)
        _, fte_overview_metrics = self._fill_fte_overview_tab(df, fs)
        fte_person_df, fte_total = self._fill_fte_by_person_tab(df, fs)
        _, efficiency_metrics = self._fill_efficiency_tab(df, fs, fte_total)

        self.chart_payloads = {
            "detail": detail_df,
            "wip": wip_df,
            "score": score_df,
            "type": type_df,
            "fte_overview_metrics": fte_overview_metrics,
            "fte_person": fte_person_df,
            "efficiency_metrics": efficiency_metrics,
        }
        self._refresh_chart_for_current_tab()

    def _fill_detail_tab(self, df: pd.DataFrame, fs: FilterState) -> pd.DataFrame:
        base = self._filter_common(df, fs, apply_period=True, apply_researcher=True)

        if base.empty:
            result = pd.DataFrame(
                columns=[
                    "实验员(E)",
                    "偶联类型(A)",
                    "偶联分类(IC/Other)",
                    "WBP Code(C)",
                    "Product ID(D)",
                    "起始日期(AF)",
                    "完成日期(AG)",
                    "统计日期(stat_date)",
                    "积分(AI)",
                    "CD_Key(C|D)",
                ]
            )
        else:
            result = (
                base[
                    [
                        "researcher",
                        "coupling_type",
                        "coupling_group",
                        "wbp_code",
                        "product_id",
                        "start_date",
                        "end_date",
                        "stat_date",
                        "score",
                        "cd_key",
                    ]
                ]
                .rename(
                    columns={
                        "researcher": "实验员(E)",
                        "coupling_type": "偶联类型(A)",
                        "coupling_group": "偶联分类(IC/Other)",
                        "wbp_code": "WBP Code(C)",
                        "product_id": "Product ID(D)",
                        "start_date": "起始日期(AF)",
                        "end_date": "完成日期(AG)",
                        "stat_date": "统计日期(stat_date)",
                        "score": "积分(AI)",
                        "cd_key": "CD_Key(C|D)",
                    }
                )
                .sort_values(["统计日期(stat_date)", "实验员(E)"], ascending=[True, True])
            )

        self._render_table(self.detail_table, result)
        return result

    def _fill_wip_tab(self, df: pd.DataFrame, fs: FilterState) -> pd.DataFrame:
        # 在研负载只看未完成实验（AG 为空），不受时间段影响
        base = self._filter_common(df, fs, apply_period=False, apply_researcher=True)
        unfinished = base[base["end_date"].isna()].copy()

        if unfinished.empty:
            result = pd.DataFrame(
                columns=["实验员", "未完成记录数", "未完成分子数(Unique C|D)", "饱和判断", "阈值"]
            )
        else:
            grouped = (
                unfinished.groupby("researcher", as_index=False)
                .agg(
                    unfinished_records=("researcher", "count"),
                    unfinished_molecules=("cd_key", lambda s: s[s != ""].nunique()),
                )
                .sort_values(["unfinished_molecules", "unfinished_records"], ascending=[False, False])
            )
            grouped["status"] = grouped["unfinished_molecules"].apply(
                lambda x: "可接新任务" if x <= fs.saturation_threshold else "已饱和"
            )
            grouped["threshold"] = fs.saturation_threshold
            result = grouped.rename(
                columns={
                    "researcher": "实验员",
                    "unfinished_records": "未完成记录数",
                    "unfinished_molecules": "未完成分子数(Unique C|D)",
                    "status": "饱和判断",
                    "threshold": "阈值",
                }
            )

        self._render_table(self.wip_table, result)
        return result

    def _fill_score_tab(self, df: pd.DataFrame, fs: FilterState) -> pd.DataFrame:
        base = self._filter_common(df, fs, apply_period=True, apply_researcher=True)

        if base.empty:
            result = pd.DataFrame(columns=["实验员", "积分合计", "记录数", "平均积分/记录"])
        else:
            grouped = (
                base.groupby("researcher", as_index=False)
                .agg(
                    total_score=("score", "sum"),
                    record_count=("researcher", "count"),
                )
                .sort_values("total_score", ascending=False)
            )
            grouped["avg_score"] = grouped["total_score"] / grouped["record_count"]
            result = grouped.rename(
                columns={
                    "researcher": "实验员",
                    "total_score": "积分合计",
                    "record_count": "记录数",
                    "avg_score": "平均积分/记录",
                }
            )

        self._render_table(self.score_table, result)
        return result

    def _fill_type_tab(self, df: pd.DataFrame, fs: FilterState) -> pd.DataFrame:
        # 需求3：统计所有实验记录的总积分，不应用实验员筛选
        base = self._filter_common(df, fs, apply_period=True, apply_researcher=False)

        ic_score = float(base.loc[base["coupling_group"] == "IC Complete", "score"].sum())
        other_score = float(base.loc[base["coupling_group"] == "Other", "score"].sum())
        total_score = ic_score + other_score

        rows = [
            ["IC Complete", ic_score, ic_score / total_score if total_score else 0.0],
            ["Other", other_score, other_score / total_score if total_score else 0.0],
            ["Total", total_score, 1.0 if total_score else 0.0],
        ]
        result = pd.DataFrame(rows, columns=["偶联类型", "积分", "占比"])
        self._render_table(self.type_table, result, percent_cols={"占比"})
        return result

    def _fill_fte_overview_tab(self, df: pd.DataFrame, fs: FilterState) -> tuple[pd.DataFrame, dict[str, float]]:
        base = self._filter_common(df, fs, apply_period=True, apply_researcher=True)
        total_score = float(base["score"].sum())
        ic_score = float(base.loc[base["coupling_group"] == "IC Complete", "score"].sum())
        fte = ic_score / total_score if total_score else 0.0

        rows = [
            ["时间段", f"{fs.start_date:%Y-%m-%d} ~ {fs.end_date:%Y-%m-%d}"],
            ["实验员筛选", fs.researcher if fs.researcher else "全部"],
            ["总积分", total_score],
            ["IC Complete积分", ic_score],
            ["FTE(IC/Total)", fte],
        ]
        result = pd.DataFrame(rows, columns=["指标", "值"])
        self._render_table(self.fte_overview_table, result, percent_rows={"FTE(IC/Total)"})
        return result, {"total_score": total_score, "ic_score": ic_score, "fte": fte}

    def _fill_fte_by_person_tab(self, df: pd.DataFrame, fs: FilterState) -> tuple[pd.DataFrame, float]:
        # 需求5：按实验员列出FTE，因此不应用实验员单选过滤（仍应用WBP/Product）
        base = self._filter_common(df, fs, apply_period=True, apply_researcher=False)

        if base.empty:
            result = pd.DataFrame(columns=["实验员", "总积分", "IC Complete积分", "FTE"])
            fte_total = 0.0
        else:
            grouped = base.groupby("researcher", as_index=False).agg(total_score=("score", "sum"))
            ic_grouped = (
                base[base["coupling_group"] == "IC Complete"]
                .groupby("researcher", as_index=False)
                .agg(ic_score=("score", "sum"))
            )
            merged = grouped.merge(ic_grouped, on="researcher", how="left").fillna({"ic_score": 0.0})
            merged["fte"] = merged.apply(
                lambda row: row["ic_score"] / row["total_score"] if row["total_score"] else 0.0,
                axis=1,
            )
            merged = merged.sort_values("fte", ascending=False)
            fte_total = float(merged["fte"].sum())
            result = merged.rename(
                columns={
                    "researcher": "实验员",
                    "total_score": "总积分",
                    "ic_score": "IC Complete积分",
                    "fte": "FTE",
                }
            )

        self._render_table(self.fte_person_table, result, percent_cols={"FTE"})
        return result, fte_total

    def _fill_efficiency_tab(
        self,
        df: pd.DataFrame,
        fs: FilterState,
        fte_total: float,
    ) -> tuple[pd.DataFrame, dict[str, float]]:
        # 需求6：使用与需求5相同的统计底集（按时间段，按WBP/Product，可跨实验员）
        base = self._filter_common(df, fs, apply_period=True, apply_researcher=False)
        unique_cd_count = float(base.loc[base["cd_key"] != "", "cd_key"].nunique())
        efficiency = unique_cd_count / fte_total if fte_total else 0.0

        rows = [
            ["时间段", f"{fs.start_date:%Y-%m-%d} ~ {fs.end_date:%Y-%m-%d}"],
            ["Unique(C|D)数量", unique_cd_count],
            ["FTE总值(来自第5页)", fte_total],
            ["人效 = Unique(C|D)/FTE总值", efficiency],
        ]
        result = pd.DataFrame(rows, columns=["指标", "值"])
        self._render_table(
            self.efficiency_table,
            result,
            percent_rows={"FTE总值(来自第5页)"},
        )
        return result, {
            "unique_cd_count": unique_cd_count,
            "fte_total": fte_total,
            "efficiency": efficiency,
        }

    def _refresh_chart_for_current_tab(self, *_: Any) -> None:
        if not hasattr(self, "tab_widget"):
            return

        idx = self.tab_widget.currentIndex()
        self.figure.clear()
        self.chart_ax = self.figure.add_subplot(111)
        self._style_axis_base(self.chart_ax)

        if idx == 0:
            self.chart_title_label.setText("筛选明细趋势图")
            self._plot_detail_chart(self.chart_ax)
        elif idx == 1:
            self.chart_title_label.setText("在研负载图")
            self._plot_wip_chart(self.chart_ax)
        elif idx == 2:
            self.chart_title_label.setText("实验员积分图")
            self._plot_score_chart(self.chart_ax)
        elif idx == 3:
            self.chart_title_label.setText("偶联类型积分占比")
            self._plot_type_chart(self.chart_ax)
        elif idx == 4:
            self.chart_title_label.setText("FTE总览图")
            self._plot_fte_overview_chart(self.chart_ax)
        elif idx == 5:
            self.chart_title_label.setText("按实验员FTE图")
            self._plot_fte_person_chart(self.chart_ax)
        elif idx == 6:
            self.chart_title_label.setText("人效图")
            self._plot_efficiency_chart(self.chart_ax)
        else:
            self._draw_empty_chart("图表数据不可用")
            return

        self.figure.tight_layout()
        self.chart_canvas.draw_idle()

    @staticmethod
    def _style_axis_base(ax: Any) -> None:
        ax.set_facecolor("#FCFEFF")
        ax.grid(axis="y", linestyle="--", linewidth=0.8, color="#DCEBFA", alpha=0.9)
        for spine in ["top", "right"]:
            ax.spines[spine].set_visible(False)
        ax.spines["left"].set_color("#B9D5EE")
        ax.spines["bottom"].set_color("#B9D5EE")
        ax.tick_params(colors="#2B5679")

    def _draw_empty_chart(self, text: str) -> None:
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        ax.axis("off")
        ax.text(
            0.5,
            0.5,
            text,
            ha="center",
            va="center",
            fontsize=13,
            color="#5D7994",
            transform=ax.transAxes,
        )
        self.chart_canvas.draw_idle()

    def _plot_detail_chart(self, ax: Any) -> None:
        df = self.chart_payloads.get("detail", pd.DataFrame())
        if df.empty:
            ax.axis("off")
            ax.text(0.5, 0.5, "无筛选明细", ha="center", va="center", color="#5D7994", transform=ax.transAxes)
            return

        dates = pd.to_datetime(df["统计日期(stat_date)"], errors="coerce").dropna()
        if dates.empty:
            ax.axis("off")
            ax.text(0.5, 0.5, "无可用统计日期", ha="center", va="center", color="#5D7994", transform=ax.transAxes)
            return

        trend = dates.dt.date.value_counts().sort_index()
        labels = [d.strftime("%m-%d") for d in trend.index]
        values = trend.values
        bars = ax.bar(labels, values, color="#36A3FF", edgecolor="#1F7BC9", linewidth=1.0)
        ax.set_title("筛选记录数趋势")
        ax.set_xlabel("统计日期")
        ax.set_ylabel("记录数")
        for bar in bars:
            h = bar.get_height()
            ax.text(bar.get_x() + bar.get_width() / 2, h, f"{int(h)}", ha="center", va="bottom", fontsize=9, color="#245981")

    def _plot_wip_chart(self, ax: Any) -> None:
        df = self.chart_payloads.get("wip", pd.DataFrame())
        if df.empty:
            ax.axis("off")
            ax.text(0.5, 0.5, "无在研负载数据", ha="center", va="center", color="#5D7994", transform=ax.transAxes)
            return

        x = df["实验员"].astype(str).tolist()
        y = pd.to_numeric(df["未完成分子数(Unique C|D)"], errors="coerce").fillna(0).tolist()
        bars = ax.bar(x, y, color="#06B6D4", edgecolor="#0891B2", linewidth=1.0)
        ax.set_title("实验员在研分子负载")
        ax.set_xlabel("实验员")
        ax.set_ylabel("Unique C|D")
        for bar in bars:
            h = bar.get_height()
            ax.text(bar.get_x() + bar.get_width() / 2, h, f"{int(h)}", ha="center", va="bottom", fontsize=9, color="#245981")

    def _plot_score_chart(self, ax: Any) -> None:
        df = self.chart_payloads.get("score", pd.DataFrame())
        if df.empty:
            ax.axis("off")
            ax.text(0.5, 0.5, "无实验员积分数据", ha="center", va="center", color="#5D7994", transform=ax.transAxes)
            return

        x = df["实验员"].astype(str).tolist()
        y = pd.to_numeric(df["积分合计"], errors="coerce").fillna(0).tolist()
        bars = ax.bar(x, y, color="#2DD4BF", edgecolor="#0F766E", linewidth=1.0)
        ax.set_title("实验员积分排行")
        ax.set_xlabel("实验员")
        ax.set_ylabel("积分")
        for bar in bars:
            h = bar.get_height()
            ax.text(bar.get_x() + bar.get_width() / 2, h, f"{h:.1f}", ha="center", va="bottom", fontsize=9, color="#245981")

    def _plot_type_chart(self, ax: Any) -> None:
        df = self.chart_payloads.get("type", pd.DataFrame())
        if df.empty or len(df) < 2:
            ax.axis("off")
            ax.text(0.5, 0.5, "无偶联类型积分数据", ha="center", va="center", color="#5D7994", transform=ax.transAxes)
            return

        pie_df = df[df["偶联类型"].isin(["IC Complete", "Other"])]
        labels = pie_df["偶联类型"].astype(str).tolist()
        values = pd.to_numeric(pie_df["积分"], errors="coerce").fillna(0).tolist()
        total = sum(values)
        if total <= 0:
            ax.axis("off")
            ax.text(0.5, 0.5, "积分总和为 0", ha="center", va="center", color="#5D7994", transform=ax.transAxes)
            return

        colors = ["#3B82F6", "#A5B4FC"]
        ax.pie(
            values,
            labels=labels,
            colors=colors,
            startangle=90,
            wedgeprops={"width": 0.45, "edgecolor": "white"},
            autopct="%1.1f%%",
            pctdistance=0.82,
            textprops={"color": "#234A6B", "fontsize": 10},
        )
        ax.set_title("IC Complete vs Other")

    def _plot_fte_overview_chart(self, ax: Any) -> None:
        metrics = self.chart_payloads.get("fte_overview_metrics", {})
        total_score = float(metrics.get("total_score", 0.0))
        ic_score = float(metrics.get("ic_score", 0.0))
        fte = float(metrics.get("fte", 0.0))

        if total_score == 0 and ic_score == 0:
            ax.axis("off")
            ax.text(0.5, 0.5, "无FTE总览数据", ha="center", va="center", color="#5D7994", transform=ax.transAxes)
            return

        labels = ["总积分", "IC积分"]
        values = [total_score, ic_score]
        bars = ax.bar(labels, values, color=["#60A5FA", "#2563EB"], edgecolor="#1D4ED8", linewidth=1.0)
        ax.set_title("FTE构成")
        ax.set_ylabel("积分")
        for bar in bars:
            h = bar.get_height()
            ax.text(bar.get_x() + bar.get_width() / 2, h, f"{h:.1f}", ha="center", va="bottom", fontsize=9, color="#245981")

        ax.text(
            0.98,
            0.95,
            f"FTE = {fte * 100:.2f}%",
            ha="right",
            va="top",
            transform=ax.transAxes,
            fontsize=11,
            color="#1E4F79",
            bbox={"boxstyle": "round,pad=0.3", "facecolor": "#E8F4FF", "edgecolor": "#BFDDF8"},
        )

    def _plot_fte_person_chart(self, ax: Any) -> None:
        df = self.chart_payloads.get("fte_person", pd.DataFrame())
        if df.empty:
            ax.axis("off")
            ax.text(0.5, 0.5, "无按实验员FTE数据", ha="center", va="center", color="#5D7994", transform=ax.transAxes)
            return

        x = df["实验员"].astype(str).tolist()
        y = pd.to_numeric(df["FTE"], errors="coerce").fillna(0).tolist()
        bars = ax.bar(x, y, color="#22C55E", edgecolor="#15803D", linewidth=1.0)
        ax.set_title("按实验员FTE")
        ax.set_xlabel("实验员")
        ax.set_ylabel("FTE")
        ax.yaxis.set_major_formatter(PercentFormatter(1.0))
        for bar in bars:
            h = bar.get_height()
            ax.text(bar.get_x() + bar.get_width() / 2, h, f"{h * 100:.1f}%", ha="center", va="bottom", fontsize=9, color="#245981")

    def _plot_efficiency_chart(self, ax: Any) -> None:
        metrics = self.chart_payloads.get("efficiency_metrics", {})
        unique_cd_count = float(metrics.get("unique_cd_count", 0.0))
        fte_total = float(metrics.get("fte_total", 0.0))
        efficiency = float(metrics.get("efficiency", 0.0))

        labels = ["Unique(C|D)", "FTE总值", "人效"]
        values = [unique_cd_count, fte_total, efficiency]
        if all(v == 0 for v in values):
            ax.axis("off")
            ax.text(0.5, 0.5, "无人效统计数据", ha="center", va="center", color="#5D7994", transform=ax.transAxes)
            return

        bars = ax.bar(labels, values, color=["#38BDF8", "#F59E0B", "#A78BFA"], edgecolor="#475569", linewidth=0.8)
        ax.set_title("人效构成指标")
        ax.set_ylabel("数值")
        for i, bar in enumerate(bars):
            h = bar.get_height()
            fmt = f"{h:.3f}" if i == 2 else f"{h:.2f}".rstrip("0").rstrip(".")
            ax.text(bar.get_x() + bar.get_width() / 2, h, fmt, ha="center", va="bottom", fontsize=9, color="#245981")

    def _render_table(
        self,
        table: QTableWidget,
        df: pd.DataFrame,
        *,
        percent_cols: set[str] | None = None,
        percent_rows: set[str] | None = None,
    ) -> None:
        percent_cols = percent_cols or set()
        percent_rows = percent_rows or set()

        table.clear()
        table.setRowCount(0)

        if df.empty:
            table.setColumnCount(1)
            table.setHorizontalHeaderLabels(["结果"])
            table.setRowCount(1)
            table.setItem(0, 0, QTableWidgetItem("无匹配数据"))
            return

        headers = df.columns.tolist()
        table.setColumnCount(len(headers))
        table.setHorizontalHeaderLabels(headers)
        table.setRowCount(len(df))

        first_col_name = headers[0] if headers else ""

        for r, (_, row) in enumerate(df.iterrows()):
            row_label = str(row[first_col_name]) if first_col_name else ""
            for c, col in enumerate(headers):
                val = row[col]
                txt = self._format_cell(val, col, row_label, percent_cols, percent_rows)
                item = QTableWidgetItem(txt)
                if isinstance(val, (int, float)):
                    item.setTextAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight)
                else:
                    item.setTextAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
                table.setItem(r, c, item)

        table.resizeColumnsToContents()

    @staticmethod
    def _format_cell(
        val: Any,
        col_name: str,
        row_label: str,
        percent_cols: set[str],
        percent_rows: set[str],
    ) -> str:
        if pd.isna(val):
            return ""

        if isinstance(val, pd.Timestamp):
            return val.strftime("%Y-%m-%d")

        if isinstance(val, datetime):
            return val.strftime("%Y-%m-%d")

        if isinstance(val, date):
            return val.strftime("%Y-%m-%d")

        if isinstance(val, (int, float)):
            if col_name in percent_cols or row_label in percent_rows:
                return f"{float(val) * 100:.2f}%"

            num = float(val)
            if abs(num - round(num)) < 1e-9:
                return f"{int(round(num)):,}"
            return f"{num:,.3f}".rstrip("0").rstrip(".")

        return str(val)


def main() -> None:
    app = QApplication([])
    app.setFont(QFont("Segoe UI", 10))
    win = LabKPIDashboard()
    win.show()
    app.exec()


if __name__ == "__main__":
    main()
