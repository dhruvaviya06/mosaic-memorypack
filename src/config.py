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

# Human-facing pack label — used in the manifest, registry UI, and demo narration.
PACK_LABEL = f"{PACK_NAME}@{PACK_VERSION}"      # e.g. "risklore@0.1.0"

# Locked design decision #7: the pack's DATASET boundary IS the pack boundary.
# Import mounts into an isolated dataset, and uninstall is a single forget() on it —
# the 5-second reversibility beat.
# NOTE: cognee 1.2.2 forbids '.' and ' ' in dataset names, so we can't use PACK_LABEL
# ("risklore@0.1.0") directly. This is the cognee-safe internal name; the pretty label
# above is what humans see.
PACK_DATASET = f"{PACK_NAME}_{PACK_VERSION.replace('.', '_')}"   # e.g. "risklore_0_1_0"

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
PACK_FILE = PACK_DIR / PACK_FILENAME

# --- Pack manifest metadata (pack.json) --------------------------------------
PUBLISHER = "dhruvaviya06 (Memory Mesh)"
LICENSE = "single-tenant, no re-export"
# Verification tier: the deep cases are AI-extracted from real regulatory/judicial
# primary sources, pending human verification (which would upgrade this to
# "human-verified primary-source"). Not "dummy" anymore — real cases now exist.
VERIFICATION_TIER = "ai-extracted primary-source"

# On import, the pack mounts into a SEPARATE dataset, so we can prove the answer
# survives a full export -> forget-original -> import round-trip.
IMPORTED_DATASET = f"{PACK_DATASET}_imported"    # e.g. "risklore_0_1_0_imported"
