"""
build_memory.py — Phase 3: build the RiskLore knowledge graph from curated cases.

Pipeline:  validate  ->  remember(case texts [+ source PDFs])  ->  improve()

This is the marketplace "publish" verb in action: publish = remember + improve.
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
from config import CASES_DIR, SOURCES_DIR, PACK_DATASET
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


async def build() -> int:
    # 1) Gate: never ingest cases that violate the contract.
    print("=== Validating cases before build ===")
    if validate_cases() != 0:
        print("\nValidation failed — aborting build.")
        return 1

    # 2) Collect curated case texts (the expertise layer).
    case_texts = []
    for path in sorted(CASES_DIR.glob("*.json")):
        case_texts.append(case_to_text(json.loads(path.read_text())))
    if not case_texts:
        print("No cases found — nothing to build.")
        return 1

    print(f"\n=== remember: ingesting {len(case_texts)} case(s) into '{PACK_DATASET}' ===")
    # self_improvement=False: build the graph now, run enrichment as a separate step below.
    await cognee.remember(case_texts, dataset_name=PACK_DATASET, self_improvement=False)

    # 3) Source PDFs (the evidence layer) — none during the dummy phase; wired for Phase 6.
    pdfs = sorted(SOURCES_DIR.glob("*.pdf"))
    if pdfs:
        print(f"=== remember: ingesting {len(pdfs)} source PDF(s) ===")
        with_handles = [open(p, "rb") for p in pdfs]
        try:
            await cognee.remember(with_handles, dataset_name=PACK_DATASET, self_improvement=False)
        finally:
            for fh in with_handles:
                fh.close()

    # 4) improve: enrich/consolidate the graph (the "improve" verb).
    print(f"=== improve: enriching '{PACK_DATASET}' ===")
    await cognee.improve(dataset=PACK_DATASET)

    print("\n[done] RiskLore graph built. Run  src/inspect.py  to X-ray it.")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(build()))
