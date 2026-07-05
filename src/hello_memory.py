"""
hello_memory.py — Phase 1 smoke test for Memory Mesh / RiskLore.

Purpose: prove cheaply that
  (a) the Gemini API key works,
  (b) cognee's local stack (LanceDB vector + Kuzu graph + SQLite) is wired up, and
  (c) we know the EXACT lifecycle parameter names for cognee 1.2.2
before we build anything real.

It runs one full lap of Cognee's memory lifecycle on two throwaway sentences:

    remember  ->  recall  ->  forget  ->  recall again (should come back empty)

Run:  .venv/bin/python src/hello_memory.py
"""

# load_dotenv() must run BEFORE importing cognee, so cognee reads our .env config
# (provider, models, ENABLE_BACKEND_ACCESS_CONTROL, CACHING) as it initializes.
from dotenv import load_dotenv
load_dotenv()

import asyncio
import cognee

# A throwaway dataset name, so this smoke test never touches real pack data.
SMOKE_DATASET = "hello_smoke"

# Two sentences about a DELIBERATELY FICTIONAL bank failure. If recall can answer
# a question about them, memory genuinely worked — a base LLM cannot know invented
# facts, so a correct answer can only come from what we just stored.
FACTS = [
    "Zephyra Bank collapsed in 2031 after a concentrated bet on crypto-custody "
    "startups turned illiquid overnight.",
    "The Zephyra collapse was investigated by the Meridian Financial Authority, "
    "which faulted the board for ignoring three internal risk memos.",
]
QUESTION = "Why did Zephyra Bank collapse, and who investigated it?"


def show(entries):
    """recall() returns a list of typed response objects; pull out readable text.

    The object type depends on how cognee's router answered: a graph-completion
    answer is a ResponseGraphEntry (text in `.text`), a Q&A answer is a
    ResponseQAEntry (text in `.answer`). Check both so either prints cleanly.
    """
    if not entries:
        print("   (no results)")
        return
    for e in entries:
        text = getattr(e, "answer", None) or getattr(e, "text", None)
        print("   -", text if text else repr(e))


async def main():
    print("1) remember: teaching cognee two fictional facts (this cognifies -> LLM calls)...")
    await cognee.remember(FACTS, dataset_name=SMOKE_DATASET)

    print("\n2) recall BEFORE forget (memory should be able to answer):")
    before = await cognee.recall(QUESTION, datasets=[SMOKE_DATASET])
    show(before)

    print("\n3) forget: uninstalling the whole smoke dataset (the reversibility beat)...")
    result = await cognee.forget(dataset=SMOKE_DATASET)
    print("   forget() returned:", result)

    print("\n4) recall AFTER forget (memory should now be gone):")
    try:
        after = await cognee.recall(QUESTION, datasets=[SMOKE_DATASET])
        show(after)
    except Exception as e:
        # A "dataset not found" here is a SUCCESS signal: the dataset is truly gone.
        print(f"   recall raised {type(e).__name__} — consistent with the dataset being removed.")

    print("\n[done] Smoke test finished. If step 2 answered and step 4 did not, the")
    print("       full remember/recall/forget lifecycle + Gemini config all work.")


if __name__ == "__main__":
    # Every cognee lifecycle call is async; asyncio.run() is the synchronous entry point
    # that starts an event loop, runs main() to completion, then tears the loop down.
    asyncio.run(main())
