"""
config.py — one place for the pack's identity, positioning, and the repo's paths.

Everything else imports from here, so there are no magic strings scattered across
the codebase. The pack is built NAME-AGNOSTIC off PACK_NAME: swap that one constant
and the dataset name, manifest, export filename, ontology filename, and MCP server
name all follow. Change the version in ONE place and every artifact tracks it.
"""

from pathlib import Path

# --- Pack identity (flows into pack.json and the Cognee dataset name) --------
PLATFORM = "mosaic"                # the platform this pack belongs to
PACK_NAME = "tessera"             # this pack's name (a tessera = one tile of a mosaic)
PACK_VERSION = "0.1.0"             # pack version (bump on re-curation)

# Human-facing pack label — used in the manifest, dashboard, and demo narration.
PACK_LABEL = f"{PACK_NAME}@{PACK_VERSION}"      # e.g. "tessera@0.1.0"
PACK_DISPLAY = PACK_NAME.capitalize()            # e.g. "Tessera" (title-case UI label)

# --- Positioning (drives all copy; single source of truth for the framing) ---
# Tessera is NOT "a database of financial disasters". It is a CASEBOOK of senior-analyst
# experience: financially analysed cases — historical failures AND investigation
# typologies — each capturing how expert analysts recognised the pattern and what steps
# resolved (or should have resolved) it. Cognee maps these into a graph, matches the
# user's situation to a precedent, and surfaces the steps experienced analysts took.
PACK_CASE_COUNT = 40
PACK_TAGLINE = "senior-analyst expertise, installable"
PACK_PITCH = (
    f"{PACK_DISPLAY}: {PACK_CASE_COUNT} analysed cases; describe your situation, "
    f"get the precedent and the playbook."
)

# The ONLY disclaimer in the product. Shown once, at install time (CLI + dashboard +
# README) — never repeated per answer. Frames the pack as shared experience, not advice.
INSTALL_NOTE = (
    f"{PACK_DISPLAY} is a casebook of senior-analyst experience — {PACK_CASE_COUNT} "
    "analysed cases. It surfaces the precedent your situation most resembles and how "
    "experienced analysts investigated it, so you don't repeat mistakes already made. "
    f"{PACK_DISPLAY} shares experience, not instructions — you connect the precedent "
    "to your own case."
)

# Locked design decision: the pack's DATASET boundary IS the pack boundary.
# Install mounts into an isolated dataset, and uninstall is a single forget() on it —
# the 5-second reversibility beat.
# NOTE: cognee 1.2.2 forbids '.' and ' ' in dataset names, so we can't use PACK_LABEL
# ("tessera@0.1.0") directly. This is the cognee-safe internal name; the pretty label
# above is what humans see.
PACK_DATASET = f"{PACK_NAME}_{PACK_VERSION.replace('.', '_')}"   # e.g. "tessera_0_1_0"

# The learn-and-forget loop writes each resolved consult as a DISTILLED case into this
# SEPARATE dataset, so the org's memory accumulates its own cases while the curated pack
# stays clean and unmutated. The raw user input is forget()-ten after resolution.
ORG_CASES_DATASET = f"{PACK_DATASET}_org_cases"    # e.g. "tessera_0_1_0_org_cases"

# --- Repo directory layout ---------------------------------------------------
# Resolved relative to this file, so scripts work no matter where they're run from.
ROOT = Path(__file__).resolve().parent.parent

SOURCES_DIR = ROOT / "sources"          # raw case PDFs — the EVIDENCE layer
CASES_DIR = ROOT / "cases"              # seven-field curated JSON — the EXPERTISE layer
ONTOLOGY_DIR = ROOT / "ontology"
ONTOLOGY_FILE = ONTOLOGY_DIR / f"{PACK_NAME}.owl"    # on-disk ontology, tracks PACK_NAME
PACK_DIR = ROOT / "pack"                # built .mempack artifacts

# The ontology's filename INSIDE a .mempack is generic, so export/import never hardcode
# a pack name — the pack format stays name-agnostic.
PACK_ONTOLOGY_MEMBER = "ontology.owl"

# The export filename target: tessera-0.1.0.mempack
PACK_FILENAME = f"{PACK_NAME}-{PACK_VERSION}.mempack"
PACK_FILE = PACK_DIR / PACK_FILENAME

# --- Pack manifest metadata (pack.json) --------------------------------------
PUBLISHER = "dhruvaviya06 (Mosaic)"
LICENSE = "single-tenant, no re-export"
# Verification tier: the deep cases are AI-extracted from real regulatory/judicial
# primary sources, pending human verification (which would upgrade this to
# "human-verified primary-source").
VERIFICATION_TIER = "ai-extracted primary-source"

# On install, the pack mounts into a SEPARATE dataset, so we can prove the answer
# survives a full export -> forget-original -> import round-trip.
IMPORTED_DATASET = f"{PACK_DATASET}_imported"    # e.g. "tessera_0_1_0_imported"

# --- Case tiers (two-tier ingestion rule) ------------------------------------
# Deep-tier cases are backed by a downloaded primary-source document and give the
# strongest evidence-trail / multi-hop demo; they are built first (quota-safe).
DEEP_TIER_CASE_IDS = {
    "archegos_2021", "svb_2023", "pnb_niravmodi_2018",
    "yesbank_2020", "ilfs_2018", "dhfl_2019",
}
# The dummy case is never part of a real pack build.
DUMMY_CASE_IDS = {"fakebank_2020"}
