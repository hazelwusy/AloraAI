"""Generate a plausible SIMULATED referral topology across the 74-facility SF
directory so the System-map view has Kumu-like density. Existing hand-authored
edges (source "baseline") are preserved and marked verified; generated edges are
tagged source "simulated_topology" so real vs. simulated stays honest.

Deterministic (seeded) so re-running produces the same graph. Safe to re-run:
regenerates the simulated edges, keeps the baseline ones.

    python3 -m scripts.generate_referral_edges          # writes data/edges_directory.json
"""
from __future__ import annotations

import json
import random
from pathlib import Path

DATA = Path(__file__).parent.parent / "data"
FAC = DATA / "facilities.json"
EDGES = DATA / "edges_directory.json"

# acuity tiers, highest (crisis entry) -> lowest (community)
TIERS = [
    ["ED_psych"],
    ["inpatient_psych"],
    ["locked_subacute"],
    ["crisis_stabilization"],
    ["residential_tx"],
    ["residential_stepdown"],
    ["PHP"],
    ["IOP"],
    ["peer_respite", "sobering"],
    ["outpatient"],
]
TIER_OF = {loc: i for i, locs in enumerate(TIERS) for loc in locs}


def _payer_overlap(a: dict, b: dict) -> bool:
    return bool(set(a.get("payers", [])) & set(b.get("payers", [])))


def _edge(frm, to, etype, freq, accept, resp):
    return {
        "from": frm, "to": to, "type": etype, "freq_sim": freq,
        "simulated": {
            "accept_rate_observed": accept,
            "avg_response_time_min_observed": resp,
            "last_updated": "2026-07-18",
            "source": "simulated_topology",
        },
    }


def generate() -> dict:
    rng = random.Random(42)
    facilities = json.loads(FAC.read_text())
    existing = json.loads(EDGES.read_text()).get("edges", [])

    # keep hand-authored/baseline edges verbatim; we only regenerate simulated ones
    baseline = [e for e in existing if e.get("simulated", {}).get("source") != "simulated_topology"]
    seen = {(e["from"], e["to"]) for e in baseline}
    out = list(baseline)

    by_tier: dict[int, list[dict]] = {}
    for f in facilities:
        t = TIER_OF.get(f["level_of_care"])
        if t is not None:
            by_tier.setdefault(t, []).append(f)

    def pick(pool, src, k):
        cands = [g for g in pool if g["id"] != src["id"] and _payer_overlap(src, g)]
        rng.shuffle(cands)
        return cands[:k]

    for f in facilities:
        t = TIER_OF.get(f["level_of_care"])
        if t is None:
            continue

        # step-down: to 1-2 tiers below (the common discharge direction)
        down = by_tier.get(t + 1, []) + by_tier.get(t + 2, [])
        for g in pick(down, f, rng.randint(2, 4)):
            key = (f["id"], g["id"])
            if key in seen:
                continue
            seen.add(key)
            out.append(_edge(*key, "step_down", rng.randint(4, 9),
                             round(rng.uniform(0.45, 0.85), 2), rng.randint(20, 90)))

        # step-up: to 1 tier above (re-escalation on deterioration)
        for g in pick(by_tier.get(t - 1, []), f, rng.randint(0, 2)):
            key = (f["id"], g["id"])
            if key in seen:
                continue
            seen.add(key)
            out.append(_edge(*key, "step_up", rng.randint(1, 5),
                             round(rng.uniform(0.4, 0.7), 2), rng.randint(30, 120)))

        # vertical: lateral, same tier (transfers / capacity balancing)
        for g in pick(by_tier.get(t, []), f, rng.randint(0, 1)):
            key = (f["id"], g["id"])
            if key in seen:
                continue
            seen.add(key)
            out.append(_edge(*key, "vertical", rng.randint(1, 4),
                             round(rng.uniform(0.4, 0.7), 2), rng.randint(30, 100)))

        # crisis re-entry: community levels back to an ED/crisis facility
        if f["level_of_care"] in ("outpatient", "IOP", "PHP", "peer_respite"):
            crisis = by_tier.get(0, []) + by_tier.get(3, [])
            for g in pick(crisis, f, 1):
                key = (f["id"], g["id"])
                if key in seen:
                    continue
                seen.add(key)
                out.append(_edge(*key, "crisis_reentry", rng.randint(1, 3),
                                 round(rng.uniform(0.5, 0.85), 2), rng.randint(15, 60)))

    return {"edges": out}


if __name__ == "__main__":
    doc = generate()
    EDGES.write_text(json.dumps(doc, indent=2) + "\n")
    from collections import Counter
    c = Counter(e["type"] for e in doc["edges"])
    n_sim = sum(1 for e in doc["edges"] if e.get("simulated", {}).get("source") == "simulated_topology")
    print(f"wrote {len(doc['edges'])} edges ({n_sim} simulated, {len(doc['edges'])-n_sim} baseline): {dict(c)}")
