"""Run the Domain Extractor over a patient's document folder and reconcile."""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from . import llm
from .reconcile import reconcile
from .schemas import ExtractedDomains, ReconciliationReport

DATA = Path(__file__).parent.parent / "data"


def extract_doc(name: str, text: str) -> ExtractedDomains:
    return llm.call_json(
        llm.load_prompt("domain_extractor"),
        f"document name: {name}\n\n{text}",
        ExtractedDomains,
        max_tokens=4096,
    )


def reconcile_patient(patient_id: str = "maria") -> ReconciliationReport:
    folder = DATA / "patients" / patient_id
    prev_docs = [extract_doc(p.name, p.read_text()) for p in sorted(folder.glob("day0_*.md"))]
    curr_docs = [extract_doc(p.name, p.read_text()) for p in sorted(folder.glob("day2_*.md"))]
    report = reconcile(
        patient_id=patient_id,
        previous_docs=prev_docs,
        current_docs=curr_docs,
        now=datetime(2026, 7, 18, 10, 0),      # demo clock: day 2, 10:00
        hours_since_previous=36.0,
    )
    out = Path("out") / f"{patient_id}_recon.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(report.model_dump_json(indent=1))
    return report
