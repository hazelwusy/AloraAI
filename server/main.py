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

from pipeline.copilot import observe, precall_brief
from pipeline.directory import load_directory, match_directory
from pipeline.learning import record_call
from pipeline.schemas import CallOutcome, CallResult

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


@app.get("/api/referrals")
def referrals():
    return _state()


def _facility(facility_id: str) -> dict:
    """Resolve against the real 74-facility directory — the single knowledge
    graph the map, matcher, and monitoring agent all share."""
    fac = next((f for f in load_directory() if f["id"] == facility_id), None)
    if not fac:
        raise HTTPException(404, "unknown facility")
    return fac


@app.post("/api/precall")
def do_precall(body: dict):
    """Job 1 — what to say. body = {patient_id, facility_id, packet_json}.
    Alora preps the case manager; she makes the call herself."""
    fac = _facility(body["facility_id"])
    brief = precall_brief(body["packet_json"], fac, body["patient_id"])
    return {"facility": fac, "brief": brief.model_dump()}


@app.post("/api/copilot/observe")
def do_observe(body: dict):
    """Job 2 — one live tick. body = {patient_id, facility_id, packet_json, transcript}.
    The case manager is on the line; Alora reads the rolling transcript and
    returns the dashboard state to render."""
    fac = _facility(body["facility_id"])
    state = observe(body.get("transcript", ""), body["packet_json"], fac, body["patient_id"])
    return {"state": state.model_dump()}


@app.post("/api/copilot/finalize")
def do_finalize(body: dict):
    """Job 3 — capture + learn. The case manager confirms the outcome (she is the
    source of truth); Alora records it into both learning ledgers and suggests a
    next candidate on decline.
    body = {patient_id, facility_id, outcome, reason, reason_category, condition,
            questions_asked_by_intake, flagged_questions, next_step_for_nurse,
            transcript, direction, payer, language}"""
    fac = _facility(body["facility_id"])
    outcome = CallOutcome(
        outcome=body["outcome"],
        reason=body.get("reason", ""),
        reason_category=body.get("reason_category"),
        condition=body.get("condition"),
        questions_asked_by_intake=body.get("questions_asked_by_intake", []),
        documents_requested=body.get("documents_requested", []),
        callback=body.get("callback"),
        next_step_for_nurse=body.get("next_step_for_nurse", ""),
        flagged_questions=body.get("flagged_questions", []),
    )
    transcript = body.get("transcript", [])
    if isinstance(transcript, str):
        transcript = [{"speaker": "call", "text": transcript}]
    result = CallResult(facility_id=fac["id"], transcript=transcript,
                        outcome=outcome, simulated_far_end=False)
    record_call(body["patient_id"], result)  # updates facility memory + patient gaps

    state = _state()
    ref = {"patient_id": body["patient_id"], "facility_id": fac["id"],
           "status": outcome.outcome,
           "events": [{"ts": _now(), "status": outcome.outcome, "facility_id": fac["id"],
                       "note": outcome.reason, "call": result.model_dump()}]}
    state["referrals"].append(ref)
    _save(state)

    nxt = None
    if outcome.outcome == "declined":
        exclude = [r["facility_id"] for r in state["referrals"] if r["patient_id"] == body["patient_id"]]
        candidates = match_directory({"direction": body.get("direction", "step_down"),
                                      "payer": body.get("payer"), "language": body.get("language"),
                                      "exclude": exclude})
        nxt = candidates[0] if candidates else None

    return {"recorded": True, "next_candidate": nxt}



# ---- v2 endpoints: reconciliation + readiness + decline routing ----

from datetime import datetime as _dt  # noqa: E402

from pipeline.readiness import check as readiness_check  # noqa: E402
from pipeline.schemas import DECLINE_ROUTING  # noqa: E402

DEMO_NOW = _dt(2026, 7, 12, 15, 0)  # aligned to Maria timeline in data/patients/maria/notes/


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
    reports = []
    for f in load_directory():
        sim = f.get("simulated", {})
        fac = {"id": f["id"], "intake_requirements": sim.get("intake_requirements", [])}
        rep = readiness_check(fac, fields, DEMO_NOW).model_dump()
        rep["name"] = f["name"]
        rep["level_of_care"] = f["level_of_care"]
        reports.append(rep)
    return {"reports": reports}


@app.post("/api/match-directory")
def do_match_directory(need: dict):
    """Match over the real 74-facility SF directory (teammate dataset)."""
    return {"candidates": match_directory(need)}


@app.get("/api/learning/{facility_id}")
def facility_learning(facility_id: str):
    from pipeline.learning import _load, FACILITY_MEM
    return _load(FACILITY_MEM).get(facility_id, {})


@app.get("/api/gaps/{patient_id}")
def patient_gaps(patient_id: str):
    from pipeline.learning import gap_checklist
    return {"gaps": gap_checklist(patient_id)}


@app.get("/api/patients")
def list_patients():
    base = ROOT / "data" / "patients"
    out = []
    for p in sorted(base.iterdir()):
        if p.is_dir() and (p / "demographics.json").exists():
            demo = json.loads((p / "demographics.json").read_text())
            out.append({"id": p.name, "age": demo.get("age"), "insurance": demo.get("insurance"),
                        "language": demo.get("language"), "n_notes": len(list((p / "notes").glob("*")))})
    return {"patients": out}


@app.get("/api/decline-routing")
def decline_routing():
    return DECLINE_ROUTING


# ---- v3: facility knowledge-graph monitoring (HITL update loop) ----

from pipeline import monitor  # noqa: E402


@app.get("/api/graph")
def graph():
    """The live knowledge graph: real 74-facility directory + referral edges,
    served from the runtime store the monitoring agent updates (out/, seeded
    from data/). This is the single graph the map, matcher, and agent share."""
    return {"facilities": monitor.load_facilities(), "edges": monitor.load_edges()}


@app.get("/api/monitor/pending")
def monitor_pending():
    return {"pending": monitor.list_pending()}


@app.post("/api/monitor/scan")
def monitor_scan():
    """Run every registered fetcher (simulated web/phone/EHR-feed checks).
    Confidence-tiered: high-confidence, non-clinical findings are auto-applied
    to the graph; the rest are queued for human review. Returns both sets."""
    return monitor.run_scan()


@app.get("/api/monitor/reliability")
def monitor_reliability():
    """The agent's learned per-source trust weights — how it 'gets better' at
    deciding what to apply on its own vs escalate to a human."""
    return {"reliability": monitor.load_reliability()}


@app.post("/api/monitor/approve/{update_id}")
def monitor_approve(update_id: str, body: dict):
    """body = {approved_by: str}"""
    try:
        return monitor.approve(update_id, approved_by=body.get("approved_by", "unknown"))
    except KeyError as e:
        raise HTTPException(404, str(e))


@app.post("/api/monitor/reject/{update_id}")
def monitor_reject(update_id: str, body: dict):
    """body = {reason: str}"""
    try:
        return monitor.reject(update_id, reason=body.get("reason", ""))
    except KeyError as e:
        raise HTTPException(404, str(e))


@app.get("/api/monitor/history/{entity_id:path}")
def monitor_history(entity_id: str):
    return {"entity_id": entity_id, "history": monitor.get_history(entity_id)}


# serve the demo UI at / — MUST stay last so it never shadows /api routes
app.mount("/", StaticFiles(directory=ROOT / "web", html=True), name="web")
