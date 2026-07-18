"""SFDPH facility source notes / process record.

NOT a runnable scraper. SFDPH's residential care & treatment facility lists were
found only as (a) a Tableau-embedded interactive dashboard at
sf.gov/residential-care-and-treatment, not scrapeable without a browser
automation layer, and (b) PDFs (BHSA Integrated Plan FY2026-29 draft,
Residential Care and Treatment Working Group Final Report Jan 2025) that
returned raw binary/unparseable content to automated fetch tools in this pass.

What was actually done: manual identification and verification of named SFDPH
facilities (ZSFG PES, Dore Urgent Care, Hummingbird Place, SoMa RISE, Minna
Project, Treasure Island stepdown, SF Behavioral Health Center, Behavioral
Health Access Center) via their own public pages and sf.gov listings, recorded
in data/facilities_raw/manual/named_facilities_verification.md and merged into
data/facilities.json by hand (data_source includes "manual" and/or "sfdph"
context in facilities_collection_notes.md).

## If re-attempting
- Try a PDF text extraction library (e.g. pypdf, as used in this project's
  earlier PA-research session) directly on the BHSA Integrated Plan / Working
  Group Report PDFs once located, rather than WebFetch's HTML-conversion path,
  which failed on these documents.
- For the Tableau dashboard, would need a headless-browser approach (e.g.
  claude-in-chrome or Selenium) rather than a plain HTTP fetch.
"""
