"""One small checker per intake requirement. Each returns a ReadinessItem with
met/missing/stale + the evidence string shown to the clinician."""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Callable

from .schemas import ReadinessItem


def _hours_old(time_str: str, now: datetime) -> float | None:
    for fmt in ("%Y-%m-%dT%H:%M", "%Y-%m-%d %H:%M"):
        try:
            return (now - datetime.strptime(time_str[:16], fmt)) / timedelta(hours=1)
        except ValueError:
            continue
    return None


def _presence(field: str, label: str) -> Callable:
    def chk(pf: dict, now: datetime) -> ReadinessItem:
        v = pf.get(field, {})
        if v.get("present"):
            return ReadinessItem(requirement=label, status="met", evidence=v.get("evidence"))
        return ReadinessItem(requirement=label, status="missing")
    return chk


def _fresh(field: str, label: str, max_hours: int) -> Callable:
    def chk(pf: dict, now: datetime) -> ReadinessItem:
        v = pf.get(field, {})
        if not v.get("present"):
            return ReadinessItem(requirement=label, status="missing")
        age = _hours_old(v.get("time", ""), now)
        if age is not None and age > max_hours:
            return ReadinessItem(requirement=label, status="stale",
                                 evidence=f"{v.get('evidence','')} (documented {age:.0f}h ago, limit {max_hours}h)")
        return ReadinessItem(requirement=label, status="met", evidence=v.get("evidence"))
    return chk


FIELD_CHECKS: dict[str, Callable] = {
    "medical_clearance_within_72h": _fresh("medical_clearance", "medical clearance <72h", 72),
    "medical_clearance_within_24h": _fresh("medical_clearance", "medical clearance <24h", 24),
    "vitals_within_12h": _fresh("vitals", "vitals <12h", 12),
    "psych_eval": _presence("psych_eval", "psychiatric evaluation"),
    "risk_assessment_current": _fresh("risk_assessment", "risk assessment <24h", 24),
    "med_rec_signed": _presence("med_rec_signed", "signed med reconciliation"),
    "legal_status_documented": _presence("legal_status", "legal status documented"),
    "voluntary_status": _presence("voluntary", "voluntary status"),
    "tb_screen": _presence("tb_screen", "TB screen"),
    "ambulatory": _presence("ambulatory", "ambulatory"),
    "no_active_violence_risk": _presence("no_violence_risk", "no active violence risk documented"),
    "pregnancy_test_if_applicable": _presence("pregnancy_test", "pregnancy test (if applicable)"),
}


# ---- teammate dataset vocabulary (simulation_params.json / facilities.json) ----
FIELD_CHECKS.update({
    "medical_clearance_24h": _fresh("medical_clearance", "medical clearance <24h", 24),
    "psychiatric_eval_current": _fresh("psych_eval", "psychiatric eval <72h", 72),
    "hold_paperwork_signed": _presence("hold_paperwork", "hold paperwork signed"),
    "med_reconciliation": _presence("med_rec_signed", "medication reconciliation"),
    "insurance_verification": _presence("insurance_verified", "insurance verification"),
    "covid_test_48h": _fresh("covid_test", "COVID test <48h", 48),
    "labs_within_72h": _fresh("labs", "labs <72h", 72),
    "guardian_contact": _presence("guardian_contact", "guardian contact on file"),
})
