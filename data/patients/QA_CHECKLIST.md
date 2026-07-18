# QA Checklist — Embedded Findings Traceability

Compliance note: all patients below are synthetic. No real patient data was used.
Patients 006-010 use Synthea-generated structural skeletons (demographics,
conditions, medications — see each patient's `raw_synthea_skeleton/`) as a
realism anchor, with hand-authored clinical notes layered on top, same as
maria/002-005. Synthea's own generation is itself fully synthetic (no real
patient data), consistent with the compliance requirement.

## maria — 7 embedded findings (per task spec)

1. **Missing signature on hold paperwork**
   File: `maria/notes/day0_psych_eval.txt`
   Sentence: "HOLD STATUS: Patient is on an involuntary hold initiated in the ED
   this evening given danger to self."
   Verification: No note in maria's set (ED transcript, psych eval, nursing note,
   SW note, day2 transcript) ever mentions a physician signature, co-signature, or
   completed hold form — the hold is referenced as clinically in effect but the
   paperwork step is never confirmed as completed. Confirmed nowhere does any note
   say "signature missing" — the gap is an absence, not a stated defect.

2. **Copy-forward (day1 nursing note repeats day0 psych eval language verbatim)**
   Files: `maria/notes/day0_psych_eval.txt` vs `maria/notes/day1_nursing_note.txt`
   Repeated verbatim phrases: "Alert, oriented x4.", "No evidence of thought
   disorder or delusional content.", "Thought process linear."
   Verification: confirmed these three phrases appear identically in both files;
   day1 note additionally contains genuinely new nursing-shift content (no PRN,
   improved appetite, uneventful overnight) around the copied phrases.

3. **Negation + time-limited qualifier ("today")**
   File: `maria/notes/day2_psych_transcript.txt`
   Sentence: "Dice que no, hoy no tiene esos pensamientos." (translation embedded
   in transcript: denies SI *today*, in response to a question also scoped to
   "today")
   Verification: confirmed the denial is explicitly scoped to the present day
   only, not a general risk reassessment.

4. **si_intent not reassessed since day0**
   Files: all notes after `day0_psych_eval.txt`
   Verification: day0_psych_eval is the only note documenting the specific plan
   (Golden Gate Bridge) and intent. Day2 transcript only asks a generic "thoughts
   of wanting to hurt yourself today" — the specific plan/intent from day0 is
   never revisited or re-assessed in any subsequent note.

5. **Collateral support unchanged/unresolved**
   File: `maria/notes/day2_sw_note.txt`
   Sentence: "Sister... reiterated what she told the RN in the ED: she does not
   have space for Maria to stay with her right now... She is willing to visit and
   stay in phone contact but cannot offer housing or in-person supervision at
   discharge."
   Verification: confirmed this directly parallels the ED-era collateral info in
   `day0_ed_transcript.txt`/`day0_psych_eval.txt` (sister present, no housing
   offered) — no change in collateral support despite patient's improved
   presentation, creating deliberate tension for the state-reconciliation demo.

6. **Psychosis domain unchanged**
   Files: `day0_psych_eval.txt` ("No auditory or visual hallucinations elicited on
   exam. No evidence of thought disorder or delusional content.") vs
   `day2_psych_transcript.txt` ("No, dice que no escucha ni ve nada raro.")
   Verification: both notes independently document absence of psychotic symptoms;
   domain is stable/unchanged across the admission, not flagged as new or resolved
   since there was nothing to resolve.

7. **Stale vitals**
   File: `maria/notes/day1_nursing_note.txt`
   Sentence: "Slept in intervals, awake for vitals at 0400 without difficulty
   returning to sleep."
   Verification: this is the last vitals timestamp anywhere in maria's record
   (2026-07-11 04:00). No vitals are recorded in `day2_sw_note.txt` or
   `day2_psych_transcript.txt` (2026-07-12, 09:50 and 13:05) — by the time of the
   day2 notes, last recorded vitals are >12 hours stale.

## patient_002 — deterioration trajectory

**Embedded finding: worsening psychosis + new command hallucinations + med refusal**
Files: `patient_002/notes/day0_psych_eval.txt` vs `patient_002/notes/day2_psych_eval.txt`
- Day0: "endorses hearing 'a voice, sometimes, telling me things' but denies it is
  commanding him to do anything right now, and denies it is bothersome."
- Day2: "the voice is 'telling me to hit the wall so it'll stop,' which he
  describes as distressing and difficult to ignore — a change from his
  description two days ago of a voice that was present but not commanding or
  bothersome."
Verification: day2 note explicitly cross-references and contrasts with day0
(non-commanding → commanding), plus new medication refusal and increased
psychomotor agitation/tangentiality — a clear directional change in the
psychosis domain (not just "changed," but worsened), confirming the system
must be able to detect degradation, not just resolution.

## patient_003 — conflicting same-day, same-domain observations

**Embedded finding: nursing vs. psychiatry conflict on the same calendar day**
Files: `patient_003/notes/day1_nursing_note.txt` (2026-07-15 09:00) vs
`patient_003/notes/day1_psych_eval.txt` (2026-07-15 13:15)
- Nursing: "Patient calm and cooperative this morning... engaged appropriately
  with peers."
- Psychiatry (4 hours later, same day): "Guarded throughout the interview...
  Irritable in manner... required verbal de-escalation once."
Verification: both notes are dated the same calendar day with different
timestamps, describing the affect/behavior domain in materially conflicting
terms from two different roles — this is a same-period conflicting-source
finding, distinct from maria's cross-time-point "changed" findings.

## patient_004 — fully ready (control case, all-green)

Verification: `day2_psych_eval.txt` explicitly documents current medical
clearance, vitals recorded same morning (07:30, note dated 10:30 — well under
12h), no active risk, current psychiatric eval, confirmed supportive collateral,
completed med reconciliation, and completed insurance verification — every
readiness field a diff against a facility's intake_requirements would check is
addressed and current, with no missing or stale items. Included as a contrast
case so the demo can show the system correctly reporting "no gaps" rather than
always finding something wrong.

## patient_005 — stable (control case, no findings)

Verification: `day1_psych_followup.txt` mirrors `day0_psych_eval.txt` across every
domain (mood, affect, thought process/content, risk, collateral/home situation)
with explicit "same as last visit" / "no change" language and no new information
introduced. Included so the demo can show the system correctly does NOT flag a
"changed" or "conflicting" finding when nothing has actually changed — i.e., it
doesn't over-trigger on a stable patient.

## Clinical plausibility self-check (maria)
- Medication/PRN use: no PRN medication given per nursing note despite admission
  agitation — consistent with agitation resolving overnight without pharmacologic
  intervention; plausible, not contradicted elsewhere.
- MSE terminology used correctly (thought process/content, insight, judgment
  distinguished).
- Timeline consistency: day1 note does not reference day2 events; day2 notes do
  not contradict day0/day1 chronology. Hold documented day0, sister collateral
  contacted day0 and re-confirmed day2, consistent throughout.
- Language style: ED/psych transcripts are conversational with interpreter relay
  markup; psych eval, nursing, and SW notes use clinical documentation register.
  No mixing of styles within a single file.
- No real PII: patient and collateral names are common placeholder first names,
  explicitly marked "(synthetic)" in demographics.json; no real facility staff
  names, only generic clinician surnames.

## Clinical plausibility / language / PII check — patients 002-005

- **patient_002**: risperidone restart plausible for schizoaffective decompensation
  from non-adherence; symptom progression (non-commanding → commanding
  hallucination, med refusal, increased psychomotor agitation) is an internally
  consistent worsening arc, not a random flip. Timeline consistent (day2 doesn't
  reference future events).
- **patient_003**: no medications documented (deliberately, given limited
  engagement/guardedness in the eval) — plausible for a patient who has not yet
  had a full assessment; conflicting notes both use correct discipline-specific
  language (nursing = behavioral observation, psychiatry = MSE terminology).
- **patient_004**: med reconciliation (continuing home escitalopram/quetiapine
  with a dose increase) and rapid stabilization are plausible for moderate MDD
  with strong protective factors and family support; explicitly voluntary
  admission, consistent with lower acuity than maria/patient_002.
- **patient_005**: outpatient-only scenario (no ED/hold) is intentionally the
  lowest-acuity patient in the set; language throughout is clinical register only
  (no transcript-style content, consistent with never having an ED encounter).
- All four: no real names, no real facility-external identifiers; clinician
  surnames are generic/common, distinct per patient to avoid implying a shared
  real practice.

## patient_006 — conflicting substance-use report (Synthea-anchored)

Files: `patient_006/notes/day0_ed_intake.txt` vs `day0_psych_consult.txt`
- ED (08:40): "Denies current alcohol use when asked directly — states 'I
  don't drink anymore.'"
- Psychiatry (11:15, same day): "reports drinking 'most days, to help me
  sleep,' estimates several drinks per evening... at odds with what patient
  told the ED team this morning."
Verification: same-day, different sources, directly conflicting substance-use
domain — a second conflicting-source example distinct from patient_003's
affect/behavior conflict, testing whether the system generalizes conflict
detection across domains.

## patient_007 — long-interval not_reassessed (Synthea-anchored)

Files: `day0_outreach_contact.txt` (2026-07-01) vs `day1_outreach_contact.txt`
(2026-07-15, 2 weeks later)
- Day0: "Last full risk/needs assessment on file is from several outreach
  contacts ago; patient has been consistently declined to sit for a full
  reassessment."
- Day1: "still declining shelter placement and a full reassessment."
Verification: explicitly documents an assessment gap spanning weeks, not
hours/days like maria's — tests the system's `stale`/`not_reassessed`
detection at a longer time scale, and confirms it shouldn't require an acute
encounter to flag a gap.

## patient_008 — negation + time-qualifier in a different domain (Synthea-anchored)

File: `day0_ed_transcript.txt`
Sentence: "DR. VARGAS: Any thoughts of hurting yourself right now, tonight?
PATIENT: No, not tonight. I just want this feeling to stop."
Verification: same negation+temporal-qualifier pattern as maria's day2, but
in an acute panic-attack context rather than a post-overdose follow-up —
tests that the finding generalizes beyond one specific clinical scenario.

## patient_009 — absent (not just unchanged) collateral (Synthea-anchored)

Files: `day0_psych_eval.txt` vs `day2_sw_note.txt`
Both independently document: "no family or friends he wants contacted... no
collateral contact has been identified." This is a distinct variant from
maria's (collateral exists but can't help) — here there is no collateral
contact at all, tested across two different note authors/days to confirm
consistency rather than an isolated statement.

## patient_010 — self-reported stale vitals (Synthea-anchored)

File: `day1_nursing_note.txt`
Sentence: "No new vitals recorded this shift yet... last full set remains
from admission yesterday morning."
Verification: unlike maria's fully implicit stale-vitals gap (never stated,
only inferable from timestamps), this note has the nurse explicitly name the
gap — a deliberately more visible variant, useful for confirming the system
catches both the subtle and the stated version of the same finding type.

## Compliance note on Synthea-anchored patients (006-010)
Demographics (age/gender) and background conditions/medications for these
five were read directly from real Synthea output (`raw_synthea_skeleton/`,
generated by a California population run — see `../../scripts/run_synthea.md`
for the run command). Housing status, emergency contact, and all note content
were then hand-authored to fit the embedded-finding spec; no field was
invented to look like real (non-synthetic, non-Synthea) source data.
