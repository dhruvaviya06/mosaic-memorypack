"""
query.py — the shared consult brain: precedent recall + the two-step answer format.

A Node exposes ONE capability to the outside world (the MCP tool `consult_pack`):
given a described situation, it recalls the closest precedent from the INSTALLED pack,
surfaces the warning signs it shares, and — on request — maps how analysts investigated
that precedent onto the user's own situation.

The answer format is precedent-first and delivered as SHARED EXPERIENCE, never as advice:
  step 1 (map_to_situation=False) — closest precedent + why + warning-sign chips + an
                                    invitation to map it onto the user's situation.
  step 2 (map_to_situation=True)  — the recommended playbook: the precedent's
                                    investigation steps, rewritten to reference the user's
                                    entities/instruments/amounts, voiced as what analysts
                                    DID (past tense, no second-person imperatives).

There is deliberately NO per-answer disclaimer — the single disclaimer lives at install
time (config.INSTALL_NOTE). The contrast harness answers the SAME question two ways so the
value is visible: a bare LLM (which confidently prescribes) vs the pack (which recounts
precedent and lets the user draw the connection).

Run:  .venv/bin/python src/query.py "<describe a situation>"
      .venv/bin/python src/query.py            # uses the default Archegos-shaped scenario
"""

from dotenv import load_dotenv
load_dotenv()

import asyncio
import functools
import json
import os
import re
import sys

from config import PACK_DATASET, PACK_DISPLAY, CASES_DIR, DUMMY_CASE_IDS

# NOTE: cognee is imported LAZILY inside consult() only. The product path
# (consult_with_citations → keyless Step 1 + litellm Step 2) needs neither cognee nor a
# key for Step 1, so importing this module stays light and works on a keyless fresh Node.

# --- Case index: match a recalled precedent back to its structured case --------
# recall() returns generated prose that NAMES a precedent (e.g. "Archegos", "IL&FS").
# We map that back to the curated case on disk to get its structured fields
# (risk_signals -> chips, investigation_steps -> the playbook we rewrite).

_STOP = {"the", "and", "for", "ltd", "plc", "inc", "bank", "capital", "group",
         "holdings", "financial", "management", "sector", "wide", "typology", "case"}

# Distinctive aliases for the name-brand cases, so matching stays robust even when
# recall paraphrases the institution name.
_CASE_ALIASES = {
    "archegos_2021": ["archegos", "credit suisse", "viacom"],
    "svb_2023": ["silicon valley bank", "svb"],
    "pnb_niravmodi_2018": ["punjab national", "nirav modi", "pnb", "lou", "letters of undertaking"],
    "yesbank_2020": ["yes bank", "yesbank"],
    "ilfs_2018": ["il&fs", "ilfs", "infrastructure leasing"],
    "dhfl_2019": ["dhfl", "dewan housing"],
    "ltcm_1998": ["ltcm", "long-term capital", "long term capital"],
    "barings_1995": ["barings", "nick leeson", "leeson"],
    "lehman_2008": ["lehman", "repo 105"],
    "wirecard_2020": ["wirecard", "marsalek"],
}


@functools.lru_cache(maxsize=1)
def _load_cases() -> list[dict]:
    """Load every real (non-dummy) curated case dict from cases/."""
    cases = []
    for path in sorted(CASES_DIR.glob("*.json")):
        try:
            d = json.loads(path.read_text())
        except (json.JSONDecodeError, OSError):
            continue
        if d.get("case_id") in DUMMY_CASE_IDS:
            continue
        cases.append(d)
    return cases


def _keywords_for(case: dict) -> tuple[set[str], set[str]]:
    """(aliases, generic tokens) that identify this case in a recall answer.

    Aliases are curated, distinctive names (e.g. "wirecard") and are weighted heavily so a
    name-brand precedent always beats a typology whose generic tokens ("payments", "wires")
    happen to overlap. Generic tokens come from the institution / case_id and only separate
    cases that have no distinctive alias.
    """
    aliases = {a for a in _CASE_ALIASES.get(case.get("case_id", ""), []) if a}
    generic: set[str] = set()
    inst = (case.get("institution") or "").lower()
    for w in re.split(r"[^a-z0-9&]+", inst):
        if len(w) >= 4 and w not in _STOP:
            generic.add(w)
    for w in (case.get("case_id") or "").lower().split("_"):
        if len(w) >= 4 and not w.isdigit() and w not in _STOP:
            generic.add(w)
    return aliases, generic - aliases


def match_case(*texts: str) -> dict | None:
    """Return the single curated case that best matches the given text(s), or None.

    Scored by how many distinctive keywords appear; multi-word aliases count double so a
    named precedent ("Silicon Valley Bank") beats an incidental single-word overlap.
    """
    hay = " ".join(t for t in texts if t).lower()
    if not hay.strip():
        return None
    best, best_score = None, 0
    for case in _load_cases():
        aliases, generic = _keywords_for(case)
        score = 0
        # Word-boundary match, so "trade" doesn't hit "trades" nor "cross" hit "across".
        for kw in aliases:
            if re.search(rf"\b{re.escape(kw)}\b", hay):
                score += 5            # a distinctive name dominates generic overlap
        for kw in generic:
            if re.search(rf"\b{re.escape(kw)}\b", hay):
                score += 2 if " " in kw else 1
        if score > best_score:
            best, best_score = case, score
    return best if best_score >= 1 else None


# --- Step 1: recall the precedent --------------------------------------------

async def consult(situation: str, dataset: str = PACK_DATASET) -> str:
    """Recall the closest precedent from the installed pack as generated prose.

    Two details matter for matching a GENERIC situation (one that does not name a
    specific institution) to the right precedent:
      - we frame the situation as a question, and
      - we use RAG_COMPLETION (semantic retrieval + one generation) rather than the
        default entity-seeded graph completion, which only fires when the query names an
        entity already in the graph.
    """
    import cognee
    from cognee.modules.search.types.SearchType import SearchType
    query = (
        f"{situation}\n\nWhat past financial-failure precedent from the pack most "
        f"closely matches this situation? Name it, give the warning signs and risk "
        f"factors it shares, and state what should be investigated."
    )
    # top_k caps how many chunks are packed into the completion context. A modest value
    # keeps the single request small (cheaper, and under free-tier per-minute token caps)
    # while still surfacing the closest precedent.
    results = await cognee.recall(
        query, query_type=SearchType.RAG_COMPLETION, datasets=[dataset], top_k=3,
    )
    for e in results:
        text = getattr(e, "answer", None) or getattr(e, "text", None)
        if text:
            return text.strip()
    return "(no precedent found in the installed pack)"


# --- Step 2: rewrite the precedent's playbook against the user's situation ----

async def rewrite_playbook(situation: str, case: dict) -> list[str]:
    """Rewrite a precedent's investigation_steps to reference the user's situation.

    The customisation IS the wow: same expertise, tailored application. The voice is
    locked to SHARED EXPERIENCE — what analysts DID in the precedent, applied to the
    user's entities/instruments/amounts. No second-person imperatives, no advice, no
    disclaimer (that lives in the install note).
    """
    steps = case.get("investigation_steps") or []
    if not steps:
        return []
    import litellm
    litellm.suppress_debug_info = True
    model = os.environ.get("LLM_MODEL", "groq/llama-3.3-70b-versatile")
    key = os.environ.get("LLM_API_KEY")

    numbered = "\n".join(f"{i+1}. {s}" for i, s in enumerate(steps))
    prompt = (
        f"You are {PACK_DISPLAY}, a casebook of senior-analyst experience.\n"
        f"PRECEDENT: {case.get('institution')} ({case.get('year')}) — {case.get('category')}\n"
        f"In that case, experienced analysts investigated it via these steps:\n{numbered}\n\n"
        f"USER'S SITUATION:\n{situation}\n\n"
        "Rewrite EACH step so it references the user's own entities, instruments, and "
        "amounts, describing what the precedent's analysts DID, applied to this situation.\n"
        "Hard rules:\n"
        "- Past-tense, precedent-anchored voice (e.g. 'Analysts sized the concentration in...').\n"
        "- NEVER use second-person imperatives ('you should', 'check', 'do X').\n"
        "- Do NOT issue advice, recommendations, or a disclaimer.\n"
        "- Return ONE rewritten step per line, same count and order, no numbering."
    )
    resp = await litellm.acompletion(
        model=model, api_key=key,
        messages=[{"role": "user", "content": prompt}],
    )
    raw = (resp.choices[0].message.content or "").strip()
    lines = [re.sub(r"^\s*\d+[.)]\s*", "", ln).strip(" -•\t")
             for ln in raw.splitlines() if ln.strip()]
    return lines or steps


# --- The shared entry point both the dashboard and MCP server call ------------

def _invitation(case: dict) -> str:
    return (f"Want me to map how the analysts in the {case.get('institution')} case "
            f"investigated it onto your situation?")


async def consult_with_citations(situation: str, dataset: str = PACK_DATASET,
                                  map_to_situation: bool = False) -> dict:
    """Two-step precedent-first consult, with the evidence trail attached.

    Returns a dict:
      answer          composed precedent-descriptive text (keeps simple surfaces working)
      precedent       {case_id, institution, year, why} or None
      risk_factors    warning-sign chips (graph nodes, not prose)
      invitation      the map-it invitation (step 1 only)
      playbook        rewritten investigation steps (step 2 only, when map_to_situation)
      citations       [{case_id, institution, year, sources[...]}] evidence trail

    Step 1 (identifying the precedent) is KEYLESS — it retrieves from the portable pack
    locally via keyless.retrieve_context (fastembed, no LLM, no Cognee install needed). Only
    Step 2 (map_to_situation) calls the LLM to tailor the playbook.
    """
    from citations import citations_for_case
    from keyless import match_pack_case

    case = match_pack_case(situation)                     # local case-level match, no key
    citations = citations_for_case(case["case_id"]) if case else []

    result: dict = {
        "answer": "(no close precedent found in the installed pack)",
        "precedent": None,
        "risk_factors": [],
        "invitation": "",
        "playbook": None,
        "citations": citations,
    }

    if case:
        result["precedent"] = {
            "case_id": case.get("case_id"),
            "institution": case.get("institution"),
            "year": case.get("year"),
            "why": case.get("category"),
        }
        result["risk_factors"] = list(case.get("risk_signals") or [])

        if map_to_situation:
            playbook = await rewrite_playbook(situation, case)
            result["playbook"] = playbook
            result["answer"] = _compose_map(case, playbook)
        else:
            inv = _invitation(case)
            result["invitation"] = inv
            result["answer"] = _compose_precedent(case, result["risk_factors"], inv)

    return result


def _compose_precedent(case: dict, risk_factors: list[str], invitation: str) -> str:
    lines = [
        f"Closest precedent: {case.get('institution')} ({case.get('year')}).",
        f"Why it matches: {case.get('category')}",
    ]
    if risk_factors:
        lines.append("Shared warning signs:")
        lines += [f"  - {s}" for s in risk_factors]
    lines += ["", invitation]
    return "\n".join(lines)


def _compose_map(case: dict, playbook: list[str]) -> str:
    lines = [
        f"Closest precedent: {case.get('institution')} ({case.get('year')}).",
        "How analysts in matching cases investigated it, applied to your situation:",
    ]
    lines += [f"  - {s}" for s in playbook]
    return "\n".join(lines)


# --- The bare-LLM baseline + contrast harness --------------------------------

async def bare_llm(question: str) -> str:
    """Ask the SAME question to the raw configured LLM with NO pack — the baseline."""
    import litellm
    litellm.suppress_debug_info = True
    model = os.environ.get("LLM_MODEL", "groq/llama-3.3-70b-versatile")
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
    print("BARE LLM  (no pack — confidently prescribes, ungrounded)")
    print("-" * 70)
    print(await bare_llm(situation), "\n")
    print("-" * 70)
    print(f"{PACK_DISPLAY}  (precedent recalled via consult_pack)")
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
