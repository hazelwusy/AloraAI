# AloraAI

Evidence intelligence agent for insurance prior authorization: retrieves clinical
evidence, reasons over it against payer criteria, and synthesizes PA submission
packages — with an emphasis on flagging evidence gaps before submission.

## Contents
- `design/evidence-intelligence-agent.md` — pipeline design, scenario choice, gaps to close.
- `research/dataset-analysis/` — analysis of Synthea synthetic patient data and why
  the long-acting-opioid PA scenario was chosen as the first narrow use case.
- `research/pa-policy-materials/` — real payer/CMS prior authorization policy
  documents used as ground-truth criteria sources.

## Workflow
`main` is protected by convention: no direct commits. All changes go through a
feature branch + pull request.
