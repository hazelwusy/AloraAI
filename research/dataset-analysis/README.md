# Synthea Dataset Analysis — Narrow Scenario Selection

Source: [synthetichealth/synthea](https://github.com/synthetichealth/synthea), three
pre-generated FHIR sample sets under `synthea-*-sample/fhir/` (24 synthetic patients
total across gynecology, chronic_pain, psychiatry groups). Analyzed with
`inspect_groups.py`.

## Why "chronic pain" (opioid PA) was chosen as the narrow scenario

Looking at actual coded content (not just folder names):

- **`chronic_pain/` folder** is dominated by noise from one CKD patient on renal
  dialysis (831 dialysis procedures) — comorbidity data, not pain-management-specific
  evidence. Not a clean scenario on its own.
- **`psychiatry/` folder** unexpectedly contains the clearest opioid therapy signal:
  patients on `72 HR Fentanyl 0.025 MG/HR Transdermal System` (12 refills) and
  `12 HR Hydrocodone Bitartrate 10 MG Extended-Release` (12 refills) — a real
  long-acting-opioid regimen, which is one of the best-documented, highest-volume
  real-world PA categories (clear MME thresholds, step-therapy rules, published
  payer criteria — see `../pa-policy-materials/`).
- **`gynecology/` folder** is mostly normal pregnancy care — low PA-friction, poor
  fit for a first proof of concept.

**Decision: narrow scenario = Prior Authorization for long-acting opioid analgesic
therapy** (fentanyl transdermal patch / extended-release hydrocodone), using the
opioid-prescribed patients found in the psychiatry sample set as the clinical
evidence source, matched against the real payer criteria in
`../pa-policy-materials/`.

## Known dataset limitations (apply to all three groups)

1. No unstructured clinical text (progress notes, letters of medical necessity) —
   only coded FHIR resources (Condition/Procedure/MedicationRequest/Observation).
   A PA agent's "subjective reasoning" step needs narrative evidence; this must be
   synthesized separately (e.g., LLM-generated notes anchored to the coded facts)
   or replaced with real de-identified notes.
2. No payer-side data (policy criteria, PA approval/denial outcomes) — sourced
   externally, see `../pa-policy-materials/`.
3. Small sample (24 patients, synthetic generation rules, no approval/denial
   ground truth) — fine for pipeline prototyping, not for accuracy evaluation.

## Files
- `inspect_groups.py` — script used to produce the per-patient resource-count
  summaries referenced above.
- `synthea-psychiatry-sample/`, `synthea-chronic-pain-sample/`,
  `synthea-gynecology-sample/` — the raw FHIR bundles as generated.
