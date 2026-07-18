"""The learning loop: every placement call teaches the system two things.

1. FACILITY MEMORY — what each facility's intake actually asks, declines on,
   and accepts conditionally. Injected into the next call to that facility (and,
   aggregated, into calls to same-level facilities) so the agent preempts
   instead of getting caught.

2. PATIENT GAP LOG — every question a packet couldn't answer is a *known
   unknown* about the patient. Aggregated per patient, deduped, surfaced to the
   nurse as a pre-call gather-list and injected into the next packet build.

Plain JSON on disk; no model training. The 'learning' is prompt-side context
accumulation — auditable, resettable, and it demos in two calls.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from .schemas import CallResult

LEARN_DIR = Path("out") / "learning"
FACILITY_MEM = LEARN_DIR / "facility_memory.json"
PATIENT_GAPS = LEARN_DIR / "patient_gaps.json"


def _load(path: Path) -> dict:
    return json.loads(path.read_text()) if path.exists() else {}


def _save(path: Path, data: dict) -> None:
    LEARN_DIR.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=1))


def record_call(patient_id: str, result: CallResult) -> None:
    """Update both memories from a finished call."""
    mem = _load(FACILITY_MEM)
    entry = mem.setdefault(result.facility_id, {
        "questions_asked": [], "decline_reasons": [], "conditions": [], "calls": 0})
    entry["calls"] += 1
    for q in result.outcome.questions_asked_by_intake:
        if q not in entry["questions_asked"]:
            entry["questions_asked"].append(q)
    if result.outcome.outcome == "declined":
        entry["decline_reasons"].append(
            {"category": result.outcome.reason_category, "reason": result.outcome.reason,
             "ts": datetime.now(timezone.utc).isoformat(timespec="seconds")})
    if result.outcome.condition:
        entry["conditions"].append(result.outcome.condition)
    _save(FACILITY_MEM, mem)

    gaps = _load(PATIENT_GAPS)
    plist = gaps.setdefault(patient_id, [])
    for q in result.outcome.flagged_questions:
        if q not in [g["question"] for g in plist]:
            plist.append({"question": q, "first_asked_by": result.facility_id,
                          "status": "open"})
    _save(PATIENT_GAPS, gaps)


def briefing_for_call(facility_id: str, patient_id: str) -> str:
    """Context block injected into the Caller's system prompt before dialing."""
    mem = _load(FACILITY_MEM)
    gaps = _load(PATIENT_GAPS).get(patient_id, [])
    lines: list[str] = []

    fac = mem.get(facility_id)
    if fac:
        if fac["questions_asked"]:
            lines.append("This facility has previously asked: "
                         + "; ".join(fac["questions_asked"][-5:])
                         + ". Address these proactively in your opening if the packet answers them.")
        if fac["conditions"]:
            lines.append("Previously stated conditions for acceptance: "
                         + "; ".join(fac["conditions"][-3:]))
        if fac["decline_reasons"]:
            last = fac["decline_reasons"][-1]
            lines.append(f"Last decline from them: {last['category']} — {last['reason']}. "
                         "If that condition is now resolved, say so explicitly and early.")

    # cross-facility: questions ANY intake asked that our packets couldn't answer
    open_gaps = [g["question"] for g in gaps if g["status"] == "open"]
    if open_gaps:
        lines.append("KNOWN UNKNOWNS about this patient (no packet answer yet): "
                     + "; ".join(open_gaps[-5:])
                     + ". If asked, say the team is gathering this — do not improvise.")

    return ("\n\n## Call briefing (accumulated from prior calls)\n" + "\n".join(f"- {l}" for l in lines)) if lines else ""


def gap_checklist(patient_id: str) -> list[dict]:
    """The nurse-facing gather-list."""
    return _load(PATIENT_GAPS).get(patient_id, [])


def memory_block(facility_id: str, patient_id: str) -> str:
    """Human-readable prior-call memory, fed to the pre-call brief prompt.
    Same two ledgers as briefing_for_call, phrased for a person, not a bot."""
    mem = _load(FACILITY_MEM).get(facility_id, {})
    gaps = [g["question"] for g in _load(PATIENT_GAPS).get(patient_id, [])
            if g.get("status") == "open"]
    lines: list[str] = []
    if mem.get("questions_asked"):
        lines.append("This facility has asked before: "
                     + "; ".join(mem["questions_asked"][-6:]))
    if mem.get("conditions"):
        lines.append("Conditions they've named for acceptance: "
                     + "; ".join(mem["conditions"][-3:]))
    if mem.get("decline_reasons"):
        last = mem["decline_reasons"][-1]
        lines.append(f"They last declined for: {last.get('category')} — {last.get('reason')}.")
    if gaps:
        lines.append("Open known-unknowns about this patient (no packet answer yet): "
                     + "; ".join(gaps[-6:]))
    return "\n".join(f"- {l}" for l in lines) if lines else "- No prior-call history for this facility yet."
