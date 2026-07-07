"""
run_eval.py — measure precedent-match accuracy on HELD-OUT scenarios.

Matching is the whole product, so this makes it a number. Each scenario in eval_set.json is
a paraphrased situation (not copied from any case) labeled with its known-correct precedent.
We run each through the KEYLESS retriever (the product's Step 1) and report top-1 / top-3
accuracy. The eval set lives here, deliberately OUT of the pack and out of cases/.

Keyless -> no LLM key, no cost. Run:  .venv/bin/python eval/run_eval.py
"""

import json
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "src"))

from keyless import rank_cases

EVAL_SET = Path(__file__).with_name("eval_set.json")


def main() -> int:
    items = json.loads(EVAL_SET.read_text())
    if not items:
        print("empty eval set")
        return 1

    rows, top1, top3 = [], 0, 0
    for it in items:
        expected, situation = it["expected"], it["situation"]
        ranked = rank_cases(situation, k=3)
        ids = [c["case_id"] for c, _ in ranked]
        got = ids[0] if ids else None
        h1, h3 = (got == expected), (expected in ids)
        top1 += h1
        top3 += h3
        rows.append((expected, got, h1, h3))

    n = len(items)
    print(f"{'expected':34}{'top-1 match':34}t1 t3")
    print("-" * 78)
    for expected, got, h1, h3 in rows:
        print(f"{expected:34}{str(got):34}{'Y ' if h1 else '. '} {'Y' if h3 else '.'}")
    print("-" * 78)
    print(f"top-1 accuracy: {top1}/{n} = {100 * top1 / n:.0f}%")
    print(f"top-3 accuracy: {top3}/{n} = {100 * top3 / n:.0f}%")
    return 0


if __name__ == "__main__":
    sys.exit(main())
