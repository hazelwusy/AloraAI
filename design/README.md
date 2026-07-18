# Design prototype

`prototype.html` is a self-contained, static visual prototype of the transition
coordination UI (Census → Reconcile → Readiness → Packet → Track → Aftercare),
wired to the same patient set as `../data/patients/` (maria, patient_002-005 at
time of writing — patient_006-010 from PR #4 aren't reflected here yet) and
referencing real facilities from `../data/facilities.json` (e.g. Hummingbird
Place, Valencia).

This is separate from `web/index.html` on `feat/transition-packet-skeleton`,
which is the actual functional app wired to a FastAPI backend. This file is a
design/pitch reference only — no backend, all interactions are simulated
client-side JS. Before the demo, someone should decide whether this design
gets merged into the functional UI, or the functional UI adopts this visual
language, rather than keeping two separate front ends.

Open directly in a browser — no build step, no dependencies.
