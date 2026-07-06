"""
walkthrough.py — the Mosaic consumer journey, end to end, in one command.

Shows exactly what a consuming organization experiences:
  discover -> inspect -> install (re-embed locally) -> consult (bare-LLM vs pack) -> uninstall

Run:  .venv/bin/python src/walkthrough.py
"""

from dotenv import load_dotenv
load_dotenv()

import asyncio

import cognee
from config import PACK_FILE, PACK_DATASET
from import_pack import import_pack, verify_and_extract
from query import consult, bare_llm

REGISTRY_URL = "https://dhruvaviya06.github.io/mosaic-memorypack/"
SITUATION = (
    "A counterparty is a family office holding concentrated, highly leveraged positions "
    "built through total return swaps across several prime brokers, with persistent "
    "margin/risk-limit breaches. Assess the risk and what to investigate."
)


def banner(n: int, title: str) -> None:
    print(f"\n{'=' * 72}\n[{n}]  {title}\n{'=' * 72}")


async def main() -> int:
    banner(1, "DISCOVER — the analyst's org browses the Mosaic registry")
    print(f"  Registry (live): {REGISTRY_URL}")
    manifest, _graph, digest, ok = verify_and_extract(PACK_FILE)
    print(f"  Found pack:  {manifest['label']}  by {manifest['publisher']}")
    print(f"  Graph:       {manifest['counts']['nodes_total']} nodes / "
          f"{manifest['counts']['edges_total']} edges")
    print(f"  License:     {manifest['license']}")
    print(f"  Ships embeddings: {manifest['embeddings_included']}  (importer re-embeds locally)")
    print(f"  sha256 seal verified on download: {ok}")

    banner(2, "INSTALL — mount the pack into our own Node (re-embed locally)")
    await import_pack(PACK_FILE, PACK_DATASET)

    banner(3, "CONSULT — our existing agent assesses a live situation")
    print(f"  Situation:\n    {SITUATION}\n")
    bare = await bare_llm(SITUATION)
    print("  --- WITHOUT the pack (a bare LLM — what every org already has) ---")
    print("    " + bare.replace("\n", "\n    ")[:750] + " …\n")
    withpack = await consult(SITUATION, PACK_DATASET)
    print("  --- WITH RiskLore installed (consult_risklore) ---")
    print("    " + withpack.replace("\n", "\n    "))

    banner(4, "UNINSTALL — a single forget() removes the pack (reversibility)")
    result = await cognee.forget(dataset=PACK_DATASET)
    print(f"  forget('{PACK_DATASET}') -> {result}")
    print("\n[done] The org's agent gained citable precedent, then cleanly removed it —")
    print("       no customer data ever changed hands, only analyst expertise.")
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(asyncio.run(main()))
