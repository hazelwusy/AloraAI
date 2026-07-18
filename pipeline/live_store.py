"""Single source of truth for the *mutable* knowledge graph at runtime.

The committed files under ``data/`` are read-only baselines — the monitoring
agent must never dirty them. On first access we seed a runtime copy under
``out/`` (git-ignored) and everything that reads or writes the live graph — the
map (/api/graph), the matcher (directory.py), and the monitoring agent
(monitor.py) — goes through here, so they always agree and the repo stays clean.

To reset the demo to the committed baseline, delete ``out/graph``.
"""
from __future__ import annotations

import json
import shutil
from pathlib import Path

ROOT = Path(__file__).parent.parent
DATA = ROOT / "data"
OUT_GRAPH = ROOT / "out" / "graph"
OUT_MONITORING = ROOT / "out" / "monitoring"

# committed baselines (seeds) -> live runtime copies
_SEEDS = {
    "facilities.json": DATA / "facilities.json",
    "edges_directory.json": DATA / "edges_directory.json",
}


def _live_path(name: str) -> Path:
    """Return the runtime path for ``name``, seeding it from the committed
    baseline on first access."""
    live = OUT_GRAPH / name
    if not live.exists():
        live.parent.mkdir(parents=True, exist_ok=True)
        seed = _SEEDS.get(name)
        if seed and seed.exists():
            shutil.copy(seed, live)
    return live


def facilities_path() -> Path:
    return _live_path("facilities.json")


def edges_path() -> Path:
    return _live_path("edges_directory.json")


def monitoring_path(name: str) -> Path:
    OUT_MONITORING.mkdir(parents=True, exist_ok=True)
    return OUT_MONITORING / name


def load_json(path: Path, default):
    return json.loads(path.read_text()) if path.exists() else default


def save_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n")
