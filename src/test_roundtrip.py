"""
test_roundtrip.py — Phase 4: THE thesis. Prove a pack survives crossing Cognee instances.

    recall(Q) on the built pack
      -> export .mempack (no embeddings, sha256 sealed)
      -> forget the original dataset          (the publisher Node uninstalls it)
      -> import into a FRESH dataset            (a second Node re-embeds locally)
      -> recall(Q) again
      -> compare the two answers

If the answer survives a full export / forget-original / import cycle, the pack is genuinely
portable — knowledge moved between instances with zero embeddings shipped. This doubles as
the live demo script.

Run:  .venv/bin/python src/test_roundtrip.py
"""

from dotenv import load_dotenv
load_dotenv()

import asyncio
import re

import cognee
from cognee.infrastructure.databases.graph import get_graph_engine
from config import PACK_DATASET, IMPORTED_DATASET, PACK_FILE
from export_pack import export
from import_pack import import_pack

# A question answerable from the pack's content (the dummy FakeBank liquidity-crisis case).
QUESTION = "What risks led to the bank's liquidity crisis and how was it resolved?"

_STOP = set(
    "the a an and or of to in is was were that this it its as for with on by from at be are "
    "has had have will would can could should more than into out over under after before".split()
)


def keywords(s: str) -> set:
    return {w for w in re.findall(r"[a-z]{4,}", s.lower()) if w not in _STOP}


async def recall_text(question: str, dataset: str) -> str:
    results = await cognee.recall(question, datasets=[dataset])
    for e in results:
        text = getattr(e, "answer", None) or getattr(e, "text", None)
        if text:
            return text.strip()
    return ""


async def main() -> int:
    engine = await get_graph_engine()
    nodes, _ = await engine.get_graph_data()
    if not nodes:
        print("No graph found — run src/build_memory.py first.")
        return 1

    print("STEP 1 — recall on the ORIGINAL pack")
    before = await recall_text(QUESTION, PACK_DATASET)
    print(f"  Q: {QUESTION}\n  A: {before}\n")

    print("STEP 2 — export the pack (.mempack, no embeddings, sha256 sealed)")
    if await export() != 0:
        return 1

    print("\nSTEP 3 — forget the ORIGINAL dataset (publisher uninstalls it)")
    await cognee.forget(dataset=PACK_DATASET)
    print(f"  forgot '{PACK_DATASET}'")

    print("\nSTEP 4 — import into a FRESH dataset (a second Node re-embeds locally)")
    await import_pack(PACK_FILE, IMPORTED_DATASET)

    print("\nSTEP 5 — recall the SAME question on the freshly imported pack")
    after = await recall_text(QUESTION, IMPORTED_DATASET)
    print(f"  Q: {QUESTION}\n  A: {after}\n")

    kb, ka = keywords(before), keywords(after)
    overlap = len(kb & ka) / max(1, len(kb))
    passed = bool(after) and overlap >= 0.30
    print("=" * 64)
    print(f"Answer-survival overlap: {overlap:.0%} of key terms carried across")
    print("ROUND-TRIP PASSED — the pack crossed instances with its knowledge intact."
          if passed else
          "ROUND-TRIP WEAK — answers diverged; inspect the reconstruction.")
    return 0 if passed else 1


if __name__ == "__main__":
    import sys
    sys.exit(asyncio.run(main()))
