# AloraAI — SF Behavioral Health Transition Orchestration Agent: Dataset

> **All patient data is synthetic.** Facility directory is from public sources;
> availability, intake requirements detail, and response behavior are
> simulated for demonstration.

This repo currently contains only the **dataset** for an agent that would help
orchestrate patient transitions between levels of behavioral-health care in San
Francisco. No agent/UI code is included yet — this is the working material for
that downstream build.

## Workflow
`main` is protected by convention: no direct commits. All changes go through a
feature branch + pull request.

## What the downstream agent does with this data
1. **State Reconciliation** — reads a patient's longitudinal notes, extracts
   domain-level status (active SI, psychosis, agitation, collateral support,
   legal/hold status, etc.), each claim traceable to a verbatim quote + source
   + timestamp, then diffs across time points to flag `changed` /
   `conflicting` / `stale` / `not_reassessed`.
2. **Transfer Readiness + Packet** — diffs a patient's readiness data against a
   target facility's `intake_requirements`, flags missing/stale items, and
   drafts a facility-specific referral packet.
3. **Decline Intelligence** — simulates a facility's structured decline reason
   for a referral, using each facility's `simulated.decline_behavior`.

## Directory map
```
data/
  facilities.json              74 SF-area behavioral health facilities
  facilities_raw/               raw source notes per collection method
  facilities_collection_notes.md  what's real, what's a gap, verification log
  simulation_params.json        documented basis for every simulated parameter
  patients/
    maria/ patient_002../010/    10 synthetic patients total
      demographics.json
      notes/*.txt
      raw_synthea_skeleton/      (patient_006-010 only — real Synthea FHIR bundle)
    QA_CHECKLIST.md             every embedded finding traced to source text
scripts/
  scrape_sfdph.py, fetch_samhsa.py   process notes (not runnable — see files)
  merge_facilities.py           schema validation, safe to re-run
  generate_availability.py      (re)generates the `simulated` block, idempotent
  run_synthea.md                actual Synthea run log + how to extend further
  generate_patients.py          prompt template + trajectory spec for notes
```

## Real vs. simulated — the boundary
Every facility record's structural fields (name, address, level_of_care,
payers, languages, `source_url`) come from a real public source — SFDPH
sf.gov pages, facility/operator websites, or general web research, each cited.
The `simulated: {}` block on every facility (bed availability, wait days,
intake requirement subset, decline behavior) is synthetic and documented in
`data/simulation_params.json` with the reasoning behind each range — **never**
treat these as live data.

Patient data is 100% synthetic: no real patient records, MIMIC-style datasets,
or scraped case reports were used anywhere in this repo. patient_006-010 use a
real Synthea-generated structural skeleton (demographics/conditions/meds,
itself fully synthetic) layered with hand-authored notes; maria/002-005 are
entirely hand-authored (Synthea wasn't available yet in that pass).

## Facility knowledge-graph monitoring (`pipeline/monitor.py`)
A HITL update loop over the real facility/edge data: (simulated) fetchers
propose changes to `data/facilities.json` or `data/edges_directory.json`
(a real-id edge set for the knowledge graph — separate from the legacy
`data/edges.json`, which pairs with `facilities_demo.json` and backs the
original network-map view); nothing is applied until a human approves it via
`/api/monitor/approve/{id}`, at which point it's written into the graph and
logged to `data/monitoring/version_history.json`.

Researched OpenBeds / California's own effort (DHCS RFI 25-071, "Bed Capacity
Data Solution") before building this: neither has a public API today — CA's
system is still at the RFI stage (due Feb 2026) — so the three fetchers
(`web`, `phone_call`, `ehr_feed` source types) are explicitly simulated,
producing example proposals rather than real crawls/calls/feed polls. See
`pipeline/monitor.py`'s docstring for what a real implementation would swap
in per source type.

## Known gaps (see data/facilities_collection_notes.md for full detail)
- SFDPH's richest bed-count PDFs (BHSA Integrated Plan, Residential Care and
  Treatment Working Group Report) were located but not text-extractable in
  this pass.
- SAMHSA's findtreatment.gov has no public bulk export; SAMHSA-tagged records
  were built from general knowledge and then individually re-verified — 8 of
  17 have confirmed street addresses and org-specific source URLs, the
  remaining 9 (out-of-county fallback facilities) remain city-level/lower
  confidence by design, not fabricated.
- No live DataSF psychiatric-bed-occupancy dataset was found; occupancy
  assumptions in `simulation_params.json` are documented estimates, not pulled
  data.

## Re-running
```bash
pip install -r requirements.txt
python3 scripts/merge_facilities.py        # validates data/facilities.json
python3 scripts/generate_availability.py   # regenerates the simulated{} block
```
