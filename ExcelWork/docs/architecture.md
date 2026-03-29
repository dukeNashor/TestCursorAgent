# Architecture Overview

Last updated: 2026-03-29

## System Overview

- This project is a single-file PyQt6 desktop dashboard for reading laboratory production Excel workbooks and calculating task scheduling, score, FTE, delivery efficiency, and TAT metrics.
- The runtime has three core concerns:
  - workbook ingestion with fixed-column plus header-discovered fields
  - filter-state driven pandas transformations
  - tabular and chart rendering inside a single main window

## System Boundary

- In scope:
  - Read-only ingestion of Excel workbook data
  - Header-based lookup for `是否新人` and `Request activity`
  - KPI calculations for detail, task scheduling, score, FTE, efficiency, and TAT
  - Interactive filtering and chart updates
- Out of scope:
  - Writing back to source Excel files
  - Persisting team-specific mappings outside the running session
  - Multi-file aggregation or server-side processing
- External systems / dependencies:
  - `openpyxl` for workbook parsing
  - `pandas` for transformations
  - `PyQt6` for desktop UI
  - `matplotlib` for chart rendering

## High-Level Module Map

- `LabKPIDashboard`:
  - owns UI widgets, filter state, data refresh flow, and chart payloads
- Workbook ingestion helpers:
  - parse fixed business columns
  - build normalized header catalog from rows 2-3
  - locate dynamic columns such as `是否新人` and `Request activity`
  - validate required field mappings and launch a manual mapping dialog when auto-resolution fails
- KPI transformation helpers:
  - prepare derived fields (`stat_date`, `is_non_other`, `ag_in_period_for_efficiency`, `is_delivered_bulk_record`)
  - build shared filtered bases for standard tabs, old-employee FTE, AG-based efficiency, and molecule-level TAT aggregation

## Main Runtime and Data Flows

1. Load workbook:
   - User selects file and sheet.
   - The app scans header rows, validates required dynamic columns, then reads row 4+ into a pandas DataFrame.
2. Build filter state:
   - UI controls produce a `FilterState`, including the selected FCT coupling type.
   - `_prepare_df_with_stat_date()` fixes general reporting to completion-date filtering and derives efficiency-specific flags.
3. Render metrics:
   - Standard tabs use the completion-date filter on `AG`.
   - The task-scheduling tab ignores the date window and only looks at unfinished rows.
   - FTE uses old-employee-only filtered bases and renders only the per-person FTE table/chart in one tab.
   - Efficiency uses the selected old-employee set, AG-closed-interval FCT completion logic, and the sum of per-researcher FTE values as denominator.
   - TAT uses the selected date window plus current FCT type, ignores researcher/WBP/Product filters, and aggregates earliest Pilot AF with latest in-period Bulk AG per molecule.

## Key Architectural Decisions

- Decision:
  Use fixed indexes for stable business columns and header-name lookup for dynamic fields.
  Rationale:
  Core business columns are known, while `是否新人` and `Request activity` may move by workbook layout.
  Consequence:
  The loader stays resilient to sheet variations without needing full schema abstraction.

- Decision:
  Keep manual column mappings in memory for the current app session only.
  Rationale:
  Operators may load multiple similarly structured files in one run, but the project does not yet need persisted mapping config.
  Consequence:
  A successful manual correction speeds up later loads in the same session without introducing config files.

- Decision:
  Treat the selected FCT coupling type as session UI state instead of a persisted mapping.
  Rationale:
  Current team differences are expressed by workbook-specific `A` column enumerations.
  Consequence:
  FTE and efficiency tabs must guard against missing selection before calculating.

- Decision:
  Use `AG` as the only reporting date basis for both general tabs and efficiency-related calculations.
  Rationale:
  The product requirement is to treat completion date as the single authoritative statistical date.
  Consequence:
  Rows without `AG` are excluded from time-bounded KPI tabs, while task scheduling remains the only unfinished-record view.

## Known Mismatches and Technical Debt

- The application remains concentrated in one Python file, so UI, ingestion, and KPI logic are tightly coupled.
- The combined FTE overview/per-person page still relies on shared in-memory chart payloads and tab-index routing.
- Session-only FCT selection avoids config complexity, but repeated operator choices are not persisted across runs.

## Safe Modification Guidance

- Areas safe to modify in isolation:
  - README and docs
  - chart labels and table column labels
  - helper methods that only post-process already-loaded DataFrames
- Areas requiring cross-module validation:
  - `_read_source_sheet()`
  - `_prepare_df_with_stat_date()`
  - FTE and efficiency helper filters
- Required validation checks:
  - missing required dynamic headers should fail fast with clear errors
  - `Pilot/Bulk` detection must remain case-insensitive
  - old-employee exclusion must only affect FTE/efficiency paths unless intentionally expanded

## Suggested Evolution

- Near-term evolution:
  - extract workbook schema helpers and KPI calculators into separate modules
- Mid-term evolution:
  - add explicit synthetic test fixtures for representative Excel layouts
- Deferred or optional evolution:
  - persist per-team coupling mappings or learn defaults per workbook family
