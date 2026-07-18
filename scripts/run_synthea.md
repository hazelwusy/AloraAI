# Synthea run notes

## Update (2026-07-18, second pass): actually run
Java became available in this environment (installed Temurin 17 locally, no
Homebrew/sudo required — see below), so Synthea was run for real to expand the
patient set beyond the original 5 hand-authored patients (maria, patient_002..005).

```bash
# Java 17 install used (no sudo, no Homebrew needed):
curl -sL -o temurin17.tar.gz \
  "https://api.adoptium.net/v3/binary/latest/17/ga/mac/aarch64/jdk/hotspot/normal/eclipse"
mkdir -p ~/.local/java && tar xzf temurin17.tar.gz -C ~/.local/java
export JAVA_HOME=~/.local/java/jdk-17.0.19+10/Contents/Home
export PATH=$JAVA_HOME/bin:$PATH

cd ~/Desktop/synthea
./gradlew build -x test -x check   # first-time build, ~2 min
./run_synthea -p 400 California    # generated 400 living patients
```

Output landed in `~/Desktop/synthea/output/fhir/*.json` (448 bundles, 400
alive). Scanned every bundle's `Condition` resources for behavioral-health-
relevant keywords (suicid*, self-harm, major depressive, schizo*, bipolar,
homeless, psychiatric, PTSD, housing instability) — 63 bundles matched
something, most just a generic "unhealthy alcohol drinking behavior" screening
finding. Narrowed to 5 with genuinely rich behavioral-health content (major
depressive disorder, severe anxiety/panic, homelessness, dependent drug abuse)
and used those as structural skeletons for **patient_006 through patient_010**
— see each patient's `../data/patients/patient_0XX/raw_synthea_skeleton/` for
the raw FHIR bundle Synthea produced, and `demographics.json` for the derived
fields (age/gender/med list read from the skeleton; housing_status/emergency
contact/notes hand-authored on top, same process as the first 5 patients).

## Original note (first pass): why it was skipped initially
No Java runtime was available in the environment used for the first 5
patients, so demographics were hand-authored from scratch instead of derived
from a Synthea run. That's still true for maria/patient_002..005 — only
patient_006-010 have a real generated skeleton underneath.

## Re-running / extending further
```bash
cd ~/Desktop/synthea
export JAVA_HOME=~/.local/java/jdk-17.0.19+10/Contents/Home   # if already installed
export PATH=$JAVA_HOME/bin:$PATH
./run_synthea -p 400 California
python3 -c "
import json, glob
KEYWORDS = ['suicid','self-harm','major depressive','schizo','bipolar','homeless',
    'psychiatric','post-traumatic','ptsd','housing instability']
for f in glob.glob('output/fhir/*.json'):
    d = json.load(open(f))
    conds = {r['resource'].get('code',{}).get('text','').lower()
             for r in d.get('entry',[]) if r['resource'].get('resourceType')=='Condition'}
    hit = [c for c in conds if any(k in c for k in KEYWORDS) and c]
    if hit: print(f, hit)
"
```
