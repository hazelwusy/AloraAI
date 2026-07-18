# AloraAI — Care-Transition Packet Agent

> "I have read everything your doctors sent over, but **paper never tells it right**."
> — hospice physician, encounter `25fb1227…`, official hackathon dataset

When a patient moves between care settings (hospital → SNF, hospital → hospice),
the receiving clinician gets a thin transfer summary and spends the first visit
re-eliciting everything: med lists read aloud line by line, allergies
double-checked "because I want them exactly right", goals of care re-asked from
scratch. XFERALL digitized how transfer documents *travel*; nobody fixed what's
*in* them.

AloraAI generates the transfer packet from the richest source that exists — the
ambient conversation plus the FHIR record — with **every claim citing the exact
words a human actually said**. The clinician reviews and signs; the agent does
the follow-through.

## Pipeline

```
transcript + note + FHIR (per encounter)
        │
        ▼
[Agent A · Context Miner]        extracts transferable facts: meds, allergies,
        │                        functional status, risk flags, goals-of-care
        │                        (verbatim), caregiver tasks — each with a span
        ▼
[Grounding Verifier]             deterministic: every claim's span must exist in
        │                        the source text, or the claim is dropped.
        ▼                        Not a prompt. A gate.
[Agent B · Packet Composer]      assembles the receiving-facility packet:
        │                        one-liner, med reconciliation table, allergy
        │                        banner, mobility/functional baseline, risks,
        ▼                        goals-of-care in the patient's own words
[Agent C · Gap Checker]          plays the receiving intake coordinator: what
        │                        would I still have to ask? → auto-drafted
        ▼                        questions back to the sender
[Sign-off queue]                 clinician approves / edits / overrides (logged)
```

## Repo layout (this branch)

| Path | What it is |
|---|---|
| `pipeline/` | Python agent pipeline (runnable CLI, no server needed) |
| `pipeline/prompts/` | Agent prompts as versioned markdown |
| `pipeline/grounding.py` | Deterministic span verifier — fully implemented |
| `pipeline/eval.py` | Runs all 6 transition encounters; grounding + coverage stats |
| `server/` | FastAPI wrapper for the demo UI |
| `web/` | Next.js demo UI (see `web/README.md` to scaffold) |
| `docs/DEMO_SCRIPT.md` | 3-minute live-demo storyboard |

## Quickstart

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env         # add your ANTHROPIC_API_KEY

# point at the official dataset (or copy it into ./data)
export DATASET=/path/to/synthetic-ambient-fhir-25/synthetic-ambient-fhir-25.jsonl

python -m pipeline.run_pipeline --list                 # show the 6 transition encounters
python -m pipeline.run_pipeline --id <encounter_id>    # run one, writes out/packets/<id>.json
python -m pipeline.eval                                # run all, print grounding stats
uvicorn server.main:app --reload                       # API for the web UI
```

## Hackathon compliance

- All code in this branch written during the hackathon (2026-07-18).
- Input data: the official Abridge synthetic dataset (25 encounters); no real
  patient data anywhere.
- Open source, MIT.
