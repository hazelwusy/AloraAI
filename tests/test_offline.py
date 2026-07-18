"""Deterministic tests — NO API key needed. Run:  python3 -m tests.test_offline"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from pipeline.matcher import match
from pipeline.readiness import check
from pipeline.reconcile import reconcile
from pipeline.schemas import DECLINE_ROUTING, DomainState, DomainValue, ExtractedDomains

ROOT = Path(__file__).parent.parent
NOW = datetime(2026, 7, 18, 10, 0)


def _doc(name: str, **domains) -> ExtractedDomains:
    return ExtractedDomains(document=name, domains=[
        DomainState(domain=d, status="unchanged",
                    current=DomainValue(value=v[0], source=name, time=v[1], quote=v[2]))
        for d, v in domains.items()])


def test_reconcile() -> None:
    prev = [_doc("day0_eval",
                 active_SI=("present with plan", "2026-07-16T21:40", "passive suicidal ideation with a plan"),
                 intent_plan=("present", "2026-07-16T21:40", "Intent assessed as present with plan"),
                 psychosis=("denied", "2026-07-16T21:40", "No hallucinations or delusional content"))]
    curr = [
        _doc("day2_psychiatry",
             active_SI=("denied (today)", "2026-07-18T09:20", "Denies suicidal ideation today"),
             psychosis=("denied", "2026-07-18T09:20", "No psychotic symptoms"),
             collateral=("no overnight distress", "2026-07-18T09:20", "no observed distress"),
             vitals=("BP 122/80 HR 84", "2026-07-17T19:30", "Last documented vitals")),
        _doc("day2_nursing",
             collateral=("sister reports 2am distressed call", "2026-07-18T07:05", "sounding tearful"),
             vitals=("BP 122/80 HR 84", "2026-07-17T19:30", "Last documented vitals")),
    ]
    r = reconcile("maria", prev, curr, NOW, hours_since_previous=36.0)
    by = {row.domain: row.status for row in r.rows}
    assert by["active_SI"] == "changed", by
    assert by["intent_plan"] == "not_reassessed", by
    assert by["psychosis"] == "unchanged", by
    assert by["collateral"] == "conflicting", by
    assert by["vitals"] == "stale", by
    assert "intent_plan" in r.unresolved and "collateral" in r.unresolved
    print("reconcile differ: changed/not_reassessed/unchanged/conflicting/stale all correct")


def test_readiness() -> None:
    """Maria is on a 5150 hold with a day-0 risk assessment: any facility requiring
    voluntary status must gate her, and stale clocks must fire. Not-ready here is
    the clinically correct answer — the gate exists to say it."""
    from datetime import datetime as dt
    NOW2 = dt(2026, 7, 12, 15, 0)
    facilities = {f["id"]: f for f in json.loads((ROOT / "data/facilities_demo.json").read_text())["facilities"]}
    fields = json.loads((ROOT / "data/patients/maria/patient_fields.json").read_text())
    dore = check(facilities["dore"], fields, NOW2)
    assert not dore.ready
    gaps = {i.requirement: i.status for i in dore.items if i.status != "met"}
    assert gaps.get("voluntary status") == "missing", gaps
    print(f"readiness gate: dore correctly NOT ready for held patient — gaps {sorted(gaps)}")


def test_matcher_and_routing() -> None:
    c = match({"direction": "step_down", "payer": "medi-cal", "language": "es", "exclude": []})
    assert c and all("facility" in x and x["reasons"] for x in c)
    assert DECLINE_ROUTING["missing_docs"] == "fix_and_resend_same_facility"
    print(f"matcher: {len(c)} explainable candidates; decline routing table intact")




def test_teammate_directory() -> None:
    """Real 74-facility directory + Maria readiness against teammate vocabulary."""
    from datetime import datetime as dt

    from pipeline.directory import load_directory, match_directory
    from pipeline.readiness import check as rcheck

    NOW2 = dt(2026, 7, 12, 15, 0)
    d = load_directory()
    assert len(d) >= 70 and all("simulated" in f for f in d)

    c = match_directory({"direction": "step_down", "payer": "medi-cal", "language": "es", "exclude": []})
    assert c, "no step-down candidates from real directory"
    assert all(x["facility"]["level_of_care"] != "inpatient_psych" for x in c)

    fields = json.loads((ROOT / "data/patients/maria/patient_fields.json").read_text())
    top = c[0]
    rep = rcheck({"id": top["facility"]["id"], "intake_requirements": top["intake_requirements"]}, fields, NOW2)
    unknown = [i for i in rep.items if i.evidence and "no checker defined" in (i.evidence or "")]
    assert not unknown, f"uncovered requirement vocab: {[i.requirement for i in unknown]}"

    # the clinically load-bearing gaps must surface: risk assessment + vitals are >limit old
    zsfg = next(f for f in d if f["id"] == "zsfg-pes")
    rep2 = rcheck({"id": "zsfg-pes", "intake_requirements": zsfg["simulated"]["intake_requirements"]}, fields, NOW2)
    stale = {i.requirement for i in rep2.items if i.status == "stale"}
    assert any("risk assessment" in s for s in stale), stale
    assert any("vitals" in s for s in stale), stale
    print(f"teammate directory: {len(d)} facilities; {len(c)} step-down candidates; "
          f"stale gaps surfaced correctly: {sorted(stale)}")


def test_monitor() -> None:
    """Knowledge-graph monitoring: propose -> approve/reject -> apply -> history.
    Runs against temp copies of facilities.json/edges_directory.json so it never
    mutates the real committed data, even though the module under test writes
    to disk (by design — pipeline/monitor.py has no in-memory-only mode, the
    queue and graph are meant to persist between server requests)."""
    import shutil
    import tempfile

    from pipeline import monitor

    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        shutil.copy(monitor.FACILITIES_PATH, tmp / "facilities.json")
        shutil.copy(monitor.EDGES_PATH, tmp / "edges_directory.json")
        orig = (monitor.FACILITIES_PATH, monitor.EDGES_PATH, monitor.PENDING_PATH, monitor.HISTORY_PATH)
        monitor.FACILITIES_PATH = tmp / "facilities.json"
        monitor.EDGES_PATH = tmp / "edges_directory.json"
        monitor.PENDING_PATH = tmp / "pending_updates.json"
        monitor.HISTORY_PATH = tmp / "version_history.json"
        try:
            proposed = monitor.run_scan()
            assert len(proposed) >= 4, "expected proposals from all three simulated fetchers"
            assert {p["source_type"] for p in proposed} == {"web", "phone_call", "ehr_feed"}

            again = monitor.run_scan()
            assert not again, "re-scanning should not duplicate already-pending proposals"

            fac_update = next(p for p in monitor.list_pending() if p["entity_type"] == "facility")
            approved = monitor.approve(fac_update["id"], approved_by="test_nurse")
            assert approved["status"] == "approved"
            after_entity = monitor._find_entity("facility", fac_update["entity_id"])[1]
            assert monitor._get_by_path(after_entity, fac_update["field_path"]) == fac_update["new_value"]
            assert after_entity["verified_date"] == monitor._now()[:10]

            edge_update = next(p for p in monitor.list_pending() if p["entity_type"] == "edge")
            rejected = monitor.reject(edge_update["id"], reason="needs a second source")
            assert rejected["status"] == "rejected"
            edge_entity = monitor._find_entity("edge", edge_update["entity_id"])[1]
            assert monitor._get_by_path(edge_entity, edge_update["field_path"]) == edge_update["old_value"], \
                "rejected update must not be applied"

            remaining_ids = {p["id"] for p in monitor.list_pending()}
            assert fac_update["id"] not in remaining_ids and edge_update["id"] not in remaining_ids

            hist = monitor.get_history(fac_update["entity_id"])
            assert any(h["id"] == fac_update["id"] and h["status"] == "approved" for h in hist)
            print(f"monitor: {len(proposed)} proposed, 1 approved + applied, 1 rejected + untouched, "
                  f"history recorded, re-scan idempotent")
        finally:
            monitor.FACILITIES_PATH, monitor.EDGES_PATH, monitor.PENDING_PATH, monitor.HISTORY_PATH = orig


if __name__ == "__main__":
    test_reconcile()
    test_readiness()
    test_matcher_and_routing()
    test_teammate_directory()
    test_monitor()
    print("\nALL OFFLINE TESTS PASS")
