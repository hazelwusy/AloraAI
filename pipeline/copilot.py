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

from . import llm
from .learning import memory_block
from .schemas import CoPilotState, PreCallBrief


def precall_brief(packet_json: str, facility: dict, patient_id: str) -> PreCallBrief:
    system = llm.load_prompt("precall")
    user = (
        f"target facility:\n{json.dumps(facility)}\n\n"
        f"prior-call memory:\n{memory_block(facility['id'], patient_id)}\n\n"
        f"packet:\n{packet_json}"
    )
    return llm.call_json(system, user, PreCallBrief, max_tokens=1500)


def observe(transcript: str, packet_json: str, facility: dict, patient_id: str) -> CoPilotState:
    """One tick of the live dashboard. `transcript` is the call so far as plain
    text (speakers may be unlabeled — a single speakerphone mic)."""
    briefing = memory_block(facility["id"], patient_id)
    system = (
        llm.load_prompt("copilot")
        + f"\n\ntarget facility:\n{json.dumps(facility)}"
        + f"\n\nCall briefing (prior calls):\n{briefing}"
        + f"\n\npacket:\n{packet_json}"
    )
    user = f"Rolling transcript of the live call so far:\n\n{transcript.strip() or '(call just connected — nothing said yet)'}"
    return llm.call_json(system, user, CoPilotState, max_tokens=1500)
