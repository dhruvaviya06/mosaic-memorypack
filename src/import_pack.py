"""
import_pack.py — Phase 4: install a .mempack into a fresh Cognee dataset (the Node install path).

Route (a), the demo-safe route: reconstruct the pack's text from graph.json and re-feed it
through remember(), so the importing Node RE-EMBEDS locally with its own model. That is the
model-agnosticism proof — the pack ships NO embeddings, yet the knowledge crosses instances.

Before ingesting, the sha256 tamper seal in pack.json is re-computed and checked.

Run:  .venv/bin/python src/import_pack.py
"""

from dotenv import load_dotenv
load_dotenv()

import asyncio
import hashlib
import json
import tarfile

import cognee
from config import PACK_FILE, PACK_ONTOLOGY_MEMBER, IMPORTED_DATASET


def verify_and_extract(mempack_path):
    """Open the tarball, re-hash the three content files, and compare to pack.json."""
    with tarfile.open(mempack_path, "r:gz") as tar:
        graph_bytes = tar.extractfile("graph.json").read()
        ont_bytes = tar.extractfile(PACK_ONTOLOGY_MEMBER).read()
        prov_bytes = tar.extractfile("provenance.json").read()
        manifest = json.load(tar.extractfile("pack.json"))

    hasher = hashlib.sha256()
    for b in (graph_bytes, ont_bytes, prov_bytes):
        hasher.update(b)
    digest = hasher.hexdigest()
    return manifest, json.loads(graph_bytes), digest, digest == manifest.get("content_hash")


def graph_to_text(graph: dict) -> str:
    """Render the pack's graph back into text so the importer can re-cognify + re-embed it.

    We include each node's substantive text, then express every edge as a sentence
    ("<source> <relationship> <target>."). Feeding this back reconstructs an equivalent
    graph locally without ever shipping a single embedding vector.
    """
    id2name = {
        n["id"]: (n.get("name") or (n.get("text") or "")[:50] or n["id"][:8])
        for n in graph["nodes"]
    }
    parts, seen = [], set()
    for n in graph["nodes"]:
        text = (n.get("text") or "").strip()
        if text and text not in seen:
            seen.add(text)
            parts.append(text)
    for e in graph["edges"]:
        s = id2name.get(e["source"], "").strip()
        d = id2name.get(e["target"], "").strip()
        if s and d:
            line = f"{s} {e['relationship'].replace('_', ' ')} {d}."
            if line not in seen:
                seen.add(line)
                parts.append(line)
    return "\n".join(parts)


async def import_pack(mempack_path=PACK_FILE, dataset=IMPORTED_DATASET) -> dict:
    manifest, graph, digest, ok = verify_and_extract(mempack_path)
    print(f"Installing pack: {manifest['label']}  (publisher={manifest['publisher']}, "
          f"tier={manifest['verification_tier']})")
    print(f"  sha256 tamper seal: {'VERIFIED' if ok else 'MISMATCH'} — {digest[:16]}...")
    if not ok:
        raise ValueError("Content hash mismatch — pack may be tampered; refusing to import.")

    text = graph_to_text(graph)
    print(f"  reconstructed {len(text)} chars from {len(graph['nodes'])} nodes / "
          f"{len(graph['edges'])} edges (pack ships no embeddings)")
    print(f"  remember() into fresh dataset '{dataset}' — re-embedding locally...")
    await cognee.remember(text, dataset_name=dataset)
    print("  install complete.")
    return manifest


if __name__ == "__main__":
    import sys
    sys.exit(0 if asyncio.run(import_pack()) else 1)
