"""Vercel serverless entrypoint. The @vercel/python runtime serves the ASGI
`app` exported here; vercel.json rewrites every route to this function, and
FastAPI's StaticFiles mount serves web/index.html at /."""
import sys
from pathlib import Path

# ensure the repo root is importable (server/, pipeline/, data/ live there)
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from server.main import app  # noqa: E402,F401
