# Real Prior Authorization Policy Materials — Long-Acting Opioid PA

Collected 2026-07-18. These are real, publicly available payer/CMS policy documents
used as ground-truth criteria sources for the opioid PA evidence-intelligence agent
prototype.

## Files

- `uhc_long_acting_opioids.pdf` — UnitedHealthcare Commercial, Program Number 2025 P 2014-30,
  effective 1/17/2026. Full step-therapy / medical-necessity decision logic for fentanyl
  transdermal patch, ER hydrocodone, methadone, MS Contin, Nucynta ER, OxyContin, etc.
  Splits criteria by cancer/end-of-life vs. non-cancer chronic pain, and by
  neuropathic/fibromyalgia sub-populations.
- `cms_prescribers_guide.pdf` — CMS MLN2886155, "A Prescriber's Guide to Medicare
  Part D Opioid Policies." Defines the 7-day acute-supply limit for opioid-naive
  patients and the 90 MME/day pharmacy safety edit that triggers prescriber consultation.
- `wa_hca_opioid_policy.pdf` — Washington State HCA Medical Policy No. 65.10.00
  (Apple Health/Medicaid), last updated 09/11/2023. Concrete MME thresholds and
  attestation requirements for chronic non-cancer pain.

## Key extracted criteria (for agent rule design)

### UnitedHealthcare — non-cancer chronic pain, initial authorization (ALL required)
1. Prescriber attests: patient screened for substance abuse/opioid dependence, AND
   pain is moderate-to-severe and expected to be chronic.
2. Documented treatment goals + estimated duration of treatment.
3. Patient screened for underlying depression/anxiety (addressed if present).
4. One of:
   - Non-neuropathic pain: failed adequate ≥4-week trial of a short-acting opioid
     (or new-to-plan patient already established on the long-acting drug), OR
   - Neuropathic pain: failed 8-week gabapentin trial AND 6-week TCA trial, OR
   - Fibromyalgia: chart notes showing established benefit from opioid therapy.
- Approval duration: 24 months (cancer/EOL) once criteria met.

### Washington HCA — MME thresholds (Medicaid)
- ≤120 MME/day: standard chronic-pain criteria (attestation form, non-opioid
  therapies tried/ineffective, ≥42 days of short-acting trial or clinical justification).
- 120–200 MME/day: requires pain management specialist consultation.
- >200 MME/day: case-by-case medical necessity review, chart notes + specialist
  consult required.
- Acute pain (non-chronic): ≤42 days supply within a rolling 90-day window before
  it's reclassified as "chronic use" requiring PA.

### CMS Part D (Medicare)
- First-time opioid fill for acute pain: max 7-day supply for opioid-naive patients.
- Cumulative >90 MME/day triggers a pharmacy point-of-sale safety edit requiring
  prescriber consultation/override.

## Gap vs. what a production agent needs
These are commercial/Medicaid/Medicare *policy text* — they give the decision logic,
but a real PA agent still needs, per request:
- Structured patient-side evidence (diagnosis, prior therapy trial dates/outcomes,
  PDMP/UDS results, functional pain scores) — none of this exists in Synthea's
  coded output; would need synthetic clinical notes layered on top (see
  `../dataset-analysis/README.md`).
- A machine-readable rule representation of the above (currently prose PDFs) —
  first implementation task for the reasoning layer.
- The actual submission form/schema per payer (UHC's dam-hosted PDF didn't include
  a fillable form; CMS's model Coverage Determination Request form is the closest
  generic template — worth pulling separately if the demo needs an output artifact).
