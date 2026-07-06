"""
throttled_build.py — build the Tessera graph ONE CASE AT A TIME, for rate-limited tiers.

WHEN TO USE THIS instead of `src/build_memory.py --all`:
  The normal build calls `remember([all case texts])` in one shot, and cognee fires the
  graph-extraction LLM calls concurrently. On a free tier that BURSTS past the per-minute
  request/token cap, throws a storm of 429s, exhausts retries, and dies with nothing saved.
  This script ingests one case at a time with a gap + backoff, so it stays under the cap.
  Slower, but it finishes — and it's RESUMABLE (a hard stop, e.g. a daily cap, doesn't lose
  the cases already in the graph; just re-run and it picks up where it left off).

  Verified path: `LLM_MODEL=groq/llama-3.1-8b-instant` (its own per-model daily budget) +
  this script built all 40 cases where a single-shot build on 70b/Gemini could not.

USAGE:
  .venv/bin/python scripts/throttled_build.py                 # build all 40 (resumes)
  .venv/bin/python scripts/throttled_build.py --scope deep    # only the 6 deep-tier cases
  .venv/bin/python scripts/throttled_build.py --prune         # clean start (prune + reset)
  .venv/bin/python scripts/throttled_build.py --gap 10        # longer pause between cases

Then publish + install as usual:  src/mesh.py publish  &&  src/mesh.py install
"""

import argparse
import asyncio
import json
import sys
from pathlib import Path

# Make src/ importable no matter where this is run from, and load the repo's .env.
_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "src"))

from dotenv import load_dotenv
load_dotenv(_ROOT / ".env")

import cognee
from config import PACK_DATASET
from build_memory import case_to_text, select_cases

# Progress lives at the repo root and is gitignored — one re-run resumes from here.
PROGRESS = _ROOT / ".throttled_build_progress.json"
MAX_RETRIES = 6          # per-case retries on 429 with escalating backoff


def _load_done() -> set[str]:
    if PROGRESS.exists():
        return set(json.loads(PROGRESS.read_text()))
    return set()


def _save_done(done: set[str]) -> None:
    PROGRESS.write_text(json.dumps(sorted(done)))


async def _remember_one(case: dict) -> None:
    text = case_to_text(case)
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            await cognee.remember([text], dataset_name=PACK_DATASET, self_improvement=False)
            return
        except Exception as e:  # noqa: BLE001 — inspect message to decide retry vs re-raise
            msg = str(e)
            is_rate = "429" in msg or "RateLimit" in msg or "rate_limit" in msg
            if not is_rate or attempt == MAX_RETRIES:
                raise
            backoff = 20 * attempt
            print(f"    429 on '{case['case_id']}' (attempt {attempt}) — sleeping {backoff}s",
                  flush=True)
            await asyncio.sleep(backoff)


async def main(scope: str, gap: int, prune: bool) -> int:
    if prune:
        # Clean start: drop the whole store (so old nodes don't leak into export) + progress.
        print("=== prune: clearing graph/vector/relational state + progress ===", flush=True)
        await cognee.prune.prune_data()
        await cognee.prune.prune_system(metadata=True)
        PROGRESS.unlink(missing_ok=True)

    cases = select_cases(scope)
    done = _load_done()
    todo = [c for c in cases if c["case_id"] not in done]
    print(f"=== throttled build ({scope}): {len(done)} done, {len(todo)} to go "
          f"(of {len(cases)}) ===", flush=True)

    for i, case in enumerate(todo, 1):
        cid = case["case_id"]
        try:
            await _remember_one(case)
        except Exception as e:  # noqa: BLE001
            print(f"[STOP] '{cid}' failed hard: {str(e)[:160]}", flush=True)
            print(f"[STOP] progress saved ({len(done)}/{len(cases)}). Re-run to resume.",
                  flush=True)
            _save_done(done)
            return 2
        done.add(cid)
        _save_done(done)
        print(f"[{len(done)}/{len(cases)}] ingested {cid}", flush=True)
        if i < len(todo):
            await asyncio.sleep(gap)

    print("=== all cases ingested — running improve() enrichment ===", flush=True)
    try:
        await cognee.improve(dataset=PACK_DATASET)
    except Exception as e:  # noqa: BLE001
        print(f"[warn] improve() failed ({str(e)[:120]}) — graph still usable without it",
              flush=True)
    print("[done] throttled build complete. Next: src/mesh.py publish && src/mesh.py install",
          flush=True)
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Rate-limit-friendly, resumable Tessera build.")
    ap.add_argument("--scope", choices=["deep", "all"], default="all",
                    help="'all' = 40 cases (default); 'deep' = the 6 primary-source cases")
    ap.add_argument("--gap", type=int, default=6,
                    help="seconds to pause between cases (raise if you still hit 429s)")
    ap.add_argument("--prune", action="store_true",
                    help="prune all cognee state + reset progress before building (clean start)")
    args = ap.parse_args()
    sys.exit(asyncio.run(main(args.scope, args.gap, args.prune)))
