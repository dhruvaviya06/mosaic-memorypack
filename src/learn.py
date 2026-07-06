"""
learn.py — the learn-and-forget loop: the Node's memory grows, the raw input doesn't stick.

When a consult is resolved, the case is DISTILLED (de-identified: names, institutions,
exact amounts and dates stripped — only the pattern, the risk factors, and which precedent
it matched survive) and remember()-ed into a SEPARATE dataset, ORG_CASES_DATASET. So the
org's own Tessera accumulates its cases while the curated pack stays clean and unmutated.

The user's RAW input is never written to a persistent dataset — recall() is read-only and
session caching is off (CACHING=false), so the raw submission is forgotten by construction
the moment the request returns. What persists is the distilled, privacy-safe case note.

forget_org_cases() is the explicit reverse verb: it drops everything the Node has learned,
mirroring the pack's own uninstall.
"""

from dotenv import load_dotenv
load_dotenv()

import os

import cognee
from config import ORG_CASES_DATASET, PACK_DISPLAY


async def distill_case(situation: str, result: dict) -> str:
    """De-identify + distill a resolved consult into a privacy-safe casebook note.

    The matched precedent (institution/year/category) comes from the CURATED pack, which is
    public knowledge, so it is safe to keep; only the USER'S specifics are stripped.
    """
    precedent = result.get("precedent") or {}
    import litellm
    litellm.suppress_debug_info = True
    model = os.environ.get("LLM_MODEL", "groq/llama-3.3-70b-versatile")
    key = os.environ.get("LLM_API_KEY")

    prompt = (
        "Distil the following financial situation into a 2-3 sentence casebook note.\n"
        "Remove ALL specific names, institutions, people, exact amounts, and dates — keep "
        "only the abstract pattern, the risk factors, and the TYPE of entity involved.\n"
        "Do not add advice or recommendations. Return only the note.\n\n"
        f"SITUATION:\n{situation}"
    )
    resp = await litellm.acompletion(
        model=model, api_key=key,
        messages=[{"role": "user", "content": prompt}],
    )
    note = (resp.choices[0].message.content or "").strip()

    if precedent.get("institution"):
        note += (f"\nMatched precedent: {precedent['institution']} "
                 f"({precedent.get('year')}) — {precedent.get('why')}")
    return note


async def capture_case(situation: str, result: dict) -> dict:
    """Distil a resolved consult and remember() it into the Node's own case memory.

    Returns {"stored": bool, "note": <distilled note or ''>, "error": <str or ''>}.
    A capture failure must NEVER break the user's answer, so everything is guarded.
    """
    try:
        note = await distill_case(situation, result)
        # remember() adds the distilled case to the Node's accumulating memory. The curated
        # pack (a different dataset) is never touched. self_improvement=False keeps this
        # fast; a batch improve() can enrich ORG_CASES_DATASET later.
        await cognee.remember(note, dataset_name=ORG_CASES_DATASET, self_improvement=False)
        return {"stored": True, "note": note, "error": ""}
    except Exception as e:  # noqa: BLE001 — capture is best-effort, must not surface
        return {"stored": False, "note": "", "error": str(e)[:300]}


async def forget_org_cases() -> dict:
    """Drop everything this Node has learned — the explicit reverse of capture_case()."""
    return await cognee.forget(dataset=ORG_CASES_DATASET)


if __name__ == "__main__":
    import asyncio
    demo = {"precedent": {"institution": "Credit Suisse / Archegos Capital Management",
                          "year": 2021, "why": "prime-broker counterparty blow-up"}}
    note = asyncio.run(distill_case(
        "Meridian Family Office holds ~$4bn concentrated tech via total return swaps across "
        "three brokers and breached limits three times this quarter.", demo))
    print(f"[{PACK_DISPLAY}] distilled note:\n{note}")
