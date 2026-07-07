"""
export_pack.py — Phase 4: export the built graph as a portable .mempack.

A .mempack is a tarball of four files, and it deliberately contains NO embeddings —
that omission IS the model-agnosticism claim (the importer re-embeds locally):

    graph.json       node + edge lists (id, type, name, text, source_ref)
    ontology.owl     the ontology (shared vocabulary) — generic name, pack-agnostic
    provenance.json  case_id -> institution / year / source documents (+ URLs)
    pack.json        manifest: identity, license, counts, and a sha256 tamper seal

The sha256 in pack.json is computed over the other three files, so any tampering
after export is detectable at import time.

Run:  .venv/bin/python src/export_pack.py
"""

from dotenv import load_dotenv
load_dotenv()

import asyncio
import hashlib
import io
import json
import tarfile
from collections import Counter

from cognee.infrastructure.databases.graph import get_graph_engine
from config import (
    CASES_DIR, ONTOLOGY_FILE, PACK_ONTOLOGY_MEMBER, PACK_DIR, PACK_FILE, PACK_FILENAME,
    PLATFORM, PACK_NAME, PACK_VERSION, PACK_LABEL, PUBLISHER, LICENSE, VERIFICATION_TIER,
    DUMMY_CASE_IDS,
)

# Cognee-internal node types that are plumbing, not curated knowledge.
_STRUCTURAL_TYPES = {"TextDocument", "DocumentChunk", "TextSummary"}


def _canonical(obj) -> bytes:
    """Deterministic JSON bytes, so the content hash is stable across runs/machines."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def build_graph_json(nodes, edges) -> dict:
    out_nodes = []
    for nid, a in nodes:
        out_nodes.append({
            "id": nid,
            "type": a.get("type"),
            "name": a.get("name") or "",
            "text": a.get("text") or a.get("description") or "",
            "source_ref": a.get("source_content_hash"),   # ties a node back to its source text
        })
    out_edges = [
        {"source": s, "target": t, "relationship": rel}
        for (s, t, rel, _props) in edges
    ]
    return {"nodes": out_nodes, "edges": out_edges}


def build_cases_digest() -> list[dict]:
    """The curated cases in clean, case-level form, embedded into the pack as cases.json.

    This is what the KEYLESS retriever (keyless.py) embeds locally to find the closest
    precedent with no LLM — so the .mempack stays the single self-contained portable unit.
    Unsealed (not in the content hash); the sealed graph remains the integrity anchor.
    """
    out = []
    for path in sorted(CASES_DIR.glob("*.json")):
        d = json.loads(path.read_text())
        if d["case_id"] in DUMMY_CASE_IDS:
            continue
        out.append(d)
    return out


def build_provenance() -> dict:
    """Document-level provenance from the curated case files (the auditability story).

    Node-level linking (each heuristic back to a page) is a Phase 6 curation refinement;
    for now we record which source documents back each case.
    """
    prov = {}
    for path in sorted(CASES_DIR.glob("*.json")):
        d = json.loads(path.read_text())
        if d["case_id"] in DUMMY_CASE_IDS:
            continue  # the dummy is never part of a real pack's provenance
        prov[d["case_id"]] = {
            "institution": d["institution"],
            "year": d["year"],
            "source_documents": d["source_documents"],
            "document_urls": {name: None for name in d["source_documents"]},  # real URLs in Phase 6
        }
    return prov


def build_manifest(graph: dict, content_hash: str) -> dict:
    node_types = Counter(n["type"] for n in graph["nodes"])
    curated = sum(c for t, c in node_types.items() if t not in _STRUCTURAL_TYPES)
    return {
        "platform": PLATFORM,
        "name": PACK_NAME,
        "version": PACK_VERSION,
        "label": PACK_LABEL,
        "publisher": PUBLISHER,
        "license": LICENSE,
        "verification_tier": VERIFICATION_TIER,
        "layers": {
            "expertise": {"description": "curated knowledge graph (cases)"},
            "evidence": {"description": "source documents referenced in provenance"},
        },
        "counts": {
            "nodes_total": len(graph["nodes"]),
            "nodes_curated": curated,
            "edges_total": len(graph["edges"]),
            "node_types": dict(node_types),
        },
        "embeddings_included": False,   # the model-agnosticism claim, stated explicitly
        "content_hash": content_hash,   # sha256 over graph.json + ontology.owl + provenance.json
    }


async def export() -> int:
    engine = await get_graph_engine()
    nodes, edges = await engine.get_graph_data()
    if not nodes:
        print("Graph is empty — run src/build_memory.py first.")
        return 1

    graph = build_graph_json(nodes, edges)
    provenance = build_provenance()
    cases_digest = build_cases_digest()
    ontology_bytes = ONTOLOGY_FILE.read_bytes() if ONTOLOGY_FILE.exists() else b""
    if not ontology_bytes:
        print(f"WARNING: {ONTOLOGY_FILE} missing — packaging without an ontology.")

    graph_bytes = _canonical(graph)
    prov_bytes = _canonical(provenance)

    # Tamper seal: hash the three content files (NOT pack.json, which contains the hash).
    hasher = hashlib.sha256()
    for b in (graph_bytes, ontology_bytes, prov_bytes):
        hasher.update(b)
    content_hash = hasher.hexdigest()

    manifest = build_manifest(graph, content_hash)
    manifest_bytes = _canonical(manifest)

    PACK_DIR.mkdir(exist_ok=True)
    members = {
        "graph.json": graph_bytes,
        PACK_ONTOLOGY_MEMBER: ontology_bytes,
        "provenance.json": prov_bytes,
        "cases.json": _canonical(cases_digest),   # unsealed — powers keyless retrieval
        "pack.json": manifest_bytes,
    }
    with tarfile.open(PACK_FILE, "w:gz") as tar:
        for name, data in members.items():
            info = tarfile.TarInfo(name=name)
            info.size = len(data)
            tar.addfile(info, io.BytesIO(data))

    print(f"Exported {PACK_FILENAME}")
    print(f"  path:          {PACK_FILE}")
    print(f"  nodes/edges:   {manifest['counts']['nodes_total']} / {manifest['counts']['edges_total']}")
    print(f"  curated nodes: {manifest['counts']['nodes_curated']}")
    print(f"  embeddings:    {manifest['embeddings_included']}  (re-embedded locally on import)")
    print(f"  sha256:        {content_hash}")
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(asyncio.run(export()))
