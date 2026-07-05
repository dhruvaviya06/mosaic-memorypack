"""
inspect_graph.py — Phase 3: X-ray the knowledge graph (debugging + curation aid).

Prints node/edge counts, a breakdown by node type and relationship, and a handful of
readable sample triples (source --relationship--> target). With --html it also writes
an interactive graph view via cognee.visualize_graph.

NAMING: this is inspect_graph.py, NOT inspect.py — a module called inspect.py sitting in
src/ would shadow Python's stdlib `inspect` (which cognee imports), breaking every script
that runs from this directory. (Verified.)

Run:  .venv/bin/python src/inspect_graph.py
      .venv/bin/python src/inspect_graph.py --html    # also write pack/graph.html
"""

from dotenv import load_dotenv
load_dotenv()

import asyncio
import sys
from collections import Counter

import cognee
from cognee.infrastructure.databases.graph import get_graph_engine
from config import PACK_DIR, PACK_DATASET


def node_label(attrs: dict) -> str:
    """A short human-readable label for a node: its name, else a snippet of its text."""
    name = (attrs.get("name") or "").strip()
    if name:
        return name
    text = (attrs.get("text") or "").strip().replace("\n", " ")
    return text[:60] + ("…" if len(text) > 60 else "")


async def xray(write_html: bool) -> int:
    engine = await get_graph_engine()
    # get_graph_data() returns (nodes, edges):
    #   node = (id, attrs_dict)                     attrs has 'type', 'name', 'text', ...
    #   edge = (source_id, target_id, rel, props)   rel is the relationship name string
    nodes, edges = await engine.get_graph_data()

    print(f"GRAPH X-RAY — {len(nodes)} nodes, {len(edges)} edges\n")

    labels = {nid: node_label(attrs) for nid, attrs in nodes}

    type_counts = Counter(attrs.get("type", "?") for _, attrs in nodes)
    print("Nodes by type:")
    for t, c in type_counts.most_common():
        print(f"  {c:4}  {t}")

    rel_counts = Counter(rel for _, _, rel, _ in edges)
    print("\nEdges by relationship:")
    for r, c in rel_counts.most_common():
        print(f"  {c:4}  {r}")

    print("\nSample relationships (source --rel--> target):")
    shown = 0
    for src, dst, rel, _ in edges:
        s, d = labels.get(src, ""), labels.get(dst, "")
        if not s or not d:
            continue  # skip edges to unlabeled structural nodes — noise for a human read
        print(f"  {s[:34]:36} --{rel}-->  {d[:34]}")
        shown += 1
        if shown >= 20:
            break

    if write_html:
        PACK_DIR.mkdir(exist_ok=True)
        out = str(PACK_DIR / "graph.html")
        try:
            await cognee.visualize_graph(destination_file_path=out, dataset=PACK_DATASET)
            print(f"\nWrote interactive graph to {out}")
        except Exception as e:
            print(f"\n(visualize_graph skipped: {type(e).__name__}: {str(e)[:120]})")

    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(xray("--html" in sys.argv)))
