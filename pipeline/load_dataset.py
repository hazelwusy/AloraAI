"""Load the official dataset and select the care-transition encounters."""
from __future__ import annotations

import json
import os
from pathlib import Path

DEFAULT_PATHS = [
    os.environ.get("DATASET", ""),
    "data/synthetic-ambient-fhir-25.jsonl",
    "../synthetic-ambient-fhir-25/synthetic-ambient-fhir-25.jsonl",
]

TRANSITION_TYPES = ("Hospital admission", "Admission to hospice", "Hospital admission for isolation")


def dataset_path() -> Path:
    for p in DEFAULT_PATHS:
        if p and Path(p).exists():
            return Path(p)
    raise FileNotFoundError(
        "Dataset not found. Set DATASET=/path/to/synthetic-ambient-fhir-25.jsonl "
        "or copy it into ./data/"
    )


def load_all() -> list[dict]:
    with open(dataset_path()) as f:
        return [json.loads(line) for line in f]


def load_transitions() -> list[dict]:
    """The 6 admission encounters — receiving side of a care transition."""
    return [r for r in load_all() if r["metadata"]["visit_type"].startswith(TRANSITION_TYPES)]


def get_encounter(encounter_id: str) -> dict:
    for r in load_all():
        if r["metadata"]["encounter_id"] == encounter_id or r["id"] == encounter_id:
            return r
    raise KeyError(f"encounter {encounter_id!r} not in dataset")


def sources_for(record: dict) -> dict[str, str]:
    """The three source documents the grounding verifier checks against."""
    return {
        "transcript": record["transcript"],
        "note": record["note"],
        "fhir": json.dumps(record["encounter_fhir"], indent=1),
    }
