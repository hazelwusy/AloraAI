"""Simulated placement call: our Caller agent vs. a role-played intake
coordinator, two Claude conversations talking to each other turn by turn.
Produces a speaker-labeled transcript + structured outcome.

Honest-demo note: the far end is simulated (and labeled as such in the UI);
production swaps this module for telephony (e.g. Twilio Voice) — the Caller
prompt and outcome contract stay identical.
"""
from __future__ import annotations

import json
import re

from . import llm
from .schemas import CallOutcome, CallResult

MAX_TURNS = 12


def _turn(system: str, history: list[dict], max_tokens: int = 300) -> str:
    resp = llm.client().messages.create(
        model=llm.MODEL, max_tokens=max_tokens, system=system, messages=history
    )
    return resp.content[0].text.strip()


def run_call(packet_json: str, facility: dict, nurse_name: str) -> CallResult:
    caller_sys = llm.load_prompt("caller") + f"\n\nnurse who authorized: {nurse_name}\npacket:\n{packet_json}\n\ntarget facility:\n{json.dumps(facility)}"
    intake_sys = llm.load_prompt("intake_roleplay") + f"\n\nyour facility profile:\n{json.dumps(facility)}"

    transcript: list[dict] = []          # [{"speaker": "agent"|"intake", "text": ...}]
    caller_hist: list[dict] = [{"role": "user", "content": "The intake line picks up. Begin the call."}]
    intake_hist: list[dict] = []

    for turn in range(MAX_TURNS):
        agent_line = _turn(caller_sys, caller_hist)
        # caller may end the call by emitting the outcome JSON
        json_match = re.search(r"\{[^{}]*\"outcome\"[\s\S]*\}", agent_line)
        spoken = re.sub(r"\{[^{}]*\"outcome\"[\s\S]*\}", "", agent_line).strip()
        if spoken:
            transcript.append({"speaker": "agent", "text": spoken})
        if json_match:
            outcome = CallOutcome.model_validate_json(json_match.group(0))
            return CallResult(facility_id=facility["id"], transcript=transcript, outcome=outcome, simulated_far_end=True)

        caller_hist += [{"role": "assistant", "content": agent_line}]
        intake_hist += [{"role": "user", "content": spoken or agent_line}]

        intake_line = _turn(intake_sys, intake_hist)
        transcript.append({"speaker": "intake", "text": intake_line})
        intake_hist += [{"role": "assistant", "content": intake_line}]
        caller_hist += [{"role": "user", "content": intake_line}]

    # ran out of turns: force the outcome
    caller_hist += [{"role": "user", "content": "End the call now and output the outcome JSON only."}]
    final = _turn(caller_sys, caller_hist, max_tokens=500)
    outcome = CallOutcome.model_validate_json(re.search(r"\{[\s\S]*\}", final).group(0))
    return CallResult(facility_id=facility["id"], transcript=transcript, outcome=outcome, simulated_far_end=True)
