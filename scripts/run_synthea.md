# Synthea run notes

Attempted to use the existing `~/Desktop/synthea` checkout to generate a California
population with behavioral-health modules enabled, then select 5 patients with a
psychiatric encounter for demographic/med-list realism.

**Result: skipped.** No Java runtime available in this environment
(`java -version` → "Unable to locate a Java Runtime"), and no pre-built jar under
`build/libs`. Per project scope, Synthea is a nice-to-have for structural/med-list
realism, not a dependency — demographics for the 5 patients were hand-authored
instead (see `../data/patients/*/demographics.json`), matching the shape Synthea
would have produced (age, gender, insurance, language, housing_status, emergency
contact) but without a generated FHIR/CSV skeleton underneath.

## If re-attempting with Java available
```bash
cd ~/Desktop/synthea
./gradlew build check test          # first-time build
./run_synthea -p 200 California      # small population run
# then filter output/fhir/*.json for bundles containing a psychiatric Condition/Encounter
# (see ~/Desktop/synthea/inspect_groups.py in an earlier session for a resourceType
# tally script that can be adapted for this filter)
```
