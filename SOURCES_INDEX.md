# Sources Index — Tessera v1.0

Derived from `sources_map.md`. This file is a **reference for populating `source_documents`
in the case JSONs**; it is NOT ingested (lives outside `sources/`, and is not a case file).

Two-tier ingestion rule:
- **DEEP tier (cases 34–39):** source document downloaded into `sources/` AND cognified.
- **LIGHT tier (cases 1–33, 40):** URL string in the case JSON is sufficient; **no PDF ingested**.
- Umbrella docs cover many LIGHT cases; reuse the same `source_ref` freely.

## Deep-tier sources — in `sources/`, WILL be ingested
| Case | Institution | File in `sources/` | Origin | Note |
|------|-------------|--------------------|--------|------|
| 34 | Archegos | `archegos_cs_paulweiss_2021_sec.htm` | SEC EDGAR (CS 6-K exhibit) | HTML (~98k words); the Paul Weiss report |
| 35 | SVB | `svb_fed_barr_report_2023.pdf` | federalreserve.gov | PDF |
| 36 | PNB / Nirav Modi | `pnb_niravmodi_ewhc_2022.pdf` | judiciary.uk (EWHC 2829) | PDF |
| 37 | Yes Bank | `yesbank_rbi_reconstruction_scheme_2020.pdf` (+ `yesbank_rbi_press_release_2020.htm`) | rbidocs.rbi.org.in (via browser) + rbi.org.in | Full RBI Reconstruction Scheme 2020 PDF, plus the press release |
| 38 | IL&FS | `ilfs_rbi_fsr_june2019.pdf` | RBI FSR Jun 2019 (phdcci mirror) | PDF; NBFC-contagion chapter. rbidocs original blocked curl |
| 39 | DHFL | `dhfl_nclt_ibbi_order_2019.pdf` | ibbi.gov.in (NCLT order) | PDF; RBI supersession press release is HTML-only |

## Umbrella docs — reference-only (LIGHT tier), NOT ingested
| ID | Doc | Status | Covers cases |
|----|-----|--------|--------------|
| U1 | RBI "BE(A)WARE" 2022 | PENDING — rbidocs blocks curl; URL: https://rbidocs.rbi.org.in/rdocs/content/pdfs/BEAWARE07032022.pdf | 1,2,3,4,5,6,7,8,11,12,14 |
| U7a | FIU-IND Annual Report 2021-22 | `fiu_ind_annual_report_2021_22.pdf` | 13,14,15,16,19 |
| U7b | FIU-IND STR Trend Analysis | `fiu_ind_str_trend_analysis.pdf` | 13,14,15,16,19 |
| U8a | FATF TBML Trends & Developments | PENDING — Cloudflare 403; URL: https://www.fatf-gafi.org/content/dam/fatf-gafi/reports/Trade-Based-Money-Laundering-Trends-and-Developments.pdf | 18 |
| U8b | FATF TBML Risk Indicators | PENDING — Cloudflare 403; URL: https://www.fatf-gafi.org/content/dam/fatf-gafi/reports/Trade-Based-Money-Laundering-Risk-Indicators.pdf | 16 |
| U12 | ACFE Report to the Nations 2024 | `acfe_report_to_the_nations_2024.pdf` (20 MB) | 25,26,27,29,30 |
| U2–U6, U9–U11, U13–U15 | (various) | [NAVIGATE] — no direct URL; LIGHT tier, URL in JSON suffices; not downloaded | see sources_map.md |

## When populating case JSONs
- `source_documents` for a **deep-tier** case = the filename above (e.g. `["svb_fed_barr_report_2023.pdf"]`).
- `source_documents` for a **light-tier** case = the umbrella doc's URL/filename ref (reuse across cases is expected and honest).
- Any [NAVIGATE] source not locatable in ~5 min → `"source_documents": ["pending — <name>"]` and move on.
