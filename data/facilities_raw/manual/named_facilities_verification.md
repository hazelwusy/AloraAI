# Manual verification notes — named key facilities (checked 2026-07-18)

## Verified, currently operating
- **ZSFG Psychiatric Emergency Services (PES)** — 1001 Potrero Ave. Confirmed via zuckerbergsanfranciscogeneral.org and UCSF Public Psychiatry Fellowship page. Widely described (SF courts resource PDF, Steinberg Institute) as the only designated evaluation/holding facility for adult 5150 holds in SF County. Included as `zsfg-pes`, ED_psych, designation_5150=true.
  Source: https://www.zuckerbergsanfranciscogeneral.org/services/psychiatric-emergency-services-pes/

- **Dore Urgent Care Clinic** — 52 Dore St/Alley, SF 94103. Operated by Progress Foundation under SFDPH contract. 24/7 drop-in psychiatric crisis triage, feeds into Progress Foundation's 14-day Acute Diversion Unit. Confirmed via sf.gov site-visit PDF (May 2024) — still active as of that report.
  Source: https://media.api.sf.gov/documents/BHC_Site_Visit_Dore_Alley_May_2024.pdf

- **Hummingbird Place / Valencia Street respite** — 1156 Valencia St. Operated by PRC (Positive Resource Center) and Salvation Army, funded by SFDPH + Tipping Point. ~60 overnight beds. Confirmed via PRC's own site and Tipping Point.
  Source: https://prcsf.org/hummingbird-valencia-opens-in-san-franciscos-mission-district/
  Note: There is also an original "Hummingbird Potrero" site (Baker Places, ~29 beds) — both included separately.

- **SoMa RISE** — 1076 Howard St. San Francisco's first drug sobering/stabilization center, operated by HealthRIGHT 360 with SFDPH oversight. ~20 capacity. Confirmed via sf.gov.
  Source: https://www.sf.gov/soma-rise-center

- **Minna Project** — 447 Minna St. 75-bed transitional housing / dual-diagnosis program for justice-involved adults, partnership of SFDPH + SFAPD + Westside Community Services. Confirmed.
  Source: https://ecbsf.com/projects/447-minna-street

- **Treasure Island step-down program** — HealthRIGHT 360 operates a 70-bed residential stepdown as part of a larger 128-bed Treasure Island behavioral health campus. Confirmed opened 2023; as of most recent reporting found, only ~39 of 70 beds occupied due to staffing shortages (operational detail noted here for later simulation task, not fabricated as a real field).
  Source: https://www.healthright360.org/program/residential-stepdown-men-and-women-treasure-island/

- **SF Behavioral Health Center** — Locked sub-acute / IMD-type facility referenced in SFDPH behavioral health program materials; exact current address/bed count could not be pinned down from a single authoritative public page in the time available. Included in facilities.json with address left partially null — flagged as LOW CONFIDENCE on exact site; may correspond to the 1380 Howard St / Potrero campus behavioral health complex referenced in SFDPH docs.
  Source: https://www.sf.gov/departments--department-public-health--behavioral-health

- **Behavioral Health Access Center (BHAC)**, 1380 Howard St, 1st Floor — Confirmed current entry point for the county behavioral health system-of-care. Drop-in 7 days/week.
  Source: https://www.sf.gov/location--behavioral-health-access-center-bhac

## Hospital psychiatric units — status as of 2026-07-18
- **CPMC (Sutter Health)** — Davies Campus in Duboce Triangle hosts CPMC's adult inpatient psychiatric unit and outpatient clinic (also the psychiatry residency home base). STILL OPEN. Bed count not published in accessible public source — left `null`.
  Source: https://www.sutterhealth.org/education/gme/residencies/cpmc-psychiatry

- **UCSF Langley Porter** — Physically moved from the Parnassus campus (demolished for the new UCSF hospital project) to UCSF Mount Zion Medical Center, reopened there. STILL OPEN, 30 adult inpatient beds (expanded from 22 at the old site). Included as `ucsf-langley-porter-mtzion`.
  Source: https://psych.ucsf.edu/news/langley-porter-psychiatric-hospital-moves-ucsf-mount-zion-medical-center

- **St. Francis Memorial Hospital** — Acquired by UCSF Health (finalized Aug 1, 2024), now operating as "UCSF Health Hyde." STILL HAS a 24-bed locked adult inpatient psychiatric unit at 900 Hyde St per public directory listings. Included as `ucsfh-hyde-stfrancis`.
  Source: https://www.findhelp.org/st.-francis-memorial-hospital--san-francisco-ca--inpatient-psychiatric-care/5150765304512512?postal=94102

- **St. Mary's Medical Center** — Also acquired by UCSF Health (Aug 2024), now "UCSF Health Stanyan Hospital." Public sources describe 35 acute psychiatry beds including the McAuley Adolescent Inpatient Unit — STILL OPEN as of the info found; no confirmed closure. Included as `ucsf-stanyan-mcauley`.
  Source: https://en.wikipedia.org/wiki/St._Mary%27s_Medical_Center_(San_Francisco)

NOTE: Because both Dignity Health hospitals were absorbed into UCSF Health in 2024, and given conflicting older web listings still under "Dignity Health"/"Saint Francis"/"Saint Mary's" branding, verified_date reflects the date this research pass was run (2026-07-18), not a fresh direct-facility confirmation call. Treat bed counts for these two as MODERATE confidence — a full audit would call the facilities directly or check HCAI (hcai.ca.gov) facility licensing data, which was not queried in this pass.

## Facilities that could NOT be fully verified / excluded
- None of the eight named facilities were found to be closed. All were confirmed to have some current public-facing presence. No exclusions were made from the main array on grounds of closure.
- "SF Behavioral Health Center" address/bed count is the single named facility with the lowest confidence — recommend a follow-up direct check of the SFDPH behavioral health services page or a call before using this record for anything beyond a demo placeholder.
