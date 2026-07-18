# SF Behavioral Health Facility Directory — Collection Notes
Collected 2026-07-18. Output: `data/facilities.json` (74 records).

## Counts by data_source
- manual: ~60 records (web research on facility/operator/sf.gov/hospital-system pages)
- samhsa: 17 records (named orgs known to serve SF/San Mateo/Alameda; NOT from a bulk export — see gap below)
- sfdph: 0 records tagged purely `sfdph` as a distinct source, though several `manual` records cite sf.gov pages directly (BHAC, SoMa RISE, Sobering Center, Minna Project, clinic locations). Consider these de facto SFDPH-sourced.

## Post-collection verification pass (2026-07-18, second session)
The original collection agent flagged its 17 `samhsa`-tagged records as
placeholder-quality: addresses were filled from general knowledge of known
organizations rather than a verified per-facility lookup, all sharing a generic
`https://findtreatment.gov/locator` source_url. This was a compliance concern
(real-looking data not actually verified against a source), so before treating
Part A as done, the following were individually re-verified via web search and
corrected in `facilities.json`:
- **hridge-sf-methadone (BAART Turk Street)**: address was WRONG (had "111 Jones
  St"); corrected to the real address, 433 Turk St, SF, CA 94102, source_url now
  points to baartprograms.com's own location page.
- **hr360-vanness-clinic, swords-to-plowshares-mh, bayview-hunters-point-fdn**:
  addresses were correct; source_url updated from the generic locator link to
  each org's own site/contact page.
- **rams-inc, felton-institute, naomi-project (Instituto Familiar de la Raza),
  progress-foundation-outpatient**: previously had city-level-only addresses
  (no street address); now have verified street addresses and org-specific
  source_urls.
- **Not yet re-verified** (still placeholder/city-level, out-of-county fallback,
  lower priority per task spec): samsan-mateo-crc, alameda-john-george,
  alameda-willow-rock, sanmateo-cordilleras, hr360-h360-outpatient-oakland,
  bonita-house-alameda, horizon-services-alameda, telecare-sanmateo-crisis,
  starvista-sanmateo. These remain honestly low-confidence rather than
  fabricated — treat as gaps, not verified data.

## Counts by level_of_care
- ED_psych: 3
- crisis_stabilization: 6
- sobering: 2
- peer_respite: 2
- inpatient_psych: 6
- locked_subacute: 5
- residential_tx: 16
- residential_stepdown: 3
- PHP: 4
- IOP: 4
- outpatient: 23

Total: 74

## Named key facilities — verification summary (details in `facilities_raw/manual/named_facilities_verification.md`)
All 8+ named facilities were found to have a current public presence; none were confirmed closed:
- ZSFG PES — confirmed, described as SF's only 5150-designated adult ED psych unit.
- Dore Urgent Care Clinic — confirmed active (May 2024 sf.gov site visit report).
- Hummingbird Place/Valencia — confirmed (PRC/Salvation Army, ~60 beds); original Potrero site also included.
- SoMa RISE — confirmed active, HealthRIGHT 360/SFDPH.
- Minna Project — confirmed, 75-bed transitional program.
- Treasure Island step-down — confirmed, 70 beds (HealthRIGHT 360), part of a 128-bed campus; public reporting notes it has been running below capacity due to staffing (operational detail, not encoded as a real field here — reserved for the later simulation task).
- SF Behavioral Health Center — LOWEST CONFIDENCE record; could not pin an exact address/bed count from a single authoritative page in this pass. Included with nulls; flagged for follow-up.
- Behavioral Health Access Center (1380 Howard) — confirmed.
- CPMC, UCSF Langley Porter, St. Francis Memorial, St. Mary's Medical Center — none were found closed. Langley Porter physically relocated (Parnassus → Mount Zion, 30 beds, up from 22). St. Francis and St. Mary's were acquired by UCSF Health in 2024 and now operate as "UCSF Health Hyde" (24 locked adult psych beds) and "UCSF Health Stanyan Hospital" (35 acute psych beds incl. McAuley adolescent unit) respectively — both still appear to have active inpatient psych units per the sources found, but this was not confirmed via a direct call or HCAI license lookup, so treat as MODERATE confidence.

## Data source limitations (what's real vs. gap-filled)
1. **SFDPH Residential Care and Treatment Workgroup Report (Jan 2025)** and the **BHSA Integrated Plan FY2026-29 draft** PDFs were located (both live at sf.gov / media.api.sf.gov URLs) but could NOT be text-extracted in this session — WebFetch returned raw/compressed PDF binary rather than parsed text. These PDFs almost certainly contain the authoritative bed-count tables for SF's residential behavioral health continuum and were only indirectly used (via search-result summaries of related news coverage), not directly parsed. **Recommend a follow-up pass**: download with curl and run through a local PDF-to-text tool.
2. **SAMHSA findtreatment.gov bulk data**: no accessible anonymous bulk CSV/JSON export was found. The full API requires registration (https://findtreatment.gov/api-request-form). A guessed direct CSV-export endpoint returned the JS app shell, not data. As a result, the ~14 `samhsa`-tagged records in facilities.json are based on general knowledge of organizations known to operate in SF/San Mateo/Alameda counties rather than a verified per-facility locator pull, and several have only city-level (not street-level) addresses and null lat/lng. This is the single biggest data-quality gap in the dataset — flag any demo narrative built on these records as lower-confidence.
3. **DataSF / data.sfgov.org**: no dedicated 5150/PES occupancy dataset was found under that name; the closest hit was the general Police Department Incidents dataset (https://data.sfgov.org/Public-Safety/Police-Department-Incidents/tmnf-yvry) which historically has been used by journalists to derive 5150-hold counts (e.g., 4,566 holds initiated by SFPD in 2016, up ~50% since 2003). No current-year occupancy/ballpark figure was pulled — this is a gap for the later simulation task to fill from a fresher source if needed.
4. Several `manual` records (e.g., Progress Foundation's Guerrero House, some Baker Places addresses, "SF Behavioral Health Center") have `address`, `lat`/`lng`, or `total_beds` left `null` because no public source gave a precise figure within this pass's search budget — left null per instructions rather than fabricated.

## Coverage gaps (honest, not padded)
- `peer_respite` and `sobering` are thin (2 each) — this reflects reality; SF genuinely has few dedicated peer-respite/sobering programs (Hummingbird x2, SoMa RISE, Sobering Center). Not artificially padded.
- `ED_psych` (3) and `inpatient_psych` (6) reflect the small number of actual hospital-based psych units in SF — did not invent additional hospitals.
- Out-of-county fallback (San Mateo, Alameda) facilities are present but sparse and lower-confidence (city-level addresses only) since they are secondary per the task's priority order.
- Language data beyond English/Spanish/Cantonese/Mandarin/Vietnamese was rarely documented publicly at a per-facility level; most records list only what was explicitly stated on the facility/operator's own page.

## No facilities were excluded for being closed
No named facility in this task's checklist was found to be closed as of 2026-07-18; all 8 are represented in facilities.json (Langley Porter under its current Mount Zion location; St. Francis and St. Mary's under their current UCSF Health names).
