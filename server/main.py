"""Demo API. State is one JSON file — no database, by design.

    uvicorn server.main:app --reload --port 8000
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from pipeline import llm
from pipeline.call_sim import run_call
from pipeline.matcher import load_facilities, match

ROOT = Path(__file__).parent.parent
STATE_PATH = ROOT / "out" / "state.json"

app = FastAPI(title="AloraAI demo API")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


def _state() -> dict:
    if STATE_PATH.exists():
        return json.loads(STATE_PATH.read_text())
    return {"referrals": []}  # each: {patient_id, facility_id, status, events: []}


def _save(state: dict) -> None:
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(json.dumps(state, indent=1))


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@app.get("/api/facilities")
def facilities():
    return {"facilities": load_facilities(),
            "edges": json.loads((ROOT / "data" / "edges.json").read_text())}


@app.post("/api/match")
def do_match(need: dict):
    return {"candidates": match(need)}


@app.get("/api/referrals")
def referrals():
    return _state()


@app.post("/api/call")
def place_call(body: dict):
    """body = {patient_id, facility_id, packet_json, nurse_name, mode: "agent"|"self"}
    mode=self returns a call script for the nurse instead of running the agent."""
    fac = next((f for f in load_facilities() if f["id"] == body["facility_id"]), None)
    if not fac:
        raise HTTPException(404, "unknown facility")

    state = _state()
    ref = {"patient_id": body["patient_id"], "facility_id": fac["id"],
           "status": "authorized", "events": [{"ts": _now(), "status": "authorized",
                                              "facility_id": fac["id"],
                                              "note": f"authorized by {body['nurse_name']} (mode={body['mode']})"}]}

    if body["mode"] == "self":
        # nurse calls herself: agent contributes the talking-points script only
        resp = llm.client().messages.create(
            model=llm.MODEL, max_tokens=800,
            system="Write a 30-second phone script (bullet points) a nurse can read to this facility's intake line, from this packet. Lead with level of care, legal status, payer, medical clearance.",
            messages=[{"role": "user", "content": f"facility: {json.dumps(fac)}\n\npacket: {body['packet_json']}"}],
        )
        ref["status"] = "calling"
        ref["events"].append({"ts": _now(), "status": "calling", "facility_id": fac["id"],
                              "note": "nurse dialing herself", "script": resp.content[0].text})
        state["referrals"].append(ref)
        _save(state)
        return {"mode": "self", "script": resp.content[0].text, "referral": ref}

    result = run_call(body["packet_json"], fac, body["nurse_name"])
    ref["status"] = result.outcome.outcome
    ref["events"].append({"ts": _now(), "status": result.outcome.outcome,
                          "facility_id": fac["id"], "note": result.outcome.reason,
                          "call": result.model_dump()})
    state["referrals"].append(ref)
    _save(state)

    nxt = None
    if result.outcome.outcome == "declined":
        exclude = [r["facility_id"] for r in state["referrals"] if r["patient_id"] == body["patient_id"]]
        candidates = match({"direction": body.get("direction", "step_down"),
                            "payer": body.get("payer"), "language": body.get("language"),
                            "exclude": exclude})
        nxt = candidates[0] if candidates else None

    return {"mode": "agent", "result": result.model_dump(), "next_candidate": nxt}



# ---- v2 endpoints: reconciliation + readiness + decline routing ----

from datetime import datetime as _dt  # noqa: E402

from pipeline.readiness import check as readiness_check  # noqa: E402
from pipeline.schemas import DECLINE_ROUTING  # noqa: E402

DEMO_NOW = _dt(2026, 7, 18, 10, 0)


@app.get("/api/reconcile/{patient_id}")
def get_reconciliation(patient_id: str, live: bool = False):
    """Cached by default (out/<id>_recon.json); pass ?live=true to re-run the
    Domain Extractor (needs ANTHROPIC_API_KEY)."""
    cache = ROOT / "out" / f"{patient_id}_recon.json"
    if cache.exists() and not live:
        return json.loads(cache.read_text())
    from pipeline.extract import reconcile_patient
    return reconcile_patient(patient_id).model_dump()


@app.get("/api/readiness/{patient_id}")
def get_readiness(patient_id: str):
    """Deterministic readiness gate for every candidate facility — no LLM."""
    fields_path = ROOT / "data" / "patients" / patient_id / "patient_fields.json"
    if not fields_path.exists():
        raise HTTPException(404, "no patient_fields.json for patient")
    fields = json.loads(fields_path.read_text())
    return {"reports": [readiness_check(f, fields, DEMO_NOW).model_dump()
                        for f in load_facilities()]}


@app.get("/api/decline-routing")
def decline_routing():
    return DECLINE_ROUTING


# serve the demo UI at / — MUST stay last so it never shadows /api routes
app.mount("/", StaticFiles(directory=ROOT / "web", html=True), name="web")
