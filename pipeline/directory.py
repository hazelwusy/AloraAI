"""Loader + matcher over the REAL 74-facility SF directory (data/facilities.json,
built from SFDPH/SAMHSA public sources; `simulated.*` fields are demo-only).
The 10-facility facilities_demo.json remains only for the network-map view."""
from __future__ import annotations

from . import live_store

STEP_DOWN_LEVELS = ["crisis_stabilization", "peer_respite", "sobering",
                    "residential_tx", "residential_stepdown", "PHP", "IOP", "outpatient"]
STEP_UP_LEVELS = ["inpatient_psych", "locked_subacute"]

LANG_MAP = {"es": "Spanish", "en": "English", "zh": ["Cantonese", "Mandarin"]}


def load_directory() -> list[dict]:
    # the live runtime graph (seeded from data/facilities.json) so the matcher
    # sees the monitoring agent's updates; committed data/ stays pristine.
    return live_store.load_json(live_store.facilities_path(), [])


def _speaks(facility: dict, lang_code: str) -> bool:
    want = LANG_MAP.get(lang_code, lang_code)
    wants = want if isinstance(want, list) else [want]
    return any(w in facility.get("languages", []) for w in wants)


def match_directory(need: dict) -> list[dict]:
    """need = {"direction", "payer", "language", "level_filter": [..] | None, "exclude": [..]}"""
    levels = need.get("level_filter") or (
        STEP_DOWN_LEVELS if need["direction"] == "step_down" else STEP_UP_LEVELS)
    out = []
    for f in load_directory():
        if f["id"] in need.get("exclude", []) or f["level_of_care"] not in levels:
            continue
        reasons, hard_fail = [], False

        if need.get("payer") and need["payer"] not in f.get("payers", []):
            hard_fail = True
        else:
            reasons.append(f"accepts {need.get('payer', 'any payer')}")

        if need.get("language") and not _speaks(f, need["language"]):
            reasons.append("interpreter needed")
        else:
            reasons.append("language OK")

        sim = f.get("simulated", {})
        beds = sim.get("availability", {}).get("available_beds")
        wait = sim.get("availability", {}).get("estimated_wait_days")
        reasons.append(f"beds: {'unknown' if beds is None else beds} · wait ~{wait}d (simulated)")

        if not hard_fail:
            score = (0 if beds is None else beds * 2) \
                + sim.get("decline_behavior", {}).get("accept_rate", 0.5) * 10 \
                - (wait or 0) * 1.5 \
                + (2 if _speaks(f, need.get("language", "")) else 0)
            out.append({"facility": {k: f[k] for k in ("id", "name", "level_of_care", "payers", "languages")},
                        "intake_requirements": sim.get("intake_requirements", []),
                        "score": round(score, 1), "reasons": reasons})
    return sorted(out, key=lambda x: -x["score"])
