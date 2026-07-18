"""Transfer readiness gate: deterministic diff between what the patient record
documents and what each facility's intake requires. LLM extracts patient-side
fields once; this module is pure code so facility A vs B comparisons are
reproducible and explainable."""
from __future__ import annotations

from datetime import datetime

from .readiness_fields import FIELD_CHECKS
from .schemas import ReadinessItem, ReadinessReport


def check(facility: dict, patient_fields: dict, now: datetime) -> ReadinessReport:
    """patient_fields: {"medical_clearance": {"present": true, "time": "...", "evidence": "..."}, ...}"""
    items: list[ReadinessItem] = []
    for req in facility.get("intake_requirements", []):
        checker = FIELD_CHECKS.get(req)
        if checker is None:
            items.append(ReadinessItem(requirement=req, status="missing",
                                       evidence="no checker defined — flag for manual review"))
            continue
        items.append(checker(patient_fields, now))
    return ReadinessReport(facility_id=facility["id"],
                           ready=all(i.status == "met" for i in items),
                           items=items)
