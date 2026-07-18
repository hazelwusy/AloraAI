"""End-to-end pipeline for one encounter.

    python -m pipeline.run_pipeline --list
    python -m pipeline.run_pipeline --id <encounter_id>
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from . import llm
from .grounding import verify_facts
from .load_dataset import get_encounter, load_transitions, sources_for
from .schemas import GapReport, MinerOutput, PipelineResult, TransferPacket

OUT_DIR = Path("out/packets")


def run(record: dict) -> PipelineResult:
    md = record["metadata"]
    sources = sources_for(record)

    user_content = (
        f"encounter_id: {md['encounter_id']}\n\n"
        f"## transcript\n{record['transcript']}\n\n"
        f"## note\n{record['note']}\n\n"
        f"## fhir\n{sources['fhir']}"
    )

    print(f"[1/3] Context Miner … ({md['visit_title']})")
    miner_raw = llm.call_json(llm.load_prompt("context_miner"), user_content, MinerOutput, max_tokens=8192)

    print(f"      mined {len(miner_raw.facts)} facts; verifying grounding …")
    miner, dropped = verify_facts(miner_raw, sources)
    print(f"      {len(miner.facts)} verified, {len(dropped)} dropped (ungrounded)")

    print("[2/3] Packet Composer …")
    facts_json = miner.model_dump_json(indent=1)
    packet = llm.call_json(
        llm.load_prompt("packet_composer"),
        f"facility_type: {md['visit_type']}\n\nverified_facts:\n{facts_json}",
        TransferPacket,
        max_tokens=8192,
    )

    print("[3/3] Gap Checker …")
    gaps = llm.call_json(
        llm.load_prompt("gap_checker"),
        f"facility_type: {md['visit_type']}\n\npacket:\n{packet.model_dump_json(indent=1)}",
        GapReport,
    )

    return PipelineResult(
        encounter_id=md["encounter_id"],
        visit_title=md["visit_title"],
        miner=miner,
        dropped_claims=dropped,
        packet=packet,
        gaps=gaps,
    )


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--list", action="store_true", help="list transition encounters")
    ap.add_argument("--id", help="encounter_id to run")
    args = ap.parse_args()

    if args.list or not args.id:
        for r in load_transitions():
            print(f"{r['metadata']['encounter_id']}  {r['metadata']['visit_title']}")
        return

    record = get_encounter(args.id)
    result = run(record)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUT_DIR / f"{result.encounter_id}.json"
    out_path.write_text(result.model_dump_json(indent=2))
    print(f"\nwrote {out_path}")
    print(f"one-liner: {result.packet.one_liner}")
    print(f"gaps for sender: {len(result.gaps.questions)}")


if __name__ == "__main__":
    main()
