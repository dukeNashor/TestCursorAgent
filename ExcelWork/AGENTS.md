# AGENTS

Use this file for stable, always-on repository guidance.

## Baseline Rules

- Keep changes scoped to the requested task.
- Prefer small, verifiable steps.
- Run targeted validation before broad validation.
- Do not rewrite task history; update task files instead.

## Required Startup Context

When beginning work, read these files in order:

1. `AGENTS.md`
2. `PLANS.md`
3. `docs/tasks/index.md`
4. Active task file under `docs/tasks/`

## Task Switching Protocol

Before switching away from a task:

1. Update `docs/tasks/<task>.md`.
2. Record `status`, `next_step`, and latest validation outcome.
3. Update `docs/tasks/index.md` to reflect state transitions.
4. Only then switch to another task.

## Task File Status Values

Use only:

- `planned`
- `active`
- `blocked`
- `done`
- `abandoned`

