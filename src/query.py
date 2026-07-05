"""
query.py — Phase 5: consult(situation) + the bare-LLM-vs-pack contrast harness.

consult(situation) is the single capability a Node exposes to the outside world
(as the MCP tool `consult_risklore`): given a described situation, it recalls
precedent from the INSTALLED pack — the org's existing agent gains citable
precedent with zero workflow change.

The contrast harness answers the SAME question two ways so the value is visible:
  (a) a bare LLM with no pack  — the baseline every org already has
  (b) the pack-backed recall   — precedent grounded in the RiskLore graph

Run:  .venv/bin/python src/query.py "<describe a situation>"
      .venv/bin/python src/query.py            # uses the default Archegos-shaped scenario
"""

from dotenv import load_dotenv
load_dotenv()

import asyncio
import os
import sys

import cognee
from cognee.modules.search.types.SearchType import SearchType
from config import PACK_DATASET


async def consult(situation: str, dataset: str = PACK_DATASET) -> str:
    """Recall precedent from the installed pack for a described situation.

    This is the function exposed as the MCP tool `consult_risklore(situation)`.

    Two details matter for matching a GENERIC situation (one that does not name a
    specific institution) to the right precedent:
      - we frame the situation as a question, and
      - we use the HYBRID retriever (vector similarity + graph context) rather than
        the default entity-seeded graph completion, which only fires when the query
        names an entity already in the graph.
    """
    query = (
        f"{situation}\n\nWhat past financial-failure precedent from the pack most "
        f"closely matches this situation? Name it, give the warning signs and risk "
        f"factors it shares, and state what should be investigated."
    )
    results = await cognee.recall(
        query, query_type=SearchType.HYBRID_COMPLETION, datasets=[dataset]
    )
    for e in results:
        text = getattr(e, "answer", None) or getattr(e, "text", None)
        if text:
            return text.strip()
    return "(no precedent found in the installed pack)"


async def bare_llm(question: str) -> str:
    """Ask the SAME question to the raw configured LLM with NO pack — the baseline."""
    import litellm
    litellm.suppress_debug_info = True
    model = os.environ.get("LLM_MODEL", "gemini/gemini-2.5-flash")
    key = os.environ.get("LLM_API_KEY")
    resp = await litellm.acompletion(
        model=model, api_key=key,
        messages=[{"role": "user", "content": question}],
    )
    return resp.choices[0].message.content.strip()


async def contrast(situation: str) -> None:
    print("SITUATION")
    print(f"  {situation}\n")
    print("-" * 70)
    print("BARE LLM  (no pack — what every org already has)")
    print("-" * 70)
    print(await bare_llm(situation), "\n")
    print("-" * 70)
    print("PACK-BACKED  (RiskLore precedent via consult_risklore)")
    print("-" * 70)
    print(await consult(situation), "\n")


# Default scenario is deliberately Archegos-shaped, so a pack containing the Archegos
# case can cite concrete precedent while the bare LLM only reasons in generalities.
DEFAULT_SITUATION = (
    "A counterparty is a family office holding concentrated, highly leveraged positions "
    "built through total return swaps across several prime brokers, with persistent "
    "margin/risk-limit breaches. Assess the risk and what to investigate."
)


if __name__ == "__main__":
    situation = " ".join(sys.argv[1:]).strip() or DEFAULT_SITUATION
    asyncio.run(contrast(situation))
