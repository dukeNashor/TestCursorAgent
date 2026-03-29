---
name: init-codex-repo
description: Initialize, generate, and inspect Codex repository context documents using Python-only workflows. Use when Codex needs deterministic initialization of AGENTS.md, PLANS.md, .codex/config.toml, docs/tasks/index.md, docs/tasks/task-slug.md, docs/architecture.md, and docs/features.md; or when Codex needs a local read-only web viewer for repository context documents.
---

# Init Codex Repo

## Overview

Provide three Python-only workflows:

1. Initialize repository-scoped Codex context files from deterministic templates.
2. Generate `docs/architecture.md` and `docs/features.md` drafts for existing repositories.
3. Inspect repository context in a local read-only web viewer.

Do not depend on PowerShell or Bash features.

## Required Inputs

Collect these inputs before running any command:

1. `python_executable` (required, absolute path)
2. `target_path` (required)
3. `repo_mode` (`new`, `existing`, or `subproject`; initializer only)
4. `task_slug` (optional, initializer only, default `getting-started`)
5. `doc_scope` (optional):
   - initializer: `context|architecture|features|all` (default `all`)
   - generator: `architecture|features|all` (default `all`)
6. `overwrite` (`ask|always|never`, default `ask`)
7. `layout` (viewer only: `auto`, `tasks`, or `plans`; default `auto`)
8. `host` and `port` (viewer only; defaults `127.0.0.1:8765`)
9. `architecture_depth` (generator only: `summary|detailed`, default `detailed`)
10. `feature_depth` (generator only: `summary|detailed`, default `detailed`)

## Workflow A: Initialize Repo Context

1. Validate runtime:
   - Run:
     ```bash
     <python_executable> --version
     ```
   - Require Python 3.9+.
2. Preview changes first:
   - Run:
     ```bash
     <python_executable> scripts/init_codex_repo.py --target-path "<target_path>" --repo-mode <repo_mode> --task-slug <task_slug> --doc-scope all --overwrite ask --dry-run
     ```
3. Execute with `ask` mode:
   - Run:
     ```bash
     <python_executable> scripts/init_codex_repo.py --target-path "<target_path>" --repo-mode <repo_mode> --task-slug <task_slug> --doc-scope all --overwrite ask
     ```
4. Handle conflicts:
   - If exit code is `2`, read the reported conflict list.
   - Ask user a single decision: overwrite all conflicts or keep all existing conflicted files.
   - Re-run with:
     - overwrite all: `--overwrite always`
     - keep existing: `--overwrite never`
5. Report final result with counts and concrete file paths.

## Workflow B: Generate Architecture and Feature Docs for Existing Repos

1. Validate runtime and repository path.
2. Preview generation first:
   - Run:
     ```bash
     <python_executable> scripts/generate_repo_docs.py --repo-path "<target_path>" --doc-scope all --architecture-depth detailed --feature-depth detailed --overwrite ask --dry-run
     ```
3. Execute generation:
   - Run:
     ```bash
     <python_executable> scripts/generate_repo_docs.py --repo-path "<target_path>" --doc-scope all --architecture-depth detailed --feature-depth detailed --overwrite ask
     ```
4. Handle conflicts with the same `ask|always|never` policy and exit-code `2` behavior.
5. Keep generated content deterministic and maintainer-facing:
   - `docs/architecture.md` is structural architecture guidance (not README/API reference).
   - `docs/features.md` is capability inventory with conservative status inference.

## Workflow C: Inspect Repo Context

1. Validate runtime and repository path:
   - Run:
     ```bash
     <python_executable> --version
     ```
   - Require Python 3.9+.
2. Start viewer:
   - Run:
     ```bash
     <python_executable> scripts/codex_repo_viewer.py --repo-path "<target_path>" --layout auto --host 127.0.0.1 --port 8765 --open-browser
     ```
3. Use viewer sections:
   - `Core`: `AGENTS.md`, `PLANS.md`
   - `Architecture`: `docs/architecture.md`
   - `Features`: `docs/features.md`
   - `Current Task`: preferred current-task document
   - `Tasks`: `docs/tasks/index.md` and `docs/tasks/*.md`
   - `Plans`: `docs/plans/*.md`
4. Interpret current-task resolution:
   - priority 1: `docs/current-task.md` if it exists
   - priority 2: active task parsed from `docs/tasks/index.md`
   - priority 3: most recently modified task file under `docs/tasks/`

## Command Reference: Initializer

```bash
<python_executable> scripts/init_codex_repo.py \
  --target-path "<path>" \
  --repo-mode <new|existing|subproject> \
  --task-slug <task-slug> \
  --doc-scope <context|architecture|features|all> \
  --overwrite <ask|always|never> \
  [--dry-run]
```

## Command Reference: Architecture/Features Generator

```bash
<python_executable> scripts/generate_repo_docs.py \
  --repo-path "<path>" \
  --doc-scope <architecture|features|all> \
  --architecture-depth <summary|detailed> \
  --feature-depth <summary|detailed> \
  --overwrite <ask|always|never> \
  [--dry-run]
```

## Command Reference: Viewer

```bash
<python_executable> scripts/codex_repo_viewer.py \
  --repo-path "<path>" \
  [--host 127.0.0.1] \
  [--port 8765] \
  [--open-browser] \
  [--layout auto|tasks|plans]
```

## Output Contract

The initializer/generator may create or update only:

- `AGENTS.md`
- `PLANS.md`
- `.codex/config.toml`
- `docs/tasks/index.md`
- `docs/tasks/<task_slug>.md`
- `docs/architecture.md`
- `docs/features.md`

If conflicts are present and `--overwrite ask` is used, it must perform no writes and return exit code `2`.

The viewer serves read-only local endpoints:

- `GET /`: single-page viewer UI
- `GET /api/context`: repository context index JSON
- `GET /api/doc?path=<relative_path>`: single document content with path-safety checks

## Document Roles

- `AGENTS.md`: stable project guidance.
- `PLANS.md`: execution/process guidance.
- `docs/tasks/*.md`: task state.
- `docs/architecture.md`: structural system description.
- `docs/features.md`: current feature inventory.

## Resources

- `scripts/init_codex_repo.py`: Python-only initializer.
- `scripts/generate_repo_docs.py`: Python-only architecture/features generator.
- `scripts/codex_repo_viewer.py`: Python-only local web viewer.
- `assets/templates/*`: canonical templates rendered into the target path.
