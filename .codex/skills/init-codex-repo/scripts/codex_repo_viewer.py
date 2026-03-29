#!/usr/bin/env python3
"""Read-only local web viewer for Codex repo context documents."""

import argparse
import json
import re
import sys
import webbrowser
from datetime import datetime, timezone
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple
from urllib.parse import parse_qs, urlparse


MAX_DOC_READ_BYTES = 1_000_000
STATUS_PATTERN = re.compile(r"(?im)^\s*status:\s*([a-z0-9_-]+)\s*$")


def iso_utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def iso_local_from_mtime(path: Path) -> str:
    return datetime.fromtimestamp(path.stat().st_mtime).astimezone().isoformat(timespec="seconds")


def normalize_slug(raw: str) -> str:
    value = raw.strip().lower()
    value = re.sub(r"[^a-z0-9._-]+", "-", value)
    value = value.strip("-._")
    value = re.sub(r"-{2,}", "-", value)
    return value


def parse_status_field(path: Path) -> Optional[str]:
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None
    match = STATUS_PATTERN.search(text[:64_000])
    return match.group(1) if match else None


def parse_active_task_slugs(index_text: str) -> List[str]:
    slugs: List[str] = []
    in_active = False
    for line in index_text.splitlines():
        heading = re.match(r"^\s*##\s+(.+?)\s*$", line)
        if heading:
            section = heading.group(1).strip().lower()
            if section == "active":
                in_active = True
                continue
            if in_active:
                break
        if not in_active:
            continue
        bullet = re.match(r"^\s*[-*]\s+(.+?)\s*$", line)
        if not bullet:
            continue
        raw_item = bullet.group(1).replace("`", "").strip()
        raw_item = raw_item.split("(")[0].strip()
        if not raw_item:
            continue
        lowered = raw_item.lower()
        if lowered in {"(none)", "none", "n/a"}:
            continue
        token = raw_item.split()[0].rstrip(",")
        basename = Path(token).name
        if basename.lower().endswith(".md"):
            basename = basename[:-3]
        slug = normalize_slug(basename)
        if slug and slug not in slugs:
            slugs.append(slug)
    return slugs


def safe_rel_path(path: Path, repo_root: Path) -> str:
    return path.resolve().relative_to(repo_root.resolve()).as_posix()


def build_doc_entry(
    repo_root: Path,
    rel_path: str,
    kind: str,
    note: str = "",
) -> Dict[str, object]:
    abs_path = (repo_root / Path(rel_path)).resolve()
    exists = abs_path.exists() and abs_path.is_file()
    entry: Dict[str, object] = {
        "path": rel_path,
        "kind": kind,
        "exists": exists,
        "size_bytes": None,
        "modified_at": None,
        "status": None,
        "is_active": False,
        "is_current": False,
        "note": note,
    }
    if exists:
        stat = abs_path.stat()
        entry["size_bytes"] = stat.st_size
        entry["modified_at"] = iso_local_from_mtime(abs_path)
        if rel_path.startswith("docs/tasks/") or rel_path.startswith("docs/plans/") or rel_path == "docs/current-task.md":
            entry["status"] = parse_status_field(abs_path)
    return entry


def discover_markdown_files(directory: Path) -> List[Path]:
    if not directory.exists() or not directory.is_dir():
        return []
    return sorted(
        [p for p in directory.iterdir() if p.is_file() and p.suffix.lower() == ".md"],
        key=lambda p: p.name.lower(),
    )


def most_recent_existing_doc(repo_root: Path, rel_paths: Sequence[str]) -> Optional[str]:
    candidates: List[Tuple[float, str]] = []
    for rel_path in rel_paths:
        abs_path = (repo_root / Path(rel_path)).resolve()
        if abs_path.exists() and abs_path.is_file():
            candidates.append((abs_path.stat().st_mtime, rel_path))
    if not candidates:
        return None
    candidates.sort(key=lambda item: item[0], reverse=True)
    return candidates[0][1]


def build_context(repo_root: Path, layout_mode: str) -> Dict[str, object]:
    if layout_mode not in {"auto", "tasks", "plans"}:
        raise ValueError(f"Unsupported layout mode: {layout_mode}")

    include_tasks = layout_mode in {"auto", "tasks"}
    include_plans = layout_mode in {"auto", "plans"}

    sections: Dict[str, List[str]] = {
        "core": [],
        "architecture": [],
        "features": [],
        "current_task": [],
        "tasks": [],
        "plans": [],
    }
    documents: Dict[str, Dict[str, object]] = {}
    warnings: List[str] = []

    def ensure(rel_path: str, kind: str, section: str, note: str = "") -> None:
        if rel_path not in documents:
            documents[rel_path] = build_doc_entry(repo_root, rel_path, kind, note=note)
        if rel_path not in sections[section]:
            sections[section].append(rel_path)

    # Core docs are always visible.
    ensure("AGENTS.md", "core", "core")
    ensure("PLANS.md", "core", "core")
    ensure("docs/architecture.md", "architecture", "architecture")
    ensure("docs/features.md", "features", "features")

    active_slugs: List[str] = []

    if include_tasks:
        ensure("docs/tasks/index.md", "task_index", "tasks")
        tasks_dir = repo_root / "docs" / "tasks"
        task_docs = [
            p for p in discover_markdown_files(tasks_dir) if p.name.lower() != "index.md"
        ]
        for path in task_docs:
            rel = safe_rel_path(path, repo_root)
            ensure(rel, "task", "tasks")

        index_abs = (repo_root / "docs" / "tasks" / "index.md").resolve()
        if index_abs.exists() and index_abs.is_file():
            text = index_abs.read_text(encoding="utf-8", errors="replace")
            active_slugs = parse_active_task_slugs(text)
            for slug in active_slugs:
                rel = f"docs/tasks/{slug}.md"
                note = "Referenced by Task Index Active section."
                ensure(rel, "task", "tasks", note=note)
                documents[rel]["is_active"] = True

    if include_plans:
        ensure("docs/current-task.md", "current_task", "current_task")
        plans_dir = repo_root / "docs" / "plans"
        for path in discover_markdown_files(plans_dir):
            rel = safe_rel_path(path, repo_root)
            ensure(rel, "plan", "plans")

    current_task_path: Optional[str] = None
    # Priority rules for auto mode.
    if layout_mode == "auto":
        current_rel = "docs/current-task.md"
        if current_rel in documents and documents[current_rel]["exists"]:
            current_task_path = current_rel
        else:
            for slug in active_slugs:
                rel = f"docs/tasks/{slug}.md"
                if rel in documents:
                    current_task_path = rel
                    break
            if not current_task_path:
                task_paths = [p for p in sections["tasks"] if p.startswith("docs/tasks/") and p != "docs/tasks/index.md"]
                current_task_path = most_recent_existing_doc(repo_root, task_paths)
    elif layout_mode == "tasks":
        for slug in active_slugs:
            rel = f"docs/tasks/{slug}.md"
            if rel in documents:
                current_task_path = rel
                break
        if not current_task_path:
            task_paths = [p for p in sections["tasks"] if p.startswith("docs/tasks/") and p != "docs/tasks/index.md"]
            current_task_path = most_recent_existing_doc(repo_root, task_paths)
    else:  # plans
        rel = "docs/current-task.md"
        if rel in documents and documents[rel]["exists"]:
            current_task_path = rel
        else:
            current_task_path = most_recent_existing_doc(repo_root, sections["plans"])

    if current_task_path:
        documents[current_task_path]["is_current"] = True
        if current_task_path not in sections["current_task"]:
            sections["current_task"].append(current_task_path)

    # Keep sections deterministic.
    sections["core"] = ["AGENTS.md", "PLANS.md"]
    sections["architecture"] = ["docs/architecture.md"]
    sections["features"] = ["docs/features.md"]
    sections["current_task"] = sorted(sections["current_task"], key=str.lower)
    sections["tasks"] = sorted(
        sections["tasks"],
        key=lambda p: (0 if p == "docs/tasks/index.md" else 1, p.lower()),
    )
    sections["plans"] = sorted(sections["plans"], key=str.lower)

    if not any(doc.get("exists") for doc in documents.values()):
        warnings.append("No known Codex context documents were found in this repository.")

    def any_existing(paths: Sequence[str]) -> bool:
        return any(bool(documents[path]["exists"]) for path in paths if path in documents)

    has_tasks = any_existing(sections["tasks"])
    has_plans = any_existing(sections["plans"]) or (
        "docs/current-task.md" in documents and bool(documents["docs/current-task.md"]["exists"])
    )
    if layout_mode == "auto":
        if has_tasks and has_plans:
            layout_effective = "mixed"
        elif has_tasks:
            layout_effective = "tasks"
        elif has_plans:
            layout_effective = "plans"
        else:
            layout_effective = "empty"
    else:
        layout_effective = layout_mode

    return {
        "repo_path": str(repo_root.resolve()),
        "layout_mode": layout_mode,
        "layout_effective": layout_effective,
        "generated_at": iso_utc_now(),
        "active_task_slugs": active_slugs,
        "current_task_path": current_task_path,
        "sections": sections,
        "documents": documents,
        "warnings": warnings,
    }


def resolve_safe_file(repo_root: Path, rel_path: str) -> Path:
    if not rel_path:
        raise ValueError("Missing 'path' query parameter.")
    candidate = Path(rel_path)
    if candidate.is_absolute():
        raise ValueError("Absolute paths are not allowed.")
    resolved = (repo_root / candidate).resolve()
    root_resolved = repo_root.resolve()
    try:
        resolved.relative_to(root_resolved)
    except ValueError as exc:
        raise ValueError("Path escapes repository root.") from exc
    return resolved


def read_document_payload(repo_root: Path, rel_path: str) -> Dict[str, object]:
    resolved = resolve_safe_file(repo_root, rel_path)
    if not resolved.exists() or not resolved.is_file():
        raise FileNotFoundError(f"File not found: {rel_path}")

    size = resolved.stat().st_size
    truncated = size > MAX_DOC_READ_BYTES
    with resolved.open("rb") as handle:
        raw = handle.read(MAX_DOC_READ_BYTES)
    content = raw.decode("utf-8", errors="replace")

    payload: Dict[str, object] = {
        "path": safe_rel_path(resolved, repo_root),
        "size_bytes": size,
        "modified_at": iso_local_from_mtime(resolved),
        "truncated": truncated,
        "max_read_bytes": MAX_DOC_READ_BYTES,
        "content": content,
    }
    if truncated:
        payload["truncation_notice"] = (
            f"File is larger than {MAX_DOC_READ_BYTES} bytes; returning the first chunk only."
        )
    return payload


HTML_PAGE = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Codex Repo Context Viewer</title>
  <style>
    :root {
      --bg: #f5f7fb;
      --panel: #ffffff;
      --ink: #17223b;
      --muted: #5a6a85;
      --line: #d8e0ef;
      --accent: #0f62fe;
      --ok: #147d64;
      --warn: #b86200;
      --bad: #b91c1c;
    }
    body {
      margin: 0;
      font-family: "Segoe UI", "Helvetica Neue", sans-serif;
      color: var(--ink);
      background: var(--bg);
    }
    header {
      padding: 12px 16px;
      border-bottom: 1px solid var(--line);
      background: linear-gradient(90deg, #e9f0ff, #f5f7fb);
    }
    header h1 {
      margin: 0;
      font-size: 18px;
    }
    header .meta {
      margin-top: 4px;
      color: var(--muted);
      font-size: 12px;
    }
    #root {
      display: grid;
      grid-template-columns: 360px 1fr;
      min-height: calc(100vh - 70px);
    }
    #sidebar {
      border-right: 1px solid var(--line);
      background: var(--panel);
      padding: 12px;
      overflow: auto;
    }
    #content {
      padding: 12px 16px;
      overflow: auto;
    }
    .section {
      margin-bottom: 14px;
    }
    .section h2 {
      margin: 0 0 6px 0;
      font-size: 13px;
      text-transform: uppercase;
      letter-spacing: 0.04em;
      color: var(--muted);
    }
    .item {
      border: 1px solid var(--line);
      border-radius: 8px;
      background: #fff;
      margin-bottom: 6px;
      padding: 8px;
      cursor: pointer;
    }
    .item:hover {
      border-color: var(--accent);
    }
    .item.active {
      border-color: var(--accent);
      box-shadow: 0 0 0 1px var(--accent) inset;
    }
    .row {
      display: flex;
      justify-content: space-between;
      gap: 8px;
      align-items: center;
    }
    .path {
      font-family: Consolas, "Courier New", monospace;
      font-size: 12px;
      overflow-wrap: anywhere;
    }
    .badges {
      display: flex;
      gap: 4px;
      flex-wrap: wrap;
    }
    .badge {
      font-size: 10px;
      border-radius: 999px;
      padding: 2px 6px;
      border: 1px solid var(--line);
      color: var(--muted);
      background: #f8faff;
    }
    .badge.current { border-color: var(--accent); color: var(--accent); }
    .badge.active { border-color: var(--ok); color: var(--ok); }
    .badge.missing { border-color: var(--bad); color: var(--bad); }
    .meta-text {
      margin-top: 6px;
      color: var(--muted);
      font-size: 11px;
    }
    .panel {
      border: 1px solid var(--line);
      border-radius: 10px;
      background: var(--panel);
      padding: 10px 12px;
      margin-bottom: 10px;
    }
    .panel h3 {
      margin: 0 0 8px 0;
      font-size: 14px;
    }
    pre {
      margin: 0;
      white-space: pre-wrap;
      word-break: break-word;
      font-family: Consolas, "Courier New", monospace;
      font-size: 12px;
      line-height: 1.45;
    }
    .warning {
      border-color: #f0cd87;
      background: #fff8e8;
      color: #6f4b00;
    }
    @media (max-width: 980px) {
      #root { grid-template-columns: 1fr; }
      #sidebar { border-right: none; border-bottom: 1px solid var(--line); }
    }
  </style>
</head>
<body>
  <header>
    <h1>Codex Repo Context Viewer</h1>
    <div id="header-meta" class="meta">Loading context…</div>
  </header>
  <main id="root">
    <aside id="sidebar"></aside>
    <section id="content"></section>
  </main>
  <script>
    const SECTIONS = [
      { key: "core", label: "Core" },
      { key: "architecture", label: "Architecture" },
      { key: "features", label: "Features" },
      { key: "current_task", label: "Current Task" },
      { key: "tasks", label: "Tasks" },
      { key: "plans", label: "Plans" }
    ];
    let state = { context: null, selectedPath: null };

    async function fetchJson(url) {
      const res = await fetch(url);
      if (!res.ok) {
        const text = await res.text();
        throw new Error(text || ("HTTP " + res.status));
      }
      return res.json();
    }

    function esc(value) {
      return (value ?? "").toString()
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;");
    }

    function selectInitialPath(context) {
      if (context.current_task_path) return context.current_task_path;
      for (const section of SECTIONS) {
        const paths = context.sections[section.key] || [];
        for (const p of paths) {
          const doc = context.documents[p];
          if (doc && doc.exists) return p;
        }
      }
      return null;
    }

    function renderSidebar() {
      const sidebar = document.getElementById("sidebar");
      const context = state.context;
      const chunks = [];

      for (const section of SECTIONS) {
        const paths = context.sections[section.key] || [];
        if (!paths.length) continue;
        chunks.push(`<div class="section"><h2>${esc(section.label)}</h2>`);
        for (const path of paths) {
          const doc = context.documents[path];
          if (!doc) continue;
          const badges = [];
          if (!doc.exists) badges.push(`<span class="badge missing">missing</span>`);
          if (doc.is_current) badges.push(`<span class="badge current">current</span>`);
          if (doc.is_active) badges.push(`<span class="badge active">active</span>`);
          if (doc.status) badges.push(`<span class="badge">status:${esc(doc.status)}</span>`);
          const selected = state.selectedPath === path ? "active" : "";
          chunks.push(`
            <div class="item ${selected}" data-path="${esc(path)}">
              <div class="row">
                <div class="path">${esc(path)}</div>
                <div class="badges">${badges.join("")}</div>
              </div>
              <div class="meta-text">${doc.exists ? "present" : "missing"}${doc.note ? " · " + esc(doc.note) : ""}</div>
            </div>
          `);
        }
        chunks.push(`</div>`);
      }

      sidebar.innerHTML = chunks.join("");
      for (const node of sidebar.querySelectorAll(".item")) {
        node.addEventListener("click", () => {
          const path = node.getAttribute("data-path");
          state.selectedPath = path;
          renderSidebar();
          renderDoc(path);
        });
      }
    }

    async function renderDoc(path) {
      const content = document.getElementById("content");
      const context = state.context;
      const doc = context.documents[path];
      if (!doc) {
        content.innerHTML = `<div class="panel warning"><h3>Unknown document</h3><pre>${esc(path)}</pre></div>`;
        return;
      }
      if (!doc.exists) {
        content.innerHTML = `
          <div class="panel warning">
            <h3>Missing document</h3>
            <pre>${esc(path)}</pre>
          </div>
        `;
        return;
      }

      content.innerHTML = `<div class="panel"><h3>Loading ${esc(path)}…</h3></div>`;
      try {
        const payload = await fetchJson("/api/doc?path=" + encodeURIComponent(path));
        const metaRows = [
          `Path: ${payload.path}`,
          `Size: ${payload.size_bytes} bytes`,
          `Modified: ${payload.modified_at}`,
          `Truncated: ${payload.truncated ? "yes" : "no"}`
        ];
        if (payload.truncation_notice) {
          metaRows.push(payload.truncation_notice);
        }
        content.innerHTML = `
          <div class="panel">
            <h3>Metadata</h3>
            <pre>${esc(metaRows.join("\\n"))}</pre>
          </div>
          <div class="panel">
            <h3>Content</h3>
            <pre>${esc(payload.content)}</pre>
          </div>
        `;
      } catch (err) {
        content.innerHTML = `<div class="panel warning"><h3>Failed to load document</h3><pre>${esc(err.message)}</pre></div>`;
      }
    }

    async function boot() {
      try {
        const context = await fetchJson("/api/context");
        state.context = context;
        state.selectedPath = selectInitialPath(context);

        const meta = [
          `Repo: ${context.repo_path}`,
          `Layout: ${context.layout_effective} (requested: ${context.layout_mode})`,
          `Generated: ${context.generated_at}`
        ];
        document.getElementById("header-meta").textContent = meta.join(" | ");

        renderSidebar();
        if (context.warnings && context.warnings.length) {
          const warning = context.warnings.map(w => `- ${w}`).join("\\n");
          document.getElementById("content").innerHTML =
            `<div class="panel warning"><h3>Warnings</h3><pre>${esc(warning)}</pre></div>`;
        }
        if (state.selectedPath) {
          renderDoc(state.selectedPath);
        } else if (!context.warnings || !context.warnings.length) {
          document.getElementById("content").innerHTML =
            `<div class="panel warning"><h3>No document selected</h3><pre>No readable context documents were found.</pre></div>`;
        }
      } catch (err) {
        document.getElementById("header-meta").textContent = "Failed to load context";
        document.getElementById("content").innerHTML =
          `<div class="panel warning"><h3>Initialization failed</h3><pre>${esc(err.message)}</pre></div>`;
      }
    }

    boot();
  </script>
</body>
</html>
"""


class ViewerRequestHandler(BaseHTTPRequestHandler):
    repo_root: Path = Path(".")
    layout_mode: str = "auto"

    def log_message(self, format: str, *args: object) -> None:  # noqa: A003
        return

    def _json(self, payload: Dict[str, object], status: HTTPStatus = HTTPStatus.OK) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status.value)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _html(self, body: str, status: HTTPStatus = HTTPStatus.OK) -> None:
        raw = body.encode("utf-8")
        self.send_response(status.value)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        if parsed.path == "/":
            self._html(HTML_PAGE)
            return
        if parsed.path == "/api/context":
            try:
                payload = build_context(self.repo_root, self.layout_mode)
            except Exception as exc:  # pragma: no cover
                self._json({"error": str(exc)}, status=HTTPStatus.INTERNAL_SERVER_ERROR)
                return
            self._json(payload)
            return
        if parsed.path == "/api/doc":
            params = parse_qs(parsed.query)
            rel_path = params.get("path", [""])[0]
            try:
                payload = read_document_payload(self.repo_root, rel_path)
            except ValueError as exc:
                self._json({"error": str(exc)}, status=HTTPStatus.BAD_REQUEST)
                return
            except FileNotFoundError as exc:
                self._json({"error": str(exc)}, status=HTTPStatus.NOT_FOUND)
                return
            except Exception as exc:  # pragma: no cover
                self._json({"error": str(exc)}, status=HTTPStatus.INTERNAL_SERVER_ERROR)
                return
            self._json(payload)
            return
        self._json({"error": "Not Found"}, status=HTTPStatus.NOT_FOUND)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Open a read-only local web viewer for Codex repo context files.",
    )
    parser.add_argument("--repo-path", required=True, help="Target repository path.")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind. Default: 127.0.0.1")
    parser.add_argument("--port", type=int, default=8765, help="Port to bind. Default: 8765")
    parser.add_argument("--open-browser", action="store_true", help="Open the UI URL in browser.")
    parser.add_argument(
        "--layout",
        choices=["auto", "tasks", "plans"],
        default="auto",
        help="Layout strategy. Default: auto",
    )
    return parser.parse_args()


def validate_runtime(repo_path: Path, port: int) -> Tuple[Path, Optional[str]]:
    if sys.version_info < (3, 9):
        raise ValueError("Python 3.9+ is required.")
    repo_root = repo_path.expanduser().resolve()
    if not repo_root.exists() or not repo_root.is_dir():
        raise ValueError(f"Invalid --repo-path: {repo_path}")
    if port < 1 or port > 65535:
        raise ValueError("--port must be between 1 and 65535.")
    return repo_root, None


def main() -> int:
    args = parse_args()
    try:
        repo_root, _ = validate_runtime(Path(args.repo_path), args.port)
    except Exception as exc:
        print(f"[ERROR] {exc}")
        return 1

    handler_cls = type(
        "ConfiguredViewerRequestHandler",
        (ViewerRequestHandler,),
        {"repo_root": repo_root, "layout_mode": args.layout},
    )

    try:
        server = ThreadingHTTPServer((args.host, args.port), handler_cls)
    except OSError as exc:
        winerror = getattr(exc, "winerror", None)
        if exc.errno in {98, 10048} or winerror in {10013, 10048}:
            print(
                f"[ERROR] Port {args.port} is unavailable on host {args.host} "
                "(already in use or not permitted). Use --port <other_port>."
            )
        else:
            print(f"[ERROR] Failed to start server: {exc}")
        return 1

    url = f"http://{args.host}:{args.port}/"
    print(f"[INFO] Repo Context Viewer")
    print(f"[INFO] Repo: {repo_root}")
    print(f"[INFO] Layout: {args.layout}")
    print(f"[INFO] URL: {url}")
    print("[INFO] Press Ctrl+C to stop.")

    if args.open_browser:
        webbrowser.open(url)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[INFO] Stopped.")
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
