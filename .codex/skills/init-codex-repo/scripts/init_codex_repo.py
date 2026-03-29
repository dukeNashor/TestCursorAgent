#!/usr/bin/env python3
"""Initialize Codex repo collaboration files in a target path."""

import argparse
import re
import sys
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Dict, List


VALID_REPO_MODES = {"new", "existing", "subproject"}
VALID_OVERWRITE_MODES = {"ask", "always", "never"}
VALID_DOC_SCOPES = {"context", "architecture", "features", "all"}


@dataclass
class PlannedFile:
    destination: Path
    template: Path
    exists: bool


def normalize_task_slug(task_slug: str) -> str:
    normalized = task_slug.strip().lower()
    normalized = re.sub(r"[^a-z0-9]+", "-", normalized)
    normalized = normalized.strip("-")
    normalized = re.sub(r"-{2,}", "-", normalized)
    if not normalized:
        raise ValueError("Task slug must contain at least one letter or digit.")
    return normalized


def validate_target_path(target_path: Path, repo_mode: str) -> Path:
    if repo_mode not in VALID_REPO_MODES:
        raise ValueError(f"Invalid repo_mode '{repo_mode}'.")

    target_path = target_path.expanduser().resolve()

    if repo_mode == "new":
        if target_path.exists() and not target_path.is_dir():
            raise ValueError(f"Target path exists and is not a directory: {target_path}")
        return target_path

    if not target_path.exists():
        raise ValueError(f"Target path does not exist for repo_mode='{repo_mode}': {target_path}")
    if not target_path.is_dir():
        raise ValueError(f"Target path is not a directory: {target_path}")
    return target_path


def template_root(script_path: Path) -> Path:
    root = script_path.resolve().parent.parent / "assets" / "templates"
    if not root.exists() or not root.is_dir():
        raise ValueError(f"Templates directory not found: {root}")
    return root


def build_plan(target_path: Path, templates_dir: Path, task_slug: str, doc_scope: str) -> List[PlannedFile]:
    if doc_scope not in VALID_DOC_SCOPES:
        raise ValueError(f"Invalid doc_scope '{doc_scope}'.")

    context_mappings = [
        ("AGENTS.md", "AGENTS.md"),
        ("PLANS.md", "PLANS.md"),
        (".codex/config.toml", ".codex-config.toml"),
        ("docs/tasks/index.md", "tasks-index.md"),
        (f"docs/tasks/{task_slug}.md", "task-template.md"),
    ]
    architecture_mappings = [("docs/architecture.md", "architecture.md")]
    features_mappings = [("docs/features.md", "features.md")]

    if doc_scope == "context":
        mappings = context_mappings
    elif doc_scope == "architecture":
        mappings = architecture_mappings
    elif doc_scope == "features":
        mappings = features_mappings
    else:
        mappings = context_mappings + architecture_mappings + features_mappings

    plan: List[PlannedFile] = []
    for rel_dest, template_name in mappings:
        template = templates_dir / template_name
        if not template.exists():
            raise ValueError(f"Required template is missing: {template}")
        destination = target_path / Path(rel_dest)
        plan.append(PlannedFile(destination=destination, template=template, exists=destination.exists()))
    return plan


def render_template(template_text: str, replacements: Dict[str, str]) -> str:
    rendered = template_text
    for key, value in replacements.items():
        rendered = rendered.replace(f"{{{{{key}}}}}", value)
    return rendered


def print_plan(plan: List[PlannedFile], target_path: Path) -> None:
    print(f"[INFO] Target path: {target_path}")
    print("[INFO] Planned files:")
    for item in plan:
        state = "CONFLICT" if item.exists else "CREATE"
        print(f"[PLAN] {state} {item.destination}")


def apply_plan(plan: List[PlannedFile], replacements: Dict[str, str], overwrite_mode: str) -> Dict[str, List[str]]:
    summary: Dict[str, List[str]] = {
        "created": [],
        "overwritten": [],
        "skipped": [],
        "failed": [],
    }

    for item in plan:
        if item.exists and overwrite_mode == "never":
            summary["skipped"].append(str(item.destination))
            continue
        if item.exists and overwrite_mode == "ask":
            summary["skipped"].append(str(item.destination))
            continue

        try:
            item.destination.parent.mkdir(parents=True, exist_ok=True)
            template_text = item.template.read_text(encoding="utf-8")
            rendered = render_template(template_text, replacements)
            item.destination.write_text(rendered, encoding="utf-8")
            if item.exists:
                summary["overwritten"].append(str(item.destination))
            else:
                summary["created"].append(str(item.destination))
        except Exception as exc:  # pragma: no cover
            summary["failed"].append(f"{item.destination}: {exc}")

    return summary


def print_summary(summary: Dict[str, List[str]]) -> None:
    print(f"[SUMMARY] created={len(summary['created'])}")
    for path in summary["created"]:
        print(f"[CREATED] {path}")

    print(f"[SUMMARY] overwritten={len(summary['overwritten'])}")
    for path in summary["overwritten"]:
        print(f"[OVERWRITTEN] {path}")

    print(f"[SUMMARY] skipped={len(summary['skipped'])}")
    for path in summary["skipped"]:
        print(f"[SKIPPED] {path}")

    print(f"[SUMMARY] failed={len(summary['failed'])}")
    for failure in summary["failed"]:
        print(f"[FAILED] {failure}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Initialize Codex repo collaboration files.")
    parser.add_argument("--target-path", required=True, help="Target repo root or subproject path.")
    parser.add_argument(
        "--repo-mode",
        required=True,
        choices=sorted(VALID_REPO_MODES),
        help="Target mode: new, existing, or subproject.",
    )
    parser.add_argument(
        "--task-slug",
        default="getting-started",
        help="Task file slug under docs/tasks/. Default: getting-started",
    )
    parser.add_argument(
        "--overwrite",
        default="ask",
        choices=sorted(VALID_OVERWRITE_MODES),
        help="Conflict policy: ask, always, never. Default: ask",
    )
    parser.add_argument(
        "--doc-scope",
        default="all",
        choices=sorted(VALID_DOC_SCOPES),
        help="Document scope: context, architecture, features, all. Default: all",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show plan only and perform no writes.",
    )
    args = parser.parse_args()

    try:
        task_slug = normalize_task_slug(args.task_slug)
        if task_slug != args.task_slug:
            print(f"[INFO] Normalized task slug '{args.task_slug}' -> '{task_slug}'")

        target_path = validate_target_path(Path(args.target_path), args.repo_mode)
        templates_dir = template_root(Path(__file__))
        plan = build_plan(target_path, templates_dir, task_slug, args.doc_scope)
    except Exception as exc:
        print(f"[ERROR] {exc}")
        return 1

    conflicts = [item for item in plan if item.exists]
    print_plan(plan, target_path)

    if args.dry_run:
        print("[INFO] Dry run complete. No files were written.")
        return 0

    if conflicts and args.overwrite == "ask":
        print("[ACTION REQUIRED] Conflicts detected and overwrite mode is 'ask'.")
        for item in conflicts:
            print(f"[CONFLICT] {item.destination}")
        print("[ACTION REQUIRED] Re-run with --overwrite always or --overwrite never.")
        return 2

    replacements = {
        "TASK_SLUG": task_slug,
        "TODAY": date.today().isoformat(),
    }
    summary = apply_plan(plan, replacements, args.overwrite)
    print_summary(summary)

    if summary["failed"]:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
