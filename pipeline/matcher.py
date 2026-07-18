"""Deterministic facility matcher. No LLM in the ranking — every result is
explainable and reproducible. The LLM only narrates trade-offs afterward."""
from __future__ import annotations

import json
from pathlib import Path

DATA = Path(__file__).parent.parent / "data"

STEP_DOWN_LEVELS = ["crisis_stabilization", "peer_respite", "adu", "residential", "php", "urgent_outpatient", "intensive_case_mgmt"]


def load_facilities() -> list[dict]:
    return json.loads((DATA / "facilities.json").read_text())["facilities"]


def match(need: dict) -> list[dict]:
    """need = {"direction": "step_down"|"step_up", "payer": str, "language": str,
               "exclude": [facility_id, ...]}
    Returns ranked candidates with per-candidate reasons."""
    out = []
    for f in load_facilities():
        reasons, hard_fail = [], False

        if f["id"] in need.get("exclude", []):
            continue
        if need["direction"] == "step_down" and f["level"] not in STEP_DOWN_LEVELS:
            continue
        if need["direction"] == "step_up" and f["type"] != "inpatient":
            continue

        if need.get("payer") and need["payer"] not in f["payers"]:
            hard_fail = True
            reasons.append(f"payer mismatch: no {need['payer']} contract")
        else:
            reasons.append(f"accepts {need.get('payer', 'any payer')}")

        if need.get("language") and need["language"] not in f["languages"]:
            reasons.append(f"no {need['language']} services (interpreter needed)")
        else:
            reasons.append("language OK")

        if f["beds_sim"] > 0:
            reasons.append(f"{f['beds_sim']} bed(s) available (simulated)")
        else:
            reasons.append("at census (simulated)")

        if not hard_fail:
            score = f["beds_sim"] * 2 + f["accept_rate_sim"] * 10 - f["median_response_hours_sim"] * 0.2
            out.append({"facility": f, "score": round(score, 1), "reasons": reasons})

    return sorted(out, key=lambda x: -x["score"])
