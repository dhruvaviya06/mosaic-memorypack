"""
validate_cases.py — enforce the case CONTRACT (schema.py) on every file in cases/.

This is what the teammate authoring cases runs to check their work, and what the
build pipeline runs as a gate before ingesting anything. It is intentionally strict
about structure (missing/mistyped fields = ERROR) but lenient about evidence that
hasn't landed yet (a source PDF not yet in sources/ = WARNING).

Run:  .venv/bin/python src/validate_cases.py
Exit code 0 = all cases valid; 1 = at least one error (usable in CI / build gates).
"""

import json
import sys

from config import CASES_DIR, SOURCES_DIR
from schema import ALL_FIELDS, LIST_FIELDS, TEXT_FIELDS, INT_FIELDS


def validate_case(data: dict) -> tuple[list[str], list[str]]:
    """Return (errors, warnings) for a single parsed case dict."""
    errors: list[str] = []
    warnings: list[str] = []

    # 1) Every required field must be present.
    for field in ALL_FIELDS:
        if field not in data:
            errors.append(f"missing required field: '{field}'")

    # 2) Unknown extra fields are allowed but flagged, so drift is visible.
    for field in data:
        if field not in ALL_FIELDS:
            warnings.append(f"unknown field (ignored by pack build): '{field}'")

    # 3) Type + non-emptiness checks for the fields that ARE present.
    for field in LIST_FIELDS & data.keys():
        value = data[field]
        if not isinstance(value, list):
            errors.append(f"'{field}' must be a list, got {type(value).__name__}")
        elif not value:
            errors.append(f"'{field}' must not be empty")
        elif not all(isinstance(item, str) and item.strip() for item in value):
            errors.append(f"'{field}' must be a list of non-empty strings")

    for field in TEXT_FIELDS & data.keys():
        value = data[field]
        if not isinstance(value, str) or not value.strip():
            errors.append(f"'{field}' must be a non-empty string")

    for field in INT_FIELDS & data.keys():
        # JSON booleans are ints in Python, so exclude bool explicitly.
        if not isinstance(data[field], int) or isinstance(data[field], bool):
            errors.append(f"'{field}' must be an integer")

    # 4) Provenance: each listed source document should eventually exist in sources/.
    for name in data.get("source_documents", []) or []:
        if isinstance(name, str) and not (SOURCES_DIR / name).exists():
            warnings.append(f"source document not found in sources/ (yet): '{name}'")

    return errors, warnings


def main() -> int:
    files = sorted(CASES_DIR.glob("*.json"))
    if not files:
        print(f"No case files found in {CASES_DIR}/ — nothing to validate yet.")
        return 0

    total_errors = 0
    for path in files:
        try:
            data = json.loads(path.read_text())
        except json.JSONDecodeError as e:
            print(f"✗ {path.name}: invalid JSON — {e}")
            total_errors += 1
            continue

        errors, warnings = validate_case(data)
        if errors:
            total_errors += len(errors)
            print(f"✗ {path.name}: {len(errors)} error(s)")
            for msg in errors:
                print(f"    ERROR:   {msg}")
        else:
            print(f"✓ {path.name}")
        for msg in warnings:
            print(f"    warning: {msg}")

    print("-" * 60)
    if total_errors:
        print(f"FAILED — {total_errors} error(s) across {len(files)} file(s).")
        return 1
    print(f"OK — all {len(files)} case file(s) valid.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
