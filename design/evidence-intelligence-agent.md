# Evidence Intelligence Agent for Insurance Prior Authorization — Design Notes

## Goal
An agent that retrieves clinical evidence, reasons over it against payer criteria,
and synthesizes a PA submission package — with a focus on **proactively flagging
evidence gaps** (what's missing that would cause a denial), not just auto-filling forms.

## Narrow first scenario
Prior authorization for long-acting opioid analgesic therapy (fentanyl transdermal
patch / ER hydrocodone) for chronic non-cancer pain. Chosen because:
- High real-world PA volume and friction (see `../research/dataset-analysis/`)
- Well-documented, publicly available payer criteria (see `../research/pa-policy-materials/`)
- Clear, checklist-able decision logic (MME thresholds, step-therapy, attestations)
  that's tractable for a v1 rules-plus-LLM approach

## Pipeline
1. **Retrieve** — pull structured evidence from the patient record (diagnosis,
   medication history incl. prior short-acting opioid trials and dates, relevant
   labs/screenings) plus any unstructured notes (LOMN, chart notes).
2. **Reason** — map retrieved evidence against the payer's specific criteria tree
   (e.g. UHC's cancer vs. non-cancer / neuropathic vs. fibromyalgia branches, WA
   HCA's MME tiers). For each criterion: satisfied / not satisfied / evidence
   missing — with the source citation for every claim.
3. **Synthesize** — produce (a) a structured PA request package mapped to the
   payer's submission format, and (b) a gap report: which required elements are
   unsupported or absent, so the provider can fix it *before* submission instead
   of waiting for a denial letter.

## Known gaps to close before this is more than a demo
- **Unstructured evidence**: Synthea has no clinical notes. Need either real
  de-identified notes or LLM-synthesized narratives anchored to the coded FHIR
  facts, otherwise "subjective reasoning" has nothing to reason over.
- **Machine-readable policy rules**: current payer criteria only exist as prose
  PDFs (see `../research/pa-policy-materials/NOTES.md`). First implementation
  task is encoding at least the UHC + WA HCA opioid logic as a structured rule
  set / decision tree the reasoning step can execute against, with citations
  back to the source PDF section.
- **No outcome ground truth**: synthetic patients have no approval/denial label,
  so accuracy can't be measured yet — v1 success criterion should be "does the
  gap report match a manual clinician/coder's read of the same chart," not
  automated accuracy metrics.

## Business angle
Differentiate on **gap detection**, not form-filling — providers already have
PA-automation vendors; the underserved pain point is knowing what's missing
*before* submission. Validate end-to-end on this one opioid scenario before
expanding to other therapy classes.
