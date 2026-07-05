"""
config.py — one place for the pack's identity and the repo's paths.

Everything else imports from here, so there are no magic strings scattered across
the codebase. Change the version in ONE place and the dataset name, manifest, and
export filename all follow.
"""

from pathlib import Path

# --- Pack identity (flows into pack.json and the Cognee dataset name) --------
PLATFORM = "memory-mesh"      # the marketplace this pack belongs to
PACK_NAME = "risklore"        # this pack's name
PACK_VERSION = "0.1.0"        # dummy-data version; bumped to 1.0.0 in Phase 6

# Locked design decision #7: the pack's DATASET boundary IS the pack boundary.
# Import mounts into an isolated dataset named "{pack_name}@{version}", and
# uninstall is a single forget() on that dataset — the 5-second reversibility beat.
PACK_DATASET = f"{PACK_NAME}@{PACK_VERSION}"    # e.g. "risklore@0.1.0"

# --- Repo directory layout ---------------------------------------------------
# Resolved relative to this file, so scripts work no matter where they're run from.
ROOT = Path(__file__).resolve().parent.parent

SOURCES_DIR = ROOT / "sources"          # raw case PDFs — the EVIDENCE layer
CASES_DIR = ROOT / "cases"              # seven-field curated JSON — the EXPERTISE layer
ONTOLOGY_DIR = ROOT / "ontology"
ONTOLOGY_FILE = ONTOLOGY_DIR / "risklore.owl"
PACK_DIR = ROOT / "pack"                # built .mempack artifacts

# The export filename target (Phase 4): risklore-0.1.0.mempack
PACK_FILENAME = f"{PACK_NAME}-{PACK_VERSION}.mempack"
