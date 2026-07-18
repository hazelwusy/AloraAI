"""Facility knowledge-graph monitoring agent.

In production this would continuously check authoritative channels — public
facility web pages, phone verification calls to intake lines, an EHR/bed-
registry feed (e.g. a future CA DHCS BCDS or OpenBeds integration, see
data/facilities_collection_notes.md: neither has a public API today, CA's own
system is still at RFI stage) — for changes to facility or referral-edge data,
and propose updates. Nothing is ever applied automatically: every proposed
update sits in a human-in-the-loop queue until approved, then is written into
data/facilities.json or data/edges_directory.json and logged to
data/monitoring/version_history.json.

Demo note: the three Fetcher classes below are SIMULATED — no real web
crawl, phone call, or EHR poll happens. Each produces a small set of example
proposals so the propose -> approve/reject -> apply -> version-history loop
can be demoed end-to-end. Swapping in a real fetcher is a drop-in
replacement: implement `.scan() -> list[ProposedUpdate]` and add it to
`FETCHERS` below — everything downstream (queue, HITL approval, graph
mutation, history log) is already generic over entity type and source type.
"""
from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal, Optional, Protocol

DATA = Path(__file__).parent.parent / "data"
FACILITIES_PATH = DATA / "facilities.json"
EDGES_PATH = DATA / "edges_directory.json"
MONITOR_DIR = DATA / "monitoring"
PENDING_PATH = MONITOR_DIR / "pending_updates.json"
HISTORY_PATH = MONITOR_DIR / "version_history.json"

SourceType = Literal["web", "phone_call", "ehr_feed"]
EntityType = Literal["facility", "edge"]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _load_json(path: Path, default):
    return json.loads(path.read_text()) if path.exists() else default


def _save_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n")


def edge_entity_id(from_id: str, to_id: str) -> str:
    return f"{from_id}|{to_id}"


def _get_by_path(obj: dict, path: str):
    cur = obj
    for part in path.split("."):
        cur = cur[part]
    return cur


def _set_by_path(obj: dict, path: str, value) -> None:
    parts = path.split(".")
    cur = obj
    for part in parts[:-1]:
        cur = cur.setdefault(part, {})
    cur[parts[-1]] = value


def _find_entity(entity_type: EntityType, entity_id: str):
    """Returns (container_to_save, entity_dict_or_None)."""
    if entity_type == "facility":
        facilities = _load_json(FACILITIES_PATH, [])
        entity = next((f for f in facilities if f["id"] == entity_id), None)
        return facilities, entity
    edges_doc = _load_json(EDGES_PATH, {"edges": []})
    from_id, to_id = entity_id.split("|", 1)
    entity = next((e for e in edges_doc["edges"] if e["from"] == from_id and e["to"] == to_id), None)
    return edges_doc, entity


@dataclass
class ProposedUpdate:
    entity_type: EntityType
    entity_id: str                    # facility id, or "from|to" for an edge
    field_path: str                   # dotted path, e.g. "simulated.availability.available_beds"
    new_value: object
    source_type: SourceType
    source_detail: str
    confidence: float
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:10])
    proposed_at: str = field(default_factory=_now)
    old_value: object = None
    status: str = "pending"

    def to_dict(self) -> dict:
        return {
            "id": self.id, "entity_type": self.entity_type, "entity_id": self.entity_id,
            "field_path": self.field_path, "old_value": self.old_value, "new_value": self.new_value,
            "source_type": self.source_type, "source_detail": self.source_detail,
            "confidence": self.confidence, "proposed_at": self.proposed_at, "status": self.status,
        }


class Fetcher(Protocol):
    source_type: SourceType

    def scan(self) -> list[ProposedUpdate]: ...


class SimulatedWebFetcher:
    """Stand-in for periodically re-checking each facility's public web page /
    sf.gov listing for a stated change (e.g. a posted wait-time or capacity
    note). Real version: WebFetch/WebSearch against `source_url` per facility,
    diffed against the last-seen snapshot."""

    source_type: SourceType = "web"

    EXAMPLE_FINDINGS = [
        ("zsfg-pes", "simulated.availability.estimated_wait_days", 1,
         "sf.gov PES status page states next-available today (simulated check)"),
        ("dore-urgent-care", "simulated.availability.available_beds", 2,
         "facility site's posted 'current capacity' note (simulated check)"),
    ]

    def scan(self) -> list[ProposedUpdate]:
        return [
            ProposedUpdate(entity_type="facility", entity_id=fid, field_path=path,
                            new_value=val, source_type=self.source_type, source_detail=detail,
                            confidence=0.65)
            for fid, path, val, detail in self.EXAMPLE_FINDINGS
        ]


class SimulatedPhoneFetcher:
    """Stand-in for a verification call to a facility's intake line. Real
    version: a Twilio-style outbound call running the same Caller agent as
    pipeline/call_sim.py, asking a scoped availability question instead of
    running a full referral."""

    source_type: SourceType = "phone_call"

    EXAMPLE_FINDINGS = [
        ("hummingbird-potrero", "simulated.availability.available_beds", 1,
         "intake line confirmed one bed opening this afternoon (simulated call)"),
        ("minna-project", "simulated.availability.estimated_wait_days", 18,
         "intake coordinator quoted a longer waitlist than currently on file (simulated call)"),
    ]

    def scan(self) -> list[ProposedUpdate]:
        return [
            ProposedUpdate(entity_type="facility", entity_id=fid, field_path=path,
                            new_value=val, source_type=self.source_type, source_detail=detail,
                            confidence=0.85)
            for fid, path, val, detail in self.EXAMPLE_FINDINGS
        ]


class SimulatedEHRFeedFetcher:
    """Stand-in for an aggregated referral-outcome or bed-registry feed (e.g.
    a future CA DHCS BCDS / OpenBeds-style integration — neither has a public
    API today, see data/facilities_collection_notes.md). Updates edge-level
    observed acceptance behavior rather than single-facility fields."""

    source_type: SourceType = "ehr_feed"

    EXAMPLE_FINDINGS = [
        (("zsfg-pes", "dore-urgent-care"), "simulated.accept_rate_observed", 0.72,
         "aggregated referral-outcome feed, trailing 30 days (simulated)"),
        (("dore-urgent-care", "soma-rise"), "simulated.avg_response_time_min_observed", 28,
         "aggregated referral-outcome feed, trailing 30 days (simulated)"),
    ]

    def scan(self) -> list[ProposedUpdate]:
        return [
            ProposedUpdate(entity_type="edge", entity_id=edge_entity_id(frm, to), field_path=path,
                            new_value=val, source_type=self.source_type, source_detail=detail,
                            confidence=0.9)
            for (frm, to), path, val, detail in self.EXAMPLE_FINDINGS
        ]


FETCHERS: list[Fetcher] = [SimulatedWebFetcher(), SimulatedPhoneFetcher(), SimulatedEHRFeedFetcher()]


def load_facilities() -> list[dict]:
    return _load_json(FACILITIES_PATH, [])


def load_edges() -> dict:
    return _load_json(EDGES_PATH, {"edges": []})


def list_pending() -> list[dict]:
    return _load_json(PENDING_PATH, [])


def propose(update: ProposedUpdate) -> dict:
    """Fill in old_value from current state, append to the pending queue."""
    _, entity = _find_entity(update.entity_type, update.entity_id)
    if entity is not None:
        try:
            update.old_value = _get_by_path(entity, update.field_path)
        except (KeyError, TypeError):
            update.old_value = None
    pending = list_pending()
    pending.append(update.to_dict())
    _save_json(PENDING_PATH, pending)
    return update.to_dict()


def run_scan() -> list[dict]:
    """Run every registered fetcher, propose everything found. Returns the
    newly proposed updates (skips anything already pending for the same
    entity+field to avoid duplicate queue entries on repeated scans)."""
    already_pending = {(u["entity_type"], u["entity_id"], u["field_path"]) for u in list_pending()}
    proposed: list[dict] = []
    for fetcher in FETCHERS:
        for update in fetcher.scan():
            key = (update.entity_type, update.entity_id, update.field_path)
            if key in already_pending:
                continue
            proposed.append(propose(update))
            already_pending.add(key)
    return proposed


def approve(update_id: str, approved_by: str) -> dict:
    pending = list_pending()
    idx = next((i for i, u in enumerate(pending) if u["id"] == update_id), None)
    if idx is None:
        raise KeyError(f"no pending update {update_id}")
    upd = pending.pop(idx)

    container, entity = _find_entity(upd["entity_type"], upd["entity_id"])
    if entity is None:
        raise KeyError(f"entity {upd['entity_id']} not found")
    _set_by_path(entity, upd["field_path"], upd["new_value"])

    if upd["entity_type"] == "facility":
        entity["verified_date"] = _now()[:10]
        _save_json(FACILITIES_PATH, container)
    else:
        _save_json(EDGES_PATH, container)

    upd["status"] = "approved"
    upd["approved_by"] = approved_by
    upd["approved_at"] = _now()
    _save_json(PENDING_PATH, pending)
    _append_history(upd)
    return upd


def reject(update_id: str, reason: str) -> dict:
    pending = list_pending()
    idx = next((i for i, u in enumerate(pending) if u["id"] == update_id), None)
    if idx is None:
        raise KeyError(f"no pending update {update_id}")
    upd = pending.pop(idx)
    upd["status"] = "rejected"
    upd["reject_reason"] = reason
    upd["rejected_at"] = _now()
    _save_json(PENDING_PATH, pending)
    _append_history(upd)
    return upd


def _append_history(upd: dict) -> None:
    history = _load_json(HISTORY_PATH, {})
    history.setdefault(upd["entity_id"], []).append(upd)
    _save_json(HISTORY_PATH, history)


def get_history(entity_id: str) -> list[dict]:
    return _load_json(HISTORY_PATH, {}).get(entity_id, [])
