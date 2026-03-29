# Feature Inventory

Last updated: 2026-03-29

## Feature Status Scale

- `implemented`: feature behavior is present and validated.
- `partial`: feature exists but has gaps, constraints, or incomplete coverage.
- `planned`: feature intent exists but implementation is not complete.
- `deprecated`: feature remains for compatibility but should not be expanded.

## Major Feature Areas

### Feature Area: Workbook ingestion

- Status: `implemented`
- Main entry points / relevant files:
  - `lab_kpi_pyqt6_app.py`
- User-visible behavior:
  - Reads a selected Excel workbook and sheet without modifying source data.
  - Uses fixed business columns plus header-based lookup for `是否新人` and `Request activity`.
  - Falls back to a manual column-mapping dialog when required fields are missing or obviously invalid.
- Limitations / caveats:
  - Session-level manual mappings are reused only while the app stays open.
- Validation hints:
  - Load a sheet with mixed-case `Request activity` headers and verify parsing succeeds.
  - Shift a required column and verify the dialog appears before load completes.

### Feature Area: General KPI filtering

- Status: `implemented`
- Main entry points / relevant files:
  - `lab_kpi_pyqt6_app.py`
- User-visible behavior:
  - Supports date range, researcher, WBP Code, and Product ID filters.
  - Shows detail, task scheduling, score, FTE, efficiency, and TAT tabs.
- Limitations / caveats:
  - Time-bounded KPI tabs always use completion date `AG`.
- Validation hints:
  - Verify that rows with `AG` outside the selected range never appear in detail or score-related tabs.

### Feature Area: FCT selection

- Status: `implemented`
- Main entry points / relevant files:
  - `lab_kpi_pyqt6_app.py`
- User-visible behavior:
  - After loading data, the app lists unique `A`-column values and lets the operator select one as the FCT type.
  - FTE and efficiency tabs require this selection before calculating.
- Limitations / caveats:
  - Only one FCT value can be selected at a time.
  - The choice is not persisted across sessions.
- Validation hints:
  - Leave the selector empty and confirm FTE/efficiency tabs show guidance instead of stale numbers.

### Feature Area: Old-employee FTE

- Status: `implemented`
- Main entry points / relevant files:
  - `lab_kpi_pyqt6_app.py`
- User-visible behavior:
  - Excludes rows where `是否新人=是`.
  - Produces both `含非FCT` and `不含非FCT` FTE views in one combined FTE tab.
  - Shows `尚未获得的积分`, defined as the sum of `AI` where `AG` is empty, grouped by researcher.
- Limitations / caveats:
  - The `不含非FCT` FTE interpretation becomes a binary active-person measure because only selected FCT rows remain.
- Validation hints:
  - Create a dataset with mixed new and old employees and verify only old employees appear on FTE tabs.

### Feature Area: Delivery efficiency

- Status: `implemented`
- Main entry points / relevant files:
  - `lab_kpi_pyqt6_app.py`
  - `README_PyQt6.md`
- User-visible behavior:
  - Efficiency is based on `AG` within the selected closed interval.
  - A molecule is counted as completed only if at least one row for the same `C|D` is `FCT`, has `Request activity=Bulk`, and has non-empty `AG` within the selected period.
  - Reports a single efficiency result using `completed molecules / sum of selected researchers' FTE values`.
- Limitations / caveats:
  - Delivery does not require a matching `Pilot` stage.
  - Efficiency shares the same completion-date basis as the general KPI tabs.
- Validation hints:
  - Verify that `Pilot`-only completed rows never count as completed molecules.

### Feature Area: TAT calculation

- Status: `implemented`
- Main entry points / relevant files:
  - `lab_kpi_pyqt6_app.py`
  - `README_PyQt6.md`
- User-visible behavior:
  - Shows FCT molecules whose `Bulk` completion date `AG` falls within the selected period.
  - Computes TAT as `latest Bulk AG - earliest Pilot AF` for the same `C|D`.
  - Highlights rows where `TAT > 10` and reports total/red-count statistics below the main table.
- Limitations / caveats:
  - TAT ignores researcher, WBP Code, and Product ID filters.
  - Molecules without a usable Pilot start date are excluded.
- Validation hints:
  - Verify that changing researcher or WBP filters does not change TAT results.
  - Verify that `TAT = 10` is not highlighted while `TAT = 11` is highlighted.
