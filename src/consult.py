"""
consult.py — one-shot terminal consult against an installed pack.

Step 1 (closest precedent + shared warning signs + citations) is KEYLESS: it reads the
tessera-<v>.mempack locally and needs NO LLM API key and NO Cognee install. Add --map to
also get the playbook tailored to your situation — Step 2 needs an LLM key in .env.

  .venv/bin/python src/consult.py "a family office with concentrated leveraged swaps"
  .venv/bin/python src/consult.py --map "a family office with concentrated leveraged swaps"
"""

from dotenv import load_dotenv
load_dotenv()

import argparse
import asyncio
import sys

from query import consult_with_citations


async def main(situation: str, do_map: bool) -> int:
    result = await consult_with_citations(situation, map_to_situation=do_map)
    p = result["precedent"]
    if not p:
        print("No close precedent found in the installed pack.")
        return 0

    print(f"\nClosest precedent: {p['institution']} ({p['year']})")
    print(f"Why it matches:    {p['why']}")

    if result["risk_factors"]:
        print("\nShared warning signs:")
        for s in result["risk_factors"]:
            print(f"  - {s}")

    for c in result.get("citations") or []:
        for s in c.get("sources", []):
            url = f"  {s['url']}" if s.get("url") else ""
            print(f"\nSource: {s['label']}{url}")

    if do_map:
        if result["playbook"]:
            print("\nHow analysts in matching cases investigated it, applied to your situation:")
            for s in result["playbook"]:
                print(f"  - {s}")
    else:
        print(f"\n{result['invitation']}")
        print("(re-run with --map to see the tailored playbook — that step needs an LLM key)")
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Keyless precedent lookup against an installed pack.")
    ap.add_argument("--map", action="store_true",
                    help="also produce the playbook tailored to your situation (needs an LLM key)")
    ap.add_argument("situation", nargs="+", help="free-text description of the situation")
    args = ap.parse_args()
    sys.exit(asyncio.run(main(" ".join(args.situation), args.map)))
