"""Validate data/facilities.json against the expected schema and print a summary.

Run after any manual edits to facilities.json (e.g. address corrections) to
catch schema drift before committing. Does not fetch anything — the actual
collection step was done via ad-hoc web research (see
data/facilities_collection_notes.md), not a single automatable scrape, because
SFDPH's facility lists are PDFs/Tableau dashboards and SAMHSA's locator has no
public bulk export (see facilities_raw/*/notes.md for what was and wasn't
reachable).
"""
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FACILITIES_PATH = ROOT / "data" / "facilities.json"

REQUIRED_FIELDS = [
    "id", "name", "level_of_care", "population", "payers", "languages",
    "data_source", "source_url", "verified_date", "simulated",
]
VALID_LEVELS = {
    "ED_psych", "crisis_stabilization", "inpatient_psych", "locked_subacute",
    "residential_tx", "residential_stepdown", "sobering", "PHP", "IOP",
    "outpatient", "peer_respite",
}


def main():
    facilities = json.loads(FACILITIES_PATH.read_text())
    ids = Counter(f["id"] for f in facilities)
    dupes = [i for i, n in ids.items() if n > 1]
    if dupes:
        raise SystemExit(f"Duplicate ids found: {dupes}")

    missing_fields = []
    bad_levels = []
    no_source_url = []
    for f in facilities:
        for field in REQUIRED_FIELDS:
            if field not in f:
                missing_fields.append((f.get("id", "?"), field))
        if f.get("level_of_care") not in VALID_LEVELS:
            bad_levels.append((f.get("id"), f.get("level_of_care")))
        if not f.get("source_url"):
            no_source_url.append(f.get("id"))

    if missing_fields:
        raise SystemExit(f"Missing required fields: {missing_fields}")
    if bad_levels:
        raise SystemExit(f"Invalid level_of_care values: {bad_levels}")
    if no_source_url:
        raise SystemExit(f"Facilities missing source_url: {no_source_url}")

    by_level = Counter(f["level_of_care"] for f in facilities)
    by_source = Counter(s for f in facilities for s in f["data_source"])

    print(f"Total facilities: {len(facilities)}")
    print("By level_of_care:")
    for level, count in sorted(by_level.items()):
        print(f"  {level}: {count}")
    print("By data_source:")
    for source, count in sorted(by_source.items()):
        print(f"  {source}: {count}")
    print("Schema validation: OK")


if __name__ == "__main__":
    main()
