"""Patient clinical narrative generation — process record + reusable prompt.

NOT a runnable script in this session (notes were authored directly, not via an
API call) but this documents the generation approach and the prompt template so
it's reproducible with an actual LLM call if regenerating or extending the
patient set.

## Approach
1. Hand-author demographics.json per patient (age, gender, insurance, language,
   housing_status, emergency_contact) — see data/patients/*/demographics.json.
   housing_status is not a Synthea field; injected manually per spec (at least
   2 of 5 patients unhoused: maria, patient_003).
2. For each patient, write a small set of notes (ED transcript and/or psych
   eval/follow-up and/or nursing/SW notes) per the trajectory below, embedding
   specific "findings" the downstream state-reconciliation agent should be able
   to detect — WITHOUT stating the finding outright (e.g. never write "signature
   missing"; instead simply never mention a signature at all).

## Patient trajectories (see data/patients/QA_CHECKLIST.md for full traceability)
- maria: improving-but-unresolved, 5 notes, 7 embedded findings (missing hold
  signature, copy-forward nursing note, negation+"today"-qualified SI denial,
  si_intent never reassessed after day0, collateral support unchanged/unresolved,
  psychosis domain unchanged, stale vitals >12h).
- patient_002: deterioration (non-commanding → commanding hallucinations, new
  medication refusal) — proves the system detects worsening, not just improving.
- patient_003: same-day conflicting observations between nursing and psychiatry.
- patient_004: fully ready/all-green control case.
- patient_005: stable/no-change control case — proves the system doesn't
  over-trigger on a patient where nothing changed.

## Prompt template used (for reproducing/extending with an actual LLM call)
```
You are writing a single synthetic clinical note for a fictional patient in a
demo dataset. This is NOT real patient data.

Note type: {note_type}  (e.g. "ED physician-patient transcript with interpreter",
  "psychiatry initial evaluation with MSE", "nursing shift assessment",
  "social work note")
Patient context: {demographics + prior notes in this patient's timeline}
Required embedded finding(s), to be shown NOT told: {finding_description}
  e.g. "the hold paperwork should be referenced as in effect but no signature
  or co-signature should ever be mentioned in this note or any other note for
  this patient — do not write the words 'signature' or 'missing'."

Constraints:
- Use correct clinical documentation register for note-type notes; use natural
  spoken language + interpreter-relay markup for transcripts. Do not mix styles.
- No real names — use common placeholder first names only, mark synthetic in
  demographics.
- Keep the finding embedded in ordinary clinical narrative — a clinician
  reading it should notice something is "off" only on careful review, not on
  a skim.
```

## Post-generation QA (required, see data/patients/QA_CHECKLIST.md)
Every embedded finding was traced back to its exact source sentence and
verified it wasn't accidentally stated outright or accidentally resolved by a
later note.
"""
