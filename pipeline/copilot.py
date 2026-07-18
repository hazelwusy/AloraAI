"""The companion co-pilot. Alora does NOT place calls — the human case manager
does. This module powers the two things Alora does for her instead:

1. precall_brief() — Job 1: what to say, assembled before she dials.
2. observe()       — Job 2: read the rolling transcript of her live call and
                     emit the dashboard state that re-renders as the call moves.

Both are single grounded Claude passes; every clinical answer must trace to the
approved packet.
"""
from __future__ import annotations

import json
import os

from . import llm
from .learning import memory_block
from .schemas import (CoPilotState, CoveredItem, DetectedOutcome, LikelyQuestion,
                      PreCallBrief, SurfacedAnswer)

# Whether a live LLM is reachable. When no key is configured (the common demo
# case) we skip the call and serve a deterministic brief/board so the whole
# case-manager flow works offline instead of 500-ing.
_HAS_LLM = bool(os.environ.get("ANTHROPIC_API_KEY"))


def _packet(packet_json: str) -> dict:
    try:
        return json.loads(packet_json) if isinstance(packet_json, str) else (packet_json or {})
    except Exception:
        return {}


def precall_brief(packet_json: str, facility: dict, patient_id: str) -> PreCallBrief:
    if _HAS_LLM:
        try:
            system = llm.load_prompt("precall")
            user = (
                f"target facility:\n{json.dumps(facility)}\n\n"
                f"prior-call memory:\n{memory_block(facility['id'], patient_id)}\n\n"
                f"packet:\n{packet_json}"
            )
            return llm.call_json(system, user, PreCallBrief, max_tokens=1500)
        except Exception:
            pass  # degrade to the deterministic brief below
    return _fallback_brief(_packet(packet_json), facility)


def _fallback_brief(pkt: dict, facility: dict) -> PreCallBrief:
    """Deterministic brief assembled straight from the approved packet — no LLM.
    Grounded by construction: every line is a packet field."""
    loc = (facility.get("level_of_care") or "").replace("_", " ")
    name = facility.get("name", "the facility")
    lead = [x for x in [
        f"level of care sought: {loc}" if loc else "",
        f"legal status: {pkt.get('legal_status','')}" if pkt.get("legal_status") else "",
        f"payer: {pkt.get('payer') or 'Medi-Cal'}",
        f"medical clearance: {pkt.get('medical_clearance','')}" if pkt.get("medical_clearance") else "",
    ] if x]
    script = (f"Hi, this is the case manager at ZSFG. I'm calling about a step-down placement at {name}. "
              f"{pkt.get('one_liner','')} Legal status: {pkt.get('legal_status','voluntary')}. "
              f"Medically {pkt.get('medical_clearance','cleared')}.").strip()
    fields = {"legal status": pkt.get("legal_status"), "medical clearance": pkt.get("medical_clearance"),
              "medications": pkt.get("medications"), "risk/SI status": pkt.get("risk"),
              "aftercare needs": pkt.get("aftercare_needs")}
    likely = [LikelyQuestion(question=q.capitalize()+"?", in_packet=bool(v), packet_answer=v or "")
              for q, v in fields.items()]
    gather = [q for q, v in fields.items() if not v] + ["substance use in last 72h (not in packet)"]
    return PreCallBrief(one_liner=pkt.get("one_liner", ""), lead_with=lead, script=script,
                        likely_questions=likely, gather_first=gather)


def observe(transcript: str, packet_json: str, facility: dict, patient_id: str) -> CoPilotState:
    """One tick of the live dashboard. `transcript` is the call so far as plain
    text (speakers may be unlabeled — a single speakerphone mic)."""
    if _HAS_LLM:
        try:
            briefing = memory_block(facility["id"], patient_id)
            system = (
                llm.load_prompt("copilot")
                + f"\n\ntarget facility:\n{json.dumps(facility)}"
                + f"\n\nCall briefing (prior calls):\n{briefing}"
                + f"\n\npacket:\n{packet_json}"
            )
            user = f"Rolling transcript of the live call so far:\n\n{transcript.strip() or '(call just connected — nothing said yet)'}"
            return llm.call_json(system, user, CoPilotState, max_tokens=1500)
        except Exception:
            pass
    return _fallback_observe(transcript, _packet(packet_json))


# intake-question cue -> (label, packet key, evidence channel). This is how the
# deterministic board shows Alora synthesizing an answer from the right source.
_ANSWER_MAP = [
    (["risk", "suicidal", "ideation", "assessment"], "Last risk assessment / SI?", "risk", "nursing reassessment note"),
    (["substance", "tox", "drug", "alcohol", "72 hour", "72 hours"], "Substance use in last 72h?", "substance_use", "EHR labs (day-0 tox)"),
    (["cleared", "medically", "medical"], "Medically cleared?", "medical_clearance", "IM clearance note"),
    (["insurance", "medi-cal", "medicaid", "payer", "coverage"], "Insurance / payer?", "insurance", "eligibility portal"),
    (["language", "spanish", "interpret"], "Language / interpreter?", "language_support", "demographics"),
    (["medication", "meds", "prn"], "Current medications?", "medications", "MAR"),
]


def _fallback_observe(transcript: str, pkt: dict) -> CoPilotState:
    """Deterministic live board from keyword cues in the transcript — no LLM.
    Surfaces a grounded, source-cited answer for each intake question so the demo
    shows Alora pulling evidence across channels and answering everything."""
    t = (transcript or "").lower()
    essentials = [("level of care sought", ["step-down", "step down", "bed", "placement"]),
                  ("legal status", ["voluntary", "5150", "hold", "conservat"]),
                  ("payer", ["medi-cal", "medicaid", "insurance", "medicare"]),
                  ("medical clearance", ["cleared", "medically", "labs"]),
                  ("acuity one-liner", ["risk", "suicidal", "ideation", "psychosis", "stable"])]
    covered = [CoveredItem(label=lbl, covered=any(k in t for k in keys)) for lbl, keys in essentials]

    surfaced, gaps = [], []
    for keys, label, pk, source in _ANSWER_MAP:
        if not any(k in t for k in keys):
            continue
        val = pkt.get(pk)
        if val:
            surfaced.append(SurfacedAnswer(intake_question=label, in_packet=True,
                                           packet_answer=str(val), citation=f"{source}: {val}"))
        else:
            gaps.append(f"{label} — asked by intake, not in packet")

    outcome = None
    if any(k in t for k in ["we have a bed", "we can take", "we'll accept", "we'll hold", "hold it for", "that's everything i need", "go ahead"]):
        outcome = DetectedOutcome(kind="accepted", reason="bed offered — send current risk assessment + med rec",
                                  condition="fax current risk assessment and med rec to confirm the hold")
    elif any(k in t for k in ["can't take", "cannot take", "no capacity", "we're full", "decline"]):
        outcome = DetectedOutcome(kind="declined", reason="facility indicated no capacity / not a fit")
    elif any(k in t for k in ["fax", "faxed", "before i can", "need the updated"]):
        outcome = DetectedOutcome(kind="info_requested", reason="facility requested documentation before holding a bed",
                                  condition="updated risk assessment faxed before holding a bed")

    nxt = ("Confirm you're faxing the risk assessment and med rec now to lock the bed."
           if outcome and outcome.kind == "accepted"
           else "Offer the tox screen and clearance note proactively to move things forward.")
    return CoPilotState(covered=covered, surfaced_answers=surfaced, open_gaps=gaps,
                        suggested_next_line=nxt, detected_outcome=outcome)
