# SFDPH source notes

Attempted to fetch:
- https://www.sf.gov/sites/default/files/2025-01/Residential%20Care%20and%20Treatment%20Workgroup%20Report%20FINAL%201.7.25_Report%20and%20Appendix.pdf
  Result: PDF located and confirmed to exist (9.6MB) via search, but WebFetch tool returned only raw/compressed PDF binary artifacts — could not extract readable table content in this session. The URL is valid and should be re-attempted with a proper PDF-to-text pipeline (e.g. `pdftotext` locally after downloading) in a follow-up pass.

- https://www.sf.gov/documents/53210/SanFrancisco_BHSA_Integrated_Plan_FY2026-29__-_Draft_for_Public_Comment.pdf
  Located via search (draft released for public comment ~April 2026) but not deep-fetched in this pass; same PDF-extraction limitation likely applies.

- SFDPH Behavioral Health Clinic Locations page (https://www.sf.gov/resource--2024--behavioral-health-clinic-locations) — identified as the authoritative directory of county-run outpatient clinics; individual clinics (Mission Mental Health, Chinatown North Beach Mental Health, Southeast Child/Family Therapy Center) were captured via search snippets and added to facilities.json, but the full clinic list was not exhaustively enumerated.

## Recommendation for follow-up
Download the two PDFs above directly (curl) and run through a local PDF text extractor to pull the full facility/bed-count tables referenced in the Residential Care and Treatment Workgroup Report (Jan 2025) — this is likely the single richest source for exact bed counts across SF's residential behavioral health continuum and was only partially exploited in this pass.
