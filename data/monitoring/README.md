# Facility knowledge-graph monitoring state

Runtime monitoring state is **not** committed. `pipeline/monitor.py` writes it to
`out/monitoring/` (git-ignored), alongside the live graph under `out/graph/`,
which is seeded on first run from the committed `data/facilities.json` /
`data/edges_directory.json` baselines. This keeps scans from ever dirtying the
committed data. See `pipeline/live_store.py`.

Files created at runtime:

- `out/monitoring/pending_updates.json` — queue of proposed changes awaiting
  human approval (empty array at rest).
- `out/monitoring/version_history.json` — append-only log of every approved,
  rejected, or auto-applied update, keyed by entity id (facility id, or
  `"from|to"` for an edge).
- `out/monitoring/source_reliability.json` — the agent's learned per-source
  trust weights (raised on approval, lowered on rejection).

To reset the demo to the committed baseline, delete `out/graph` and
`out/monitoring`.
