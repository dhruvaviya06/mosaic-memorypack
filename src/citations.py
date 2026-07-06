"""
citations.py — turn a consult answer into an evidence trail (provenance IS the product).

The consult answer names a precedent (e.g. "IL&FS (2018)"). We map that case to its
source documents using the pack's provenance.json — so every answer can render the
regulatory/judicial documents it rests on. Case-level provenance (which survives in the
pack) is enough; we do not depend on node-level source_ref surviving re-import.

Shared by BOTH the Node dashboard UI and the MCP server, per the access architecture.
"""

import json
import tarfile

from config import PACK_FILE

# filename (as in provenance.json / sources/) -> human label + canonical URL
SOURCE_META = {
    "archegos_cs_paulweiss_2021_sec.htm": {
        "label": "CS / Archegos — Paul, Weiss report (SEC EDGAR, 2021)",
        "url": "https://www.sec.gov/Archives/edgar/data/1053092/000137036821000064/a210729-ex992.htm"},
    "svb_fed_barr_report_2023.pdf": {
        "label": "Federal Reserve — Barr Report on SVB (2023)",
        "url": "https://www.federalreserve.gov/publications/files/svb-review-20230428.pdf"},
    "pnb_niravmodi_ewhc_2022.pdf": {
        "label": "UK High Court — Modi v Govt of India (EWHC, 2022)",
        "url": "https://www.judiciary.uk/wp-content/uploads/2022/11/2022-EWHC-2829-Admin-CO-1537-2021-Modi-v-Government-of-India-Approved-Judgment.pdf"},
    "yesbank_rbi_reconstruction_scheme_2020.pdf": {
        "label": "RBI — Yes Bank Reconstruction Scheme (2020)",
        "url": "https://rbidocs.rbi.org.in/rdocs/content/pdfs/DraftSoR232020UK.pdf"},
    "yesbank_rbi_press_release_2020.htm": {
        "label": "RBI — Yes Bank moratorium press release (2020)",
        "url": "https://www.rbi.org.in/scripts/BS_PressReleaseDisplay.aspx?prid=49479"},
    "ilfs_rbi_fsr_june2019.pdf": {
        "label": "RBI — Financial Stability Report (Jun 2019)",
        "url": "https://www.rbi.org.in/Scripts/FsReports.aspx"},
    "dhfl_nclt_ibbi_order_2019.pdf": {
        "label": "NCLT / IBBI — DHFL administrator order (2019)",
        "url": "https://ibbi.gov.in/uploads/order/4dc4028ccc12768a83b5726399fc8698.pdf"},
}

# distinctive keywords per deep case, for matching which case an answer cites
CASE_KEYWORDS = {
    "archegos_2021": ["archegos"],
    "svb_2023": ["silicon valley bank", "svb"],
    "pnb_niravmodi_2018": ["punjab national", "nirav modi", "pnb"],
    "yesbank_2020": ["yes bank"],
    "ilfs_2018": ["il&fs", "ilfs", "infrastructure leasing"],
    "dhfl_2019": ["dhfl", "dewan housing"],
}

_PROV_CACHE = None


def load_provenance() -> dict:
    """case_id -> {institution, year, source_documents} from the installed pack."""
    global _PROV_CACHE
    if _PROV_CACHE is None:
        with tarfile.open(PACK_FILE, "r:gz") as tar:
            _PROV_CACHE = json.load(tar.extractfile("provenance.json"))
    return _PROV_CACHE


def citations_for(answer: str) -> list[dict]:
    """Return the evidence trail for the cases named in a consult answer.

    Each entry: {case_id, institution, year, sources:[{name, label, url}]}.
    """
    prov = load_provenance()
    low = (answer or "").lower()
    out = []
    for case_id, keywords in CASE_KEYWORDS.items():
        if any(k in low for k in keywords):
            p = prov.get(case_id, {})
            sources = []
            for name in p.get("source_documents", []):
                meta = SOURCE_META.get(name, {})
                sources.append({"name": name,
                                "label": meta.get("label", name),
                                "url": meta.get("url")})
            out.append({"case_id": case_id,
                        "institution": p.get("institution", case_id),
                        "year": p.get("year"),
                        "sources": sources})
    return out
