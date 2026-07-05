"""
schema.py — THE CONTRACT between the pipeline and the teammate authoring cases.

Each curated case is one JSON file in cases/. It must contain the seven "expertise"
fields plus the provenance-meta fields. `validate_cases.py` enforces this exactly, so
this file is the single source of truth for what a valid case looks like.

Field-shape rules (kept deliberately simple):
  - LIST fields hold a list of short strings (each becomes graph-friendly structure).
  - TEXT fields hold a prose string.
  - "year" is an integer.
"""

# The seven-field case schema (adopted from the Memory Mesh doc). Order = narrative order.
CASE_FIELDS = [
    "category",             # TEXT  — kind of failure / risk domain
    "risk_signals",         # LIST  — observable warning signs, one per item
    "analyst_reasoning",    # TEXT  — how an analyst reads those signals
    "investigation_steps",  # LIST  — what to check / how to dig, one step per item
    "decision",             # TEXT  — the call that was (or should have been) made
    "outcome",              # TEXT  — what actually happened
    "lessons_learned",      # LIST  — durable heuristic(s), one per item
]

# Provenance-meta fields — the auditability / "verified" story.
META_FIELDS = [
    "case_id",              # TEXT  — stable id, e.g. "archegos_2021"
    "institution",          # TEXT  — e.g. "Archegos Capital Management"
    "year",                 # INT   — e.g. 2021
    "source_documents",     # LIST  — filenames that must exist in sources/
]

ALL_FIELDS = CASE_FIELDS + META_FIELDS

# Type expectations used by the validator.
LIST_FIELDS = {"risk_signals", "investigation_steps", "lessons_learned", "source_documents"}
TEXT_FIELDS = {"category", "analyst_reasoning", "decision", "outcome", "case_id", "institution"}
INT_FIELDS = {"year"}
