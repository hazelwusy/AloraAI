"""Fill the `simulated` block of each facility in data/facilities.json.

Idempotent: re-running regenerates the same simulated values given the fixed
seed in data/simulation_params.json, so it's safe to re-run after real fields
change without needing to hand-edit simulated data back in.
"""
import json
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FACILITIES_PATH = ROOT / "data" / "facilities.json"
PARAMS_PATH = ROOT / "data" / "simulation_params.json"


def pick_intake_requirements(rng, level, base_reqs):
    # Drop 0-2 items at random per facility so facilities at the same level
    # still differ from each other (supports a readiness-diff demo).
    reqs = list(base_reqs)
    n_drop = rng.choice([0, 0, 1, 1, 2])
    for _ in range(min(n_drop, max(0, len(reqs) - 2))):
        reqs.pop(rng.randrange(len(reqs)))
    return reqs


def main():
    facilities = json.loads(FACILITIES_PATH.read_text())
    params = json.loads(PARAMS_PATH.read_text())

    rng = random.Random(params["random_seed"])

    for f in facilities:
        level = f["level_of_care"]
        base_reqs = params["intake_requirements_by_level"].get(level, [])
        lo_acc, hi_acc = params["accept_rate_ranges_by_level"].get(level, [0.5, 0.7])
        lo_wait, hi_wait = params["wait_days_by_level"].get(level, [0, 7])
        declines = params["possible_declines_by_level"].get(level, ["no_capacity"])

        total_beds = f.get("total_beds")
        available_beds = None
        if isinstance(total_beds, int) and total_beds > 0:
            # Bias toward high occupancy per occupancy_basis_note.
            occupied_frac = rng.uniform(0.85, 0.98)
            available_beds = max(0, round(total_beds * (1 - occupied_frac)))

        f["simulated"] = {
            "intake_requirements": pick_intake_requirements(rng, level, base_reqs),
            "availability": {
                "available_beds": available_beds,
                "estimated_wait_days": rng.randint(lo_wait, hi_wait),
                "last_updated": "2026-07-18",
            },
            "decline_behavior": {
                "accept_rate": round(rng.uniform(lo_acc, hi_acc), 2),
                "possible_declines": declines,
                "median_response_min_sim": rng.choice([15, 30, 45, 60, 90, 120, 240]),
            },
        }

    FACILITIES_PATH.write_text(json.dumps(facilities, indent=2, ensure_ascii=False) + "\n")
    print(f"Updated simulated fields for {len(facilities)} facilities.")


if __name__ == "__main__":
    main()
