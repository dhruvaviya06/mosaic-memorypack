"""
keyless.py — local, NO-LLM Step-1 retrieval straight from the portable pack.

This is the portability proof: given only a tessera-<v>.mempack, a fresh Node finds the
closest precedent with NO LLM API key. We read the pack's cases.json (clean, case-level
curated text), embed it LOCALLY with fastembed (the model the pack "re-embeds with"), and
rank cases by cosine similarity to the situation. The best case IS the precedent — its
fields give the warning-sign chips and (for Step 2) the playbook; provenance gives citations.

Only the Step-2 playbook rewrite needs a key; Step 1 here is fully offline.

Embeddings are cached next to the pack (keyed by the pack's content hash), so the first
consult builds the index (~seconds) and later ones are instant.
"""

import json
import os
import tarfile
from pathlib import Path

import numpy as np

from config import PACK_FILE

_MODEL = None
MIN_SIM = 0.30      # below this, we treat the situation as having no close precedent


def _embedder():
    global _MODEL
    if _MODEL is None:
        from fastembed import TextEmbedding
        name = os.environ.get("EMBEDDING_MODEL", "BAAI/bge-small-en-v1.5")
        _MODEL = TextEmbedding(model_name=name)
    return _MODEL


def _embed(texts: list[str]) -> np.ndarray:
    vecs = np.asarray(list(_embedder().embed(texts)), dtype=np.float32)
    norms = np.linalg.norm(vecs, axis=1, keepdims=True)
    return vecs / (norms + 1e-9)


def _case_text(case: dict) -> str:
    """The text we embed for a case — the substance a situation should match against."""
    parts = [
        case.get("institution", ""),
        case.get("category", ""),
        " ".join(case.get("risk_signals") or []),
        case.get("analyst_reasoning", ""),
        " ".join(case.get("lessons_learned") or []),
    ]
    return " ".join(p for p in parts if p)


def _load_pack_cases(pack_file: Path = PACK_FILE) -> tuple[list[dict], str]:
    """Return (case dicts, content_hash) from a .mempack's cases.json."""
    with tarfile.open(pack_file, "r:gz") as tar:
        if "cases.json" not in tar.getnames():
            return [], "nocases"
        cases = json.load(tar.extractfile("cases.json"))
        manifest = json.load(tar.extractfile("pack.json"))
    return cases, manifest.get("content_hash", "nohash")


def _index(pack_file: Path = PACK_FILE) -> tuple[list[dict], np.ndarray]:
    """Build (or load from cache) the local case-embedding index for a pack."""
    cases, chash = _load_pack_cases(pack_file)
    cache = pack_file.parent / f".keyless_index_{chash[:12]}.npz"
    if cache.exists():
        data = np.load(cache, allow_pickle=True)
        if int(data["n"]) == len(cases):
            return cases, data["emb"]
    emb = _embed([_case_text(c) for c in cases]) if cases else np.zeros((0, 384), np.float32)
    np.savez(cache, emb=emb, n=len(cases))
    return cases, emb


def match_pack_case(situation: str, pack_file: Path = PACK_FILE,
                    min_sim: float = MIN_SIM) -> dict | None:
    """Return the curated case whose text is closest to the situation — locally, no LLM.

    None if no case clears the similarity floor (treat as 'no close precedent').
    """
    if not pack_file.exists():
        return None
    cases, emb = _index(pack_file)
    if not cases:
        return None
    q = _embed([situation])[0]
    sims = emb @ q
    i = int(np.argmax(sims))
    return cases[i] if float(sims[i]) >= min_sim else None


def pack_available(pack_file: Path = PACK_FILE) -> bool:
    return pack_file.exists()


if __name__ == "__main__":
    import sys
    sit = " ".join(sys.argv[1:]) or "concentrated leveraged total return swaps, margin breaches"
    c = match_pack_case(sit)
    print(f"[keyless] {sit!r}\n -> {c['institution'] +' ('+str(c['year'])+')' if c else 'no close precedent'}")
