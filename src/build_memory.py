"""
build_memory.py — Phase 3: build the Tessera knowledge graph from curated cases.

Pipeline:  validate  ->  remember(case texts [+ source PDFs])  ->  improve()

This is the pack "publish" step in action: publish = remember + improve.
We split them explicitly (remember with self_improvement=False, then a separate
improve()) so the two steps are visible and we don't pay for enrichment twice.

Run:  .venv/bin/python src/build_memory.py
"""

from dotenv import load_dotenv
load_dotenv()

import asyncio
import json
import sys

import cognee
from config import CASES_DIR, PACK_DATASET, DEEP_TIER_CASE_IDS, DUMMY_CASE_IDS
from validate_cases import main as validate_cases


def case_to_text(data: dict) -> str:
    """Render a case dict as labeled prose, so cognify extracts rich, typed structure.

    We feed readable text (not raw JSON) because the graph extractor reasons over
    natural language far better than over braces and quotes.
    """
    lines = [
        f"Financial failure case: {data['institution']} ({data['year']}) "
        f"[case_id: {data['case_id']}]",
        f"Category: {data['category']}",
        "Risk signals (warning signs):",
        *[f"  - {s}" for s in data["risk_signals"]],
        f"Analyst reasoning: {data['analyst_reasoning']}",
        "Investigation steps:",
        *[f"  - {s}" for s in data["investigation_steps"]],
        f"Decision taken: {data['decision']}",
        f"Outcome: {data['outcome']}",
        "Lessons learned (heuristics):",
        *[f"  - {s}" for s in data["lessons_learned"]],
    ]
    return "\n".join(lines)


def select_cases(scope: str) -> list[dict]:
    """Load case dicts for the requested scope, always excluding the dummy.

    scope="deep" -> only the deep-tier cases (backed by a primary-source document).
    scope="all"  -> every real case (deep + light typologies).
    """
    selected = []
    for path in sorted(CASES_DIR.glob("*.json")):
        data = json.loads(path.read_text())
        cid = data.get("case_id")
        if cid in DUMMY_CASE_IDS:
            continue
        if scope == "deep" and cid not in DEEP_TIER_CASE_IDS:
            continue
        selected.append(data)
    return selected


async def build(scope: str = "deep") -> int:
    # 1) Gate: never ingest cases that violate the contract.
    print("=== Validating cases before build ===")
    if validate_cases() != 0:
        print("\nValidation failed — aborting build.")
        return 1

    # 2) Collect the curated case texts for the chosen scope (the expertise layer).
    cases = select_cases(scope)
    if not cases:
        print(f"No cases found for scope '{scope}' — nothing to build.")
        return 1
    case_texts = [case_to_text(c) for c in cases]
    ids = ", ".join(c["case_id"] for c in cases)
    print(f"\n=== remember: ingesting {len(case_texts)} '{scope}' case(s) into "
          f"'{PACK_DATASET}' ===\n  {ids}")

    # Two-tier rule: we ingest the CURATED CASE JSONs (which already distill the sources).
    # We deliberately do NOT cognify the full source PDFs — that would burn free-tier quota
    # on hundreds of pages. The evidence trail to source documents is preserved through
    # provenance.json (built by export_pack from each case's source_documents).
    await cognee.remember(case_texts, dataset_name=PACK_DATASET, self_improvement=False)

    # 3) improve: enrich/consolidate the graph (the "improve" verb).
    print(f"=== improve: enriching '{PACK_DATASET}' ===")
    await cognee.improve(dataset=PACK_DATASET)

    print("\n[done] Tessera graph built. Run  src/inspect_graph.py  to X-ray it.")
    return 0


if __name__ == "__main__":
    # scope: "deep" (default, quota-safe) or "all"
    scope = "all" if "--all" in sys.argv else "deep"
    sys.exit(asyncio.run(build(scope)))
