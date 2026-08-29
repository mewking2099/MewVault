"""mew index — build and query ChromaDB semantic indexes for project graphs.

Commands:
  mew index build                  Build index for the currently locked project
  mew index build --all            Build for all projects with a graph.json
  mew index build <project-path>   Build for a specific project path
  mew index status                 Show collection stats across all indexed projects
  mew index search "query"         Test semantic search against the active project
"""
from __future__ import annotations

import sys
from pathlib import Path

from mew.workspace import find_workspace_root
from mew.routing import vector_index


def run_index(args) -> None:
    action = getattr(args, "index_action", None)
    if action == "build":
        _build(args)
    elif action == "status":
        _status()
    elif action == "search":
        _search(args)
    else:
        print("mew index: specify build, status, or search", file=sys.stderr)
        sys.exit(1)


def _build(args) -> None:
    workspace_root = find_workspace_root()

    if getattr(args, "all", False):
        base = workspace_root or Path(".")
        graphs = sorted(base.glob("*/*/graphify-out/graph.json")) + \
                 sorted(base.glob("*/graphify-out/graph.json"))
    elif getattr(args, "project_path", None):
        project = Path(args.project_path).resolve()
        graphs = [project / "graphify-out" / "graph.json"]
    else:
        from mew.commands.dispatch import _read_active_project, _detect_silo, _project_graph_path
        lock = _read_active_project(workspace_root)
        silo = _detect_silo(workspace_root)
        graph = _project_graph_path(workspace_root, silo, lock)
        graphs = [graph] if graph.exists() else []

    if not graphs:
        print("index build: no graph.json found — run graphify update . first", file=sys.stderr)
        sys.exit(1)

    total = 0
    for graph_path in graphs:
        if not graph_path.exists():
            label = "/".join(graph_path.parts[-4:-2])
            print(f"  skip  {label:<40} (no graph.json)")
            continue
        label = "/".join(graph_path.parts[-4:-2])
        print(f"  indexing  {label:<40} ...", end=" ", flush=True)
        count, name = vector_index.build(graph_path)
        if count > 0:
            print(f"{count:>6} nodes  →  '{name}'")
            total += count
        else:
            print("failed  (check chromadb: pip install chromadb)")

    print(f"\ndone — {total} nodes indexed across {len(graphs)} project(s)")
    if total == 0:
        print("note: on first run ChromaDB downloads an embedding model (~90 MB); needs internet")


def _status() -> None:
    workspace_root = find_workspace_root() or Path(".")
    graphs = sorted(workspace_root.glob("*/*/graphify-out/graph.json")) + \
             sorted(workspace_root.glob("*/graphify-out/graph.json"))

    if not graphs:
        print("index status: no graphify-out/ directories found")
        return

    print(f"{'Project':<42} {'Nodes':>7}  Status")
    print("-" * 65)
    for g in graphs:
        label = "/".join(g.parts[-4:-2])
        s = vector_index.stats(g)
        print(f"{label:<42} {s['count']:>7}  {s['status']}")


def _search(args) -> None:
    query = args.query
    workspace_root = find_workspace_root()
    from mew.commands.dispatch import _read_active_project, _detect_silo, _project_graph_path
    lock  = _read_active_project(workspace_root)
    silo  = _detect_silo(workspace_root)
    graph = _project_graph_path(workspace_root, silo, lock)

    if not graph.exists():
        print("index search: no graph found for active project", file=sys.stderr)
        sys.exit(1)

    label = "/".join(graph.parts[-4:-2])
    print(f"project: {label}")
    print(f"query:   {query!r}")
    print()

    ids = vector_index.search(query, graph, n_results=getattr(args, "limit", 20))
    if not ids:
        print("  no results — is the index built?  run: mew index build")
        return
    for i, nid in enumerate(ids, 1):
        print(f"  {i:2d}.  {nid}")
