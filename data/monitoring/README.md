# Facility knowledge-graph monitoring state

- `pending_updates.json` — queue of proposed changes to `../facilities.json`
  or `../edges_directory.json`, awaiting human approval. Empty array at rest.
- `version_history.json` — append-only log of every approved or rejected
  update, keyed by entity id (facility id, or `"from|to"` for an edge).

Both files are runtime state written by `pipeline/monitor.py` — safe to reset
to `[]` / `{}` between demo runs. See that module's docstring for what's real
vs. simulated in how updates get proposed.
