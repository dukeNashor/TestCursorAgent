#!/usr/bin/env python3
"""Generate docs/architecture.md and docs/features.md from repository inspection."""

import argparse
import re
import sys
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Set, Tuple


VALID_DOC_SCOPES = {"architecture", "features", "all"}
VALID_OVERWRITE_MODES = {"ask", "always", "never"}
VALID_DEPTHS = {"summary", "detailed"}

SKIP_DIR_NAMES = {
    ".git",
    ".hg",
    ".svn",
    ".idea",
    ".vscode",
    "__pycache__",
    "node_modules",
    "dist",
    "build",
    "out",
    "target",
    ".venv",
    "venv",
}

SOURCE_EXTENSIONS = {
    ".py",
    ".js",
    ".ts",
    ".jsx",
    ".tsx",
    ".go",
    ".rs",
    ".java",
    ".kt",
    ".cpp",
    ".cc",
    ".c",
    ".h",
    ".hpp",
    ".cs",
    ".rb",
    ".php",
    ".swift",
}

ENTRYPOINT_BASENAMES = {
    "main.py",
    "app.py",
    "manage.py",
    "index.js",
    "index.ts",
    "server.js",
    "server.ts",
    "main.go",
    "main.rs",
    "program.cs",
    "main.cpp",
    "main.c",
}

CONFIG_BASENAMES = {
    "pyproject.toml",
    "requirements.txt",
    "requirements-dev.txt",
    "poetry.lock",
    "package.json",
    "package-lock.json",
    "pnpm-lock.yaml",
    "yarn.lock",
    "go.mod",
    "cargo.toml",
    "pom.xml",
    "build.gradle",
    "build.gradle.kts",
    "cmakelists.txt",
    "dockerfile",
    "docker-compose.yml",
    "docker-compose.yaml",
    "makefile",
}

TEST_DIR_NAMES = {"test", "tests", "__tests__", "spec", "specs"}
STATUS_VALUES = {"implemented", "partial", "planned", "deprecated"}


@dataclass
class PlannedDoc:
    destination: Path
    exists: bool
    content: str


@dataclass
class DepthLimits:
    max_top_level: int
    max_entry_points: int
    max_modules: int
    max_tests: int
    max_features: int
    max_feature_files: int


def depth_limits(depth: str) -> DepthLimits:
    if depth == "summary":
        return DepthLimits(
            max_top_level=10,
            max_entry_points=8,
            max_modules=8,
            max_tests=6,
            max_features=8,
            max_feature_files=3,
        )
    return DepthLimits(
        max_top_level=20,
        max_entry_points=16,
        max_modules=16,
        max_tests=12,
        max_features=16,
        max_feature_files=6,
    )


def validate_repo_path(repo_path: Path) -> Path:
    if sys.version_info < (3, 9):
        raise ValueError("Python 3.9+ is required.")
    resolved = repo_path.expanduser().resolve()
    if not resolved.exists() or not resolved.is_dir():
        raise ValueError(f"Invalid --repo-path: {repo_path}")
    return resolved


def truncate_list(values: Sequence[str], limit: int) -> List[str]:
    if len(values) <= limit:
        return list(values)
    return list(values[:limit])


def normalize_slug(raw: str) -> str:
    value = raw.strip().lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    value = re.sub(r"-{2,}", "-", value).strip("-")
    return value


def iter_repo_files(repo_root: Path) -> List[Path]:
    files: List[Path] = []
    for root, dirnames, filenames in __import__("os").walk(repo_root):
        dirnames[:] = sorted(
            [d for d in dirnames if d not in SKIP_DIR_NAMES and not d.startswith(".pytest_cache")]
        )
        filenames = sorted(filenames)
        root_path = Path(root)
        for name in filenames:
            files.append(root_path / name)
    return files


def relative(path: Path, repo_root: Path) -> str:
    return path.resolve().relative_to(repo_root.resolve()).as_posix()


def has_source_file(path: Path) -> bool:
    if not path.exists() or not path.is_dir():
        return False
    for child in path.rglob("*"):
        if not child.is_file():
            continue
        if child.suffix.lower() in SOURCE_EXTENSIONS:
            return True
    return False


def build_signals(repo_root: Path, arch_depth: str, feature_depth: str) -> Dict[str, object]:
    top_level_dirs = sorted(
        [p.name for p in repo_root.iterdir() if p.is_dir() and p.name not in SKIP_DIR_NAMES]
    )
    top_level_files = sorted([p.name for p in repo_root.iterdir() if p.is_file()])
    all_files = iter_repo_files(repo_root)
    rel_files = [relative(p, repo_root) for p in all_files]

    entry_points: List[str] = []
    for rel_path in rel_files:
        lower = rel_path.lower()
        basename = Path(lower).name
        if basename in ENTRYPOINT_BASENAMES or "bootstrap" in basename:
            entry_points.append(rel_path)
    entry_points = sorted(set(entry_points))

    config_files: List[str] = []
    for rel_path in rel_files:
        basename = Path(rel_path).name.lower()
        if basename in CONFIG_BASENAMES:
            config_files.append(rel_path)
        elif rel_path in {".codex/config.toml", "codex/config.toml"}:
            config_files.append(rel_path)
    config_files = sorted(set(config_files))

    test_roots: Set[str] = set()
    global_test_files: List[str] = []
    for rel_path in rel_files:
        parts = Path(rel_path).parts[:-1]
        basename = Path(rel_path).name.lower()
        if any(part.lower() in TEST_DIR_NAMES for part in parts) or "test" in basename:
            global_test_files.append(rel_path)
        for idx, part in enumerate(parts):
            if part.lower() in TEST_DIR_NAMES:
                test_roots.add("/".join(parts[: idx + 1]))
    test_roots_sorted = sorted(test_roots)

    module_map: List[str] = []
    src_dir = repo_root / "src"
    if src_dir.exists() and src_dir.is_dir():
        for child in sorted(src_dir.iterdir(), key=lambda p: p.name.lower()):
            if child.is_dir():
                module_map.append(f"src/{child.name}")
            elif child.is_file() and child.suffix.lower() in SOURCE_EXTENSIONS:
                module_map.append(f"src/{child.name}")
    if not module_map:
        for child in sorted(repo_root.iterdir(), key=lambda p: p.name.lower()):
            if not child.is_dir():
                continue
            if child.name in {"docs"} | SKIP_DIR_NAMES:
                continue
            if has_source_file(child):
                module_map.append(child.name)

    feature_areas: List[Dict[str, object]] = []
    feature_candidates: List[Path] = []
    features_dir = repo_root / "features"
    if features_dir.exists() and features_dir.is_dir():
        feature_candidates = [
            p for p in sorted(features_dir.iterdir(), key=lambda p: p.name.lower()) if p.is_dir()
        ]
    elif src_dir.exists() and src_dir.is_dir():
        feature_candidates = [
            p for p in sorted(src_dir.iterdir(), key=lambda p: p.name.lower()) if p.is_dir()
        ]
    else:
        for child in sorted(repo_root.iterdir(), key=lambda p: p.name.lower()):
            if not child.is_dir():
                continue
            if child.name in {"docs"} | SKIP_DIR_NAMES:
                continue
            if has_source_file(child):
                feature_candidates.append(child)

    seen_feature_names: Set[str] = set()
    limits = depth_limits(feature_depth)
    for candidate in feature_candidates:
        feature_name = candidate.name.replace("_", " ").replace("-", " ").strip().title()
        if not feature_name:
            continue
        key = feature_name.lower()
        if key in seen_feature_names:
            continue
        seen_feature_names.add(key)

        source_files: List[str] = []
        test_files: List[str] = []
        matched_global_tests: List[str] = []
        slug = normalize_slug(candidate.name)
        for file_path in sorted(candidate.rglob("*")):
            if not file_path.is_file():
                continue
            rel = relative(file_path, repo_root)
            if any(part in SKIP_DIR_NAMES for part in file_path.parts):
                continue
            if any(part.lower() in TEST_DIR_NAMES for part in file_path.parts):
                test_files.append(rel)
            elif file_path.suffix.lower() in SOURCE_EXTENSIONS:
                source_files.append(rel)

        for test_path in global_test_files:
            test_base = Path(test_path).name.lower()
            if slug and slug.replace("-", "") in test_base.replace("_", "").replace("-", ""):
                matched_global_tests.append(test_path)

        has_source = bool(source_files)
        has_tests = bool(test_files) or bool(matched_global_tests)
        name_lower = candidate.name.lower()
        if "deprecated" in name_lower or "legacy" in name_lower or "obsolete" in name_lower:
            status = "deprecated"
            evidence = "Directory name indicates legacy/deprecated intent."
        elif has_source and has_tests:
            status = "implemented"
            evidence = "Source files detected and at least one matching test signal was found."
        elif has_source:
            status = "partial"
            evidence = "Source files detected; complete coverage evidence not established."
        else:
            status = "planned"
            evidence = "No implementation files detected for this area."

        feature_areas.append(
            {
                "name": feature_name,
                "status": status,
                "evidence": evidence,
                "entry_points": truncate_list(sorted(source_files), limits.max_feature_files),
                "test_hints": truncate_list(sorted(set(test_files + matched_global_tests)), limits.max_feature_files),
            }
        )
        if len(feature_areas) >= limits.max_features:
            break

    return {
        "top_level_dirs": top_level_dirs,
        "top_level_files": top_level_files,
        "entry_points": entry_points,
        "config_files": config_files,
        "test_roots": test_roots_sorted,
        "module_map": module_map,
        "feature_areas": feature_areas,
        "arch_depth": arch_depth,
        "feature_depth": feature_depth,
    }


def render_architecture(repo_root: Path, signals: Dict[str, object], depth: str) -> str:
    limits = depth_limits(depth)
    top_dirs = truncate_list(signals["top_level_dirs"], limits.max_top_level)
    entry_points = truncate_list(signals["entry_points"], limits.max_entry_points)
    module_map = truncate_list(signals["module_map"], limits.max_modules)
    config_files = truncate_list(signals["config_files"], limits.max_modules)
    test_roots = truncate_list(signals["test_roots"], limits.max_tests)

    lines: List[str] = []
    lines.append("# Architecture Overview")
    lines.append("")
    lines.append(f"Last updated: {date.today().isoformat()}")
    lines.append("")
    lines.append(
        "This document is maintainer-facing architecture guidance. It is not a README and not an API reference."
    )
    lines.append("")
    lines.append("## System Overview")
    lines.append("")
    lines.append(f"- Repository root: `{repo_root}`")
    lines.append(
        f"- Top-level directories (detected): {', '.join(f'`{d}`' for d in top_dirs) if top_dirs else '(none detected)'}"
    )
    lines.append(
        f"- Primary entry points (detected): {', '.join(f'`{p}`' for p in entry_points) if entry_points else '(no strong entry-point signal found)'}"
    )
    lines.append("")
    lines.append("## System Boundary")
    lines.append("")
    lines.append("- In scope:")
    lines.append(
        f"  - Core repository modules and configs under `{repo_root.name}`."
    )
    lines.append("- Out of scope:")
    lines.append("  - External services and infrastructure not represented in this repository.")
    lines.append("- External systems / dependencies:")
    lines.append(
        f"  - Config/manifests hinting integration points: {', '.join(f'`{c}`' for c in config_files) if config_files else '(none detected)'}"
    )
    lines.append("")
    lines.append("## High-Level Module Map")
    lines.append("")
    if module_map:
        for item in module_map:
            lines.append(f"- `{item}`")
    else:
        lines.append("- No clear module map detected; consider adding explicit module boundaries.")
    lines.append("")
    lines.append("## Main Runtime and Data Flows")
    lines.append("")
    if entry_points:
        lines.append("1. Runtime starts from detected entry points.")
        lines.append("2. Entry points delegate into core modules.")
        lines.append("3. Tests validate behavior around these execution paths.")
    else:
        lines.append("1. No deterministic runtime entry point could be inferred from filenames.")
        lines.append("2. Review bootstrap/startup scripts and update this section with concrete flow.")
    lines.append("")
    lines.append("## Key Architectural Decisions")
    lines.append("")
    lines.append("- Decision: Keep Codex coordination artifacts in dedicated docs and task files.")
    lines.append("  Rationale: Preserve stable guidance, process guidance, and task state separation.")
    lines.append("  Consequence: Operational context remains explicit and machine-readable.")
    lines.append("- Decision: Use deterministic, Python-only automation for repository documentation.")
    lines.append("  Rationale: Avoid shell-specific coupling and keep behavior portable.")
    lines.append("  Consequence: All update workflows can run through a single runtime path.")
    lines.append("")
    lines.append("## Known Mismatches and Technical Debt")
    lines.append("")
    if not test_roots:
        lines.append("- Test root signal is weak or absent.")
        lines.append("  Impact: Validation scope may be unclear for maintainers and Codex threads.")
        lines.append("  Risk: Modifications can regress behavior without focused test guidance.")
    else:
        lines.append("- Test roots are present but coverage depth is unknown from structure alone.")
        lines.append("  Impact: Implemented pathways may still have untested edge cases.")
        lines.append("  Risk: Structure-level inference can overestimate confidence.")
    lines.append("")
    lines.append("## Safe Modification Guidance")
    lines.append("")
    lines.append("- Prefer localized edits inside one module boundary at a time.")
    lines.append("- Update task state docs when crossing module boundaries or changing execution flow.")
    lines.append("- Run targeted checks nearest to changed entry points and touched modules.")
    lines.append("")
    lines.append("## Suggested Evolution")
    lines.append("")
    lines.append("- Near-term: refine this document with explicit runtime call paths.")
    lines.append("- Mid-term: add explicit module ownership and dependency constraints.")
    lines.append("- Deferred: add architecture decision records for high-impact refactors.")
    lines.append("")
    return "\n".join(lines)


def render_features(repo_root: Path, signals: Dict[str, object], depth: str) -> str:
    limits = depth_limits(depth)
    features = truncate_list(signals["feature_areas"], limits.max_features)
    test_roots = truncate_list(signals["test_roots"], limits.max_tests)

    lines: List[str] = []
    lines.append("# Feature Inventory")
    lines.append("")
    lines.append(f"Last updated: {date.today().isoformat()}")
    lines.append("")
    lines.append("## Feature Status Scale")
    lines.append("")
    lines.append("- `implemented`: behavior appears present with clear implementation and validation signals.")
    lines.append("- `partial`: behavior appears present but confidence/coverage is incomplete.")
    lines.append("- `planned`: intent exists but implementation signal is weak.")
    lines.append("- `deprecated`: capability appears legacy and should not be expanded.")
    lines.append("")
    lines.append("## Major Feature Areas")
    lines.append("")

    if not features:
        lines.append("### Feature Area: (not detected)")
        lines.append("")
        lines.append("- Status: `planned`")
        lines.append("- Main entry points / relevant files: (none detected)")
        lines.append("- User-visible behavior: Unable to infer from structure alone.")
        lines.append("- Limitations / caveats: Add explicit feature modules or docs to improve discoverability.")
        lines.append("- Validation hints: Establish dedicated test roots and feature-level tests.")
        lines.append("")
        return "\n".join(lines)

    for feature in features:
        status = feature["status"]
        if status not in STATUS_VALUES:
            status = "partial"
        lines.append(f"### Feature Area: {feature['name']}")
        lines.append("")
        lines.append(f"- Status: `{status}`")
        lines.append(
            "- Main entry points / relevant files: "
            + (
                ", ".join(f"`{p}`" for p in feature["entry_points"])
                if feature["entry_points"]
                else "(none detected)"
            )
        )
        lines.append(
            f"- User-visible behavior: Provides `{feature['name']}` related behavior (inferred from repository structure)."
        )
        lines.append(f"- Limitations / caveats: {feature['evidence']}")
        lines.append(
            "- Validation hints: "
            + (
                ", ".join(f"`{p}`" for p in feature["test_hints"])
                if feature["test_hints"]
                else (
                    ", ".join(f"`{p}`" for p in test_roots)
                    if test_roots
                    else "No direct test hint for this feature; add targeted tests."
                )
            )
        )
        lines.append("")
    return "\n".join(lines)


def build_plan(
    repo_root: Path,
    doc_scope: str,
    architecture_content: str,
    features_content: str,
) -> List[PlannedDoc]:
    if doc_scope not in VALID_DOC_SCOPES:
        raise ValueError(f"Invalid doc_scope '{doc_scope}'.")

    mappings: List[Tuple[str, str]] = []
    if doc_scope == "architecture":
        mappings = [("docs/architecture.md", architecture_content)]
    elif doc_scope == "features":
        mappings = [("docs/features.md", features_content)]
    else:
        mappings = [
            ("docs/architecture.md", architecture_content),
            ("docs/features.md", features_content),
        ]

    plan: List[PlannedDoc] = []
    for rel_path, content in mappings:
        destination = (repo_root / rel_path).resolve()
        plan.append(PlannedDoc(destination=destination, exists=destination.exists(), content=content))
    return plan


def print_plan(repo_root: Path, plan: Sequence[PlannedDoc]) -> None:
    print(f"[INFO] Target path: {repo_root}")
    print("[INFO] Planned files:")
    for item in plan:
        state = "CONFLICT" if item.exists else "CREATE"
        print(f"[PLAN] {state} {item.destination}")


def apply_plan(plan: Sequence[PlannedDoc], overwrite_mode: str) -> Dict[str, List[str]]:
    summary: Dict[str, List[str]] = {
        "created": [],
        "overwritten": [],
        "skipped": [],
        "failed": [],
    }
    for item in plan:
        if item.exists and overwrite_mode in {"never", "ask"}:
            summary["skipped"].append(str(item.destination))
            continue
        try:
            item.destination.parent.mkdir(parents=True, exist_ok=True)
            item.destination.write_text(item.content, encoding="utf-8")
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
    parser = argparse.ArgumentParser(
        description="Generate docs/architecture.md and docs/features.md from repository inspection.",
    )
    parser.add_argument("--repo-path", required=True, help="Target repository path.")
    parser.add_argument(
        "--doc-scope",
        default="all",
        choices=sorted(VALID_DOC_SCOPES),
        help="Document scope: architecture, features, all. Default: all",
    )
    parser.add_argument(
        "--architecture-depth",
        default="detailed",
        choices=sorted(VALID_DEPTHS),
        help="Architecture detail level: summary or detailed. Default: detailed",
    )
    parser.add_argument(
        "--feature-depth",
        default="detailed",
        choices=sorted(VALID_DEPTHS),
        help="Feature detail level: summary or detailed. Default: detailed",
    )
    parser.add_argument(
        "--overwrite",
        default="ask",
        choices=sorted(VALID_OVERWRITE_MODES),
        help="Conflict policy: ask, always, never. Default: ask",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show plan only and perform no writes.",
    )
    args = parser.parse_args()

    try:
        repo_root = validate_repo_path(Path(args.repo_path))
        signals = build_signals(repo_root, args.architecture_depth, args.feature_depth)
        architecture_content = render_architecture(repo_root, signals, args.architecture_depth)
        features_content = render_features(repo_root, signals, args.feature_depth)
        plan = build_plan(repo_root, args.doc_scope, architecture_content, features_content)
    except Exception as exc:
        print(f"[ERROR] {exc}")
        return 1

    conflicts = [item for item in plan if item.exists]
    print_plan(repo_root, plan)

    if args.dry_run:
        print("[INFO] Dry run complete. No files were written.")
        return 0

    if conflicts and args.overwrite == "ask":
        print("[ACTION REQUIRED] Conflicts detected and overwrite mode is 'ask'.")
        for item in conflicts:
            print(f"[CONFLICT] {item.destination}")
        print("[ACTION REQUIRED] Re-run with --overwrite always or --overwrite never.")
        return 2

    summary = apply_plan(plan, args.overwrite)
    print_summary(summary)
    if summary["failed"]:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
