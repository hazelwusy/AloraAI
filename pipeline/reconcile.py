"""Deterministic reconciliation differ: compares domain states across two
timepoints. The LLM only extracts per-document state (with quotes); every
changed/conflicting/stale/not_reassessed judgment here is plain code.
"""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional

from .schemas import (
    RECON_DOMAINS,
    DomainState,
    DomainValue,
    ExtractedDomains,
    ReconciliationReport,
)

STALE_AFTER_HOURS = {"vitals": 12}
NOT_REASSESSED_AFTER_HOURS = {"intent_plan": 24, "active_SI": 24}

BANNER = (
    "Several documented domains have changed; {unresolved_list} remain unresolved. "
    "Consider reassessment."
)


def _norm(v: str) -> str:
    return " ".join(v.lower().split())


def _pick(doc: ExtractedDomains, domain: str) -> Optional[DomainValue]:
    for d in doc.domains:
        if d.domain == domain and d.current:
            return d.current
    return None


def reconcile(
    patient_id: str,
    previous_docs: list[ExtractedDomains],
    current_docs: list[ExtractedDomains],
    now: datetime,
    hours_since_previous: float,
) -> ReconciliationReport:
    rows: list[DomainState] = []

    for domain in RECON_DOMAINS:
        prev_vals = [v for doc in previous_docs if (v := _pick(doc, domain))]
        curr_vals = [v for doc in current_docs if (v := _pick(doc, domain))]

        # conflict INSIDE the current timepoint (e.g. nursing vs psychiatry note)
        if len({_norm(v.value) for v in curr_vals}) > 1:
            rows.append(DomainState(
                domain=domain, status="conflicting",
                current=curr_vals[0], previous=curr_vals[1],
                note="same-day sources disagree: " + " vs ".join(f"{v.source}: '{v.value}'" for v in curr_vals),
            ))
            continue

        curr = curr_vals[0] if curr_vals else None
        prev = prev_vals[0] if prev_vals else None

        if curr is None and prev is not None:
            limit = NOT_REASSESSED_AFTER_HOURS.get(domain)
            if limit is not None and hours_since_previous >= limit:
                rows.append(DomainState(
                    domain=domain, status="not_reassessed", previous=prev,
                    note=f"last addressed {hours_since_previous:.0f}h ago; not reassessed since",
                ))
            else:
                rows.append(DomainState(domain=domain, status="unchanged", previous=prev,
                                        note="not addressed in current documents"))
            continue

        if curr is None:
            continue  # never documented anywhere — report nothing, silence is not data

        # clock-based staleness beats value comparison: a "current" value whose
        # own documented time is too old is stale no matter what it says
        stale_limit = STALE_AFTER_HOURS.get(domain)
        age = _hours_old(curr.time, now)
        if stale_limit is not None and age is not None and age > stale_limit:
            rows.append(DomainState(domain=domain, status="stale", current=curr, previous=prev,
                                    note=f"documented {age:.0f}h ago (limit {stale_limit}h)"))
        elif prev is None:
            rows.append(DomainState(domain=domain, status="changed", current=curr,
                                    note="newly documented"))
        elif _norm(curr.value) != _norm(prev.value):
            rows.append(DomainState(domain=domain, status="changed", current=curr, previous=prev))
        else:
            rows.append(DomainState(domain=domain, status="unchanged", current=curr, previous=prev))

    changed = [r.domain for r in rows if r.status == "changed"]
    unresolved = [r.domain for r in rows if r.status in ("conflicting", "stale", "not_reassessed")]
    banner = BANNER.format(unresolved_list=", ".join(unresolved) or "none")
    return ReconciliationReport(patient_id=patient_id, rows=rows,
                                changed=changed, unresolved=unresolved, banner=banner)


def _hours_old(time_str: str, now: datetime) -> Optional[float]:
    for fmt in ("%Y-%m-%dT%H:%M", "%Y-%m-%d %H:%M"):
        try:
            return (now - datetime.strptime(time_str[:16], fmt)) / timedelta(hours=1)
        except ValueError:
            continue
    return None
