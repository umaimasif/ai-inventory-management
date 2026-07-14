"""Vercel serverless entrypoint.

Vercel's Python runtime picks up an ASGI app named `app` from this module and
serves it. `vercel.json` routes every /api/* request here, while the Next.js
frontend is served from the same domain — so the browser makes same-origin
calls and CORS never enters the picture.

The FastAPI app already prefixes its own routes with /api, so the path Vercel
forwards (e.g. /api/health) matches what the router expects.
"""
import sys
from pathlib import Path

# The application package lives in backend/, one level up from this file.
BACKEND_DIR = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from app.main import app  # noqa: E402

__all__ = ["app"]
